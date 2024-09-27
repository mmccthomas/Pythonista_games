# https://github.com/ianastewart/tracks
# modified for ios.
# removed turtle graphics `CMT
import numpy as np
import traceback
import os
import sys
from collections import defaultdict
from math import sqrt
from enum import Enum
from time import perf_counter, time, sleep
from scene import *
from ui import Image
import dialogs
import ui
from types import SimpleNamespace
from queue import Queue
from collections import deque
from random import choice, randint, shuffle
from time import time
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
greatgrandparent = os.path.dirname(grandparent)
sys.path.append(greatgrandparent)
from gui.gui_interface import Coord, Gui, Squares
from gui.gui_scene import Tile
import gui.gui_scene as gscene


def check_in_board(coord):
    r, c = coord
    return (0 <= r < SIZE) and (0 <= c < SIZE)

        
SIZE = 1
DEBUG = False
FONT = ("sans-serif", 18, "normal")
TRAINS = 'traintracks.txt'


class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = ' '
    self.PLAYER_2 = BLACK = '#'
 
    self.PIECE_NAMES = {'┃': 'NS',  '━': 'EW', '┓': 'NW', '┏': 'NE', '┗': 'SE', '┛': 'SW', '?': '?', 'x': 'x'}
    self.PIECES = [f'../gui/tileblocks/{tile}.png' for tile in self.PIECE_NAMES.values()]  # use keys() for lines
    self.NAMED_PIECES = {v: k for k, v in self.PIECE_NAMES.items()}

  
class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

        
class TrainTracks():
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.game_item, size = self.load_words_from_file(TRAINS)
        
        self.display_board = np.zeros((size, size), dtype=int)
        self.board = None
        # allows us to get a list of rc locations
        self.log_moves = True
        self.q = Queue()
        self.gui = Gui(self.display_board, Player())
        self.gui.gs.q = self.q  # pass queue into gui
        self.gui.set_alpha(False)
        self.gui.set_grid_colors(grid='black', z_position=5, grid_stroke_color='black')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        
        self.gui.setup_gui(log_moves=True, grid_fill='white')
        self.gui.build_extra_grid(size, size, grid_width_x=1, grid_width_y=1, color='black', line_width=2, offset=None, z_position=100)
        # menus can be controlled by dictionary of labels and functions without parameters
        self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                                 'New Game': self.restart,
                                 'Reveal': self.reveal,
                                 'Quit': self.gui.gs.close})
      
        self.gui.start_menu = {'New Game': self.restart, 'Quit': self.gui.gs.close}
        self.size = size
        #self.display_rack(self.gui.player.PIECE_NAMES)
        self.solution_board = np.full((size, size), '-', dtype='U1')
        self.empty_board = np.full((size, size), '-', dtype='U1')
        self.erase = True
        self.edit_mode = False
        self.start_track = '____s'
        self.end_track = '____e'
        self.identify_mode = False
        self.save_enabled = False
        self.letter = 'x'
        self.constraints = self.game_item
        self.error = self.initialize()
                
    def update_board(self, board):
      self.gui.update(board)
      self.display_rack(self.gui.player.PIECE_NAMES)
            
    def display_rack(self, tiles, y_off=-50):
        """ display players rack
        y position offset is used to select player_1 or player_2
        """
        parent = self.gui.game_field
        _, _, w, h = self.gui.grid.bbox
        sqsize = self.gui.gs.SQ_SIZE
        x, y = (50, h - sqsize)
        offx, offy = self.posn.rackpos
        x = x + offx
        y = y + offy
        rack = {}
        r = self.posn.rackoff
        for n, tile in enumerate(tiles):
          t = Tile(Texture(Image.named(f'../gui/tileblocks/{tiles[tile]}.png')), 0,  0, sq_size = sqsize * self.posn.rackscale)
          t.position = (w + x + (n % r * (20 + sqsize * self.posn.rackscale)), y - n // r * (20 + sqsize* self.posn.rackscale))
          rack[t.bbox] = tile
          parent.add_child(t)
        
        self.rack = rack
        
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
      """Takes in the user's input and performs that move on the board, returns the coordinates of the move
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
        """Takes in the user's input and performs that move on the board, returns the coordinates of the move
        Allows for movement over board"""
        move = self._get_player_move(self.board)
        rack = self.rack
        # self.gui.set_message2(f'{move[0]}..{move[-2]}')
        if move[0] == (-1, -1):
           return (None, None), 'Enter', None  # pressed enter button
           
        # deal with buttons. each returns the button text
        elif move[0][0] < 0 and move[0][1] < 0:
          return (None, None), self.gui.gs.buttons[-move[0][0]].text, None
          
        point = self.gui.gs.start_touch - gscene.GRID_POS
        # get letter from rack
        for index, k in enumerate(rack):
            if k.contains_point(point):
                self.letter = rack[k]
                rc = move[-2]
                return rc, self.letter, index
        # single press uses previous letter
        try:
          if move[0] == move[-2]:
             return move[-2], self.letter, None
        except (AttributeError):
          pass
        return (None, None), None, None
    
    def load_words_from_file(self, file_list, no_strip=False):
        # read the entire wordfile as text
        with open(f'{file_list}', "r", encoding='utf-8') as f:
          data = f.read()
        # split and remove comment and blank lines
        data_list = data.split('\n')
        data_list = [item for item in data_list if item != '' and not item.startswith('#')]
        # choice random line
        selected = choice(data_list)
        # selected = data_list[10]
        size = int(selected.split(':')[0])
        return selected, size
    
    def initial_board(self):
        """ Get board layout and permanent cells from board_obj"""
        pass
        self.empty_board = np.full((self.size, self.size), '-', dtype='U1')
        board = self.convert_tracks()
        perm = self.convert_permanent()
        if not self.edit_mode:
           self.gui.clear_squares()
           self.highlight_permanent(perm.start.loc, 'A')
           self.empty_board[perm.start.loc] = perm.start.track
           self.highlight_permanent(perm.end.loc, 'B')
           self.empty_board[perm.end.loc] = perm.end.track
           for known in perm.known:
             self.highlight_permanent(known.loc, '')
             self.empty_board[known.loc] = known.track
           self.board = self.empty_board.copy()
                                    
    def initialize(self):
        """This method should only be called once, when initializing the board."""
        self.gui.clear_messages()
        self.gui.clear_numbers()
        self.gui.set_top(f'Train Tracks: {self.game_item}')
        # add boxes and buttons if not already placed
        if not hasattr(self, 'edit'):
            self.box_positions()
            self.add_boxes()
            self.set_buttons()
        try:
           self.board_obj = parse(self.game_item, self)
        except ValueError as e:
           self.gui.set_prompt(str(e))
           return e
        self.draw_initial()
        try:
            start = perf_counter()
            self.initial_board()
            self.update_board(self.board)
            self.convert_permanent()
            
            self.board_obj.solve()
        except ValueError as e:
            end = perf_counter()
            elapsed = end - start
            self.board_obj.result(str(e), elapsed)
            self.solution_board = self.convert_tracks()
            if not self.edit_mode:
                self.update_board(self.board)
            else:
                self.update_board(self.solution_board)
            self.gui.print_board(self.solution_board, 'solution')
            return e
            
    def convert_tracks(self):
      """get layout from board_obj and create array"""
      board = np.full((self.size, self.size), '-', dtype='U1')
      for r in range(self.size):
         for c in range(self.size):
          _char = self.board_obj.layout[r][c].track
          if _char is not None:
            board[r, c] = self.gui.player.NAMED_PIECES[_char.name]
      return board
      
    def convert_permanent(self):
      """get permanent locations from layout and produce permanent dictionary"""
      b = self.convert_tracks()
      start_loc = (self.board_obj.start, 0)
      end_loc = (self.board_obj.end_row, self.board_obj.end)
      known_loc = [(r, c) for r in range(self.size) for c in range(self.size) if self.board_obj.layout[r][c].permanent]
      known_loc.remove(start_loc)
      known_loc.remove(end_loc)
      # use dotdict ckass to provide simpler access
      self.permanent = dotdict({'start': dotdict({'loc': start_loc, 'track': b[start_loc]}),
                                'end': dotdict({'loc': end_loc, 'track': b[end_loc]}),
                                'known': [dotdict({'loc': loc, 'track': b[loc]}) for loc in known_loc]})
      return self.permanent
      
    def highlight_permanent(self, coord, text=''):
        params = {'color': 'cyan', 'text_color': 'blue',
                  'z_position': 1000, 'stroke_color': 'clear',
                  'alpha': 0.1, 'radius': 5,
                  'sqsize': self.gui.gs.SQ_SIZE, 'offset': (0.0, 0.0),
                  'font': ('Arial Rounded MT Bold', 30), 'text_anchor_point': (-1, 1)}
        self.gui.add_numbers([Squares(coord, text, **params)], clear_previous=False)
        r, c = coord
        self.board_obj.layout[r][c].permanent = True
        
    def draw_initial(self, moves=False):
        # Numbers across the top
        self.gui.replace_labels('col', self.board_obj.col_constraints, colors=None)
        # Numbers down right side
        self.gui.replace_labels('row', reversed(self.board_obj.row_constraints), colors=None)
        # start and end
        #self.gui.clear_squares()
        #self.initial_board()
        
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
      self.board = self.solution_board
      self.update_board(self.board)
      dialogs.hud_alert('Game over')
      sleep(2)
      self.gui.show_start_menu()
       
    def hint(self):
        # place a random track piece not already placed
        @np.vectorize
        def contained(x):
          return x in list(self.gui.player.PIECE_NAMES.keys())[:-2]
          
        solution_tracks = np.argwhere(self.solution_board != '-')
        existing_tracks = np.argwhere(contained(self.board))
            
        # find solution tracks not in existing tracks
        # https://stackoverflow.com/questions/69435359/fast-check-if-elements-in-array-are-within-another-array-2d
        uni = np.any(np.all(solution_tracks[None, :, :] == existing_tracks[:, None, :], axis=-1,), axis=0,)
            
        unplaced_sol = solution_tracks[~uni]
        try:
            idx = randint(0, len(unplaced_sol)-1)
            loc = tuple(unplaced_sol[idx])
            self.board[loc] = self.solution_board[loc]
            self.highlight_permanent(loc)
            self.code_constraints(self.board)
        except (ValueError):
            dialogs.hud_alert('No more hints')
            return 1
        self.update_board(self.board)
    
    def perm_to_str(self, dict_):
        """ convert dotdict {'loc': xy, 'track': trackcode}
        to 4 character NW35 """
        r, c = dict_.loc
        rc_str = ''.join([str(r), str(c)])
        dir = self.gui.player.PIECE_NAMES[dict_.track]
        return dir + rc_str
                  
    def start_edit_mode(self):
      """ Entering edit mode modies currentle selected track set """
      self.board = self.convert_tracks()
      perm = self.convert_permanent()
                
      self.start_track = self.perm_to_str(perm.start) + 's'
      self.end_track = self.perm_to_str(perm.end) + 'e'
      self.known = [self.perm_to_str(k) for k in perm.known]
      self.update_board(self.board)
      
    def mark_start_end(self, coord, letter):
      """ check if new track is at edge and mark start or
      end as appropriate
      """
      dict_ = dotdict({'loc': coord, 'track': letter})
      r, c = coord
      dirn = self.gui.player.PIECE_NAMES[letter]
      # mark start
      if c == 0 and 'W' in dirn:        
        self.gui.clear_numbers(self.permanent.start.loc)
        
        self.board[self.permanent.start.loc] = '-'
        self.permanent.start.loc = coord
        self.permanent.start.track = letter
        self.highlight_permanent(coord, 'A')
        self.start_track = self.perm_to_str(dict_) + 's'
        return True
        
      # mark end
      if ((r == 0 and 'S' in dirn) or (r == (self.size-1) and 'N' in dirn)):
         self.gui.clear_numbers(self.permanent.end.loc)
         
         self.board[self.permanent.start.loc] = '-'
         self.permanent.end.loc = coord
         self.permanent.end.track = letter
         self.highlight_permanent(coord, 'B')  
         self.end_track = self.perm_to_str(dict_) + 'e'
         return True
      return False
      
    def mark_known (self, coord, letter):
      """ check if new track is known and mark or clear as appropriate
      """
      dict_ = dotdict({'loc': coord, 'track': self.board[coord]})      
      if coord in [k.loc for k in self.permanent.known]:
        #remove known
        self.gui.clear_numbers(coord)
        self.permanent.known = [kv for kv in self.permanent.known if kv.loc != coord]
        self.known.remove(self.perm_to_str(dict_)) 
      else:
        # new known
        self.permanent.known.append(dict_)
        self.known.append(self.perm_to_str(dict_))
        self.highlight_permanent(coord, '')              
            
    def add_new_track(self, coord, letter, row):
      dict_ = dotdict({'loc': coord, 'track': letter})
      dir_rc = self.perm_to_str(dict_)
      
      if self.identify_mode and row is None:
          start_end = self.mark_start_end(coord, letter)
          if not start_end:
              self.mark_known(coord, letter) 
          self.toggle_identify_tile()
      else:
          try:
            self.gui.set_prompt(f'adding new track {letter} to {coord}')
            self.board[coord] = letter
            self.update_board(self.board)
            
          except (IndexError):
            pass
      
      row, col = self.compute_constraints()
      self.gui.replace_labels('col', col, colors=None)
      # Numbers down right side
      self.gui.replace_labels('row', row, colors=None)
      self.update_board(self.board)
      sleep(1)
      self.gui.set_prompt('')
      
    def compute_constraints(self):
      """calculate constraint string
      format is Size:ColumnConstraintsRowConstraints:track-tuple:track-tuple
      """
      @np.vectorize
      def contained(x):
          return x in list(self.gui.player.PIECE_NAMES.keys())[:-2]
          
      col_sums = np.sum(contained(self.board), axis=0).astype('U1')
      row_sums = np.flip(np.sum(contained(self.board), axis=1)).astype('U1')
      constraintrc = ''.join(col_sums) + ''.join(row_sums)
      if self.known:
         self.constraints = ':'.join([str(self.size), constraintrc,
                                     self.start_track, ':'.join(self.known),
                                     self.end_track])
      else:
        self.constraints = ':'.join([str(self.size), constraintrc,
                                    self.start_track, self.end_track])
      self.gui.set_message2(self.constraints)
      
      return row_sums, col_sums
                                            
    def toggle_identify_tile(self):
      """ when identify tile is pressed, allow next pressed tile to be added to or deleted from known"""
      self.identify_mode = not self.identify_mode
      self.gui.set_props(self.identify, fill_color='red' if self.identify_mode else 'orange')
      
    def test_solve(self):
      """ Try to solve modified track layout
          if successful save button is enabled """
      self.gui.set_prompt('solve pressed')
      if hasattr(self, 'constraints'):
        print(self.constraints)
        self.game_item = self.constraints
        self.empty_board = np.full((self.size, self.size), '-')
        self.solution_board = self.empty_board.copy()
        result = self.initialize()
        if isinstance(result, ValueError) and 'Solved' in result.args:
            self.save_enabled = True
            self.gui.set_props(self.save, fill_color='orange')
      sleep(1)
      self.gui.set_prompt('')
      
    def save_constraint(self):
      """ If enabled, saves new track to end of traintracks.txt
          Disables save afterward"""
      if self.save_enabled:
        comment = dialogs.input_alert('Add comment')
        text = f'{self.constraints} #{comment}'
        print(text)
        with open(TRAINS, 'a')as f:
          f.write(text + '\n')
        self.save_enabled = False
        self.gui.set_props(self.save, fill_color='grey')
                    
    def process_turn(self, move, board):
        """ process the turn
        move is coord, new letter, selection_row
        """
        if move:
          coord, letter, row = move
          r, c = coord
          if letter == 'Enter':
            finished = self.hint()
            if finished:
              return 1
          
          elif letter == 'Edit Mode':
              self.edit_mode = not self.edit_mode
              self.gui.set_props(self.edit, fill_color='red' if self.edit_mode else 'orange')
              if self.edit_mode:
                self.start_edit_mode()
              else:
                #exit edit mode, leaving new board
                self.game_item = self.constraints
                self.initialize()
                #self.board = self.empty_board.copy()
                self.update_board(self.board)
        
          elif letter == 'Identify':
              self.toggle_identify_tile()
      
          elif letter == 'Solve':
              self.test_solve()
               
          elif letter == 'Save':
              self.save_constraint()
                
          elif coord == (None, None):
              return 0
                                     
          elif letter != '':  # valid selection
            if self.edit_mode:
              self.add_new_track(coord, letter, row)
            else:
                try:
                    r, c = coord
                    cell = self.board_obj.layout[r][c]
                    if not cell.permanent:
                       self.board[coord] = letter
                       self.update_board(self.board)
                       complete = self.code_constraints(self.board)
                       return complete
                except (IndexError):
                  pass
        return 0
    
    def code_constraints(self, board):
       """compare constraints with actual counts
       colour the constraints to match"""
       
       @np.vectorize
       def contained(x):
          return x in list(self.gui.player.PIECE_NAMES.keys())[:-2]
          
       def compute_check(known, sums, dirn):
           check = np.equal(sums, known)
           colors = np.where(check, 'white', '#ff5b5b')
           self.gui.replace_labels(dirn, known, colors=colors, font=('Arial Rounded MT Bold', 30))
           return np.all(check)
             
       col_known = np.array(self.board_obj.col_constraints)
       col_sums = np.sum(contained(self.board), axis=0)
       row_known = np.flip(np.array(self.board_obj.row_constraints))
       row_sums = np.flip(np.sum(contained(self.board), axis=1))
       
       return all([compute_check(col_known, col_sums, 'col'),
                   compute_check(row_known, row_sums, 'row')])
                  
    def game_over(self, finished):
      
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
       g = TrainTracks()
       g.run()
       
    def box_positions(self):
        x, y, w, h = self.gui.grid.bbox
        sqsize = self.gui.gs.SQ_SIZE
        # rack tiles are computed with this code
        # t.position = (w + 50 + (n % 2 * (20 + sqsize)) , h_sqsize-  n //2 * (20 + sqsize))
        
        # positions of all objects for all devices
        position_dict = {
        'ipad13_landscape': {'rackpos': (0, 0), 'rackscale': 1.0, 
                             'rackoff': 2,  'edit_size': (280, 125),
                             'button1': (w + 40, h / 12), 'button2': (w + 40, 220), 'button3': (w + 200, 220),
                             'button4': (w + 200, 150), 'button5': (w + 40, 150),
                             'box1': (w + 30, h - 50 - 4 * (sqsize + 20)), 'box2': (w + 30, 150 - 6), 'box3': (w + 5, 2 * h / 3),
                             'box4': (w + 5, h - 50), 'font': ('Avenir Next', 24)},
                                           
        'ipad13_portrait': {'rackpos': (50 - w, h + 50), 'rackscale': 1.0, 
                            'rackoff': 2, 'edit_size': (280, 125),
                            'button1': (w / 2, h + 200), 'button2': (w / 2, h + 50), 'button3': (w / 2, h + 250),
                            'button4': (w / 2, h + 100), 'button5': (w / 2, h + 150),
                            'box1': (45, h + h / 8 + 45), 'box2': (45, h + 45), 'box3': (2 * w / 3, h + 45),
                            'box4': (2 * w / 3, h + 200), 'font': ('Avenir Next', 24)},
        
        'ipad_landscape': {'rackpos': (0, -10), 'rackscale': 1.0, 'rackoff': 2, 'edit_size': (230, 110),
                           'button1': (w + 35, h / 12), 'button2': (w + 35, 190), 'button3': (w + 150, 190),
                           'button4': (w + 150, 140), 'button5': (w + 35, 140),
                           'box1': (w + 30, h - 4 * (sqsize + 20)), 'box2': (w + 30, 125-6), 'box3': (w + 5, 2 * h / 3),
                           'box4': (w + 5, h - 50), 'font': ('Avenir Next', 20)},
        
        'ipad_portrait': {'rackpos': (-w, 249), 'rackscale': 0.7, 'rackoff': 4, 'edit_size': (250, 110),
                          'button1': (690, h + 100), 'button2': (430, h +150), 'button3': (550 , h + 150),
                          'button4': (550, h + 100), 'button5': (430, h + 100),
                          'box1': (45, h + 55), 'box2': (420, h + 90), 'box3': (3 * w / 4, h + 35),
                          'box4': (3 * w / 4, h + 160), 'font': ('Avenir Next', 20)},
        
        'iphone_landscape': {'rackpos': (0, -50), 'rackscale': 1.5, 'rackoff': 2, 'edit_size': (255, 130),
                             'button1': (w + 185, h / 6), 'button2': (w + 185, 230), 'button3': (w + 330, 245),
                             'button4': (w + 330, 180), 'button5': (w + 185, 180),
                             'box1': (w + 30, h - 50 -4* (sqsize +20)), 'box2': (w + 180, 165 - 6), 'box3': (w + 5, 2 * h / 3),
                             'box4': (w + 5, h - 50), 'font': ('Avenir Next', 20)},
            
        'iphone_portrait': {'rackpos': (-w -25, h -10), 'rackscale': 1.5, 'rackoff': 2, 'edit_size': (135, 190),
                            'button1': (9 * w / 15, h + 100), 'button2': (9 * w / 15, h + 300), 'button3': (9 * w / 15, h + 250),
                            'button4': (9 * w / 15, h + 200), 'button5': (9 * w / 15, h + 150),
                            'box1': (0, h + h / 8 + 45), 'box2': (180,  h + 145), 'box3': (3 * w / 4, h + 35),
                            'box4': (3 * w / 4, h + 160), 'font': ('Avenir Next', 15)},
         }
        self.posn = SimpleNamespace(**position_dict[self.gui.device])
        
    def add_boxes(self):
      """ add non responsive decoration boxes"""
      x, y, w, h = self.gui.grid.bbox
      r = self.posn.rackoff
      t = self.posn.rackscale
      tsize = self.gui.gs.SQ_SIZE
      box = self.gui.add_button(text='', title='Tracks', position=self.posn.box1,
                                min_size=(r * t*tsize + 60, 8/r * (t*tsize + 20) + 20),
                                fill_color='clear')
      self.gui.set_props(box, font=self.posn.font)
      
      box = self.gui.add_button(text='', title='Editor', position=self.posn.box2,
                                min_size=self.posn.edit_size,
                                fill_color='clear')
      self.gui.set_props(box, font=self.posn.font)
      
    def set_buttons(self):
      """ install set of active buttons """
      x, y, w, h = self.gui.grid.bbox
      button = self.gui.set_enter('Hint', position=self.posn.button1,
                                  stroke_color='black', fill_color='yellow',
                                  color='black', font=self.posn.font)
      self.edit = self.gui.add_button(text='Edit Mode', title='', position=self.posn.button2,
                                      min_size=(80, 32), reg_touch=True,
                                      stroke_color='black', fill_color='orange',
                                      color='black', font=self.posn.font)
      self.identify = self.gui.add_button(text='Identify', title='', position=self.posn.button3,
                                          min_size=(100, 32), reg_touch=True,
                                          stroke_color='black', fill_color='orange',
                                          color='black', font=self.posn.font)
      button = self.gui.add_button(text='Solve', title='', position=self.posn.button4,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='orange',
                                   color='black', font=self.posn.font)
      self.save = self.gui.add_button(text='Save', title='', position=self.posn.button5,
                                      min_size=(100, 32), reg_touch=True,
                                      stroke_color='black', fill_color='grey',
                                      color='black', font=self.posn.font)
          

class Track(Enum):
    NE = 1
    SE = 2
    SW = 3
    NW = 4
    NS = 5
    EW = 6
    TEMP = 7

    @classmethod
    def identify(cls, str):
        """ return matching enum from 2 char string, order undefined"""
        for tr in cls:
            if str[0] in tr.name and str[1] in tr.name:
                return tr


class Cell:
    def __init__(self, row, col, cell_size):
        self.cell_size = cell_size
        self.y = row
        self.x = col
        self.row = row
        self.col = col
        self.permanent = False
        self.track = None
        self.must_connect = ""
        self.is_start = False
        self.is_end = False

    def __str__(self):
        return f"R:{self.row} C:{self.col} {self.track}"

    def is_empty(self):
        return self.track is None

    def has_dir(self, dir):
        if self.track:
            return dir in self.track.name

            
class Layout:
    def __init__(self, size=8, gui=None):
        self.size = size
        self.gui = gui
        self.layout = [[Cell(row, col, 0) for col in range(size)]
                       for row in range(size)]
        self.start = None
        self.end = None
        self.end_row = None
        self.move_count = 0
        self.move_max = 1000000
        self.col_count = []
        self.row_count = []
        self.col_perm = []
        self.row_perm = []

    def set_constraints(self, values):
        """ Takes string of numbers representing top and right side """
        v = list(values)
        self.col_constraints = [int(i) for i in v[: self.size]]
        right = v[self.size:]
        right.reverse()
        self.row_constraints = [int(i) for i in right]

    def add_track(self, track, row, col, start=False, end=False):
        """
        Add a permanent piece of track to the layout
        Start and end are special cases
        """
        cell = self.layout[row][col]
        cell.permanent = True
        cell.track = Track[track]
        if start:
            if col != 0:
                raise ValueError("Invalid start position")
            self.start = row
            cell.is_start = True
        if end:
            self.end = col
            self.end_row = row
            cell.is_end = True

        # determine adjacent cells that must connect
        # modify to allow end row to be 0 or size-1
        if "N" in track and row < self.size-1:
            self.layout[row + 1][col].must_connect += "S"
        if "S" in track and row > 0:
            self.layout[row - 1][col].must_connect += "N"
        if "W" in track and col > 0:
            self.layout[row][col - 1].must_connect += "E"
        if "E" in track:
            self.layout[row][col + 1].must_connect += "W"

    def moves(self, cell):
        """ return a list of possible moves from a cell """

        result = []
        r1 = cell.row - 1
        r2 = cell.row + 1
        c1 = cell.col - 1
        c2 = cell.col + 1

        if r2 < self.size and (not cell.track or cell.has_dir("N")):
            new_cell = self.layout[r2][cell.col]
            if not new_cell.track or new_cell.has_dir("S"):
                result.append("N")
        if r1 >= 0 and (not cell.track or cell.has_dir("S")):
            new_cell = self.layout[r1][cell.col]
            if not new_cell.track or new_cell.has_dir("N"):
                result.append("S")
        if c1 >= 0 and (not cell.track or cell.has_dir("W")):
            new_cell = self.layout[cell.row][c1]
            if not new_cell.track or new_cell.has_dir("E"):
                result.append("W")
        if c2 < self.size and (not cell.track or cell.has_dir("E")):
            new_cell = self.layout[cell.row][c2]
            if not new_cell.track or new_cell.has_dir("W"):
                result.append("E")
        if cell.is_start and "W" in result:
            result.remove("W")
        if cell.is_end and "S" in result:
            result.remove("S")
        return result

    def check_constraints(self, exact=False):
        """ Returns true if all cell counts within limits """
        self.row_count = (
            []
        )  # difference between actual count of occupied cells and expected count
        self.row_perm = []  # number of permanent cells in this row
        self.col_count = []
        self.col_perm = []
        for row in range(self.size):
            count = 0
            perm = 0
            for col in range(self.size):
                cell = self.layout[row][col]
                if cell.track:
                    count += 1
                if cell.permanent:
                    perm += 1
                if exact:
                    if cell.must_connect and not cell.track:
                        if DEBUG:
                            print("Must connect failure")
                        return False
            self.row_count.append(self.row_constraints[row] - count)
            self.row_perm.append(perm)
            if exact:
                if count != self.row_constraints[row]:
                    if DEBUG:
                        print(
                            f"Exact Row {row} failure {count} != {self.row_constraints[row]}"
                        )
                    return False
            elif count > self.row_constraints[row]:
                if DEBUG:
                    print(f"Row {row} failure {count} > {self.row_constraints[row]}")
                return False
        for col in range(self.size):
            count = 0
            perm = 0
            for row in range(self.size):
                cell = self.layout[row][col]
                if cell.track:
                    count += 1
                if cell.permanent:
                    perm += 1
            self.col_count.append(self.col_constraints[col] - count)
            self.col_perm.append(perm)
            if exact:
                if count != self.col_constraints[col]:
                    if DEBUG:
                        print(
                            f"Exact column {col} failure {count} != {self.col_constraints[col]}"
                        )
                    return False
            elif count > self.col_constraints[col]:
                if DEBUG:
                    print(f"Column {col} failure {count} > {self.col_constraints[col]}")
                return False
        return True

    def not_trapped(self, cell):
        """ Return false if trapped one side of a full row or col and need to get to the other side """

        for c in range(1, self.size - 1):
            if self.col_count[c] == 0:
                # ignore cols with a permanent track - if not connected, it may be a path back to other side
                if self.col_perm[c] == 0:
                    if cell.col < c:
                        for i in range(c + 1, self.size):
                            if self.col_count[i] > 0:
                                return False
                    elif cell.col > c:
                        for i in range(0, c):
                            if self.col_count[i] > 0:
                                return False
        for r in range(1, self.size - 1):
            if self.row_count[r] == 0:
                # ignore rows with a permanent track - if not connected, it may be a path back to other side
                if self.row_perm[r] == 0:
                    if cell.row < r:
                        for i in range(r + 1, self.size):
                            if self.row_count[i] > 0:
                                return False
                    if cell.row > r:
                        for i in range(0, 2):
                            if self.row_count[i] > 0:
                                return False
        return True

    def done(self, cell):
        if cell.row == self.end_row and cell.col == self.end:
            if self.check_constraints(exact=True):
                return True
        return False

    def move_from(self, cell, dir):
        """ move from cell in direction dir  """
        self.move_count += 1
        if DEBUG:
          self.gui.gui.set_moves(f'Moves {self.move_count}', position=(self.gui.gui.grid.bbox[2]+20, 20))
          self.gui.gui.update(self.gui.convert_tracks())
          sleep(0.1)
        if self.move_count == self.move_max:
            raise ValueError("Max move count reached")
        # if self.move_count == 8400:
        #     self.draw()
        #     breakpoint()
        
        if dir == "N":
            from_dir = "S"
            new_cell = self.layout[cell.row + 1][cell.col]
        elif dir == "S":
            from_dir = "N"
            new_cell = self.layout[cell.row - 1][cell.col]
        elif dir == "E":
            from_dir = "W"
            new_cell = self.layout[cell.row][cell.col + 1]
        elif dir == "W":
            from_dir = "E"
            new_cell = self.layout[cell.row][cell.col - 1]
        undo = False
        # temporarily add a track if empty so can calculate constraints
        if not new_cell.track:
            new_cell.track = Track.TEMP
        if self.done(new_cell):
            raise ValueError("Solved")
        if self.check_constraints():
            if self.not_trapped(new_cell):
                if new_cell.track == Track.TEMP:
                    new_cell.track = None
                moves = self.moves(new_cell)
                if from_dir in moves:
                    moves.remove(from_dir)
                bad_move = False
                # must connect cells are special case not handled in move generation
                if new_cell.must_connect:
                    if from_dir in new_cell.must_connect:
                        to_dir = new_cell.must_connect.replace(from_dir, "")
                        if to_dir:
                            moves = to_dir
                    else:
                        if len(new_cell.must_connect) == 1:
                            moves = new_cell.must_connect
                        else:
                            # must connect cell is already fully connected
                            bad_move = True

                if not bad_move:
                    # Recursively explore each possible move, depth first
                    for to_dir in moves:
                        if not new_cell.track:
                            new_cell.track = Track.identify(from_dir + to_dir)
                        self.move_from(new_cell, to_dir)
            else:
                if DEBUG:
                    print("Would be trapped")
        # Get here if all moves fail and we need to backtrack
        if not new_cell.permanent:
            new_cell.track = None
        if not cell.permanent:
            cell.track = None

    def solve(self):
        """ Initiate the recursive solver """
        new_cell = self.layout[self.start][0]
        moves = self.moves(new_cell)
        for to_dir in moves:
            self.move_from(new_cell, to_dir)
        raise ValueError("Failed to find solution")

    def result(self, message, elapsed):
        self.gui.gui.set_message(f"{message} in {self.move_count} moves. Time:{elapsed:.2f}s")
        if DEBUG:
            self.gui.gui.set_moves('')

# This class represents a directed graph 
# using adjacency list representation
class Graph:
      
  def __init__(self, vertices, board):
          # No. of vertices
          self.V = vertices 
          self.select =  int((vertices + (2 * sqrt(vertices) -1)) /2)
          self.no = 0
          self.allpaths =[]
          self.lengths =[]
          self.max_paths = 1
          self.t = time()
          
          # default dictionary to store graph
          self.graph = self.adj(board)
        
  def adj(self, board):
        xmax, ymax = board.shape
        adjdict = {}
        for r in range(ymax):
          for c in range(xmax):
            neighbours = []
            #random.shuffle(a)
            for dir in [(1,0), (0, -1), (-1, 0), (0, 1)]:
              yd, xd = dir
              if 0<=(r + yd)<ymax and 0<=(c + xd)<xmax:
                neighbours.append(board[r+yd][c+xd])
            shuffle(neighbours)
            adjdict[board[r, c]] = neighbours
        return adjdict     
      
        
  def printAllPathsUtil(self, u, d, visited, path):
          '''A recursive function to print all paths from 'u' to 'd'.
        visited[] keeps track of vertices in current path.
        path[] stores actual vertices and path_index is current
        index in path[]'''
          if self.finished:
            return True
          # Mark the current node as visited and store in path
          visited[u]= True
          path.append(u)
      
          # If current vertex is same as destination, then print
          # current path[]
          if u == d:
            #print (self.no, path)
            p = path.copy()
            if len(p) == self.select:
               self.allpaths.append(p)
               self.lengths.append(len(p))
               if len(self.allpaths) == self.max_paths:
                 #path =[]
                 return True
            self.no += 1
            
          else:
            # If current vertex is not destination
            # Recur for all the vertices adjacent to this vertex
            for i in self.graph[u]:
              if visited[i]== False:
                self.finished =  self.printAllPathsUtil(i, d, visited, path)
                if self.finished:
                  return True
                
          # Remove current vertex from path[] and mark it as unvisited
          path.pop()
          visited[u]= False
          return False
      
      
        
  def printAllPaths(self, s, d):
          # Prints all paths from 's' to 'd'
          # Mark all the vertices as not visited
          visited =[False]*(self.V)
          
          # Create an array to store paths
          path = []
          
          self.t = time()
          self.finished = False
          # Call the recursive helper function to print all paths
          self.printAllPathsUtil(s, d, visited, path)
          print('time', self.no, time()-self.t)          

def parse(params, gui):
    """
    Structure: Size:Constraints:track-tuple:track-tuple
    """
    bits = params.split(":")
    size = int(bits[0])
    if len(bits[1]) != 2 * size:
        raise ValueError("Error, constraint bits wrong length")
    layout = Layout(size, gui)
    layout.set_constraints(bits[1])
    
    for i in range(2, len(bits)):
        c = bits[i]
        start = False
        end = False
        if len(c) > 4:
            if c[4] == "s":
                start = True
            elif c[4] == "e":
                end = True
            # else:
            # raise (ValueError, "Params wrong - 2")
        layout.add_track(c[:2], int(c[2]), int(c[3]), start=start, end=end)
    if layout.start is None:
        raise ValueError('Error, start not specified, forgot to add "s"')
    if layout.end is None:
        raise ValueError('Error, end not specified, forgot to add "e"')
    return layout

def find_random_path(n=8):                  
      # Python program to print all paths from a source to destination.                  
      # This code is contributed by Neelam Yadav
      
      board = np.arange(n*n).reshape((n,n))
      start = board[(randint(0,n-3), 0)]
      end = board[(n-1, randint(4,n-1))]
      for _ in range(1):       
         g = Graph(n*n, board)
         g.max_paths = 1
         g.printAllPaths(start, end)
         print(f'{n=},{g.no=}')
         for p in g.allpaths:
            print(p)
            coords =[divmod(rc, n) for rc in p]
            print(coords)
      print(board)

                                                
if __name__ == '__main__':
  find_random_path(8)
  game = TrainTracks()
  game.run()











