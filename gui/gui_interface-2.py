from scene import *
import ui
import sys
import time
import os
import console
from queue import Queue

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)

import util.gui.gui_scene as gscene

class Gui():
  # TODO Deal with menu buttons in gui
  # 'H': coord, linesWrittenToConsole = getBoardHistoryInputFromUser
  # allow for non square board
  # use DIMENSION_X and DIMENSION_Y
  
  def __init__(self, board, player):
    
    self.v = SceneView()
    self.v.scene = gscene.GameBoard()
    w,h = get_screen_size()
    self.v.present('sheet')
    self.gs = self.v.scene
    self.gs.board = list(map(list, board)) #board.copy()
    self.gs.Player = player
    self.player = player
    self.gs.DIMENSION_Y = len(self.gs.board)
    self.gs.DIMENSION_X = len(self.gs.board[0])
    self.use_alpha = True
    self.q = None
    


    # menus can be controlled by dictionary of labels and functions without parameters
    self.gs.pause_menu = {'Continue': self.gs.dismiss_modal_scene,  
                           'Quit': self.gs.close}
    self.gs.start_menu = {'New Game': self.gs.dismiss_modal_scene,  
                           'Quit': self.gs.close}
                           
  def set_grid_colors(self, grid=None, highlight=None):
    if grid is not None:
      try:          
          image = ui.Image.named(grid)
          self.gs.grid_fill = 'clear'
          self.gs.background_image = image
      except (Exception) as e:
          print('error in set_grid_colors', e)
          if grid.startswith('#') or ui.parse_color(grid)!=(0.0,0.0,0.0,0.0):
            self.gs.grid_fill = grid
        
    if highlight is not None:
       self.gs.highlight_fill = highlight
       
  def setup_gui(self):
     self.gs.setup_gui()
     
  def require_touch_move(self, require=True):
    self.gs.require_touch_move = require
    
  def allow_any_move(self, allow=False):
    self.gs.allow_any_square = allow
     
  def set_player(self, current_player, Player):
    self.gs.Player = Player()
    self.gs.current_player = current_player 
                           
  def set_alpha(self, mode=True):
    # allows for column numbers to be letters or numbers
    self.use_alpha = mode
    self.gs.use_alpha = mode
          
  def set_prompt(self, msg, **kwargs):
    # lowest level at bottom
    for k, v in kwargs.items():
      setattr(self.gs.msg_label_prompt, k, v)
    self.gs.msg_label_prompt.text = msg
    
  def set_message(self, msg, **kwargs):
    # message below box
    for k, v in kwargs.items():
      setattr(self.gs.msg_label_b, k, v)
    self.gs.msg_label_b.text = msg
    
  def set_message2(self, msg, **kwargs):
    # message below box
    for k, v in kwargs.items():
      setattr(self.gs.msg_label_b2, k, v)
    self.gs.msg_label_b2.text = msg
    
  def set_top(self, msg, **kwargs):
    # message above box
    for k, v in kwargs.items():
      setattr(self.gs.msg_label_t, k, v)
    self.gs.msg_label_t.text = msg
     
  def set_moves(self, msg, **kwargs):
    # right box
    for k, v in kwargs.items():
      setattr(self.gs.msg_label_r, k, v)
    self.gs.msg_label_r.text = msg
    
  def update(self, board=None):
    ''' if board, it is a single [row,col] '''
    self.gs.board = list(map(list, board)) # board.copy()
    self.gs.redraw_board()
    
  def add_numbers(self, items):
    # items are each an instance of Swuares object
    self.gs.add_numbers(items)
  
  def valid_moves(self, validmoves, message=True, alpha=1.0):
    """ add highlights to show valid moves """
    msg = [self.ident(move) for move in validmoves] 
    if message: 
      self.set_message2('valid:  ' + ', '.join(msg))
    self.gs.highlight_squares(validmoves,alpha=alpha)
    
  def get_board(self):
    return self.gs.board
    
  def changed(self, board):
    """ get gui copy of board
    iterate until a difference is seen
    return row, column of different cell
    """
    gui_board = self.get_board()
    for j, row in enumerate(board):
      for i, col in enumerate(row):
        if gui_board[j][i] != col:
          return j, i
    return None
    
  def ident(self, changed):
    # change rc to ident A1 or 11
    if self.use_alpha:
      c = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z '
    else:
      c =  '1 2 3 4 5 6 7 8 9 1011121314151617181920'
    r = '1 2 3 4 5 6 7 8 9 1011121314151617181920'
           
    y = changed[0]
    x = changed[1]
        
    msg = c[2* x: 2*x+2] + r[2*y:2*y+2]
    msg = msg.replace(' ', '')
    return  msg
    
  def wait_for_gui(self, board):
    # loop until gui board is not same as local version
    while True:
      # if view gets closed, quit the program
      # self.dump_board(self.get_board(), 'gui')
      # self.dump_board(board, '')
      if not self.v.on_screen:
        print('View closed, exiting')
        sys.exit() 
        break   
      if  self.get_board() != board:
        break
      time.sleep(0.5)
      
    coord = self.ident(self.changed(board))
    # print('changed' , self.changed(board), coord)
    return coord
    
  def dump(self):
    tiles = [t.name for t in self.gs.get_tiles()]
    print('gui:', tiles)
        
  def dump_board(self, board, which=None):
    items = []
    for j, row in enumerate(board):
      for i, col in enumerate(row):
        cell = board[j][i] 
        if cell != self.player.EMPTY:
          items.append(f"{cell}{j}{i}")
    print('board:', which, items)
  
  def print_board(self, board, which=None):
    print('board:', which)
    for j, row in enumerate(board):
      for i, col in enumerate(row):
        print(board[j][i], end=' ')
      print() 
    
  def input_message(self, message):
    response = console.input_alert(message)
    return response
  
        

class Squares():
  ''' holds parameters for coloured squares'''
  def __init__(self, position, text=' ',color='clear', **kwargs):
    
    self.position = position
    self.text = text
    self.color = color
    self.radius = 1
    
    self.stroke_color = 'black'
    self.text_color = 'black'
    self.font_size = 24
    self.font = ('Avenir Next', self.font_size)
    
    for k, v in kwargs.items():
      setattr(self, k, v)
      
    
