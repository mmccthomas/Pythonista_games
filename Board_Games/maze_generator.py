#TODO modify to use selectable generators from mazelib
# use routine to convert blocks and spaces  grid to 3d northband east grid as this is efficient
# wilson does not produce very nice mazes

# Maze Generator
#  Wilson's Loop Erased Random Walk Algorithm
# Author: CaptainFlint
# https://artofproblemsolving.com/community/c3090h2221709_wilsons_maze_generator_implementation
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent) 
sys.path.append(current + '/Mazelib')
import random
import numpy as np
from time import time, sleep
from random import sample, randint, choice, shuffle
import traceback
from queue import Queue
from Mazelib.mazelib import Maze
from Mazelib.mazelib.generate.MazeGenAlgo import MazeGenAlgo
from Mazelib.mazelib.generate.AldousBroder import AldousBroder
from Mazelib.mazelib.generate.BacktrackingGenerator import BacktrackingGenerator
from Mazelib.mazelib.generate.BinaryTree import BinaryTree
from Mazelib.mazelib.generate.CellularAutomaton import CellularAutomaton
from Mazelib.mazelib.generate.Division import Division
from Mazelib.mazelib.generate.DungeonRooms import DungeonRooms
from Mazelib.mazelib.generate.Ellers import Ellers
from Mazelib.mazelib.generate.GrowingTree import GrowingTree
from Mazelib.mazelib.generate.HuntAndKill import HuntAndKill
from Mazelib.mazelib.generate.Kruskal import Kruskal
from Mazelib.mazelib.generate.Prims import Prims
from Mazelib.mazelib.generate.Sidewinder import Sidewinder
from Mazelib.mazelib.generate.TrivialMaze import TrivialMaze
from Mazelib.mazelib.generate.Wilsons import Wilsons
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch

NORTH = 0
EAST = 1     
                                    
        
class HunterKillerMaze():
  
  def __init__(self, width, height):
    """ initialises maze
    self.grid has format n x m x 2,
    where axis 2 is not North border, not East border 
    """
    self.width = width
    self.height = height
    #self.grid = np.zeros((height, width, 2), bool)
    # a grid to track if the cell has been visited
    self.visited = np.zeros((self.height, self.width), bool)
    self.solution = []
    self.dirn = { (-1, 0): 'N', (1, 0): 'S', (0, 1): 'E', (0, -1): 'W'}
    self.inv_dirn = {v: k for k, v in self.dirn.items()}
    self.generated = False
    self.directions = [self.north, self.south, 
                        self.east, self.west]
    self.start = (self.height - 1, 0)
    self.end = (0, self.width - 1)
    
  def north(self, cell):
      r, c = cell
      return r - 1, c

  def south(self, cell):
      r, c = cell
      return r + 1, c
        
  def east(self, cell):
      r, c = cell
      return r, c + 1
    
  def west(self, cell):
      r, c = cell 
      return r, c - 1
      
  def endpoints(self, start, end):
        self.start = start
        self.end = end
           
  def can_move(self, dir_str, cell):
    """ return if cell in direction dir_str N,S,E,W is reachable"""
    dy, dx = self.inv_dirn[dir_str]
    r, c = cell
    
    if  not (0 <= c + dx < self.width and 0 <= r + dy < self.height):
      return False
      
    match dir_str:
      case 'E':      
        return self.grid[cell][EAST]
      case 'S':      
        return self.grid[self.south(cell)][NORTH]
      case 'W':
        return self.grid[self.west(cell)][EAST]
      case 'N':      
        return self.grid[cell][NORTH]
      case _:
        return False
        

  def draw_maze(self):
    
    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    width = self.grid.shape[1]
    height = self.grid.shape[0]

    # draw the south and west outer walls
    plt.plot([0, width], [0, 0], color="black")
    plt.plot([0, 0], [0, height], color="black")
    # upside down
    for r in range(height):
        for c in range(width):
            value = self.grid[self.height-1- r, c]

            if not value[EAST]:
                # draw a east wall
                plt.plot([c + 1, c + 1], [r, r + 1], color="black")

            if not value[NORTH]:
                # draw a north wall
                plt.plot([c, c + 1], [r + 1, r + 1], color="black")

    plt.show()

  def check_in_grid(self, new_cell):
       return   0 <= new_cell[1] < self.width and  0 <= new_cell[0] < self.height
              
  def possible_moves(self, cell: (int, int)):
      moves = []  
      for direction in self.directions:
          new_cell = direction(cell)
          if not self.check_in_grid(new_cell) or self.visited[new_cell]:
              continue      
          moves.append(new_cell)  
      return moves
  

  def get_adjacent_visited(self, cell):
      cells = []
      for direction in self.directions:
          new_cell = direction(cell)  
          if not self.check_in_grid(new_cell):
              continue     
          if self.visited[new_cell]:
              cells.append(new_cell)
  
      return cells
  
  def hunt(self):
      """ choose a new starting point next to a visited cell """
      for r in range(self.height):
          for c in range(self.width):
              if self.visited[(r, c)]:
                  continue                  
              adjacent = self.get_adjacent_visited((r, c))
              if len(adjacent) == 0:
                  continue                      
              new_cell = random.choice(adjacent)
              return new_cell, (r, c)
              
  def link_cells(self, current_cell, new_cell):
    ''' link it to a cell next to it that has already been visited
    linking is removing wall'''
    r, c = current_cell
    r1, c1 = new_cell
    dirn = self.dirn[(r1 - r, c1 - c)]
    
    #print(f'moving {dirn} {current_cell=}, {new_cell=}')
    match dirn:
      case 'E':      
        self.grid[current_cell][EAST] = True    
      case 'S':      
        self.grid[new_cell][NORTH] = True    
      case 'W':
        self.grid[new_cell][EAST] = True
      case 'N':      
        self.grid[current_cell][NORTH] = True
  
  def _get_next_cell(self, cell, dirNum, fact):
        """
        Outputs the next cell when moved a distance fact in the
        direction specified by dirNum from the initial cell.
        """
        dirTup = np.array(self.inv_dirn['NSEW'[dirNum]])
        next = np.array(cell) + fact * dirTup
        return tuple(next)
        
  def _is_valid_direction(self, cell, dirNum):
        """
        Checks if the adjacent cell in the direction specified by
        dirNum is within the grid
        cell: tuple (y,x) representing position of initial cell
        dirNum: int with values 0,1,2,3"""
        newCell = self._get_next_cell(cell, dirNum, 2)
        r, c = tuple(newCell)
        return (0 <= r < self.width and 0 <= c < self.height)
                  
  def generate_maze(self):  
      # set the current cell to a random value

      current_cell = (random.randint(0, self.height - 1), random.randint(0, self.width - 1))
        
      unvisited_count = self.width * self.height
  
      self.visited[current_cell] = True
      unvisited_count -= 1
  
      while unvisited_count > 0:
          
          #self.draw_maze()
          #sleep(.1)
          moves = self.possible_moves(current_cell)          
          if len(moves) > 0:
              new_cell = random.choice(moves)
          else:
              current_cell, new_cell = self.hunt()  
              
          self.link_cells(current_cell, new_cell)  
          self.visited[new_cell] = True
          unvisited_count -= 1  
          current_cell = new_cell
      
      self.generated = True
      return self.grid
        
  def adjacency(self):
      """construct adjacency matrix
      neighbours are shuffled to force random path
      board is a numpy 3d array of booleans
      """
      adjdict = {}
      for r in range(self.height):
          for c in range(self.width):
              rc = r, c
              neighbours = []
              for dir_str in  'NSEW':
                    if self.can_move(dir_str, rc):
                       yd, xd = self.inv_dirn[dir_str]    
                       neighbours.append((r + yd, c + xd))
              shuffle(neighbours)
              adjdict[(r, c)]= neighbours
      return adjdict
  
    
  def dfs(self, node, graph, visited, path, stop=None):
    #component.append(node)  # Store answer
    if node == stop:
       return True
    visited[node] = True  # Mark visited
    if node == stop:
          #component.append(node) 
          return 
    # Traverse to each adjacent node of a node
    for coord in graph[node]:
                 
        if not visited[coord]:  # Check whether the node is visited or not
            path[coord] = node
            finished =self.dfs(coord, graph, visited, path, stop)  # Call the dfs recursively  
            if finished:
              return True
        
  
  def bfs(self, node, graph, visited, path,stop=None): #function for BFS
    """ This will return all child node of starting node
    return is a list of dictianaries {'word_obj', 'depth' 'parent'} """
    queue = Queue()
    visited[node] = True
    queue.put(node)
    
    while not queue.empty():    # Creating loop to visit each node      
      node = queue.get() # from front of queue     
      if node == stop:
          return     
      for coord in graph[node]:        
        if  not visited[coord]:
          visited[coord] = True
          queue.put(coord)
          path[coord] = node
    return   
            
  def solve_maze(self, method='bfs'):
        """
        Solves the maze according to the Wilson Loop Erased Random
        Walk Algorithm"""
        # if there is no maze to solve, cut the method
        if not self.generated:
            return None
            
        solve_fn = self.dfs if method == 'dfs' else self.bfs
          
        visited = np.zeros((self.height, self.width), dtype=bool)
        adj = self.adjacency()
        path = {}
        solve_fn(self.start, adj, visited, path, stop=self.end)
        
        # path is a dictionary of form {parent_node: child node} """
        # convert to simple path list from end to start
        index = self.end
        path_list = []
        while index != self.start:
          path_list.append(path[index])
          index = path[index]
        #path_list.append(self.start) 
        return path_list
      
  def convert_grid(self):
    """ convert grid into simple block and space to compare with generated grid"""
    self.display_grid = np.full((2 * self.height + 1, 2 * self.width + 1), 0, dtype=int)
    self.display_grid[:, 0] = 1
    self.display_grid[-1, :] = 1       
    # this is for visibility and debugging     
    dirgrid = np.full((self.height, self.width), '. ', dtype='U2')
    for r in range(self.height):
      for c in range(self.width):
         text = [' ', ' ']
         if not self.grid[(r, c)][EAST]:
           text[1] = 'E'
         if not self.grid[(r, c)][NORTH]:
           text[0] = 'N'
         dirgrid[(r,c)] = ''.join(text)
         
    for r in range(self.height):
      for c in range(self.width):
         if 'N' in dirgrid[(r, c)]:
           self.display_grid[2*r, 2*c :2*c+3] = 1
         if 'E' in dirgrid[(r, c)]:
           self.display_grid[2 * r : 2*r+3, 2*c +2] = 1    
    return self.display_grid, dirgrid

class SelectableMaze(HunterKillerMaze):
  
  def __init__(self, height, width, mazetype=None):
      super().__init__(width, height)
      self.height, self.width = height, width
      self.maze = Maze()
      self.mazetypes = [AldousBroder, BacktrackingGenerator,
                        CellularAutomaton,
                        DungeonRooms,
                        GrowingTree,
                        HuntAndKill, Kruskal,
                        Prims, Sidewinder,
                        Wilsons]
      if mazetype is None:
        self.maze_fn = choice(self.mazetypes)                 
      else:
        try:
          # convert from string to class
          self.maze_fn = globals()[mazetype]
        except (KeyError):
          raise KeyError(f'Maze type {mazetype} not known')
      self.maze.generator = self.maze_fn(height, width)
      
  def generate_maze(self):
      """ generate a maze and return a block grid and 3d grid """
      self.maze.generate()
      self.maze.generate_entrances(self.start, self.end)
      self.block_grid = self.maze.grid.copy()
      self.grid = self.generate_north_east()
      self.generated = True
    
  def generate_north_east(self):
      """ convert block maze to n x m x 2 grid
          grid represents ability to move north or east from east cell
          1=clear, 0=blocked
      """
      self.grid = np.full((self.height, self.width, 2), False, dtype=bool)
      # north
      for index, r in enumerate(range(1, self.block_grid.shape[0], 2)):          
          blocks = self.block_grid[r - 1, 1::2]
          self.grid[index, :, NORTH] = np.logical_not(blocks==1)         
      # east      
      for index, c in enumerate(range(1, self.block_grid.shape[1], 2)):          
          blocks = self.block_grid[1::2, c + 1]
          self.grid[:, index, EAST] = np.logical_not(blocks==1)          
        
      return self.grid  
             
  def showPNG(self,grid):
    """Generate a simple image of the maze."""
    plt.figure(figsize=(10, 5))
    plt.imshow(grid, cmap=plt.cm.binary, interpolation='nearest')
    plt.xticks([]), plt.yticks([])
    plt.show() 
    
  def plotXKCD(self, grid):
    """ Generate an XKCD-styled line-drawn image of the maze. """
    
    def use_run(codes, vertices, run):
        """Helper method for plotXKCD. Updates path with newest run."""
        if run:
            codes += [Path.MOVETO] + [Path.LINETO] * (len(run) - 1)
            vertices += run
        
    H = len(grid)
    W = len(grid[0])
    h = (H - 1) // 2
    w = (W - 1) // 2

    with plt.xkcd(0,0,0):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        vertices = []
        codes = []

        # loop over horizontals
        for r,rr in enumerate(range(1, H, 2)):
            run = []
            for c,cc in enumerate(range(1, W, 2)):
                if grid[rr-1,cc]:
                    if not run:
                        run = [(r,c)]
                    run += [(r,c+1)]
                else:
                    use_run(codes, vertices, run)
                    run = []
            use_run(codes, vertices, run)

        # grab bottom side of last row
        run = []
        for c,cc in enumerate(range(1, W, 2)):
            if grid[H-1,cc]:
                if not run:
                    run = [(H//2,c)]
                run += [(H//2,c+1)]
            else:
                use_run(codes, vertices, run)
                run = []
            use_run(codes, vertices, run)

        # loop over verticles
        for c,cc in enumerate(range(1, W, 2)):
            run = []
            for r,rr in enumerate(range(1, H, 2)):
                if grid[rr,cc-1]:
                    if not run:
                        run = [(r,c)]
                    run += [(r+1,c)]
                else:
                    use_run(codes, vertices, run)
                    run = []
            use_run(codes, vertices, run)

        # grab far right column
        run = []
        for r,rr in enumerate(range(1, H, 2)):
            if grid[rr,W-1]:
                if not run:
                    run = [(r,W//2)]
                run += [(r+1,W//2)]
            else:
                use_run(codes, vertices, run)
                run = []
            use_run(codes, vertices, run)

        vertices = np.array(vertices, float)
        path = Path(vertices, codes)

        # for a line maze
        pathpatch = PathPatch(path, facecolor='None', edgecolor='black', lw=2)
        ax.add_patch(pathpatch)

        # hide axis and labels
        ax.axis('off')
        #ax.set_title('XKCD Maze')
        ax.dataLim.update_from_data_xy([(-0.1,-0.1), (h + 0.1, w + 0.1)])
        ax.autoscale_view()

        plt.show()
                                    
if __name__ == '__main__':
    """ test all suitable generators """
    width, height = 50, 50
    
    for fn in [AldousBroder, BacktrackingGenerator,
                        CellularAutomaton,
                        DungeonRooms,
                        GrowingTree,
                        HuntAndKill, Kruskal,
                        Prims, Sidewinder,
                        Wilsons]:
        fn_string = str(fn).split('.')[-1][:-2]
        g = SelectableMaze(height, width, fn_string)
        t = time()
        g.generate_maze()
        elapsed = time() - t
        display_grid, dirgrid = g.convert_grid()
        #g.showPNG(g.block_grid)
        #g.showPNG(display_grid)
        g.draw_maze()
        print(fn_string, elapsed)
        #g.plotXKCD(g.block_grid)
       
        path = g.solve_maze()
        #print(path)





