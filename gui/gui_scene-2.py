#
# The GUI engine for several games
#
from scene import *

import sys
import os
from queue import Queue
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)


from ui import Path
from  copy import copy
import console
from time import sleep
from util.gui.game_menu import MenuScene
from scene import Vector2, get_screen_size
screen_width, screen_height = get_screen_size()
 
#current = os.path.dirname(os.path.realpath(__file__))
#parent = os.path.dirname(current)
#sys.path.append(parent)

import logging

logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
A = Action
"""Variables"""
if screen_width > 500:
  WIDTH = HEIGHT = 512  # width and height of the board
  GRID_POS =(200,150)
else:
  WIDTH = HEIGHT = 360
  GRID_POS =(10, 200)
DIMENSION_X = 8
DIMENSION_Y = 8  # the dimensions of the chess board
SQ_SIZE = HEIGHT // DIMENSION_Y # the size of each of the squares in the board

MOVE_SPEED = 0.05

class Player_test():
  def __init__(self):
    self.PLAYER_1 = WHITE = 'O'
    self.PLAYER_2 = BLACK = '0'
    self.EMPTY = '.'
    self.PLAYERS =[self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:White_Circle', 'emj:Black_Circle']
    self.PIECE_NAMES ={BLACK: 'Black', WHITE: 'White'}


  
class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, tile, row=0, col=0, sq_size=None, dims=None):
    # put these at front with z_position
    SpriteNode.__init__(self, tile, z_position=10)
    if sq_size is None:
       self.SQ_SIZE = 10
    else:
       self.SQ_SIZE = sq_size
     
    if dims is None:      
       self.DIM_Y, self.DIM_X = 6,7
    else:
       self.DIM_Y, self.DIM_X = dims
       
    self.size = (self.SQ_SIZE, self.SQ_SIZE)
    self.anchor_point = 0,0 
    self.number = 1
    self.name = ''
    
    self.set_pos(row, col)
    
  def set_pos(self, row, col=0, animation=True):
    """
    Sets the position of the tile in the grid.
    """
    if isinstance(row,tuple):
      row, col  = row     
    if col < 0 or col >= self.DIM_X:
      return    
    if row < 0 or row >= self.DIM_Y:
      return        
    self.col = int(col)
    self.row = (self.DIM_Y - 1 - int(row))
    
    pos = Vector2()
    pos.x = col * self.SQ_SIZE + 10
    pos.y = (self.DIM_Y -1 - row) * self.SQ_SIZE + 10
    
    """
    if animation:
      spd = MOVE_SPEED
      wait = 0.02
    else:
      spd = 0.01
      wait = 0.02
    self.run_action(A.sequence(
      A.move_to(pos.x,pos.y, spd), 
      A.wait(wait), 
      A.remove))
    """
    self.position = pos
    
        
class GameBoard(Scene): 

  def  __init__(self): #board, player,response):
    ''' board is 2d list of characters
    player is Player class
    reponse is output from touch operations
    '''
    Scene.__init__(self)
    self.board = [[]]
    self.Player = None
    
    # this is just for test
    self.board = [['.'] *7 for i in range(6)]
    self.board[3][4] = self.board[4][3]  ='o'
    self.board[4][4] = self.board[3][3] = '@'
    self.DIMENSION_Y = len(self.board) 
    self.DIMENSION_X = len(self.board[0]) 
    self.background_color =  "#232323"
    self.background_image = None
    self.grid_fill = 'lightgreen'
    self.highlight_fill = '#00bc10'
    self.use_alpha = False
    self.require_touch_move = False
    self.allow_any_square = False
    self.last_board = list(map(list, self.board)) 
    self.q = None
    self.setup_menus()
        
    if __name__ =="__main__":
      self.Player = Player_test()
      self.setup_gui()
    
  def setup_gui(self):
    
    self.SQ_SIZE = HEIGHT // self.DIMENSION_Y # the size of each of the squares in the board
    self.current_player = self.Player.PLAYER_1    
    # Root node for all game elements
    self.game_field = Node(parent=self, position=GRID_POS)

    self.IMAGES = {}
    self.highlights = [ [] ]
    self.squares = {}
    self.touch_indicator = None
    self.line_timer = 0.5 
    self.go = False
    
    
    self.load_images()
    self.setup_ui()
    self.redraw_board()
    
    #if first_time:
    #  self.show_start_menu()
  
  def setup_menus(self):
      self.pause_menu = {'Continue': self.dismiss_modal_scene,  'Undo': self.dismiss_modal_scene, 
                         'New Game': self.dismiss_modal_scene,  'Quit': self.close}
      self.start_menu =  {'New Game': self.dismiss_modal_scene,   'Quit': self.close}
      
  def build_background_grid(self):
    parent = Node()
    if self.background_image:
      background = SpriteNode(Texture(self.background_image))
      background.size = (self.SQ_SIZE * self.DIMENSION_X, self.SQ_SIZE * self.DIMENSION_Y )
      background.position = (0,0)
      background.anchor_point = (0,0)
      parent.add_child(background)  
    if self.use_alpha:
      row_labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    else:
      row_labels = '123456789'
    # Parameters to pass to the creation of ShapeNode
    params = {
      "path": Path.rect(0, 0, self.SQ_SIZE, self.SQ_SIZE * self.DIMENSION_Y),
      "fill_color": self.grid_fill,
      "stroke_color": "darkgrey"
    } 
    anchor = Vector2(0, 0)  
    # Building the columns
    for i in range(self.DIMENSION_X):
      n = ShapeNode(**params)
      pos = Vector2(0 + i * self.SQ_SIZE, 0)    
      n.position = pos
      n.anchor_point = anchor   
      parent.add_child(n)
      n = LabelNode(row_labels[i], parent=self.game_field)
      n.position = (pos.x + self.SQ_SIZE/2, pos.y + self.DIMENSION_Y * self.SQ_SIZE + 20)
    
    # Building the rows
    params["path"] = Path.rect(0, 0, self.SQ_SIZE * self.DIMENSION_X, self.SQ_SIZE)
    params['fill_color'] = 'clear'
    for i in range(self.DIMENSION_Y):
      n = ShapeNode(**params)
      pos = Vector2(0, 0 + i * self.SQ_SIZE)    
      n.position = pos
      n.anchor_point = anchor   
      parent.add_child(n)
      n = LabelNode(str(self.DIMENSION_Y - i), parent=self.game_field)
      n.position = (pos.x - 20, pos.y + self.SQ_SIZE/2)
          
    return parent
    
  def setup_ui(self):
    
    pause_button = SpriteNode('iow:pause_32', position=(32, self.size.h-36), parent=self)
    self.game_field.add_child(self.build_background_grid())
    x, y, w, h = self.game_field.bbox
    font = ('Avenir Next', 32)
    self.msg_label_t = LabelNode("", font=font, position=(0, h +50), parent=self.game_field)
    self.msg_label_t.anchor_point=(0,0)
    self.msg_label_r = LabelNode("", font=font, position=(w +50, h / 2), parent=self.game_field)
    self.msg_label_r.anchor_point=(0,0.5)
    self.msg_label_b = LabelNode("", font=font, position=(0, -50), parent=self.game_field)
    self.msg_label_b.anchor_point=(0,0)
    self.msg_label_b2 = LabelNode("", font=font, position=(0, -100), parent=self.game_field)
    self.msg_label_b2.anchor_point=(0,0)
    self.msg_label_prompt = LabelNode("", font=font, position=(0, -150), parent=self.game_field)
    self.msg_label_prompt.anchor_point=(0,0)
    
    self.enter_button = ShapeNode(ui.Path.rounded_rect(0, 0, 100, 32, 5), position=(w + 200, y), parent=self)
    self.enter_button.anchor_point = (0, 0)
    self.enter_button.line_width=2
    self.enter_button.fill_color = 'clear'
    self.enter_button.stroke_color='white'
    self.enter_label = LabelNode('Enter', position=(w + 205, y+5), parent=self)
    self.enter_label.anchor_point = (0, 0)

  def load_images(self):
    ''' Load images for the chess pieces '''
    for p in self.Player.PIECES:
      if ':' in p:  # internal icon
        self.IMAGES = {player: image for player, image in zip(self.Player.PLAYERS, self.Player.PIECES)}
      #else:
      #  self.IMAGES ={player: "images/" + player + ".png" for player, image in zip(Player.PLAYERS, Player.PIECES)}
      
  def get_piece(self,r,c):
    return self.board[r][c]
    
  def set_player(self, player):
    self.current_player = player
     
  def redraw_board(self):
    ''' Draw the pieces onto the board'''
    # remove existing
    for t in self.get_tiles():
      t.remove_from_parent()

    parent = self.game_field
    for r in range(self.DIMENSION_Y):
      for c in range(self.DIMENSION_X):
        piece = self.get_piece(r, c)
        animation = True
        #animation = False if piece == self.last_board[r][c] else True
        try:
          t = Tile(Texture(self.IMAGES[piece]), 0,0, sq_size=self.SQ_SIZE, dims=(self.DIMENSION_Y, self.DIMENSION_X))
          #t.DIM_Y, t.DIM_X = self.DIMENSION_Y, self.DIMENSION_X
          #t.SQ_SIZE = self.SQ_SIZE
          t.set_pos(r,c,animation=animation)
          t.name = piece + str(r * self.DIMENSION_Y + c)
          t.size = (self.SQ_SIZE-20, self.SQ_SIZE-20)
          parent.add_child(t)
        except (KeyError) as e:
          pass
          
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
      if True : #if not self.tile_at(move):
        t=ShapeNode(ui.Path.rect(0, 0, self.SQ_SIZE, self.SQ_SIZE), fill_color=self.highlight_fill,  position=self.rc_to_pos(move[0], move[1]), parent=self.game_field, alpha=alpha)
        t.anchor_point = (0,0)
        self.highlights.append(move)
        self.hl.append(t)
        
  def add_numbers(self, items): 
    # items is a list of Squares objects
    # items are each a dictionary of (row,col), text, color
    
    self.numbers = []
    
    def add(a,b):
      return tuple(p+q for p, q in zip(a, b))

    for item  in items:
        r, c = item.position
        t=ShapeNode(ui.Path.rounded_rect(0, 0, self.SQ_SIZE, self.SQ_SIZE, item.radius), fill_color=item.color,  position=self.rc_to_pos(r, c), 
        stroke_color=item.stroke_color,
        parent=self.game_field)
        t.anchor_point = (0,0)
        self.numbers.append(t)     
           
        t1 = LabelNode(str(item.text), color=item.text_color, font=item.font, position=add(self.rc_to_pos(r, c),(self.SQ_SIZE/2, self.SQ_SIZE/2)), parent=self.game_field)
        t1.anchor_point = (0.5,0.5)
        
        self.numbers.append(t1)
        
  def clear_highlights(self):
    if hasattr(self, 'hl'):
      for t in self.hl:
        t.remove_from_parent()
    self.highlights = []
    self.hl = []
      
  def draw_text(self, text):
    self.status_label.text = text
    #self.status_label.size = (146,44)
  
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
          
            
  def turn_status(self,turn): 
      self.status_label.text = "white turn" if turn else "black turn"
      #self.status_label.size = (146,44)
      
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
  
  def touch_began(self, touch):
    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.show_pause_menu()
      return
    elif self.enter_button.bbox.contains_point(touch.location):
      return
    else:
      t = touch.location 
      rc = self.point_to_rc(t)
      self.last_rc = rc
      self.touch_indicator = Tile(self.IMAGES[self.current_player], rc, sq_size=self.SQ_SIZE, dims=(self.DIMENSION_Y, self.DIMENSION_X))
      #self.touch_indicator.anchor_point = (0.5, 0.5)
      self.game_field.add_child(self.touch_indicator)

  def touch_moved(self, touch):
    if self.touch_indicator:
      self.touch_indicator.set_pos(self.point_to_rc(touch.location))
      rc = self.point_to_rc(touch.location)
      if self.use_alpha:
        c = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z '
      else:
        c =  '1 2 3 4 5 6 7 8 9 1011121314151617181920'
      r = '1 2 3 4 5 6 7 8 9 1011121314151617181920'                  
      y,x = rc[0], rc[1]        
      msg = c[2* x: 2*x+2] + r[2*y:2*y+2]
      msg = msg.replace(' ', '')
      self.enter_label.text = f'{y},{x}__{msg}'
    
  def touch_ended(self, touch):
    
    if self.touch_indicator:
      self.touch_indicator.remove_from_parent()
      self.touch_indicator = None      
    logger.debug('touch ended')
  
    rc = self.point_to_rc(touch.location)
    if (rc == self.last_rc) and self.require_touch_move:
      # not moved       
      return
           
    if list(rc) in self.highlights or self.allow_any_square:
      self.board[rc[0]][rc[1]] = self.current_player
      if self.q:
        self.q.put(rc)
      self.clear_highlights()
      # update gui 
      self.redraw_board()                     
      #self.board_print()
      
  def point_to_rc(self,point):
    """ covert touch point to rc tuple """  
    col = int((point.x - GRID_POS[0]) / (self.SQ_SIZE))
    row = self.DIMENSION_Y - 1  - int((point.y - GRID_POS[1]) / (self.SQ_SIZE))
    return row, col

  def rc_to_pos(self,row,col):
    """ covert col row  to Point object in game field coordinates
    row, col are in (0,0) is topleft
    x,y is (0,0 is bottom right) """
    bbox = self.game_field.bbox # x,y,w,h
    row = self.DIMENSION_Y - 1 - row
    x = col * self.SQ_SIZE
    y = row * self.SQ_SIZE
    return Point(x,y)
    
  def get_tiles(self):
    """
    Returns an iterator over all tile objects
    """
    
    for o in self.game_field.children:
      if isinstance(o, Tile) :
        yield o
        
  def tile_at(self, row, col=None, multi=False):
    '''select tile'''
    tiles=[]
    if isinstance(row,(tuple,list)):
      r,c = row[0], row[1]
    else:
      r, c = row, col
    r =  self.DIMENSION_Y -1 - r 
    
    for t in self.get_tiles():
      if t.row == r and t.col == c :
        if multi ==False:
          return t
        else:
          tiles.append(t)
    if tiles:
      return tiles
    else:
      return None
    
  def square_at(self, row, col=None):
    '''select tile'''
    if isinstance(row,(tuple,Point)):
      r,c = row
    else:
      r, c = row, col
    return self.squares[(r,c)]  

  def clear_squares(self):
    for t in self.squares.values():
      t.remove_from_parent()
    self.squares = {}
    
  def clear_numbers(self):
    for t in self.numbers:
      t.remove_from_parent()
    self.numbers = []
          
  def tile_drop(self, rc, selected):
    """ move tile to new location   """
    if selected :
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
      print('waiting for close')
      sleep(.2)
      
    
  def show_pause_menu(self):
    self.menu = MyMenu('Paused', '', [i for i in self.pause_menu])
    self.present_modal_scene(self.menu)

  def show_start_menu(self):    
    self.menu = MyMenu('New Game?','', [i for i in self.start_menu])
    self.present_modal_scene(self.menu) 

  def menu_button_selected(self, title):
    """ Pass back selected item to main program loop
    menu items are passed a dictionary of title: functions """
    if title in self.pause_menu:
      fn_ = self.pause_menu[title] 
      self.dismiss_modal_scene()
      self.menu = None
      #print(f' putting {fn_} to queue') 
      self.q.put(fn_) 
                  
    elif title in self.start_menu:
      fn_ = self.start_menu[title]      
      self.dismiss_modal_scene()
      self.menu = None
      #print(f' putting {fn_} to queue') 
      self.q.put(fn_) 
  
    else: 
      self.dismiss_modal_scene()     
      self.menu = None 
      
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
      self.bg.position = self.size.w * 0.5, self.size.h *0.6
    else:
      self.bg.position = self.size.w * 0.85, self.size.h * 0.5
    self.menu_bg.position = self.bg.position

if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',level=logging.WARNING)   
  run(GameBoard(), LANDSCAPE, show_fps=True)
    


