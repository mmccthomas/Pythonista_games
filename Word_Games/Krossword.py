# Krossword game
# first letter position is given
# choose word from list to fit in a direction
# game is to choose the direction to fill the grid
# 1. read grid and words
# place numbered squares at each number in grid. leave alpha characters in grid
# 2. seperate words into dictionary with number as key
# 3. solve krossword using starting letter and match parameters
# 4. reset grid and allow play.
# 5. drag letters same as wordsearch, then select word from list.
# 6. challenge to display wordlists efficiently

import os
import sys
import re
from itertools import groupby
from queue import Queue
from time import sleep
import random
import numpy as np
import traceback
from copy import deepcopy
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from word_square_gen import create_word_search
from Letter_game import LetterGame, Player
from gui.gui_interface import Gui, Squares, Coord
BLOCK = '#'
SPACE = ' '
WORDLIST = "krossword.txt"
HINT = (-1, -1)
GRIDSIZE = '13,13'
 
 
class KrossWord(LetterGame):
  
  def __init__(self):
    
    # allows us to get a list of rc locations
    self.log_moves = True
    self.debug = False
    self.table = None
    self.straight_lines_only = True
    self.load_words_from_file(WORDLIST)
    self.get_size()  # just to provide board and sizex
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q  # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    
    self.gui.set_alpha(True)
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.selection = self.select_list()
    self.SIZE = self.get_size()
    self.gui.gs.DIMENSION_Y, self.gui.gs.DIMENSION_X = self.SIZE
    self.gui.setup_gui(log_moves=True)
    self.gui.build_extra_grid(self.gui.gs.DIMENSION_X, self.gui.gs.DIMENSION_Y,
                              grid_width_x=1, grid_width_y=1,
                              color='grey', line_width=1)
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'Reveal': self.reveal,
                             'Replay': self.replay,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart,
                            'Quit': self.quit})
    self.known_locs = []
    self.word_coords = {}
    self.moves = []
    self.checkpoints = []
    
  def find_possibles(self, start, word):
      start = Coord(start)
      #try all directions
      possible_direction = []
      for dirn in start.all_dirs:
          dirn = Coord(dirn)
          match = ['.' for _ in range(len(word))]
          match[0] = word[0] # first letter
          skip = False
          next = start + dirn
          for i in range(1, len(word)):                                
              if not self.check_in_board(next):
                  skip = True
                  break
              else:
                  l = self.board[next]
                  if l.isalpha():
                    match[i] = l
                  next += dirn
          if skip: 
              continue
                                        
          m = re.compile(''.join(match)) 
          if m.search(word):   
               possible_direction.append((dirn, match))
      return possible_direction 
      
  def print_possible(self, possibles):
    compass = {(-1, 0): 'N', (-1, 1): 'NE', (0, 1): 'E',  
               (1, 1): 'SE', (1, 0): 'S', (1, -1): 'SW', 
               (0, -1): 'W', (-1, -1): 'NW'}
    
    msg = ',\t'.join([compass[possible[0]] + '\t' + ' '.join(possible[1]) for possible in possibles])
    return msg
  
  def find_best_possible(self, word, possible_direction, no):
    """ 1. large number matches, relative to length of word
        2. match more than 1  in one direction but no others and no other word in group has match in that direction
        2. word would fill a gap with correct length
        3. word would fit when none of the other words would
        4. if no possible_direction, mistake made, we may need to go back - how?
    """
    def find_start(no):
      for start, no_str in self.start_dict.items():
        if no_str == str(no):
          return start
          
    def no_matches(match):
      return np.sum(np.char.isalpha(np.array(match)))
      
    def word_fills_gap(match, no, dirn):
      """ find start location from no
      start at start move len match in dirn
      if no space beyond extent or edge of board  then fills gap
      dirn already deals with case where word would not fit
      """
      word_matches = no_matches(match) > 1
      start = find_start(no)
      loc = start + dirn * (len(match) + 1)
      if self.check_in_board(loc):
         alpha = self.board[loc].isalpha()
         return alpha and word_matches
      else:
        return word_matches
          
    def word_fits_out_of_group(word, match, no, dirn):
      """word would fit when none of the other words would"""
      group = self.wordlist[int(no)] 
      start = find_start(no)
      fit = []
      for other_word in group:
        if other_word == word:
          word_matches = no_matches(match) > 2
          continue
        possibles = dict(self.find_possibles(start, other_word))
        try:
          m = possibles[dirn]       
          fit.append(no_matches(m) > 1)
        except (KeyError):
          continue
      if not any(fit):
        return word_matches
      return False
      
    for (d, match) in possible_direction:
       #if no_matches(match) >=2:
       #      return d, match
       fills = word_fills_gap(match, no, d)
       
       fits = word_fits_out_of_group(word, match, no, d)
       print(f'{fills =}, {fits = }')
       if fits:
          return d, match, 'pink'
       if fills:
          return d, match, 'cyan'
    return None, None, None                         
    
  def solve(self):    
    """solve the krossword
    suppose approach this as dfs
    at each point where guess is made, store the state.
    if get to end with squares still blank, note no blank squares.
    restore the state and restart the solve """
    self.empty_board = self.board.copy()
    self.wordlist_original = deepcopy(self.wordlist)
    placed = 1
    iteration = 0
    total_placed = 0
    enable_best_guess = False
    while placed:
      placed = 0
      iteration += 1
      print(f'{iteration = }, best_guess={enable_best_guess}')
      for start, no in self.start_dict.items():
        #for each start location , load the words for that location 
        # for each direction  then calculate a match word to encode existing letters
        # if match, put unto list of possible direction
        # if only one possible direction, place it
        # TODO what to do if there is more than one possible?
        # could try and mark location to revert?
        # trigger might be no possible directions
        
        start = Coord(start)
        try:
          words = self.wordlist[int(no)]
          for word in sorted(words, key=len, reverse=True):
            
            possible_direction = self.find_possibles(start, word)
            if possible_direction is None:
            	return False
            print()
            print(start, no, word, self.print_possible(possible_direction))
            # try only one possible
            # or only one with match having more than one alpha
            dirn = None            
            if len(possible_direction) == 1:
               dirn, _ = possible_direction.pop()
               color = 'orange'
               print('only one', word, no)
            else:
              if enable_best_guess:
                dirn, match, color = self.find_best_possible(word, possible_direction, no)
              if dirn:
                 print('best match', word, no, match)
                 
              
            if dirn: 
               self.moves.append((self.board.copy(), deepcopy(self.wordlist))) 
               if color != 'orange':
                   self.checkpoints.append((len(self.moves), dirn))
               for index, letter in enumerate(word):
                self.board[start + dirn * index] = letter
               self.wordlist[int(no)].remove(word)
               placed += 1
               total_placed += 1
               print(f'placed {word} at {start}')
               self.gui.update(self.board)
               coords = [start + dirn * index  for index in range(len(word))]
               self.highlight_(coords, color)
               sleep(.01)
               
        except (Exception) as e:
          print(traceback.format_exc())
          continue
      self.gui.set_message(f'Placed {placed} words on iteration {iteration}, {total_placed} total')
      
      if placed == 0 and total_placed != len(self.all_words) and iteration < 20:
         enable_best_guess = True
         placed = 1
      else:
        enable_best_guess = False
         
    #self.gui.set_message('')   
    self.solution = self.board.copy()
    self.gui.print_board( self.empty_board, 'initial')
    self.gui.print_board( self.solution, 'solution')
    self.board = self.empty_board
    self.wordlist = self.wordlist_original.copy()
    self.gui.update(self.board)  
    self.decode_moves()
  
  def decode_moves(self):
  	if self.checkpoints:
  		before = self.moves[self.checkpoints[0][0]][0]
  		after = self.moves[self.checkpoints[0][0] + 1][0]
  		changed_board = np.argwhere(after != before)
  		self.highlight_(changed_board, 'red')
  		
  def highlight_(self, coords, color):
    square_list = []
    for coord in coords:
      if Coord(tuple(coord)) in self.start_dict:
        text = self.start_dict[Coord(tuple(coord))]
      else:
        text = ''
      square_list.append(Squares(coord, text, color, z_position=30,
                                        alpha=0.5, font=('Avenir Next', 20),
                                        text_anchor_point=(-1.1, 1.2)))                        
    self.gui.add_numbers(square_list, clear_previous=False)      
                
  def print_board(self):
    """
    Display the  players game board, we neve see ai
    """
    display_words = self.wordlist
    msg = ''
    for k, v in display_words.items():
      msg += f'\n{k}\n'
      try:
          max_len = max([len(word) for word in v]) + 1
      except ValueError:
          max_len = 10
      msg += self.format_cols(v, columns=3, width=max_len)
      #msg += '\t'.join(v)
    
    #if self.gui.gs.device.endswith('_landscape'):
    #msg = self.format_cols(display_words, columns=2, width=)
    #    self.gui.set_moves(msg, font=('Avenir Next', 25))
    #elif self.gui.gs.device.endswith('_portrait'):
    #    msg = self.format_cols(display_words, columns=5, width=max_len)
    self.gui.set_moves(msg, font=('Avenir Next', 16))
    self.gui.update(self.board)
    
  def get_size(self):
     # note 20x20 is largest before tile image size is too small
     if self.table:
         gridsize = f'{len(self.table)},{len(self.table)}'
     else:
         try:
             if len(self.wordlist) > 40:
                 gridsize = '20,20'
             else:
                 gridsize = GRIDSIZE
         except (AttributeError):
             gridsize = GRIDSIZE
     return LetterGame.get_size(self, gridsize)
  
  def initialise_board(self):
    def split_text(s):
         for k, g in groupby(s, str.isalpha):
             yield ''.join(g)
             
    board = [row.replace("'", "") for row in self.table]
    board = [row.split('/') for row in board]
    self.board = np.array(board)
    # deal with number/alpha combo
    number_letters = np.array([(r,c) for c in range(self.sizex) 
                               for r in range(self.sizey) 
                               if len(list(split_text(board[r][c])))>1])
    numbers = np.argwhere(np.char.isnumeric(self.board))
    self.start_dict = {}
    square_list = []
    for number in np.append(numbers, number_letters, axis=0):
      try:
         no, letter = list(split_text(self.board[tuple(number)]))
         self.board[tuple(number)] = letter
      except (ValueError) as e:
         no = self.board[tuple(number)]
         
      self.start_dict[Coord(tuple(number))] = no
      square_list.append(Squares(number, no, 'clear', z_position=30,
                                        alpha=0.5, font=('Avenir Next', 20),
                                        text_anchor_point=(-1.1, 1.2)))
                        
    self.gui.add_numbers(square_list)
    self.board[np.char.isnumeric(self.board)] = SPACE
    
    # split the words and numbers into dictionary
    key = None
    w_dict = {}
    w_list = []
    for word in self.wordlist:
      # skip comment
      if word.startswith('#'):
        continue
      if word.isnumeric():
        if key:
          w_dict[key] = w_list # remove empty string
          w_list = []
        key = int(word)        
      else:
        w_list.append(word)
    w_dict[key] = w_list # remove empty string   
                                                             
    self.gui.update(self.board)   
    self.wordlist = w_dict
    self.all_words = [word for words in self.wordlist.values() for word in words]
    self.gui.set_prompt(f'Placed {len(w_dict.values())} groups, {len(self.all_words)} words')
    return
  
  def get_words(self):
    ''' construct subsets of words for each required length
    Use setattr to construct named word sublists '''
    words = self.all_words
    for length in range(self.min_length, self.max_length + 1):
      setattr(self, f'words_{length}', {w for w in words if len(w) == length})
      filelist = getattr(self, f'words_{length}')
      print(f'Wordlist length {length} is {len(filelist)}')
  
  def select_list(self):
      '''Choose which category'''
      items = [s.capitalize() for s in self.word_dict.keys()]
      items = [item for item in items if not item.endswith('_frame')]
      # return selection
      self.gui.selection = ''
      selection = ''
      prompt = ' Select category'
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800, 0))
        while self.gui.text_box.on_screen:
          try:
            selection = self.gui.selection.capitalize()
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
            
        if len(selection) > 1:
          self.wordlist = self.word_dict[selection]
          if selection + '_frame' in self.word_dict:
             self.table = self.word_dict[selection + '_frame']
          self.wordlist = [word.lower() for word in self.wordlist]
          self.gui.selection = ''
          return selection
        elif selection == "Cancelled_":
          return False
        else:
            return False
            
  def process_turn(self, move, board):
    """ process the turn
    """
    #self.delta_t('start process turn')
    def uniquify(moves):
      """ filters list into unique elements retaining order"""
      return list(dict.fromkeys(moves)) 
           
    def strike(text):
      result = ''
      for c in text:
          result = result + c + '\u0336'
      return result
          
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
            start = move[0]
            item_list = self.wordlist[int(self.start_dict[start])]
            prompt = f"Select from {len(item_list)} items"
            if len(item_list) == 0:
               raise (IndexError, "list is empty")
      
             
            # return selection
            self.gui.selection = ''
            selection = ''
            while self.gui.selection == '':
              self.gui.input_text_list(prompt=prompt, items=item_list, position=(800, 0))
              while self.gui.text_box.on_screen:
                try:
                  selection = self.gui.selection.lower()
                  selection_row = self.gui.selection_row
                except (Exception) as e:
                  print(e)
                  print(traceback.format_exc())
                  
              if selection in item_list and len(move) == len(selection):
                self.gui.selection = ''
                
                # store board and wordlist before this move
                self.moves.append((self.board.copy(), deepcopy(self.wordlist)))
                
                if self.debug:
                    print('letter ', selection, 'row', selection_row)
                for coord, letter in zip(move, selection):
                  self.board[coord] = letter
                #strike thru text
                if all([self.board[coord] == self.solution[coord] for coord in move]):
                   word =self.wordlist[int(self.start_dict[start])][selection_row]
                   word = strike(word)
                   self.wordlist[int(self.start_dict[start])][selection_row] = word
                   self.print_board()
                
                self.gui.update(self.board)  
                return
              elif selection == "Cancelled_":
                return
              else:
                return            
        except (Exception):
              """ all_words may not exist or clicked outside box"""
              if self.debug:
                print(traceback.format_exc())
              return
              
  
  def reveal(self):
      # reveal all words
      self.gui.update(self.solution)
      
      sleep(5)
      #self.gui.show_start_menu()
      
  def restart(self):
    """ reinitialise """
    self.gui.gs.close()
    self.__init__()
    self.run()
            
  def game_over(self):
    """
    Checks if the game is over
    """
    return np.all(self.board == self.solution)
    
  def undo(self):
    """ reverse changes"""      
    try:
       self.board, self.wordlist = self.moves.pop()
       self.gui.update(self.board)
       self.print_board()
    except (IndexError):
      return
      
  def replay(self):
    """ replay from stored moves"""
    self.gui.clear_numbers()      
    try:
       #self.moves.reverse()
       length = len(self.moves)
       for i in range(length):
           self.board, self.wordlist = self.moves[i]
           self.gui.update(self.board)
           self.print_board()
           sleep(1)
    except (IndexError):
      return
      
  def run(self):
    # LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    self.gui.clear_numbers()
    self.gui.clear_messages()
    self.gui.set_top(f'Krossword - {self.selection} orange=only pink=fits, cyan=fills')
    _, _, w, h = self.gui.grid.bbox
    if self.gui.device.endswith('_landscape'):
        self.gui.set_enter('Undo', position=(w + 50, -50))
    else:
        self.gui.set_enter('Undo', position=(w - 50, h + 50))
    self.word_locations = []
    
    self.initialise_board()
    self.print_board()
    error = self.solve() 
    if error == False:
    	raise IndexError
    while True:
      move = self.get_player_move(self.board)
      if move[0] == HINT:
        self.undo()
      move = self.process_turn(move, self.board)
  
      # if finish:
      #  break
      #if self.game_over():
      # break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('')
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
    

if __name__ == '__main__':
  g = KrossWord()
  g.run()
 
  while True:
    quit = g.wait()
    if quit:
      break
  
























