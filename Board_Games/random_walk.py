# https://github.com/ianastewart/tracks
# modified for ios.
# removed turtle graphics `CMT
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

from gui.gui_scene import Tile
from enum import Enum
from time import perf_counter
from  scene import *
from ui import Image
import ui

def check_in_board(coord):
    r, c = coord
    return (0 <= r < SIZE) and (0 <= c < SIZE)
    
SIZE = 1
DEBUG = False
FONT = ("sans-serif", 18, "normal")

class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = ' '
    self.PLAYER_2 = BLACK = '#'
    self.EMPTY = ' '
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    
    self.PIECES = [f'../gui/tileblocks/&.png', f'../gui/tileblocks/_.png', f'../gui/tileblocks/e.png', f'../gui/tileblocks/s.png',
                   f'../gui/tileblocks/┃.png', f'../gui/tileblocks/━.png', f'../gui/tileblocks/┏.png', f'../gui/tileblocks/┓.png',
                   f'../gui/tileblocks/┛.png', f'../gui/tileblocks/┗.png']
    self.PIECE_NAMES = {'#': 'Black', ' ': 'White', 'e':'End', 's':'Start', '┃':'NS',  '━':'EW', '┏':'NE', '┓':'NW', '┛': 'SW',  '┗':'SE'} 
    
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
        self.gui.set_grid_colors(grid='black', z_position=5, grid_stroke_color='black')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        
        self.gui.setup_gui(log_moves=False, grid_fill='white')
        self.gui.build_extra_grid(size, size, grid_width_x=1, grid_width_y=1, color='black', line_width=2, offset=None, z_position=100)
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save, 
        #                 'Load': load,  'Quit': self.gui.gs.close}
        self.gui.start_menu = {'New Game': self.restart, 'Quit': self.gui.gs.close} 
        self.size =  size # 2
        self.display_rack(['┃',  '━', '┏', '┓',  '┛', '┗' ,'x', '?'] )
        self.solution_board = np.full((size, size), '-', dtype='U1')
        self.empty_board = np.full((size, size), '-', dtype='U1')
        
    def update_board(self, board):
      self.gui.update(board)
      self.display_rack(['┃',  '━', '┏', '┓',  '┛', '┗' ,'x', '?'] )
      
      
    def display_rack(self, tiles, y_off=0):
        """ display players rack
        y position offset is used to select player_1 or player_2
        """   
        parent = self.gui.game_field
        _, _, w, h = self.gui.grid.bbox
        sqsize = self.gui.gs.SQ_SIZE
        x, y = (50, h-sqsize)
        y = y + y_off
        rack = {}
        for n, tile in enumerate(tiles):    
          t = Tile(Texture(Image.named(f'../gui/tileblocks/{tile}.png')), 0,  0, sq_size=sqsize)   
          t.position = (w + x + (n %2 *(20+sqsize)) , y -  n//2 * (20+sqsize))
          rack[t.bbox] = tile
          parent.add_child(t)                     
        
        self.rack = rack
        
    def _get_player_move(self, board=None):
      """Takes in the user's input and performs that move on the board, returns the coordinates of the move
      Allows for movement over board"""
      #self.delta_t('start get move')
      if board is None:
          board = self.game_board
      coord_list = []
      prompt = (f"Select  position (A1 - {self.COLUMN_LABELS[-1]}{self.sizey})")
      # sit here until piece place on board   
      items = 0
      
      while items < 1000: # stop lockup
        #self.gui.set_prompt(prompt, font=('Avenir Next', 25))
        
        move = self.wait_for_gui()
        if items == 0: st = time()
        #print('items',items, move)
        try:
          # spot = spot.strip().upper()
          # row = int(spot[1:]) - 1
          # col = self.COLUMN_LABELS.index(spot[0])
          if self.log_moves:
            coord_list.append(move)
            items += 1
            if move == -1:
              #self.delta_t('end get move')
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
        """Takes in the user's input and performs that move on the board, returns the coordinates of the move
        Allows for movement over board"""
        move = self._get_player_move(self.board)
        rack = self.rack
        
        if move[0] == (-1, -1):
           return (None, None), 'Enter', None # pressed enter button
           
        # deal with buttons. each returns the button text    
        elif move[0][0] < 0 and move[0][1] < 0:
          return (None, None), self.gui.gs.buttons[-move[0][0]].text, None
          
        point = self.gui.gs.start_touch - gscene.GRID_POS
        # get letter from rack
        for index, k in enumerate(rack):
            if k.contains_point(point):
                letter = rack[k]
                rc = move[-2]
                return rc, letter, index
        return (None, None), None, None    
              
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
        
    def run(self):    
        """
        Main method that prompts the user for input
        """    
        while True:            
            move = self.get_player_move(self.board)         
            pieces_used = self.process_turn( move, self.board)         
            self.update_board()
            if self.game_over(): break      
          
    def process_turn(self, move, board):
        """ process the turn
        move is coord, new letter, selection_row
        """ 
        rack = self.rack        
        if move:
          coord, letter, row = move
          r,c = coord
          if letter == 'Enter':
            # confirm placement                       
            no_pieces_used = len(self.letters_used)                                                 
          elif coord == (None, None):
            return 0                           
          elif letter != '':  # valid selection
            try:
                r,c = coord
                cell = self.gamestate.board.board[r][c]
                # get point value of selected tile
                point = player.rack.tiles[row].point
                cell.tile = scrabble_objects.Tile(letter.upper(),point=point)                                                 
                self.update_board()
                
            except (IndexError):
              pass             
        return 0   
        
    def game_over(self):
      return False
              
    def restart(self):
       self.gui.gs.close()
       self.__init__()
       #self.run() 


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
        self.y = row
        self.x = col
        self.row = row
        self.col = col
        self.permanent = False
        self.track = None
        self.must_connect = ""
        self.is_start = False
        self.is_end = False
        self.gui = gui

    def __str__(self):
        return f"R:{self.row} C:{self.col} {self.track}"

    def is_empty(self):
        return self.track is None

    def has_dir(self, dir):
        if self.track:
            return dir in self.track.name

    
    def draw_track(self, erase=False):
        """ Draw the track piece in the cell """
        dir_dict = {'NS':'┃',  'EW': '━',  'NE': '┏', 'NW': '┓',  'SW': '┛',  'SE': '┗' }  
        s = self.gui.gui.gs.SQ_SIZE
        s2 = s / 2
        xy = self.gui.gui.rc_to_pos((self.y - 0.5, self.x + 0.5))
        hor = Point(s2,0)
        ver = Point(0, s2)
        
        if DEBUG and self.must_connect:
            pass
            
        if self.track:
            color = "white" if erase else "black"
            self.gui.solution_board[(self.y, self.x)] = '-' if erase else dir_dict[self.track.name]              
            if self.permanent:
                color = "blue"
                self.gui.empty_board[(self.y, self.x)] = dir_dict[self.track.name]
                
            params = {"stroke_color": color,"line_width": 10, 'line_join_style': ui.LINE_JOIN_ROUND, 'alpha':0.5}
            dir_coords_dict = {'NS': [xy - ver, xy, xy + ver],  'EW': [xy - hor, xy + hor],  
                         'NE': [xy - ver, xy, xy + hor],  'NW': [xy - ver, xy, xy - hor],  
                         'SW': [xy - hor, xy, xy + ver],  'SE': [xy + hor, xy, xy + ver]}  
            self.gui.gui.draw_line(dir_coords_dict[self.track.name],  **params)   
            
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
        self.gui.gui.replace_column_labels(self.col_constraints, colors=None)
        
        # Numbers down right side
        self.gui.gui.replace_row_labels(self.row_constraints, colors=None)        
        # start and end
        self.gui.gui.clear_squares()
        self.gui.gui.add_numbers([Squares((self.start, 0) , 'A', **params),   
                                  Squares((self.end_row, self.end) , 'B', **params)])     


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
            #if row != 0:
            #   raise ValueError("Invalid end position")
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
        if cell.row == self.end_row and cell.col == self.end:
            if self.check_constraints(exact=True):
                return True
        return False

    def move_from(self, cell, dir):
        """ move from cell in direction dir  """
        self.move_count += 1
        if DEBUG:
          self.gui.gui.set_moves(f'Moves {self.move_count}')
          self.gui.gui.update(self.gui.display_board)
        if self.move_count == self.move_max:
            raise ValueError("Max move count reached")
        # if self.move_count == 8400:
        #     self.draw()
        #     breakpoint()
        if DEBUG:
            cell.draw_track()
            sleep(0.1)
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
        
    def reveal(self):  
        for r, row_ in enumerate(self.layout):
          for cell in row_:
            cell.draw_track()


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
    #if not start:
    # raise ValueError('start not specified, forgot to add "s"')
    #if not end:
    # raise ValueError('end not specified, forgot to add "e"')
    return l

dirs = {'NS':'┃',  'EW': '━',  'NE': '┏', 'NW': '┓',  'SW': '┛',  'SE': '┗' }  

def main():
    game_item = "8:2464575286563421:NW60s:SE72:EW24:NS04e"
    #game_item = "8:3456623347853221:NW30s:SW32:SW62:NS04e" #907
    #game_item = "8:8443143523676422:NW00s:NE41:NS45:NS07e" #908
    #game_item = "8:1216564534576221:EW40s:NS03e:NS45" #909
    #game_item = "8:1225446636611544:EW60s:NS03e:EW75:SE26e" #910
    #game_item = "8:1556443846643364:EW50s:NE53:SE76:NS02e"
    #game_item = "8:3552325322474243:EW30s:NS17:NS04e"
    #game_item = "8:1452563325211765:EW60s:NS45:SE26:NS02e"
    #game_item = "8:1452563356711252:EW10s:NS35:NE56:NS72e"
    #game_item = "8:3552325334247422:EW40s:NS67:NS74e"
    #game_item = "10:13172648231465163443:EW20s:EW75:SE65:NW77:NS93e"
    #game_item = "10:16351336251542622643:EW70s:EW82:SW25:NE57:NS96e"
    game = RandomWalk(int(game_item.split(':')[0]))
    
    game.gui.clear_messages()
    game.gui.set_top(f'Train Tracks\t\t{game_item}')
    board = parse(game_item, game) #904         

    #game.initialize()
    board.draw()
    try:
        start = perf_counter()
        board.reveal()        
        board.solve()
    except ValueError as e:
        end = perf_counter()
        elapsed = end - start
        board.result(str(e), elapsed)
        game.board = game.empty_board.copy()
        board.reveal()
        game.gui.print_board(game.solution_board)
        game.update_board(game.solution_board)
        game.run()
                        
if __name__ == '__main__':
  main()










