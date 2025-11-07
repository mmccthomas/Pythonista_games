# Quoteword game
# fit a quote of less than 144 characters into 12 x 12 grid
# use textwrap to split the quote
# take each 3x3 tile and scramble the letters
# "list the scrambled letters and where they fit in 4x4 grid
# choose a set of letters by touching grid. letters fill.
# then swap letters to make the words

from time import sleep
from PIL import Image
import ui
import io
import numpy as np
import textwrap
import random

from types import SimpleNamespace
from Letter_game import LetterGame
import gui.gui_scene as gscene
from gui.gui_scene import Tile
from gui.gui_interface import Coord
from setup_logging import logger
PUZZLELIST = "quoteword.txt"
TILESIZE = 3


class QuoteWord(LetterGame):
  
  def __init__(self):    
    LetterGame.__init__(self, column_labels_one_based=True)
    self.first_letter = False
    self.tiles = None
    self.load_words_from_file(PUZZLELIST, no_strip=True) 
    self.selection = self.select_list()
    if self.selection is False:
       self.gui.show_start_menu()
       return 
    self.gui.build_extra_grid(4, 4, grid_width_x=3, grid_width_y=3,
                              color='red', line_width=5)
    self.gui.build_extra_grid(12, 12, grid_width_x=1, grid_width_y=1,
                              color='black', line_width=2)                        
    
       
    x, y, w, h = self.gui.grid.bbox
    
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'New ....': self.restart,
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.span = self.sizex // TILESIZE
    self.rack, msg = self.display()
    
    self.gui.clear_messages()
    self.gui.set_enter('', stroke_color='black') # hide box
    self.gui.set_moves(msg, position=(w + 50, h / 2), font=('Fira Mono', 20))
    self.gui.set_top(f'Pieceword no {self.selection.capitalize()}')
    self.finished = False
    
  def run(self):
    """
    Main method that prompts the user for input
    """    
    while True:
      move = self.get_player_move(self.board)
      move = self.process_turn(move, self.board)
      if self.game_over():
        break
    self.gui.set_message2('')
    self.complete()
    
  def select_list(self):
      '''Choose which category'''
      items = [s.capitalize() for s in self.word_dict.keys()]
      items = [item for item in items
               if (not item.endswith('_text') and not item.endswith('_frame'))]
      # return selection
      self.gui.selection = ''
      selection = ''
      prompt = ' Select puzzle'
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800, 0))
        while self.gui.text_box.on_screen:
          try:            
            selection = self.gui.selection.lower()
          except (Exception) as e:
            print(e)
        if selection == 'cancelled_':
          return False 
        if len(selection):
          logger.debug(f'{selection=}')
          self.wordlist = self.word_dict[selection]   
          self.gui.selection = ''
          return selection
        elif selection == "Cancelled_":
          return False
        else:
            return False
  
  def display(self):
      """ display tiles on board
      """
      text = self.wordlist[0].lower().replace(' ', '#')
      words_list = textwrap.wrap(text, width=12, break_long_words=True, max_lines=12)
      for r, row in enumerate(words_list):
        for c, char in enumerate(row):
          self.board[r][c] = char
      self.gui.update(self.board)  
      rack = {}
    
      self.board = np.array(self.board)
      self.solution = self.board.copy()
      for n in range(self.span * self.sizey//TILESIZE):
        coord = divmod(n, self.span)       
        line = self.get_tile(coord).reshape((1,-1))[0]
        np.random.shuffle(line)
        rack[coord] = line.copy()
      text = [] 
      for k,v in rack.items():
        v[~np.char.isalpha(v)] = ''
        coord = str(TILESIZE * k[0]+ 1) + 'ABCDEFGHIJKL'[k[1]*TILESIZE]
        text.append(f'{coord} {"".join(v)}')
      msg = '\n'.join(text)
      self.gui.print_board(self.board)  
      self.gui.update(self.board)
      self.board[np.char.isalpha(self.board)] = ' '
      self.gui.update(self.board)
                  
      return rack, msg
          
  def get_size(self):
    LetterGame.get_size(self, '12, 12')
    
  def load_words(self, word_length, file_list=PUZZLELIST):
    return
     
  def initialise_board(self):
    pass   
      
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board,
    returns the coordinates of the move
    Allows for movement over board"""
    
    move = LetterGame.get_player_move(self, self.board)
    
    if move[0] == (-1, -1):
       return (None, None), 'Enter', None  # pressed enter button
      
    point = self.gui.start_touch - self.gui.grid_pos
    # touch on board
    # Coord is a tuple that can support arithmetic
    rc_start = Coord(self.gui.grid_to_rc(point)) # // TILESIZE
    
    if self.check_in_board(rc_start):
      
        rc = Coord(move[-2]) // TILESIZE
        if self.board[rc_start] == ' ':
          if rc in self.rack:
            arr = self.rack[rc].copy()
            self.rack.pop(rc, None)
          return rc, arr, rc_start
        else:
          return Coord(move[-2]) , self.board[rc_start], rc_start
                           
    return (None, None), None, None
  
  def place_tile(self, origin, letter):
        #fill 3x3 tile with contents of letter array
        coord_ = Coord(origin) // TILESIZE
        coord_ = coord_ * TILESIZE
        self.gui.set_message(f'{origin}>{coord_}')
        pos_index, letter_index = 0, 0
        while True:
          r_, c_ = divmod(pos_index, TILESIZE)
          try:
            l = letter[letter_index]
            if l.isalpha():
              if  self.board[coord_ + (r_, c_)] == ' ':
                 self.board[coord_ + (r_, c_)] = l
                 letter_index += 1
              pos_index += 1
              
            else:
              letter_index +=1
          except (IndexError):
            break
                
  def get_tile(self, coord):
      r, c = coord
      return self.board[r * TILESIZE:r * TILESIZE + TILESIZE,
                 c * TILESIZE:c * TILESIZE + TILESIZE] 
         
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter, selection_row
    """
    if move:
      coord, letter, origin = move
      self.gui.set_message(f'{origin}>{coord}={letter}')
      # self.gui.set_message(f'{origin}>{coord}={letter}')
      if coord == (None, None):
        return 0
      elif isinstance(letter, np.ndarray):
        self.place_tile(origin, letter)
      elif letter != ' ':        
        # swap tiles
        # take tile at end coord and move it to start coord
        if self.board[origin].isalpha() and self.board[coord].isalpha():
           self.board[origin], self.board[coord] = self.board[coord], self.board[origin]
           
      self.gui.update(self.board)
    return 0
    
  def reveal(self): 
    """ place all tiles in their correct location """
    
    self.gui.update(self.solution)
        
    sleep(2)
    self.game_over()
    self.gui.show_start_menu()
      
  def game_over(self):
    # compare placement with solution    
    if np.array_equal(self.board,self.solution):
      self.gui.set_message('Game over')
      return True
    return False
      
  def restart(self):
    self.gui.close()
    self.__init__()
    self.run()
       
    
if __name__ == '__main__':
  g = QuoteWord()
  g.run()
  while (True):
    quit = g.wait()
    if quit:
      break

































