#
# The GUI engine for Python Chess
# converted to pythonista scene by CMT
# Author: Boo Sung Kim, Eddie Sharick
# Note: The pygame tutorial by Eddie Sharick was used for the GUI engine. The GUI code was altered by Boo Sung Kim to
# fit in with the rest of the project.
#
import os
import sys
from queue import Queue
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
import chess_engine
import ai_engine
from scene import *
from ui import Path
import console
from time import sleep
import copy
from scene import Vector2, get_screen_size
screen_width, screen_height = get_screen_size()
 
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from gui.game_menu import MenuScene
import logging
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares, Coord
from Word_Games.Letter_game import LetterGame

logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

MOVE_SPEED = 0.8

def fn_piece(piece):
      try:
         return f'{piece.player}_{piece.name}'
      except (AttributeError) :
         return None

def copy_board(board):
  return list(map(list, board)) 
  
class Player():
  def __init__(self):
    self.PLAYER_1 = 'white'
    self.PLAYER_2 = 'black'
    self.EMPTY = -9
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]    
    self.PIECE_NAMES  = [f'{p}_{piece}' for piece in 'rbnpqk' for p in self.PLAYERS] + ['blank']
    self.PIECES = [f'{p}_{piece}.png' for piece in 'rbnpqk' for p in self.PLAYERS] + ['blank.png']
        
class ChessGame(gscene.GameBoard):
  def __init__(self):
    
    gscene.GameBoard.__init__(self)
    self.gs = chess_engine.game_state(Player())
    self.board = self.gs.board 
    
    self.log_moves = True
    self.debug = False
    self.straight_lines_only = False
    
    self.SIZE = self.sizex = self.sizey= 8
    self.DIMENSION_X = self.DIMENSION_Y = 8
    # load the gui interface
    self.q = Queue()
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.use_alpha = False
    image = ui.Image.named('board_grey.jpg')
    self.grid_fill = 'clear'          
    self.background_image = image
    self.highlight_fill ='lightblue'
    self.require_touch_move = False
    self.allow_any_move = True
    self.Player = Player()
    self.setup_gui(log_moves=True)
    
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.pause_menu = {'Continue': self.dismiss_modal_scene, 
                       'New Game': self.restart,
                       'Undo': self.undo,
                       'Quit': self.quit}
    self.start_menu = {'Single Player': self.single,
                       '2 Player': self.two_player, 
                       'AI play': self.ai_play,
                       'Quit': self.quit}

                               
    #self.all = [[j,i] for i in range(self.sizex) for j in range(self.sizey) if self.board[j][i] == SPACE]
    self.ai = ai_engine.chess_ai(self.Player)
    self.paused = True
    self.smaller_tile = 30      
    self.redraw_board(fn_piece=fn_piece) 
    self.msg_label_b2.text = ''
    self.msg_label_b.text = ''
    self.msg_label_r.text = ''
    self.msg_label_prompt.text = ''
  
    #self.show_start_menu() 
    self.turn = True 
    # self.play_ai()       
  
  def highlight_square(self, valid_moves, square_selected):
    if square_selected != () and self.gs.is_valid_piece(square_selected[0], square_selected[1]):
      row, col = square_selected
      turn = self.gs.whose_turn() 
      p = self.gs.get_piece(row, col)
      
      if (turn and p.is_player(self.Player.PLAYER_1)) or \
        (not turn and p.is_player(self.Player.PLAYER_2)):
        # hightlight selected square
        self.highlight_squares(valid_moves)
  
  
  def check_endgame(self):  
    msg_list = ["Black wins.", "White wins.", "Stalemate."]
    # 0 if white lost, 1 if black lost, 2 if stalemate, 3 if not game over
    endgame = self.gs.checkmate_stalemate_checker()
    
    if endgame in list(range(3)):
      game_over = True
      self.draw_text(msg_list[endgame])
      self.redraw_board(fn_piece=fn_piece)
      sleep(2)
    else:
      game_over = False
    return game_over
    

  def remove_taken_piece(self,rc):
    r,c = rc
    piece = self.gs.get_piece(r, c)
    tiles = self.tile_at(rc,multi=True)
    if len(tiles) == 1 or tiles is None:
      return
    for t in tiles:
      if t.name != f"{piece.player}_{piece.name}":
        t.remove_from_parent()
          
  def update(self):
    # dt is provided by Scene t is time since start
     
    self.line_timer -= self.dt
    self.go = True
    if self.line_timer <= 0:
      self.line_timer = 0.5
      self.turn_status(self.gs.whose_turn())
      self.go = True
  
  def touch_began(self, touch):
    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.tile_selected = None
      self.show_pause_menu()
      return
    t = touch.location
    rc = self.point_to_rc(t)  
    self.last_rc = rc
    self.tile_selected = self.tile_at(rc) 
    valid_moves = self.gs.get_valid_moves(rc)
    self.highlight_square(valid_moves, rc)
      
  def touch_ended(self, touch):
    logger.debug('touch ended')
  
    if self.tile_selected:
      logger.debug(f'tile {self.tile_selected.number} to move')
      rc = self.point_to_rc(touch.location)
      if rc == self.last_rc:
        self.clear_highlights()
        return
      if rc in self.gs.get_valid_moves(Coord(self.last_rc)):
        self.gs.move_piece(starting_square=Coord(self.last_rc), ending_square=Coord(rc), is_ai=False)
        self.redraw_board(fn_piece=fn_piece)   
        self.clear_highlights()             
      else:
        print('invalid move')
      if self.single:
        self.black_play() 
              
      if self.check_endgame():
          self.show_start_menu()
          
  def black_play(self):
      # now ai move for black
      copied_board = copy_board(self.gs.board)
      start, end = self.ai.minimax(self.gs, 3, -100000, 100000, True, self.Player.PLAYER_1)      
      print(f'ai moves from {start} to {end}')
      self.msg_label_prompt.text = f'ai moves from {start} to {end}'
      self.gs.white_turn = False
      self.gs.board = copied_board
      self.board = self.gs.board
      self.gs.move_piece(starting_square=Coord(start), ending_square=Coord(end), is_ai=True, debug=True)
      self.gs.board_print() 
      self.turn_status(self.gs.whose_turn())
      self.redraw_board(fn_piece=fn_piece)         
      self.clear_highlights()
      print('after ai move')
      self.gs.board_print()  
          
  def play_ai(self):
    
    """ WIP not working yet 
    """
    #self.paused = True
    
    turns = [self.Player.PLAYER_2, self.Player.PLAYER_1]
    while True:
        sleep(.5)
        plyr = turns[int(self.gs.whose_turn())]

        #self.gs.white_turn = not turn_idx
        # now ai move 
        copied_board = copy_board(self.board)
        print(self.gs.whose_turn(), plyr)
        start, end = self.ai.minimax(game_state=self.gs, depth=3, alpha=-100000, beta=100000, maximizing_player=self.gs.whose_turn(), player_color=plyr)
        if isinstance(end, tuple):
            self.msg_label_prompt.text = f'{plyr} moves from {start} to  {end}'
            print( f'{plyr} moves from {start} to  {end}')
            self.board = copied_board
            self.gs.move_piece(Coord(start), Coord(end), is_ai=True)
            self.redraw_board(fn_piece=fn_piece)     
            self.gs.board_print()  
        else:
          print(start, end)                
        if  self.check_endgame(): 
          break                 
        #turn_idx = not turn_idx
    self.show_start_menu()
   
  def quit(self):
    self.close()
    sys.exit() 
     
  def restart(self, first_time=False):
    self.finished = False
    self.__init__()
    #self.run()
    
  def undo(self):
    self.gs.undo_move()
    print(len(self.gs.move_log))
    
  def single(self):
    self.single = True
    self.restart()
    
  def two_player(self):     
    self.single = False
    self.restart()  
    
  def ai_play(self):
    self.single = False
    self.restart(False)
    self.play_ai()    
      

if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',level=logging.WARNING)   
  run(ChessGame())
    

