# Maze Generator
#  Wilson's Loop Erased Random Walk Algorithm
# Author: CaptainFlint
# https://artofproblemsolving.com/community/c3090h2221709_wilsons_maze_generator_implementation
"""
Wilson's Algorithm is an algorithm to generate a
uniform spanning tree using a loop erased random walk.
Algorithm:
1. Choose a random cell and add it to the visited list
2. Choose another random cell (Don’t add to visited list).
   This is the current cell.
3. Choose a random cell that is adjacent to the current cell
   (Don’t add to visited list). This is your new current cell.
4. Save the direction that you traveled on the previous cell.
5. If the current cell is not in the visited cells list:
   a. Go to 3
6. Else:
   a. Starting at the cell selected in step 2, follow the arrows
      and remove the edges that are crossed.
   b. Add all cells that are passed into the visited list
7. If all cells have not been visited
   a. Go to 2
Source: http://people.cs.ksu.edu/~ashley78/wiki.ashleycoleman.me/index.php/Wilson's_Algorithm.html
"""
 
import random
import numpy as np
from time import time, sleep
from random import sample, randint, choice, shuffle
import matplotlib.pyplot as plt
import traceback
from queue import Queue
NORTH = 0
EAST = 1     

                                    
class WilsonMazeGenerator:
    """Maze Generator using Wilson's Loop Erased Random Walk Algorithm"""
 
    def __init__(self, height, width):
        """ Creates a maze generator with specified width and height"""
        self.width = 2 * (width // 2) + 1    # Make width odd
        self.height = 2 * (height // 2) + 1  # Make height odd
        self._initialize_grid()
 
        # valid directions in random walk
        self.directions_np = np.array([[0, 1], [1, 0], [0, -1], [-1, 0]])
        # indicates whether a maze is generated
        self.generated = False
 
        # shortest solution
        self.solution = []
        self.showSolution = False
        self.start = (self.height - 1, 0)
        self.end = (0, self.width - 1)
        
    def endpoints(self, start, end):
        self.start = start
        self.end = end
        
    def __str__(self):
        """ outputs a string version of the grid"""
        block = u'\u2588'  # block character
        grid_disp = self.grid_np.copy().astype('U1')
        grid_disp[grid_disp == '0'] = block
        grid_disp[grid_disp == '1'] = ' '
               
        if self.showSolution:
          grid_disp[tuple(np.array(self.solution).T)] = '.'
          
        # produce frame with blocks around each edge and insert grid
        frame = np.full((self.height + 2, self.width + 2), block)
        frame[1:-1, 1:-1] = grid_disp
        frame[self.start] = '1'
        frame[self.end] = '2'
        # produce integer version for export
        # 0=space, 1=block, 2=end, 3=start, 4=solution
        frame_int = frame.copy()
        frame_int[frame_int == ' '] = '0'
        frame_int[frame_int == '1'] = '3'
        frame_int[frame_int == block] = '1'
        frame_int[frame_int == '.'] = '4'
        self.frame = frame_int.astype(int)
        print(self.frame.shape)
        return ''.join([''.join(row) + '\n' for row in frame])
 
    def get_solution(self):
        """
        Returns the solution to the maze as a list
        of tuples"""
        return self.solution
 
    def show_solution(self, show):
        """
        Set whether WilsonMazeGenerator.__str__() outputs the
        solution or not"""
        self.showSolution = show
        
    def generate_north_east(self):
        """ convert frame to nxmx2 grid"""
        self.grid3d = np.full((self.height, self.width, 2), False, dtype=bool)
        index = 0
        for r in range(1, self.height, 2):
          
          row = self.frame[r, :] #north
          blocks = self.frame[r-1, :]
          self.grid3d[index, :, 0] = blocks==1
          index += 1
          
        index = 0      
        for c in range(1, self.width, 2):
          
          col = self.frame[:, c] #east
          blocks = self.frame[:, c+1]
          self.grid3d[:, index, 1] = blocks==1
          index += 1    
        
          
    
    def generate_maze(self):
        """
        Generates the maze according to the Wilson Loop Erased Random
        Walk Algorithm"""
        # reset the grid before generation
        self._initialize_grid()
 
        # choose the first cell to put in the visited list
        # see Step 1 of the algorithm.
        current = self.unvisited.pop(random.randint(0, len(self.unvisited) - 1))
        self.visited.append(current)
        self._cut(current)
 
        # loop until all cells have been visited
        while len(self.unvisited) > 0:
            # choose a random cell to start the walk (Step 2)
            first = self.unvisited[random.randint(0, len(self.unvisited) - 1)]
            current = first
            # loop until the random walk reaches a visited cell
            while True:
                # choose direction to walk (Step 3)
                dirNum = random.randint(0, 3)
                # check if direction is valid. If not, choose new direction
                while not self._is_valid_direction(current, dirNum):
                    dirNum = random.randint(0, 3)
                # save the cell and direction in the path
                self.path[current] = dirNum
                # get the next cell in that direction
                current = self._get_next_cell(current, dirNum, 2)
                if (current in self.visited):  # visited cell is reached (Step 5)
                    break
 
            current = first  # go to start of path
            # loop until the end of path is reached
            while True:
                # add cell to visited and cut into the maze
                self.visited.append(current)
                self.unvisited.remove(current)  # (Step 6.b)
                self._cut(current)
 
                # follow the direction to next cell (Step 6.a)
                dirNum = self.path[current]
                crossed = self._get_next_cell(current, dirNum, 1)
                self._cut(crossed)  # cut crossed edge
 
                current = self._get_next_cell(current, dirNum, 2)
                if (current in self.visited):  # end of path is reached
                    self.path = dict()  # clear the path
                    break
 
        self.generated = True
 
    def solve_maze(self):
        """
        Solves the maze according to the Wilson Loop Erased Random
        Walk Algorithm"""
        # if there is no maze to solve, cut the method
        if not self.generated:
            return None
 
        # initialize with empty path at starting cell
        self.path = dict()
        current = self.start
 
        # loop until the ending cell is reached
        while True:
            while True:
                # choose valid direction
                # must remain in the grid
                # also must not cross a wall
                dirNum = random.randint(0, 3)
                adjacent = self._get_next_cell(current, dirNum, 1)
                if self._is_valid_direction(current, dirNum):
                    hasWall = self.grid_np[adjacent] == 0
                    if not hasWall:
                        break
            # add cell and direction to path
            self.path[current] = dirNum
 
            # get next cell
            current = self._get_next_cell(current, dirNum, 2)
            if current == self.end:
                break  # break if ending cell is reached
 
        # go to start of path
        current = self.start
        self.solution.append(current)
        # loop until end of path is reached
        while not (current == self.end):
            dirNum = self.path[current]  # get direction
            # add adjacent and crossed cells to solution
            crossed = self._get_next_cell(current, dirNum, 1)
            current = self._get_next_cell(current, dirNum, 2)
            self.solution.append(crossed)
            self.solution.append(current)
 
        self.path = dict()
 
    def _get_next_cell(self, cell, dirNum, fact):
        """
        Outputs the next cell when moved a distance fact in the the
        direction specified by dirNum from the initial cell.
        cell: tuple (y,x) representing position of initial cell
        dirNum: int with values 0,1,2,3
        fact: int distance to next cell"""
        dirTup_np = self.directions_np[dirNum]
        next = np.array(cell) + fact * dirTup_np
        return tuple(next)
 
    def _is_valid_direction(self, cell, dirNum):
        """WilsonMazeGenerator(tuple,int) -> boolean
        Checks if the adjacent cell in the direction specified by
        dirNum is within the grid
        cell: tuple (y,x) representing position of initial cell
        dirNum: int with values 0,1,2,3"""
        newCell = self._get_next_cell(cell, dirNum, 2)
        r, c = tuple(newCell)
        return (0 <= c < self.width and 0 <= r < self.height)
 
    def _initialize_grid(self):
        """
        Resets the maze grid to blank before generating a maze."""
        self.grid_np = np.zeros((self.height, self.width), dtype=int)
        # fill up unvisited cells
        self.unvisited = [(r, c) for c in range(0, self.width, 2) for r in range(0, self.height, 2)]
        self.visited = []
        self.path = dict()
        self.generated = False
 
    def _cut(self, cell):
        """
        Sets the value of the grid at the location specified by cell
        to 1
        cell: tuple (y,x) location of where to cut"""
        self.grid_np[cell] = 1
        
class HunterKillerMaze():
  
  def __init__(self, width, height):
    """ initialises maze
    self.grid has format n x m x 2,
    where axis 2 is not North border, not East border 
    """
    self.width = width
    self.height = height
    self.grid = np.zeros((height, width, 2), bool)
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
      t = time()
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
      print('time to generate ', time() -t)
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
              #shuffle(neighbours)
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
        if method == 'dfs':
          fn = self.dfs
        else:
          fn = self.bfs
          
        path = {}
        visited = np.zeros((self.height, self.width), dtype=bool)
        adj = self.adjacency()
        fn(self.start, adj, visited, path, self.end)
        
        index = self.end
        path_list = []
        while index != self.start:
          path_list.append(path[index])
          index = path[index]
        #path_list.append(self.start) 
        return path_list
      
  def convert_grid(self):
    """ convert grid into simple block and space"""
    self.display_grid = np.full((2*self.height+1,2*self.width+1),0, dtype=int)
    self.display_grid[:,0]=1
    self.display_grid[-1,:] = 1       
         
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
           self.display_grid[2*r, 2*c :2*c+2] = 1
         if 'E' in dirgrid[(r, c)]:
           self.display_grid[2 * r : 2*r+2, 2*c +2] = 1    
    return self.display_grid, dirgrid
                        
if __name__ == '__main__':
    gen = WilsonMazeGenerator(10,10)
    t = time()
    gen.generate_maze()
    print('Maze Generated', time() - t)
    gen.solve_maze()
    print("Solution Generated", time() - t)
    # quest = input("Do you want the solution shown? (Y/N) ")
    gen.show_solution(True)  # quest.strip().lower() == "y")
    print(gen)
    # gen.generate_north_east()
    # hunt kill algorithm
    
    h = HunterKillerMaze(10,10)
    h.generate_maze()
    h.draw_maze()

    block = u'\u2588'  # block character
    frame, dirgrid= h.convert_grid()
    frame_int = frame.astype('U1')
    #frame_int[frame_int == '0'] = '0'
    #frame_int[frame_int == '1'] = 
    #frame_int[frame_int == '2'] = '-'
    #print(''.join([''.join(row) + '\n' for row in frame_int]))
    #print(dirgrid)
    path = h.solve_maze()
    print(path)



















