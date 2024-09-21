import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from time import sleep
from queue import Queue
from collections import deque
from random import choice, randint
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
greatgrandparent = os.path.dirname(grandparent)
sys.path.append(greatgrandparent)
from gui.gui_interface import Coord, Gui, Squares
from enum import Enum
from time import perf_counter
from  scene import LabelNode, Point

def check_in_board(coord):
    r, c = coord
    return (0 <= r < SIZE) and (0 <= c < SIZE)
    
SIZE = 1
DEBUG = True

class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = ' '
    self.PLAYER_2 = BLACK = '#'
    self.EMPTY = ' '
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    
    self.PIECES = [f'../gui/tileblocks/&.png', f'../gui/tileblocks/_.png', f'../gui/tileblocks/e.png', f'../gui/tileblocks/s.png']
    self.PIECE_NAMES = {'#': 'Black', ' ': 'White', 'e':'End', 's':'Start'}
    
class RandomWalk():
    def __init__(self, size=8):
        """Create, initialize and draw an empty board."""
        self.display_board = np.zeros((size, size), dtype=int)
        self.empty_board = self.display_board.copy()
        self.board = None
        self.q = Queue()
        self.gui = Gui(self.display_board, Player())
        self.gui.gs.q = self.q # pass queue into gui
        self.gui.set_alpha(False) 
        self.gui.set_grid_colors(grid='lightgrey', z_position=5, grid_stroke_color='lightgrey')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        
        self.gui.setup_gui(log_moves=False) #grid_fill='lightgrey')
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save, 
        #                 'Load': load,  'Quit': self.gui.gs.close}
        self.gui.start_menu = {'New Game': self.restart, 'Quit': self.gui.gs.close} 
        self.size =  size # 2
        
    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # Apply marker dots to board
        start = Coord((randint(0, self.size-1), 0))
        xy = start
        dirns = start.nsew_dirs
        XY = []
        t=1
        for _ in range(500):
          dxdy = choice(dirns)  
          if xy + dxdy in XY or not check_in_board(xy+dxdy):
            continue
          xy = xy + dxdy
          XY.append(xy)
          self.display_board[xy] = t
          t += 1
          
        
        self.gui.clear_messages()
        self.square_list =[]
        # place dots
        
        for i in range(0, self.size):
            for j in range(0, self.size):
                if self.display_board[(i,j)]:
                  self.square_list.append(Squares((i, j), self.display_board[(i,j)], 'lightgreen', text_color='white',
                                                z_position=5, stroke_color='clear',alpha =1, 
                                                radius=5, sqsize=15, offset=(0.5, -0.5), 
                                                font = ('Avenir', 15), text_anchor_point=(-.2, 0.5)))     
               
        self.gui.add_numbers(self.square_list )
        
        self.sq = self.gui.gs.SQ_SIZE #2  
        self.boxes = []
        
    def plot(self, board):
        """This method should only be called once, when initializing the board."""
        self.gui.clear_squares()
        self.square_list =[]
        # place dots
        
        for i in range(0, SIZE):
            for j in range(0, SIZE):
                if board[(i,j)]>0:
                  self.square_list.append(Squares((i, j), board[(i,j)], 'black', text_color='white',
                                                z_position=5, stroke_color='clear',alpha =1, 
                                                radius=5, sqsize=15, offset=(0.5, -0.5), 
                                                font = ('Avenir', 15), text_anchor_point=(-.2, 0.5)))     
               
        self.gui.add_numbers(self.square_list )
        
        
            
    def restart(self):
       self.gui.gs.close()
       self.__init__()
       #self.run() 
                    

FONT = ("sans-serif", 18, "normal")
DEBUG = False

""" convert from turtle graphics """

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
    def __init__(self, row, col, cell_size, gui):
        self.cell_size = cell_size
        self.x = col
        self.y = row 
        self.row = row
        self.col = col
        self.permanent = False
        self.track = None
        self.must_connect = ""
        self.is_start = False
        self.is_end = False
        self.gui = gui

    def __str__(self):
        return f"R:{self.row} C:{self.col} {self.content} {self.track}"

    def is_empty(self):
        return self.track is None

    def has_dir(self, dir):
        if self.track:
            return dir in self.track.name

    
    def draw_track(self, erase=False):
        """ Draw the track piece in the cell """
        s = self.gui.gui.gs.SQ_SIZE
        s2 = s / 2
        xy = self.gui.gui.rc_to_pos((self.y + 0.5, self.x + 0.5))
        hor = Point(s2,0)
        ver = Point(0, s2)
        
        if DEBUG and self.must_connect:
            pass
            
        if self.track:
            color = "black" if erase else "white"
            if self.permanent:
                color = "blue"
            params = {"stroke_color": color,"line_width": 10}
            match self.track:
              case Track.NS:
                self.gui.gui.draw_line([xy - hor, xy, xy + hor],  **params)                                                                    
              case Track.EW:
                self.gui.gui.draw_line([xy - ver, xy + ver], **params)                        
              case Track.NE:
                self.gui.gui.draw_line([xy - hor, xy, xy + ver], **params)                
              case Track.SE:
                self.gui.gui.draw_line([xy + hor, xy, xy + ver], **params)                                              
              case Track.NW:
                self.gui.gui.draw_line([xy - hor, xy, xy - ver], **params)                                             
              case Track.SW:
                self.gui.gui.draw_line([xy + hor, xy, xy - ver], **params)                                            
    

class Layout:
    def __init__(self, size=8, gui=None):
        self.size = size
        self.gui = gui

        self.layout = []
        for row in range(size):
            col_list = []
            for col in range(size):
                col_list.append(Cell(row, col, 0, gui))
            self.layout.append(col_list)

        self.start = 0
        self.end = 0
        self.move_count = 0
        self.move_max = 1000000
        self.col_count = []
        self.row_count = []
        self.col_perm = []
        self.row_perm = []

    def draw(self, moves=False):  
        params = {'color':'black', 'text_color':'white',               
                 'z_position':5, 'stroke_color':'clear',
                 'alpha':1, 'radius':5, 
                 'sqsize':1, 'offset':(0.5, -0.5), 
                 'font': ('Avenir', 24), 'text_anchor_point':(-1, 1)}      
        # Numbers across the top
        self.gui.gui.replace_column_labels(self.col_constraints)
        
        # Numbers down right side
        self.gui.gui.replace_column_labels(self.row_constraints)        
        # start and end
        self.gui.gui.clear_squares()
        self.gui.gui.add_numbers([Squares((self.start, 0) , 'A', **params),   
                                  Squares((0, self.end) , 'B', **params)])          

    def coords(self, row, col):
        """ Convert row, column to screen coordinates """
        x = col * self.cell_size + self.cell_size / 2
        y = row * self.cell_size + self.cell_size / 2
        return x, y

    def draw_moves(self, cell):
        """ debug routine to list all possible moves from a cell """
        pass
        #self.turtle.goto(cell.x, cell.y)
        #self.turtle.write(self.moves(cell))

    def set_constraints(self, values):
        """ Takes string of numbers representing top and right side """
        v = list(values)
        self.col_constraints = [int(i) for i in v[: self.size]]
        right = v[self.size :]
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
            if row != 0:
                raise ValueError("Invalid end position")
            self.end = col
            cell.is_end = True

        # determine adjacent cells that must connect
        if "N" in track:
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
        if cell.row == 0 and cell.col == self.end:
            if self.check_constraints(exact=True):
                return True
        return False

    def move_from(self, cell, dir):
        """ move from cell in direction dir  """
        self.move_count += 1
        if self.move_count == self.move_max:
            raise ValueError("Max move count reached")
        # if self.move_count == 8400:
        #     self.draw()
        #     breakpoint()
        if DEBUG:
            cell.draw_track()
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
            if DEBUG:
                cell.draw_track(erase=True)
            cell.track = None

    def solve(self):
        """ Initiate the recursive solver """
        new_cell = self.layout[self.start][0]
        moves = self.moves(new_cell)
        for to_dir in moves:
            self.move_from(new_cell, to_dir)
        raise ValueError("Failed to find solution")

    def result(self, message, elapsed):
        
        self.gui.gui.set_message( f"{message} in {self.move_count} moves. Time:{elapsed:.2f}s")
        


def parse(params, gui):
    """
    Structure: Size:Constraints:track-tuple:track-tuple
    """
    bits = params.split(":")
    size = int(bits[0])
    if len(bits[1]) != 2 * size:
        raise ValueError("Params wrong - 1")
    l = Layout(size, gui)
    l.set_constraints(bits[1])
    for i in range(2, len(bits)):
        c = bits[i]
        start = False
        end = False
        if len(c) == 5:
            if c[4] == "s":
                start = True
            elif c[4] == "e":
                end = True
            else:
                raise ("Params wrong - 2")
        l.add_track(c[:2], int(c[2]), int(c[3]), start=start, end=end)
    return l


def main():
    game_item = "8:2464575286563421:NW60s:SE72:EW24:NS04e"
    game = RandomWalk(int(game_item.split(':')[0]))
    
    board = parse(game_item, game) #904
    # board = parse("8:3456623347853221:NW30s:SW32:SW62:NS04e") #907
    # board = parse("8:8443143523676422:NW00s:NE41:NS45:NS07e") #908
    # board = parse("8:1216564534576221:EW40s:NS03e:NS45") #909
    # board = parse("8:1225446636611544:EW60s:NS03e:EW75:SE26") #910

    # board = parse("8:4533433525853421:SW40s:NE52:NS03e")
    
    #board1 = game.empty_board.copy()
    start = Coord((randint(0, game.size//2), 0))
    end = Coord((SIZE-1, randint(game.size//2, game.size-1)))
  
    board.game = game
    #game.initialize()
    board.draw()
    try:
        start = perf_counter()
        board.solve()
    except ValueError as e:
        end = perf_counter()
        elapsed = end - start
        board.result(str(e), elapsed)


if __name__ == '__main__':
  main()







