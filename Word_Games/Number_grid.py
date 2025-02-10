import os
import sys
import random
import traceback
from time import sleep, time
from queue import Queue
import numpy as np
from Letter_game import LetterGame
import latin_squares
import sudoko_solve
from cages import Cages
import base_path
base_path.add_paths(__file__)
from gui.gui_interface import Gui, Squares


""" This game is a number grid puzzle
You have to guess the numbers
Chris Thomas Feb 2025

"""
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
NOTE = (-1, -1)
HINT = (-2, -2)
SIZE = 9  # fixed for Sudoko

class Player():
  def __init__(self):
    
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  = [str(i) for i in range(26)]
    
    
    self.PIECES = [f'../gui/tileblocks/{k}.png' for k in self.PIECE_NAMES]
    self.PIECE_NAMES.extend(list('+-*/=#'))
    for k in ['add', 'sub', 'mult', 'div', 'eq', '&']:
        self.PIECES.append(f'../gui/tileblocks/{k}.png')
    
    
    self.PLAYERS = None
    
class NumberGrid(LetterGame):
  
  def __init__(self):
    self.debug = False
    self.sleep_time = 0.1
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
    selected = self.resize_grid()
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                             'New ....': self.restart,
                             'Hint': self.perform_hint,
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    
    '''.                 r c.           cols.                rows
    board dict converts from alpha numeric grid location to (r, c)
     '''
    self.board_dict={k: (v,i) for i in range(SIZE) for v, k in enumerate(sudoko_solve.unitlist[i])}
    
    # self.display_squares(color='red')
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
    self.gui.set_enter('Note ', fill_color='clear', font=('Avenir Next', 50),position=position)
    self.gui.set_top('', position=(0, h+30))
       
  def display_squares(self, color=None):
    """ render the empty grid with coloured and white squares """
    self.gui.clear_numbers()
    self.square_list = []
    for r, row in enumerate(self.board):
      for c, character in enumerate(row):
        # every 3 in r and c direction
        color_ = color if  ((r<3 or r>5) and (c<3 or c>5) or (2<r<6 and 2<c<6)) else 'white'
        self.square_list.append(Squares((r, c), '' ,color_, z_position=30, 
                                        alpha=.2, font=('Avenir Next', 20),
                                        text_anchor_point=(-1, 1)))
    self.gui.add_numbers(self.square_list)
   
  def create_number_board(self):
    """ redraws the board with cleared items blank tiles for unknowns
    and letters for known"""
    # start with empty board
    self.solution_board = self.copy_board(self.board)
         
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
    
  def resize_grid(self):
    selected = self.select_list()
    self.N = int(self.puzzle[0])  
    self.gui.gs.DIMENSION_X = self.gui.gs.DIMENSION_Y = 2*self.N +1
    for c in self.gui.game_field.children:
      c.remove_from_parent()
    self.gui.setup_gui(log_moves=False, grid_fill='white')
    return selected
                
  def calc_board(self, board, values):
     [self.board_rc(self.board_dict[k], board, ' ' if v in ['.', '0'] else v) for k, v in values.items()]
     return board
  
  def prepare_board(self):
      items = list(range(1, self.N*self.N + 1))
      # shuffle items
      random.shuffle(items)
      square = np.array(items).reshape(self.N,self.N).astype('U2')
      square, val = latin_squares.operators(self.N, square, add_only=False)
      display = latin_squares.add_result(self.N, square, val)   
      self.board =  latin_squares.create_empty(display)
      self.solution_board = display
      locs = np.argwhere(np.char.isnumeric(self.board))        
      
      self.gui.add_numbers([Squares(loc, self.board[tuple(loc)] ,'black', z_position=30, 
                                        alpha=0, font=('Avenir Next', self.gui.gs.SQ_SIZE/2),
                                        text_anchor_point=(-.7,.6))
                            for loc in locs])           
      for loc in locs:
          self.board[tuple(loc)] = ' '                                        
      self.gui.update(self.board)
  #########################################################################
  # main loop
  def run(self):
    """
    Main method that prompts the user for input
    """
    self.gui.clear_messages()
    self.gui.set_enter('Note', fill_color='clear')
    self.notes = {}
    
    self.prepare_board()     
    self.gui.set_message2('')
    while True:
      self.gui.set_top(f'Sudoko\t\tLevel {self.puzzle}\t\tHints : {self.hints}',
                       font=('Avenir Next', 20))
      move = self.get_player_move(self.board)
      sleep(1)
      moves = self.select(move, self.board, text_list=False)
      self.process_selection(moves)
      
      if self.game_over():
        break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('')
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
  ######################################################################
  
  def select_list(self):
      '''Choose which category'''
      items = ['3x3', '4x4', '5x5']
      self.gui.selection = ''
      selection = ''
      prompt = ' Select category'
      while self.gui.selection == '':
        if self.gui.device.endswith('_portrait'):
            x, y, w, h = self.gui.game_field.bbox
            position = (x + w, 40)
        else:
            position = None
        self.gui.input_text_list(prompt=prompt, items=items, position=position)
        
        while self.gui.text_box.on_screen:
          sleep(.2)
          try:
            selection = self.gui.selection
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
   
        if selection == "Cancelled_":
          return False
        elif len(selection) > 1:
          
          self.puzzle = selection
          self.gui.selection = ''
          return True
        else:
            return False
                
  def game_over(self):
    """ check for finished game
    board matches solution"""
    return np.all(self.board[:2*self.N, :2*self.N] == self.solution_board[:2*self.N, :2*self.N])
 
  def update_notes(self, coord):
     """ update any related notes using known validated number"""
     # remove note from validated cell
     self.notes.pop(coord, None)
     known_value = str(self.get_board_rc(coord, self.board))
     
     r, c = coord
     # look along row
     for col in range(SIZE):
       try:
         self.notes[(r, col)].remove(known_value)
       except (KeyError, ValueError):
         pass
     # look along col
     for row in range(SIZE):
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
              self.gui.update(self.board)
              
              # test if correct
              if self.get_board_rc(coord, self.board) != self.get_board_rc(coord, self.solution_board):
                if self.debug:
                   print('testing', letter, coord)
                # make square flash yellow
                #temp = self.gui.get_numbers(coord)
                #tdata = temp[coord]
                #data_temp = data.copy()
                #data_temp['color'] = 'yellow'
                #data_temp['alpha'] = 0.7
                #self.gui.put_numbers({coord: data_temp})
                sleep(1)
                self.board_rc(coord, self.board, ' ')
                
                # clear note. should clear try value from note also
                try:
                       self.notes[(coord)].remove(letter)
                except (KeyError, ValueError):
                       pass
                #data['text'] = ''
                #self.gui.put_numbers({coord: data})
                   
                self.hints += 1
                
              else:  # correct (or lucky guess!)
                #temp = self.gui.get_numbers(coord)
                #data = temp[coord]
                #if self.puzzle.startswith('Killer'):
                #   data['text'] = str(self.totals[coord]) if coord in self.totals else ''
                # else:
                   # clear trial numbers
                #    data['text'] = ''
                #self.gui.put_numbers({coord: data})
                pass
              self.update_notes(coord)
              self.gui.update(self.board)
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
          possibles = list(sudoko_solve.digits)  # 1 thru 9
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
            panel_choice = {3: 'Number_panel.pyui', 4: 'Number_panel16.pyui', 5: 'Number_panel25.pyui'}
            panel = select_method(prompt=prompt, items=items, position=position, panel=panel_choice[self.N],
                                      allows_multiple_selection = (long_press or self.hint))             
            while panel.on_screen:
                sleep(.2)
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
    self.gui.update(self.solution_board[:2*self.N, :2*self.N])
    # This skips the wait for new location and induces Finished boolean to
    # halt the run loop
    self.q.put(FINISHED)
    sleep(4)
    self.gui.show_start_menu()
    
  def perform_hint(self):
    """ uncover a random empty square """
    while True:
      coord = (random.randint(0, 2*self.N-1), random.randint(0, 2*self.N-1))
      if self.get_board_rc(coord, self.board) == SPACE:
        break
    self.board[coord] = self.solution_board[coord]
    self.gui.update(self.board)
    letter = self.get_board_rc(coord, self.solution_board)
    self.hint_result = (coord, letter)
    self.hints += 2
    self.q.put(HINT)
    
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    self.__init__()
    self.run()
     
  def display(self, values):
    """Display these values as a 2-D grid.
    A1=(0,0), A2=(0,1), B1=(1,0) etc"""
    [self.board_rc(self.board_dict[k], self.board, ' ' if v in ['.', '0'] else v) for k, v in values.items()]
    self.gui.update(self.board)
    sleep(self.sleep_time)
    
          
if __name__ == '__main__':
  NumberGrid().run()




