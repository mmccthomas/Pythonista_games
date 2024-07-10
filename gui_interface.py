# this module is an interface layer to the lower level graphics below
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

import gui.gui_scene as gscene
from gui.gui_scene import BoxedLabel

class Gui():
  # allow for non square board
  # use DIMENSION_X and DIMENSION_Y
  
  def __init__(self, board, player):
    
    self.v = SceneView()
    self.v.scene = gscene.GameBoard()
    self.wh = get_screen_size()
    self.v.present('sheet')
    self.gs = self.v.scene
    self.gs.board = list(map(list, board)) #board.copy()
    self.gs.Player = player
    self.player = player
    self.gs.DIMENSION_Y = len(self.gs.board)
    self.gs.DIMENSION_X = len(self.gs.board[0])
    self.use_alpha = True
    self.q = None
    self.selection = ''
    self.selection_row = 0
    self.button_index = 2
    self.dismiss_menu = self.gs.dismiss_modal_scene
    self.device = self.gs.device
    self.long_touch = self.gs.long_touch

    # menus can be controlled by dictionary of labels and functions without parameters
    self.gs.pause_menu = {'Continue': self.gs.dismiss_modal_scene,  
                           'Quit': self.gs.close}
    self.gs.start_menu = {'New Game': self.gs.dismiss_modal_scene,  
                           'Quit': self.gs.close}
                           
  def input_text_list(self, prompt='', position=None,items=None,**kwargs):
    ''' show a single line text box with an ok and a cancel button
    try to adapt size to number of list items'''
    if position is None:
      # place to right of game field
      x, y, w, h = self.gs.game_field.bbox
      position = (x + w +100, 40)
    self.font = ('Avenir Next', 32)
    self.allows_multiple_selection = False
    
    for k,v in kwargs.items():
      setattr(self, k,v)
      
    # allow for 2 lines of prompt
    self.text_box = ui.View(bg_color='lightgrey',frame=(position[0], position[1], 200, 550))    
    lb = ui.ButtonItem(image=ui.Image.named('iob:close_32'), enabled = True, 
                       action = self.cancel)
    self.text_box.left_button_items=[lb]
    self.data = ui.ListDataSource(items=items)
    if self.allows_multiple_selection:
        pass
    else:
        self.data.action = self.text_input
    # set table size to hold data
    no_items = len(items)
    req_height = no_items * self.font[1] * 1.40
    height = min(req_height, 400)
    self.t = ui.TableView(name='text',frame=(10,45, 170, height), font=self.font, 
                     text_color = 'black', bordered=True)
    # change frame size to fit list
    self.text_box.frame=(0, 0, 200, height + 55)
    self.t.data_source = self.t.delegate = self.data
    self.t.allows_multiple_selection = self.allows_multiple_selection
    self.text_box.add_subview(self.t)
    
    label = ui.Label(frame = (5,5, 180, 40), font = ('Avenir Next', 18), 
                     text=prompt, number_of_lines=0, line_break_mode=ui.LB_WORD_WRAP)
    self.text_box.add_subview(label)
    if self.allows_multiple_selection:
      # Enter button
      rb = ui.ButtonItem(image=ui.Image.named('iob:arrow_return_left_32'), action=self.enter)
      self.text_box.right_button_items=[rb]
       
    if self.gs.device.startswith('ipad'):
       self.text_box.present('popover', popover_location = position)
    else: # iphone
     self.text_box.present('sheet')
    # self.v.add_subview(self.text_box) 
    return self.text_box
  
  def enter(self, sender):
    ''' completes multiple selection '''
    selected_rows = self.t.selected_rows # a list of (section, row)
    data = [self.data.items[row] for _, row in selected_rows]
    self.selection = data
    self.selection_rows = self.t.selected_rows
    try:
        sender.superview.close()
        # self.v.remove_subview(self.text_box)  
    except(AttributeError):
        self.text_box.close() 
        # self.v.remove_subview(self.text_box)   
    
  def text_input(self, sender):
    self.selection = sender.items[sender.selected_row]
    self.selection_row = sender.selected_row
    sender.tableview.superview.close()
    # self.v.remove_subview(self.text_box)  
    
  def cancel(self, sender):
    self.selection = 'Cancelled_'
    try:
        sender.superview.close() 
        # self.v.remove_subview(self.text_box)  
    except(AttributeError):
        self.text_box.close()
        # self.v.remove_subview(self.text_box)  
       
  def button_tapped(self, sender):
    '@type sender: ui.Button'
    # Get the button's title for the following logic:
    t = sender.title
    # get calling item
    if hasattr(self, 'number_panel'):
      self._panel = self.number_panel
      self._itemlist = self.number_items
    else:
      self._panel = self.letter_panel
      self._itemlist = self.letter_items
      
    # Get the labels:
    label = sender.superview['label1']
    if t in '0123456789':    
        if not self.number_panel.allows_multiple_selection:
          sender.background_color='yellow'
          self.selection = t
          self.selection_row = None
          sender.background_color='white'
          sender.superview.close()
          self.v.remove_subview(self.number_panel)
        else:
            sender.background_color='yellow'
            if t in self.number_items:
                  self.number_items.remove(t)
                  sender.background_color='white'
            else: 
                self.number_items.append(t)
                self.prompt.text = ' '.join(self.number_items)
            
                
    elif t in 'abcdefghijklmnopqrstuvwxyz ':
         if not self.letter_panel.allows_multiple_selection:
            sender.background_color='yellow'
            self.selection = t
            self.selection_row = None
            sender.background_color='white'
            sender.superview.close()
            self.v.remove_subview(self.letter_panel)
         else:
            sender.background_color='yellow'
            self.letter_items.append(t)  
            self.prompt.text = ' '.join(self.letter_items)
          
    elif t == 'Return':
       # send selected items
       self.selection = self._itemlist.copy()
       if hasattr(self, 'letter_panel'):
           self.selection_row = self._panel.direction
       self.v.remove_subview(self._panel)
       
       
       for button in self.buttons:
          button.background_color='white'
       sender.superview.close()
       
    elif t == 'Delete':
       # remove last item
       if self._itemlist:
          removed = self._itemlist.pop()
          self.prompt.text = ' '.join(self._itemlist)
          self._panel[f'button{removed}'].background_color='white'       
    
    elif t == 'Across' or t == 'Down':
       # change across or down direction
       self.letter_panel.direction = self.across_down(t)              
              
  def across_down(self, direction):
      # a = {'across': (False, 'yellow'), 'down': (True, 'white')}
      if  direction == 'Across':
              self._panel[f'button_across'].enabled = False
              self._panel[f'button_down'].enabled = True
              self._panel[f'button_down'].background_color='white'
              self._panel[f'button_across'].background_color='yellow'
      else: 
              self._panel[f'button_across'].enabled = True
              self._panel[f'button_down'].enabled = False
              self._panel[f'button_down'].background_color='yellow'
              self._panel[f'button_across'].background_color='white'      
      return direction
  
  def input_numbers(self, prompt='', position=None, items=None, **kwargs):
    """ pop up a number panel """
    self.number_panel = ui.load_view('../gui/Number_panel.pyui')
    self.buttons = [self.number_panel[f'button{n}'] for n in range(1,10)]
    self.prompt= self.number_panel['prompt']
    self.prompt.text = prompt
    self.prompt.font = ('Avenir Next', 30)
    self.position = position
    self.number_panel.frame = (self.position[0], self.position[1], 357, 306)
    self.number_panel.allows_multiple_selection = False  
    for k,v in kwargs.items():
      setattr(self.number_panel, k,v)     
    self.number_items = []
    self._panel = self.number_panel
    self._itemlist = self.number_items
    self.v.add_subview(self.number_panel)
    return self.number_panel
    
  def input_letters(self, prompt='', position=None, items=None, **kwargs):
    """ pop up a letter panel """
    self.letter_panel = ui.load_view('../gui/Letter_panel.pyui')
    self.buttons = [self.letter_panel[f'button{n}'] for n in 'abcdefghijklmnopqrstuvwxyz ']
    self.prompt= self.letter_panel['prompt']
    self.prompt.text = prompt
    self.prompt.font = ('Avenir Next', 30)
    self.position = position
    self.letter_panel.frame = (self.position[0], self.position[1], 345, 550)
    self.letter_panel.allows_multiple_selection = False       
    self.letter_panel.direction = 'Across'
    for k,v in kwargs.items():
      setattr(self.letter_panel, k,v)  
    self.letter_items = []
    self._panel = self.letter_panel
    self._itemlist = self.letter_items
    self.across_down(self.letter_panel.direction.capitalize())
    
    self.v.add_subview(self.letter_panel)
    return self.letter_panel
         
  def set_grid_colors(self, grid=None, highlight=None, z_position=10):
    if grid is not None:
      try:          
          image = ui.Image.named(grid)
          self.gs.grid_fill = 'clear'
          self.gs.background_image = image
      except (Exception) as e:
          print('error in set_grid_colors', e)
          if grid.startswith('#') or ui.parse_color(grid)!=(0.0,0.0,0.0,0.0):
            self.gs.grid_fill = grid
            
    self.gs.grid_z_position = z_position   
    if highlight is not None:
       self.gs.highlight_fill = highlight
       
  def get_device(self):
    # returns string ipad_landscape, ipad_portrait, 
    #.               iphone_landscape, iphone_portrait
    return self.gs.device
        
  def setup_gui(self,**kwargs):
     self.gs.setup_gui(**kwargs)
     self.game_field = self.gs.game_field
     self.grid = self.gs.grid
     
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
    
  def set_enter(self, msg, **kwargs):
    # modify existing enter button BoxedLabel object
    self.gs.enter_button.set_props(**kwargs)  
    self.gs.enter_button.set_text(msg)  
    return self.gs.enter_button      
  
  def set_props(self, button_str, **kwargs):
    # modify existing button BoxedLabel object
    b = getattr(self.gs, button_str)
    if 'anchor_point' in kwargs:
       print(f'anchor_point not supported for {button_name}')
       kwargs.pop('anchor_point')
    b.set_props(**kwargs)        
    
  def set_text(self, button_str, msg, **kwargs):
    # modify existing enter button BoxedLabel object
    b = getattr(self.gs, button_str)
    b.set_props(**kwargs)  
    b.set_text(msg)      
    
  def add_button(self, text='button', title='title', position=(100,100), min_size=(100, 50), reg_touch=False, **kwargs):
     # create a gui button that can invoke action if reg_touch is true
     box = BoxedLabel(text=text, title=title, position=position, min_size=min_size, parent=self.gs.game_field)
     box.set_index(self.button_index)
     button_name = f'button_{self.button_index}'
     setattr(self.gs, button_name, box)
     button = getattr(self.gs, button_name)
     if reg_touch:
         self.gs.buttons[self.button_index] = box
     if 'anchor_point' in kwargs:
       print(f'anchor_point not supported for {button_name}')
       kwargs.pop('anchor_point')
     button.set_props(**kwargs)            
     self.button_index += 1
     return button_name
     
  def update(self, board=None, fn_piece=None):
    ''' if board, it is a single [row,col] '''
    self.gs.board = list(map(list, board)) # board.copy()
    self.gs.redraw_board(fn_piece=fn_piece)
    
  def add_numbers(self, items, clear_previous=True, **kwargs):
    # items are each an instance of Swuares object
    self.gs.add_numbers(items, clear_previous, **kwargs)
    
  def replace_numbers(self, items, **kwargs):
    # items are each an instance of Swuares object
    self.gs.replace_numbers(items, **kwargs)
    
  def get_numbers(self, coords):
    return self.gs.get_numbers(coords)
    
  def put_numbers(self, items, **kwargs):
    self.gs.put_numbers(items, **kwargs)
      
  def clear_numbers(self, number_list=None):
    # allow for clearing some highlighted squares
    try: 
      self.gs.clear_numbers(number_list)
    except (AttributeError):
      pass
  
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
    
  def clear_squares(self):
    self.gs.clear_squares()
    
  def clear_messages(self):
    self.set_message2('')
    self.set_message('')
    self.set_top('')
    self.set_prompt('')
    self.set_enter('')
    self.set_moves('')
    
  def show_start_menu(self):
    # pass start_menu call to gs_scene
    self.gs.show_start_menu()
    
  def set_pause_menu(self, menu_dict):
    self.gs.pause_menu = menu_dict
    
  def set_start_menu(self, menu_dict):
    self.gs.start_menu = menu_dict 
    
  def build_extra_grid(self, grids_x, grids_y, grid_width_x=None, grid_width_y=None, color=None, line_width=2, z_position=100):
     self.gs.build_extra_grid(grids_x, grids_y, 
                              grid_width_x=grid_width_x, grid_width_y=grid_width_y, 
                              color=color, line_width=line_width, z_position=z_position)
                              
  def draw_line(self, coords, **kwargs):
    self.gs.draw_line(coords, **kwargs)
                               
  def rc_to_pos(self, coord): 
    return self.gs.rc_to_pos(coord[0], coord[1])

class Coord(tuple):
    ''' a simple class to allow addition and slicing'''
    
    def __init__(self, val):
        self.val = val
        
    def __add__(self, other):
       return tuple(p+q for p, q in zip(self.val, other))
       
    def __sub__(self, other):
        return tuple(p-q for p, q in zip(self.val, other))
        
    def col(self):
      return self.val[1]
    
    def row(self):
      return self.val[0]
      
    def c(self):
      return self.val[1]
    
    def r(self):
      return self.val[0]
    
class Squares():
  ''' holds parameters for coloured squares'''
  def __init__(self, position, text=' ',color='clear', **kwargs):
    
    self.position = position
    self.text = text
    self.color = color
    self.radius = 1
    self.z_position = 20
    self.alpha = .5
    self.text_anchor_point = (0.5, 0.5)
    
    self.stroke_color = 'black'
    self.text_color = 'black'
    self.font_size = 24
    self.font = ('Avenir Next', self.font_size)
    
    for k, v in kwargs.items():
      setattr(self, k, v)
      


