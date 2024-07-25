import os
import sys
from queue import Queue
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
greatgrandparent = os.path.dirname(grandparent)
sys.path.append(greatgrandparent)
import Dots_Boxes.DotAndBoxGame as dg
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
from scene import Point
from collections import Counter
from time import sleep
"""
This file is the GUI on top of the game backend.
modified for ios using Pythonista by CMT using my gui framework
"""
BOARDSIZE = 31

def point_to_rc(point):
  #point is 1 based
  r, c = point[1] - 1, point[0] - 1
  return  r, c

def rc_to_point(rc):
  x, y = rc[0], rc[1]
  return Point(x, y)


            
class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = 'O'
    self.PLAYER_2 = BLACK = '0'
    self.EMPTY = ' '
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:White_Circle', 'emj:Black_Circle']
    self.PIECE_NAMES = {'0': 'Black', 'O': 'White'}
    
class DotAndBox():
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.display_board = [[' ' for c in range(BOARDSIZE)] for r in range(BOARDSIZE)]
        self.empty_board = self.display_board.copy()
        self.board = None
        self.q = Queue()
        self.gui = Gui(self.display_board, Player())
        self.gui.gs.q = self.q # pass queue into gui
        self.gui.set_alpha(False) 
        self.gui.set_grid_colors(grid='grey', highlight='lightblue', z_position=5, grid_stroke_color='lightgrey')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        #self.gui.build_extra_grid(grids_x=BOARDSIZE-1, grids_y=BOARDSIZE-1, 
        #                          grid_width_x=1, grid_width_y=1, color='grey', 
        #                          line_width=2, offset=(self.gui.gs.SQ_SIZE/2, self.gui.gs.SQ_SIZE/2), 
        #                          z_position=5) 
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save, 
        #                 'Load': load,  'Quit': self.gui.gs.close}
        #self.gui.start_menu = {'New Game': run, 'Quit': self.gui.gs.close} 
        self.score = {'red':0, 'blue':0}
        self.gameplay = dg.game('Human',  "alphabeta", (BOARDSIZE+1) / 2, (BOARDSIZE+1) / 2)
                     
    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # Apply marker dots to board
        self.gui.clear_messages()
        self.square_list =[]
        
        for i in range(0, BOARDSIZE, 2):
            for j in range(0, BOARDSIZE, 2):
                self.square_list.append(Squares((i, j), '', 'white', 
                                                z_position=5, stroke_color='clear',alpha =1, 
                                                radius=5, sqsize=10, offset=(0.5, -0.5), anchor_point=(0.5, 0.5)))     
        self.gui.add_numbers(self.square_list )
        
        self.sq = self.gui.gs.SQ_SIZE /2  
        self.boxes = Counter({(r, c): 0 for c in range(1, BOARDSIZE, 2) for r in range(1, BOARDSIZE, 2)})

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

    
    def wait_for_gui(self):
        # loop until dat received over queue
        while True:
          # if view gets closed, quit the program
          if not self.gui.v.on_screen:
            print('View closed, exiting')
            sys.exit() 
            break   
          #  wait on queue data, either rc selected or function to call
          sleep(0.01)
          if not self.q.empty():
            data = self.q.get(block=False)
            
            #self.delta_t('get')
            #self.q.task_done()
            if isinstance(data, (tuple, list, int)):
              coord = data # self.gui.ident(data)
              break
            else:
              try:
                #print(f' trying to run {data}')
                data()
              except (Exception) as e:
                print(traceback.format_exc())
                print(f'Error in received data {data}  is {e}')
        return coord
    
    def process_turn(self, move, board):
        """ process the turn
        move is coord, new letter, selection_row
        """ 
        def key_from_value(dict_, val):
          for k, v in dict_.items():
            if v == val:
              return k
          return None
             
        if move:
          coord, letter, row = move
          r,c = coord
          if letter == 'Enter':
            
            return False
          elif coord == (None, None):
            return False
        
          elif letter != '':  # valid selection                               
              return False 
          else:
              return False     
          return False
           
    def human_move(self):
        while True:
           coord = self.wait_for_gui()
           return  coord
           
    def process_move(self, move, color='red'):
       # process selection
       row, col = move
       xy = self.gui.rc_to_pos(move)
       # if col is even, it is a vertical line
       if col % 2 == 0 and row % 2 == 1:
           # vertical
           self.gui.draw_line([xy - (-self.sq, self.sq), xy + (self.sq, 3 * self.sq)], 
                              stroke_color=color, line_width=5)
           
           inc = Counter({(row, col + dx):1 for dx in [-1,1] if self.gui.gs.check_in_board((row, col + dx))})
           self.boxes = self.boxes + inc
       elif row % 2 == 0:
           # horizontal
           self.gui.draw_line([xy - (self.sq, -self.sq), xy + (3 * self.sq, self.sq)], 
                              strike_color=color, line_width=5)
           inc = Counter({(row+dy, col):1 for dy in [-1,1] if self.gui.gs.check_in_board((row+dy, col))})
           self.boxes = self.boxes + inc
           
       print(f'{self.boxes = }')
       for k, v in self.boxes.items():
         if v == 4:
           # fill box
           self.gui.add_numbers([Squares(k, '', color, z_position=30, 
                                         sqsize=4*self.sq,
                                         anchor_point=(0.5, 0.5), 
                                         offset=(0.5, -0.5), alpha = .5)], 
                                         clear_previous=False) 
           self.boxes[k] = 0 # to avoid double counting
           self.score[color] += 1
           return True
       return False
        
                              
       
       

    def run(self):
        while True:
            additional_move = True
            while additional_move:
                move = self.human_move()
                self.gui.set_prompt(str(move))
                additional_move = self.process_move(move)
      
      
        
def main():
  game = DotAndBox()
  game.initialize()
  game.run()
  
if __name__ == '__main__':
  main()
