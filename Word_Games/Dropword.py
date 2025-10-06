""" This game is the classic Number grid puzzle
All the leters have been replaced by a random letter
You have to guess the letter
Chris Thomas May 2024

The games uses a 20k word dictionary
currntly fixed at 13 x 13 size due to needing to create grid manually
attempts to automate grid creation ahve not been succesful so far
"""
import random
import console
from time import sleep
import numpy as np
import requests
from queue import Queue
from Letter_game import LetterGame, Player
from gui.gui_interface import Gui, Squares, Coord
from crossword_create import CrossWord
import gui.gui_scene as gs
WordleList = [ 'wordlists/5000-more-common.txt', 'wordlists/words_20000.txt'] 
BLOCK = '#'
SPACE = ' '
file = 'https://gist.githubusercontent.com/eyturner/3d56f6a194f411af9f29df4c9d4a4e6e/raw/63b6dbaf2719392cb2c55eb07a6b1d4e758cc16d/20k.txt'
file = 'https://www.mit.edu/~ecprice/wordlist.10000'
def get_word_file(location, filename):
  r = requests.get(location)
  with open(filename, 'w') as f:
    f.write(r.text)

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
  
def  get_board_rc(rc, board):
  return board[rc[0]][rc[1]]
  
def copy_board(board):
  return list(map(list, board))
  

class DropWord(LetterGame):
  
  def __init__(self, debug=False):
    self.debug = debug
    # allows us to get a list of rc locations
    self.log_moves = False
    self.min_length = 2 # initial min word length
    self.max_length = 15 # initial  maximum word length
    self.load_words_from_file('dropword_templates.txt')
    self.initialise_board() 
    # create game_board
    self.SIZE = self.get_size() 
    self.columns = list(range(self.sizex))
    random.shuffle(self.columns)
    # load the gui interface
    self.gui = Gui(self.board, Player())
    self.gui.q = Queue()
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='white', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(grid_fill='black')
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Hint': self.hint,
                              'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
          
    self.load_words(word_length=self.sizex)    
    
    self.max_depth = 1 # search depth for populate  
    self.load_words(word_length=self.sizex) 
    self.moves = []   
    self.gui.clear_messages() 
    _, _, w, h = self.gui.grid.bbox 
    if self.gui.device.endswith('_landscape'):
       self.gui.set_enter('Undo', position = (w+50, h-150), 
                          stroke_color='black', 
                          fill_color='yellow',color='black')       
    self.gui.set_top('Dropword')
    self.hintbox = self.gui.add_button(text='', title='Hint word', 
                          position=(w+50, h-50), 
                          min_size=(150, 32))                      
    _ = self.gui.add_button(text='Hint', title='', position=(w+50,h-100),
                                   min_size=(100, 32), reg_touch=True, 
                                   stroke_color='black', 
                                   fill_color='yellow',color='black')                   
      

  def drop_words(self):
    """ delete all blocks and drop letters to the bottom """
    self.solution = self.board.copy()    
    #self.gui.update(self.board)
    #sleep(0.5)
    self.board[self.board =='.'] = '#'
    self.gui.print_board(self.board, 'initial board')
    for r in range(self.sizey-1, 1, -1):
      for c in range(self.sizex):
        while True:
          # remove BLOCK at bottom of column until letter
          if self.board[r,c] == BLOCK:            
            above = self.board[:r, c]
            self.board[1: above.shape[0] + 1, c] = above
            self.board[0, c] = ' '
            #self.gui.update(self.board, str(r))
          else:
            break
    # now reset centre column
    self.board[:, self.sizex//2] = self.solution[:, self.sizex//2]
    self.gui.print_board(self.board)
    self.gui.update(self.board)

  def indicate_hint(self, c):
    """ briefly make column orange
    """     
    self.gui.add_numbers([Squares((r,c), '', 'orange' , z_position=30, alpha = .5, stroke_color='white') 
                          for r in range(len(self.board))]) 
    sleep(1)
    self.gui.clear_numbers()
    
  def fill_crossword(self):
     def transfer_props(props):
       return  {k: getattr(self, k) for k in props}
     cx = CrossWord(self.gui, self.word_locations, self.all_words)
     cx.set_props(**transfer_props(['board', 'empty_board', 'all_word_dict', 
                                   'max_depth', 'debug']))
     self.board = cx.populate_words_graph(max_iterations=200,
                             length_first=False,
                             max_possibles=100,
                             swordsmith_strategy='dfs')
     self.board = np.array(self.board)
     self.board[self.board == '.'] = BLOCK
     fixed = len([word for word in self.word_locations if word.fixed]) 
     no_words = len(self.word_locations)      
     self.gui.set_message(f'Filled {fixed}/ {no_words} words')       
     #self.gui.update(self.board)                
        
  def run(self):
    """
    Main method that prompts the user for input
    """ 
    wait = self.gui.set_waiting('Generating Puzzle')   
    self.partition_word_list() 
    self.compute_intersections()
    if self.debug:
        print(self.word_locations)
    self.fill_crossword()
    self.drop_words()
    self.gui.set_message('')
    self.gui.reset_waiting(wait)
    while True:
      move = self.get_player_move(self.board)               
      finish = self.process_turn( move, self.board) 
      if finish or self.game_over():
         break
    console.hud_alert('Game Over')
    self.complete()

  def game_over(self):
    """ check for finished game   
    board = solution"""
    return  np.all(self.board == self.solution)

  def load_words(self, word_length, file_list=WordleList):
    LetterGame.load_words(self, word_length, file_list=file_list)

  def initialise_board(self):
    boards = {}
    if self.word_dict:
      # get words and puzzle frame from dict
      for key, v in self.word_dict.items():
        if '_frame' in key:
         board = [row.replace("'", "") for row in v]
         #board = [row.replace('"', '') for row in board]
         board =  [row.split('/') for row in board]   
         name  = key.split('_')[0]         
         boards[name]  = board

    self.puzzle = random.choice(list(boards))
    #self.puzzle = 'Puzzle'
    self.board = boards[self.puzzle]
    self.word_locations = []
        
    self.length_matrix()                                    
    self.empty_board = copy_board(self.board)
    print(len(self.word_locations), 'words', self.min_length, self.max_length) 
      
  def undo(self):
    try:
       self.board = self.moves.pop()
       self.gui.update(self.board)
    except (IndexError):
      return
  
  def shift(self, distance, start): 
    
    def swap(col, start, dir=1):
      if (col[start-dir] == BLOCK) or (col[start-dir] == SPACE):
          col[start-dir], col[start] = col[start], col[start-dir]  
      else:
          return True
                    
    col = self.selected_col.copy()
    if (distance == 1) and (col[start-1] == BLOCK or col[start-1] == SPACE):
        swap(col, start, dir=1)    
    elif distance > 0:
        for d in range(distance):
            alphas = np.char.isalpha(col)
            if any(alphas[:start-1]): # alpha to left of selected
                 #find 1st non_alpha to left of selected
                 a = np.argwhere(~alphas[:start-1])
                 if a.shape[0] == 0: # no space
                    return col
                 first_alpha = np.max(a)+1
                 for x in range(first_alpha, start+1):
                    if swap(col, x, dir=1):
                        return self.selected_col                              
            else: # no alpha so simple move
                if swap(col, start, dir=1):
                  return self.selected_col                                    
            start -= 1          
    else: # move a single tile down
        swap(col, start, dir=-1) 
        
    alphas = np.char.isalpha(col)
    col[~alphas] = BLOCK  
    return col      

  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter
    """    
    if move:
      coord, letter, row = move
      if move == ((None, None), None, None):
        return False
      r,c = coord
      
      if letter == 'Enter':
        self.undo()
        return False
      elif letter == 'Hint':
        self.hint()
        return False
      elif letter == 'Finish':
        return True    
      elif letter != '':
        if c != row[1]:
            return False # not allowed
        self.moves.append(self.board.copy())
        r_start, r_end = row[0], coord[0]
        self.selected_col = self.board[:, row[1]]
        if r_start == r_end: # tap on char
            # move adjacent alphas left if blank to move into
            self.board[:, c] = self.shift(1, r_start)
        else:
            self.board[:, c] = self.shift(r_start - r_end, r_start)       
      self.gui.update(self.board)
      return False

  def hint(self):
    try:   
        across_words =  [word for word in self.word_locations if word.direction == 'across']
        random.shuffle(across_words)
        hintword = across_words[0]
        self.gui.set_text(self.hintbox,f'{hintword.word} at row {hintword.start[0]}')
        #col = self.columns.pop()
        #self.board[:, col] = self.solution[:, col]
        #self.indicate_hint(col)
        self.gui.update(self.board)
    except (IndexError):
      self.game_over()
      self.gui.q.put((-10, -10))       

  def reveal(self):
    ''' skip to the end and reveal the board '''
    self.gui.update(self.solution)
    # This skips the wait for new location and induces Finished boolean to 
    # halt the run loop
    self.gui.q.put((-10, -10)) 

  def get_player_move(self, board=None):
      """Takes in the user's input and performs that move on the board,
      returns the coordinates of the move
      Allows for movement over board"""
      
      move = LetterGame.get_player_move(self, self.board)
      #self.gui.set_message(str(move))
      # deal with buttons. each returns the button text 
      
      if move == (-1, -1):
          return (None, None), 'Enter', None   
      if move == (-10, -10):
          return (None, None), 'Finish', None 
      # deal with buttons. each returns the button text    
      if move[0] < 0 and move[1] < 0:
          return (None, None), self.gui.buttons[-move[0]].text, None  
              
      point = self.gui.start_touch - self.gui.grid_pos
      # touch on board
      # Coord is a tuple that can support arithmetic
      rc_start = Coord(self.gui.grid_to_rc(point))      
      if self.check_in_board(rc_start):
          rc = Coord(move)
          return rc, self.get_board_rc(rc, self.board), rc_start                             
      return (None, None), None, None

  def restart(self):
    self.gui.close()
    self.finished = False
    g = DropWord()
    g.run()
    #self.__init__()
    #self.run() 

if __name__ == '__main__':
  g = DropWord(debug=False)
  g.run()
  
  while(True):
    quit = g.wait()
    if quit:
      break
