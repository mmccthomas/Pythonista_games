
import random
import traceback
from time import sleep, time
from queue import Queue
import numpy as np
import ui
from scene import ShapeNode
from Letter_game import LetterGame, Player
import sudoko_solve
from cages import Cages

from gui.gui_interface import Gui, Squares
from setup_logging import logger, is_debug_level

""" This game is the Sudoko grid puzzle
both standard and Killer type are supported
You have to guess the number
Chris Thomas June 2024
Added Kropki mode. white circles between adjacent cells
which contain consective numbers. Not all white circles are 
given. Black circles between adjacent cell which are factor of 2
Chris Thomas July 2025
"""
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
NOTE = (-1, -1)
HINT = (-2, -2)
SIZE = 9  # fixed for Sudoko


class Sudoko(LetterGame):
  
  def __init__(self):
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
    # load the gui interface
    self.gui = Gui(self.board, Player())
    self.gui.q = Queue()
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
    
    self.display_squares(color='red')
    x, y, w, h = self.gui.grid.bbox
    W, H = self.gui.get_device_screen_size()                     
    if W > H:
        position = (w+10, 8*h/9)       
    else:
        position = (7*w/9, h+50)
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
    
  def white_dots(self, values, number=10):
    """ place white circles on itersection of consecutive numbers """
    board = [[0] * SIZE for row_num in range(SIZE)]
    [self.board_rc(self.board_dict[k], board, int(v)) for k, v in values.items()]
    board = np.array(board)
    path = ui.Path.oval(0, 0, 15, 15)
    path.line_width = 2
    for axis in range(2):
       diff = np.diff(board, axis=axis)
       diff[diff>1] = 0
       diff[diff<-1] = 0
       diff = np.abs(diff)
       coords = np.argwhere(diff) 
       if axis == 0:
        coords = coords + np.array([0, 0.5])
       else:
         coords = coords + np.array([-0.5, 1])
       np.random.shuffle(coords)
       coords = coords[:number, :]
       points = [self.gui.rc_to_pos(coord) for coord in coords]
       for point in points:
          circle = ShapeNode(
                      path,
                      position=point,
                      z_position=1000,
                      stroke_color='black',
                      fill_color='white',
                      parent=self.gui.game_field)
           
     
  def black_dots(self, values, number=1):
    """ place black circles on itersection of numbers with factor 2 """
    board = [[0] * SIZE for row_num in range(SIZE)]
    [self.board_rc(self.board_dict[k], board, int(v)) for k, v in values.items()]
    board = np.array(board)
    path = ui.Path.oval(0, 0, 15, 15)
    path.line_width = 2
    for axis in range(2):       
       if axis: #x
           ratios = board[:, 1:] / board[:, :-1]
       else:
           ratios = board[1:, :] / board[:-1, :]
       #diff = np.diff(board, axis=axis)
       ratios[ratios == 2] = 1
       ratios[ratios == 0.5] = 1
       ratios[ratios != 1] = 0
       coords = np.argwhere(ratios)
       np.random.shuffle(coords)
       coords = coords[:number, :]
       if axis == 0:
        coords = coords + np.array([0, 0.5])
       else:
         coords = coords + np.array([-0.5, 1])
       points = [self.gui.rc_to_pos(coord) for coord in coords]
       for point in points:
          circle = ShapeNode(
                      path,
                      position=point,
                      z_position=1000,
                      stroke_color='black',
                      fill_color='black',
                      parent=self.gui.game_field) 
    
  def kropki_setup(self, grid):
    """ setup grid for kropki. white circle between some consecutive numbers"""
    kropki_board = np.zeros((SIZE, SIZE), dtype=int)
    self.display(sudoko_solve.grid_values(grid))
    values = sudoko_solve.solve(grid)
    if values:
        self.calc_board(kropki_board, values)
  
    self.white_dots(values, number=9) # up to 18 white dots
    self.black_dots(values, number=2) # up to 4 black dots
    
  def killer_setup(self, grid, random_color=False, kenken=False):
    """ setup grid for killer sudoko """
    self.board = [[SPACE] * SIZE for row_num in range(SIZE)]
    self.gui.update(self.board)
    
    self.gui.build_extra_grid(3, 3, grid_width_x=3, grid_width_y=3, color='white', line_width=2)
    # level controls which cages are used Easy is 2s and 3s
    level = 'Easy' if self.puzzle in [ 'Killer', 'Killer_Harder', 'KenKen'] else  None
    cg = Cages(level)
    killer_board = np.zeros((SIZE, SIZE), dtype=int)
    values = sudoko_solve.solve(grid)
    if values:
        self.calc_board(killer_board, values)
    # fit cages to board
    # might take several goes
    self.start_time = time()
    while True:
      result = cg.check_cage(killer_board, kenken=kenken)
      if result:
        break
        
    # now to assign colours and numbers
    self.cage_board = cg.cage_board_view()
    # store coord and total for later display
    self.totals = {k[0]: v for v, k in cg.cages}
    logger.debug(f'cage board\n {self.cage_board}')
    self.adj_matrix = cg.calc_adj_matrix(self.cage_board)
    color_map_dict = cg.color_4colors(colors=self.cage_colors)
    self.delta_t('calculate cages')
    self.square_list = []
    self.start_time = time()
    # add dotted lines around cages
    if kenken:
        delta=0.49
        linewidth=6
        linedash=[20,1]
    else:
        delta=0.45
        linewidth=2
        linedash=[10,10]
    for index, item in enumerate(cg.cages):
      number_val, coords = item              
      points = cg.dotted_lines(coords, delta=delta)
      points = [self.gui.rc_to_pos(point) for point in points]
      self.gui.draw_line(points, line_width=linewidth, stroke_color='black', 
                            set_line_dash=linedash, z_position=50)
                            
      if random_color is False:
         color = color_map_dict[index]
      else:
          color = self.random_color()
      for  coord in coords:
        text = self.totals[coord] if coord in self.totals else ''
        self.square_list.append(Squares(coord, text, color, z_position=30,
                                        alpha=0.5, font=('Avenir Next', 20),
                                        text_anchor_point=(-0.9, 0.9)))
    self.gui.add_numbers(self.square_list)
    
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
    self.load_words_from_file("sudoko.txt")
    self.create_number_board()
    self.notes = {}
    selected = self.select_list()
    if selected:
        #                             controls decode of puzzle spec
        puzzles = self.process_wordlist(self.puzzle in ['Easy', 'Killer', 'Killer_Harder', 'KenKen'])
        grid = random.choice(puzzles)
        
        if self.puzzle.startswith('Killer'):          
            self.killer_setup(grid, random_color=False)            
            self.board = [[SPACE for i in range(SIZE)] for j in range(SIZE)]
        elif self.puzzle == 'KenKen':
            self.killer_setup(grid, random_color=False, kenken=True)            
            self.board = [[SPACE for i in range(SIZE)] for j in range(SIZE)]
        elif self.puzzle == 'Kropki':
            self.kropki_setup(grid)            
        else:
            self.display(sudoko_solve.grid_values(grid))
        values = sudoko_solve.solve(grid)
        if values:
          self.calc_board(self.solution_board, values)
    else:
        self.gui.set_message2('No level selected')
        sleep(1)
        self.restart() 
          
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
    self.complete()
    
  ######################################################################
  
  def select_list(self):
      '''Choose which category'''
      items = [s.capitalize() for s in self.word_dict.keys()] + ['Killer', 'Killer_Harder', 'KenKen', 'Kropki']
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
          if selection in [ 'Killer', 'Killer_Harder', 'KenKen']:
             self.wordlist = self.word_dict['Easy']
          elif selection == 'Kropki':
             self.wordlist = self.word_dict['Hard']
          else:
             self.wordlist = self.word_dict[selection]
          self.puzzle = selection
          self.gui.selection = ''
          return True
        else:
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
     logger.debug(f'removed note {coord}, {known_value}, {self.notes}')
     
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
      logger.debug(f'received move {move}')
      r, c = coord
      if not isinstance(letter, list):
          if coord == (None, None):
            return False
          elif letter == 'Finish':
            return True
            
          elif letter != '':
            # if Killer mode, need to always display totals
            logger.debug(f'processing {letter}, {coord}')
            if self.get_board_rc(coord, self.board) != BLOCK:
              self.board_rc(coord, self.board, letter)
              self.gui.update(self.board)
              
              # test if correct
              if self.get_board_rc(coord, self.board) != self.get_board_rc(coord, self.solution_board):
                logger.debug(f'testing {letter}, {coord}')
                # make square flash yellow
                temp = self.gui.get_numbers(coord)
                data = temp[coord]
                data_temp = data.copy()
                data_temp['color'] = 'yellow'
                data_temp['alpha'] = 0.7
                self.gui.put_numbers({coord: data_temp})
                sleep(1)
                self.board_rc(coord, self.board, ' ')
                if self.puzzle.startswith('Killer'):
                   # reset
                   self.gui.put_numbers(temp)
                else:
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
                if self.puzzle.startswith('Killer'):
                   data['text'] = str(self.totals[coord]) if coord in self.totals else ''
                else:
                   # clear trial numbers
                   data['text'] = ''
                self.gui.put_numbers({coord: data})
              self.update_notes(coord)
              self.gui.update(self.board)
              return False
            else:
              return False
              
      else:  # we've  got a list
        # add notes to square
        self.notes[coord] = letter
        logger.debug(f'add note  {coord}, {self.notes}')
        self.add_note(coord, letter)
           
      return True
                  
  def select(self, moves, board, text_list=True):
      W, H = self.gui.get_device_screen_size()
      long_press = self.gui.long_touch
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
            if W > H:
                position = (x+w+50, h / 2)                    
            else:                                 
                position = (x, y)
            
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
              logger.debug(f'letter {selection}, row {selection_row}')
              return rc, selection, selection_row
              
            elif selection == "Cancelled_":
              return (None, None), None, None
              
            elif all([sel in items for sel in selection]):
              self.gui.selection = ''
              logger.debug(f'letters {selection}, rows {selection_row}')
              return rc, selection, selection_row
            else:
              return (None, None), None, None
      
  def reveal(self):
    ''' skip to the end and reveal the board '''
    self.gui.update(self.solution_board)
    # This skips the wait for new location and induces Finished boolean to
    # halt the run loop
    self.gui.q.put(FINISHED)
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
    self.gui.q.put(HINT)
    
  def restart(self):
    self.gui.close()
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
  Sudoko().run()

