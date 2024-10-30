# Pieceword game
# tiles are 3x3 squares, to fit into 15 x 35 grid
# file for each puzzle has 3 sections , puzzleno, puzzleno_text, and puzzleno_frame

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
PUZZLELIST = "pieceword.txt"
TILESIZE = 3


class PieceWord(LetterGame):
  
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
    self.gui.build_extra_grid(5, 7, grid_width_x=3, grid_width_y=3,
                              color='red', line_width=5)
    try:
       self.image_name = Image.open(self.image)
       vsize, hsize = self.image_dims
       self.images = self.slice_image_into_tiles(self.image_name, img_count_h=hsize, img_count_v=vsize)
    except (FileNotFoundError):
       self.images = None
       
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
          
          if selection + '_text' in self.word_dict:
             self.table = self.word_dict[selection + '_text']
             self.image = self.wordlist[0]
             self.image_dims = [int(st) for st in self.wordlist[1].split(',')]
             self.solution = self.wordlist[2]
             
          if selection + '_frame' in self.word_dict:
            # rearrange frame text into N 3x3 tiles
            frame = self.word_dict[selection + '_frame']
            if self.debug:   
               [print(row, len(row)) for row in frame] # for debug
            assert all([len(row) == len(frame[0]) for row in frame]), 'Error in string lengths'
            # convert to numpy
            frame = np.array([np.array(row.lower(), dtype=str) for row in frame])
            frame = np.char.replace(frame, "'", '')
            frame = np.char.replace(frame, '/', '')
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
            
          self.wordlist = [word for word in self.table if word]
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
    if self.tiles is not None:
      self.board = np.array(self.board)
      for n in range(self.span * self.sizey//TILESIZE):
        coord = divmod(n, self.span)       
        rack[coord] = n
        self.place_tile(coord, n)
         
      self.gui.update(self.board)
      
    else:
      parent = self.gui.game_field
      
      sqsize = self.gui.gs.SQ_SIZE*TILESIZE
      for n, tile in enumerate(self.images.values()):
        if n == self.span * self.sizey//TILESIZE:
          break
        r, c = divmod(n, self.span)         
        t = Tile(Texture(self.pil2ui(tile)), r,  c, sq_size=sqsize,
                 dims=(self.gui.gs.DIMENSION_Y // TILESIZE, self.gui.gs.DIMENSION_X // TILESIZE))
        t.row, t.col = r, c
        t.number = n
        rack[(r, c)] = t
        parent.add_child(t)
              
    return rack
          
  def get_size(self):
    LetterGame.get_size(self, '15, 21')
    
  def load_words(self, word_length, file_list=PUZZLELIST):
    return
     
  def initialise_board(self):
    pass
      
  def pil2ui(self, imgIn):
    """ import a photo library image and convert to jpg in memory """
    with io.BytesIO() as bIO:
      imgIn.save(bIO, 'PNG')
      imgOut = ui.Image.from_data(bIO.getvalue())
    del bIO
    return imgOut
  
  def slice_image_into_tiles(self, in_image, img_count_h, img_count_v=1):
    """ take an image name or image object,
    crop into tile and add to dictionary"""
    
    if isinstance(in_image, str):
      img = Image.open(in_image)
    else:
      img = in_image
    w, h = img.size  # get the size of the big image
    w /= img_count_h      # calculate the size of smaller images
    h /= img_count_v
    index = 0
    images = {}
    try:
      
      for y in range(img_count_v):
        for x in range(img_count_h):
          index += 1
          img2 = img.crop((x * w, y * h, (x + 1) * w, (y + 1) * h))
          images.setdefault(index, img2)
    except (OSError) as e:
      print(e)
    return images
    
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
    try:
        rc_start = Coord(self.gui.gs.grid_to_rc(point)) // TILESIZE
        
        if self.check_in_board(rc_start):
            rc = Coord(move[-2]) // TILESIZE
            if self.tiles is None:
               return rc, self.rack[rc_start].number, rc_start
            else:
              return rc, self.rack[rc], rc_start
    except (KeyError):
      pass
                           
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
  g = PieceWord()
  g.run()
  while (True):
    quit = g.wait()
    if quit:
      break































