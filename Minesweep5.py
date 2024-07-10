"""
The game of minesweeper using Pythonista
uses Tile objects to store options
long press on tile more than 0.5 sec to mark bomb

modified to all ui with buttons
"""
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from scene import *
import ui
import sound
import random
from random import randint
from queue import Queue
from gui.game_menu import MenuScene
import gui.gui_scene as gscene
from Word_Games.Letter_game import LetterGame, Player, Word
from gui.gui_interface import Gui, Squares
from time import sleep
import console

UPDATE = 1
                    
def intersects_sprite(point, sprite):
  norm_pos = Vector2()
  norm_pos.x = sprite.position.x - (sprite.size.w * sprite.anchor_point.x)
  norm_pos.y = sprite.position.y - (sprite.size.h * sprite.anchor_point.y)
  
  return (point.x >= norm_pos.x and point.x <= norm_pos.x + sprite.size.w) and (
          point.y >= norm_pos.y and point.y <= norm_pos.y + sprite.size.h)
  
  
class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, color=None, row=0, col=0, tsize=48, bsizex=10, bsizey=0):
    SpriteNode.__init__(self, Texture('pzl:Gray3'))
    if color is None:
      self.texture = Texture('pzl:Gray3')
    else:
      self.color = color
    self.tsize = tsize
    self.bsizex = bsizex
    self.bsizey = bsizey
    self.size = (tsize, tsize)
    self.scale = 1.0
    self.anchor_point = (0.5, 0.5)
    self.type = '-'  # options are  -, #, 0-9
    self.set_pos(col, row)
  
  def set_pos(self, col=0, row=0):
    """
    Sets the position of the tile in the grid.
    """
    self.col = col
    self.row = row
    pos = Vector2()
    pos.x = int(self.size.w / 2) + (self.tsize * col) + 50
    pos.y = int(self.size.h / 2) - (self.tsize * row) + int(self.bsizey * self.tsize)
    self.position = pos

  def set_texture(self, image):
    self.texture = Texture(image)
    self.size = (self.tsize, self.tsize)


class App(LetterGame):
  
  def __init__(self):
    self.debug = True
    self.cheat = False
    self.background_color = '#828adb'
    self.sleep_time = 0.1
    # allows us to get a list of rc locations
    self.log_moves = False
    self.straight_lines_only = False
    self.hint = False
    #self.load_words_from_file(WordList)
    #self.initialise_board() 
    # create game_board and ai_board
    self.SIZE = self.get_size('9,9') 
    
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(False) 
    self.gui.set_grid_colors(grid='black', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=False) # SQ_SIZE=45)
    
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.run, 'Quit': self.quit})
    
  def setup(self, level=None):
    # turn cheat to True to see the mines while playing
    self.cheat = False
    self.background_color = '#828adb'
    self.grid = None
    
    try:
      button = self.view.superview['button_hint']
      button.action = self.hint
      for i in ['button_beg', 'button_int', 'button_exp', 'button_quit']:
        button = self.view.superview[i]
        button.action = self.button_tapped
        button.enabled = False
        button.background_color='grey'
    except(Exception) as e:
      pass
    # tile color according values
    self.tileColor = {
    "0": 'pzl:Green3', "1": 'pzl:Blue3', "2": 'pzl:Yellow3',
    "3": 'pzl:Red3', "4": 'pzl:Red3', "5": 'pzl:Red3',
    "6": 'pzl:Red3', "7": 'pzl:Red3', "-": 'pzl:Gray3', "#": 'pzl:Gray3'}
 
    # TSIZE BSIZEX BSIZEY no mines
    if not self.view.superview:
      self.size_dict = {"Beginner": (48, 9, 9, 10), 
      "Intermediate": (40, 16, 16, 40),
      "Expert": (30, 30, 16, 99)}
    else:
      self.size_dict = {"Beginner": (48, 9, 9, 10), 
      "Intermediate": (28, 16, 16, 40),
      "Expert": (19, 30, 16, 99)}
          
    if level is None:
      self.level = "Beginner"
    else:
      self.level = level
    self.TSIZE, self.BSIZEX, self.BSIZEY, self.no_mines = self.size_dict[self.level]
    if self.size.w < 1000 and not self.view.superview:
      self.TSIZE /= 2
    self.marked = []
    self.labelFont = ('Adidas Unity', self.TSIZE)
    self.start = True
    self.game_status = ''
    self.run_time = 0
    self.update_timer = UPDATE
    
    self.board_obj = self.set_mines()
    self.setup_board()

  def find_tile(self, row, col):
    for x in self.board_obj:
      if x.row == row and x.col == col:
        return x
    return None 
           
  def hint(self, sender):
    """ this function only functions in ui view"""
    for t in self.board_obj:
      if t.type=='#':
        if (t.row,t.col) in self.marked:
          continue
        else:
          # check surrounding tiles, only reveal if next to other tiles
          for y in [-1,1]:
            for x in [-1,1]:
              tile = self.find_tile(t.row + y, t.col + x)
              if tile and tile.type in '0123456':
                self.marked.append((t.row, t.col))
                self.grid.add_child(SpriteNode(Texture('emj:Cross_Mark'),
                                               position=t.position, scale=0.5))
                return
    console.hud_alert('No more hints','error',1)    
      
  def set_mines(self):
    """ randomly install the mines on the board,
    '-' = empty space and '#' = mine
    assume a square board
    """
    self.board_obj = [Tile(None, row, col, self.TSIZE, self.BSIZEX, self.BSIZEY) 
                      for row in range(self.BSIZEY) for col in range(self.BSIZEX)]

    for i in range(self.no_mines):
      t = self.find_tile(randint(0, self.BSIZEY-1), randint(0, self.BSIZEX-1))
      if t:
        t.type = '#'
    return self.board_obj

  def touch_began(self, touch):
    self.touch_location = touch.location
    self.touch_time= self.t
   
  def touch_ended(self, touch):
    touch_length = self.t - self.touch_time
    if touch_length > 0.5:
      self.long_touch()
    else:
      self.update_all()

  def long_touch(self):
    # implement guess of bomb position
    for t in self.board_obj:
      if intersects_sprite(self.touch_location, t):
        self.grid.add_child(SpriteNode(Texture('emj:Cross_Mark'),
                                               position=t.position, scale=0.5))
        self.marked.append((t.row,t.col))
        break
        
  def select_list(self):
      '''Choose which category'''
      
      self.size_dict = {"Beginner": (48, 9, 9, 10), 
      "Intermediate": (40, 16, 16, 40),
      "Expert": (30, 30, 16, 99)}
      items =  list(self.size_dict)
      #return selection
      self.gui.selection = ''
      selection = ''
      prompt = ' Select category'
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800,0))
        while self.gui.text_box.on_screen:    
          try:
            selection = self.gui.selection
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
            
        if len(selection) > 1:
          self.wordlist = self.size_dict[selection]
          self.puzzle = selection
          self.gui.selection = ''
          return True
        elif selection == "Cancelled_":
          return False
        else:
            return False   
            
  def run(self):
    selected = self.select_list()
    
  def setup_board(self):
    """ draw a new board and add all tiles """
    self.grid = Node(parent=self)
    for t in self.board_obj:
      self.grid.add_child(t)
    self.update_board()
    self.status_label(0,color="#000000")

  def update(self):
    self.update_timer -= self.dt
    if self.update_timer <= 0:
      self.update_timer = UPDATE
      self.run_time += 1  
      self.time_label.text = str(self.run_time)   
    
  def update_board(self):
    """ called on every key press """
    for t in self.board_obj:
      if self.cheat and t.type == '#':
        self.grid.add_child(SpriteNode(Texture('emj:Bomb'),
                                                 position=t.position, scale=0.5))

      if t.type != "-" and t.type != "#":
        self.grid.add_child(LabelNode(t.type, self.labelFont,
                                          position=t.position, scale=0.5))
        t.set_texture(self.tileColor[t.type])

  def status_label(self, label, color):
    """display time"""
    self.time_label = LabelNode(str(label), ('Anantason', 12),
                                  position=(80, 20),
                                  scale=3, color=color)
    self.grid.add_child(self.time_label)

  def update_all(self):
    # check for touch input. is touch input on the board
    found = False
    for tile in self.board_obj:
      if intersects_sprite(self.touch_location, tile):
        sound.play_effect('8ve:8ve-beep-shinymetal')
        if self.start:
          found = True
          break

    if found:
      # check if user touched on the mine
      if tile.type == "#":
        self.start = False
        self.game_status = 'LOSE!'
      else:
        # else reveal the number of mines that surround the tile
        self.board_obj = self.zero_scanning(tile)

      self.found_space = False
      # check if all tiles are revealed
      for t in self.board_obj:
        if t.type == '-':
          self.found_space = True
          break

      # if there is no empty tile left = win!
      if self.found_space is False:
        self.game_status = 'WIN!'
        self.start = False
      if self.start:
        self.update_board()
      # if game ends
      else:
        # reveals the mine
        self.cheat = True
        self.start = False
        self.update_board()
        if self.game_status:
          self.show_start_menu()

  def count_mines(self, tile):
    """return number of mines around current tile"""
    count = 0
    # check surrounding tiles
    for y in range(-1, 2):
      for x in range(-1, 2):
        t = self.find_tile(tile.row + y, tile.col + x)
        if t and t.type == '#':
          count += 1
    return str(count)

  def zero_scanning(self, start_tile):
    """ recursive routine to uncover adjacent zeros"""
    start_tile.type = self.count_mines(start_tile)
    start_tile.set_texture(self.tileColor[start_tile.type])
    if start_tile.type == '0':
      for x in range(-1, 2):
        for y in range(-1, 2):
          t = self.find_tile(start_tile.row + y, start_tile.col + x)
          try:
            if self.count_mines(t) == "0" and t.type != '0':
              self.zero_scanning(t)
            else:
              t.type = self.count_mines(t)
          except (AttributeError):
            pass
    return self.board_obj
          
  def clear(self):
    for t in self.grid.children:
      t.remove_from_parent()
      
    
  def button_tapped(self,sender):
    self.menu_button_selected(sender.title)
    for i in ['button_beg', 'button_int', 'button_exp', 'button_quit']:
      button = self.view.superview[i]
      button.enabled = False
      
  def show_start_menu(self):
    try:
      for i in ['button_beg', 'button_int', 'button_exp', 'button_quit']:
        button = self.view.superview[i]
        button.enabled = True
        button.background_color='lightgreen'
        
    except(Exception):
      self.menu = MyMenu(self.game_status,
      'New Game?', ['Beginner', 'Intermediate', 'Expert', 'Quit'])
      self.present_modal_scene(self.menu)
    
  def menu_button_selected(self, title):
    """ choose to play again or quit """
    if title == "Quit":
      self.view.close()
      try:
        self.view.superview.close()
      except(AttributeError):
        pass
    else:
      # start again
      self.clear()
      self.dismiss_modal_scene()
      self.menu = None
      self.setup(title)

            
class MyMenu(MenuScene):
  """ subclass MenuScene to move menu to right """
  def __init__(self, title, subtitle, button_titles):
    MenuScene.__init__(self, title, subtitle, button_titles)
    
  def did_change_size(self):
    # 834,1112 ipad portrait
    # 1112, 834 ipad landscape
    # 852, 393 iphone landscape

    self.bg.size = (1, 1)
    self.bg.position = self.size.w * 0.85, self.size.h / 2
    self.menu_bg.position = self.bg.position

TYPE = "scen"
if __name__ == '__main__':
  g= App()
  g.run()


