import numpy as np
import traceback
import os
import sys
from time import perf_counter, time, sleep
from scene import Texture
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
from gui.gui_interface import Coord, Gui, Squares, dotdict
from track_solver import Graph, Layout
from gui.gui_scene import Tile
import gui.gui_scene as gscene
DEBUG = 0
TRAINS = 'traintracks.txt'


class Player():
  def __init__(self):
    self.PLAYER_1 = ' '
    self.PIECE_NAMES = {'┃': 'NS',  '━': 'EW', '┓': 'NW',
                        '┏': 'NE', '┗': 'SE', '┛': 'SW', '?': '?', 'x': 'x'}
    self.PIECES = [f'../gui/tileblocks/{tile}.png' for tile in self.PIECE_NAMES.values()]
    # use keys() instead of values() for lines
    self.NAMED_PIECES = {v: k for k, v in self.PIECE_NAMES.items()}

        
class TrainTracks():
    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.debug = False
        self.puzzle_select = 10
        self.game_item, size = self.load_words_from_file(TRAINS)
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
        
        self.gui.setup_gui(log_moves=True, grid_fill='white')
        self.gui.build_extra_grid(size, size, grid_width_x=1, grid_width_y=1,
                                  color='black', line_width=2, offset=None,
                                  z_position=100)
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
          t = Tile(Texture(Image.named(f'../gui/tileblocks/{tiles[tile]}.png')),
                   0,  0, sq_size=sqsize * self.posn.rackscale)
          t.position = (w + x + (n % r * (20 + sqsize * self.posn.rackscale)),
                        y - n // r * (20 + sqsize * self.posn.rackscale))
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
        rack = self.rack

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
        data_list = [item for item in data_list if item != '' and 
                     not item.startswith('#')]
        # choice random or selected
        if self.puzzle_select:
            selected = data_list[self.puzzle_select]
        else:
            selected = choice(data_list)
        size = int(selected.split(':')[0])
        return selected, size
        
    def show_permanent(self):
        """ clear and display permanent squares """
        self.gui.clear_squares()
        self.highlight_permanent(self.permanent.start.loc, 'A')
        self.highlight_permanent(self.permanent.end.loc, 'B')
        self.empty_board[self.permanent.start.loc] = self.permanent.start.track
        self.empty_board[self.permanent.end.loc] = self.permanent.end.track
        for known in self.permanent.known:
            self.highlight_permanent(known.loc, '')
            self.empty_board[known.loc] = known.track
        
    def initial_board(self):
        """ Get board layout and permanent cells from board_obj"""
        pass
        self.empty_board = np.full((self.size, self.size), '-', dtype='U1')
        board = self.convert_tracks()
        perm = self.convert_permanent_from_layout()
        if not self.edit_mode:
           self.show_permanent()
           self.board = self.empty_board.copy()
                                    
    def initialize(self):
        """This method should only be called once,
        when initializing the board."""
        self.gui.clear_messages()
        self.gui.set_enter('Hint')
        self.gui.clear_numbers()
        self.gui.set_top(f'Train Tracks: {self.game_item}')
        # add boxes and buttons if not already placed
        if not hasattr(self, 'edit'):
            self.box_positions()
            self.add_boxes()
            self.set_buttons()
        # parse constraint line
        try:
           self.board_obj = parse(self.game_item, self)
        except ValueError as e:
           self.gui.set_prompt(str(e))
           return e
        self.draw_constraints()
        try:
            start = perf_counter()
            self.initial_board()
            self.update_board(self.board)
            self.convert_permanent_from_layout()
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
            self.gui.set_prompt('')
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
      
    def convert_permanent_from_layout(self):
      """get permanent locations from layout
      and produce permanent dictionary"""
      b = self.convert_tracks()
      start_loc = (self.board_obj.start, 0)
      end_loc = (self.board_obj.end_row, self.board_obj.end)
      known_loc = [(r, c) for r in range(self.size) for c in range(self.size)
                   if self.board_obj.layout[r][c].permanent]
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
                  'alpha': 0.25, 'radius': 5,
                  'sqsize': self.gui.gs.SQ_SIZE, 'offset': (0.0, 0.0),
                  'font': ('Arial Rounded MT Bold', 30),
                  'text_anchor_point': (-1, 1)}
        self.gui.add_numbers([Squares(coord, text, **params)], clear_previous=False)
        r, c = coord
        self.board_obj.layout[r][c].permanent = True
        
    def draw_constraints(self):
        # Numbers across the top
        self.gui.replace_labels('col', self.board_obj.col_constraints, colors=None)
        # Numbers down left side
        self.gui.replace_labels('row', reversed(self.board_obj.row_constraints), colors=None)
        
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
    
    def perm_to_str(self, dict_, terminator=None):
        """ convert dotdict {'loc': xy, 'track': trackcode}
        to 4 character NW35 """
        r, c = dict_.loc
        rc_str = ''.join([str(r), str(c)])
        dir = self.gui.player.PIECE_NAMES[dict_.track]
        if terminator:
            return dir + rc_str + terminator
        else:
            return dir + rc_str
                  
    def start_edit_mode(self):
        """ Entering edit mode modies currently selected track set """
        self.board = self.convert_tracks()
        self.convert_permanent_from_layout()
        self.update_board(self.board)
      
    def place_random(self):
       if self.edit_mode:
          self.gui.set_message('Computing random track route')
          g = Graph(self.size)
          g.gui = self.gui
          coords, self.board = g.compute_random_path(self.size)
          self.gui.print_board(self.board)
          self.gui.clear_numbers()
          self.gui.set_message('')
          self.permanent = dotdict({'start': None,
                                    'end': None,
                                    'known': []})
          self.mark_start_end(g.start_loc, self.board[g.start_loc])
          self.mark_start_end(g.end_loc, self.board[g.end_loc])
          # mark up to 4 tracks as known
          track_length = len(coords)
          indexes = set([randint(3, track_length - 3) for _ in range(randint(1,4))])
          for idx in indexes:
            k = coords[idx]
            self.permanent.known.append(dotdict({'loc': k, 'track': self.board[k]}))
            self.highlight_permanent(k, '')
            
          row, col = self.compute_constraints()
          self.gui.replace_labels('col', col, colors=None)
          self.gui.replace_labels('row', row, colors=None)
          self.gui.set_top(self.constraints)
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
        try:
            self.gui.clear_numbers(self.permanent.start.loc)
            self.board[self.permanent.start.loc] = '-'
        except (AttributeError):
            pass
        self.permanent.start = dict_
        self.highlight_permanent(coord, 'A')
        return True
        
      # mark end
      if ((r == 0 and 'S' in dirn) or (r == (self.size-1) and 'N' in dirn)):
         try:
             self.gui.clear_numbers(self.permanent.end.loc)
             self.board[self.permanent.start.loc] = '-'
         except (AttributeError):
             pass
         self.permanent.end = dict_
         self.highlight_permanent(coord, 'B')
         return True
      return False
      
    def mark_known(self, coord, letter):
      """ check if new track is known and mark or clear as appropriate
      """
      dict_ = dotdict({'loc': coord, 'track': self.board[coord]})
      if coord in [k.loc for k in self.permanent.known]:
        # remove known
        self.gui.clear_numbers(coord)
        self.permanent.known = [kv for kv in self.permanent.known
                                if kv.loc != coord]
      else:
        # new known
        self.permanent.known.append(dict_)
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
      
      if self.permanent.known:
         known = [self.perm_to_str(k) for k in self.permanent.known]
         self.constraints = ':'.join([str(self.size), constraintrc,
                                      self.perm_to_str(self.permanent.start, 's'),
                                      ':'.join(known),
                                      self.perm_to_str(self.permanent.end, 'e')])
      else:
        self.constraints = ':'.join([str(self.size), constraintrc,
                                     self.perm_to_str(self.permanent.start, 's'),
                                     self.perm_to_str(self.permanent.end, 'e')])
                                    
      self.gui.set_message2(self.constraints)
      return row_sums, col_sums
                                            
    def toggle_identify_tile(self):
      """ when identify button is pressed, allow next pressed tile to be added to or deleted from known"""
      self.identify_mode = not self.identify_mode
      self.gui.set_props(self.identify, fill_color='red' if self.identify_mode else 'orange')
      
    def test_solve(self):
      """ Try to solve modified track layout
          if successful save button is enabled """
      self.gui.set_prompt('solve pressed')
      if hasattr(self, 'constraints'):
        print('trying to solve', self.constraints)
        self.game_item = self.constraints
        self.empty_board = np.full((self.size, self.size), '-')
        self.solution_board = self.empty_board.copy()
        result = self.initialize()
        if isinstance(result, ValueError) and 'Solved' in result.args:
            self.save_enabled = True
            self.gui.set_props(self.save, fill_color='orange')
            self.show_permanent()
      else:
          self.gui.set_message('Constraints not set')
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
              self.gui.set_props(self.edit, fill_color='red'
                                 if self.edit_mode else 'orange')
              self.gui.set_props(self.random, fill_color='orange'
                                 if self.edit_mode else 'grey')
              if self.edit_mode:
                self.start_edit_mode()
              else:
                # exit edit mode, leaving new board
                self.game_item = self.constraints
                self.initialize()
                # self.board = self.empty_board.copy()
                self.update_board(self.board)
        
          elif letter == 'Identify':
              self.toggle_identify_tile()
      
          elif letter == 'Solve':
              self.test_solve()
               
          elif letter == 'Save':
              self.save_constraint()
              
          elif letter == 'Random':
              self.place_random()
                
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
           self.gui.replace_labels(dirn, known, colors=colors,
                                   font=('Arial Rounded MT Bold', 30))
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
        # positions of all objects for all devices
        position_dict = {
        'ipad13_landscape': {'rackpos': (0, -45), 'rackscale': 1.0,
                             'rackoff': 2,  'edit_size': (280, 150),
                             'button1': (w + 40, h / 12), 'button2': (w + 40, 220),
                             'button3': (w + 200, 220), 'button4': (w + 200, 170),
                             'button5': (w + 40, 120), 'button6': (w+40, 170),
                             'box1': (w + 30, h - 50 - 4 * (sqsize + 20)), 'box2': (w + 30, 120 - 6),
                             'box3': (w + 5, 2 * h / 3),
                             'box4': (w + 5, h - 50), 'font': ('Avenir Next', 20)},
                                           
        'ipad13_portrait': {'rackpos': (50 - w, h + 50), 'rackscale': 1.0,
                            'rackoff': 2, 'edit_size': (280, 125),
                            'button1': (w / 2, h + 200), 'button2': (w / 2, h + 50), 'button3': (w / 2, h + 250),
                            'button4': (w / 2, h + 100), 'button5': (w / 2, h + 150), 'button6': (w / 2, h + 150),
                            'box1': (45, h + h / 8 + 45), 'box2': (45, h + 45), 'box3': (2 * w / 3, h + 45),
                            'box4': (2 * w / 3, h + 200), 'font': ('Avenir Next', 24)},
        
        'ipad_landscape': {'rackpos': (0, -10), 'rackscale': 1.0, 'rackoff': 2, 'edit_size': (230, 140),
                           'button1': (w + 35, 20), 'button2': (w + 35, 190), 'button3': (w + 150, 190),
                           'button4': (w + 150, 140), 'button5': (w + 35, 90), 'button6': (w + 35, 140), 
                           'box1': (w + 30, h -10 - 4 * (sqsize + 20)), 'box2': (w + 30, 90-6), 'box3': (w + 5, 2 * h / 3),
                           'box4': (w + 5, h - 50), 'font': ('Avenir Next', 20)},
        
        'ipad_portrait': {'rackpos': (-w, 249), 'rackscale': 0.7, 'rackoff': 4, 'edit_size': (250, 110),
                          'button1': (690, h + 100), 'button2': (430, h +150), 'button3': (550 , h + 150),
                          'button4': (550, h + 100), 'button5': (430, h + 100), 'button6': (430, h + 100),
                          'box1': (45, h + 55), 'box2': (420, h + 90), 'box3': (3 * w / 4, h + 35),
                          'box4': (3 * w / 4, h + 160), 'font': ('Avenir Next', 20)},
        
        'iphone_landscape': {'rackpos': (0, -50), 'rackscale': 1.5, 'rackoff': 2, 'edit_size': (255, 130),
                             'button1': (w + 185, h / 6), 'button2': (w + 185, 230), 'button3': (w + 330, 245),
                             'button4': (w + 330, 180), 'button5': (w + 185, 180), 'button6': (9 * w / 15, h + 150),
                             'box1': (w + 30, h - 50 -4* (sqsize +20)), 'box2': (w + 180, 165 - 6), 'box3': (w + 5, 2 * h / 3),
                             'box4': (w + 5, h - 50), 'font': ('Avenir Next', 20)},
            
        'iphone_portrait': {'rackpos': (-w -25, h -10), 'rackscale': 1.5, 'rackoff': 2, 'edit_size': (135, 190),
                            'button1': (9 * w / 15, h + 100), 'button2': (9 * w / 15, h + 300), 'button3': (9 * w / 15, h + 250),
                            'button4': (9 * w / 15, h + 200), 'button5': (9 * w / 15, h + 150), 'button6': (9 * w / 15, h + 150),
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
      box = self.gui.add_button(text='', title='Tracks',
                                position=self.posn.box1,
                                min_size=(r * t * tsize + 60, 8 / r * (t * tsize + 20) + 20),
                                fill_color='clear')
      self.gui.set_props(box, font=self.posn.font)
      
      box = self.gui.add_button(text='', title='Editor',
                                position=self.posn.box2,
                                min_size=self.posn.edit_size,
                                fill_color='clear')
      self.gui.set_props(box, font=self.posn.font)
      
    def set_buttons(self):
      """ install set of active buttons """
      x, y, w, h = self.gui.grid.bbox
      button = self.gui.set_enter('Hint', position=self.posn.button1,
                                  stroke_color='black', fill_color='yellow',
                                  color='black', font=self.posn.font)
      self.edit = self.gui.add_button(text='Edit Mode', title='',
                                      position=self.posn.button2,
                                      min_size=(80, 32), reg_touch=True,
                                      stroke_color='black', fill_color='orange',
                                      color='black', font=self.posn.font)
      self.identify = self.gui.add_button(text='Identify', title='',
                                          position=self.posn.button3,
                                          min_size=(100, 32), reg_touch=True,
                                          stroke_color='black', fill_color='orange',
                                          color='black', font=self.posn.font)
      button = self.gui.add_button(text='Solve', title='',
                                   position=self.posn.button4,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='orange',
                                   color='black', font=self.posn.font)
      self.save = self.gui.add_button(text='Save', title='',
                                      position=self.posn.button5,
                                      min_size=(100, 32), reg_touch=True,
                                      stroke_color='black', fill_color='grey',
                                      color='black', font=self.posn.font)
      self.random = self.gui.add_button(text='Random', title='',
                                        position=self.posn.button6,
                                        min_size=(100, 32), reg_touch=True,
                                        stroke_color='black', fill_color='grey',
                                        color='black', font=self.posn.font)
          
          
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

                                                
if __name__ == '__main__':

  game = TrainTracks()
  game.run()






















