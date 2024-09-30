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
from time import time


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
 

if __name__ == '__main__':
    gen = WilsonMazeGenerator(200, 150)
    t = time()
    gen.generate_maze()
    print('Maze Generated', time() - t)
    gen.solve_maze()
    print("Solution Generated", time() - t)
    # quest = input("Do you want the solution shown? (Y/N) ")
    gen.show_solution(True)  # quest.strip().lower() == "y")
    print(gen)
    pass



