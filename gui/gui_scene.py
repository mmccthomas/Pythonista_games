#
# The GUI engine for several games
#
from scene import *
from scene import Vector2 # , get_screen_size
try:
    from change_screensize import get_screen_size
except ImportError:
    from scene import get_screen_size
import sound
from ui import Path, Image
from copy import copy
import console
from collections import defaultdict
from time import sleep, time
import sys
from queue import Queue
import logging
import traceback
from types import SimpleNamespace as ns

try:
   from gui.game_menu import MenuScene
except ModuleNotFoundError:
    from game_menu import MenuScene



screen_width, screen_height = get_screen_size()

logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
A = Action
"""Variables"""
if screen_width > screen_height:
  WIDTH = HEIGHT = 512  # width and height of the board
  GRID_POS = (100, 85)
else:
  WIDTH = HEIGHT = 360
  GRID_POS = (30, 85)
DIMENSION_X = 8
DIMENSION_Y = 8  # the dimensions of the chess board
SQ_SIZE = HEIGHT // DIMENSION_Y  # the size of each of the squares in the board
MOVE_SPEED = 0.05

                                      
class Player_test():
  def __init__(self):
    self.PLAYER_1 = WHITE = 'O'
    self.PLAYER_2 = BLACK = '0'
    self.EMPTY = '.'
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:White_Circle', 'emj:Black_Circle']
    self.PIECE_NAMES = {BLACK: 'Black', WHITE: 'White'}

  
class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, tile, row=0, col=0, sq_size=None, dims=None, **kwargs):
    # put these at front with z_position
    SpriteNode.__init__(self, tile, z_position=10)
    for k, v in kwargs.items():
      setattr(self, k, v)
    self.offset = 0  # was 10
    if sq_size is None:
       self.SQ_SIZE = 10
    else:
       self.SQ_SIZE = sq_size
     
    if dims is None:
       self.DIM_Y, self.DIM_X = 6, 7
    else:
       self.DIM_Y, self.DIM_X = dims
       
    self.size = (self.SQ_SIZE, self.SQ_SIZE)
    self.anchor_point = 0, 0
    self.number = 1
    self.name = ''
    
    self.set_pos(row, col)
    
  def set_pos(self, row, col=0, animation=False):
    """
    Sets the position of the tile in the grid.
    """
    if isinstance(row, tuple):
      row, col = row
    if col < 0 or col >= self.DIM_X:
      return
    if row < 0 or row >= self.DIM_Y:
      return
    self.col = int(col)
    self.row = (self.DIM_Y - 1 - int(row))
    
    pos = Vector2()
    pos.x = col * self.SQ_SIZE + self.offset
    pos.y = (self.DIM_Y - 1 - row) * self.SQ_SIZE + self.offset
    
    
    if animation:
      spd = animation
      wait = 0.02
    
      self.run_action(A.sequence(
        A.move_to(pos.x,pos.y, spd),
        A.wait(wait),
        A.remove))
    
    self.position = pos
    
        
class GameBoard(Scene):
  
  global GRID_POS

  def __init__(self):  # board, player, response):
    ''' board is 2d list of characters
    player is Player class
    reponse is output from touch operations
    '''
    Scene.__init__(self)
    self.board = [[]]
    self.Player = None
    
    # this is just for test
    self.board = [['.'] * 10 for i in range(10)]
    self.board[3][4] = self.board[4][3] = 'o'
    self.board[4][4] = self.board[3][3] = '@'
    self.DIMENSION_Y = len(self.board)
    self.DIMENSION_X = len(self.board[0])
    self.background_color = "#232323"
    self.background_image = None
    self.grid_label_color = 'white'
    self.grid = None
    self.grid_fill = 'lightgreen'
    self.grid_stroke_color = None
    self.grid_z_position = 10
    self.row_labels = None
    self.highlight_fill = '#00bc10'
    self.use_alpha = False
    self.column_labels = None
    self.require_touch_move = False
    self.allow_any_square = False
    self.last_board = list(map(list, self.board))
    self.q = None
    self.device = self.device_size()
    self.log_moves = False
    self.debug = False
    self.buttons = {}  # bbox: box _obj
    self.long_touch = False  # detects if touch for longer than 1 sec
    self.setup_menus()
        
    if __name__ == "__main__":
      self.Player = Player_test()
      self.setup_gui()
      self.test_lines()
  
  
          
  def device_size(self):
      """ return the device type and orientation """
      size = tuple(get_screen_size())
      match size:
        case (1366.00, 1024.00):
          device = 'ipad13_landscape'
        case (1024.00, 1366.00):
          device = 'ipad13_portrait'
        case (1112.00, 834.00):
          device = 'ipad_landscape'
        case (834.00, 1112.00):
          device = 'ipad_portrait'
        case (852.00, 393.00):
          device = 'iphone_landscape'
        case (393.00, 852.00):
          device = 'iphone_portrait'
        case (1133.0, 744.0):
          device = 'ipad_mini_landscape'
        case (744.0, 1133.0):
          device = 'ipad_mini_portrait'
        case _:
          device = None
      return device
      
  def grid_sizes(self, device, dimx, dimy):
    w, h = get_screen_size()
    match device:
      case 'ipad_landscape':
         GRID_POS = (50, 85)
         grid_size = h - 150
         font_size = 24
         
      case 'ipad_portrait':
         GRID_POS = (35, 85)
         grid_size = w - 50
         font_size = 24
         
      case 'iphone_landscape':
         GRID_POS = (30, 40)
         grid_size = h - 80
         font_size = 16
         
      case 'iphone_portrait':
         GRID_POS = (30, 60)
         grid_size = w - 50
         font_size = 12
         
      case 'ipad13_landscape':
         GRID_POS = (100, 85)
         grid_size = h - 150
         font_size = 24
         
      case 'ipad13_portrait':
         GRID_POS = (30, 85)
         grid_size = w - 50
         font_size = 24
         
      case 'ipad_mini_landscape':
         GRID_POS = (50, 85)
         grid_size = h - 150
         font_size = 24
         
      case 'ipad_mini_portrait':
         GRID_POS = (35, 85)
         grid_size = w - 50
         font_size = 24
         
    SQ_SIZE = grid_size // max(dimx, dimy)
         
    return GRID_POS, SQ_SIZE, font_size
  
  def get_fontsize(self):
      # adjustable font sizes for screen
      fontsize = {'iphone_landscape': 16, 'iphone_portrait': 12, 
                      'ipad_landscape': 24, 'ipad_portrait': 24,
                      'ipad13_landscape': 24, 'ipad13_portrait': 24,
                      'ipad_mini_landscape': 24, 'ipad_mini__portrait': 24}[self.device_size()]
      return fontsize
          
  def setup_gui(self, **kwargs):
    global GRID_POS
    GRID_POS, self.SQ_SIZE, self.font_size = self.grid_sizes(self.device, self.DIMENSION_X, self.DIMENSION_Y)
    
    for k, v in kwargs.items():
      setattr(self, k, v)
      
    self.smaller_tile = 0  # was 20
    self.current_player = self.Player.PLAYER_1
    # Root node for all game elements
    self.game_field = Node(parent=self, position=GRID_POS)

    self.IMAGES = {}
    self.highlights = [[]]
    self.squares = {}
    self.numbers = {} # (coords): {shape:shapeNode, label:LabelNode}
    self.touch_indicator = None
    self.line_timer = 0.5
    self.start_touch = None
    self.go = False
    
    self.load_images()
    self.setup_ui()
    # self.redraw_board()
  
  def setup_menus(self):
      self.pause_menu = {'Continue': self.dismiss_modal_scene,
                         'Undo': self.dismiss_modal_scene,
                         'New Game': self.dismiss_modal_scene,
                         'Quit': self.close}
      self.start_menu = {'New Game': self.dismiss_modal_scene,
                         'Quit': self.close}
  
  # #########################################################################
  # GUI
   
  def build_extra_grid(self, grids_x, grids_y,
                       grid_width_x=None, grid_width_y=None,
                       color=None, line_width=2, offset=None,
                       z_position=100):
    """ define a grid to overlay on top of everything else
    allow offset to place grid at centre of square (e.g. go game)"""
    if grid_width_x is None:
      grid_width_x = grids_x
    if grid_width_y is None:
      grid_width_y = grids_y
    if offset is None:
      offx, offy = 0, 0
    else:
      offx, offy = offset
    # Parameters to pass to the creation of ShapeNode
    x = Path.rect(0, 0, self.SQ_SIZE * grid_width_x,
                  self.SQ_SIZE * grids_y * grid_width_y)
    x.line_width = line_width
    params = {
      "path": x,
      "fill_color": 'clear',
      "stroke_color": "black" if color is None else color,
      "parent": self.game_field,
      "z_position": z_position
    }
    anchor = Vector2(0, 0)
    # Building the columns
    for i in range(grids_x):
      n = ShapeNode(**params)
      pos = Vector2(offx + i * self.SQ_SIZE * grid_width_x, offy)
      n.position = pos
      n.anchor_point = anchor
    
    # Building the rows
    y = Path.rect(0, 0, self.SQ_SIZE * grids_x * grid_width_x,
                  self.SQ_SIZE * grid_width_y)
    y.line_width = line_width
    params["path"] = y
    
    for i in range(grids_y):
      n = ShapeNode(**params)
      pos = Vector2(offx, offy + i * self.SQ_SIZE * grid_width_y)
      n.position = pos
      n.anchor_point = anchor

    
  def add_row_column_labels(self):
      font = ('Avenir Next', self.font_size)
      if self.use_alpha:
          row_labels = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z AAABACAD'
      else:
          if self.row_labels:
              row_labels = self.row_labels
          else:
              row_labels = '0 1 2 3 4 5 6 7 8 9 101112131415161718192021222324252627282930'
      if self.column_labels:
          column_labels = self.column_labels
      else:
          column_labels = '0 1 2 3 4 5 6 7 8 9 101112131415161718192021222324252627282930'
      for i in range(self.DIMENSION_X):
          pos = Vector2(0 + i * self.SQ_SIZE, 0)
          n = LabelNode(row_labels[2 * i: 2 * i + 2], parent=self.game_field)
          n.position = (pos.x + self.SQ_SIZE / 2,
                    pos.y + self.DIMENSION_Y * self.SQ_SIZE + 20)
          n.color = self.grid_label_color
          n.font = font
          
      for i in range(self.DIMENSION_Y):
          pos = Vector2(0, 0 + i * self.SQ_SIZE)
          idx = self.DIMENSION_Y - 1 - i
          n = LabelNode(column_labels[2 * idx: 2 * idx + 2],
                        parent=self.game_field)
          n.position = (pos.x - 20, pos.y + self.SQ_SIZE/2)
          n.color = self.grid_label_color
          n.font = font
      
  def build_background_grid(self):
    parent = Node()
    
    if self.background_image:
      background = SpriteNode(Texture(self.background_image))
      background.size = (self.SQ_SIZE * self.DIMENSION_X,
                         self.SQ_SIZE * self.DIMENSION_Y)
      background.position = (0, 0)
      background.anchor_point = (0, 0)
      parent.add_child(background)
    
    # Parameters to pass to the creation of ShapeNode
    params = {
      "path": Path.rect(0, 0, self.SQ_SIZE, self.SQ_SIZE * self.DIMENSION_Y),
      "fill_color": self.grid_fill,
      "stroke_color": "darkgrey" if self.grid_stroke_color is None else self.grid_stroke_color,
      "z_position": self.grid_z_position
    }
    anchor = Vector2(0, 0)
    # Building the columns
    for i in range(self.DIMENSION_X):
      n = ShapeNode(**params)
      pos = Vector2(0 + i * self.SQ_SIZE, 0)
      n.position = pos
      n.anchor_point = anchor
      parent.add_child(n)
      
    # Building the rows
    params["path"] = Path.rect(0, 0, self.SQ_SIZE * self.DIMENSION_X,
                               self.SQ_SIZE)
    params['fill_color'] = 'clear'
    for i in range(self.DIMENSION_Y):
      n = ShapeNode(**params)
      pos = Vector2(0, 0 + i * self.SQ_SIZE)
      n.position = pos
      n.anchor_point = anchor
      parent.add_child(n)
      
    return parent
    
  def setup_ui(self):
    
    pause_button = SpriteNode('iow:pause_32', position=(32, self.size.h - 36),
                              parent=self)
    self.grid = self.build_background_grid()
    self.game_field.add_child(self.grid)
    self.add_row_column_labels()
    x, y, w, h = self.grid.bbox  # was game_field
    font = ('Avenir Next', self.font_size)
    # all location relative to grid
    self.msg_label_t = LabelNode("top", font=font, position=(0, h + 30),
                                 parent=self.game_field)
    self.msg_label_t.anchor_point = (0, 0)
    
    self.msg_label_b = LabelNode("bottom", font=font, position=(0, -30),
                                 parent=self.game_field)
    self.msg_label_b.anchor_point = (0, 0)
    self.msg_label_b2 = LabelNode("bottom2", font=font, position=(0, -60),
                                  parent=self.game_field)
    self.msg_label_b2.anchor_point = (0, 0)
    self.msg_label_prompt = LabelNode("prompt", font=font, position=(0, -90),
                                      parent=self.game_field)
    self.msg_label_prompt.anchor_point = (0, 0)
    # position right hand message text and enter button
    match self.device:
      case 'ipad_landscape':
        position = (w + 10, h / 2)
        anchor_point = (0, 0.5)
        pos_button = (800, 0)
      case 'ipad_portrait':
        position = (150, h + 30)
        anchor_point = (0, 0)
        pos_button = (600, 600)
      case 'ipad13_landscape':
        position = (w + 10, h / 2)
        anchor_point = (0, 0.5)
        pos_button = (w, 0)
      case 'ipad13_portrait':
        position = (150, h + 30)
        anchor_point = (0, 0)
        pos_button = (870, h+50)
      case 'iphone_portrait':
        position = (150, h + 20)
        anchor_point = (0, 0)
        pos_button = (350, 350)
      case _:
        position = (150, h + 20)
        anchor_point = (0, 0)
        pos_button = (350, 0)
    
    self.msg_label_r = LabelNode("right", font=font, position=position,
                                 parent=self.game_field)
    self.msg_label_r.anchor_point = anchor_point
    
    # self.enter_button = ShapeNode(ui.Path.rounded_rect(0, 0, 100, 32, 5),
    #                               position=pos_button, parent=self)
    # self.enter_button.anchor_point = (0, 0)
    # self.enter_button.line_width = 2
    # self.enter_button.fill_color = 'clear'
    # self.enter_button.stroke_color = 'white'
    # self.enter_label = LabelNode('Enter', position=(5,5), 
    #.                             parent=self.enter_button)
    # self.enter_label.anchor_point = (0, 0)
    self.enter_button = BoxedLabel('Hint', '', position=pos_button,
                                   min_size=(100, 32),
                                   parent=self.game_field)
    self.buttons[1] = self.enter_button
    self.buttons[1].set_index(1)
    self.enter_button.set_text_props(font=font)
  
  # #########################################################################
  # LINES 
    
  def test_lines(self):
    rcs = [(0.5, 0.5), (0.5, 2.5), (3.5, 2.5),
           (3.5, 4.5), (4.5, 4.5), (4.5, 0.5), (0.5, 0.5)]
    points = [self.rc_to_pos(r - 1, c) for r, c in rcs]
    self.draw_line(points, line_width=1,
                   stroke_color='black', set_line_dash=[10, 2])
    x, y = -.75, 1.25
    self.add_numbers([Squares((0,0), 'A', 'red', z_position=30, sqsize=self.SQ_SIZE,
                                   alpha=0.5, font=('Avenir Next', self.SQ_SIZE),
                                   offset=(0, 0),
                                   text_anchor_point=(x, y))])
   
  def draw_line(self, coords, **kwargs):
    ''' coords is an array of Point objects from rc_to_point
    '''
    # if self.line is not None:
    #  self.line.remove_from_parent()
    path = ui.Path()
    
    path.line_width = 2
    # modify path parameters
    for k, v in kwargs.items():
        try:
          setattr(path, k, v)
        except (AttributeError):
            try:
              fn = getattr(path, k)
              fn(v)
            except (AttributeError, TypeError) as e:
              pass
              # print(traceback.format_exc())
    minx, miny = None, None
    for i, p in enumerate(coords):
      # get/update the lower left corner minimum
      try:
          minx, miny = (p.x if minx is None else min(minx, p.x),
                        p.y if miny is None else min(miny, p.y))
          
          if i == 0:
            path.move_to(p.x, -p.y)
          else:
            path.line_to(p.x, -p.y)
      except (AttributeError):
        print('coords param needs to be array of Points from rc_to_pos()')
        print(traceback.format_exc())
        raise AttributeError
        
      path.stroke()
      
    # the offset(position) of our node has to be the lower left corner
    # point plus the center vector of our path
    self.line = ShapeNode(path,
                          position=(minx + path.bounds.w * 0.5,
                                    miny + path.bounds.h * 0.5),
                          z_position=1000,
                          parent=self.game_field)
    self.line.stroke_color = 'red'
    self.line.fill_color = 'transparent'
    # modify line parameters
    for k, v in kwargs.items():
        try:
          setattr(self.line, k, v)
        except (AttributeError):
          pass
  
  # #########################################################################
      
  def check_in_board(self, coord):
    r, c = coord
    return (0 <= r < self.DIMENSION_Y) and (0 <= c < self.DIMENSION_X)

  def load_images(self):
    ''' Load images for the chess pieces '''
    if isinstance(self.Player.PIECES, dict):
      self.IMAGES = self.Player.PIECES
    else:
      if ':' in self.Player.PIECES:  # internal icon
          self.IMAGES = {player: image
                         for player, image in zip(self.Player.PLAYERS,
                                                  self.Player.PIECES)}
      else:
          self.IMAGES = {player: image
                         for player, image in zip(self.Player.PIECE_NAMES,
                                                  self.Player.PIECES)}
      
  def get_piece(self, r, c):
    return self.board[r][c]
    
  def set_player(self, player):
    self.current_player = player
     
  def redraw_board(self, fn_piece=None):
    ''' Draw the pieces onto the board'''
    # remove existing
    for t in self.get_tiles():
      t.remove_from_parent()
      
    if fn_piece is None:
      def fn_piece(piece): return piece

    parent = self.game_field
    for r in range(self.DIMENSION_Y):
      for c in range(self.DIMENSION_X):               
        # animation = False if piece == self.last_board[r][c] else True
        try:
          piece = self.get_piece(r, c)
          animation = False
          k = fn_piece(piece)
          if self.debug:
              print('fnpiece', k)
          # fn_piece allows computation of image name from calling module
          t = Tile(Texture(self.IMAGES[k]), 0, 0,
                   sq_size=self.SQ_SIZE,
                   dims=(self.DIMENSION_Y, self.DIMENSION_X))
          # t.DIM_Y, t.DIM_X = self.DIMENSION_Y, self.DIMENSION_X
          
          t.size = (self.SQ_SIZE - self.smaller_tile,
                    self.SQ_SIZE - self.smaller_tile)
          t.set_pos(r, c, animation=animation)
          t.name = str(fn_piece(piece)) + str(r * self.DIMENSION_Y + c)
          t.position = t.position + (self.smaller_tile / 2, self.smaller_tile / 2)
          parent.add_child(t)
        except (AttributeError, KeyError, TypeError, IndexError) as e:
          if self.debug:
             print(k)
             print(traceback.format_exc())
          
    self.last_board = list(map(list, self.board))
    
  def changed(self, board_update):
    ''' return first differnce '''
    gui_board = self.board
    for j, row in enumerate(board_update):
      for i, col in enumerate(row):
        if gui_board[j][i] != col:
          return board_update[j][i], i, j
    return None
    
  def highlight_squares(self, valid_moves, alpha=1):
    # highlight move squares
    self.highlights = []
    self.hl = []
    for move in valid_moves:
      if True:
        t = ShapeNode(ui.Path.rect(0, 0, self.SQ_SIZE, self.SQ_SIZE),
                      fill_color=self.highlight_fill,
                      position=self.rc_to_pos(move[0], move[1]), alpha=alpha,
                      parent=self.game_field, )
        t.anchor_point = (0, 0)
        self.highlights.append(move)
        self.hl.append(t)
        
  # #########################################################################
  # NUMBERS 
        
  def get_numbers(self, coords):
    """ get color and text of number square objects for temporary storage
    (coords): {shape:shapeNode, label:LabelNode}"""
    if isinstance(coords, tuple):
        coords = [coords]
    if isinstance(coords, list):
      items = {}
      for coord in coords:
        # remove existing
        try:
           v = self.numbers[coord]
           color = v.shape.color
           alpha = v.shape.alpha
           text = v.label.text
           text_color = v.label.color
              
           items[coord] = {'color': color, 'text': text,
                        'text_color': text_color, 'alpha': alpha}
        except (KeyError):
          pass
      return items
      
  def put_numbers(self, items, **kwargs):
    """ put temporary items back again items are dictionary of coord:
    (color, text, text_color)
    (coords): {shape:shapeNode, label:LabelNode}
    """
    for k, v in kwargs.items():
      setattr(self, k, v)
      
    if isinstance(items, dict):
      for coord, data in items.items():
        # remove existing
        try:
          v = self.numbers[coord]           
          v.shape.color = data['color']
          v.shape.alpha = data['alpha']            
          v.label.text = data['text']
          v.label.color = data['text_color']
        except (KeyError):
          pass
    
  def replace_numbers(self, items, **kwargs):
    """ replace the properties of specified number squares """
    # items is a list of
    # items are each a dictionary of (row,col), text, color
    for k, v in kwargs.items():
      setattr(self, k, v)
    
    def add(a, b):
      return tuple(p + q for p, q in zip(a, b))
      
    if isinstance(items, list):
      for item in items:
        # remove existing
        try:
           v = self.numbers[item]            
           v.shape.remove_from_parent()           
           v.label.remove_from_parent()
           self.numbers[item] = {}
        except (KeyError):
          pass
      # now add new
      self.add_numbers(items, clear_previous=False, **kwargs)
        
  def add_numbers(self, items, clear_previous=True, **kwargs):
    # items is a list of Squares objects
    # items are each a dictionary of (row,col), text, color
    # (coords): {shape:shapeNode, label:LabelNode}
    for k, v in kwargs.items():
      setattr(self, k, v)
    if clear_previous:
        self.clear_numbers()
            
    def add(a, b):
        return tuple(p + q for p, q in zip(a, b))

    for item in items:
        if hasattr(item, 'sqsize'):
           sqsize = item.sqsize
        else:
           sqsize = self.SQ_SIZE
        r, c = item.position
        x, y = item.offset
        t = ShapeNode(ui.Path.rounded_rect(0, 0, sqsize, sqsize, item.radius),
                      fill_color=item.color,
                      position=self.rc_to_pos(r + y, c + x),
                      stroke_color=item.stroke_color,
                      z_position=item.z_position,
                      alpha=item.alpha,
                      parent=self.game_field)
        if hasattr(item, 'anchor_point'):
            t.anchor_point = item.anchor_point
        else:
            t.anchor_point = (0, 0)
        
        #  unmodified text point is centre of cell
        # text anchor point will be -1 to +1
        tposx, tposy = item.text_anchor_point
        tpos_x = (self.SQ_SIZE / 2) + tposx * (self.SQ_SIZE / 2) # - 5)
        tpos_y = (self.SQ_SIZE / 2) + tposy * (self.SQ_SIZE / 2) # - 5)
        pos1 = self.rc_to_pos(r, c)
        pos = add(self.rc_to_pos(r, c), (tpos_x, tpos_y))
        t1 = LabelNode(str(item.text), color=item.text_color,
                       font=item.font, position=pos,
                       z_position=item.z_position + 5,
                       parent=self.game_field)
        t1.anchor_point = (0, 1.0)
        self.numbers[tuple(item.position)] = ns(**{'shape': t, 'label': t1})
      
  
  def clear_numbers(self, number_list=None):
    """ clear some or all numbers
    if number_list is specified, it is [(r,c)] 
    Need to remove both shape and labelnode
    they have different position but same grid position
    (coords): {shape:shapeNode, label:LabelNode}
    """
    if number_list is None:
      for v in self.numbers.values():
         v.shape.remove_from_parent()
         v.label.remove_from_parent()
      self.numbers = {}
      
    elif isinstance(number_list, list):
      for pos in number_list:
        try:
          v = self.numbers[pos]           
          v.shape.remove_from_parent()            
          v.label.remove_from_parent()            
          self.numbers[pos] = {}
        except (KeyError):
          pass   
    elif isinstance(number_list, tuple):
      # slicing ( self.numbers[:] ) is important to avoid skipping
      try:
          v = self.numbers[number_list] 
          v.shape.remove_from_parent()            
          v.label.remove_from_parent()            
          self.numbers[number_list] = {}
      except (KeyError):
          pass   
  
  # ######################################################################### 
                     
  def clear_highlights(self):
    if hasattr(self, 'hl'):
      for t in self.hl:
        t.remove_from_parent()
    self.highlights = []
    self.hl = []
      
  def draw_text(self, text):
    self.msg_label_t.text = text
  
  def board_print(self):
    for r in range(self.DIMENSION_Y):
      for c in range(self.DIMENSION_X):
        piece = self.get_piece(r, c)
        if piece is not None and piece != Player.EMPTY:
          print(piece.player[0]+piece.name, end=" ")
        else:
          print('..', end=" ")
      print()
    print()
    
  def turn_status(self, turn, custom_message=None):
      if custom_message:
         self.msg_label_t.text = custom_message
      else:
          self.msg_label_t.text = "white turn" if turn else "black turn"
      
  def will_close(self):
    print('closing')
         
  '''def update(self):
    # dt is provided by Scene t is time since start
    self.line_timer -= self.dt
    self.go = True
    if self.line_timer <= 0:
      self.line_timer = 0.5
      # self.turn_status()
      self.go = True'''
  
  # #########################################################################
  # TOUCH 
  
  def touch_began(self, touch):
    self.touch_time = time()
    self.beep = False
    self.start_touch = touch.location
    button_touch = [button.bounds.contains_point(touch.location)
                    for button in self.buttons.values()]
    
    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.show_pause_menu()
      return
      
    # elif self.enter_button.bbox.contains_point(touch.location):
    # if self.q:
    #      self.q.put((-1, -1))
    
    elif any(button_touch):
      for k, button in self.buttons.items():
        if button.bounds.contains_point(touch.location):
          if self.q:
            self.q.put(button.ident)
          return
    
    else:
      t = touch.location
      rc = self.point_to_rc(t)
      self.last_rc = rc
      
      try:
          self.touch_indicator = Tile(Texture(self.IMAGES[self.current_player]),
                                      rc, sq_size=self.SQ_SIZE,
                                      dims=(self.DIMENSION_Y, self.DIMENSION_X))
          # self.touch_indicator.anchor_point = (0.5, 0.5)
          self.game_field.add_child(self.touch_indicator)
      except (KeyError):
        pass
      if self.log_moves:
        if self.q:
          self.q.put(rc)

  def touch_moved(self, touch):
    touch_length = time() - self.touch_time
    if touch_length > 0.5 and not self.beep:
      sound.play_effect('digital:TwoTone2')
      self.beep = True
      
    if self.touch_indicator:
      self.touch_indicator.set_pos(self.point_to_rc(touch.location))
      rc = self.point_to_rc(touch.location)
      if self.debug:
          if self.use_alpha:
            c = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z '
          else:
            c = '1 2 3 4 5 6 7 8 9 1011121314151617181920'
          r = '1 2 3 4 5 6 7 8 9 1011121314151617181920'
          y, x = rc[0], rc[1]
          msg = c[2 * x: 2 * x + 2] + r[2 * y:2 * y + 2]
          msg = msg.replace(' ', '')
          self.enter_label.text = f'{y},{x}__{msg}'
      if self.log_moves:
        if self.q:
          self.q.put(rc)
   
  def touch_ended(self, touch):
    touch_length = time() - self.touch_time
    self.long_touch = touch_length > 0.5
    self.beep = False
    if self.touch_indicator:
      self.touch_indicator.remove_from_parent()
      self.touch_indicator = None
    logger.debug('touch ended')
  
    rc = self.point_to_rc(touch.location)
    r, c = rc
    # move testing to top level list(rc) in self.highlights or self.allow_any_square:        
    if self.check_in_board(rc):  
      self.board[rc[0]][rc[1]] = self.current_player
      if self.q:
        self.q.put(rc)
        # print('end',time())
    if self.q and self.log_moves:
      self.q.put(-1)
      if self.debug:
          self.enter_label.text = 'End'
      # self.clear_highlights()
      # update gui
      # self.redraw_board()
      # self.board_print()
      
  def point_to_rc(self, point):
    """ covert touch point to rc tuple """
    col = int((point.x - GRID_POS[0]) / (self.SQ_SIZE))
    row = self.DIMENSION_Y - 1 - int((point.y - GRID_POS[1]) / (self.SQ_SIZE))
    return row, col
    
  def grid_to_rc(self, point):
    """ convert Point object in game field coordinates to rc tuple
    Inverse of rc_to_pos
    """
    col = int(point.x / self.SQ_SIZE)
    row = self.DIMENSION_Y - 1 - int(point.y / self.SQ_SIZE)
    return row, col
    
  def rc_to_pos(self, row, col):
    """ covert col row  to Point object in game field coordinates
    row, col are in (0,0) is topleft
    x,y is (0,0 is bottom right) """
    # bbox = self.game_field.bbox  # x,y,w,h
    row = self.DIMENSION_Y - 1 - row
    x = col * self.SQ_SIZE
    y = row * self.SQ_SIZE
    return Point(x, y)
 
  # #########################################################################
  # TILES 
  
  def get_tiles(self):
    """
    Returns an iterator over all tile objects
    """
    for o in self.game_field.children:
      if isinstance(o, Tile):
        yield o
        
  def get_squares(self):
    """
    Returns an iterator over all Squares objects
    """
    for o in self.game_field.children:
      if isinstance(o, Square):
        yield o
        
  def tile_at(self, row, col=None, multi=False):
    '''select tile'''
    tiles = []
    if isinstance(row, (tuple, list)):
      r, c = row[0], row[1]
    else:
      r, c = row, col
    r = self.DIMENSION_Y - 1 - r
    
    for t in self.get_tiles():
      if t.row == r and t.col == c:
        if multi is False:
          return t
        else:
          tiles.append(t)
    if tiles:
      return tiles
    else:
      return None
    
  def square_at(self, row, col=None):
    '''select tile'''
    if isinstance(row, (tuple, Point)):
      r, c = row
    else:
      r, c = row, col
    return self.squares[(r, c)]

  def clear_squares(self, squares_list=None):
    """ clear some or all squares
    if squares_list is specified, it is [(r,c)] """
    if squares_list is None:      
      for t in self.squares.values():
        t.remove_from_parent()
        self.squares = {}
    elif isinstance(squares_list, list):
      for pos in squares_list:
        for t in self.squares.values()[:]:
          tpos = self.grid_to_rc(t.position)
          if tpos == pos:
            t.remove_from_parent()
            self.squares.remove(t)
    elif isinstance(squares_list, tuple):
      for t in self.squares.values()[:]:
          tpos = self.grid_to_rc(t.position)
          if tpos == squares_list:
            t.remove_from_parent()
            self.squares.remove(t)
    
          
  def tile_drop(self, rc, selected):
    """ move tile to new location   """
    if selected:
      logger.debug(f' move to {rc}')
      selected.set_pos(rc)
  
  def restart(self, first_time=False):
    self.dismiss_modal_scene()
    self.menu = None
    for o in self.game_field.children:
      o.remove_from_parent()
    self.setup(first_time=first_time)
    self.paused = False
    
  def close(self):
    self.view.close()
    # wait until closed
    while self.view.on_screen:
      #print('waiting for close')
      sleep(.2)
    
  def get_text_image(self, text, font, color):
    """get a text string ss an image for use in Texture(img) """
    w, h = ui.measure_string(text, font=font)
    # Round up size to next multiple of screen scale
    # (makes it easier to get crisp rendering in common cases)
    s = get_screen_scale()
    w = math.ceil(w / s) * s
    h = math.ceil(h / s) * s
    with ui.ImageContext(max(w, 1), max(h, 1)) as ctx:
      ui.draw_string(text, (0, 0, w, h), font, color=color)
      img = ctx.get_image()
    return img
  
  # #########################################################################
  # MENU 
      
  def show_pause_menu(self, **kwargs):
    self.menu = MyMenu('Paused', '', [i for i in self.pause_menu], **kwargs)
    self.present_modal_scene(self.menu)
    self.paused = True

  def show_start_menu(self, **kwargs):
    self.menu = MyMenu('New Game?', '', [i for i in self.start_menu], **kwargs)
    self.present_modal_scene(self.menu)
    self.paused = True

  def menu_button_selected(self, title):
    """ Pass back selected item to main program loop
    menu items are passed a dictionary of title: functions """
    if title in self.pause_menu:
      fn_ = self.pause_menu[title]
      self.dismiss_modal_scene()
      self.menu = None
      if self.debug:
          print(f'putting {fn_} to queue')
      self.q.put(fn_)
                  
    elif title in self.start_menu:
      fn_ = self.start_menu[title]
      self.dismiss_modal_scene()
      self.menu = None
      if self.debug:
          print(f' putting {fn_} to queue')
      self.q.put(fn_)
    else:
      self.dismiss_modal_scene()
      self.menu = None
    self.paused = False

# #########################################################################
  # BOXED LABEL
                      
class BoxedLabel():
  """ a simple class of boxed label with a title
      box follows text size
      text positions must follow box position
  """
  global GRID_POS
  
  def __init__(self, text='text', title='boxed_label',
               min_size=(100, 50), position=(0, 0), parent=None):
      ''' position is rel to grid'''
      self.position = position
      self.parent = parent
      self.size = min_size
      self.font = ('Avenir Next', 24)
      self.title = title
      self.text = text
      self.index = 1
      self.bounds = Rect(0, 0, 10, 10)
      self.l_box_name = None
      self.draw_box(min_size)
      # add text centred on box
      x, y, w, h = self.l_box_name.bbox
      self.l_name =  LabelNode(text,
                               position=(position[0] + 5,position[1] + 2),
                               anchor_point=(0, 0), font=self.font,
                               parent=parent)
      self.l_name.anchor_point = (0, 0)  # bottom left
      self.l_name.color = 'white'
      self.set_text(text)
      self.ident = (-self.index, -self.index)
      
  def draw_box(self, min_size=(100, 50)):
      # fix anchor point at (0,0) otherwise text goes walkabout
      radius = 5
      offset = 1
      w_, h_ = min_size
      self.l_box_name = ShapeNode(ui.Path.rounded_rect(0, 0, w_, h_,  radius),
                                  position=self.position,
                                  parent=self.parent)
      self.l_box_name.anchor_point = (0, 0)  # bottom left
      self.l_box_name.line_width = 1
      self.l_box_name.fill_color = 'clear'
      self.l_box_name.stroke_color = 'white'
      x, y, w, h = self.l_box_name.bbox
      self.bounds = Rect(x + GRID_POS[0], y + GRID_POS[1], w, h)
      self.l_box_title = LabelNode(self.title, position=(x + 5, y + h),
                                   anchor_point=(0, 0), font=self.font,
                                   parent=self.parent)
                                   
  def update_text_positions(self):
      """ sync text locations """
      # if key == 'position':
      # change text position and bounds
      x, y, w, h = self.l_box_name.bbox
      self.bounds = Rect(x + GRID_POS[0], y + GRID_POS[1], w, h)
      b_x, b_y = self.l_box_name.position
      self.l_name.position = position = (b_x + 5, b_y + 2)
      self.l_box_title.position = (b_x + 5, b_y + h)
                                              
  def set_text(self, text):
      """ sets box text and recomputes box"""
      self.text = ''
      self.text = text
      self.l_name.text = text
      
      # possibly resize box
      x, y, w, h = self.l_name.bbox
      w1, h1 = self.size
      x_scale = (w + 8) / w1 if w > w1 else 1.0
      y_scale = h / h1 if h > h1 else 1.0
      self.l_box_name.x_scale = x_scale
      self.l_box_name.y_scale = y_scale
      
      self.update_text_positions()
      
  def get_text(self): 
      return self.text
              
  def set_props(self, **kwargs):
    # pass kwargs to box, or box text
    # text can change box size
    # box can change text position
    text_props = {k: v for k, v in kwargs.items() if k in ['color', 'font']}
    [kwargs.pop(k) for k in text_props]
    self.set_box_props(**kwargs)
    self.set_text_props(**text_props)
      
  def set_text_props(self, **kwargs):
      for k, v in kwargs.items():
          try:
              setattr(self.l_name, k, v)
          except (AttributeError):
              print(traceback.format_exc())
      if 'font' in kwargs:
         self.set_text(self.text)
            
  def set_box_props(self, **kwargs):
      for k, v in kwargs.items():
          try:
              setattr(self.l_box_name, k, v)
          except (AttributeError):
              print(traceback.format_exc())
      if 'position' in kwargs or 'anchor_point' in kwargs:
          self.update_text_positions()
              
  def set_index(self, index):
    self.index = index
    self.ident = (-index, -index)


# #########################################################################
# MYMENU  
                                                 
class MyMenu(MenuScene):
  """ subclass MenuScene to move menu to right """
  def __init__(self, title, subtitle, button_titles, layout=None):
    MenuScene.__init__(self, title, subtitle, button_titles, layout)
    
  def did_change_size(self):
    # 834,1112 ipad portrait
    # 1112, 834 ipad landscape
    # 852, 393 iphone landscape
    self.bg.size = (1, 1)
    if self.size.h > self.size.w:
      self.bg.position = self.size.w * 0.5, self.size.h * 0.6
    else:
      self.bg.position = self.size.w * 0.85, self.size.h * 0.5
    self.menu_bg.position = self.bg.position


if __name__ == "__main__":
  from gui_interface import Squares
  logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',
                      level=logging.WARNING)
  run(GameBoard(), LANDSCAPE, show_fps=True)
