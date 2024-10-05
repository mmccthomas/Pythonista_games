# This program produces a maze using one of two algorithms
# Wilson's Loop Erased Random Walk  and
# Hunter Killer algorithm 
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
from random import randint, seed, choice
from time import sleep, time
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from gui.gui_interface import Gui, Squares
from maze_generator import WilsonMazeGenerator, HunterKillerMaze, SelectableMaze
DEBUG = 0
TRAINS = 'traintracks.txt'


class Player():
  def __init__(self):
    self.PLAYER_1 = 0
    self.PIECE_NAMES = {0: '_', 1: '&', 2: 'e', 3: 's', 4: 'blue', 5: 'cyan'}
    self.PIECES = [f'../gui/tileblocks/{tile}.png' for tile in self.PIECE_NAMES.values()]
    # use keys() instead of values() for lines
    self.NAMED_PIECES = {v: k for k, v in self.PIECE_NAMES.items()}

        
class MazeTrial():
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.debug = False
        generator = choice(['Hunter', 'Wilson'])
        select = dialogs.list_dialog('Maze size', ['Small', 'Medium', 'Large',  'Hunter SuperLarge'])
        match select:
          case 'Small': 
            size = 10          
          case 'Medium': 
            size = 30            
          case 'Large': 
            size = 50          
          case  'Hunter SuperLarge': 
            size = 80
            generator = 'Hunter'
          case _: 
            size = 30
            
               
        self.display_board = np.zeros((size, size), dtype=int)
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
        self.size = size
        self.generator = generator
        
        self.erase = True
        self.edit_mode = False
        self.identify_mode = False
        self.save_enabled = False
        self.letter = 'x'
        self.gui.replace_labels('row', [''for n in range(self.size)][::-1], color='white', font=('Avenir', 15))
        self.gui.replace_labels('col', ['' for n in range(self.size)], color='white', font=('Avenir', 15))
        self.start = (self.size-1, 0) # always bottom left
        # top right quadrant
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
        
    def _get_player_move(self):
      """Takes in the user's input and performs that move on the board, returns the coordinates of the move
      Allows for movement over board"""
      
      coord_list = []
      
      # sit here until piece place on board   
      items = 0
      
      while items < 1000: # stop lockup        
        move = self.wait_for_gui()
        if items == 0: st = time()
        #print('items',items, move)
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
      sqsize=self.gui.gs.SQ_SIZE
      text_y_pos = {30: 2.5, 10: 1.5, 50: 6, 100:6}
      #adjust text position relative to size
      try:
         y = text_y_pos[self.size]
      except (KeyError):
       	 y= 2.5
      square_list = []
      for  coord in coords:
        square_list.append(Squares(coord, text, color, z_position=30, sqsize = rel_size * sqsize,
                                   alpha=0.5, font=('Avenir Next', sqsize), 
                                   offset=((1.0 - rel_size) / 2, -(1.0 - rel_size) / 2),
                                   text_anchor_point=(-1, y)))
      self.gui.add_numbers(square_list, clear_previous=False)
        
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

        params = {'line_width': 2, 'line_cap_style': LINE_CAP_ROUND, 'stroke_color': 'black'}
        # bottom line
        self.gui.draw_line([self.gui.rc_to_pos((self.size -1,  0)),
                            self.gui.rc_to_pos((self.size -1, self.size))],
                            **params)
        # left line 
        self.gui.draw_line([self.gui.rc_to_pos((-1 , 0)),
                            self.gui.rc_to_pos((self.size - 1, 0))],
                            **params)       
        # draw horizontal lines
        for r in range(self.size):
          row = board[r, :, 0] #north
          lengths, positions, values = self.rle(row)
          for length, position, value in zip(lengths, positions, values):
             if not(value) :
                self.gui.draw_line([self.gui.rc_to_pos((r - 1, position)),
                                    self.gui.rc_to_pos((r - 1, position + length))],
                                   **params)                
        # draw vertcal lines
        for c in range(self.size):
          col = board[:, c, 1] #east
          lengths, positions, values = self.rle(col)
          for length, position, value in zip(lengths, positions, values):
             if not(value):
                self.gui.draw_line([self.gui.rc_to_pos((position - 1, c + 1)),
                                    self.gui.rc_to_pos((position - 1 + length, c + 1))],
                                   **params)
    
    def initial_board(self):
        """ Display board and generate maze"""
        
        self.highlight([self.start], 'S', 'red')
        self.highlight([self.end], 'E', 'green')
        maze = SelectableMaze(self.size, self.size, mazetype=None)
        #self.maze = WilsonMazeGenerator(2*self.size-2, 2*self.size-2)
        
        t = time()
        self.maze.generate_maze()
        str(self.maze)
        grid = self.maze.generate_north_east()
        print('Wilson generate time', time() - t)
        maze = HunterKillerMaze(self.size, self.size)
        maze.endpoints(self.start, self.end)
        t = time()
        maze.generate_maze()
        print('Hunter generate time', time() - t)
        
        if self.generator == 'Wilson':
          maze.grid = grid
        # only use HunterKiller sove routine
        t = time()
        self.path = maze.solve_maze(method='bfs')
        print('solve time', time() -t)
                
        self.moves = []
        
        if self.generator == 'Wilson':
           self.create_line_borders(grid)
        else:
           self.create_line_borders(maze.grid)
        # self.board = self.empty_board.copy()
                                    
    def initialize(self):
        """This method should only be called once,
        when initializing the board."""
        _,_,w,h = self.gui.grid.bbox
        self.gui.clear_messages()
        self.gui.set_enter('Hint', position=(w+50,0) if self.gui.device.endswith('_landscape') else (w-100,h+10))
        self.gui.clear_numbers()
        self.gui.set_top(f'Maze: {self.generator} {self.size}')
        
        try:
            self.initial_board()
            
        except ValueError as e:           
            self.gui.set_prompt('')
            return e
    
    def run(self):
        """
        Main method that prompts the user for input
        """
        try:
            while True:
                move = self.get_player_move()
                finished = self.process_turn(move)
                if self.game_over(finished):
                  break
        except (Exception):
          print(traceback.format_exc())
          print(self.error)
          
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
                  self.highlight([coord], '', 'orange', rel_size=0.5)
              except (IndexError):
                  pass
        return 0
                  
    def game_over(self, finished):
        pass
        
              
    def restart(self):
       self.gui.gs.close()
       g = MazeTrial()
       g.run()
       
    
if __name__ == '__main__':

  game = MazeTrial()
  game.run()






























