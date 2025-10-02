import random
import traceback
from time import sleep, time
from queue import Queue
import numpy as np
import console
from Letter_game import LetterGame
import latin_squares
from gui.gui_interface import Gui, Squares

""" This game is a number grid puzzle
You have to guess the numbers
the comparison between some adjacent numbers are given
# A latin square is generated first, then all comparisons are filled
then some or most of the comparisons are randomly removed depending
upon difficulty level
Chris Thomas Feb 2025

"""
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
NOTE = (-1, -1)
HINT = (-2, -2)
SIZE = 5  # fixed
INITIAL = 2 # initial visible numbers


class Player():
    def __init__(self):
      
        self.PLAYER_1 = ' '
        self.PLAYER_2 = '@'
        self.EMPTY = ' '
        self.PIECE_NAMES = [str(i) for i in range(26)]
        self.PIECES = [f'../gui/tileblocks/{k}.png' for k in self.PIECE_NAMES]
        self.PIECE_NAMES.extend(["\u2228", "\u2227", "<", ">"])
        for k in ['down', 'up', 'left', 'right']:
            self.PIECES.append(f'../gui/tileblocks/{k}.png')
        self.PLAYERS = None

        
class Futoshiki(LetterGame):
  
    def __init__(self):
        self.debug = False
        self.N = SIZE
        self.sleep_time = 0.1
        self.hints = 0
        self.inequalities = ["\u2228", "\u2227", "<", ">"]
        # allows us to get a list of rc locations
        self.log_moves = False
        self.straight_lines_only = False
        self.hint = False
        self.hint_result = None
        # create game_board and ai_board
        self.SIZE = self.get_size(f'{SIZE},{SIZE}')
        # load the gui interface
        self.q = Queue()
        self.gui = Gui(self.board, Player())
        self.gui.gs.q = self.q  # pass queue into gui
        self.gui.set_alpha(False)
        self.gui.set_grid_colors(grid='black', highlight='lightblue')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        self.resize_grid()
        self.select_list()
        
        self.gui.build_extra_grid(2*self.N-1, 2*self.N-1,
                                  grid_width_x=1, grid_width_y=1,
                                  color='lightgrey', line_width=2)
        # menus can be controlled by dictionary of labels and functions without parameters
        self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                                 'New ....': self.restart,
                                 'Hint': self.perform_hint,
                                 'Reveal': self.reveal,
                                 'Quit': self.quit})
        self.gui.set_start_menu({'New Game': self.restart,
                                 'Quit': self.quit})
            
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
        self.gui.set_enter('Note ', fill_color='clear',
                           font=('Avenir Next', 50),
                           position=position)
        self.gui.set_top('', position=(0, h+30))
          
    def create_number_board(self):
      """ redraws the board with cleared items blank tiles for unknowns
      and letters for known"""
      # start with empty board
      self.solution_board = self.copy_board(self.board)
      
    def resize_grid(self):
        # selected = self.select_list()
        
        self.gui.gs.DIMENSION_X = self.gui.gs.DIMENSION_Y = 2*self.N -1
        self.gui.gs.column_labels = self.gui.gs.row_labels = None
        for c in self.gui.game_field.children:
          c.remove_from_parent()
        self.gui.setup_gui(log_moves=False, grid_fill='white')
        return 5 # selected            
    
    def prepare_board(self):
        """ create board from random latin square
        compute inequalities for all values
        then remove some of them.
        Difficulty level selects number of inequalties to remain
        """
        # wait = self.gui.set_waiting('Solving')
        
        items = list(range(1, self.N + 1))
        random.shuffle(items)
        rows = np.array(latin_squares.latin_square1(items, True))
        diffsh = np.sign(np.diff(rows, axis=1))
        diffsv = np.sign(np.diff(rows, axis=0))
        # print(is_latin_square(rows))
        # self.gui.reset_waiting(wait)
        # fill board with numbers and logic symbols
        self.board = np.zeros((2*self.N-1, 2*self.N-1), dtype='U1')
        for i, row in enumerate(rows):
            for j, char in enumerate(row):
              self.board[2*i, 2*j] = char
        ineq_list = []
        # add l_r inequalities
        for i, row in enumerate(diffsh):
            for j, char in enumerate(row):
                ineq_list.append((i*2, 2*j+1))
                self.board[i*2, 2*j+1] = '<' if char > 0 else '>'
        # add u_d inequalities
        for i, row in enumerate(diffsv):
            for j, char in enumerate(row):
                ineq_list.append((i*2+1, 2*j))
                self.board[i*2+1, 2*j] = "\u2227" if char>0 else "\u2228"
        #self.board[self.board == ''] = ' '
        self.number_locs = np.argwhere(np.char.isnumeric(self.board))
        number_loc_list = list(self.number_locs)
        random.shuffle(number_loc_list)   
        # remove some inequalities
        random.shuffle(ineq_list)
        # these are number of inequalities to leave
        difficulty = {'Easy': 30, 'Moderate': 10, 'Difficult': 5}
        eq_to_remove = len(ineq_list) - difficulty.get(self.puzzle, 10)
        ineq_list = ineq_list[:eq_to_remove]
        [self.board_rc(loc, self.board, ' ') for loc in ineq_list]
               
        # colour the number squares
        self.gui.add_numbers([Squares(loc, '', 'yellow',
                                      z_position=30, alpha=0.1)
                              for loc in self.number_locs])
    
        self.solution_board = self.board.copy()
        # clear all numbers  bar two
        [self.board_rc(loc, self.board, ' ') for loc in number_loc_list[INITIAL:]]
        
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
            self.gui.set_top(f'Futoshiki\t\tLevel {self.puzzle}\t\tHints : {self.hints}',
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
        items = ['Easy', 'Moderate', 'Difficult']
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
                sleep(.1)
                try:
                    selection = self.gui.selection
                except (Exception) as e:
                    print(e)
                    print(traceback.format_exc())
       
            if selection == "Cancelled_":
                self.puzzle = None
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
        return np.all(self.board == self.solution_board)
   
    def _update_notes(self, coord):
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
           
    def add_note(self, coord, item):
        """ add a note to a cell"""
        font = ('Avenir', 30)
        msg = ''.join([f'{let}\n' if i % 4 == 3 else f'{let}  ' for i, let in enumerate(item)]).strip()
        self.gui.clear_numbers(coord)
        self.gui.add_numbers([Squares(coord, msg, 'white',font=font,
                                      text_anchor_point=(-0.7, 0.6))],
                                      clear_previous=False)
        
    def flash_square(self, coord, color='white'):
        self.gui.clear_numbers(coord)
        self.gui.add_numbers([Squares(coord, '', color)], clear_previous=False)
        sleep(0.5)                         
        self.gui.clear_numbers(coord)
        self.gui.add_numbers([Squares(coord, '', 'yellow', alpha=0.1)], clear_previous=False)
        
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
                  if self.debug:
                    print('processing', letter, coord)
                  if self.get_board_rc(coord, self.board) != BLOCK:
                    self.board_rc(coord, self.board, letter)
                    self.gui.update(self.board)
                    
                    # test if correct
                    if self.get_board_rc(coord, self.board) != self.get_board_rc(coord, self.solution_board):
                      if self.debug:
                         print('testing', letter, coord)
                      self.flash_square(coord, color='yellow')
                      # clear the guess
                      self.board_rc(coord, self.board, ' ')            
                      self.hints += 1
                      
                    else:  # correct (or lucky guess!)
                        self.flash_square(coord, color='green')
                    # self.update_notes(coord)
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
        # process a touch on an empty number square
        if np.array(rc) in self.number_locs and self.get_board_rc(rc, self.board) == SPACE:
            # now got rc as move
            # now open list
            if board is None:
                board = self.board
            possibles = [str(i) for i in range(1, 26)]
            
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
              panel_choice = {3: '../gui/Number_panel.pyui',
                              4: '../gui/Number_panel16.pyui',
                              5: '../gui/Number_panel25.pyui'}
              panel = select_method(prompt=prompt, items=items,
                                    position=position, panel='../gui/Number_panel.pyui',
                                    allows_multiple_selection = (long_press or self.hint))
              while panel.on_screen:
                  sleep(.1)
                  try:
                    selection = self.gui.selection
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
        """ uncover a random empty number square """
        locs = [loc for loc in self.number_locs if self.board[tuple(loc)] == SPACE]
        coord = tuple(random.choice(locs))
        self.board[coord] = self.solution_board[coord]
        self.gui.update(self.board)
        letter = self.get_board_rc(coord, self.solution_board)
        self.hint_result = (coord, letter)
        self.hints += 2
        self.q.put(HINT)
      
    def restart(self):
        print('restarting')
        # self.q.put(FINISHED)
        self.gui.gs.close()
        # self.finished = True
        self.__init__()
        self.run()

          
if __name__ == '__main__':
  Futoshiki().run()

















