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
                                    
        
class SelectableMaze():
  
  def __init__(self, height, width, mazetype=None):
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
        
    self.maze = Maze()
    self.mazetypes = [AldousBroder, BacktrackingGenerator,
                      CellularAutomaton, DungeonRooms,
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
      
      if not (0 <= c + dx < self.width and 0 <= r + dy < self.height):
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
      """ depth first search """
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
      """ This will return a dictionary, path,  child node of starting node
      """
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

     
  def generate_maze(self):
      """ generate a maze and return a block grid and 3d grid """
      self.maze.generate()
      self.maze.generate_entrances(self.start, self.end)
      self.block_grid = self.maze.grid.copy()
      self.grid = self.generate_north_east_map()
      self.generated = True
    
  def generate_north_east_map(self):
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
    
  if __name__ == '__main__':
    """ test all suitable generators """
    width, height = 50, 50
    
    for fn in [AldousBroder, BacktrackingGenerator,
               CellularAutomaton, DungeonRooms,
               GrowingTree, HuntAndKill, Kruskal,
               Prims, Sidewinder, Wilsons]:
        # convert classname into simple string
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
       
        path = g.solve_maze()
        #print(path)






