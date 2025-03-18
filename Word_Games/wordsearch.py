# Wordsearch game - a classic
import os
import sys
from queue import Queue
from time import sleep
import random
import numpy as np
import traceback
import base_path
base_path.add_paths(__file__)
from word_square_gen import create_word_search
from Letter_game import LetterGame, Player
from gui.gui_interface import Gui, Squares, Coord
BLOCK = '#'
SPACE = ' '
WORDLIST = "wordsearch_list.txt"
GRIDSIZE = '19,19'
HINT = (-1, -1)
 
 
class WordSearch(LetterGame):
  
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
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart,
                            'Quit': self.quit})
    self.known_locs = []
    self.word_coords = {}
    
  def print_board(self):
    """
    Display the  players game board
    """
    display_words = [word.capitalize() for word in self.wordlist]
    try:
       max_len = max([len(word) for word in display_words]) + 1
    except ValueError:
       max_len = 10
    _, _, w, h = self.gui.grid.bbox
    if self.gui.gs.device.endswith('_landscape'):
        msg = self.format_cols(display_words, columns=2, width=max_len)
        self.gui.set_moves(msg, font=('Avenir Next', 25), anchor_point=(0,0),position=(w+40,0))
    elif self.gui.gs.device.endswith('_portrait'):
        msg = self.format_cols(display_words, columns=5, width=max_len)
        self.gui.set_moves(msg, font=('Avenir Next', 20), position=(0, h+40) )
    self.gui.update(self.board)
    
  def get_size(self):
     # note 20x20 is largest before tile image size is too small
     if self.table:
         gridsize = f'{len(self.table[0])},{len(self.table)}'
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
    if self.table is None:
        [self.board_rc((r, c), self.board, SPACE)
         for c in range(self.sizex) for r in range(self.sizey)]
        no_words_placed = 0
        for i in range(30):
            self.board, words_placed, self.word_coords = create_word_search(self.wordlist, size=self.sizex)
            # print(f'{i =}, {len(words_placed)}/{len(self.wordlist)}')
            if len(words_placed) > no_words_placed:
                best = self.board, words_placed, self.word_coords
                no_words_placed = len(words_placed)
                if len(words_placed) == len(self.wordlist):
                    break
        self.board, words_placed, self.word_coords = best
    else:
        letters = np.array([list(i.lower()) for i in self.table])
        self.board = letters
        self.gui.update(self.board)
        words_placed = self.wordlist
        for word in words_placed:
          coords = self.find_word(word)
          # print('np rc', self.find_word_np(word))
          self.word_coords[word] = coords
    self.gui.set_prompt(f'Placed {len(words_placed)}/{len(self.wordlist)} words')
    self.wordlist = words_placed
    self.all_words = [word.replace(' ', '') for word in self.wordlist]
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
            selection = self.gui.selection.lower()
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
              
  def match_word(self, move):
    """ match word to move"""
    word = []
    for rc in move:
      rc = Coord(rc)
      if self.check_in_board(rc) and isinstance(rc, tuple):
        word.append(self.get_board_rc(rc, self.board))        
    selected_word = ''.join(word)
    self.gui.clear_numbers(number_list=move)
    for word in self.wordlist:
      kword = word.replace(' ', '')
      kword = kword.lower()
      if kword == selected_word:
        self.wordlist.remove(word)
        self.known_locs.extend(move)
        self.gui.draw_line([self.gui.rc_to_pos(Coord(move[i]) + (-.5, .5))
                            for i in [0, -1]],
                           line_width=8, color='red', alpha=0.5)
        self.print_board()
        break
      else:
        self.gui.clear_numbers(number_list=move)
          
  def reveal(self):
      # reveal all words
      for word, coords in self.word_coords.items():
          if coords:
             self.gui.draw_line([self.gui.rc_to_pos(Coord(coords[i]) + (-.5, .5))
                                 for i in [0, -1]],
                                line_width=8, color='red', alpha=0.5)
          else:
             print('unplaced word', word)
          sleep(0.5)
      sleep(5)
      self.gui.show_start_menu()
      
  def restart(self):
    """ reinitialise """
    self.gui.gs.close()
    self.__init__()
    self.run()
            
  def game_over(self):
    """
    Checks if the game is over
    """
    return self.wordlist == []
    
  def hint(self):
      """ illuminate the start letter of a random unplaced word """
      word = random.choice(self.wordlist)
      word = word.replace(' ', '')
      coords = self.word_coords[word]
      # note that if start and end letter are same this will fail, but OK
      coord = coords[0] if word[0] == self.get_board_rc(coords[0], self.board) else coords[-1]
      self.gui.add_numbers([Squares(coord, '', 'cyan', z_position=30,
                            alpha=.5)],
                           clear_previous=False)
             
  def run(self):
    # LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    self.gui.clear_numbers()
    self.gui.clear_messages()
    self.gui.set_top(f'Wordsearch - {self.selection.capitalize()}')
    _, _, w, h = self.gui.grid.bbox
    if self.gui.device.endswith('_landscape'):
        self.gui.set_enter('Hint', position=(w + 50, -50))
    else:
        self.gui.set_enter('Hint', position=(w - 50, h + 50))
    self.word_locations = []
    
    self.initialise_board()
    self.print_board()
    
    while True:
      move = self.get_player_move(self.board)
      if move[0] == HINT:
        self.hint()
      move = self.process_turn(move, self.board)
      
      self.print_square(move, clear=False, alpha=0.2)
      sleep(1)
      self.match_word(move)
      # if finish:
      #  break
      if self.game_over():
       break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('')
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
    
  def find_word_np(self, word):
      word = list(word.lower())
      locs = np.argwhere(self.board == word[0])
      for rc in locs:
        r, c = rc
        all_dirs, indices = self.dirs(self.board, r, c, len(word))
        for dir in all_dirs:
          if len(dir) >= len(word):
             if all(dir[:len(word)] ==list(word)):
                return rc, indices
    
  def find_word(self, word):
      # for each word, find the first letter
      # then try in all directions to get second letter
      # if ok, keep going in that direction until word is complete
      # or letter is wrong.
      # then try other directions and then next occurrence of letter
      word = list(word.lower())
      locs = np.argwhere(self.board == word[0])
      for rc in locs:
          rc = Coord(rc)            
          for dir in rc.all_dirs:
              self.moves = [rc]
              rc_next = rc
              for letter in word[1:]:
                  rc_next = rc_next + dir
                  if not self.check_in_board(rc_next):
                      break
                  next = self.get_board_rc(rc_next, self.board)
                  if next == letter:
                      self.moves.append(rc_next)
                  else:
                      break  # next direction
                  if len(self.moves) == len(word):
                      return self.moves


if __name__ == '__main__':
  g = WordSearch()
  g.run()
 
  while True:
    quit = g.wait()
    if quit:
      break
  
