"""
The game of minesweeper using Pythonista
uses Tile objects to store options
long press on tile more than 0.5 sec to mark bomb

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
    self.PIECE_NAMES  ='01234567-#xXB'
    self.PIECES = ['pzl:Green3', 'pzl:Blue3', 'pzl:Yellow3',
                   'pzl:Red3', 'pzl:Red3', 'pzl:Red3',
                   'pzl:Red3', 'pzl:Red3', 'pzl:Gray3','pzl:Gray3', 'emj:Cross_Mark', 'emj:Cross_Mark', 'emj:Bomb']
  
    self.PLAYERS = None

class App(LetterGame):
  
  def __init__(self):
    self.debug = True
    self.cheat = True
    self.background_color = '#828adb'
    self.sleep_time = 0.1
    # allows us to get a list of rc locations
    self.log_moves = False
    self.straight_lines_only = False
    # create game_board and ai_board
    #self.SIZE = self.get_size('9x9') 
    self.board = [['-' for col in range(9)]for row in range(9)] # initial size, change later
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:9]
    self.gui.set_alpha(False) 
    self.gui.set_grid_colors(grid='black', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True) 
    self.select_list()
    self.setup(self.puzzle)
    
    self.gui.gs.DIMENSION_X, self.gui.gs.DIMENSION_Y  = self.BSIZEX, self.BSIZEY
    #self.gui.gs.board=self.board
    self.gui.setup_gui(log_moves=False, board=self.board)
    
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    
  def setup(self, level=None):
    # turn cheat to True to see the mines while playing
    self.cheat = False
    self.background_color = '#828adb'
    
 
    # TSIZE BSIZEX BSIZEY no mines
    if self.gui.get_device().endswith('_landscape'):
      self.size_dict = {"Beginner": (48, 9, 9, 10), 
      "Intermediate": (25, 16, 16, 40),
      "Expert": (15, 30, 16, 99)}
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
    self.board = self.set_mines()
           
  def hint(self):
    """uncover adjacent tiles"""
    for r, row  in enumerate(self.board):
      for c, t  in enumerate(row):
        if t == 'x' or t == 'X':
          continue
        elif t == '#':
          # check surrounding tiles, only reveal if next to other tiles
          coord = Coord((r, c))          
          for dxdy in coord.all_neighbours():
              if self.check_in_board(dxdy):
                  n = self.get_board_rc(dxdy, self.board)           
                  if n and n in '0123456':
                       self.marked.append(coord)     
                       self.board_rc(coord, self.board, 'B')      
                       self.gui.update(self.board)    
                       return
    console.hud_alert('No more hints','error',1)    
      
  def set_mines(self):
    """ randomly install the mines on the board,
    '-' = empty space and '#' = mine
    assume a square board
    """
    self.board = [['-' for col in range(self.BSIZEX)]for row in range(self.BSIZEY)]
    i = 0
    while i < self.no_mines:
        # not the corners
        r = randint(0, self.BSIZEY -1)
        c = randint(0, self.BSIZEX -1)
        if (r, c) in [(0,0), (0, self.BSIZEX -1), (self.BSIZEY - 1, 0), (self.BSIZEY - 1, self.BSIZEX -1)]:
            continue
        else:
            self.board_rc((randint(0, self.BSIZEY-1), randint(0, self.BSIZEX-1)), self.board, '#')
            i = i + 1
    return self.board 
  
  def long_touch(self, coord):
      # implement guess of bomb position
      # change board to X if bomb, else x
      self.gui.set_prompt('long touch')
      t = self.get_board_rc(coord, self.board)
      mark = 'X' if t == '#' else 'x'      
      self.board_rc(coord, self.board, mark)
      self.marked.append(coord)
      self.gui.update(self.board)
        
  def select_list(self):
      '''Choose which category'''
      items =  ["Beginner", "Intermediate",  "Expert"]
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
          #self.wordlist = self.size_dict[selection]
          self.puzzle = selection
          self.gui.selection = ''
          return True
        elif selection == "Cancelled_":
          return False
        else:
            return False   
            
  def run(self):
    start_time = time()
    self.gui.clear_messages()
    self.gui.set_enter('Hint')
    self.gui.update(self.board)
    while True:
      move = self.get_player_move()
      self.update_all(move)
      self.gui.set_top(str(int(time() - start_time)))
     
    
  def update_board(self):
      """ called on every key press
      add mine proximity numbers """
      self.gui.clear_numbers()
      square_list = []
      if self.cheat:
          self.gui.gs.IMAGES['#'] = 'emj:Bomb'           
      for r, row in enumerate(self.board):
          for c, t_str in enumerate(row):
              if t_str in '01234567':
                  square_list.append(Squares((r,c), t_str, 
                                           z_position=30, font=self.labelFont,
                                           text_anchor_point=(-0.25, 0.5)))
      self.gui.add_numbers(square_list)  
      self.gui.update(self.board) 
        
  def status_label(self, label, color):
      """display time"""
      self.gui.set_top(label)

  def update_all(self, move):
      # check for touch input. is touch input on the board

      if move == ENTER:
         self.hint()
         return
         
      item = self.get_board_rc(move, self.board)
      sound.play_effect('8ve:8ve-beep-shinymetal')
          
      if self.gui.gs.long_touch:
           self.long_touch(move)
                   
      elif item in '#XB':
           # check if user touched on the mine
           self.gui.update(self.board) 
           self.start = False
           self.game_status = 'LOSE!'
      else:
           # else reveal the number of mines that surround the tile        
           self.board = self.zero_scanning(Coord(move))
  
           # if there is no empty tile left = win!
           if not '-' in self.flatten(self.board) :
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

  def count_mines(self, current):
      """return number of mines around current tile"""
      count = 0
      coord = Coord(current)
      # check surrounding tiles
      for dxdy in coord.all_neighbours():
          if not self.check_in_board(dxdy):
              continue
          t = self.get_board_rc(dxdy, self.board)
          if t in '#XB':
              count += 1
      return str(count)

  def zero_scanning(self, start_pos):
      """ recursive routine to uncover adjacent zeros
      startpos is Coord type that allows addition and has neighbours method"""
      start_pos = Coord(start_pos)
      start_tile = self.count_mines(start_pos)
      self.board_rc(start_pos, self.board, start_tile)
      if start_tile == '0':
        dd = start_pos.all_neighbours()
        for t in start_pos.all_neighbours():
            try:
              if not self.check_in_board(t):
                  continue
              if self.count_mines(t) == '0' and self.get_board_rc(t, self.board) != '0':
                self.zero_scanning(t) # recursion
              else:
                self.board_rc(t, self.board, self.count_mines(t))
            except (IndexError,AttributeError):
              continue
      return self.board
   
  def reveal(self):
      # reveals the mine
          self.cheat = True
          self.start = False
          self.update_board()
          self.gui.show_start_menu()    
 
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    """
    #prompt = (f"Select  position (A1 - {self.COLUMN_LABELS[-1]}{self.sizey})")
    # sit here until piece place on board         
    move = self.wait_for_gui()  
    return move

    
TYPE = "scen"
if __name__ == '__main__':
  g= App()
  g.run()


