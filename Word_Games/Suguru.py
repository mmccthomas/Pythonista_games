
import random
import traceback
from time import sleep, time
from queue import Queue
import numpy as np
from itertools import permutations
from Letter_game import LetterGame, Player
import sudoko_solve
from cages import Cages

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


class Suguru(LetterGame):
  
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
                         
  def check_valid(self, cage, number_set):
      # check if surrounding squares have same number
      # return False if found      
      for index, loc in zip(number_set, cage):     
          r, c = loc
          # max 3x3 array around loc
          subset = self.board[max(r-1,0):min(r+2, self.size), max(c-1, 0):min(c+2, self.size)] 
          if np.any(np.isin(index, subset)):              
              return False
          # if ok, set board[loc] to value
          self.board_rc(loc, self.board, index)
               #neighbours = loc.all_neighbours(self.size, self.size)
               #if any([self.get_board_rc(neighbour, self.board) == index for neighbour in neighbours]):
               #    return False
      return True
                           
  def fill(self, cage_no, animate):
      """ use dfs to iterate through permutations of number set
      """ 
      if animate:
            #utils.clear_terminal()
            self.gui.print_board(self.board, which=str(cage_no))     
            if cage_no < len(self.cage_coords):
                print(self.cage_coords[cage_no])

      # if the grid is filled, succeed if every word is valid and otherwise fail
      if ~np.any(self.board ==0):
            return True
      if cage_no == len(self.cage_coords):
            return False
      cage = self.cage_coords[cage_no]
      numbers = self.permutation_dict[len(cage)] 
      random.shuffle(numbers)
      for number_set in numbers:
          if self.check_valid(cage, number_set):
               if self.fill(cage_no+1, animate):
                  return True
          else:
              # t = np.array(cage)
              # self.board[(t[:,0], t[:,1])] = 0
              [self.board_rc(coord, self.board, 0) for coord in cage]        
      return False
          
  def create_puzzle(self, cages):
       """Create Suguru puzzle
       rules: 
           each cage contains numbers up to its size
           each number may not be adjacent to the same number in any direction           
       
       """
       # self.board = np.zeros((self.size, self.size), dtype=int)
       self.cage_coords = sorted([[Coord((r, c)) for r, c, _ in cage]  for cage in cages], key=len)       
       cage_no = 0
       result = self.fill(cage_no, animate=False)           
       if result:                                        
          self.solution_board = self.board.copy()
          self.gui.print_board(self.solution_board, which='final')
       else:
           raise RuntimeError('no fill possible')
       
  def suguru_setup(self, random_color=False):
    """ setup grid for suguru """
    self.board = np.zeros((self.size,self.size), dtype=int)
    self.gui.remove_labels()
    self.gui.replace_grid(*self.board.shape)
    self.gui.remove_labels()
    self.sizey, self.sizex = self.board.shape
    
    # setup cages creation
    cg = Cages('Full', size=self.size, pent_set=[2,3,4,5,6])
    cg.suguru = True
    self.permutation_dict = {k: list(permutations(list(range(1, k+1)))) for k in range(1,7)}
    
    # fit cages to board
    # might take several goes
    self.start_time = time()
    iteration = 0
    while True:
      try:
          # This performs search and then checks whether any
          # cages are adjacent to one with same number          
          cg.solution, cg.cages = cg.run(display=self.debug)     
          if self.debug:     
             cg.draw_board(cg.solution)
          self.create_puzzle(cg.cages)
          break
      except RuntimeError:
         iteration += 1
         print(f'{cg.iterations}')
         print(f'{iteration=} not solvable')
         continue
  
    self.gui.set_message(f'Solved in {iteration * cg.iterations} iterations in {(time() - self.start_time):.2f} secs')    
    
    # display starting values
    # clear all numbers  bar two
    self.board = self.board.astype('U1')
    INITIAL=3
    self.number_locs = np.argwhere(np.char.isnumeric(self.board))
    number_loc_list = list(self.number_locs)
    random.shuffle(number_loc_list)   
    [self.board_rc(loc, self.board,  ' ') for loc in number_loc_list[INITIAL:]]
    self.gui.update(self.board.astype('U1'))
    
    # now to assign colours and numbers
    self.cage_board = cg.solution
    # store coord and total for later display
    
    if self.debug:
        self.gui.print_board(self.cage_board, which='cage board')
    self.adj_matrix = cg.adj_matrix(self.cage_board)
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
         
  def calc_board(self, board, values):
     [self.board_rc(self.board_dict[k], board, ' ' if v in ['.', '0'] else v) for k, v in values.items()]
     return board
  
  #########################################################################
  # main loop
  def run(self):
    """
    Main method that prompts the user for input
    """
    self.gui.clear_messages()
    self.gui.set_enter('Note', fill_color='clear')    
    self.notes = {}
    selected = self.select_list()
    self.suguru_setup(random_color=False)            
    #self.gui.update(self.solution_board.astype('U1'))     
    self.gui.set_message2('')
    while True:
      self.gui.set_top(f'Sudoko\t\tLevel {self.puzzle}\t\tHints : {self.hints}',
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
  
  def select_list(self):
      '''Choose which category'''
      items = [s.capitalize() for s in ['5x5', '6x6', '7x7', '9x9', '11x11']]
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
          self.size = int(selection.split('x')[0])
            
          self.puzzle = self.size
          self.gui.selection = ''
          return True
        else:
            self.size = 7
            return False
                
  def game_over(self):
    """ check for finished game
    board matches solution"""
    return self.board == self.solution_board  
 
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
      if self.puzzle.startswith('Killer'):
         total = str(self.totals[pos]) if pos in self.totals else ''
         data['text'] = total + '\n' + msg
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
              if self.get_board_rc(coord, self.board) != str(self.get_board_rc(coord, self.solution_board)):
                if self.debug:
                   print('testing', letter, coord)
                # make square flash yellow
                temp = self.gui.get_numbers(coord)
                data = temp[coord]
                data_temp = data.copy()
                data_temp['color'] = 'yellow'
                data_temp['alpha'] = 0.7
                self.gui.put_numbers({coord: data_temp})
                sleep(0.5)
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
                     
            panel = select_method(prompt=prompt, items=items, position=position,
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
    self.gui.update(self.solution_board.astype('U1'))
    # This skips the wait for new location and induces Finished boolean to
    # halt the run loop
    self.q.put(FINISHED)
    sleep(4)
    self.gui.show_start_menu()
    
  def perform_hint(self):
    """ uncover a random empty square """
    while True:
      coord = (random.randint(0, 8), random.randint(0, 8))
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
     
  def display(self, values):
    """Display these values as a 2-D grid.
    A1=(0,0), A2=(0,1), B1=(1,0) etc"""
    [self.board_rc(self.board_dict[k], self.board, ' ' if v in ['.', '0'] else v) for k, v in values.items()]
    self.gui.update(self.board.astype('U1'))
    sleep(self.sleep_time)
    
          
if __name__ == '__main__':
  Suguru().run()
