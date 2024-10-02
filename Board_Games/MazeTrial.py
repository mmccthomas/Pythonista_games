# TODO Change this to use lines along each grid edge instead of blocks
import numpy as np
import traceback
import os
import sys
import dialogs
from ui import LINE_CAP_ROUND
from queue import Queue
from random import randint, seed
from time import sleep
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from gui.gui_interface import Gui
from maze_generator import WilsonMazeGenerator, HunterKillerMaze
DEBUG = 0
TRAINS = 'traintracks.txt'
seed(1)

class Player():
  def __init__(self):
    self.PLAYER_1 = ' '
    self.PIECE_NAMES = {0: '_', 1: '&', 2: 'e', 3: 's', 4: 'blue', 5: 'cyan'}
    self.PIECES = [f'../gui/tileblocks/{tile}.png' for tile in self.PIECE_NAMES.values()]
    # use keys() instead of values() for lines
    self.NAMED_PIECES = {v: k for k, v in self.PIECE_NAMES.items()}

        
class MazeTrial():
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.debug = False
        size = 51
        
        self.display_board = np.zeros((size, size), dtype=int)
        self.board = None
        self.log_moves = True  # allows us to get a list of rc locations
        self.q = Queue()
        self.gui = Gui(self.display_board, Player())
        self.gui.gs.q = self.q  # pass queue into gui
        self.gui.set_alpha(False)
        self.gui.set_grid_colors(grid='black', z_position=5,
                                 grid_stroke_color='black')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        
        self.gui.setup_gui(log_moves=True, grid_fill='black')
        # self.gui.build_extra_grid(size, size, grid_width_x=1, grid_width_y=1,
        #                          color='black', line_width=2, offset=None,
        #                          z_position=100)
        # menus can be controlled by dictionary of labels and
        # functions without parameters
        self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                                 'New Game': self.restart,
                                 'Reveal': self.reveal,
                                 'Quit': self.gui.gs.close})
      
        self.gui.start_menu = {'New Game': self.restart,
                               'Quit': self.gui.gs.close}
        self.size = size
        self.solution_board = np.full((size, size), '-', dtype='U1')
        self.empty_board = np.full((size, size), '-', dtype='U1')
        self.erase = True
        self.edit_mode = False
        self.identify_mode = False
        self.save_enabled = False
        self.letter = 'x'
        self.gui.replace_labels('row', [''for n in range(self.size)][::-1], color='white', font=('Avenir', 15))
        self.gui.replace_labels('col', ['' for n in range(self.size)], color='white', font=('Avenir', 15))
        self.start = (randint(0, self.size-1), randint(0, self.size-1))
        self.end = (randint(0, self.size-1), randint(0, self.size-1))
        self.error = self.initialize()
        
    def update_board(self, board):
      self.gui.update(board)
    
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
            # self.delta_t('get')
            # self.q.task_done()
            if isinstance(data, (tuple, list, int)):
              coord = data  # self.gui.ident(data)
              break
            else:
              try:
                # print(f' trying to run {data}')
                data()
              except (Exception) as e:
                print(traceback.format_exc())
                print(f'Error in received data {data}  is {e}')
        return coord
        
    def _get_player_move(self, board=None):
      """Takes in the user's input and performs that move on the board,
         returns the coordinates of the move
         Allows for movement over board"""
      if board is None:
          board = self.game_board
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
       
    def get_player_move(self, board=None):
        """Takes in the user's input and performs that move on the board,
           returns the coordinates of the move
           Allows for movement over board"""
        move = self._get_player_move(self.board)
        print(move)
        if move[0] == (-1, -1):
           return (None, None), 'Enter', None  # pressed enter button
        # deal with buttons. each returns the button text
        elif move[0][0] < 0 and move[0][1] < 0:
          return (None, None), self.gui.gs.buttons[-move[0][0]].text, None
        else:
          return move, None, None
        return (None, None), None, None
        
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
          
    def create_line_borders(self):
        """ find blocks and create lines vertical and horizontal """
        sq = self.gui.gs.SQ_SIZE
        p5 = 0.5
        params = {'line_width': 8, 'line_cap_style': LINE_CAP_ROUND}
        # draw horizontal lines
        for r in range(0, self.size, 2):
          row = self.board[r, :]
          lengths, positions, values = self.rle(row)
          for length, position, value in zip(lengths, positions, values):
             if value == 1 and length > 1:
                self.gui.draw_line([self.gui.rc_to_pos((r - p5, position + p5)),
                                    self.gui.rc_to_pos((r - p5, position - p5 + length))],
                                   **params)
        # draw vertcal lines
        for c in range(0, self.size, 2):
          col = self.board[:, c]
          lengths, positions, values = self.rle(col)
          for length, position, value in zip(lengths, positions, values):
             if value == 1 and length > 1:
                self.gui.draw_line([self.gui.rc_to_pos((position - p5, c + p5)),
                                    self.gui.rc_to_pos((position - 1 - p5 + length, c + p5))],
                                   **params)
    
    def initial_board(self):
        """ Get board layout and permanent cells from board_obj"""
        pass
        self.empty_board = np.full((self.size, self.size), '-', dtype='U1')
        self.maze = WilsonMazeGenerator(self.size-2, self.size-2)
        # self.maze.endpoints(self.start, self.end)
        self.maze.generate_maze()
        _ = str(self.maze)
        maze = HunterKillerMaze(self.size-2, self.size-2)
        maze.generate_maze()
        self.board, _ = maze.convert_grid()
        self.maze.grid_np = self.board.copy()
        #maze.solve_maze()
        maze.draw_maze()
        #self.board = self.maze.frame
        self.update_board(self.board)
        self.maze.solve_maze()
        #self.maze.show_solution(False)
        #_ = str(self.maze)
        #self.board = self.maze.frame
        self.create_line_borders()
        # self.board = self.empty_board.copy()
                                    
    def initialize(self):
        """This method should only be called once,
        when initializing the board."""
        self.gui.clear_messages()
        self.gui.set_enter('Hint')
        self.gui.clear_numbers()
        self.gui.set_top(f'Maze: {self.size}')
        
        try:
            self.initial_board()
            self.update_board(self.board)
            
        except ValueError as e:
            
            # self.solution_board = None
            
            self.gui.set_prompt('')
            return e
    
    def run(self):
        """
        Main method that prompts the user for input
        """
        try:
            self.update_board(self.board)
            while True:
                move = self.get_player_move(self.board)
                finished = self.process_turn(move, self.board)
                self.update_board(self.board)
                if self.game_over(finished):
                  break
        except (Exception):
          print(traceback.format_exc())
          print(self.error)
          
    def reveal(self):
      """finish the game by revealing solution"""
      self.maze.show_solution(True)
      _ = str(self.maze)
        
      self.board = self.maze.frame
      
      self.update_board(self.board)
      dialogs.hud_alert('Game over')
      sleep(2)
      self.gui.show_start_menu()
       
    def hint(self):
        # place a random track piece not already placed
        pass
                    
    def process_turn(self, move, board):
        """ process the turn
        move is coord, new letter, selection_row
        """
        print(move)
        if isinstance(move, list):
          for coord in move[:-2]:
            if self.board[coord] == 0:
               self.board[coord] = 5
          self.update_board(self.board)
        elif move:
          coord, letter, row = move
          r, c = coord
          if letter == 'Enter':
            finished = self.hint()
            if finished:
              return 1
                
          elif coord == (None, None):
              return 0
                                     
          elif letter != '':  # valid selection
              try:
                  r, c = coord
              except (IndexError):
                  pass
        return 0
                  
    def game_over(self, finished):
        pass
        
        @np.vectorize
        def contained(x):
            return x in list(self.gui.player.PIECE_NAMES.keys())[:-2]
  
        board = np.where(contained(self.board), self.board, ' ')
        soln = np.where(contained(self.solution_board), self.solution_board, ' ')
        compare = (board == soln)
      
        if finished and np.all(compare):
          dialogs.hud_alert('Game over')
          sleep(2)
          self.gui.show_start_menu()
        return False
              
    def restart(self):
       self.gui.gs.close()
       g = MazeTrial()
       g.run()
       
    
if __name__ == '__main__':

  game = MazeTrial()
  game.run()



























