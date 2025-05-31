import random
import traceback
from time import sleep, time
import numpy as np
import inspect
import json
from itertools import permutations
from cages import Cages

""" This is the calcultion section of suguru
to run on native Python
This uses no Pyhonista code
Chris Thomas April 2025
"""
BLOCK = '#'
SPACE = ' '
SIZE = 9  # fixed f
FILENAME = 'suguru.txt'
    
class Suguru(): 
   
  def __init__(self, test=None):
    self.debug = False    
    self.test = test
      
  def subset(self, board, loc, N=3):
        # get a subset of board of max NxN, centred on loc
        # subset is computed with numpy slicing
        # to make it as fast as possible
        # max and min are used to clip subset close to edges
        r, c = loc
        subset = board[max(r - (N-2), 0):min(r + N-1, board.shape[0]),
                              max(c - 1, 0):min(c + 2, board.shape[1])] 
        return subset
                       
  def time_us(self, t0, msg=''):
     print(f'{msg} {int((time()-t0) * 1e6):_}us')
     
  def board_rc(self, rc, board, value):
      board[rc[0]][rc[1]] = value
                              
  def check_valid(self, cage, number_set):
      # iterate thru each location in cage with
      # corresponding number
      # for each, check if surrounding squares have same number
      # return False if found
      for index, loc in zip(number_set, cage):
          subset = self.subset(self.board, loc, N=3)
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
        
  def sort_cages(self, cg, mode=0):
      self.cage_coords = [[(r, c) for r, c, _ in cage]
                          for cage in cg.cages]
      if mode == 1:
          # perfom depth first search on cages starting from shortest
          cg.small_adj_matrix()
          # start from smallest cage
          a = [len(v) for v in cg.cages]
          start = a.index(min(a))
          cg.dfs(start)
          self.cage_coords = [x for _, x in sorted(zip(cg.path, self.cage_coords),
                                                   key=lambda pair: pair[0])]
      else:
          self.cage_coords = sorted([[(r, c)
                                      for r, c, _ in cage]
                                     for cage in cg.cages],
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
          if self.test:
              print(self.msg)
          return puzzles
      except FileNotFoundError:
          pass
      
  def store_valid_puzzle(self, cg):
      """ add valid puzzle to file """
      # store in cages
      cages = [[(cage[0], cage[1], int(self.board[(cage[0], cage[1])]))
                for cage in cagelist]
               for cagelist in cg.cages]
      with open('suguru.txt', 'a') as f:
          f.write(json.JSONEncoder().encode(cages) + '\n')
                                                                                                                                                 
  def fill(self, cage_no, length, animate):
      """ use dfs to iterate through permutations of number set
      """
      self.fill_iteration += 1
      
      # return if the grid is filled
      if ~np.any(self.board == 0):
          return True
      if cage_no == length:
          return False
     
      if self.fill_iteration > self.size*10:
          if self.debug:
              print('too many iterations')
          return False
   
      cage = self.cage_coords[cage_no]
      if self.debug:
          print(f'\nCage {cage_no} Recursion depth >>>>>>>>>>>>>>>>>>>>>>'
                f'{len(inspect.stack())-self.initial_depth}')
          # self.cg.print_cage_board(self.board, self.cage_coords,
          # which=str(cage_no), highlight=cage)
          
      numbers = self.permutation_dict[len(cage)]
      random.shuffle(numbers)
      number_sets = self.permutation_dict[len(cage)]
      for index, number_set in enumerate(number_sets):
          if self.debug:
              self.cg.print_cage_board(self.board, self.cage_coords,
                                   which=f'cage={cage_no} index={index}',
                                   highlight=self.cage_coords[cage_no])
          t = time()
          if self.check_valid(cage, number_set):
              if self.fill(cage_no+1, length, animate):
                  if self.debug:
                      self.time_us(t, f'fill pass {index}')
                  return True
              self.clear_cage(cage)
              if self.debug:
                  print('backing up')
          # self.time_us(t, f'check fail {index}')
      if self.debug:
          self.time_us(t, f'fill fail {index}')
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
    result = self.fill(cage_no=0,
                       length=len(self.cage_coords),
                       animate=False)
    if result:
      self.solution_board = self.board.copy().astype('U1')
      self.cg.print_cage_board(self.solution_board, self.cage_coords, which='final')
    else:
       raise RuntimeError('no fill possible')
       
  
  def suguru_setup(self, random_color=False):
    """ setup grid for suguru
    choose either new puzzle or
    stored puzzle
    """
    if isinstance(self.puzzle, int):
        # #############################################################################
        # create new puzzle of size self.puzzle
        self.board = np.zeros((self.size, self.size), dtype=int)
        
        # self.gui.remove_labels()
        self.sizey, self.sizex = self.board.shape
        
        # setup cages creation
        cg = Cages('Full', size=self.size, pent_set=self.tiles)
        cg.suguru = True
        self.permutation_dict = {k: list(permutations(list(range(1, k + 1))))
                                 for k in range(1, 7)}
        
        # fit cages to board
        # might take several goes
        self.start_time = time()
        iteration = 0
        times = []
        times2 = []
        t2 = time()
        
        # loop until vslid puzzle found
        while True:
            try:
                # compute a cage set
                
                t = time()
                cg.solution, cg.cages = cg.run(display=self.debug)
                if self.debug:
                    cg.draw_board(cg.solution)
                times.append(time()-t)
                t = time()
                # now try to fill the cage set
                self.create_puzzle(cg)
                times2.append(time()-t)
                break
            except RuntimeError:
                iteration += 1
                times2.append(time()-t)
                # print(f'{cg.iterations}')
                if self.debug:
                    print(f'{iteration=} not solvable')
                continue
        times = np.array(times)
        times2 = np.array(times2)
        # print(times)
        # print(times2)
        print(f'{np.mean(times)=:.3f} {np.std(times)=:.3f}')
        print(f'{np.mean(times2)=:.3f} {np.std(times2)=:.3f}')
        print(f'{iteration=}') 
        print(f'total time {time()-t2:.2f}')
        self.store_valid_puzzle(cg)                                
        # now to assign colours and numbers
        self.cage_board = cg.solution
        # store coord and total for later display
        

                                                     
  #########################################################################
  # main loop
  def run(self):
      """
      Main method that prompts the user for input
      """ 
      self.cg = Cages()                 
      self.puzzles_from_file = self.load_puzzles()      
      self.select_list(self.test)                         
      self.suguru_setup(random_color=False)
      self.cg.print_cage_board(self.board, self.cage_coords, highlight=[(0,0)])              
  ######################################################################
  
  def select_list(self, test=None):
      '''Choose which category
                               
       for puzzles from file, categorise by size
       choose a size and it picks one at random
                                     N.  piece sizes visible'''
      self.options = {'Random 5x5': (5, [1, 3, 4, 5], 8),
                      'Random 6x6': (6, [1, 3, 4, 5, 6], 7),
                      'Random 7x7': (7, [1,2, 3, 4, 5], 10),
                      'Random 8x8': (8, [2, 3, 4, 5, 6], 9),
                      'Random 9x9': (9, [2, 3, 4, 5, 6], 10),
                      '-----------': (5, [1, 3, 4, 5], 8),
                      'Easy': (5, [1, 3, 4, 5], 8),
                      'Regular': (6, [1, 3, 4, 5, 6], 7),
                      'Medium': (7, [2, 3, 4, 5], 10),
                      'Hard': (8, [2, 3, 4, 5, 6], 9),
                      'Hardest': (9, [2, 3, 4, 5, 6], 10)}
      
      self.puzzle_no = -1       
      # testing we enter here
      selection = test
      self.size, self.tiles, self.start_visible = self.options[selection]
      self.puzzle = self.size          
      return True
                      
  
if __name__ == '__main__':
    Suguru(test='Easy').run()
