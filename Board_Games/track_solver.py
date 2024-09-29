# classes to implement track solution from constraints
# original code from
# https://github.com/ianastewart/tracks
# modified for ios and removed turtle graphics `CMT

# class to find a random path in a grid
import numpy as np
import os
import sys
from enum import Enum
from time import time
from random import randint, shuffle
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from gui.gui_interface import Coord

DEBUG = False


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
        # difference between actual count of occupied cells and expected count
        self.row_count = []
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
                       print(f"Exact Row {row} failure {count} != {self.row_constraints[row]}")
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
                    print(
                      f"Column {col} failure {count} > {self.col_constraints[col]}")
                return False
        return True

    def not_trapped(self, cell):
        """ Return false if trapped one side of a full row or col
        and need to get to the other side """

        for c in range(1, self.size - 1):
            if self.col_count[c] == 0:
                # ignore cols with a permanent track
                # - if not connected, it may be a path back to other side
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
                # ignore rows with a permanent track
                # - if not connected, it may be a path back to other side
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
        if self.gui.debug:
          self.gui.gui.set_prompt(f'Moves {self.move_count}')
          self.gui.gui.update(self.gui.convert_tracks())
        
        if self.move_count == self.move_max:
            raise ValueError("Max move count reached")
        
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
                # must connect cells are special case not handled
                # in move generation
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
        self.gui.gui.set_message(
          f"{message} in {self.move_count} moves. Time:{elapsed:.2f}s")
        if DEBUG:
            self.gui.gui.set_moves('')


class Graph:
  """This class represents a directed graph
  using adjacency list representation
  """
  def __init__(self, size):
      # No. of vertices
      self.size = size
      self.span = 4
      self.select_min = int((size*size + (2 * size - 1)) / 2)
      self.select_max = self.select_min + self.span
      self.no = 0
      self.found_path = None
      self.t = time()
      self.iter = 0
      board = np.arange(size * size).reshape((size, size))
      # default dictionary to store graph
      self.graph = self.adjacency(board)
      # _, self.board = self.compute_random_path(size)
          
  def compute_random_path(self, n=8):
      # Compute a random path from a source to destination
      # This code is contributed by Neelam Yadav
      nsew_dirs = {(-1, 0): 'N', (0, 1): 'W', (1, 0): 'S', (0, -1): 'E'}
      PIECE = {'NS': '┃', 'EW': '━', 'NW': '┓', 
               'NE': '┏', 'SE': '┗', 'SW': '┛'}
      # construct opposite of keys
      PIECE = PIECE | {k[::-1]: v for k, v in PIECE.items()}
      	      
      board = np.arange(n * n).reshape((n, n))  # numbers 0 to n*n
      char_board = np.full((n, n), '-')
      self.start_loc = (randint(1, n - 3), 0)
      self.end_loc = (n - 1, randint(3, n - 1))
      start = board[self.start_loc]
      end = board[self.end_loc]
      
      path = self.find_path(start, end)
      
      # convert to compass directions, then to display board
      coords = [divmod(rc, n) for rc in path]
      for index, rc in enumerate(coords):
        rc = Coord(rc)
        if index == 0:
          dir_from = 'W'
        else:
          dir_from = nsew_dirs[rc - Coord(coords[index - 1])]
        
        if index == len(coords) - 1:
            dir_to = 'S' if rc.r == 0 else 'N'
        else:
            dir_to = nsew_dirs[rc - Coord(coords[index+1])]
        char_board[rc] = PIECE[dir_from + dir_to]
        
      return coords, char_board
            
  def adjacency(self, board):
      """construct adjacency matrix
      neighbours are shuffled to force random path
      board is a numpy 2d array of ints
      """
      xmax, ymax = board.shape
      adjdict = {}
      for r in range(ymax):
          for c in range(xmax):
              rc = Coord((r, c))
              neighbours = []
              for dir in rc.nsew_dirs:
                  yd, xd = dir
                  if 0 <= (r + yd) < ymax and 0 <= (c + xd) < xmax:
                      neighbours.append(board[r + yd][c + xd])
              shuffle(neighbours)
              adjdict[board[r, c]] = neighbours
      return adjdict
              
  def find_path_util(self, u, d, visited, path):
      '''A recursive function to print all paths from 'u' to 'd'.
      visited[] keeps track of vertices in current path.
      path[] stores actual vertices and path_index is current
      index in path[]'''
      if self.finished:
          return True
      # Mark the current node as visited and store in path
      visited[u] = True
      path.append(u)
      
      # If current vertex is same as destination, then finish
      # if path length is between (selected length, selected length + 4)
      # current path[]
      if u == d:
          p = path[:]
          if self.select_min <= len(p) <= self.select_max:
              self.found_path = p
              return True
            
          self.no += 1  # increment paths counter
            
      else:
          # If current vertex is not destination
          # Recur for all the vertices adjacent to this vertex
          self.iter += 1
          if self.iter % 100 == 0:
              self.gui.set_message(f'Computing random track route {self.iter}')
          for i in self.graph[u]:
              if visited[i] is False:
                self.finished = self.find_path_util(i, d, visited, path)
                if self.finished:
                  return True
                
      # Remove current vertex from path[] and mark it as unvisited
      path.pop()
      visited[u] = False
      return False
        
  def find_path(self, s, d):
      # finds a random path from 's' to 'd'
      # Mark all the vertices as not visited
      visited = [False] * (self.size * self.size)
          
      # Create an array to store paths
      path = []
          
      self.t = time()
      self.finished = False
      # Call the recursive helper function to print all paths
      self.find_path_util(s, d, visited, path)
      print(
        f'paths checked {self.no}, time to find path {time() - self.t:.6f}')
      return self.found_path

