import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
greatgrandparent = os.path.dirname(grandparent)
sys.path.append(greatgrandparent)
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
#import pygame
"""
This file is the GUI on top of the game backend.
modified for ios using Pythonista by CMT using my gui framework
"""

BACKGROUND = 'game/images/ramin.jpg'
BOARD_SIZE = (820, 820)
BLACK = (0, 0, 0)
SIZE = 19

def get_rbg(color):
    if color == 'WHITE':
        return 255, 255, 255
    elif color == 'BLACK':
        return 0, 0, 0
    else:
        return 0, 133, 211


def coords(point):
    """Return the coordinate of a stone drawn on board"""
    return 5 + point[0] * 40, 5 + point[1] * 40

def point_to_rc(point):
  #point is 1 based
  r, c = point[1] - 1, point[0] - 1
  return  r, c

def rc_to_point(rc):
  x, y = rc[0], rc[1]
  return x, y
    
def leftup_corner(point):
    return -15 + point[0] * 40, -15 + point[1] * 40

class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = 'O'
    self.PLAYER_2 = BLACK = '0'
    self.EMPTY = ' '
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2, '.']
    self.PIECES = ['emj:White_Circle', 'emj:Black_Circle', 'iow:close_circled_24']
    self.PIECE_NAMES = {BLACK: 'Black', WHITE: 'White'}
    
class UI:
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.display_board = [[' ' for c in range(SIZE)] for r in range(SIZE)]
        self.board = None
        self.gui = Gui(self.display_board, Player())
        #self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
        self.gui.set_alpha(False) 
        self.gui.set_grid_colors(grid=BACKGROUND, highlight='lightblue', z_position=5)
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        self.gui.build_extra_grid(grids_x=SIZE-1, grids_y=SIZE-1, grid_width_x=1, grid_width_y=1, color='black', line_width=2, offset=(self.gui.gs.SQ_SIZE/2,self.gui.gs.SQ_SIZE/2), z_position=10,) 
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save, 
        #                 'Load': load,  'Quit': self.gui.gs.close}
        #self.gui.start_menu = {'New Game': run, 'Quit': self.gui.gs.close} 
        self.outline = self.gui.grid.bbox
        #self.outline = pygame.Rect(45, 45, 720, 720)
        self.screen = None
        self.background = None
        
    def update_board(self):
        for color_, item in self.board.stonedict.d.items():          
            for position, group in item.items():
              if group != []:
                  # structure is [BLACK - stones: [(10, 10)]; liberties: [(9, 10), ...(11, 10)]]              
                  group = group[0]
                  points = group.points
                  liberties = group.liberties
                  color = group.color
                  for point in points:
                      r,c = point_to_rc(point)
                      self.display_board[r][c] = '0' if color == 'BLACK' else 'O'
                  for liberty in liberties:
                      r, c = point_to_rc(liberty)
                      self.display_board[r][c] = '.'
                      
        self.gui.update(self.display_board)
                  
    
    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # Apply marker dots to board, use bold 'o' 
        self.square_list =[]
        for i in range(3):
            for j in range(3):
                self.square_list.append(Squares((3 + (i*6), 3 + (j*6)), chr(664), 'clear', z_position=30, stroke_color='clear', text_anchor_point=(-.45, .9), alpha =1, text_color='grey', font=('Arial Rounded MT Bold', 24)))     
        self.gui.add_numbers(self.square_list)   

    def draw(self, point, color, size=20):
        """ place color at point, need to convert to rc 
        10,10 is centre of board"""
        #piece = 'o' if color == 'WHITE' else '0' 
        #piece = '.'
        self.update_board()
        #r,c = point_to_rc(point)
        #self.display_board[r][c] = piece
      

    def remove(self, point):
        """ remove piece at point """
        self.update_board()
        r,c = point_to_rc(point)
        if self.display_board[r][c] == '.':
            self.display_board[r][c] = ' '   
        self.gui.update(self.display_board)
        
    def human_move(self):
        while True:
           coord = self.gui.wait_for_gui(self.display_board)
           rc  = (int(coord[:2]), int(coord[2:])) 
           point = rc_to_point(rc)
           self.gui.set_prompt(f'{rc =}')
           return point

    def save_image(self, path_to_save):
        pass
        #pygame.image.save(self.screen, path_to_save)
