""" This game is the classic Number grid puzzle
All the leters have been replaced by a random letter
You have to guess the letter
Chris Thomas May 2024
# Modifications to allow predefined grid filled with numbers
# in this case random crossword creation is not used and a
# solver is called instead
Chris Thomas October 2024
The games uses a 20k word dictionary
#
# if grid has been produced from Ocr.py, there can be errors.
# incorrect blocks, missing numbers, incorrect numbers
# or word not in words_alpha.txt
# To  find and diagnose if solution not possible
# number could be wrong ( particularly 19 fo 9 etc)
# or word not in wordlist
# added code to :
# check for number > 30 and report its location
# report single word not found if solved more than 60%
# to allow word to be added to extra_words.txt
# report single word location to inspect numbers for that word
# removed 2nd solver since it adds nothing more
# and reporting best guess usually allows diagnosis
# TODO could the solver be faster? takes 2.5secs to form word_trie
#  but very fast to search
"""
import random
import dialogs
import numpy as np
import traceback
import string
from itertools import groupby
from time import sleep, time
from queue import Queue
from ui import Image
from scene import Texture
import inspect
from cv_codeword_solver_main.solver_tools import CodewordSolverDFS, WordDictionary
import base_path
base_path.add_paths(__file__)
from Letter_game import LetterGame, Player
from gui.gui_interface import Gui, Squares, Board
from crossword_create import CrossWord
from gui.gui_scene import Tile

#  First item is huge list for solving existing grid,
# and common lists when computing  grid
WordleList = ['wordlists/words_alpha.txt',
              'wordlists/extra_words.txt',
              'wordlists/5000-more-common.txt',
              'wordlists/words_20000.txt']
BLOCK = '#'
SPACE = ' '
BLOCKS = '¥&€█'

  
class CrossNumbers(LetterGame):
  
    def __init__(self, test=None):
        # test overrides manual selections
        self.test = test
        self.debug = False
        self.use_np = False
        self.word_trie = None
        # allows us to get a list of rc locations
        self.log_moves = True
        self.load_words_from_file('crossword_templates.txt')
        self.initialise_board()
        # create game_board and ai_board
        self.SIZE = self.get_size()
         
        # load the gui interface
        self.q = Queue()
        self.gui = Gui(self.board, Player())
        self.gui.gs.q = self.q  # pass queue into gui
        self.gui.set_alpha(False)
        self.gui.set_grid_colors(grid='white', highlight='lightblue')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        
        # menus can be controlled by dictionary of labels and functions without parameters
        self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                                 'New ....': self.restart,
                                 'Reveal': self.reveal,
                                 'Quit': self.quit})
        self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
              
        self.load_words(word_length=None)  # self.sizex)
        self.min_length = 2  # initial min word length
        self.max_length = 15  # initial  maximum word length
        self.max_depth = 1  # search depth for populate
        _, _, w, h = self.gui.grid.bbox
        if self.gui.device.endswith('_landscape'):
           self.gui.set_enter('Hint', position=(w+100, -50))
        else:
          self.gui.set_enter('Hint', position=(w-65, h+30), size=(60, 40))
        self.display = 'tiles'
        self.max_items = 13  # items in key list
      
    def generate_word_number_pairs(self):
        """ create 2 dictionaries
        solution contains complete number, letter pairs
        known_dict contains partial known items
        """
        self.letters = [letter for letter in string.ascii_lowercase]
        numbers = list(range(1, 27))
        if not self.filled_board:
            shuffled = random.sample(self.letters, k=len(self.letters))
            self.solution_dict = {number:letter for number, letter in zip(numbers, shuffled)}
            self.solution_dict[' '] = ' '
            self.solution_dict[0] = '.'
            choose_three = random.choices(numbers, k=3)
            self.known_dict = {number: [' ', False] for number in numbers}
            for no in choose_three:
              self.known_dict[no] = [self.solution_dict[no][0], True]
            # fill any empty spaces
            self.board[self.board == '.'] = ' '
            self.board[self.board == SPACE] = BLOCK
        else:
            # solution_dict should start with just known letters
            #self.solution_dict = {number: self.solution_dict.get(number, 'None') for number in numbers}
            # known_dict has boolean showing whether incorrect
            self.known_dict = {number: [' ', False] for number in numbers}
            letter_pos = np.argwhere(np.char.isalpha(self.empty_board))
            for loc in letter_pos:
                no = self.number_board[tuple(loc)]
                letter = self.empty_board[loc[0]][loc[1]]
                self.known_dict[no] = [letter, True]
                
        # now produce solution board and revert board to empty
        # at this point solution board is just numbers
        self.solution_board = self.board.copy()
        self.board = self.empty_board.copy()
       
    def create_number_board(self):
        """
        empty board is array of characters, with # for block
        board derives from this empty board
        number_board is array of numbers, with 0 as block
        unknown numbers are None
        solution board is filled with characters. Some may be empty string"""
        # start with empty board
        if not self.filled_board:
            self.number_board = np.zeros(self.board.shape, dtype=int)
            self.inv_solution_dict = {v[0]: k for k, v in self.solution_dict.items()}
            try:
                # produce the number_board in a numpy vectorised form
                def func(k):
                   return self.inv_solution_dict.get(k, 0)
                vfunc = np.vectorize(func)
                self.number_board = vfunc(self.solution_board)
            except (ValueError):
              print(traceback.format_exc())
      
    def display_numberpairs(self, tiles, off=0, max_items=13):
        """ display players rack
        x position offset is used to select letters or numbers
        """
        parent = self.gui.game_field
        _, _, w, h = self.gui.grid.bbox
        if self.gui.device.endswith('_landscape'):
            if self.sizey < max_items:
              size = self.gui.gs.SQ_SIZE * 13 / max_items
            else:
              size = self.gui.gs.SQ_SIZE
            x, y = 5, 0
            x = x + off*size
            for n, tile in enumerate(tiles):
              t = Tile(Texture(Image.named(f'../gui/tileblocks/{tile}.png')), 0,  0, sq_size=size)
              t.position = (w + x + 3*int(n/max_items)*size , h - (n % max_items + 1)*size + y)
              parent.add_child(t)
        else:
            size = self.gui.gs.SQ_SIZE * 0.9
            x, y = 30, 40
            y = y + off * size
            for n, tile in enumerate(tiles):
              t = Tile(Texture(Image.named(f'../gui/tileblocks/{tile}.png')), 0,  0, sq_size=size)
              t.position = (x + int(n % max_items)*size , h + (2*int(n / max_items) )*size + y)
              parent.add_child(t)
          
    def update_board(self, hint=False, filter_placed=True, tile_color='yellow', first_time=False):
        """ redraws the board with numbered squares and blank tiles for unknowns
        and letters for known
        empty board is array of characters, with # for block
        board derives from this empty board
        number_board is array of numbers, with 0 as block
        unknown numbers are None
        solution board is filled with characters. Some may be empty string"""
        """ requires solution_dict from generate_word_number_pairs
                     solution_board from create_number_board
                     TODO needs to allow for incomplete dictionary
                     solution_dict[no] =[' ', False]
        Hint needs to allow for incomplete dictionary
        """
        nonzero = np.argwhere(self.number_board > 0)
        square_list = [Squares(tuple(loc), self.number_board[tuple(loc)], 'white',
                               z_position=30, alpha=.25,
                               font=('Avenir Next', 15),
                               text_anchor_point=(-1, 1))
                       for loc in nonzero]
        self.gui.add_numbers(square_list, clear_previous=True)
        
        wrong = np.argwhere((self.board != self.solution_board)
                            & (self.board != ' ')
                            & (np.char.isalpha(self.solution_board)))
        if hint:
            # make wrong items orange temporarily
            # cleared when update_board called again
            items = self.gui.get_numbers([tuple(loc) for loc in wrong])
            [v.update(color='orange') for v in items.values()]
            self.gui.put_numbers(items)
    
        else:
            # clear wrong squares
            [self.board_rc(loc, self.board, ' ') for loc in wrong]
            if not first_time:
              for loc in nonzero:
                  # fill other cells of same number. Dont do this initially
                  # to allow initial board to match given puzzle
                  k = self.known_dict[self.number_board[tuple(loc)]][0]
                  self.board_rc(loc, self.board, k)
       
        # display the letters remaining to be placed
        known = [val[0] for val in self.known_dict.values() if val[0] != ' ']
        missing = set(string.ascii_lowercase).difference(set(known))
        missing = sorted([letter.upper() for letter in missing])
        self.gui.set_message2(f'Missing letters {missing}')
                               
        # create text list for known dict
        msg = []
        list_known = list(self.known_dict.items())  # no,letter
        list_known = sorted(list_known, key=lambda x: x[1])
    
        # create a list of letters in correct order
        list_of_known_letters = ['_' for _ in range(len(list_known))]
        for i, v in enumerate(list_known):
            no, l = v
            letter, _ = l
            if isinstance(no, int):
               if letter == ' ':
                 letter = '_'
               list_of_known_letters[no-1] = letter
        
        # now set up text string
        for i, v in enumerate(list_known):
            no, l = v
            letter, _ = l
            letter = letter.upper()
            if no != ' ' and no != '.':
              msg.append(f'{no:>2} = {letter:<2} ')
            if self.gui.device in ['ipad_landscape', 'ipad13_landscape']:
                msg.append('\n' if i % 2 == 0 else ' ' * 2)
            elif self.gui.device == 'ipad_portrait':
                msg.append('\n' if i % 5 == 0 else ' ' * 2)
        msg = ''.join(msg)
        
        # should now have numbers in number board
        
        self.gui.update(self.board)
        # now choose text or tiles
        if self.display == 'tiles':
            self.display_numberpairs(list(range(1, len(list_of_known_letters)+1)), max_items=self.max_items)
            self.display_numberpairs(list_of_known_letters, off=1, max_items=self.max_items)
        else:
            self.gui.set_moves(msg, font=('Avenir Next', 23))
          
    def decode_and_display_filled_board(self):
        """ take a number filled board, display
        format is '#/#/3/4/5b/' etc"""
        def split_text(s):
            for k, g in groupby(s, str.isalpha):
                yield ''.join(g)
                 
        self.board = np.array(self.board)
        self.board[self.board == '-'] = ' '
        # deal with number/alpha combo
        number_letters = np.array([(r, c) for c in range(self.sizex)
                                   for r in range(self.sizey)
                                   if len(list(split_text(self.board[r][c])))>1])
        numbers = np.argwhere(np.char.isnumeric(self.board))
        self.number_board = np.zeros(self.board.shape, dtype=int)
        # add in number_letters if any
        if number_letters.size > 0:
           numbers = np.append(numbers, number_letters, axis=0)
           
        for number in numbers:
            try:
                no, letter = list(split_text(self.board[tuple(number)]))
                self.board[tuple(number)] = letter
            except (ValueError):
                no = self.board[tuple(number)]
            self.number_board[tuple(number)] = int(no)
            # check for invalid number
            if int(no) < 1:
                raise ValueError(f'Number {no} at location rc{number} is invalid (0)')
            if int(no) > 30:
                raise ValueError(f'Number {no} at location rc{number} is invalid (>30)')
                        
        self.board[np.char.isnumeric(self.board)] = ' '
        self.gui.update(self.board)
        return self.board, self.number_board
          
    def copy_known(self, board=None):
        """ fill other copies of known letter """
        if board is None:
          board = self.board
        # now fill the rest of board with these
        for r in range(len(board)):
          for c in range(len(board[0])):
              no = self.number_board[(r, c)]
              letter = self.solution_dict.get(no, None)
              if letter:
                  board[(r, c)] = letter
            
    def decode_filled_board(self):
        """ take a number filled board, and display it"""
        self.decode_and_display_filled_board()
        self.empty_board = self.board.copy()
        self.solution_dict = {}
        # get starting known values
        letter_pos = np.argwhere(np.char.isalpha(self.board))
        for pos in letter_pos:
            letter = self.board[tuple(pos)]
            no = self.number_board[tuple(pos)]
            self.solution_dict[no] = letter
            self.known_dict[no] = [letter, True]
               
        # self.copy_known()
        self.gui.update(self.board)
        return
      
    def finish_population_of_grid(self):
        """complete board population after generating with random words """
        if self.debug:
            print([word.word for word in self.word_locations])
    
        self.solution_board = self.board.copy()
        self.board = self.empty_board.copy()
      
    def create_solve_dict(self):
        """ create dict for solver
        format is {name: {'given_letters': {4: 's', 20: 'r', 23: 'i'},
                    'encoded_words': [list of numbers for each word]}
        """
        
        numbers = [[self.number_board[coord] for coord in word.coords]
                   for word in self.word_locations]
        given_letters = self.solution_dict.copy()
        code_dict = {i: "." for i in range(1, 27)}
        code_dict.update(given_letters)
                
        # Load the list of words and construct the trie
        # print('Building trie word dictionary ...\n')
        if self.word_trie is None:
            if not self.use_np:
    	        try:
    	          import pickle
    	          with open('word_trie.pk', 'rb') as f:
    	            self.word_trie = pickle.load(f)
    	        except Exception as e:
    	           # print('error', e)
    	           self.word_trie = WordDictionary()
    	           # TODO This is quite slow. is re.match on all_word_dict faster?
    	           [self.word_trie.add_word(word) for word in self.all_words]
            else :
            	  self.word_trie = None 
        #with open('word_trie.pkl', 'wb') as f:
        #   pickle.dump(word_trie, f)
        return code_dict, numbers, self.word_trie
        
    def reconstruct_board(self, decoded_words):
        # from solver decoded words reconstruct and print the board
        # words are in same order and same length as self.word_locations
        display_board = self.board.copy()
        for decode, word in zip(decoded_words, self.word_locations):
            for letter, coord in zip(decode, word.coords):
                display_board[coord] = letter
        self.gui.print_board(display_board, 'best try')
        return display_board
                    
        
    def solve(self):
        # solver from  https://github.com/rg1990/cv-codeword-solver
              
        def check_results(word_trie, decoded_words):
            # Check if the solver failed and notify the user
            result = True
            if np.any(["." in word for word in decoded_words]):
                print("Solving failed! Incomplete words remain in decoded_words. Check puzzle details are correct.")
                result = False
            # Catch the case where the words don't have wildcards, but are nonsense words
            # if not np.all([word_trie.search(word) for word in decoded_words]):
            if not np.all([word in self.all_words for word in decoded_words]):
                print(f"One or more decoded words are not valid:\n{decoded_words}")
                #raise RuntimeError(f"One or more decoded words are not valid:\n{decoded_words}")
                result = False
            return result
        t=time()
        code_dict, all_encoded_words, self.word_trie = self.create_solve_dict()
        print(f'time to prepare {time()-t:.2f}s')
        solver = CodewordSolverDFS(all_encoded_words, code_dict,
                                   self.word_trie, self.all_word_dict,  use_heuristics=True, use_np=self.use_np)                          
        solver.debug = self.debug        
        t=time()                
        solver.solve()
        print(f'time to solve {time()-t:.2f}s')
        decoded_words = solver.decode_words_in_list(all_encoded_words)
        result = check_results(self.word_trie, decoded_words)
        if self.debug:
           print(f"Decoded words:\n{decoded_words}")
           solver.print_decoded_letters()
        if result:
            self.solution_dict = solver.code_dict.copy()
            nonzero = np.argwhere(self.number_board > 0)
            [self.board_rc(loc, self.solution_board, self.solution_dict[self.number_board[tuple(loc)]])
             for loc in nonzero]
        else:
            if self.debug:
              print('='*20,'DEBUG', '='*20)
              try:
                  max_percent = max(solver.word_missing_dict)
                  print('possible unknown words', solver.word_missing_dict)
                  if max_percent > 60:
                      word, location = solver.word_missing_dict[max_percent]
                      print(f'Most likely unknown word is {word}')
                      print(f'if best set looks sensible, check unknown word {word}')
                      print(f'or numbers at {self.word_locations[location]}')
                      print('Particularly check for 12, 13,14 instead of 2, 3, 4')
              except ValueError:
                pass
              print('where number is percent of solved words, higher is better')
              print()
              print('best set was', solver.best_wordset)              
              print()              
              self.best_guess = self.reconstruct_board(solver.best_wordset)
              print('='*25)             
        return result
        
    def run(self, test=None):
        """
        Main method that prompts the user for input
        if test is provided, skips user interaction
        """
        def transfer_props(props):
           return {k: getattr(self, k) for k in props}
           
        self.gui.clear_messages()
        self.gui.set_top(f'{self.puzzle}')
        self.print_square(None)
        self.partition_word_list()
        self.compute_intersections()
        #if self.debug:
        #    print(self.word_locations)
        self.generate_word_number_pairs()
        self.create_number_board()
        if self.filled_board:
            self.decode_filled_board()
            
        # self.copy_board(self.empty_board)
        cx = CrossWord(self.gui, self.word_locations, self.all_words)
        cx.set_props(**transfer_props(['board', 'empty_board', 'all_word_dict',
                                       'max_depth', 'debug']))
        if self.filled_board:
           # try cv_codeword_solver first. if it fails try crossword_create solver
           if self.test is None:
               wait = self.gui.set_waiting('Solving')
           success = self.solve()
           self.gui.set_prompt('Decode successful' if success else 'Decode failed')
           if False: # not success:
               try:
                 cx.set_props(**transfer_props(['solution_dict', 'number_board', 'copy_known']))
                 cx.number_words_solve(max_iterations=30,
                                       max_possibles=None)
                 nonzero = np.argwhere(self.number_board > 0)
                 [self.board_rc(loc, self.solution_board, self.solution_dict[self.number_board[tuple(loc)]])
                      for loc in nonzero]
                 self.gui.set_prompt('Solution Complete')     
               except (Exception):
                   print(traceback.format_exc())
                   self.gui.set_prompt('Solution failed, No hints available')
           if self.test is None:
               self.gui.reset_waiting(wait)
        else:
            try:
              if self.test is None:
                  wait = self.gui.set_waiting('Generating')
              self.board = cx.populate_words_graph(max_iterations=200,
                  length_first=False,
                  max_possibles=100,
                  swordsmith_strategy='dfs')
              self.finish_population_of_grid()
            except (Exception):
                print(traceback.format_exc())
            finally:
                if self.test is None:
                    self.gui.reset_waiting(wait)
            
        self.gui.update(self.board)
        # self.print_board()
        self.create_number_board()
        self.update_board(first_time=True)
        x, y, w, h = self.gui.grid.bbox
    
        self.gui.set_message('')
        print(' ')
        print(' ') # to clear console
        self.gui.set_enter('Hint', position=(w, h + 5), fill_color='red')
        if self.test is None:
            while True:
              move = self.get_player_move(self.board)
              finish = self.process_turn(move, self.number_board)
              self.gui.set_prompt('')
              sleep(1)
              if finish:
                break
              if self.game_over():
                break
            
            self.gui.set_message2('Game over')
            self.check_words()
            self.complete()
            
        
                 
    def game_over(self):
        """ check for finished game
        no more empty letters left in board and all known dict items are correct
        also allows for SkelNumbers version"""
        full_squares = ~np.any(self.board == SPACE)
        letters_ok = True
        # need to allow for unused letters
        for v in self.known_dict.values():
          if v[0] != SPACE and not v[1]:
            letters_ok = False
            break
        return full_squares and letters_ok
             
    def load_words(self, word_length, file_list=WordleList):
        # choose only first item in wordslist for filled board (usually words_alpha)
        # or the rest for random puzzle
        if self.filled_board:
          file_list = file_list[0:2]
        else:
          file_list = file_list[1:]
        LetterGame.load_words(self, word_length, file_list=file_list)
    
    def initialise_board(self, non_filled_only=False):
        # detects if board has digits, indicating a prefilled board
        boards = {}
        if self.word_dict:
          # get words and puzzle frame from dict
          for key, v in self.word_dict.items():
            if '_frame' in key:
             board = [row.replace("'", "") for row in v]
             board = [row.split('/') for row in board]
             name = key.split('_')[0]
             boards[name] = board
        if non_filled_only:
          boards = {name: board for name, board in boards.items() if name.startswith('Puzzle')}
        
        if self.test is None:
           self.puzzle = self.select_list(boards)
           if not self.puzzle:
              self.puzzle = random.choice(list(boards))
        else:
            self.puzzle = self.test
            
        self.board = boards[self.puzzle]
        self.sizey, self.sizex = len(self.board), len(self.board[0])
        self.word_locations = []
        self.length_matrix()
        #print(self.board), len(self.board[0]))
        
        # [print(word.coords) for word in self.word_locations]
        if self.debug:
            print('frame ', [len(y) for y in self.board])
            print(len(self.word_locations), 'words', self.min_length, self.max_length)
        self.filled_board = np.any(np.char.isdigit(np.array(self.board, dtype='U3')))
        self.board = np.array(self.board)
        self.empty_board = self.board.copy()
        
      
    def print_square(self, process, color=None):
        """ render the empty grid with black squares """
        blocks = np.argwhere(self.board == BLOCK)
        self.gui.add_numbers([Squares(tuple(block), '', 'black', z_position=30, alpha=.5)
                              for block in blocks],
                             clear_previous=True)
        return
    
    def process_turn(self, move, board):
        """ process the turn
        move is coord, new letter
        """
        if move:
          coord, letter = move
          if move == ((None, None), None):
              return False
          r, c = coord
          if letter == 'Enter':
            # show all incorrect squares
            self.gui.set_prompt('Incorrect squares marked orange')
            self.update_board(hint=True)
            # now turn off marked squares
            sleep(2)
            for k, v in self.known_dict.items():
                if not v[1]:
                    self.known_dict[k] = [' ', False]
            self.update_board(hint=False)
            return False
          elif letter == 'Finish':
              return True
          elif letter != '':
            correct = False
            # check if correct, solution_dict might be incomplete
            no = self.number_board[(r, c)]
            correct_letter = self.solution_dict.get(no, None)
            if correct_letter:
                correct = correct_letter[0] == letter
                
                # this is for SkelNumbers to make all blocks equivalent
                if letter in BLOCKS and correct_letter[0] in BLOCKS:
                  correct = True
            # else:
            #    correct = True
            #    self.solution_dict[no] = letter
            self.known_dict[no] = [letter, correct]
            self.update_board()
                
          return False
    
    def reveal(self):
        ''' skip to the end and reveal the board '''
        self.board = self.solution_board
        self.gui.update(self.board)
        # This skips the wait for new location and induces Finished boolean to
        # halt the run loop
        self.q.put((-10, -10))
          
    def get_player_move(self, board=None):
        """Takes in the user's input and performs that move on the board,
        returns the coordinates of the move
        Allows for movement over board"""
        if board is None:
            board = self.board
        prompt = ("Select  position on board")
        # sit here until piece place on board
        rc = self.wait_for_gui()
        # print('selection position',rc)
        # self.gui.set_prompt(f'selected {rc}')
        if rc == (-1, -1):
          return (None, None), 'Enter'  # pressed enter button
          
        if rc == (-10, -10):
          return (None, None), 'Finish'  # induce a finish
          
        if self.get_board_rc(rc, board) != BLOCK:
          # now got rc as move
          # now open list
          if board is None:
              board = self.board
          possibles = [letter.upper() for letter in self.letters]
          prompt = f"Select from {len(possibles)} items"
          if len(possibles) == 0:
            raise (IndexError, "possible list is empty")
            
          items = list(possibles)
          self.gui.selection = ''
          selection = ''
          while self.gui.selection == '':
            self.gui.input_text_list(prompt=prompt, items=items, position=(800,0))
            while self.gui.text_box.on_screen:
              try:
                selection = self.gui.selection.lower()
              except (Exception) as e:
                print(e)
                print(traceback.format_exc())
                
            if len(selection) == 1:
              self.gui.selection = ''
              # print('letter ', selection)
              return rc, selection
            elif selection == "Cancelled_":
              return (None, None), None
            else:
              return (None, None), None
         
    def restart(self):
        self.gui.gs.close()
        self.finished = False
        g = CrossNumbers()
        g.run()
        while (True):
            quit = g.wait()
            if quit:
              break
  
              
if __name__ == '__main__':
    g = CrossNumbers()  # test='Puzzle1')
    g.run()
      
    while (True):
        quit = g.wait()
        if quit:
          break











