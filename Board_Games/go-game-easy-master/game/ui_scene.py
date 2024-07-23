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
from game.go import BOARD_SIZE
#import pygame
"""
This file is the GUI on top of the game backend.
modified for ios using Pythonista by CMT using my gui framework
"""

BACKGROUND = 'game/images/ramin.jpg'

SIZE = BOARD_SIZE - 1

def point_to_rc(point):
  #point is 1 based
  r, c = point[1] - 1, point[0] - 1
  return  r, c

def rc_to_point(rc):
  x, y = rc[0], rc[1]
  return x, y

def get_rbg(color):
    if color == 'WHITE':
        return 255, 255, 255
    elif color == 'BLACK':
        return 0, 0, 0
    else:
        return 0, 133, 211
            
class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = 'O'
    self.PLAYER_2 = BLACK = '0'
    self.EMPTY = ' '
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:White_Circle', 'emj:Black_Circle']
    self.PIECE_NAMES = {'0': 'Black', 'O': 'White'}
    
class UI:
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.display_board = [[' ' for c in range(SIZE)] for r in range(SIZE)]
        self.board = None
        self.gui = Gui(self.display_board, Player())
        self.gui.set_alpha(False) 
        self.gui.set_grid_colors(grid=BACKGROUND, highlight='lightblue', z_position=5, grid_stroke_color='clear')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        self.gui.build_extra_grid(grids_x=SIZE-1, grids_y=SIZE-1, 
                                  grid_width_x=1, grid_width_y=1, color='black', 
                                  line_width=2, offset=(self.gui.gs.SQ_SIZE/2, self.gui.gs.SQ_SIZE/2), 
                                  z_position=5) 
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save, 
        #                 'Load': load,  'Quit': self.gui.gs.close}
        #self.gui.start_menu = {'New Game': run, 'Quit': self.gui.gs.close} 
                     
    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # Apply marker dots to board
        self.gui.clear_messages()
        self.square_list =[]
        if BOARD_SIZE == 10:
            start, spacing = 0, 3
        elif BOARD_SIZE == 14:
            start, spacing = 1, 4
        else:  # BOARD_SIZE == 20
            start, spacing = 2, 6
        for i in range(3):
            for j in range(3):
                self.square_list.append(Squares((start + (i*spacing), start+1 + (j*spacing)), '', 'black', 
                                                z_position=5, stroke_color='clear',alpha =1, 
                                                radius=5, sqsize=10, offset=(0.5,0.5), anchor_point=(0.5, 0.5)))     
        self.gui.add_numbers(self.square_list )   

    def draw(self, point, color, size=None):
        """ place color at point, need to convert to rc 
        """
        if size is None:
            # place tile
            r,c = point_to_rc(point)
            self.display_board[r][c] = '0' if color == 'BLACK' else 'O'
            self.gui.update(self.display_board)
        else:          
            color = get_rbg(color)
            if isinstance(point, list):
                points = [(point_to_rc(p)[0]-1, point_to_rc(p)[1]) for p in point]
                squares = [Squares((r, c), '', color, z_position=8, alpha=1,
                                   stroke_color='clear',  radius=5, sqsize=size, 
                                   offset = (0.5, 0.5), anchor_point=(0.5, 0.5)) 
                                   for r,c in points]
                self.gui.replace_numbers(squares)
            else:
                 r,c = point_to_rc(point)      
                 self.gui.replace_numbers([Squares((r, c), '', color, z_position=8, alpha=1,
                                           stroke_color='clear',  radius=5, sqsize=size, 
                                           offset = (0.5, 0.5), anchor_point=(0.5, 0.5))])    
            self.gui.set_moves(str(len(self.gui.gs.numbers)))     

    def remove(self, point):
        """ remove liberties at point """
        if isinstance(point, list):
            points = [(point_to_rc(p)[0]-1, point_to_rc(p)[1]) for p in point]
            self.gui.clear_numbers(points)
        else:
            r,c = point_to_rc(point)
            self.gui.clear_numbers([(r, c)])
        self.gui.set_moves(str(len(self.gui.gs.numbers)))
        
    def human_move(self):
        while True:
           coord = self.gui.wait_for_gui(self.display_board)
           rc  = (int(coord[:2]), int(coord[2:])) 
           return  rc_to_point(rc)

    def save_image(self, path_to_save):
        pass
        #pygame.image.save(self.screen, path_to_save)
