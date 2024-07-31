""" This game is the classic Number grid puzzle
All the leters have been replaced by a random letter
You have to guess the letter
Chris Thomas May 2024

The games uses a 20k word dictionary
currntly fixed at 13 x 13 size due to needing to create grid manually
attempts to automate grid creation ahve not been succesful so far
"""
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
import random
import console
import dialogs
import re
import traceback
from time import sleep, time
from queue import Queue
from collections import defaultdict
from Letter_game import LetterGame, Player, Word
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
from crossword_create import CrossWord
from gui.gui_scene import Tile, BoxedLabel
from ui import Image, Path, LINE_JOIN_ROUND, LINE_JOIN_MITER
from scene import Texture, Point
WordleList = [ '5000-more-common.txt', 'words_20000.txt'] 
BLOCK = '#'
SPACE = ' '
file = 'https://gist.githubusercontent.com/eyturner/3d56f6a194f411af9f29df4c9d4a4e6e/raw/63b6dbaf2719392cb2c55eb07a6b1d4e758cc16d/20k.txt'
file = 'https://www.mit.edu/~ecprice/wordlist.10000'
def get_word_file(location, filename):
  r = requests.get(name)
  with open('filename', 'w') as f:
    f.write(r.text)
    
def add(a,b):
  """ helper function to add 2 tuples """
  return tuple(p+q for p, q in zip(a, b))

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
  
def  get_board_rc(rc, board):
  return board[rc[0]][rc[1]]
  
def copy_board(board):
  return list(map(list, board))
  
def lprint(seq, n):
  if len(seq) > 2 * n:
      print(f'{seq[:n]}...........{seq[-n:]}')
  else:
      print(seq)        

class CrossNumbers(LetterGame):
  
  def __init__(self):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = True
    #self.word_locations = []
    self.load_words_from_file('crossword_templates.txt')
    self.initialise_board() 
    # create game_board and ai_board
    self.SIZE = self.get_size() 
     
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    #self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='white', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=False) # SQ_SIZE=45)
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
          
    self.load_words(word_length=self.sizex)    
    self.min_length = 2 # initial min word length
    self.max_length = 15 # initial  maximum word length
    self.max_depth = 1 # search depth for populate  
    _, _, w, h = self.gui.grid.bbox 
    if self.gui.device.endswith('_landscape'):
       self.gui.set_enter('Hint', position = (w+100, -50))       
    self.display = 'tiles'
    
  def generate_word_number_pairs(self):
    """ create 2 dictionaries
    solution contains complete number, letter pairs
    known_dict contains partial known items
    """
    self.letters = [letter for letter in 'abcdefghijklmnopqrstuvwxyz']
    numbers = list(range(1,27))
    shuffled = random.sample(self.letters, k=len(self.letters))
    self.solution_dict = {number:[letter, True] for number, letter in zip(numbers, shuffled)}
    self.solution_dict[' '] = [' ', False]
    self.solution_dict['.'] = ['.', False]
    choose_three = random.choices(numbers, k=3)
    self.known_dict={number: [' ', False] for number in numbers}
    for no in choose_three:
      self.known_dict[no] =[self.solution_dict[no][0], True]
    self.known_dict[' '] = [' ', False]
    self.known_dict['.'] = ['.', False]
    
  def create_number_board(self):
    """ redraws the board with numbered squares and blank tiles for unknowns
    and letters for known"""          
    # start with empty board    
    self.number_board = copy_board(self.empty_board)
    self.board = [[" " if _char == "." else _char for c, _char in enumerate(row)] for r, row in enumerate(self.board)]
    self.solution_board = copy_board(self.board)
    self.board = copy_board(self.empty_board)
    for r, row in enumerate(self.solution_board):
      for c, _char in enumerate(row):
        if _char == SPACE:
          self.board_rc((r, c), self.board, BLOCK)
    self.update_board()
    
  def display_numberpairs(self, tiles, x_off=0):
    """ display players rack
    x position offset is used to select letters or numbers
    """   
    parent = self.gui.game_field
    _, _, w, h = self.gui.grid.bbox        
    x, y = 5, 0
    x = x + x_off* self.gui.gs.SQ_SIZE
    rack = {}
    for n, tile in enumerate(tiles):    
      t = Tile(Texture(Image.named(f'../gui/tileblocks/{tile}.png')), 0,  0, sq_size=self.gui.gs.SQ_SIZE)   
      t.position = (w + x + 3 * int(n/13) * self.gui.gs.SQ_SIZE , h - (n % 13 +1)* self.gui.gs.SQ_SIZE + y)
      parent.add_child(t)     
               
        
  def update_board(self, hint=False, filter_placed=True):
    """ requires solution_dict from generate_word_number_pairs
                 solution_board from create_number_board 
    """
    def key_from_value(dict_, val, pos=0):
      for k, v in dict_.items():
        if v[pos] == val:
          return k
      return None
      
    self.gui.clear_numbers()
    square_list = []
    for r, row in enumerate(self.board):
      for c, char_ in enumerate(row):
        if char_ != BLOCK:
          no = key_from_value(self.solution_dict, self.solution_board[r][c])
          self.number_board[r][c] = no
          # reveal known
          k = self.known_dict[no][0]
          if k != ' ':
            self.board[r][c] = k
            if hint:
              color = 'yellow' if self.known_dict[no][1] else 'orange'
            else:
              color = 'yellow'
            square_list.append(Squares((r,c), '', color , z_position=30, alpha = .5, stroke_color='white'))
          else:
            self.board[r][c] = ' '
            # number in top left corner
            square_list.append(Squares((r,c), no, 'white' , z_position=30, alpha = .5,
                                       font = ('Avenir Next', 15), text_anchor_point=(-1,1)))
                                       
    

    # create text list for known dict
    msg = []
    list_known=list(self.known_dict.items()) # no,letter
    list_known =sorted(list_known, key = lambda x: x[1])
    # create a list of letters in correct order
    list_of_known_letters = ['_' for _ in range(26)]
    for i, v in enumerate(list_known):
        no, l = v
        letter, _ = l 
        if isinstance(no, int):
           if letter == ' ':
             letter = '_'
           list_of_known_letters[no-1] = letter
    
    for i, v in enumerate(list_known):
      no, l = v
      letter, _ = l
      letter = letter.upper()
      if no  != ' ' and no != '.':
        msg.append(f'{no:>2} = {letter:<2} ')
      if self.gui.device in ['ipad_landscape','ipad13_landscape']:
           msg.append('\n' if i % 2 == 0 else ' ' * 2)
      elif self.gui.device =='ipad_portrait':
           msg.append('\n' if i % 5 == 0 else ' ' * 2)
    
    msg = ''.join(msg)
    
    #should now have numbers in number board   
    self.gui.add_numbers(square_list)  
    self.gui.update(self.board)
    if self.display == 'tiles':
        self.display_numberpairs(list(range(1, 27)))
        self.display_numberpairs(list_of_known_letters, x_off=1)
    else:
        self.gui.set_moves(msg, font=('Avenir Next', 23))
    
       
  
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    cx = CrossWord(self.gui, self.word_locations, self.all_words)
    self.gui.clear_messages()
    
    self.print_square(None) 
    self.partition_word_list() 
    self.compute_intersections()
    if self.debug:
        print(self.word_locations)
    cx.set_props(board=self.board,
                 empty_board=self.empty_board, 
                 all_word_dict=self.all_word_dict, 
                 max_depth=self.max_depth)
    cx.populate_words_graph(max_iterations=200,
                            length_first=False,
                            max_possibles=100)  
    # self.print_board()
    self.check_words()
    self.generate_word_number_pairs()
    self.create_number_board()
    if self.debug:
      print(self.anagrams())
      [print(word, count) for word, count in self.word_counter.items() if count > 1]
    self.gui.set_message('')
    while True:
      move = self.get_player_move(self.board)               
      finish = self.process_turn( move, self.number_board) 
      sleep(1)
      if finish:
        break
      if self.game_over():
        break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
      
  def game_over(self):
    """ check for finished game   
    no more empty letters left in bosrd"""
    test = []
    for r, row in enumerate(self.number_board):
      for c, _char in enumerate(row):
        if isinstance(_char, int):
          test.append(self.board[r][c].isalpha())
    return all(test)
           
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
  
    #if not hasattr(self, 'puzzle'):        
    self.puzzle = random.choice(list(boards))
    #self.puzzle = 'Puzzle2'
    self.board = boards[self.puzzle]
    self.word_locations = []
    self.length_matrix()                  
    self.empty_board = copy_board(self.board)
    print(len(self.word_locations), 'words', self.min_length, self.max_length) 
    
  def print_square(self, process, color=None):
    """ render the empty grid with black and white squares """
    self.gui.clear_numbers()     
    self.square_list =[]
    for r, row in enumerate(self.board):
      for c, character in enumerate(row):
        if character == BLOCK:
          self.square_list.append(Squares((r, c), '', 'black' , z_position=30, alpha = .5)) 
        else:
          self.square_list.append(Squares((r, c), '', 'white' , z_position=30, alpha = .5))     
    self.gui.add_numbers(self.square_list)   
    return   
  
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter
    """    
    if move:
      coord, letter = move
      if move == ((None, None), None):
        return False
      r,c = coord
      if letter == 'Enter':
        # show all incorrect squares
        self.gui.set_prompt('Incorrect squares marked orange')
        self.update_board(hint=True)
        # now turn off marked squares
        sleep(2)
        for k,v in self.known_dict.items():
          if not v[1]:
            self.known_dict[k] = [' ', False]
        self.update_board(hint=False)
        return False
      elif letter == 'Finish':
        return True    
      elif letter != '':
        no = board[r][c]
        if no != BLOCK:
          correct = self.solution_dict[no][0] == letter
          self.known_dict[no] = [letter, correct]
          self.update_board()
          return False 
        else:
          return False     
      return True
  
  def reveal(self):
    ''' skip to the end and reveal the board '''
    self.known_dict = self.solution_dict
    self.update_board()
    # This skips the wait for new location and induces Finished boolean to 
    # halt the run loop
    self.q.put((-10, -10)) 
        
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    #self.delta_t('start get move')
    self.gui.set_enter('Hint')
    if board is None:
        board = self.board
    prompt = (f"Select  position on board")
    # sit here until piece place on board   
    rc = self.wait_for_gui()
    # print('selection position',rc)
    self.gui.set_prompt(f'selected {rc}')  
    if rc == (-1, -1):
      return (None, None), 'Enter' # pressed enter button
    if rc == (-10, -10):
      return (None, None), 'Finish' # induce a finish
    if get_board_rc(rc, board) != BLOCK:
      # now got rc as move
      # now open list
      if board is None:
          board = self.board
      selected_ok = False
      possibles = [letter.upper() for letter in  self.letters]
      prompt = f"Select from {len(possibles)} items"
      if len(possibles) == 0:
        raise (IndexError, "possible list is empty")
      items = sorted(list(possibles)) 
             
      #return selection
      self.gui.selection = ''
      selection = ''
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800,0))
        while self.gui.text_box.on_screen:    
          try:
            selection = self.gui.selection.lower()
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
            
        if len(selection) == 1:
          self.gui.selection =''
          # print('letter ', selection)
          return rc, selection
        elif selection == "Cancelled_":
          return (None, None), None
        else:
          return (None, None), None      
       
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    self.__init__()
    self.run() 

if __name__ == '__main__':
  g = CrossNumbers()
  g.run()
  
  while(True):
    quit = g.wait()
    if quit:
      break
  

