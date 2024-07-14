"""
The game of minesweeper using Pythonista
uses Tile objects to store options
long press on tile more than 0.5 sec to mark bomb

modified to all ui with buttons
This version uses gui_interface Gui framework
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
from gui.gui_scene import Tile
import Word_Games.Letter_game as lg
from Word_Games.Letter_game import LetterGame
from gui.gui_interface import Gui, Squares, Coord
from time import sleep, time
import console

UPDATE = 1
ENTER = (-1, -1)                   

class Player():
  def __init__(self):    
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  ='01234567-#x'
    self.PIECES = ['pzl:Green3', 'pzl:Blue3', 'pzl:Yellow3',
                   'pzl:Red3', 'pzl:Red3', 'pzl:Red3',
                   'pzl:Red3', 'pzl:Red3', 'pzl:Gray3','pzl:Gray3', 'emj:Cross_Mark']
  
    self.PLAYERS = None

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
    # create game_board and ai_board
    self.SIZE = self.get_size('9x9') 
    
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(False) 
    self.gui.set_grid_colors(grid='black', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True) 
    self.select_list()
    self.setup(self.puzzle)
    self.gui.gs.DIMENSION_X, self.gui.gs.DIMENSION_Y  = self.wordlist[1], self.wordlist[2]
    #self.gui.gs.board=self.board_obj
    self.gui.setup_gui(log_moves=False, board=self.board_obj)
    
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.run, 'Quit': self.quit})
    #self.setup()
    
  def setup(self, level=None):
    # turn cheat to True to see the mines while playing
    self.cheat = False
    self.background_color = '#828adb'
    self.grid = None
    
    
    # tile color according values
    self.tileColor = {
    "0": 'pzl:Green3', "1": 'pzl:Blue3', "2": 'pzl:Yellow3',
    "3": 'pzl:Red3', "4": 'pzl:Red3', "5": 'pzl:Red3',
    "6": 'pzl:Red3', "7": 'pzl:Red3', "-": 'pzl:Gray3', "#": 'pzl:Gray3'}
 
    # TSIZE BSIZEX BSIZEY no mines
    if self.gui.get_device().endswith('_landscape'):
      self.size_dict = {"Beginner": (48, 9, 9, 10), 
      "Intermediate": (40, 16, 16, 40),
      "Expert": (40, 30, 16, 99)}
    else:
      self.size_dict = {"Beginner": (48, 9, 9, 10), 
      "Intermediate": (28, 16, 16, 40),
      "Expert": (24, 30, 16, 99)}
          
    if level is None:
      self.level = "Beginner"
    else:
      self.level = level
    self.TSIZE, self.BSIZEX, self.BSIZEY, self.no_mines = self.size_dict[self.level]
    self.marked = []
    self.labelFont = ('Adidas Unity', self.TSIZE)
    self.start = True
    self.game_status = ''
    self.run_time = 0
    self.update_timer = UPDATE
    
    self.board_obj = self.set_mines()
    self.board = self.board_obj
    #self.setup_board()
           
  def hint(self):
    """uncover adjacent tiles"""
    for r, row  in enumerate(self.board_obj):
      for c, t  in enumerate(row):
        if t == 'x':
          continue
        else:
          # check surrounding tiles, only reveal if next to other tiles
          coord = Coord((r, c))
          for dxdy in coord.all_neighbours():
              t = lg.get_board_rc(dxdy, self.board_obj)
              if t in '0123456':
                self.marked.append(coord)                
                return
    console.hud_alert('No more hints','error',1)    
      
  def set_mines(self):
    """ randomly install the mines on the board,
    '-' = empty space and '#' = mine
    assume a square board
    """
    self.board_obj = [['-' for col in range(self.BSIZEX)]for row in range(self.BSIZEY)]
    for i in range(self.no_mines):
      lg.board_rc((randint(0, self.BSIZEY-1), randint(0, self.BSIZEX-1)), self.board_obj, '#')
    return self.board_obj
  
   
  
  def long_touch(self, coord):
    # implement guess of bomb position
        r,c = coord
        self.grid.add_child(Tile('emj:Cross_Mark', r,c, scale=0.5))
        self.marked.append((r, c))
        
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
    #selected = self.select_list()
    self.gui.update(self.board_obj)
    while True:
      move = self.get_player_move()
      self.update_all(move)
    
  
    
  def update_board(self):
      """ called on every key press """
      self.gui.clear_numbers()
      square_list = []
      for r, row in enumerate(self.board_obj):
        for c, t in enumerate(row):
          if self.cheat and t == '#':
              self.gui.game_field.add_child(Tile('emj:Bomb', r,c, scale=0.5))
  
          elif t != "-" and t != "#":
            square_list.append(Squares((r,c), t , 'clear' , 
                                       z_position=30, alpha = .5,
                                       text_anchor_point=(-0.25, 0.25)))
      self.gui.add_numbers(square_list)  
      self.gui.update(self.board_obj) 
        
  def status_label(self, label, color):
      """display time"""
      self.gui.set_top(label)

  def update_all(self, move):
      # check for touch input. is touch input on the board
      if move == ENTER:
         self.hint()
         return
      r, c = move
      item = lg.get_board_rc(move, self.board_obj)
      sound.play_effect('8ve:8ve-beep-shinymetal')
          
      if self.gui.long_touch:
           self.long_touch(move)
                   
      elif item == '#':
           # check if user touched on the mine
           self.gui.update(self.board_obj) 
           self.start = False
           self.game_status = 'LOSE!'
      else:
           # else reveal the number of mines that surround the tile        
           self.board_obj = self.zero_scanning(Coord(move))
  
           # if there is no empty tile left = win!
           if not '-' in self.flatten(self.board_obj) :
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
                  self.gui.show_start_menu()

  def count_mines(self, pos):
      """return number of mines around current tile"""
      count = 0
      # check surrounding tiles
      for y in range(-1, 2):
        for x in range(-1, 2):
          try:
              t = lg.get_board_rc((pos[0] + y, pos[1] + x), self.board_obj)
          except IndexError:
              continue
          if t == '#':
            count += 1
      return str(count)

  def zero_scanning(self, start_pos):
      """ recursive routine to uncover adjacent zeros
      startpos is Coord type that allows addition and has neighbours method"""
      start_tile = self.count_mines(start_pos)
      lg.board_rc(start_pos, self.board_obj, start_tile)
      if start_tile == '0':
        for t in start_pos.all_neighbours():
            try:
              if not self.check_in_board(t):
                  continue
              if self.count_mines(t) == "0" and lg.get_board_rc(t, self.board_obj) != '0':
                self.zero_scanning(t)
              else:
                lg.board_rc(t, self.board_obj,self.count_mines(t))
            except (IndexError,AttributeError):
              continue
      return self.board_obj
          
  def clear(self):
    for t in self.grid.children:
      t.remove_from_parent()
 
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    """
    prompt = (f"Select  position (A1 - {self.COLUMN_LABELS[-1]}{self.sizey})")
    # sit here until piece place on board         
    move = self.wait_for_gui()  
    return move

    
TYPE = "scen"
if __name__ == '__main__':
  g= App()
  g.run()


