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
    self.PIECE_NAMES  =' abcdefghijklmnopqrstuvwxyz0123456789.'
    self.PIECES = [f'../gui/{k}.png' for k in self.PIECE_NAMES[:-1]]
    self.PIECES.append(f'../gui/@.png')
    self.PLAYERS = None

                                                     
SOUND = True
#WORDLISTS = [ 'letters5.txt'] 
WORDLISTS = ['5000-more-common.txt'] # 'letters3.txt', 'letters10.txt'] 
  

class LetterGame():
  
  def __init__(self):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = True
    self.straight_lines_only = True
    self.word_dict = None
    self.remaining_ships =[[]]
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
              
  def load_words_from_file(self, file_list):
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
        
  def load_words(self, word_length, file_list=None):
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
        
    word_list = [line for line in all_word_list  if len(line) == word_length]
      
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
     
  def get_possibles(self, match_pattern, max_possibles=None):
    ''' get a list of words matching match_pattern, if any
    from self.word_dict '''     
    
    known_words = [word.word for word in self.word_locations if word.fixed]
    m = re.compile(match_pattern)
    try:
        possibles = [word for word in self.all_word_dict[len(match_pattern)] 
          if  m.search(word) and word not in known_words]
        l= len(possibles)
        if max_possibles and l > max_possibles:
          possibles= possibles[0:max_possibles]
        if possibles:
            return len(possibles), possibles
        else:
            # print(f'could find {match_pattern} for req_letters')
            return None, match_pattern
    except(KeyError):
         print(match_pattern)
         print(traceback.format_exc())
         return None, match_pattern
         
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
                
  def compute_depths(self):
    """ find how many nodes to traverse before arriving  back at same word"""
    for node in self.word_locations:
        [w.set_visited(False) for w in self.word_locations if w is not node]
        visited = [item for item in self.word_locations if item.get_visited()]
        component = self.bfs(node, visited, stop=self.max_depth)  # Traverse to each node of a graph
        #path = [f'Node={node.index} item={item.index}, {item.start}' for item in component]  
    return component 
                    
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
      
  def fix_word(self, word_obj, text):   
     """ place a known word """ 
     if not word_obj.fixed:
       word_obj.set_word(text)
       word_obj.fixed = True
       self.populate_order.append(text)
       word_obj.match_pattern = text
       word_obj.update_grid('', self.board, text)
       if self.debug:
           print(f'Placed word {word_obj}')
       self.update_children_matches(word_obj)      
       for coord, child in word_obj.children.items(): 
         #print(child.match_pattern, type(child.match_pattern))
         child.update_grid('', self.board, child.match_pattern)
       
  def known(self):
    """ Find all known words and letters """
    known = []
    # get characters from empty board
    #written this wa to allow single step during debugging
    [known.append((r,c)) if self.get_board_rc((r,c), self.empty_board) != SPACE and self.get_board_rc((r,c), self.empty_board) != BLOCK  else None for r, rows in enumerate(self.empty_board) for c, char_ in enumerate(rows) ]
    #board = np.array(self.empty_board)
    #known = np.where(board!=BLOCK || board!#==SPACE)
    # now fill known items into word(s)
    if known:
      for word in self.word_locations:
        for k in known:
          if word.intersects(k) : # found one
            if all([wc in known for wc in word.coords]): # full word known
              word.set_word(''.join([self.get_board_rc(pos, self.empty_board) for pos in word.coords]))
              if self.debug:
                  print(f'>>>>>>>>>Set word from known {word}')
              word.match_pattern = word.word
              word.fixed = True
              break
      # now deal with indivdual letters
      # check each coordinate
      for coord in known:
        for word in self.word_locations:
          if word.intersects(coord) : # found one
            letter = self.get_board_rc(coord, self.empty_board)
            match = ''.join([letter if coord == c else '.' for c in word.coords])
            if word.match_pattern:
              word.match_pattern = self.merge_matches(word.match_pattern, match)
            else:
              word.match_pattern = match
            if self.debug:
                print('set word match  from known ', word.start, word.index, word.match_pattern)
    return known
    
  def merge_matches(self, a, b):
    ''' take two matches and combine them'''
    if a == '': return b
    elif b == '': return a
    else:
      return ''.join([y if x=='.' else x for x,y in zip(a,b)])    
     
  def update_children_matches(self, word_obj, clear=False):
    """ update the match patterns for children of current wordl
    eg if word = abacus and child1 intersects at pos 1 match for child is 'a.....' """
    parent_word = word_obj.word
    children_dict = word_obj.children
    intersections = word_obj.get_inter()
    coords = word_obj.coords
    for key, child in children_dict.items():
      if clear:
        child.match_pattern = ''
      else:        
        match = []
        for ichild in child.coords:
            l = '.'
            for p, letter in zip(word_obj.coords,parent_word):
                if ichild == p:
                    l=letter 
            match.append(l )
        match = ''.join(match)
        child.match_pattern = self.merge_matches(child.match_pattern, match)
        #if not child.fixed:
           #child.set_word(match)  # for testing
           #child.update_grid('', self.board, match)
            
  def calc_matches(self, word_obj, try_word=None):
    """ calculate the match patterns for children of current word
    eg if word = abacus and child1 intersects at pos 1 match for child is 'a.....' """
    if try_word is None:
        parent_word = word_obj.word
    else:
        parent_word = try_word 
    children_dict = word_obj.children
    intersections = word_obj.get_inter()
    coords = word_obj.coords
    c_dict ={}
    for key, child in children_dict.items():
        match = []
        for ichild in child.coords:
            l = '.'
            for p, letter in zip(word_obj.coords,parent_word):
                if ichild == p:
                    l=letter 
            match.append(l)
        match = ''.join(match)
        c_dict[key]= self.merge_matches(child.match_pattern, match)
    return c_dict
    
  def dfs(self, node, graph, visited, component, stop=None):
    component.append(node)  # Store answer
    node.visited = True  # Mark visited
    # Traverse to each adjacent node of a node
    for coord, child in node.children.items():
        if child is stop:
          return
        if not child.get_visited():  # Check whether the node is visited or not
            self.dfs(child, graph, visited, component, stop)  # Call the dfs recursively   
            
  def bfs(self, node, visited, stop=None): #function for BFS
    """ This will return all child node of starting node
    return is a list of dictianaries {'word_obj', 'depth' 'parent'} """
    queue = []
    component=[]
    component.append({'word_obj': node, 'depth':0, 'parent':None})
    node.visited = True
    queue.append((0,None,node))
    
    while queue:          # Creating loop to visit each node      
      depth, coord, item = queue.pop(0)      
      if depth >= stop:
        break   
      #print(f'Depth={depth} Item={item.index} item={item.start}')   
      for coord, child in item.children.items():
        if not child.get_visited():
          component.append({'word_obj': child, 'depth':depth + 1, 'parent':item})
          child.visited = True
          queue.append((depth + 1, coord, child))
    return component
            
  def search(self):
    graph = self.word_locations
    known = self.known()
    if known:
      for word in self.word_locations:
        if word.intersects(known[0]) : # found one
          node = word
          break
    else:
      node = self.word_locations[0]  # Starting node
    [w.set_visited(False) for w in self.word_locations]
    visited = [item for item in graph if item.get_visited()]
    component = []
    self.dfs(node, graph, visited, component)  # Traverse to each node of a graph
    path = [f'{item.index}, {item.start}' for item in component]
    if self.debug:
      print(f"Following is the Depth-first search:")  # Print the answer
      for p in path:
        print(p)
    for i, c in enumerate(component[1:]):
      self.word_locations[i-1].parent_node = c
    return component
    
  def _best_score(self, options):
      """place best choice from options
      the aim is place best word that allows other words to follow
      highest score wins, since this means greatest options for next level
      1000 means only one word fits at some level, so not a good choice
      need to avoid choosing  word that blocks an intersecting word
      options is dictionary of try_word, list of dictionary for intersections , score
      """
      scores =[(key, [v_[0][1] for _, v_ in v.items()]) for key, v in options]
      if self.debug:
          print(f'Scores________{len(scores)} words__________')
          [print(score) for score in scores]
      #def mx(n): return sum(n[1])
      # filter subwords not possible 
      scores1 =[score for score in scores if 0 not in score[1]]
      # filter only one option for subword
      scores2 =[score for score in scores1 if 1000 not in score[1]] # remove unique word
      # if result is empty, reinstate unique word
      if not scores2:
          scores2= scores1
      # still no good, reinstate not possible subword, since we' re probably at end of board fill
      if not scores2:
          scores2 = scores                                      
      s = sorted(scores2, key= lambda x: sum(x[1]), reverse=True)
      if self.debug:
          print(f'Scores filtered_____{len(s)} words__________')
          [print(score) for score in s]
      
      # choose shortest that is not zero
      try:
          # find all best that have same score
          first = sum(s[0][1])
          best = [word for word, score in s if sum(score) >= first - 5]
          if self.debug:
            print('best',best)
          select = random.choice(best)
      except(IndexError):
          return None
      return select
                     
  def _search_down(self, word, dict_parents,try_word=None, max_possibles=None):
        """ recursive function to establish  viabilty of options """
        # sets matches for all children of word using try_word
        #component.append({'try_word': try_word, 'word_obj': word, 'depth':0, 'parent':None})
        
        matches = self.calc_matches(word, try_word)
        found = defaultdict(list)
        for child, depth in dict_parents[word]:
            if child.fixed:
              continue
            coord = word.get_child_coord(child)
            match = matches[coord]        
            length, possibles  = self.get_possibles(match, max_possibles)
            #print(length, 'possible words for ', child.start, child.direction )
            if not length and not child.fixed:
                found[child].append((match, 0))
                
            elif length == 1:
                if not child.fixed:
                   found[child].append((possibles.pop(), 1000))
                   
            else:
              try:
                found[child].append((lprint(possibles,3), length)) # must be atleast 1
                #found[child].append((possibles,100 * depth + length)) # must be atleast 1
                for index, try_word in enumerate(possibles): 
                    #self.gui.set_message2(f'{index}/{length} possibles  at {child.start} trying {try_word}')
                    result = self._search_down(child, dict_parents, try_word, max_possibles)
                    found[child].extend(result)
              except(KeyboardInterrupt):
                  return None
                    
        return found # list of True, False for this top,level option
          
  def look_ahead_3(self, word, max_possibles=100):
    """ This uses breadth first search  to look ahead
       use max_possibles with a full word 
       list comprehensions are extensively used to allow simple stepove during debug
       for defined word puzzles. there is no guessing. there can be only one solution, so if a decision cannot be made in this iteration, it must be der
       deferred  to later.
       Use varaible max_possibles to switch between unconstrained and constrained puzzles """
    #self.update_board(filter_placed=True)
    #sleep(1) 
    
    [w.set_visited(False) for w in self.word_locations]
    [word.set_visited(True) for w in self.word_locations if w.fixed]
    visited = [item for item in self.word_locations if item.get_visited()]
    components = self.bfs(word, visited, stop=self.max_depth)
    if False: #self.debug:
      for c in components:
        try:
          print(f"{c['word_obj'].start}{c['word_obj'].direction}  depth={c['depth']} parent={c['parent'].start}{c['parent'].direction}")
        except:
          pass
    # now have  list of dictionaries {'word_obj', 'depth' 'parent'}
    # create dictionary of children of each parent
    
    # create a new dictionary using parent word as key
    dict_parents = defaultdict(list) 
    {dict_parents[c['parent']].append((c['word_obj'], c['depth'])) for c in components if c['parent'] is not None}    
    # {dict_parents[c['parent']].append(c['word_obj']) for c in components if c['parent'] is not None}   
    if self.debug:
        print('>Start', word) 
    #[print('parent ', k.start,k.direction,[str(f.start)+f.direction for f in v]) for k,v in dict_parents.items()]
    match = word.match_pattern    
    length, possibles  = self.get_possibles(match, max_possibles)
    if self.debug:
        print(length, 'possible words')
    options = []
    try:
        # simple solutions 
        if word.fixed:
          result = True
        # no word fits here
        elif length is None and not word.fixed:          
            result = False #print(f'wrong parent word {word.word} shouldnt be here')
        # only one word fits
        elif  length == 1:
            # only word. use it
            self.fix_word(word, possibles.pop()) 
            if self.debug:
                print('>>>>>>>>fix word line 701', word)
            result = True
        # ok now need to look ahead
        else: 
            options = []          
            max_component = []
            for index, try_word in enumerate(possibles):
              if self.debug:
                  self.gui.set_message(f'{index}/{length} possibles  at {word.start} trying {try_word}')
              result = self._search_down(word, dict_parents, try_word=try_word, max_possibles=max_possibles)   
              # need result to be greatest number of hits in order to best choose options    
              #if self.debug:
              #    print('Try Word ', try_word)
              #     [print('Key', k, v)  for k, v in result.items()]                             
              if result is None:
                if self.debug:
                    print('result is NoneXXXXXXXXXXXXXXXXXXXXXXXX')                
                return None
              if max_possibles:
                 if all(result):
                    options.append((try_word, result))
              else:                
                #if all(result):
                valid = True
                for i in result.values():
                  if len(i) == 1 and i.pop()[1] == 0:
                    valid = False
                    break # not valid
                if valid:
                   options.append((try_word, result))  
            #if self.debug:    
            #    print('result OPTIONS ',word, options)
            if len(options) == 1 and not word.fixed :
                self.fix_word(word, options.pop()[0])
                if self.debug:
                    print('>>>>>>>>>>fix word line 703 ', word)
                
                result = True 
                #print(f'try_word at {word.start} {try_word} {result}')
            elif options: #and max_possibles:
                # dealwith only one option is not zero              
                _options =[option for option in options if option[1] != 0]
                if len(_options) == 1:
                     self.fix_word(word, _options.pop()[0]) # already random
                     if self.debug:
                         print('>>>>>>>>>fix word line 773 from max options ', word)
                     return
                # deal with one option being large and all others = 100
                _options =[option for option in options if option[1] != 1000]
                if len(_options) == 1:
                     self.fix_word(word, _options.pop()[0]) # already random
                     if self.debug:
                         print('>>>>>>>>>fix word line 773 from max options ', word)
                     return
                     
                if max_possibles:
                    select = self._best_score(_options)
                    if select:
                       self.fix_word(word, select) # already random
                       if self.debug:
                          print('selectxxxxxxxxxxxxx', select)
                          print('>>>>>>>>>fix word line 773 from max options ', word)
  
    except(Exception, IndexError):
        print(locals())
        print(traceback.format_exc()) 
            
    finally:       
        return options # unplaced option   
               
  def get_next_cross_word(self, iteration, length_first=True, max_possibles=None):
    """ computes the next word to be attempted """
    
    def log_return(word):
        """ count the occurence of a word
        allows detection of unplaceable word
        """
        self.word_counter[word] += 1
        if self.word_counter[word] > 50:
          #word.fixed = True # dont try it again?
          if self.debug:
            print(f'Word {word} tried more than 50 times')
          #return word
          raise ValueError(f'Word {word} tried more than 50 times')
        else:
          return word
        
    if iteration == 0:  
      def longest():
        #def req(n): return n.length
        return sorted(self.word_locations, key= lambda x: x.length, reverse=False)   
      self.word_counter = Counter()
      if len(self.all_words) > 1000:
        max_possibles = max_possibles
      else:
        max_possibles = None 
      known = self.known() # populates word objects with match_pattern
      self.hints = list(set([word for word in self.word_locations for k in known if word.intersects(k)]))
      try:
        self.gui.set_moves('hints')
        return  log_return(self.hints.pop())     
      except(ValueError, IndexError):
        pass        
      try: 
        self.gui.set_moves('longest')
        return  log_return(longest()[-1])
      except (ValueError, IndexError):
        pass
      try:
        self.gui.set_moves('fixed')
        return  log_return([word for word in self.word_locations if word.fixed][0]) 
      except (ValueError):
        print('returned here')
        return None
             
      #wordlist = longest()      
      
    else:
        fixed =  [word for word in self.word_locations if word.fixed]
        if self.debug:
            self.gui.set_message(f' placed {len(fixed)} {iteration} iterations')
        
        fixed_weights = [5 for word in fixed]
        # create weight for all unplaced words based on word length
        #def req(n): return n.length
        unplaced = sorted([word for word in self.word_locations if not word.fixed], key=lambda x: x.length, reverse=True)
        unplaced_weights = [word.length for word in unplaced]
        
        unplaced_long_words = sorted( [word for word in unplaced if word.length > 6], key=lambda x: x.length)
         
        def match_size(n):
            return sum([i.isalnum() for i in n if '.' in n])
        # all match patterns except for full words
        patterned =  [word for word in self.word_locations if word.match_pattern and '.' in word.match_pattern]
        patterned_weights = [4 * match_size(match.match_pattern) for match in patterned]
        # so pick a random choice of words with patterns, followed by all unplaced words, with
        # reference for longest word
        try:
          # self.gui.set_moves('hints')
          return log_return( self.hints.pop())
        except(ValueError, IndexError):
          pass
        if length_first:
          try:
              # self.gui.set_moves('unplaced long')
              return log_return(unplaced_long_words.pop())
              #print(' unplaced long words', unplaced_long_words)
          except(ValueError, IndexError):  # no more long words
            pass
          try:
              # self.gui.set_moves('random patterned')
              return log_return(random.choices(patterned, weights=patterned_weights,k=1)[0])
              #return random.choices(patterned + unplaced, weights=patterned_weights + unplaced_weights,k=1).pop()
          except(ValueError, IndexError):
            pass
          try:
              # self.gui.set_moves('random')
              return log_return(random.choice(self.word_locations))
          except(ValueError):
              print('returned here')
              return None
              
        else: 
           try:
              # self.gui.set_moves('patterned and unplaced')
              #return random.choices(patterned, weights=patterned_weights,k=1)[0]
              return log_return(random.choices(patterned + unplaced, weights=patterned_weights + unplaced_weights,k=1).pop())
              #print(' unplaced long words', unplaced_long_words)
           except(ValueError, IndexError):  # no more long words
              pass
           try:
               # self.gui.set_moves('long words')
               return log_return(unplaced_long_words.pop())               
           except(ValueError, IndexError):
               pass
           try:
              # self.gui.set_moves('random')
              return log_return(random.choice(self.word_locations))
           except(ValueError):
              return None
 
         
  def populate_words_graph(self, length_first=True, max_iterations=2000, max_possibles=None):
    # for all words attempt to fit in the grid, allowing for intersections
    # some spaces may be known on empty board
    self.start_time = time()
    index = 0 
    self.populate_order = []
    while any([not word.fixed for word in self.word_locations]):
        fixed =  [word for word in self.word_locations if word.fixed]
        if self.debug:
            self.gui.set_message(f' placed {len(fixed)} {index} iterations')
        word = self.get_next_cross_word(index, max_possibles,length_first)   
        
        if word is None:
          if self.debug:
              try:
                print(f'options for word at {word.start} are {options}')
                print('possibles for stuck word', self.possibles)
              except(AttributeError):
                pass
          continue
            
        if self.debug:
          try:
            self.show_squares(word.coords)            
            self.gui.update(self.board)
            sleep(.25)  
          except(AttributeError):
            pass
        if index == max_iterations:
          break
        
        options = self.look_ahead_3(word, max_possibles=max_possibles) # child, coord)   
        if options is None:
          break                   
        index += 1
        
    fixed = [word for word in self.word_locations if word.fixed]   
    
    #self.update_board(filter_placed=False)
    if self.debug:
        self.gui.print_board(self.board)
        print('Population order ', self.populate_order)
    ptime = self.delta_t('time', do_print=False)
    msg = f'Filled {len(fixed)}/ {len(self.word_locations)} words in {index} iterations, {ptime}secs'
    words=len([w for w in self.word_locations if w.word])
    print('no words', words)
    print(msg)   
    self.gui.set_prompt(msg)
    self.gui.update(self.board) 
    
  
  def get_word(self, wordlist, req_letters, wordlength):
    ''' get a word matching req_letters (letter, position) '''
    match =['.'] * wordlength
    for req in req_letters:
      match[req[1]] = req[0] if req[0] != ' ' else '.'
    match = ''.join(match)
    #self.gui.set_moves(match)
    m = re.compile(match)
    possible_words = [word for word in wordlist if  m.search(word)]
    # remove already placed words
    
    if possible_words:
      try_word = random.choice(possible_words)
      self.score += 1
      return try_word, possible_words
    else:
      # print(f'could find {match} for req_letters')
      return match, None                        
      
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
    if hasattr(self, 'board'):
      selection = f'{len(self.board)},{len(self.board[0])}'
    else:
      if size is None:
        selection = console.input_alert("What is the dimension of the board (X, Y)? (Default is 5x5)\nEnter 2 numbers:")
      else:
        selection = size
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
    if hasattr(self, 'board'):
      pass
    else:
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
    
    while items < 200: # stop lockup
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
    self.finished = False
    self.SIZE = self.get_size() 
    self.gui = Gui(self.game_board, Player())
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(SIZE=30)
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





