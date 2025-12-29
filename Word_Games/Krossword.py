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
from time import sleep, time
import random
import numpy as np
import traceback
import inspect
from copy import deepcopy
#import generate_fiveway
from word_square_gen import create_word_search
from Letter_game import LetterGame, Player, Word
from gui.gui_interface import Gui, Squares, Coord
from setup_logging import logger, is_debug_level
BLOCK = '#'
SPACE = ' '
WORDLIST = "wordlists/words_10000.txt"
HINT = (-1, -1)
GRIDSIZE = '13,13'
 
 
class KrossWord(LetterGame):
  
  def __init__(self):
    self.wordfile = 'krossword.txt'
    # allows us to get a list of rc locations
    self.strikethru = True
    self.log_moves = True
    self.max_iteration = 1000
    self.table = None
    self.straight_lines_only = True
    self.get_size()  # just to provide board and sizex
    # load the gui interface
    self.gui = Gui(self.board, Player())
    self.gui.q = Queue()
    self.gui.set_alpha(True)
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.SIZE = self.get_size()
    self.gui.DIMENSION_Y, self.gui.DIMENSION_X = self.SIZE
    self.gui.setup_gui(log_moves=True)
    self.gui.orientation(self.display_setup)
    self.gui.build_extra_grid(self.gui.DIMENSION_X, self.gui.DIMENSION_Y,
                              grid_width_x=1, grid_width_y=1,
                              color='grey', line_width=1)
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'New Game': self.restart,
                             'Reveal': self.reveal,
                             'Replay': self.replay,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart,
                            'Quit': self.quit})
 
    self.moves = []
    self.valid_dirns = [0, 1, 2, 3, 4, 5, 6, 7]
    self.iteration_counter = 0
    self.placed = 0    
 
  def display_setup(self):
    """set positions of display
    elements for different device
    sizes
    This is called also when devis is rotated
    """
    W, H = self.gui.get_device_screen_size()
    self.gui.device = self.gui.get_device()
    x, y, w, h = self.gui.grid.bbox
    if W > H:    
           self.gui.set_enter('Undo', position=(w + 50, -50))
           self.start_menu_pos = (w+250, h)
           position_puzzles = (w+10, 0)
    else:       
           self.gui.set_enter('Undo', position=(w - 50, h + 50))
           self.start_menu_pos = (w-50, h+50)
           position_puzzles = (w/2, h)
       
    self.gui.gs.pause_button.position = (32, H - 36)   
    self.gui.set_top(self.gui.get_top(),
                     position=(0, h+25))
    self.gui.set_moves(self.gui.get_moves(),
                       anchor_point=(0, 0),
                       position=position_puzzles) 
                       
  def ix(self, tuple_list):
     """ create a numpy index that can be used directly on 2d array """
     return tuple(np.array(tuple_list).T)         
     
  def update_matches(self, board=None):
      """update matches list in start_coords dictionary 
      matches are from start location to edge of board
      structure
       {letter: {words: [wordlist], coords: {Coord: [matches], Coord: [matches], ...}}"""
      if board is None:
        board = self.board
      for letter, letter_dict in self.start_dict.items():
          for start, matches in letter_dict['coords'].items():
              all_dirs = [start.all_dirs[i]  for i in self.valid_dirns]
              for index, dirn in enumerate(all_dirs):
                  dirn = Coord(dirn)
                  match = board[start]
                  next = start + dirn       
                  while True:                                        
                      if not self.check_in_board(next):
                          break
                      else:
                          l = board[next]
                          if l.isalpha():
                            match += l
                          else:
                            match += '.'
                      next += dirn                 
                  matches[index] = match                  
      return 
 
  def find_possibles(self, word, pos=None):
       possibles = [] 
       if pos is None:
         pos = word[0]
       else:
         pos = str(pos)  
       for coord, matches in self.start_dict[pos]['coords'].items():
           
               word_len = len(word)
               for index, match in enumerate(matches):
                   if len(match) < word_len:
                       continue
                   elif word == match[:word_len]:
                     # found complete match
                     # TODO this can find very rare false positives where placed words
                     # just happens to satisfy word to be yet placed
                     # this is flagged when wordlist is empty but not all squares filled
                     return [(coord, index, word, pos)]
                   else:
                       m = re.compile(match[:word_len])
                       if m.search(word):
                           possibles.append((coord, index, word, pos))
       return  possibles
      
  def board_is_full(self):
    """board is full
    OR no words left in wordlist """
    board_full = np.all(np.char.isalpha(self.board))
    wordlist = [word for words in self.wordlist.values() for word in words]
    wordlist_empty = len(wordlist)== 0
    if wordlist_empty:
      logger.debug(f'All words used, {board_full=}')
    return board_full or wordlist_empty
  
  def word_is_full(self, possibles):
       """ check if possible already contains filled word"""       
       for possible in possibles:
           start, index, word, pos = possible
           match = self.start_dict[pos]['coords'][start][index]
           if match[:len(word)] == word:
              return True
       return False
            
  def print_possible(self, possibles):
    compass = {(-1, 0): 'N', (-1, 1): 'NE', (0, 1): 'E',  
               (1, 1): 'SE', (1, 0): 'S', (1, -1): 'SW', 
               (0, -1): 'W', (-1, -1): 'NW'}
    
    msg = ',\t'.join([compass[possible[0]] + '\t' + ' '.join(possible[1]) for possible in possibles])
    return msg
    
  def fewest_matches(self):
        """Finds the slot that has the fewest possible matches, this is probably the best next place to look."""
        fewest_possibles = []
        fewest_matches = max(self.SIZE) + 1
        for position, contents in self.wordlist.items():
            for word in contents[:]:
                possibles = self.find_possibles(word, pos=position)
                
                if len(possibles) > 0:
                  # known complete beginning word
                  if self.word_is_full(possibles):
                       return [possibles.pop()], 1
                  if len(possibles) < fewest_matches:
                    fewest_matches = len(possibles)
                    fewest_possibles = possibles
        if len(fewest_possibles) == 0:
          fewest_matches = 0
        return fewest_possibles, fewest_matches     
        
  def get_word(self, start,  direction):
    for word in self.word_locations:
        if  word.start == start and word.direction.lower() == direction.lower():
          return word
    
  def place_word(self, possible, previous=False):
      """ fill board
      if previous is True, fill with match """
      compass = {(-1, 0): 'N', (-1, 1): 'NE', (0, 1): 'E',  
               (1, 1): 'SE', (1, 0): 'S', (1, -1): 'SW', 
               (0, -1): 'W', (-1, -1): 'NW'}
      start, index, word, position = possible
      
      
      dirn =  Coord([start.all_dirs[i]  for i in self.valid_dirns][index])
      if is_debug_level():
         msg = f'{"Removed" if previous else "Placed"} {word}@{start}_{compass[tuple(dirn)]}'
         self.gui.set_message(msg)
         print(msg)
      if not previous:
          for index, l in enumerate(word):
              self.board[start + dirn * index] = l
              self.letter_board[start + dirn * index] = l
          w = Word(rc=start, direction=compass[tuple(dirn)].lower(), length=len(word), word=word)
          self.word_locations.append(w)
          try:             
              self.start_dict[position]['words'].remove(word)
              self.wordlist[position].remove(word)
          except (ValueError):
            pass
          except (KeyError):
            #try:
                self.wordlist[None].remove(word)
            #except ValueError:
            # pass
          self.placed += 1          
      else:
          # board has already reverted
          try:
              self.start_dict[position]['words'].append(word)
              self.wordlist[position].append(word)
              self.word_locations.remove(self.get_word(word,compass[tuple(dirn)].lower()))
              
          except (KeyError, ValueError) as e:
             pass
             self.wordlist[None].append(word)
          self.placed -= 1
          
      if is_debug_level():
         
         self.gui.print_board(self.board, f'stack depth= {len(inspect.stack(0))} iteration {self.iteration_counter}')        
         self.gui.update(self.board)
         print('\n\n')
         #sleep(0.1)
      self.update_matches(self.letter_board)  
          
  def no_locs_filled(self):
      latest = self.board.size - len(np.argwhere(self.board == ' '))
      return latest  
                                    
  def fill(self):
        self.iteration_counter += 1
        if self.iteration_counter >= self.max_iteration:
          return True
        # if the grid is filled, succeed if every word is valid and otherwise fail
        if self.board_is_full():
            return True

        # choose position with fewest matches
        possibles, num_matches = self.fewest_matches()
        
        if num_matches == 0:
          logger.debug('no matches, backing up')
          return False
        
        # iterate through all possible matches in the fewest-match slot
        #store a copy of the current board
        previous_board = self.board.copy()
        # store best filled board for later debug
        if self.no_locs_filled() > self.best_filled:
            self.best_filled = self.no_locs_filled()
            self.best_filled_board = self.board.copy()
            
        previous_letter_board = self.letter_board.copy()
        
        logger.debug(f'remaining words {self.wordlist}')
        logger.debug(f'{possibles=}')
        for i, possible in enumerate(possibles):
            logger.debug(f'iteration {i}')
            self.place_word(possible)
            # now proceed to next fewest match
            if self.fill():
                return True
            # back here if match failed
            # if no match works, restore previous word and board
            self.board = previous_board
            self.letter_board = previous_letter_board
            # cancel the placement
            self.place_word(possible, previous=True)

        return False
                     
  def solve(self):    
    """solve the krossword
    use dfs search.
    """  
    self.word_locations = []
    t = time()
    self.best_filled = 0
    self.fill()
    solve_time = time() - t
    complete = 'Board Complete' if self.board_is_full() else 'Board not Complete'
    msg = f'Placed {self.placed} words ,{complete} in {self.iteration_counter} iterations, {solve_time:.3f}secs'
    if not self.board_is_full():
      self.gui.print_board(self.best_filled_board, which='best filled board for debug')
    self.gui.set_prompt(msg)
    self.gui.set_message('')   
    self.solution = self.board.copy()
    self.board = self.empty_board
    self.wordlist = self.wordlist_original.copy()
    self.gui.update(self.board) 
    return msg
    
  def print_board(self, remove=None):
    """
    Display the  players game board
    """
    display_words = self.wordlist
    
    msg = ''
    for k, v in display_words.items():
      try: 
         v.remove(remove)
      except (ValueError):
          pass
      if k:
          msg += f'\n{k}\n'
      try:
         # word length for only alphanumeric characters ( not strrikethru)
          max_len = max([sum([c.isalnum() for c in word]) for word in v]) + 2                    
      except ValueError:
          max_len = 10
      v = [word.capitalize() for word in v]
      msg += self.format_cols(v, columns=3, width=max_len+1)
      #msg += '\t'.join(v)
    
    #if self.gui.device.endswith('_landscape'):
    #msg = self.format_cols(display_words, columns=2, width=)
    #    self.gui.set_moves(msg, font=('Avenir Next', 25))
    #elif self.gui.device.endswith('_portrait'):
    #    msg = self.format_cols(display_words, columns=5, width=max_len)
    self.gui.set_moves(msg, font=('Avenir Next', 18))
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
     
  def create_wordlist_dictionary(self):
      # split the words and numbers into dictionary
      key = None
      w_dict = {}
      w_list = []
      for word in self.wordlist:
        # skip comment
        if word.startswith('#'):
          continue
        if word.isnumeric(): # key for krossword
          if key:
            w_dict[key] = w_list # remove empty string
            w_list = []
          key = word      
        else:
          w_list.append(word)
      w_dict[key] = w_list # remove empty string   
      
      return w_dict
    
  def initialise_board(self):
    """ For krossword board text may be number or number letter
        For fiveways board text may only be letter
    create start_dict with structure
    {: {words: [wordlist], coords: {Coord: [matches], Coord: [matches], ...}}"""
        
    def split_text(s):
         for k, g in groupby(s, str.isalpha):
             yield ''.join(g)
    """        
    if self.selection == "New":
        try:
            cx = generate_fiveways.Cross()
            cx.all_start_coords = cx.get_starts(self.wordfile)
            word_dict, _ = cx.load_words(filename=WORDLIST)  
            cx.board = np.full(self.SIZE, ' ')
            best = cx.create_krossword_dfs(word_dict, self.sizey, None, None, iterations=3)
            kross = cx.decode_krossword(best.word_locs)
            self.board = np.full(self.SIZE, '  ')
            #self.board = cx.board
            numbers = cx.start_locs
            self.gui.add_numbers([Squares(number, no+1, 'yellow', z_position=30,
                                          alpha=0.5, font=('Avenir Next', 18),
                                          text_anchor_point=(-1.1, 1.2))
                                  for no, number in enumerate(numbers)])
            self.start_dict = {}                     
             
            w_dict = kross  
            for (no, words), coord in zip(kross.items(), numbers):
              self.start_dict[str(no)] = {'words': words, 'coords': {coord: ['' for word in words]}}    
    
            self.letter_board = self.board.copy()
            self.letter_board[self.ix(numbers)] = cx.board[self.ix(numbers)]
        except NameError:
           pass
           
    else:
    """
    if True:
        board = [row.replace("'", "") for row in self.table]
        board = [row.split('/') for row in board]
        self.board = np.array(board)
        # deal with number/alpha combo
        number_letters = np.array([(r,c) for c in range(self.sizex) 
                                   for r in range(self.sizey) 
                                   if len(list(split_text(board[r][c])))>1])
                                   
        numbers = np.argwhere(np.char.isnumeric(self.board))
        w_dict = self.create_wordlist_dictionary()
        self.start_dict = {}
        square_list = []
        for number in np.append(numbers, number_letters, axis=0):
          try:
             no, letter = list(split_text(self.board[tuple(number)]))
             self.board[tuple(number)] = letter
          except (ValueError) as e:
             no = self.board[tuple(number)]
             
          self.start_dict[no] = {'words': [], 'coords': {Coord(tuple(number)): ['' for _ in range(len(self.valid_dirns))]}}             
          #self.start_dict[Coord(tuple(number))] = no
          
          square_list.append(Squares(number, no, 'yellow', z_position=30,
                                            alpha=0.5, font=('Avenir Next', 18),
                                            text_anchor_point=(-1.1, 1.2)))                     
        self.gui.add_numbers(square_list)
        # number clues display as blank
        self.board[np.char.isnumeric(self.board)] = SPACE
      
        # letter board is invisble version of board, 
        # where numbers have been replaced by start letter
        # we dont want to see equivalent letters on board, but solver needs them
        self.letter_board = self.board.copy()
        for k, words  in w_dict.items():
          self.start_dict[str(k)]['words'] = words
          # get equivalent letter for number.                               first letter of first word
          try:
              self.letter_board[list(self.start_dict[(str(k))]['coords'].keys())[0]] = words[0][0]
          except (IndexError, TypeError):
              pass
                                                                                                                     
    self.gui.update(self.board)   
    self.wordlist = w_dict
    self.all_words = [word for words in self.wordlist.values() for word in words]
    self.gui.set_prompt(f'Placed {len(w_dict.values())} groups, {len(self.all_words)} words')
    self.update_matches(self.letter_board)
  
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
                    
        if selection == "Cancelled_":
          selection = random.choice(items)
          self.wordlist = self.word_dict[selection]
          if selection + '_frame' in self.word_dict:
             self.table = self.word_dict[selection + '_frame']
          self.wordlist = [word.lower() for word in self.wordlist]
          self.gui.selection = ''
          return selection
        elif selection == 'New':
          self.gui.selection = ''
          return selection
        elif len(selection) > 1:
          self.puzzle = selection
          self.wordlist = self.word_dict[selection]
          if selection + '_frame' in self.word_dict:
             self.table = self.word_dict[selection + '_frame']
          self.wordlist = [word.lower() for word in self.wordlist]
          self.gui.selection = ''
          return selection
        else:
            return False
            
  def process_turn(self, move, board, test=None):
    """ process the turn
        provide test as selection to skip input list
    """
    #self.delta_t('start process turn')
    def uniquify(moves):
      """ filters list into unique elements retaining order"""
      return list(dict.fromkeys(moves)) 
           
    def strike(text):
      """ convert all letters to strikethru """
      result = ''
      for c in text:
          #.                    minus sign below  striketrhu
          result = result + c + '\u0320' + '\u0336'
      return result
          
   # try to deal with directions 
    if isinstance(move, list):
        # lets count no of unique coordinates to see how long on each square
        move.pop(-1) # remove terminator
        if self.straight_lines_only:
          move = self.predict_direction(move)
        else:
          move = uniquify(move)        
        
        try:
              start = move[0]
              for index, letter_dict in self.start_dict.items():
                  if Coord(start) in list(letter_dict['coords'].keys()):
                    break                
              try:    
                  item_list = self.wordlist[index]
              except (KeyError): # for Fiveways
                 item_list = [l for l in self.wordlist[None] if l.startswith(self.board[start])]
                 
              prompt = f"Select from {len(item_list)} items"
              if len(item_list) == 0:
                 raise (IndexError, "list is empty")
      
              if test is None: 
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
              else:
                   selection, selection_row = test
                  
              if selection in item_list and len(move) == len(selection):
                self.gui.selection = ''
                
                # store board and wordlist before this move
                self.moves.append((self.board.copy(), deepcopy(self.wordlist)))
                
                logger.debug(f'letter {selection}, row {selection_row}')
                for coord, letter in zip(move, selection):
                  self.board[coord] = letter
                self.move = move   
                #check if correct
                if all([self.board[coord] ==self.solution[coord] for coord in move]):                 
                   word = item_list[selection_row]      
                                                                   
                   #strikethru or remove from list    
                   if self.strikethru:
                       try:
                           self.wordlist[index][selection_row] = strike(word)
                       except (KeyError): # for Fiveways
                           self.wordlist[None][self.wordlist[None].index(word)] = strike(word)           
                       self.print_board()
                   else:
                        self.print_board(remove=word)                                  
                self.gui.update(self.board)  
                return
                
              elif selection == "Cancelled_":
                return
              else:
                return            
        except (Exception):
              """ all_words may not exist or clicked outside box"""
              logger.debug(f'{traceback.format_exc()}')
              return
              
  
  def reveal(self):
      # reveal all words
      self.gui.update(self.solution)
      for word in self.word_locations:
          #self.gui.draw_line([self.gui.rc_to_pos(Coord(word.coords[i]) + (-.5, .5))
          #                    for i in [0, 1]],
          #                   line_width=10, color='green', alpha=0.8)         
          self.gui.draw_line([self.gui.rc_to_pos(Coord(word.coords[i]) + (-.5, .5))
                                 for i in [0, -1]],
                                line_width=8, color='red', alpha=0.5)         
      
      sleep(3)
      self.gui.show_start_menu(menu_position=self.start_menu_pos)
      
      
  def restart(self):
    """ reinitialise """
    self.gui.close()
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
       for move in self.moves:
           self.board, self.wordlist = move
           self.gui.update(self.board)
           self.print_board()
           sleep(1)
    except (IndexError):
      return
      
  def run(self):
    """
    Main method that prompts the user for input
    """
    self.gui.clear_numbers()
    self.gui.clear_messages()
    self.load_words_from_file(self.wordfile)
    self.selection = self.select_list()
    self.gui.set_top(f'{self.__class__.__name__} - {self.selection}')
    self.display_setup()
    self.word_locations = []
    
    self.initialise_board()
    self.print_board()
    self.empty_board = self.board.copy()
    self.wordlist_original = deepcopy(self.wordlist)
    self.solve() 
    # user interaction loop
    while True:
      move = self.get_player_move(self.board)
      if move[0] == HINT:
        self.undo()
      move = self.process_turn(move, self.board)

      if self.game_over():
         break
    
    self.gui.set_message2('Game over')
    self.complete()
    

if __name__ == '__main__':
  g = KrossWord()
  g.run()
 
  while True:
    quit = g.wait()
    if quit:
      break



