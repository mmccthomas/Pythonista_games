import random
import traceback
from time import sleep, time
from queue import Queue
import numpy as np
import inspect
import console
import json
from itertools import permutations
from Letter_game import LetterGame, Player
from cages import Cages
from gui.gui_interface import Gui, Squares, Coord
from setup_logging import logger, is_debug_level
""" This game is the Suguru grid puzzle
You have to guess the number
Chris Thomas April 2025
"""
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
NOTE = (-1, -1)
HINT = (-2, -2)
SIZE = 9  # fixed f
FILENAME = 'suguru.txt'
INITIAL_DICT = 'sug_dict.txt'
NOTE_text = '\u270e'


class Suguru(LetterGame):
  
  def __init__(self, test=None):
    self.sleep_time = 0.1
    self.test = test
    self.hints = 0
    # allow use of initial value file
    # with computed start values
    self.computed_known = True
    self.cage_colors = ['teal', 'salmon', 'dark turquiose', 'yellow',
                        'lunar green', 'cashmere', 'linen']
    # self.cage_colors = ['#D8D0CD', '#B46543', '#DF5587', '#C83F5F']
    
    # allows us to get a list of rc locations
    self.log_moves = False
    self.straight_lines_only = False
    self.hint = False
    self.hint_result = None
    # create game_board and ai_board
    self.SIZE = self.get_size(f'{SIZE},{SIZE}')
    # load the gui interface
    
    self.gui = Gui(self.board, Player())
    self.gui.q = Queue()  # pass queue into gui
    self.gui.set_alpha(False)
    self.gui.set_grid_colors(grid='black', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=False)
    self.gui.orientation(self.display_setup)
    # menus can be controlled by dictionary of labels
    # and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'New ....': self.restart,
                             'Hint': self.perform_hint,
                             'Fill possibles': self.possibles,
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    
  def display_setup(self):
    """set positions of display
    elements for different device
    sizes
    This is called also when devis is rotated
    """
    W, H = self.gui.get_device_screen_size()
    self.gui.device = self.gui.get_device()
    x, y, w, h = self.gui.grid.bbox
    match  self.gui.device:
       case'ipad_landscape':
           position_hint = (w+10, 8*h/9)
           self.num_position = (x+w+50, h / 2)
           position_puzzles = (w+10, h/4)
       case'ipad_portrait':
           position_hint = (7*w/9, h+50)
           self.num_position = (w/3, y)
           position_puzzles = (w/2, h)
       case 'iphone_portrait':
           position_hint = (200, 420)
           self.num_position = (x, y)
           position_puzzles = (x+30, h+50)
       case 'ipad13_landscape':
           position_hint = (w+10, 8*h/9)
           self.num_position = (w+100, h / 2)
           position_puzzles = (w+10, h/4)
       case 'ipad13_portrait':
           position_hint = (7*w/9, h+50)
           self.num_position = (w/3, y)
           position_puzzles = (w/2, h)
       case'ipad_mini_landscape':
           position_hint = (w+10, 8*h/9)
           self.num_position = (x+w+50, h / 2)
           position_puzzles = (w+10, h/4)
       case'ipad_mini_portrait':
           position_hint = (8*w/9, h+50)
           self.num_position = (w/3, 30)
           position_puzzles = (w/2, h+50)
       case'iphone_landscape':
           position_hint = (w+10, 8*h/9)
           self.num_position = (x+w+50, h / 2)
           position_puzzles = (w+10, h/4)
       case _:
           position_hint = (w+10, 8*h/9)
           self.num_position = (x+w+50, h / 2)
           position_puzzles = (w+10, h/4)
           
    self.gui.gs.pause_button.position = (32, H - 36)
    self.gui.set_enter(NOTE_text, color='red', fill_color='lightgrey',
                       font=('Avenir Next', 50),
                       position=position_hint)
    self.gui.set_top(self.gui.get_top(),
                     position=(0, h))
    self.gui.set_moves(self.gui.get_moves(),
                       anchor_point=(0, 0),
                       position=position_puzzles)
         
  def process_wordlist(self,  sep=False):
    puzzles = []
    puzzle = ''
    for line in self.wordlist:
        if sep:
            if '==' in line:
                puzzles.append(puzzle+'\n')
                puzzle = ''
            else:
                puzzle = puzzle + line.strip()
        else:
            puzzles.append(line)
    return puzzles
    
  def time_us(self, t0, msg=''):
     print(f'{msg} {int((time()-t0) * 1e6):_}us')
                         
  def check_valid(self, cage, number_set):
      # iterate thru each location in cage with
      # corresponding number
      # for each, check if surrounding squares have same number
      # return False if found
      for index, loc in zip(number_set, cage):
          subset = self.gui.subset(self.board, loc, N=3)
          if np.any(np.isin(index, subset)):
              self.clear_cage(cage)
              return False
          else:
              self.board_rc(loc, self.board, index)
              
      return True
        
  def clear_cage(self, cage):
      # clear cage
      c = np.array(cage)
      self.board[(c[:, 0], c[:, 1])] = 0
        
  def sort_cages(self, mode=0):
      self.cage_coords = [[Coord((r, c)) for r, c, _ in cage]
                          for cage in self.cg.cages]
      if mode == 1:
          # perfom depth first search on cages starting from shortest
          self.cg.small_adj_matrix()
          # start from smallest cage
          a = [len(v) for v in self.cg.cages]
          start = a.index(min(a))
          self.cg.dfs(start)
          self.cage_coords = [x for _, x in sorted(zip(self.cg.path, self.cage_coords),
                                                   key=lambda pair: pair[0])]
      else:
          self.cage_coords = sorted([[Coord((r, c))
                                      for r, c, _ in cage]
                                     for cage in self.cg.cages],
                                    key=len)
  
  def cage_board_view(self, cages):
      # create cage view of board
      # set board very big, then reduce
      board = np.zeros((20, 20), dtype=int)
      for cage in cages:
          for item in cage:
              r, c, number_val = item
              board[(r, c)] = number_val
      # furthest non zero value
      r, c = np.max(np.argwhere(board > 0), axis=0)
      board = board[:r + 1, :c + 1]
      return board
                  
  def load_puzzles(self):
      """ return a dictionary of list of puzzles for each size"""
      try:
          self.solution_dict = {}
          with open(FILENAME, 'r') as f:
              data = f.read()
          puzzle_strings = data.split('\n')
          puzzles = {'5x5': [], '6x6': [], '7x7': [], '8x8': [], '9x9': []}
          cage_sets = [json.loads(p) for p in puzzle_strings if p]
          for cage in cage_sets:
              board = self.cage_board_view(cage)
              shape = f'{board.shape[0]}x{board.shape[1]}'
              puzzles[shape].append((board, cage))
          self.msg = '\n'.join([f'{k},  {len(v)} puzzles'
                                for k, v in puzzles.items()])

          if self.computed_known:
              with open(INITIAL_DICT, 'r') as f:
                  data = f.read()
              self.solution_dict = json.loads(data)
            
          if self.test:
              print(self.msg)
          return puzzles
      except FileNotFoundError:
          pass
      
  def store_valid_puzzle(self):
      """ add valid puzzle to file """
      # store in cages
      cages = [[(cage[0], cage[1], int(self.board[(cage[0], cage[1])]))
                for cage in cagelist]
               for cagelist in self.cg.cages]
      with open('suguru.txt', 'a') as f:
          f.write(json.JSONEncoder().encode(cages) + '\n')
                                                                                                                                                 
  def fill(self, cage_no, length, animate):
      """ use dfs to iterate through permutations of number set
      TODO not working correctly yet needs debug
      """
      self.fill_iteration += 1
      
      # return if the grid is filled
      if ~np.any(self.board == 0):
          return True
      if cage_no == length:
          return False
     
      if self.fill_iteration > self.size*10:
          logger.debug('too many iterations')
          return False
   
      cage = self.cage_coords[cage_no]
      logger.debug(f'\nCage {cage_no} Recursion depth >>>>>>>>>>>>>>>>>>>>>>')
      logger.debug(f'{len(inspect.stack())-self.initial_depth}')
          # self.gui.print_board(self.board,
          # which=str(cage_no), highlight=cage)
          
      numbers = self.permutation_dict[len(cage)]
      random.shuffle(numbers)
      number_sets = self.permutation_dict[len(cage)]
      for index, number_set in enumerate(number_sets):
          if is_debug_level():
              self.gui.print_board(self.board,
                                   which=f'cage={cage_no} index={index}',
                                   highlight=self.cage_coords[cage_no])
          t = time()
          if self.check_valid(cage, number_set):
              if self.fill(cage_no+1, length, animate):
                  if is_debug_level():
                      self.time_us(t, f'fill pass {index}')
                  return True
              self.clear_cage(cage)
              logger.debug('backing up')
          # self.time_us(t, f'check fail {index}')
      if is_debug_level():
          self.time_us(t, f'fill fail {index}')
      return False
    
  def create_puzzle(self):
      """Create Suguru puzzle
      rules:
         each cage contains numbers up to its size
         each number may not be adjacent to the same number in any direction
      cages is generated by Cages.run() in cages.py
      TODO order the cages so as to fail early
      currently by length, but maybe proximity?
      """
      self.board = np.zeros((self.size, self.size), dtype=int)
      self.sort_cages(mode=0)
      
      # shuffle once
      [random.shuffle(self.permutation_dict[len(cage)]) for cage in self.cg.cages]
      self.initial_depth = len(inspect.stack())
      self.fill_iteration = 0
      self.initial_depth = len(inspect.stack())
      result = self.fill(cage_no=0,
                         length=len(self.cage_coords),
                         animate=False)
      if result:
        self.solution_board = self.board.copy().astype('U1')
        self.gui.print_board(self.solution_board, which='final')
      else:
         raise RuntimeError('no fill possible')
       
  def create_new_puzzle(self):
      # create new puzzle of size self.puzzle
      self.board = np.zeros((self.size, self.size), dtype=int)
      self.gui.replace_grid(*self.board.shape)
      # self.gui.remove_labels()
      self.sizey, self.sizex = self.board.shape
      
      # setup cages creation
      self.cg = Cages('Full', size=self.size, pent_set=self.tiles)
      self.cg.suguru = True
      self.permutation_dict = {k: list(permutations(list(range(1, k + 1))))
                               for k in range(1, 7)}
      
      # fit cages to board
      # might take several goes
      self.start_time = time()
      iteration = 0
      times = []
      times2 = []
      t2 = time()
      wait = self.gui.set_waiting('Finding puzzle')
      # loop until vslid puzzle found
      while True:
          try:
              # compute a cage set
              wait.name = f'# {iteration} in {(time()-t2):.1f}s'
              t = time()
              self.cg.solution, self.cg.cages = self.cg.run(display=is_debug_level())
              if is_debug_level():
                  self.cg.draw_board(self.cg.solution)
              times.append(time()-t)
              t = time()
              # now try to fill the cage set
              self.create_puzzle()
              times2.append(time()-t)
              break
          except RuntimeError:
              iteration += 1
              times2.append(time()-t)
              # print(f'{self.cg.iterations}')
              logger.debug(f'{iteration=} not solvable')
              continue
      times = np.array(times)
      times2 = np.array(times2)
      # print(times)
      # print(times2)
      print(f'{np.mean(times)=:.3f} {np.std(times)=:.3f}')
      print(f'{np.mean(times2)=:.3f} {np.std(times2)=:.3f}')
      print(f'{iteration=}')
      self.gui.reset_waiting(wait)
      self.store_valid_puzzle()
      self.gui.set_message(f'Solved in {iteration * self.cg.iterations}'
             f'iterations in {(time() - self.start_time):.2f} secs')
                      
      # now to assign colours and numbers
      self.cage_board = self.cg.solution
      # store coord and total for later display
      self.solved = None
      if is_debug_level():
          self.gui.print_board(self.cage_board, which='cage board')
      # clear all numbers  bar INITIAL
      self.board = self.board.astype('U1')
      number_loc_list = self.gui.number_locs(self.board)
      random.shuffle(number_loc_list)
      [self.board_rc(loc, self.board,  ' ')
          for loc in number_loc_list[self.start_visible:]]
            
  def puzzle_from_file(self):
      # selected a working puzzle from the file
      self.board, cages = self.puzzle
      self.cg = Cages('Full', size=self.board.shape[0])
      self.cg.suguru = True
      self.gui.replace_grid(*self.board.shape)
      # self.gui.remove_labels()
      self.sizey, self.sizex = self.board.shape
      self.cage_coords = sorted([[Coord((r, c)) for r, c, _ in cage]
                                 for cage in cages], key=len)
      self.cage_board = self.board.copy()
      self.solution_board = self.board.copy().astype('U1')
      self.cg.cages = cages
      self.cages = cages
          
      if self.computed_known and self.solution_dict:
          number_loc_list = self.solution_dict[str(cages)][0]
          # mark if puzzle was solved or not
          self.solved = bool(self.solution_dict[str(cages)][1])
          self.start_visible = 0
          board = np.full(self.board.shape, ' ')
          [self.board_rc(loc, board, str(self.board[tuple(loc)]))
           for loc in number_loc_list]
          self.board = board
      else:
          self.board = self.board.astype('U1')
          number_loc_list = self.gui.number_locs(self.board)
          random.shuffle(number_loc_list)
          [self.board_rc(loc, self.board,  ' ')
           for loc in number_loc_list[self.start_visible:]]
             
  def display_starting_values(self):
    # display starting values

    self.gui.update(self.board.astype('U1'))
      
    # convert to non adjacent colours
    [self.board_rc((r, c), self.cage_board, k)
        for (k, v) in enumerate(self.cg.cages)
        for (r, c, _) in v]
    self.adj_matrix = self.cg.calc_adj_matrix(self.cage_board)
    color_map_dict = self.cg.color_4colors(colors=self.cage_colors)
    color_map_dict = {k: color_map_dict[k]
                      for k in sorted(list(color_map_dict))}
    self.cg.color_map = list(color_map_dict.values())
        
    delta = 0.45
    linewidth = 2 if self.gui.device.startswith('ipad') else 1
    linedash = [10, 10]
    for coords in self.cage_coords:
        # add dotted lines around cages
        points = self.cg.dotted_lines(coords, delta=delta)
        points = [self.gui.rc_to_pos(point) for point in points]
        self.gui.draw_line(points, line_width=linewidth, stroke_color='black',
                           set_line_dash=linedash, z_position=50)
        
        # now colour cage
        color = color_map_dict[self.cage_board[coords[0]]]
        self.gui.add_numbers([Squares(coord, '', color, z_position=30,
                                      alpha=0.5, font=('Avenir Next', 20),
                                      text_anchor_point=(-0.9, 0.9))
                              for coord in coords], clear_previous=False)
                                                         
  def suguru_setup(self, random_color=False):
    """ setup grid for suguru    """
    if isinstance(self.puzzle, int):
        self.create_new_puzzle()
    else:
        self.puzzle_from_file()
    self.display_starting_values()    
    
  # main loop
  def run(self):
      """
      Main method that prompts the user for input
      """
      if self.test is None:
         console.clear()
      self.gui.clear_messages()
      self.gui.set_enter(NOTE_text, color='red', fill_color='lightgrey')
      self.notes = {}
      self.puzzles_from_file = self.load_puzzles()
      self.select_list(self.test)
      self.display_setup()
      self.gui.set_moves(self.msg)
              
      if is_debug_level() or self.test:
          self.gui.close()
      self.suguru_setup(random_color=False)
      
      self.gui.set_message2('')
      if self.test is None:
        while True:
            if self.solved is None:
                status = '?'
            else:
                status = '\u2713' if self.solved else '\u2717'
            if self.puzzle_no >= 0:
                self.gui.set_top(f'Suguru\t{self.board.shape[0]}x{self.board.shape[1]}'
                                 f'\t#{self.puzzle_no}\t{status}\tHints : {self.hints}',
                                 font=('Avenir Next', 20))
            else:
                self.gui.set_top(f'Suguru\t{self.board.shape[0]}x{self.board.shape[1]}'
                                 f'\t{status}\tHints : {self.hints}',
                                 font=('Avenir Next', 20))
            move = self.get_player_move(self.board)
            sleep(0.0)
            moves = self.select(move, self.board, text_list=False)
            self.process_selection(moves)
            
            if self.game_over():
              break
      
        self.gui.set_message2('Game over')
        self.complete()
    
  ######################################################################
  
  def select_list(self, test=None):
      '''Choose which category
                               
       for puzzles from file, categorise by size
       choose a size and it picks one at random
                                     N.  piece sizes visible'''
      self.options = {'Random 5x5': (5, [1, 3, 4, 5], 8),
                      'Random 6x6': (6, [1, 3, 4, 5, 6], 7),
                      'Random 7x7': (7, [2, 3, 4, 5], 10),
                      'Random 8x8': (8, [2, 3, 4, 5, 6], 9),
                      'Random 9x9': (9, [2, 3, 4, 5, 6], 10),
                      '-----------': (5, [1, 3, 4, 5], 8),
                      'Easy': (5, [1, 3, 4, 5], 8),
                      'Regular': (6, [1, 3, 4, 5, 6], 7),
                      'Medium': (7, [2, 3, 4, 5], 10),
                      'Hard': (8, [2, 3, 4, 5, 6], 9),
                      'Hardest': (9, [2, 3, 4, 5, 6], 10)}
      
      self.puzzle_no = -1
      items = [s.capitalize() for s in self.options]
      self.gui.selection = ''
      selection = ''
      if test is None:
          prompt = ' Select category'
          while self.gui.selection == '':
            if self.gui.device.endswith('_portrait'):
                x, y, w, h = self.gui.game_field.bbox
                position = (x + w, 40)
            else:
                position = None
            self.gui.input_text_list(prompt=prompt,
                                     items=items,
                                     position=position)
            
            while self.gui.text_box.on_screen:
                sleep(.1)
                try:
                    selection = self.gui.selection
                except (Exception) as e:
                    print(e)
                    print(traceback.format_exc())
       
            if selection == "Cancelled_":
                self.restart()
            elif len(selection) > 1:
                self.size, self.tiles, self.start_visible = self.options[selection]
                if selection.startswith('Random'):
                    puzzle_list = self.puzzles_from_file[selection.split(' ')[1]]
                    if puzzle_list:
                        self.puzzle_no = random.randint(0, len(puzzle_list)-1)
                        self.puzzle = puzzle_list[self.puzzle_no]
                    else:
                        console.hud_alert(f'No stored puzzles {selection.split(" ")[1]}')
                        return False
                else:
                    self.puzzle = self.size
                self.gui.selection = ''
                return True
            else:
                self.size = 7
                return False
      else:
          # testing we enter here
          selection = test
          self.size, self.tiles, self.start_visible = self.options[selection]
          self.puzzle = self.size
          self.gui.selection = ''
          return True
                     
  def game_over(self):
      """ check for finished game
      board matches solution"""
      return np.array_equal(self.board, self.solution_board)
      
  def update_notes(self, coord):
     """ update any related notes using known validated number"""
     # remove note from validated cell
     coord = Coord(coord)
     self.notes.pop(coord, None)
     known_value = str(self.get_board_rc(coord, self.board))
     for neighbour in coord.all_neighbours():
       try:
         self.notes[neighbour].remove(known_value)
       except (KeyError, ValueError):
         pass
     # remove known from notes in same cage
     same_cage_coords = np.argwhere(self.cage_board == self.cage_board[coord])
     for loc in same_cage_coords:
         try:
             self.notes[tuple(loc)].remove(known_value)
         except (KeyError, ValueError):
            pass
     logger.debug(f'removed note {coord}, {known_value}, {self.notes}')
     
     # now update squares
     for pos, item in self.notes.items():
         self.add_note(pos, item)
         
  def possibles(self):
      for cage in self.cages:
          cell_coords = [(cell[0], cell[1]) for cell in cage]
          existing = [self.board[loc] for loc in cell_coords]
          for cell in cage:
              loc = (cell[0], cell[1])
              if self.board[loc] != ' ':
                  continue
              subset = list(np.ravel(self.gui.subset(self.board, loc, N=3)))
              exclude = set(existing + subset)
              cell_poss = [str(i) for i in range(1, len(cage) + 1)
                           if str(i) not in exclude]
              self.notes[loc] = cell_poss
              self.add_note(loc, cell_poss)
                               
  def add_note(self, pos, item):
      """ add a note to a cell"""
      font = ('Avenir', 6)
      msg = ''.join([f'{let}\n' if i % 4 == 3 else f'{let}  '
                     for i, let in enumerate(item)]).strip()
      data = self.gui.get_numbers(pos)[pos]
      data['text'] = msg
      
      self.gui.put_numbers({pos: data}, font=font)
  
  def process_selection(self, move):
      """ process the turn
      move is coord, new letter, selection_row
      """
      if move:
          coord, letter, row = move
          logger.debug(f'received move {move}')
          r, c = coord
          if not isinstance(letter, list):
              if coord == (None, None):
                  return False
              elif letter == 'Finish':
                  return True
                
              elif letter != '':
                  logger.debug(f'processing {letter}, {coord}')
                  if self.get_board_rc(coord, self.board) != BLOCK:
                      self.board_rc(coord, self.board, letter)
                      self.gui.update(self.board.astype('U1'))
                      
                      # test if correct
                      if self.board[coord] != self.solution_board[coord]:
                          logger.debug(f'testing {letter}, {coord}')
                          # make square flash yellow
                          temp = self.gui.get_numbers(coord)
                          data = temp[coord]
                          data_temp = data.copy()
                          data_temp['color'] = 'yellow'
                          data_temp['alpha'] = 0.7
                          self.gui.put_numbers({coord: data_temp})
                          sleep(1.0)
                          self.board_rc(coord, self.board, ' ')
                            
                          # clear note. should clear try value from note also
                          try:
                              self.notes[(coord)].remove(letter)
                          except (KeyError, ValueError):
                              pass
                          data['text'] = ''
                          self.gui.put_numbers({coord: data})
                               
                          self.hints += 1
                      
                      else:  # correct (or lucky guess!)
                          temp = self.gui.get_numbers(coord)
                          data = temp[coord]
                          
                          # clear trial numbers
                          data['text'] = ''
                          self.gui.put_numbers({coord: data})
                      self.update_notes(coord)
                      self.gui.update(self.board.astype('U1'))
                      return False
                  else:
                      return False
                
          else:  # we've  got a list
              # add notes to square
              self.notes[coord] = letter
              logger.debug(f'add note {coord}, {self.notes}')
              self.add_note(coord, letter)
             
          return True
                  
  def select(self, moves, board, text_list=True):
      """
      open number panel to select number
      or numbers
      """
      long_press = self.gui.long_touch
      # toggle hint button
      if moves == NOTE:
          self.hint = not self.hint
          if self.hint:
              self.gui.set_enter(NOTE_text,
                                 color='white',
                                 fill_color='red')
          else:
              self.gui.set_enter(NOTE_text.upper(),
                                 color='red',
                                 fill_color='lightgrey')
          return (None, None), None, None
        
      if moves == HINT:
          return self.hint_result[0], self.hint_result[1], None
        
      rc = moves
      if self.get_board_rc(rc, self.board) == SPACE:
          # now got rc as move
          # now open list
          if board is None:
              board = self.board
          possibles = list('123456789')  # 1 thru 9
          items = possibles
          if long_press or self.hint:
              prompt = "Select multiple"
          else:
              prompt = "Select a number"
          if len(possibles) == 0:
            raise (IndexError, "possible list is empty")
               
          self.gui.selection = ''
          selection = ''
          x, y, w, h = self.gui.grid.bbox
          while self.gui.selection == '':
                     
              panel = self.gui.input_numbers(
                         prompt=prompt, items=items,
                         position=self.num_position,
                         allows_multiple_selection=(long_press or self.hint))
              while panel.on_screen:
                  sleep(.01)
                  try:
                      selection = self.gui.selection.lower()
                      selection_row = self.gui.selection_row
                  except (AttributeError):  # got a list
                      selection = self.gui.selection
                      selection_row = self.gui.selection_row
                  except (Exception) as e:
                      print(e)
                      print(traceback.format_exc())
            
              if selection in items:
                  self.gui.selection = ''
                  logger.debug(f'letter {selection}, row {selection_row}')
                  return rc, selection, selection_row
                
              elif selection == "Cancelled_":
                  return (None, None), None, None
                
              elif all([sel in items for sel in selection]):
                  self.gui.selection = ''
                  logger.debug(f'letters {selection}, rows {selection_row}')
                  return rc, selection, selection_row
              else:
                  return (None, None), None, None
      
  def reveal(self):
      ''' skip to the end and reveal the board '''
      self.gui.update(self.solution_board.astype('U1'))
      # This skips the wait for new location and induces Finished boolean to
      # halt the run loop
      self.gui.q.put(FINISHED)
      sleep(4)
      self.gui.show_start_menu()
    
  def perform_hint(self):
      """ uncover a random empty square """
      # self.possibles()
      while True:
          coord = (random.randint(0, self.size), random.randint(0, self.size))
          if self.get_board_rc(coord, self.board) != SPACE:
              continue
          else:
              break
      letter = self.get_board_rc(coord, self.solution_board)
      self.board_rc(coord, self.board, letter)
      self.hint_result = (coord, letter)
      self.hints += 2
      self.gui.q.put(HINT)
    
  def restart(self):
      self.gui.close()
      self.finished = False
      self.__init__()
      self.run()
     
          
if __name__ == '__main__':
    Suguru().run()
