""" This game is the classic Number grid puzzle
All the leters have been replaced by a random letter
You have to guess the letter
Chris Thomas May 2024
# Modifications to allow predefined grid filled with numbers
# in this case random crossword creation is not used and a solver is called instead
Chris Thomas October 2024
The games uses a 20k word dictionary
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
import numpy as np
import traceback
from itertools import groupby
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
WordleList = ['wordlists/5000-more-common.txt', 'wordlists/words_20000.txt'] #, 'wordlists/letters10.txt'] 
BLOCK = '#'
SPACE = ' '
file = 'https://gist.githubusercontent.com/eyturner/3d56f6a194f411af9f29df4c9d4a4e6e/raw/63b6dbaf2719392cb2c55eb07a6b1d4e758cc16d/20k.txt'
file = 'https://www.mit.edu/~ecprice/wordlist.10000'
def get_word_file(location, filename):
  r = requests.get(name)
  with open('filename', 'w') as f:
    f.write(r.text)

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
  
def  get_board_rc(rc, board):
  return board[rc[0]][rc[1]]
  
def copy_board(board):
  return list(map(list, board))
  

class CrossNumbers(LetterGame):
  
  def __init__(self):
    self.debug = True
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
          
    self.load_words(word_length=None) #self.sizex)    
    self.min_length = 2 # initial min word length
    self.max_length = 15 # initial  maximum word length
    self.max_depth = 1 # search depth for populate  
    _, _, w, h = self.gui.grid.bbox 
    if self.gui.device.endswith('_landscape'):
       self.gui.set_enter('Hint', position = (w+100, -50))      
    else:
      self.gui.set_enter('Hint', position=(w-65, h+30),size=(60, 40)) 
    self.display = 'tiles'
    self.max_items = 13 # items in key list
    
  def generate_word_number_pairs(self):
    """ create 2 dictionaries
    solution contains complete number, letter pairs
    known_dict contains partial known items
    """
    self.letters = [letter for letter in 'abcdefghijklmnopqrstuvwxyz']
    numbers = list(range(1,27))
    if not self.filled_board:
        shuffled = random.sample(self.letters, k=len(self.letters))
        self.solution_dict = {number:[letter, True] for number, letter in zip(numbers, shuffled)}
        self.solution_dict[' '] = [' ', False]
        self.solution_dict['.'] = ['.', False]
        choose_three = random.choices(numbers, k=3)
        self.known_dict={number: [' ', False] for number in numbers}
        for no in choose_three:
          self.known_dict[no] =[self.solution_dict[no][0], True]
    else:
        self.solution_dict = {number:[self.soln_dict.get(number, ' '), True] for number in numbers}
        self.known_dict = {number: [' ', False] for number in numbers}
        letter_pos = np.argwhere(np.char.isalpha(self.initial_board))
        for loc in letter_pos:    
            no =  self.numbers[tuple(loc)]  
            letter = self.initial_board[loc[0]][loc[1]]
            self.known_dict[no] = [letter, True]
    #self.known_dict[' '] = [' ', False]
    #self.known_dict['.'] = ['.', False]
    
  def create_number_board(self):
    """ redraws the board with numbered squares and blank tiles for unknowns
    and letters for known"""          
    # start with empty board
    if self.filled_board:
        self.number_board = copy_board(self.initial_board)    
    else:
        self.number_board = copy_board(self.empty_board)
    self.board = [[" " if _char == "." else _char for c, _char in enumerate(row)] for r, row in enumerate(self.board)]
    self.solution_board = copy_board(self.board)
    self.board = copy_board(self.number_board)
    if not self.filled_board:
        # fill any empty spaces
        for r, row in enumerate(self.solution_board):
          for c, _char in enumerate(row):
            if _char == SPACE:
              self.board_rc((r, c), self.board, BLOCK)
    #self.update_board()
    
  def display_numberpairs(self, tiles, off=0, max_items=13):
    """ display players rack
    x position offset is used to select letters or numbers
    """   
    parent = self.gui.game_field
    _, _, w, h = self.gui.grid.bbox
    if self.gui.device.endswith('_landscape'): 
        if self.sizey < max_items:
          size =  self.gui.gs.SQ_SIZE * 13 / max_items   
        else:
          size =  self.gui.gs.SQ_SIZE
        x, y = 5, 0
        x = x + off* size
        for n, tile in enumerate(tiles):    
          t = Tile(Texture(Image.named(f'../gui/tileblocks/{tile}.png')), 0,  0, sq_size=size)   
          t.position = (w + x + 3 * int(n/max_items) * size , h - (n % max_items +1)* size + y)
          parent.add_child(t) 
    else: 
        size =  self.gui.gs.SQ_SIZE * 0.9
        x, y = 30, 40
        y = y + off* size
        for n, tile in enumerate(tiles):    
          t = Tile(Texture(Image.named(f'../gui/tileblocks/{tile}.png')), 0,  0, sq_size=size)   
          t.position = (x + int(n % max_items ) * size , h + (2* int(n / max_items) )* size + y)
          parent.add_child(t)         
        
  def update_board(self, hint=False, filter_placed=True, tile_color='yellow'):
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
              color = tile_color if self.known_dict[no][1] else 'orange'
            else:
              color = tile_color
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
    list_of_known_letters = ['_' for _ in range(len(list_known))]
    for i, v in enumerate(list_known):
        no, l = v
        letter, _ = l 
        if isinstance(no, int):
           if letter == ' ':
             letter = '_'
           list_of_known_letters[no-1] = letter
    
    # now set up text string
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
    # now choose text or tiles
    if self.display == 'tiles':
        self.display_numberpairs(list(range(1, len(list_of_known_letters)+1)), max_items=self.max_items)
        self.display_numberpairs(list_of_known_letters, off=1, max_items=self.max_items)
    else:
        self.gui.set_moves(msg, font=('Avenir Next', 23))
        
  def decode_and_display_filled_board(self):
    """ take a number filled board, display"""
    def split_text(s):
         for k, g in groupby(s, str.isalpha):
             yield ''.join(g)
             
    self.board = np.array(self.board)
    self.board[self.board=='-'] = ' '
    # deal with number/alpha combo
    number_letters = np.array([(r,c) for c in range(self.sizex) 
                               for r in range(self.sizey) 
                               if len(list(split_text(self.board[r][c])))>1])
    numbers = np.argwhere(np.char.isnumeric(self.board))
    #self.start_dict = {}
    self.numbers = np.zeros(self.board.shape, dtype=int)
    square_list = []
    for number in np.append(numbers, number_letters, axis=0):
      try:
         no, letter = list(split_text(self.board[tuple(number)]))
         self.board[tuple(number)] = letter      
      except (ValueError) as e:
         no = self.board[tuple(number)]
      self.numbers[tuple(number)] = int(no)
      #self.start_dict[tuple(number)] = no
      square_list.append(Squares(number, no, 'white', z_position=30,
                                        alpha=0.5, font=('Avenir Next', 18),
                                        text_anchor_point=(-1.0, 1.0)))
                        
    self.gui.add_numbers(square_list)
    self.board[np.char.isnumeric(self.board)] = ' '                                                            
    self.gui.update(self.board)   
    return self.board, self.numbers
        
  def copy_known(self):
    # now fill the rest of board with these
    for r in range(len(self.board)):
      for c in range(len(self.board[0])):
        no = self.numbers[(r,c)]
        letter = self.soln_dict.get(no, None)
        if letter:
          self.board[(r,c)] = letter
          
  def decode_filled_board(self):
    """ take a number filled board, display and attempt to solve """
    self.decode_and_display_filled_board()
    self.initial_board = copy_board(self.board)
    self.soln_dict ={} 
    # get starting known values
    letter_pos = np.argwhere(np.char.isalpha(self.board))
    for pos in letter_pos:
       letter = self.board[tuple(pos)]
       no = self.numbers[tuple(pos)]
       self.soln_dict[no] = letter
           
    self.copy_known()
    self.empty_board = copy_board(self.board)
    self.gui.update(self.board)
    return    
  
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    def transfer_props(props):
       return  {k: getattr(self, k) for k in props}
       
    self.gui.clear_messages()    
    self.print_square(None) 
    self.partition_word_list() 
    self.compute_intersections()
    if self.debug:
        print(self.word_locations)        
    if self.filled_board:
        self.decode_filled_board()
    cx = CrossWord(self.gui, self.word_locations, self.all_words)
    props = ['board', 'empty_board', 'all_word_dict', 'max_depth', 'debug']
    cx.set_props(**transfer_props(props))
    if self.filled_board:
       props = ['soln_dict', 'numbers', 'copy_known']      
       cx.set_props(**transfer_props(props))
       cx.number_words_solve(max_iterations=20, 
                             max_possibles=None)      
    else:       
        cx.populate_words_graph(max_iterations=200,
                                length_first=False,
                                max_possibles=100)  
    self.copy_known()
    self.gui.update(self.board)
    # self.print_board()
    self.check_words()    
    self.create_number_board()
    self.generate_word_number_pairs()
    self.update_board()
    if self.debug:
      print(self.anagrams())
      # [print(word, count) for word, count in self.word_counter.items() if count > 1]
    self.gui.set_message('')
    self.gui.set_enter('Hint')
    while True:
      move = self.get_player_move(self.board)               
      finish = self.process_turn( move, self.number_board) 
      sleep(1)
      if finish:
        break
      if self.game_over():
        break
    
    self.gui.set_message2('Game over')
    dialogs.hud_alert('Game Over')
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
    # detects if board has digits, indicating a prefilled board
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
    self.puzzle = 'Frame8'
    self.board = boards[self.puzzle]
    self.word_locations = []
    self.length_matrix()      
    print('frame lengths', [len(y) for y in self.board])
    self.filled_board = np.any(np.char.isdigit(np.array(self.board, dtype='U3')))  
    #self.empty_board = copy_board(self.board)
    self.table = copy_board(self.board)
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
    #self.gui.set_enter('Hint')
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
      #items = sorted(list(possibles)) 
      items = list(possibles)       
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
  









