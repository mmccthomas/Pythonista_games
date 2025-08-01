# ageneral purpose starting point for letter tile games -
import sys 
import os
from time import sleep, time
import random
import re
import traceback
from collections import Counter
from collections import defaultdict
from itertools import zip_longest
from queue import Queue
from glob import glob
#Third party
import console
import dialogs
import clipboard
# from tiles import pil2ui, slice_image_into_tiles
import matplotlib.colors as mcolors
import numpy as np
from objc_util import on_main_thread
#Local imports
import base_path
base_path.add_paths(__file__)
from gui.gui_interface import Gui, Squares

# Board characters
EMPTY = "-"
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
# this set of wordlists will be set in child class
WORDLISTS = ['wordlists/5000-more-common.txt']
  


def add(a, b):
  """ helper function to add 2 tuples """
  return tuple(p+q for p, q in zip(a, b))

    
def sub(a, b):
  """ helper function to subtract 2 tuples """
  return tuple(p-q for p, q in zip(a, b))


def board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value

    
def get_board_rc(rc, board):
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
      return (seq)


def rle(inarray):
    """ run length encoding. Partial credit to R rle function.
    Multi datatype arrays catered for including non Numpy
    returns: tuple (runlengths, startpositions, values) """
    ia = np.asarray(inarray)                # force numpy
    n = len(ia)
    if n == 0:
        return (None, None, None)
    else:
        y = ia[1:] != ia[:-1]               # pairwise unequal (string safe)
        i = np.append(np.where(y), n - 1)   # must include last element posi
        z = np.diff(np.append(-1, i))       # run lengths
        p = np.cumsum(np.append(0, z))[:-1]  # positions
        return (z, p, ia[i])

                        
def run_length_encoding(inarray):
    """expanded name for rle"""
    return rle(inarray)

# #Encode word dictionary as Trie Node
# Slow to initialise, fast to search

                                                                                                                
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        
        
class WordDictionary:
    def __init__(self):
        self.root = TrieNode()
        self.possibles = []

    def add_word(self, word):
        current_node = self.root
        for character in word:
            current_node = current_node.children.setdefault(character, TrieNode())
        # Node for final char in word. Set flag is_word to True
        current_node.is_word = True
        
    def search(self, word):
        # is word in dictionary?
        def dfs(node, index):
            if index == len(word):
                return node.is_word
               
            if word[index] == ".":
                for child in node.children.values():
                    if dfs(child, index+1):
                        return True
                    
            if word[index] in node.children:
                return dfs(node.children[word[index]], index+1)
            
            return False
        return dfs(self.root, 0)
    
    def get_possibles(self, pattern):
        # find all possibles for match patter in dictionary
        words = []
        self._collect_words(self.root, pattern, 0, '', words)
        return words

    def _collect_words(self, node, pattern,  index, current_word, word_list):
        if index == len(pattern):
          if node.is_word:
              word_list.append(current_word)
          return
        char = pattern[index]
        if char == ".":
            # Wildcard: Explore all children
            for c, child in node.children.items():
                self._collect_words(child, pattern, index+1,  current_word+c, word_list)
        elif char in node.children:
            # Exact match
            self._collect_words(node.children[char], pattern, index + 1, current_word + char, word_list)
              

class Word():
  # class instance or _word_trie for later searching
  _word_trie = None
  
  """ holds a word instance """
  def __init__(self, rc, direction, length, **kwargs):
    self.start = rc
    self.index = 0
    self.coords = []
    self.np_coords = None
    self.intersections = []  # shared positions with other words
    self.direction = direction
    self.length = length
    self.word = ''
    self.match_pattern = ''  # store known letters
    self.word_dict = {}
    self.children = {}  # holds linked words as coord: word_obj pairs
    self.parent_node = None
    self.visited = False  # for searching
    self.fixed = False  # positively correct
    
    self.child_index = 0
    self.max_depth = 3
    self.no_possibles = 0
    self.possibles = []
 
    self.direction_deltas = {
        'across': (0, 1), 'e': (0, 1),
        'down': (1, 0), 's': (1, 0),
        'n': (-1, 0),
        'ne': (-1, 1), 'se': (1, 1),
        'sw': (1, -1), 'w': (0, -1),
        'nw': (-1, -1)
    }
    self.set_coords()
    for k, v in kwargs.items():
      setattr(self, k, v)
      
  def __repr__(self):
    word = self.word if self.word else self.match_pattern
    return (f'Word_{self.index}{self.start}_{self.direction.upper()}({self.length})= {word.capitalize()}')
    
  def set_coords(self):
    r, c = self.start
    # In set_coords:
    delta_r, delta_c = self.direction_deltas.get(self.direction.lower())
    if delta_r is None: # handle unknown direction if not caught by init validation
        raise ValueError(f'Direction {self.direction} not known')
    self.coords = [(r + i * delta_r, c + i * delta_c) for i in range(self.length)]
           
    # this is used to apply to board array    
    self.np_coords = tuple(np.array(self.coords).T)
    
  def set_word(self, word, index=None):
    self.word = word
    # dictionary is coord: (letter, index of letter)}
    a = zip(self.coords, word)
    self.word_dict = {coord: (l, i) for i, (coord, l) in enumerate(a)}
    if index:
      self.index = index
    
  def get_word(self):
    return self.word
    
  @property
  def is_diagonal(self):
      return self.direction in ['NE', 'SE', 'SW', 'NW']
       
  def undo_word(self, coord, direction):
    """ erase a word, except for intersection
    Placeholder for inheritor """
    raise NotImplementedError
    
  def get_children(self):
   """exclude caller"""
   return {coord: child for coord, child in self.children.items() if child != self}
      
  def get_next_child(self):
    """ fetch next child word in order"""
    child = list(self.children)[self.child_index]
    self.child_index += 1
    if self.child_index >= len(self.children):
      self.child_index = 0
    return child
    
  def board_rc(self, rc, board, value):
    """ set character on board """
    try:
      board[rc[0]][rc[1]] = value
    except (IndexError):
      return None
           
  def update_grid(self, coord, board, word):
    if isinstance(word, str):
      for i, letter in enumerate(word):
        self.board_rc(list(self.coords)[i], board, letter)
    else:
      raise (TypeError)
      
  def set_inter(self, inter):
      self.intersections = inter
    
  def get_inter(self):
      return self.intersections
    
  def set_visited(self, value):
      self.visited = value
    
  def get_visited(self):
      return self.visited
  
  def set_fixed(self, value):
      self.fixed = value
  
  def set_index(self, value):
      self.index = value

  def intersects(self, rc, direction=None):
    if direction:
     return direction == self.direction and rc in self.coords
    else:
      return rc in self.coords
     
  def other_inter(self, coord):
    """ return intersections except for specified one"""
    return [i for i in self.intersections if i != coord]

  def set_length(self, rc, direction, board):
      """Placeholder for inheritor """
      raise NotImplementedError   
                        
  def update_match(self, board):
      """ update match_pattern from supplied numpy 2d board """
      # use self.np_coords which are in correct form to 
      # directly index 2d character array
      # try to get fastest.
      # assumes empty squares are dot
      b = board[self.np_coords]
      self.match_pattern  = ''.join(b)
          
  def get_child_coord(self, child_obj):
    '''returns key from children dictionary'''
    for coord, v in self.children.items():
        if v == child_obj:
            return coord

  def get_possibles(self, wordlist=None):
      # if specified, wordlist is set of words with correct length
      # it may also have correct start letter
      if Word._word_trie:
          possibles = Word._word_trie.get_possibles(self.match_pattern)
      elif wordlist:
          m = re.compile(self.match_pattern)
          possibles = [w for w in wordlist if m.search(w)]
      else:
          raise RuntimeError('No wordlist or word_trie set')
      self.no_possibles = len(possibles)
      self.possibles = possibles
      return possibles
      
  @classmethod
  def create_trie(cls, word_dict):
      """ load word trie """
      cls._word_trie = WordDictionary()
      [cls._word_trie.add_word(word) for word in word_dict]

                    
class Player():
  """ defines character/ image file lookup """
  
  def __init__(self):
    # base path is parent of current directory
    base_path = os.path.dirname(os.path.dirname(__file__))
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES = 'abcdefghijklmnopqrstuvwxyz0123456789. '
    self.PIECES = [os.path.join(base_path, 'gui', 'tileblocks', f'{k}.png') for k in self.PIECE_NAMES[:-2]]
    self.PIECES.append(os.path.join(base_path, 'gui', 'tileblocks', '@.png'))
    self.PIECES.append(os.path.join(base_path, 'gui', 'tileblocks', '_.png'))
    self.PLAYERS = None
    
                                                     
class LetterGame():
  """ Base Class for a series of letter based word games """
  
  def __init__(self, **kwargs):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = True
    self.straight_lines_only = False
    self.word_dict = None
    self.column_labels_one_based = False
    # create game_board and ai_board
    self.SIZE = self.get_size()
     
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q  # pass queue into gui
    self.gui.set_alpha(True)
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.gs.one_based_labels = self.column_labels_one_based
    
    for k, v in kwargs.items():
      setattr(self, k, v)
    
    self.gui.setup_gui(log_moves=True)
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'Show ....': self.run,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    self.max_depth = 4
    self.word_counter = None
    self.all = [[j, i] for i in range(self.sizex) for j in range(self.sizey) if self.board[j][i] == EMPTY]
    
    self.load_words(word_length=self.sizex)
    self.word_locations = []
    self.length_matrix()
    self.compute_intersections()
    
  #  Main Game loop #######s#
  
  def delta_t(self, msg=None, do_print=True):
    try:
        t = time() - self.start_time
        if do_print:
          print(f'{msg} {t:.3f}')
        return f'{msg} {t:.3f}'
    except (AttributeError):
      print('self.start_time not defined')
      print(traceback.format_exc())
    
  def random_color(self):
    colordict = mcolors.CSS4_COLORS  # a curated list of colors
    return colordict[random.choice(list(colordict))]
    
  def copy_board(self, board):
    return list(map(list, board))
     
  def board_rc(self, rc, board, value):
    """ set character on board """
    try:
      board[rc[0]][rc[1]] = value
    except (IndexError):
      return None
  
  def get_board_rc(self, rc, board):
    try:
      return board[rc[0]][rc[1]]
    except (IndexError):
      return None
      
  def replace_board_section(self, coord, replacement, board=None):
      """replace a section of ndarray board with replacement ndarray
      """
      if board is None:
          board = self.board
      r, c = coord
      tile_y, tile_x = replacement.shape
      board[r * tile_y:r * tile_y + tile_y,
            c * tile_x:c * tile_x + tile_x] = replacement
      return board
                   
  def format_cols(self, my_list, columns=3, width=1):
    msg = []
    if len(my_list) < columns:
       return ' '.join(my_list)
       
    match columns:
       case 2:
          for first, second, in zip_longest(
                 my_list[::columns],
                 my_list[1::columns], fillvalue=''):
             msg.append(f'{first: <{width}}{second}')
       case 3:
          for first, second, third in zip_longest(
                 my_list[::columns],
                 my_list[1::columns],
                 my_list[2::columns], fillvalue=''):
             msg.append(f'{first: <{width}}{second: <{width}}{third}')
       case 4:
          for first, second, third, fourth in zip_longest(
                 my_list[::columns],
                 my_list[1::columns],
                 my_list[2::columns],
                 my_list[3::columns], fillvalue=''):
             msg.append(f'{first: <{width}}{second: <{width}}{third: <{width}}{fourth}')
       case 5:
          for first, second, third, fourth, fifth in zip_longest(
                 my_list[::columns],
                 my_list[1::columns],
                 my_list[2::columns],
                 my_list[3::columns],
                 my_list[4::columns], fillvalue=''):
             msg.append(f'{first: <{width}}{second: <{width}}{third: <{width}}{fourth: <{width}}{fifth}')
       case _:
           raise ValueError('Columns > 5 not supported')
                 
    msg_str = '\n'.join(msg)
    msg_str = msg_str.strip()  # remove trailing CR
    return msg_str
       
  def flatten(self, list_of_lists):
    """ nice simple metthod to flatten a nested 2d list """
    return sum(list_of_lists, [])
  
  @on_main_thread
  def clipboard_set(self, msg):
      '''clipboard seems to need @on_main_thread '''
      clipboard.set(msg)
             
  @on_main_thread
  def clipboard_get(self):
      return clipboard.get()
            
  def check_clipboard(self):
      data = self.clipboard_get()
      if data == '':
          print('clipboard fail')
      else:
          print('clipboard', data)
                 
  def format_for_portrait(self, word_dict):
      """ expects a dictionary with len(words) as key, and unsorted
      list of words with that length
      transform dictionary into columns with each column being same length
      Need to use monospaced font such as Fira Mono
      """
      headers = [f'{k:<{k}}' for k in word_dict]
      rows = [sorted(list(value)) for value in word_dict.values()]
      cols = [list(c) for c in zip_longest(*rows, fillvalue='')]
      for i, row in enumerate(cols):
        for j, item in enumerate(row):
          if len(item) == 0:
            cols[i][j] = f'{" ":<{len(headers[j])}}'
            
      words = [' '.join(headers), '\n', '\n'.join([' '.join(c) for c in cols])]
      no_lines = len(cols) + 1
      return words, ''.join(words), no_lines
  
  def complete(self):
      """ standard finish up the game """
      console.hud_alert('Game Over')
      self.gui.set_message('')
      self.gui.set_prompt('')
      sleep(4)
      self.finished = True
      self.gui.show_start_menu()
      # allow menu item to be processed
      self.wait_for_gui()
                           
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
      # self.gui.set_top('Human turn')
      self.print_board()
      move = self.get_player_move(self.board)
      print(move)
      # hit = self.check_hit(move ,self.board)
      move = self.process_turn(move, self.board)
      # self.gui.set_message(f"Message", font=('Avenir Next', 25))
      self.print_square(move)
      if self.game_over():
        break
     
      self.print_board()
      self.gui.gs.clear_highlights()
       
    self.print_board()
    self.gui.set_message2(f'{self.game_over()} WON!')
    self.complete()
  
  def get_frame_sizes(self, word_dict):
      # get board size for items in word_dict
      # return list of strings in form '(rowsxcols)'
      item_sizes = []
      for item, values in word_dict.items():
          y_len = len(values)
          if '/' in values[0]:
             x_len = len(values[0].split('/'))
          else:
             x_len = len(values[0])
          item_sizes.append(f'({y_len}x{x_len})')
      return item_sizes
              
  def select_list(self, word_lists, add_frame_sizes=True):
      '''Choose which category
      optionally add the grid size to the list
      '''
      items = [s.capitalize() for s in word_lists.keys()]
      items = [item for item in items
               if not item.endswith('_frame')]
      if add_frame_sizes:
         frame_sizes = self.get_frame_sizes(word_lists)
         items = [item + ' ' + item_size for item, item_size in zip(items, frame_sizes)]
      # return selection
      selection = ''
      prompt = ' Select puzzle'
      selection = dialogs.list_dialog(prompt, items)
      
      if selection is None:  # 'cancelled_':
          return None
      if len(selection):
          if self.debug:
            print(f'{selection=}')
          return selection.split(' ')[0]
            
  def initialise_board(self):
    """ requires sizex, sizey fron get_size
                 letter_weights from load_words
    """
    for r in range(self.sizey):
      for c in range(self.sizex):
        self.board[r][c] = random.choices(self.gui.player.PIECE_NAMES[1:], self.letter_weights.values(), k=1)[0]
    return
    for r in range(self.sizey):
      word = random.choice(self.wordlist)
      for c in range(self.sizex):
        self.board[r][c] = word[c]
        
  def show_squares(self, coords):
      self.gui.clear_numbers()
      square_list = []
      for coord in coords:
          square_list.append(Squares(coord, '', 'orange',
                                     z_position=30, alpha=.5, stroke_color='white'))
      self.gui.add_numbers(square_list)
              
  def load_words_from_file(self, file_list, no_strip=False):
    # read the entire wordfile as text
    with open(f'{file_list}', "r", encoding='utf-8') as f:
      data = f.read()
    
    data = data.replace('-', ' ')
    data_list = data.split('\n')
    w_dict = {}
    w_list = []
  
    key = None
    for word in data_list:
      if no_strip is False:
          word = word.strip()
      
      if ':' in word:
        if key:
          w_dict[key] = w_list[:-1]  # remove empty string
          w_list = []
        key = word.split(':')[0]
      else:
        w_list.append(word)
    w_dict[key] = w_list[:-1]  # remove empty string
    # print(w_dict)
    # self.all_words = self.wordlist
    self.word_dict = w_dict
        
  def last_puzzle_name(self, file):
      """ get last puzzle name and number in file """
      with open(file, 'r', encoding='utf-8') as f:
          lines = f.read()
      lines = lines.replace('-', ' ')
      lines = lines.split('\n')
      w_list = [line.removesuffix('_frame:') for line in lines if line.endswith('_frame:')]
      last_name = w_list[-1]
      numbers = re.findall(r'\d+', last_name)
      last_number = numbers[-1]
      base = last_name[:last_name.index(last_number)]
      next_number = int(last_number) + 1
      return base, next_number
        
  def load_words(self, word_length=None, file_list=None):
    # get subset of words
    # letter weighting
    # computed from 5000 common words
    self.letter_weights = {
        'a': 0.601, 'b': 0.127, 'c': 0.366, 'd': 0.282, 'e': 1.0,   'f': 0.144,
        'g': 0.200, 'h': 0.178, 'i': 0.670, 'j': 0.013, 'k': 0.058, 'l': 0.412,
        'm': 0.208, 'n': 0.600, 'o': 0.490, 'p': 0.241, 'q': 0.016, 'r': 0.622,
        's': 0.4884, 't': 0.613, 'u': 0.2863, 'v': 0.1164, 'w': 0.0696,
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
    self.wordset = set(word_list)  # for fast search
    self.all_words = set(all_word_list)  # fast seach for checking
  
  def check_for_ascii(self, wordlist, source):
      # check for unicode characters from ocr
      for word in wordlist:
          for letter in word:
              if 32 <= ord(letter) <= 122:
                  continue
              else:
                  raise RuntimeError(f'{source} {word} contains non-ascii {letter}')
                  
  def length_matrix(self, search_directions=['down', 'across']):
    # process the board to establish starting points of words, its direction, and length
    
    self.word_locations = []
    # self.start_time= time()
    direction_lookup = {'down': (1, 0), 'across': (0, 1), 'left': (0, -1),
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
            while self.check_in_board(add(rc, delta)) and self.get_board_rc(add(rc, delta), self.board) != BLOCK:
                length += 1
                delta = add(delta, d)
            length -= 1
            t = Word(rc, d_name, length)
            
            if length > 1 and not any([w.intersects(rc, d_name)
                                       for w in self.word_locations]):
              self.word_locations.append(t)
              
    if self.word_locations:
      for word in self.word_locations:
        word.match_pattern = '.' * word.length
      # find length of all words
      lengths = Counter([word.length for word in self.word_locations])
      self.wordlengths = dict(sorted(lengths.items()))
      self.min_length = min(self.wordlengths)
      self.max_length = max(self.wordlengths)
      # self.delta_t('len matrix')
    return self.min_length, self.max_length
               
  def compute_intersections(self):
    """ fill all word objects with linked (children) word objects,
    forming a graph """
    for i, word in enumerate(self.word_locations):
      all_coords = [word.coords for word in self.word_locations]
      all_coords.remove(word.coords)
      # flatten
      all_coords = set([x for xs in all_coords for x in xs])
      inter = set(word.coords).intersection(all_coords)
      word.set_inter(inter)
      word.index = i
    for word in self.word_locations:
      word.children = {}
      for child in word.get_inter():
        for w in self.word_locations:
          if w.intersects(child):  # found one
            if w != word:
              word.children[child] = w
                                   
  def partition_word_list(self):
    ''' construct subsets of words for each required length
    Use dictionary keys for lengths. to construct named word sublists '''
    words = self.all_words
    # strip out spaces
    words = [word.replace(' ', '') for word in words]
    self.all_word_dict = {}
    for length in range(self.min_length, self.max_length + 1):
      self.all_word_dict[length] = {w for w in words if len(w) == length}
      if self.debug:
          print(f'Wordlist length {length} is {len(self.all_word_dict[length])}')
      
  
  def uniquify(self, moves):
      """ filters list into unique elements retaining order"""
      return list(dict.fromkeys(moves))
        
  def predict_direction(self, move):
      ''' take a asequence of coordinates and predict direction (N, S,E,W etc)'''
      def sign(x):
        return (x > 0) - (x < 0)
           
      move = self.uniquify(move)
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
        rc_s = [add(start, (c*dy, c*dx)) for c in range(abs(deltax)+1)]
      return rc_s
        
  def process_turn(self, move, board):
    """ process the turn
    """
    # self.delta_t('start process turn')
    
   # try to deal with directions
    if isinstance(move, list):
        # lets count no of unique coordinates to see how long on each square
        move.pop(-1)  # remove terminator
        if self.straight_lines_only:
          move = self.predict_direction(move)
        else:
          pass
          move = self.uniquify(move)
        
        try:
            word = ''.join([board[rc[0]][rc[1]] for rc in move if isinstance(rc, tuple)])
            if self.debug:
                print(word)
            valid = word in self.all_words
            check = '\t\tValid word' if valid else '\t\tNot valid'
            self.gui.set_message(f'Word= {word} {check}')
            # self.delta_t('end process_turn')
        except (IndexError, AttributeError):
          """ all_words may not exist or clicked outside box"""
          if self.debug:
            print(traceback.format_exc())
        return move
        
    else:
      return move
         
  def print_square(self, moves, color='orange', clear=True, alpha=0.5):
    #
    if clear:
      self.gui.clear_numbers()
    if isinstance(moves, list):
      square_list = [Squares(rc, '', color, z_position=30, alpha=alpha)
                     for rc in moves]
      self.gui.add_numbers(square_list, clear)
    return
    
  def get_size(self, size=None):
    # size can override board size
    # size is x, y
    if isinstance(size, tuple):
       selection = f'{size}'
    elif isinstance(size, str):
        selection = size
    elif hasattr(self, 'board') and self.board is not None:
        selection = f'{len(self.board[0])},{len(self.board)}'
        self.sizey, self.sizex = len(self.board), len(self.board[0])
        # self.gui.gs.DIMENSION_Y, self.gui.gs.DIMENSION_X = self.sizey, self.sizex
        return len(self.board), len(self.board[0])
    else:
        selection = console.input_alert("What is the dimension of the board (X, Y)? (Default is 5x5)\nEnter 2 numbers:")
    try:
      # can use space, comma or x for seperator
      size = selection.replace(',', ' ').replace('x', ' ').split()
      if len(size) == 2:
        self.sizey = int(size[1])
        self.sizex = int(size[0])
      elif len(size) == 1:
        self.sizex = self.sizey = int(size)

      board_dimension = (self.sizey, self.sizex)
    except (AttributeError, TypeError):
       self.sizex = self.sizey = 5
       board_dimension = (5, 5)
       print("Invalid input. The board will be 5x5!")
    # self.gui.gs.DIMENSION_Y, self.gui.gs.DIMENSION_X = board_dimension
    self.create_game_board(board_dimension)
    return board_dimension
      
  def create_game_board(self, dimension):
    """Creates the gameBoard with the specified number of rows and columns"""
    self.board = [[EMPTY] * dimension[1] for row_num in range(dimension[0])]
                  
  def check_in_board(self, coord):
    r, c = coord
    try:
      return (0 <= r < self.sizey) and (0 <= c < self.sizex)
    except (AttributeError):
      return (0 <= r < len(self.board)) and (0 <= c < len(self.board[0]))
          
  def check_words(self):
    msg = []
    for word in self.word_locations:
      # board = ''.join([self.board[r][c] for r,c in word.coords])
      if word.word:
        if word.word not in self.all_words:
          msg.extend(f' {word.word}\n')
    if msg:
      print('unknown words', "".join(msg))
      # self.gui.set_message2(''.join(msg), font=('Avenir Next', 20))
      
  def _print_square(self, process, color=None):
    """ render the empty grid with black and white squares """
    self.gui.clear_numbers()
    self.square_list = []
    for r, row in enumerate(self.board):
      for c, character in enumerate(row):
        if character == BLOCK:
          self.square_list.append(Squares((r, c), '', 'black', z_position=30, alpha=.2))
        else:
          self.square_list.append(Squares((r, c), '', 'white', z_position=30, alpha=.2))
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
              square_list.append(Squares((r, c), '', 'orange',
                                         z_position=30, alpha=.5,
                                         stroke_color='white'))
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
          if (len(word) == len(w)):
             # if sorted char arrays are same
             if (sorted(word) == sorted(w)):
               dict_anagrams[word].append(w)
      for word, values in dict_anagrams.items():
        if len(values) == 1 and values.pop() == word:
          b = list(word)
          random.shuffle(b)
          dict_anagrams[word] = [''.join(b)]
        if word in values:
          values.remove(word)
      return dict_anagrams
    except (AttributeError):
      print(traceback.format_exc())
      return None
      
  def dirs(self, board, y, x, length=None):
      """fast finding of all directions from starting location
      optional masking of length
      TODO change to finding coordinates, then use those to slice
      readability is sacrificed for speed
      
      """
      # get all indices  of board 
      #[[[r0, c0], [r1, c0].. ], [[r0, c1], [r1, c1] ]] etc
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
    # self.update_board()
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
        
        # self.delta_t('get')
        # self.q.task_done()
        if isinstance(data, (tuple, list, int)):
          coord = data  # self.gui.ident(data)
          break
        else:
          try:
            # print(f' trying to run {data}')
            data()
          except (Exception) as e:
            print(traceback.format_exc())
            print(f'Error in received data {data}  is {e}')
    return coord
  
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board,
    returns the coordinates of the move
    Allows for movement over board"""
    # self.delta_t('start get move')
    if board is None:
        board = self.game_board
    coord_list = []
    # sit here until piece place on board
    items = 0
    
    while items < 1000:  # stop lockup
      
      move = self.wait_for_gui()
      # if items == 0:
      #     st = time()
      # print('items',items, move)
      try:
        if self.log_moves:
          coord_list.append(move)
          items += 1
          if move == -1:
            # self.delta_t('end get move')
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
    # wait until closed by gui or new game
    while True:
      if not self.gui.v.on_screen:
        print('View closed, exiting')
        return True
        
      if self.finished:  # skip if in game
        try:
          if not self.q.empty():
            item = self.q.get(block=False)
            if item == self.quit:
              return True
            item()
        except (Exception) as e:
          print(traceback.format_exc())
          print(e)
      
      sleep(0.5)

        
if __name__ == '__main__':
  g = LetterGame()
  g.run()
  while True:
    quit = g.wait()
    if quit:
      break
