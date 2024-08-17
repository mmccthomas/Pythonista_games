# ageneral purpose starting point for letter tile games -
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
#sys.path.append(f'{parent}/gui')

from datetime import datetime
from time import sleep, time
import math
import random
import re
import traceback
from  collections import Counter
from types import SimpleNamespace
from collections import defaultdict
from itertools import groupby
from queue import Queue
import console
import sound
#from tiles import pil2ui, slice_image_into_tiles
import matplotlib.colors as mcolors
import numpy as np


import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares


# Board characters
DESTROY = "D"
EMPTY = "-"
HIT = "H"
MISS = "^"
POSSIBLE = "?"

BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)

def add(a,b):
  """ helper function to add 2 tuples """
  return tuple(p+q for p, q in zip(a, b))
  
def sub(a,b):
  """ helper function to subtract 2 tuples """
  return tuple(p-q for p, q in zip(a, b)) 

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
  
def  get_board_rc(rc, board):
  return board[rc[0]][rc[1]]
  
def copy_board(board):
  return list(map(list, board)) 
  
def equal(a, b):
  """ test strings """
  # Ignore non-space and non-word characters
  regex = re.compile(r'[^\s\w]')
  return regex.sub('', a) == regex.sub('', b)
  
def lprint(seq, n):
  if len(seq) > 2 * n:
      return f'{seq[:n]}...........{seq[-n:]}'
  else:
      return(seq)

class Word():
  """ holds a word instance """
  def __init__(self, rc, direction, length):
    self.start = rc
    self.index = 0
    self.coords = []
    self.intersections = [] # shared positions with other words
    self.direction = direction
    self.length = length
    self.word = ''
    self.match_pattern = '' # store known letters
    self.word_dict : {}
    self.children = {} # holds linked words as coord: word_obj pairs
    self.parent_node = None
    self.visited = False # for searching
    self.fixed = False # positively correct 
    self.set_coords()
    self.child_index = 0
    self.max_depth = 3
    
  def __repr__(self):
    return(f'Word_{self.index}{self.start}_{self.direction}({self.length})={self.word}')
    
  def set_coords(self):
    r,c = self.start
    if self.direction == 'across':
      self.coords = [(r, c + x) for x in range(self.length)]
    else:
       self.coords = [(r + y, c ) for y in range(self.length)]
       
  def set_word(self, word, index=None):
    self.word=word
    # dictionary is coord: (letter, index of letter)}
    a= zip(self.coords,word)
    self.word_dict = {coord: (l,i) for i, (coord, l) in enumerate(a)}
    if index:
      self.index = index
     
    
  def get_word(self):
    return self.word
    
  def undo_word(self,coord, direction):
    """ erase a word, except for intersection """
    raise NotImplementedError
    
  def get_children(self):
   """exclude caller"""
   return {coord:child for coord,child in self.children.items() if child!= self}
      
  def get_next_child(self):
    """ fetch next child word in order"""
    child = list(self.children)[self.child_index]
    self.child_index += 1
    if self.child_index >= len(self.children):
      self.child_index = 0
    return child
    
  def  board_rc(self, rc, board, value):
    """ set character on board """
    try:
      board[rc[0]][rc[1]] = value
    except(IndexError):
      return None  
           
  def update_grid(self, coord, board, word):
    if isinstance(word, str):
      for i, letter in enumerate(word):
        self.board_rc(list(self.coords)[i], board, letter)
    else:
      raise(TypeError)
      
  def set_inter(self,inter):
    self.intersections = inter 
    
  def get_inter(self):
    return self.intersections
    
  def set_visited(self,value):
    self.visited = value
    
  def get_visited(self):
    return self.visited
  
  def set_fixed(self,value):
    self.fixed = value
      
  def intersects(self, rc, direction=None):
    if direction:
     return direction == self.direction and rc in self.coords
    else:
      return rc in self.coords
     
  def other_inter(self, coord):
    """ return intersections except for specified one"""
    return [i for i in self.intersections if i != coord]
     
  def set_length(self, rc, direction, board):
     pass
     """ 
       delta = (0, 0) 
            length = 1             
            while self.check_in_board(add(rc, delta)) and self.get_board_rc(add(rc, delta), self.board) != BLOCK :
                length +=1
                delta = add(delta, d)
            length -= 1  
            """ 
  def get_child_coord(self, child_obj):
    '''returns key from children dictionary'''
    for coord,v in self.children.items():
        if v == child_obj:
            return coord
      
class Player():
  def __init__(self):
    
    #images = slice_image_into_tiles('Letters_blank.jpg', 6, 5)
    characters ='__abcd_efghijklmnopqrstuv wxyz*'
    #IMAGES ={characters[j]:pil2ui(images[j]) for j in range(1,30)}
    # test
    #for d,i in IMAGES.items():
    # print(d), i.show()
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  ='abcdefghijklmnopqrstuvwxyz0123456789. '
    self.PIECES = [f'../gui/tileblocks/{k}.png' for k in self.PIECE_NAMES[:-2]]
    self.PIECES.append(f'../gui/tileblocks/@.png')
    self.PIECES.append(f'../gui/tileblocks/_.png')
    self.PLAYERS = None

                                                     
SOUND = True
#WORDLISTS = [ 'letters5.txt'] 
WORDLISTS = ['5000-more-common.txt'] # 'letters3.txt', 'letters10.txt'] 
  

class LetterGame():
  
  def __init__(self, **kwargs):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = True
    self.straight_lines_only = False
    self.word_dict = None
    self.remaining_ships =[[]]
    self.column_labels_one_based = False
    # create game_board and ai_board
    self.SIZE = self.get_size() 
     
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    for k, v in kwargs.items():
    	setattr(self, k, v)
    if self.column_labels_one_based:
    	self.gui.gs.column_labels = '1 2 3 4 5 6 7 8 9 10111213141516171819202122232425262728293031'
    self.gui.setup_gui(log_moves=True)
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'Show ....': self.run,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    self.max_depth = 4
    self.word_counter = None
    self.all = [[j,i] for i in range(self.sizex) for j in range(self.sizey) if self.board[j][i] == EMPTY]
    #self.gui.valid_moves(self.all, message=None)
    #self.toggle_density_chart = False # each call to density chart will switch on and off
    self.load_words(word_length=self.sizex)
    self.word_locations = []
    
  #.  Main Game loop #######s#  
  
  def delta_t(self, msg=None, do_print=True):
    try:
        t =  time() - self.start_time 
        if do_print:
          print(f'{msg} {t:.3f}') 
        return f'{msg} {t:.3f}'
    except(AttributeError):
      print('self.start_time not defined')
      print(traceback.format_exc())
    
  def random_color(self):
    colordict = mcolors.CSS4_COLORS # a curated list of colors
    return  colordict[random.choice(list(colordict))]  
    
  def copy_board(self, board):
    return list(map(list, board)) 
     
  def  board_rc(self, rc, board, value):
    """ set character on board """
    try:
      board[rc[0]][rc[1]] = value
    except(IndexError):
      return None 
  
  def  get_board_rc(self, rc, board):
    try:
      return board[rc[0]][rc[1]]
    except(IndexError):
      return None
      
  def format_cols(self, my_list, columns=3, width=1):
    msg = []
    if len(my_list) < columns:
       return ''.join(my_list)
       
    match columns:
       case 2:
          for first, second, in zip(
                 my_list[::columns], 
                 my_list[1::columns]):
             msg.append(f'{first: <{width}}{second}')
       case 3:
          for first, second, third in zip(
                 my_list[::columns], 
                 my_list[1::columns], 
                 my_list[2::columns]):
             msg.append(f'{first: <{width}}{second: <{width}}{third}')      
       case 4:
          for first, second, third, fourth in zip(
                 my_list[::columns], 
                 my_list[1::columns], 
                 my_list[2::columns],
                 my_list[3::columns]):
             msg.append(f'{first: <{width}}{second: <{width}}{third: <{width}}{fourth}')      
       case 5:
          for first, second, third, fourth, fifth in zip(
                 my_list[::columns], 
                 my_list[1::columns], 
                 my_list[2::columns],
                 my_list[3::columns],
                 my_list[4::columns]):
             msg.append(f'{first: <{width}}{second: <{width}}{third: <{width}}{fourth: <{width}}{fifth}')      
       case _ :
           raise ValueError('Columns > 5 not supported')
                 
    msg_str = '\n'.join(msg)
    msg_str = msg_str.strip() # remove trailing CR
    return msg_str
       
  def flatten(self, list_of_lists):
    """ nice simple metthod to flatten a nested 2d list """
    return sum(list_of_lists, [])
    
  def run(self):
    """
    Main method that prompts the user for input
    """
    self.start_time = time()
    self.print_square(1)
    self.initialise_board()    
    self.gui.set_message2(f"{len(self.all_words)} words", font=('Avenir Next', 25))
    self.finished = False
    while True:
      # for debug
      
      self.gui.gs.clear_highlights()
      
      # human play
      #self.gui.set_top('Human turn')           
      self.print_board()
      move = self.get_player_move(self.board)               
      #hit = self.check_hit(move ,self.board)
      move = self.process_turn( move, self.board)
      #self.gui.set_message(f"Message", font=('Avenir Next', 25)) 
      self.print_square(move)
      if self.game_over():
        break 
     
      self.print_board()
      self.gui.gs.clear_highlights()   
       
    self.print_board()
    self.gui.set_message2(f'{self.game_over()} WON!')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.gs.show_start_menu()
    
  def initialise_board(self):
    """ requires sizex, sizey fron get_size
                 letter_weights from load_words
    """
    for r in range(self.sizey):
      for c in range(self.sizex):
        self.board[r][c] = random.choices(self.gui.player.PIECE_NAMES[1:], self.letter_weights.values(),k=1)[0]
    return    
    for r in range(self.sizey):
      word = random.choice(self.wordlist)
      for c in range(self.sizex):
        self.board[r][c] = word[c]
        
  def show_squares(self, coords):        
      self.gui.clear_numbers()
      square_list = []
      for coord in coords:
          square_list.append(Squares(coord, '', 'orange' , 
                                     z_position=30, alpha = .5, stroke_color='white'))
      self.gui.add_numbers(square_list)   
              
  def load_words_from_file(self, file_list, no_strip=False):
    # read the entire wordfile as text
    with open(f'{file_list}', "r", encoding='utf-8') as f:
      data = f.read()
    # yaml read not working, so parse file, 
    # removing hyphens and spaces
    data = data.replace('-',' ')
    data_list = data.split('\n')
    w_dict = {}
    w_list = []
  
    key = None
    for word in data_list:
      if no_strip == False:
          word = word.strip()
      
      if ':' in word:
        if key:
          w_dict[key] = w_list[:-1] # remove empty string
          w_list = []
        key = word.split(':')[0]         
      else:
        w_list.append(word)
    w_dict[key] = w_list[:-1] # remove empty string  
    #print(w_dict)
    #self.all_words = self.wordlist
    self.word_dict = w_dict      
        
  def load_words(self, word_length=None, file_list=None):
    # get subset of words
    # letter weighting
    # computed from 5000 common words
    self.letter_weights= {'a': 0.601, 'b': 0.127, 'c': 0.366, 'd': 0.282, 'e': 1.0,   'f': 0.144,
                          'g': 0.200, 'h': 0.178, 'i': 0.670, 'j': 0.013, 'k': 0.058, 'l': 0.412, 
                          'm': 0.208, 'n': 0.600, 'o': 0.490, 'p': 0.241, 'q': 0.016, 'r': 0.622, 
                          's': 0.4884,'t': 0.613, 'u': 0.2863,'v': 0.1164,'w': 0.0696, 
                          'x': 0.030, 'y': 0.123, 'z': 0.008, 
                          '0': 0.0, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0,
                          '6': 0.0, '7': 0.0, '8': 0.0, '9': 0.0, '.': 0.0}
    if file_list is None:
      file_list = WORDLISTS
    all_word_list = []
    for word_file in file_list:
      with open(f'{word_file}', 'r') as f:
        words = [line.strip() for line in f]
      all_word_list.extend(words)
    
    
    if word_length:
        word_list = [line for line in all_word_list if len(line) == word_length]
    else:
        word_list = all_word_list
      
    self.wordlist = word_list
    self.wordset = set(word_list) # for fast search
    self.all_words = set(all_word_list) # fast seach for checking
  
  def length_matrix(self, search_directions=['down','across']):
    # process the board to establish starting points of words, its direction, and length
    self.word_locations = []
    #self.start_time= time()
    direction_lookup =  {'down': (1, 0), 'across': (0, 1), 'left': (0, -1),
                         'up': (-1, 0),  'diag_lr': (1, 1), 'diag_rl': (1, -1),
                         'diag_ul': (-1, -1), 'diag_ur': (-1, 1)}
    directions = [direction_lookup[d] for d in search_directions]      
               
    for r, row in enumerate(self.board):
      for c, character in enumerate(row):
        rc = r, c        
        if character == BLOCK:
          continue
        else:          
          for d, d_name in zip(directions, search_directions):
            delta = (0, 0) 
            length = 1             
            while self.check_in_board(add(rc, delta)) and self.get_board_rc(add(rc, delta), self.board) != BLOCK :
                length +=1
                delta = add(delta, d)
            length -= 1 
            t = Word(rc, d_name, length)  
            
            if length > 1 and not any([w.intersects(rc, d_name) for w in self.word_locations]):
              self.word_locations.append(t)
              
    if self.word_locations:
      for word in self.word_locations:
        word.match_pattern = '.' * word.length
                  
      self.min_length = min([t.length for t in self.word_locations])         
      self.max_length = max([t.length for t in self.word_locations])
      #self.delta_t('len matrix')       
    return self.min_length, self.max_length
    
  
         
  def compute_intersections(self):
    
    """ fill all word objects with linked (children) word objects  , forming a graph """
    for i, word in enumerate(self.word_locations):
      all_coords = [word.coords for word in self.word_locations]           
      all_coords.remove(word.coords)
      #flatten
      all_coords = set([x for xs in all_coords for x in xs]) 
      inter = set(word.coords).intersection(all_coords) 
      word.set_inter(inter)
      word.index = i
    for word in self.word_locations:
      word.children = {}
      for child in word.get_inter():
        for w in self.word_locations:
          if w.intersects(child) : # found one
            if w != word:
              word.children[child] = w   
             
                      
  def partition_word_list(self):
    ''' construct subsets of words for each required length
    Use dictionary keys for lengths. to construct named word sublists '''
    words = self.all_words
    # strip out spaces
    words = [word.replace(' ', '') for word in words]
    self.all_word_dict = {}
    for length in range(self.min_length, self.max_length +1):
      self.all_word_dict[length] =  {w for w in words if len(w) == length}
      print(f'Wordlist length {length} is {len(self.all_word_dict[length])}')
      
  def check_hit(self, rc):    
    pass    
  
  def predict_direction(self, move):
      ''' take a asequence of coordinates and predict direction (N, S,E,W etc)'''
      def sign(x):
        return (x > 0) - (x < 0)
        
      def uniquify(moves):
        """ filters list into unique elements retaining order"""
        return list(dict.fromkeys(moves)) 
      
      move = uniquify(move)      
      start = move[0]
      st_r, st_c = start
      end = move[-1]
      diff = sub(end, start)
      deltay, deltax = diff
      
      dx = sign(deltax)
      dy = sign(deltay) 
      # interpolate between start and end points
      if dx == 0 and dy == 0:
        rc_s = []
      elif dx == 0:
        rc_s = [add(start, (c*dy, 0)) for c in range(abs(deltay)+1)]  
      elif dy == 0:
        rc_s = [add(start, (0, c*dx)) for c in range(abs(deltax)+1)] 
      else:
        rc_s = [add(start, (c*dy, c*dx))  for  c in range(abs(deltax)+1)]          
      return rc_s        
        
  def process_turn(self, move, board):
    """ process the turn
    """
    #self.delta_t('start process turn')
    def uniquify(moves):
      """ filters list into unique elements retaining order"""
      return list(dict.fromkeys(moves))      
          
   # try to deal with directions 
    if isinstance(move, list):
        # lets count no of unique coordinates to see how long on each square
        move.pop(-1) # remove terminator
        if self.straight_lines_only:
          move = self.predict_direction(move)
        else:
          pass
          move = uniquify(move)        
        
        try:
            word = ''.join([board[rc[0]][rc[1]] for rc in move if isinstance(rc, tuple)])
            if self.debug:
                print(word)
            valid = word in self.all_words
            check = '\t\tValid word' if valid else '\t\tNot valid'
            self.gui.set_message(f'Word= {word} {check}')
            #self.delta_t('end process_turn')
        except(IndexError, AttributeError):
          """ all_words may not exist or clicked outside box"""
          if self.debug:
            print(traceback.format_exc())
        return move
        
    else:
      #board_rc(move, board, HIT)
      #self.initialise_board()
      return move
   
        
  def print_square(self, moves, color='orange', clear=True, alpha=0.5):
    #
    if clear:   
      self.gui.clear_numbers()
    if isinstance(moves, list): 
      square_list =[Squares(rc, '', color , z_position=30, alpha = alpha) for rc in moves]
      self.gui.add_numbers(square_list, clear)  
    return
    # random colours for testing
    square_list = []
    for r in range(self.sizey):
      for c in range(self.sizex):
        rc = r,c
        square_list.append(Squares(rc, '', random.choice(['orange', 'green', 'clear', 'cyan', 'yellow']) , z_position=30, alpha = .5))
    self.gui.add_numbers(square_list)  

    
  def get_size(self, size=None):
    # size can override board size
    # size is x, y
    if isinstance(size, tuple):
       selection = f'{size}'     
    elif isinstance(size, str):
         selection = size
    elif hasattr(self, 'board'):
        selection = f'{len(self.board[0])},{len(self.board)}'
        self.sizey, self.sizex = len(self.board), len(self.board[0])
        #self.gui.gs.DIMENSION_Y, self.gui.gs.DIMENSION_X = self.sizey, self.sizex
        return len(self.board), len(self.board[0])
    else:
        selection = console.input_alert("What is the dimension of the board (X, Y)? (Default is 5x5)\nEnter 2 numbers:")
    try:
      selection = selection.strip() 
      size = selection.split(',')
      if len(size) == 2:
        self.sizey = int(size[1])
        self.sizex = int(size[0])
      elif len(size) == 1:
        self.sizex = self.sizey= int(size)

      board_dimension = (self.sizey, self.sizex)      
    except(AttributeError, TypeError):
       self.sizex = self.sizey= 5
       board_dimension = (5,5)
       print(f"Invalid input. The board will be 5x5!")
    #self.gui.gs.DIMENSION_Y, self.gui.gs.DIMENSION_X = board_dimension
    self.create_game_board(board_dimension)
    return board_dimension
      
  def create_game_board(self, dimension):
    """Creates the gameBoard with the specified number of rows and columns"""   
    self.board = [[EMPTY] * dimension[1] for row_num in range(dimension[0])]
                  
  def check_in_board(self, coord):
    r,c = coord 
    try:
      return  (0 <= r < self.sizey) and  (0 <= c <  self.sizex)
    except(AttributeError):
      return  (0 <= r < len(self.board)) and  (0 <= c <  len(self.board[0]))
          
  def check_words(self):
    msg = []
    for word in self.word_locations:
      #board = ''.join([self.board[r][c] for r,c in word.coords])
      if word.word:
        if word.word not in self.all_words:
          msg.extend(f' {word.word}\n')
    if msg:
      print('unknown words', "".join(msg)) 
      #self.gui.set_message2(''.join(msg), font=('Avenir Next', 20))
      
  def _print_square(self, process, color=None):
    """ render the empty grid with black and white squares """
    self.gui.clear_numbers()     
    self.square_list =[]
    for r, row in enumerate(self.board):
      for c, character in enumerate(row):
        if character == BLOCK:
          self.square_list.append(Squares((r, c), '', 'black' , z_position=30, alpha = .2)) 
        else:
          self.square_list.append(Squares((r, c), '', 'white' , z_position=30, alpha = .2))     
    self.gui.add_numbers(self.square_list)   
    return
    
  def update_board(self, hint=False, filter_placed=False): 
       
    if hint:     
      self.gui.clear_numbers()
      square_list = []
      for r, row in enumerate(self.board):
        for c, char_ in enumerate(row):
          if char_ != BLOCK and char_ != SPACE:
            if char_ != self.solution_board[r][c]:
              square_list.append(Squares((r,c), '', 'orange' , z_position=30, alpha = .5, stroke_color='white'))
      self.gui.add_numbers(square_list)           
    else:
      self.gui.clear_numbers()        
           
  def print_board(self):
    """
    Display the  players game board, we neve see ai
    """            
    self.gui.set_moves('', font=('Avenir Next', 25))
    self.gui.update(self.board)
 
  def anagrams(self):
    """ create anagrams of all placed words
    if no valid words in wordlist, use scrambled letters
    return dictionary of {word_text [anagrams]}
    """
    try:
      dict_anagrams = defaultdict(list)
      for word in self.populate_order:
        for w in self.all_words:
          # check if length is same
          if(len(word) == len(w)):
             # if sorted char arrays are same
             if(sorted(word) == sorted(w)):  
               dict_anagrams[word].append(w)
      for word, values in dict_anagrams.items():
        if len(values) ==1 and values.pop() == word:
          b = list(word)
          random.shuffle(b)
          dict_anagrams[word] = [''.join(b)]
        if word in values:
          values.remove(word)
      return dict_anagrams
    except(AttributeError):
      print(traceback.format_exc())
      return None
      
  def dirs(self, board, y, x, length=None):
      # fast finding of all directions from starting location
      # optional masking of length
      # TODO change to finding coordinates, then use those to slice
      a = np.array(board)
      a = np.indices(a.shape).transpose()
      e = a[y, x:]
      w = np.flip(a[y, :x+1])
      s = a[y:, x]
      n = np.flip(a[:y+1, x])
      se = np.diag(a[y:, x:])
      sw = np.diag(np.fliplr(a[y:, :x+1]))
      ne = np.diag(np.flipud(a[:y+1, x:]))
      nw = np.flip(np.diag(a[:y+1, :x+1]))
      all_dirs = [n, ne, e, se, s, sw, w, nw]
      if length:
          for dirn in all_dirs:
              dirn = dirn[:length]
              if len(dirn) < length:
                  dirn = [] 
      
      indices = [dirn.indices for dirn in all_dirs]       
      return all_dirs, indices
          
  def reveal(self):
    ''' skip to the end and reveal the board '''
    self.gui.update(self.solution_board)
    #self.update_board()
    # This skips the wait for new location and induces Finished boolean to 
    # halt the run loop
    self.q.put(FINISHED)    

  def game_over(self):
    """
    Checks if the game is over
    """  
    return False
          
  def wait_for_gui(self):
    # loop until dat received over queue
    while True:
      # if view gets closed, quit the program
      if not self.gui.v.on_screen:
        print('View closed, exiting')
        sys.exit() 
        break   
      #  wait on queue data, either rc selected or function to call
      sleep(0.01)
      if not self.q.empty():
        data = self.q.get(block=False)
        
        #self.delta_t('get')
        #self.q.task_done()
        if isinstance(data, (tuple, list, int)):
          coord = data # self.gui.ident(data)
          break
        else:
          try:
            #print(f' trying to run {data}')
            data()
          except (Exception) as e:
            print(traceback.format_exc())
            print(f'Error in received data {data}  is {e}')
    return coord
  
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    #self.delta_t('start get move')
    if board is None:
        board = self.game_board
    coord_list = []
    prompt = (f"Select  position (A1 - {self.COLUMN_LABELS[-1]}{self.sizey})")
    # sit here until piece place on board   
    items = 0
    
    while items < 1000: # stop lockup
      #self.gui.set_prompt(prompt, font=('Avenir Next', 25))
      
      move = self.wait_for_gui()
      if items == 0: st = time()
      #print('items',items, move)
      try:
        # spot = spot.strip().upper()
        # row = int(spot[1:]) - 1
        # col = self.COLUMN_LABELS.index(spot[0])
        if self.log_moves:
          coord_list.append(move)
          items += 1
          if move == -1:
            #self.delta_t('end get move')
            return coord_list       
        else:
          break
      except (Exception) as e:
        print(traceback.format_exc())
        print('except,', move, e)
        coord_list.append(move)
        return coord_list
    return move

  def quit(self):
    self.gui.gs.close()
    sys.exit() 
  
  def restart(self):
    self.gui.gs.close()
    self.__init__()
    self.run()
        
  def wait(self):
    #wait until closed by gui or new game
    while True:
      if not self.gui.v.on_screen:
        print('View closed, exiting')
        return True
        break
      if self.finished: # skip if in game
        try:
          if not self.q.empty():
            item = self.q.get(block=False)
            # print('item', item)
            if item is self.quit:
              return True
            item()
        except (Exception) as e:
          print(traceback.format_exc())
          print(e)
      
      sleep(0.5)    
    
if __name__ == '__main__':
  g = LetterGame()
  g.run()
  while(True):
    quit = g.wait()
    if quit:
      break






