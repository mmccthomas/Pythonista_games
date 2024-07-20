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
from gui.gui_interface import Gui
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
  #r,c = int(point[1] - 10+(SIZE)/2), int(point[0] - 10 +(SIZE)/2) # check this
  r, c = point[1], point[0]
  return  r, c

def rc_to_point(rc):
  #x, y = rc[1] + 10 - (SIZE)/2, rc[0] + 10 -(SIZE)/2 # check this
  x, y = rc[1], rc[0]
  return (x, y)
    
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
        self.board = [[' ' for c in range(SIZE)] for r in range(SIZE)]
        self.gui = Gui(self.board, Player())
        #self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
        self.gui.set_alpha(False) 
        self.gui.set_grid_colors(grid=BACKGROUND, highlight='lightblue', z_position=30)
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        self.gui.build_extra_grid(grids_x=SIZE-1, grids_y=SIZE-1, grid_width_x=1, grid_width_y=1, color='black', line_width=1, offset=(self.gui.gs.SQ_SIZE/2,self.gui.gs.SQ_SIZE/2), z_position=100) 
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save, 
        #                 'Load': load,  'Quit': self.gui.gs.close}
        #self.gui.start_menu = {'New Game': run, 'Quit': self.gui.gs.close} 
        self.outline = self.gui.grid.bbox
        #self.outline = pygame.Rect(45, 45, 720, 720)
        self.screen = None
        self.background = None

    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # This method is from https://github.com/eagleflo/goban/blob/master/goban.py
        #pygame.init()
        #pygame.display.set_caption('Goban')
        #self.screen = pygame.display.set_mode(BOARD_SIZE, 0, 32)
        #self.background = pygame.image.load(BACKGROUND).convert()

        #pygame.draw.rect(self.background, BLACK, self.outline, 3)
        # Outline is inflated here for future use as a collidebox for the mouse
        #self.outline.inflate_ip(20, 20)
        #for i in range(18):
        #    for j in range(18):
        #        rect = pygame.Rect(45 + (40 * i), 45 + (40 * j), 40, 40)
        #        pygame.draw.rect(self.background, BLACK, rect, 1)
        #for i in range(3):
        #     for j in range(3):
        #        coords = (165 + (240 * i), 165 + (240 * j))
        #        pygame.draw.circle(self.background, BLACK, coords, 5, 0)
        #self.screen.blit(self.background, (0, 0))
        #pygame.display.update()

    def draw(self, point, color, size=20):
        """ place color at point, need to convert to rc 
        10,10 is centre of board"""
        #piece = 'o' if color == 'WHITE' else '0' 
        piece = '.'
        r,c = point_to_rc(point)
        self.board[r][c] = piece
        self.gui.update(self.board)
        #color = get_rbg(color)
        #pygame.draw.circle(self.screen, color, coords(point), size, 0)
        #pygame.display.update()

    def remove(self, point):
        """ remove piece at point """
        r,c = point_to_rc(point)
        if self.board[r][c] == '.':
          self.board[r][c] = ' '   
        #blit_coords = leftup_corner(point)
        #area_rect = pygame.Rect(blit_coords, (40, 40))
        #self.screen.blit(self.background, blit_coords, area_rect)
        #pygame.display.update()
        
    def human_move(self):
        while True:
           coord = self.gui.wait_for_gui(self.board.copy())
           rc  = (int(coord[:2]), int(coord[2:])) 
           point = rc_to_point(rc)
           self.gui.set_prompt(f'{point =}')
           return point

    def save_image(self, path_to_save):
        pass
        #pygame.image.save(self.screen, path_to_save)
