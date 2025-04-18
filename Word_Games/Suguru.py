
import random
import traceback
from time import sleep, time
from queue import Queue
import numpy as np
import inspect
import console
from itertools import permutations
from Letter_game import LetterGame, Player
from cages import Cages
from  peek import peek
import json
import matplotlib.pyplot as plt
from gui.gui_interface import Gui, Squares, Coord

""" This game is the Sudoko grid puzzle
both standard and Killer type are supported
You have to guess the number
Chris Thomas June 2024

"""
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
NOTE = (-1, -1)
HINT = (-2, -2)
SIZE = 9  # fixed for Sudoko
FILENAME = 'suguru.txt'

class Suguru(LetterGame):
  
  def __init__(self, test=None):
    self.debug = False
    self.sleep_time = 0.1
    self.test = test
    self.hints = 0
    self.cage_colors = ['teal', 'salmon', 'dark turquiose', 'yellow']
    # self.cage_colors = ['lunar green', 'desert brown', 'cashmere', 'linen']
    # self.cage_colors = ['#D8D0CD', '#B46543', '#DF5587', '#C83F5F']
    
    # allows us to get a list of rc locations
    self.log_moves = False
    self.straight_lines_only = False
    self.hint = False
    self.hint_result = None
    # create game_board and ai_board
    self.SIZE = self.get_size(f'{SIZE},{SIZE}')
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q  # pass queue into gui
    self.gui.set_alpha(False)
    self.gui.set_grid_colors(grid='black', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=False)
    
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'New ....': self.restart,
                             'Hint': self.perform_hint,
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    
    
    x, y, w, h = self.gui.grid.bbox
    match  self.gui.device:
       case'ipad_landscape':
           position = (w+10, 8*h/9)
       case'ipad_portrait':
           position = (7*w/9, h+50)
       case 'iphone_portrait':
           position = (180, 470)
       case 'ipad13_landscape':
           position = (w+10, 8*h/9)
       case 'ipad13_portrait':
           position = (8*w/9, h+50)
       case'ipad_mini_landscape':
           position = (w+10, 8*h/9)
       case'ipad_mini_portrait':
           position = (7*w/9, h+50)
           
    self.gui.set_enter('Note ', fill_color='clear', font=('Avenir Next', 50),position=position)
    self.gui.set_top('', position=(0, h+30))
   
         
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
      #locs=[]     
      for index, loc in zip(number_set, cage):          
          subset = self.gui.subset(self.board, loc, N=3)          
          if np.any(np.isin(index, subset)):
              self.clear_cage(cage)
              return False
          else:
              
              self.board_rc(loc, self.board, index)
              #locs.append(loc)
      return True
        
  def clear_cage(self, cage):
      # clear cage
      c = np.array(cage)
      self.board[(c[:,0], c[:,1])] = 0  
        
  def sort_cages(self, cg, mode=0):  
      self.cage_coords = [[Coord((r, c)) for r, c, _ in cage]  for cage in cg.cages]  
      if mode == 1:
           # perfom depth first search on cages starting from shortest
           cg.small_adj_matrix()
           #start from smallest cage
           a = [len(v) for v in cg.cages]
           start = a.index(min(a))
           cg.dfs(start)               
           self.cage_coords  =  [x for _, x in sorted(zip(cg.path, self.cage_coords), key=lambda pair: pair[0])]
      else:
            self.cage_coords = sorted([[Coord((r, c)) for r, c, _ in cage]  for cage in cg.cages], key=len)     
  
  def cage_board_view(self, cages):
        # create cage view of board
        # set board very big, then reduce
        board = np.zeros((20, 20), dtype=int)
        for cage in cages:
            for item in cage:
                r, c, number_val = item
                board[(r, c)] = number_val
        # furthest non zero value 
        r, c = np.max(np.argwhere(board>0), axis=0)
        board = board[:r+1, :c+1]
        return board
                  
  def load_puzzles(self):                   
      try:
          with open(FILENAME, 'r') as f:
              data = f.read()
          puzzle_strings = data.split('\n')          
          puzzles = []
          cage_sets= [json.loads(p) for p in puzzle_strings if p]
          for cage in cage_sets:
              board = self.cage_board_view(cage)
              puzzles.append((board, cage))
          return puzzles
      except FileNotFoundError:
          pass
      
  def store_valid_puzzle(self, cg):
      """ add valid puzzle to file """
      # store in cages
      cages = [[(cage[0], cage[1], int(self.board[(cage[0], cage[1])])) for cage in cagelist] for cagelist in cg.cages]    
      with open('suguru.txt', 'a') as f:
          f.write(json.JSONEncoder().encode(cages) + '\n')
                                                                                                                                                 
  def fill(self, cage_no, length, animate):
      """ use dfs to iterate through permutations of number set
      TODO not working correctly yet needs debug
      """ 
      self.fill_iteration += 1
      
      # if the grid is filled, succeed if every word is valid and otherwise fail
      if ~np.any(self.board ==0):
            return True
      if cage_no == length:
            return False
     
      if self.fill_iteration > self.size*10:
            if self.debug: print('too many iterations')
            return False
   
      cage = self.cage_coords[cage_no]
      if self.debug:
          print(f'\nCage {cage_no} Recursion depth >>>>>>>>>>>>>>>>>>>>>> {len(inspect.stack())-self.initial_depth}')                    
          # self.gui.print_board(self.board, which=str(cage_no), highlight=cage)     
          
      numbers = self.permutation_dict[len(cage)] 
      random.shuffle(numbers)
      number_sets = self.permutation_dict[len(cage)]
      for index, number_set in enumerate(number_sets):
          if self.debug:
              #print(f'{number_set} {index=}/{len(self.permutation_dict[len(cage)])}', end=' ')
              self.gui.print_board(self.board, which=f'cage={cage_no} index={index}', highlight=self.cage_coords[cage_no])     
          t=time()
          if self.check_valid(cage, number_set):               
               if self.fill(cage_no+1, length, animate):
                  if self.debug: self.time_us(t, f'fill pass {index}')
                  return True
               self.clear_cage(cage)
               if self.debug: print('backing up')
          #self.time_us(t, f'check fail {index}')
      if self.debug: self.time_us(t, f'fill fail {index}')
      return False      

  def create_puzzle(self, cg):
       """Create Suguru puzzle
       rules: 
           each cage contains numbers up to its size
           each number may not be adjacent to the same number in any direction      
       cages is generated by Cages.run() in cages.py 
       TODO order the cages so as to fail early
       currently by length, but maybe proximity?           
       """       
       self.board = np.zeros((self.size, self.size), dtype=int)
       self.sort_cages(cg, mode=0)       
       
       # shuffle once
       [random.shuffle(self.permutation_dict[len(cage)]) for cage in cg.cages]
       self.initial_depth = len(inspect.stack())       
       self.fill_iteration = 0
       self.initial_depth = len(inspect.stack())       
       result = self.fill(cage_no=0, length=len(self.cage_coords), animate=False)           
       if result:                                        
          self.solution_board = self.board.copy().astype('U1')
          self.gui.print_board(self.solution_board, which='final')
       else:
           raise RuntimeError('no fill possible')
       
  def suguru_setup(self, random_color=False):
    """ setup grid for suguru 
    options
    6x6, 2-6, 5 visible
    8x8, 1-5, 10 visible
    8x8, 2-6, 9 visible
    8x8, 1-5, 9 visible"""
    if isinstance(self.puzzle, int):        
        self.board = np.zeros((self.size,self.size), dtype=int)    
        self.gui.replace_grid(*self.board.shape)
        #self.gui.remove_labels()
        self.sizey, self.sizex = self.board.shape
        
        # setup cages creation
        cg = Cages('Full', size=self.size, pent_set=self.tiles)
        cg.suguru = True
        self.permutation_dict = {k: list(permutations(list(range(1, k+1)))) for k in range(1,7)}
        
        # fit cages to board
        # might take several goes
        self.start_time = time()
        iteration = 0
        times = []
        times2=[]
        t2=time()
        wait = self.gui.set_waiting('Finding puzzle')
        while True:
            try: 
                wait.name = f'# {iteration} in {(time()-t2):.1f}s'     
                t=time()
                cg.solution, cg.cages = cg.run(display=self.debug)                 
                if self.debug: cg.draw_board(cg.solution)
                times.append(time()-t)
                t=time()
                self.create_puzzle(cg)
                times2.append(time()-t)
                break
            except RuntimeError:
                iteration += 1
                times2.append(time()-t)
                #print(f'{cg.iterations}')
                if self.debug: print(f'{iteration=} not solvable')
                continue 
        times = np.array(times)
        times2 = np.array(times2)
        # print(times)
        # print(times2)
        print(f'{np.mean(times)=:.3f} {np.std(times)=:.3f}')
        print(f'{np.mean(times2)=:.3f} {np.std(times2)=:.3f}')
        print(f'{iteration=}')
        self.gui.reset_waiting(wait)
        self.store_valid_puzzle(cg)
        #plt.cla()
        #plt.hist(times, density=False, bins=30)  # density=False would make counts
        #plt.hist(times2, density=False, bins=30)  # density=False would make counts
        #plt.show()
        self.gui.set_message(f'Solved in {iteration * cg.iterations} iterations in {(time() - self.start_time):.2f} secs')    
                        
        # now to assign colours and numbers
        self.cage_board = cg.solution
        # store coord and total for later display
        
        if self.debug:
            self.gui.print_board(self.cage_board, which='cage board')
            
    else:
        # selected a working puzzle from the file
        self.board, cages = self.puzzle
        cg = Cages('Full', size=self.board.shape[0])
        cg.suguru = True
        self.start_visible = 8
        self.gui.replace_grid(*self.board.shape)
        #self.gui.remove_labels()
        self.sizey, self.sizex = self.board.shape
        self.size = self.board.shape[0]
        self.cage_coords = sorted([[Coord((r, c)) for r, c, _ in cage]  for cage in cages], key=len)    
        self.cage_board = self.board.copy()
        self.solution_board = self.board.copy().astype('U1')
    # display starting values
    # clear all numbers  bar INITIAL
    self.board = self.board.astype('U1')
    number_loc_list = self.gui.number_locs(self.board)
    random.shuffle(number_loc_list)   
    [self.board_rc(loc, self.board,  ' ') for loc in number_loc_list[self.start_visible:]]
    self.gui.update(self.board.astype('U1'))       
    
    self.adj_matrix = cg.calc_adj_matrix(self.cage_board)
    color_map_dict = cg.color_4colors(colors=self.cage_colors)
    color_map_dict = {k: color_map_dict[k] for k in sorted(list(color_map_dict))}
    color_map_list = list(color_map_dict.values())
    
    cg.color_map = color_map_list
    #cg.draw_board(self.cage_board)
    
        
    self.delta_t('calculate cages')
    self.square_list = []
    self.start_time = time()
    # add dotted lines around cages
    
    delta=0.45
    linewidth=2
    linedash=[10,10]
    for coords in self.cage_coords:                    
        points = cg.dotted_lines(coords, delta=delta)
        points = [self.gui.rc_to_pos(point) for point in points]
        self.gui.draw_line(points, line_width=linewidth, stroke_color='black', 
                           set_line_dash=linedash, z_position=50)
                                
        if random_color is False:
            color = color_map_dict[self.cage_board[coords[0]]]
        else:
            color = self.random_color()
        self.gui.add_numbers([Squares(coord, '', color, z_position=30,
                                      alpha=0.5, font=('Avenir Next', 20),
                                      text_anchor_point=(-0.9, 0.9))
                              for coord in coords], clear_previous=False)
    self.delta_t('display cages')
         
  
  #########################################################################
  # main loop
  def run(self):
    """
    Main method that prompts the user for input
    """
    if self.test is None:
       console.clear()
    self.gui.clear_messages()
    self.gui.set_enter('Note', fill_color='clear')    
    self.notes = {}
    selected = self.select_list(self.test)
    
        
    if self.debug: self.gui.gs.close()
    self.suguru_setup(random_color=False)            
    # self.gui.update(self.solution_board.astype('U1'))     
    self.gui.set_message2('')
    if self.test is None:
        while True:
          self.gui.set_top(f'Sudoko\t\tLevel {self.board.shape[0]}\t\tHints : {self.hints}',
                           font=('Avenir Next', 20))
          move = self.get_player_move(self.board)
          sleep(0.1)
          moves = self.select(move, self.board, text_list=False)
          self.process_selection(moves)
          
          if self.game_over():
            break
    
          self.gui.set_message2('Game over')
          self.complete()
    
  ######################################################################
  
  def select_list(self, test=None):
      '''Choose which category
                               N.  piece sizes visible'''
      puzzles_from_file = self.load_puzzles()
          
      self.options = {'Easy': (5, [1,3,4,5], 8),
                      'Guardian': (6, [1,3,4,5], 7),
                      'Medium': (7, [2, 3, 4, 5], 10),
                      'Hard': (8, [2,3,4,5,6], 9),
                      'Hardest': (8, [1,2,3,4,5], 8)}
      for ix, puzzle in enumerate(puzzles_from_file):
          s = puzzle[0].shape
          self.options[f'Puzzle{ix+1} ({s[0]}x{s[1]})'] = ix
          
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
            self.gui.input_text_list(prompt=prompt, items=items, position=position)
            
            while self.gui.text_box.on_screen:
              sleep(.1)
              try:
                selection = self.gui.selection
              except (Exception) as e:
                print(e)
                print(traceback.format_exc())
       
            if selection == "Cancelled_":
              return False
            elif len(selection) > 1:
              if selection.startswith('Puzzle'):
                 self.puzzle = puzzles_from_file[int(selection.split(' ')[0][6:])]
                 
              else:
                  self.size = self.options[selection][0]
                  self.tiles = self.options[selection][1]  
                  self.start_visible = self.options[selection][2] 
                  self.puzzle = self.size
              self.gui.selection = ''
              return True
            else:
                self.size = 7
                return False
      else:
           # testing we enter here
           selection = test
           self.size = self.options[selection][0]
           self.tiles = self.options[selection][1]  
           self.start_visible = self.options[selection][2] 
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
     self.notes.pop(coord, None)
     known_value = str(self.get_board_rc(coord, self.board))
     
     r, c = coord
     # look along row
     for col in range(self.size):
       try:
         self.notes[(r, col)].remove(known_value)
       except (KeyError, ValueError):
         pass
     # look along col
     for row in range(self.size):
       try:
         self.notes[(row, c)].remove(known_value)
       except (KeyError, ValueError):
         pass
     # look in local 3x3 square
     # gets start of enclosing 3x3 square
     r_off = 3 * (r // 3)
     c_off = 3 * (c // 3)
 
     for r in range(3):
       for c in range(3):
         try:
           self.notes[(r + r_off, c + c_off)].remove(known_value)
         except (KeyError, ValueError):
           pass
     if self.debug:
         print('removed note', coord, known_value, self.notes)
     
     # now update squares
     for pos, item in self.notes.items():
         self.add_note(pos, item)
         
  def add_note(self, pos, item):
      """ add a note to a cell"""
      font=('Avenir', 6)
      msg = ''.join([f'{let}\n' if i % 4 == 3 else f'{let}  ' for i, let in enumerate(item)]).strip()
      data = self.gui.get_numbers(pos)[pos]
      data['text'] = msg
      
      self.gui.put_numbers({pos: data}, font=font)
  
  def process_selection(self, move):
    """ process the turn
    move is coord, new letter, selection_row
    """
    if move:
      coord, letter, row = move
      if self.debug:
        print('received move', move)
      r, c = coord
      if not isinstance(letter, list):
          if coord == (None, None):
            return False
          elif letter == 'Finish':
            return True
            
          elif letter != '':
            # if Killer mode, need to always display totals
            if self.debug:
              print('processing', letter, coord)
            if self.get_board_rc(coord, self.board) != BLOCK:
              self.board_rc(coord, self.board, letter)
              self.gui.update(self.board.astype('U1'))
              
              # test if correct
              if self.get_board_rc(coord, self.board) != self.get_board_rc(coord, self.solution_board):
                if self.debug:
                   print('testing', letter, coord)
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
        if self.debug:
            print('add note', coord, self.notes)
        self.add_note(coord, letter)
           
      return True
                  
  def select(self, moves, board, text_list=True):
      
      long_press = self.gui.gs.long_touch
      # toggle hint button
      if moves == NOTE:
        self.hint = not self.hint
        if self.hint:
            self.gui.set_enter('NOTE', fill_color='red')
        else:
            self.gui.set_enter('Note ', fill_color='clear')
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
            if self.gui.device in ['ipad13_landscape']:
                position = (950, h / 2)       
            elif self.gui.device == 'ipad_landscape':
                position = (x+w+50, h / 2)    
            elif self.gui.device.endswith('_portrait'):               
                position = (x, y)
            else:
                position = (x + w, h / 2)
                
            select_method = self.gui.input_text_list if text_list else self.gui.input_numbers
                     
            panel = select_method(prompt=prompt, items=items, position=position,
                                      allows_multiple_selection = (long_press or self.hint))             
            while panel.on_screen:
                sleep(.1)
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
              if self.debug:
                  print('letter ', selection, 'row', selection_row)
              return rc, selection, selection_row
              
            elif selection == "Cancelled_":
              return (None, None), None, None
              
            elif all([sel in items for sel in selection]):
              self.gui.selection = ''
              if self.debug:
                  print('letters ', selection, 'rows', selection_row)
              return rc, selection, selection_row
            else:
              return (None, None), None, None
      
  def reveal(self):
    ''' skip to the end and reveal the board '''
    self.gui.update(self.solution_board.astype('U1'))
    # This skips the wait for new location and induces Finished boolean to
    # halt the run loop
    self.q.put(FINISHED)
    sleep(4)
    self.gui.show_start_menu()
    
  def perform_hint(self):
    """ uncover a random empty square """
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
    self.q.put(HINT)
    
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    self.__init__()
    self.run()
     
          
if __name__ == '__main__':
  Suguru().run()
