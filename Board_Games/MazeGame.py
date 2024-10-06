# This program produces a maze using one of severalalgorithms
#
# sizes selectable are 10x10, 30x30 and 50x50
# best played using a pencil or similar
# solution uses  breadth-first search, depth-first search is optional at line 261

import numpy as np
import traceback
import os
import sys
import dialogs
from ui import LINE_CAP_ROUND
from queue import Queue
from random import randint
from time import sleep, time
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from gui.gui_interface import Gui, Squares
from maze_generator import SelectableMaze


class Player():
  def __init__(self):
    self.PLAYER_1 = 0
    self.PIECE_NAMES = {0: '_', 1: '&', 2: 'e', 3: 's', 4: 'blue', 5: 'cyan'}
    self.PIECES = [f'../gui/tileblocks/{tile}.png' for tile in self.PIECE_NAMES.values()]
    # use keys() instead of values() for lines
    self.NAMED_PIECES = {v: k for k, v in self.PIECE_NAMES.items()}

MAZE_GENERATORS = ['AldousBroder', 'BacktrackingGenerator',
                   'CellularAutomaton', 'DungeonRooms',
                   'GrowingTree', 'HuntAndKill', 'Kruskal',
                   'Prims', 'Sidewinder', 'Wilsons']
                
class MazeTrial():
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.debug = False
        self.generator = None
        sizes = {'Small': 15, 'Medium': 30, 'Large': 50, 'SuperLarge': 80}
        select = dialogs.list_dialog('Maze size', ['Small', 'Medium', 'Large',  'SuperLarge'])
        self.size = sizes.get(select, 30)
          
        self.display_board = np.zeros((self.size, self.size), dtype=int)
        self.log_moves = True  # allows us to get a list of rc locations
        self.straight_lines_only = False
        self.q = Queue()
        self.gui = Gui(self.display_board, Player())
        self.gui.gs.q = self.q  # pass queue into gui
        self.gui.set_alpha(False)
        self.gui.set_grid_colors(grid='white', z_position=5,
                                 grid_stroke_color='white')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        
        self.gui.setup_gui(log_moves=True, grid_fill='white')

        # menus can be controlled by dictionary of labels and
        # functions without parameters
        self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                                 'New Game': self.restart,
                                 'Reveal': self.reveal,
                                 'Quit': self.gui.gs.close})
      
        self.gui.start_menu = {'New Game': self.restart,
                               'Quit': self.gui.gs.close}
                               
        self.gui.replace_labels('row', ['' for n in range(self.size)][::-1])
        self.gui.replace_labels('col', ['' for n in range(self.size)])
        
        self.start = (self.size-1, 0)  # always bottom left
        # random position in top right quadrant
        self.end = (randint(0, self.size // 2), randint(self.size//2, self.size-1))
        self.error = self.initialize()
    
    def wait_for_gui(self):
      # loop until dat received over queue
      while True:
        # if view gets closed, quit the program
        if not self.gui.v.on_screen:
          print('View closed, exiting')
          sys.exit()
          break
        #  wait on queue data, either rc selected or function to call
        sleep(0.001)
        if not self.q.empty():
          data = self.q.get(block=False)
          if isinstance(data, (tuple, list, int)):
            coord = data  # self.gui.ident(data)
            break
          else:
            try:
              data()
            except (Exception) as e:
              print(traceback.format_exc())
              print(f'Error in received data {data}  is {e}')
      return coord
        
    def _get_player_move(self):
      """Takes in the user's input and performs that move on the board, returns the coordinates of the move
      Allows for movement over board"""      
      coord_list = []
            
      # sit here until piece place on board
      items = 0
      
      while items < 1000:  # stop lockup
        move = self.wait_for_gui()
        try:
          if self.log_moves:
            coord_list.append(move)
            items += 1
            if move == -1:
              return coord_list
          else:
            break
        except (Exception) as e:
          print(traceback.format_exc())
          print('except,', move, e)
          coord_list.append(move)
          return coord_list
      return move
       
    def get_player_move(self):
        """Takes in the user's input and performs that move on the board,
           returns the coordinates of the move
           Allows for movement over board"""
        move = self._get_player_move()
        
        if move[0] == (-1, -1):
           return (None, None), 'Enter', None  # pressed enter button
           
        # deal with buttons. each returns the button text
        elif move[0][0] < 0 and move[0][1] < 0:
          return (None, None), self.gui.gs.buttons[-move[0][0]].text, None
        else:
          return move, None, None
        return (None, None), None, None
        
    def highlight(self, coords, text, color, rel_size=0.9):
      sqsize = self.gui.gs.SQ_SIZE
      self.gui.add_numbers([Squares(coord, text, color, z_position=30, sqsize=rel_size * sqsize,
                             alpha=0.5, font=('Avenir Next', sqsize),
                             offset=((1.0 - rel_size) / 2, -(1.0 - rel_size) / 2),
                             text_anchor_point=(-0.75, 1.35)) for coord in coords],
                           clear_previous=False)
        
    def rle(self, inarray):
        """ run length encoding. Partial credit to R rle function.
        Multi datatype arrays catered for including non Numpy
        returns: tuple (runlengths, startpositions, values) """
        ia = np.asarray(inarray)                # force numpy
        n = len(ia)
        if n == 0:
          return (None, None, None)
        else:
          y = ia[1:] != ia[:-1]               # pairwise unequal (string safe)
          i = np.append(np.where(y), n - 1)   # must include last element posi
          z = np.diff(np.append(-1, i))       # run lengths
          p = np.cumsum(np.append(0, z))[:-1]  # positions
          return (z, p, ia[i])
          
    def create_line_borders(self, board):
        """ find blocks and create lines vertical and horizontal
        board is nxmx2 where axis 2 is North, East
        use run length encoding to reduce number of lines """

        params = {'line_width': 4, 'line_cap_style': LINE_CAP_ROUND, 'stroke_color': 'black'}
        # bottom line
        self.gui.draw_line([self.gui.rc_to_pos((self.size - 1,  0)),
                            self.gui.rc_to_pos((self.size - 1, self.size))],
                           **params)
        # left line
        self.gui.draw_line([self.gui.rc_to_pos((-1, 0)),
                            self.gui.rc_to_pos((self.size - 1, 0))],
                           **params)
        # draw horizontal lines
        for r in range(self.size):
          row = board[r, :, 0]  # north
          lengths, positions, values = self.rle(row)
          for length, position, value in zip(lengths, positions, values):
             if not value:
                self.gui.draw_line([self.gui.rc_to_pos((r - 1, position)),
                                    self.gui.rc_to_pos((r - 1, position + length))],
                                   **params)
        # draw vertcal lines
        for c in range(self.size):
          col = board[:, c, 1]  # east
          lengths, positions, values = self.rle(col)
          for length, position, value in zip(lengths, positions, values):
             if not value:
                self.gui.draw_line([self.gui.rc_to_pos((position - 1, c + 1)),
                                    self.gui.rc_to_pos((position - 1 + length, c + 1))],
                                   **params)
    
    def initial_board(self):
        """ Display board and generate maze"""
    
        self.highlight([self.start], 'S', 'red')
        self.highlight([self.end], 'E', 'green')
        maze = SelectableMaze(self.size, self.size, mazetype=self.generator)
        maze.endpoints(self.start, self.end)
        t = time()
        maze.generate_maze()
        elapsed = time() - t
        # print('Maze time', elapsed)
        self.gui.set_prompt(f'Generated in {elapsed:.3f} secs')
        # display_grid, dirgrid = maze.convert_grid()
        
        t = time()
        self.path = maze.solve_maze()
        # print('solve time', time() -t)
        self.create_line_borders(maze.grid)        
        self.gui.set_top(f'Maze: {maze.mazetype}     Size: {self.size}')               
                                    
    def initialize(self):
        """This method should only be called once,
        when initializing the board."""
        _, _, w, h = self.gui.grid.bbox
        self.gui.clear_messages()
        self.gui.set_enter('Hint', position=(w + 50, 0) if self.gui.device.endswith('_landscape') else (w - 100, h + 10))
        self.gui.clear_numbers()

        self.moves = []
        try:
            self.initial_board()
            
        except ValueError as e:
            self.gui.set_prompt('')
            return e
             
    def reveal(self):
      """finish the game by revealing solution"""
      self.highlight(self.path[:-1], '', 'cyan', 0.8)
      dialogs.hud_alert('Game over')
      sleep(2)
      self.gui.show_start_menu()
       
    def hint(self):
        # place a random piece if the solution path
        try:
            idx = randint(0, len(self.path) - 1)
            p = self.path.pop(idx)
            self.highlight([p], '', 'cyan')
        except (IndexError, ValueError):
            dialogs.hud_alert('No more hints')
            self.gui.show_start_menu()
            return True
        
    def process_turn(self, move):
        """ process the turn
        move is coord, new letter, selection_row
        """
        def uniquify(moves):
            """ filters list into unique elements retaining order"""
            return list(dict.fromkeys(moves))
                    
        if isinstance(move[0], list):
          moves = move[0]
          moves.pop(-1)
          moves = uniquify(moves)
          # remove any out of grid moves
          moves = [move for move in moves if self.gui.gs.check_in_board(move)]
          # use sets to filter moves, most obvious and efficient
          # find moves in previous moves
          common = list(set(moves).intersection(set(self.moves)))
          # find moves that are not in previuos moves
          difference = list(set(moves).difference(set(common)))
          
          if common:
              self.gui.clear_numbers(common)
              # remove common from previous moves
              self.moves = list(set(self.moves).difference(set(common)))
          self.moves.extend(difference)
          self.highlight(difference, '', 'orange', rel_size=0.5)
            
        elif move:
          coord, letter, row = move
                    
          if letter == 'Enter':
            finished = self.hint()
            if finished:
              return 1
                
          elif coord == (None, None):
              return 0
                                     
          elif letter != '':  # valid selection
              try:
                  r, c = coord
                  if (0 <= r < self.size) and (0 <= c < self.size):
                    self.highlight([coord], '', 'orange', rel_size=0.5)
              except (IndexError):
                  pass
        return 0
                  
    def game_over(self, finished):
        """ finish if coorect moves within 5 of solution """
        intersection = set(self.moves).intersection(set(self.path))
        correct = len(intersection)
        path_length = len(self.path)
        if path_length - correct < 20:
        	self.gui.set_message(f'{path_length - correct} moves left')
        if path_length - 5 <= correct <= path_length:
            return True
                    
    def restart(self):
       self.gui.gs.close()
       g = MazeTrial()
       g.run()
    
    def run(self):
        """
        Main method that prompts the user for input
        """
        try:
            while True:
                move = self.get_player_move()
                finished = self.process_turn(move)
                if self.game_over(finished):
                   self.reveal()
        except (Exception):
          print(traceback.format_exc())   
    
if __name__ == '__main__':
  game = MazeTrial()
  game.run()

