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
from types import SimpleNamespace
from Letter_game import LetterGame
import gui.gui_scene as gscene
from gui.gui_scene import Tile
from gui.gui_interface import Coord
from scene import Texture, LabelNode
PUZZLELIST = "quoteword.txt"
TILESIZE = 3


class QuoteWord(LetterGame):
  
  def __init__(self):    
    LetterGame.__init__(self, column_labels_one_based=True)
    self.first_letter = False
    self.tiles = None
    self.debug = True
    self.load_words_from_file(PUZZLELIST, no_strip=True) 
    self.selection = self.select_list()
    if self.selection is False:
       self.gui.gs.show_start_menu()
       return 
    self.gui.build_extra_grid(4, 4, grid_width_x=3, grid_width_y=3,
                              color='red', line_width=5)
    
       
    x, y, w, h = self.gui.grid.bbox
    
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'New ....': self.restart,
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.span = self.sizex // TILESIZE
    self.rack = self.display()
    
    self.gui.clear_messages()
    self.gui.set_enter('', stroke_color='black') # hide box
    self.gui.set_moves('\n'.join(self.wordlist), position=(w + 50, h / 2), font=('Avenir', 20))
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
    self.gui.set_message('')
    self.gui.set_prompt('')
    sleep(2)
    self.gui.gs.show_start_menu()
    
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
          if self.debug:   
            print(f'{selection=}')
          self.wordlist = self.word_dict[selection]
          
          
             
          if selection + '_frame' in self.word_dict:
            # rearrange frame text into N 3x3 tiles
            frame = self.word_dict[selection + '_frame']
            if self.debug:   
               [print(row, len(row)) for row in frame] # for debug
            assert all([len(row) == len(frame[0]) for row in frame]), 'Error in string lengths'
            # convert to numpy
            frame = np.array([np.array(row.lower(), dtype=str) for row in frame])
            
            frame = frame.view('U1').reshape((-1, self.image_dims[1] * TILESIZE))
            # replace spaces and dot by hash for display
            frame[frame == ' '] = '#'
            frame[frame == '.'] = '#'
            # divide into rows of 3
            rowsplit = np.split(frame, self.image_dims[0], axis=0)
            # divide each row into blocks of 3x3
            colsplit = [np.split(rowsplit[i], self.image_dims[1], axis=1) for i in range(len(rowsplit))]
            # add all together to get N 3x3 blocks
            self.tiles = np.concatenate(colsplit)
            
          
          self.gui.selection = ''
          return selection
        elif selection == "Cancelled_":
          return False
        else:
            return False
  
  def display(self):
      """ display tiles on board
      """
      rack = {}
    
      self.board = np.array(self.board)
      for n in range(self.span * self.sizey//TILESIZE):
        coord = divmod(n, self.span)       
        rack[coord] = n
        self.place_tile(coord, n)
         
      self.gui.update(self.board)
      
                  
      return rack
          
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
      
    point = self.gui.gs.start_touch - gscene.GRID_POS
    # touch on board
    # Coord is a tuple that can support arithmetic
    rc_start = Coord(self.gui.gs.grid_to_rc(point)) // TILESIZE
    
    if self.check_in_board(rc_start):
        rc = Coord(move[-2]) // TILESIZE
        if self.tiles is None:
           return rc, self.rack[rc_start].number, rc_start
        else:
          return rc, self.rack[rc], rc_start
                           
    return (None, None), None, None
  
  def place_tile(self, coord, tile_index):
      r, c = coord
      self.board[r * TILESIZE:r * TILESIZE + TILESIZE,
                 c * TILESIZE:c * TILESIZE + TILESIZE] = self.tiles[tile_index]
         
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter, selection_row
    """
    if move:
      coord, letter, origin = move
      
      # self.gui.set_message(f'{origin}>{coord}={letter}')
      if coord == (None, None):
        return 0
        
      elif letter == 'Finish':
        return 0
      elif letter != '':
        # swap tiles
        # take tile at end coord and move it to start coord
        tile_move = self.rack[origin]
        tile_existing = self.rack[coord]
        if self.tiles is None:
          tile_move.set_pos(coord)
          tile_existing.set_pos(origin)         
        else:
          self.place_tile(coord, tile_move)
          self.place_tile(origin, tile_existing)
          self.gui.update(self.board)
        # now update rack
        self.rack[origin] = tile_existing
        self.rack[coord] = tile_move
    return 0
    
  def get_tile_no(self, n):
    for t in self.gui.gs.get_tiles():
        if t.number == n:
            return t
                        
  def reveal(self): 
    """ place all tiles in their correct location """
    for n in range(self.span * self.sizey//TILESIZE):
        val = int(self.solution[n * 2: n * 2 + 2])
        coord = Coord(divmod(n, self.span))
        if self.tiles is not None:
          self.place_tile(coord,  val)
          self.rack[coord] = val
          self.gui.update(self.board)
        else:
          try:
            t = self.get_tile_no(val)
            t.set_pos(coord)
            self.rack[coord] = t
          except (AttributeError):
            pass        
    sleep(2)
    self.game_over()
    self.gui.gs.show_start_menu()
      
  def game_over(self):
    # compare placement with solution
    state = ''
    for r in range(self.sizey // TILESIZE):
      for c in range(self.span):
        if self.tiles is None:
          no = f'{self.rack[(r, c)].number:02d}'
        else:
          no = f'{self.rack[(r, c)]:02d}'
        state += no 
    if self.debug:   
        print(state)
    if state == self.solution:
      self.gui.set_message('Game over')
      return True
    return False
      
  def restart(self):
    self.gui.gs.close()
    self.__init__()
    self.run()
       
    
if __name__ == '__main__':
  g = QuoteWord()
  g.run()
  while (True):
    quit = g.wait()
    if quit:
      break






























