""" This game is the zip word grid puzzle
Some letters are prefilled
You have to guess the letter
Chris Thomas May 2024

The games uses a 20k word dictionary
currntly fixed at 25 x 25 size due to needing to create grid manually
attempts to automate grid creation ahve not been succesful so far
"""
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
import random
import console
import dialogs
import re
from collections import defaultdict
import traceback
from time import sleep, time
from queue import Queue
from Letter_game import LetterGame, Player, Word
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
from crossword_create import CrossWord

#WordleList = [ '5000-more-common.txt', 'words_20000.txt'] 
WordList = 'wordpuzzles.txt'
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
file = 'https://gist.githubusercontent.com/eyturner/3d56f6a194f411af9f29df4c9d4a4e6e/raw/63b6dbaf2719392cb2c55eb07a6b1d4e758cc16d/20k.txt'
file = 'https://www.mit.edu/~ecprice/wordlist.10000'          

class ZipWord(LetterGame):
  
  def __init__(self):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = True
    self.word_dict = {}
    self.word_locations = []
    self.load_words_from_file(WordList)
    self.initialise_board() 
    # create game_board and ai_board
    self.SIZE = self.get_size() 
     
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
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
    self.gui.set_start_menu({'New Game': self.run, 'Quit': self.quit})
            
  def create_number_board(self):
    """ redraws the board with cleared items blank tiles for unknowns
    and letters for known"""          
    # start with empty board    
    self.solution_board = self.copy_board(self.board)
    self.board = self.copy_board(self.empty_board)
    self.update_board()
    
    
  def update_board(self, hint=False, filter_placed=None):   
    LetterGame.update_board(self,hint, filter_placed)     
    # create text list    
   
    msg = []
    # TODO this needs some work
    # if filter_placed list only those words not yet on the board, else those words on the board
    words_placed = [word.word for word in self.word_locations if  word.fixed]    
    words = []
    x, y, width, height = self.gui.grid.bbox
    for k, v in self.all_word_dict.items():
      if v:
         words.append(f'\nLEN={k}\n')
         if filter_placed is True:
           # sort unplaced words
           w = sorted([word for word in v if word not in words_placed])
           self.word_display = w
         elif filter_placed is False:
           # sort placed words
           w = sorted([word for word in v if word in words_placed])  
           self.word_display = w
         else: # None
           if hasattr(self, 'word_display'):
               # previous displayed list
               w = self.word_display
           else:
               w =  sorted([word for word in v]) 
         if self.gui.device.endswith('landscape'):        
               words.extend([f'{word}\n' if i %3 ==2 else f'{word}  ' for i, word in enumerate(w)])     
               position = (width + 10, -20)
               fontsize = 20
               anchor =(0, 0)
         else: # self.gui.device == 'ipad_portrait':  
               words.extend([f'{word}\n' if i %10 ==2 else f'{word}  ' for i, word in enumerate(w)])  
               anchor = (0,0)
               position = (40, height+20)
               fontsize = 15
      
    msg = ''.join(words)
    # set message box to be anchored at bottom left
    self.gui.set_moves(msg, font=('Avenir Next',fontsize), anchor_point=anchor,position=position)
    # now have numbers in number board   
    #self.gui.add_numbers(square_list)  
    self.gui.update(self.board)  
  
  def run(self):
    """
    Main method that prompts the user for input
    """
    cx = CrossWord(self.gui, self.word_locations, self.all_words)
    self.gui.clear_messages()
    self.gui.set_message2(f'{self.puzzle}')
    x, y, w, h = self.gui.grid.bbox
    self.gui.set_enter('Hint', position=(w, -75))
    self.partition_word_list()
    self.compute_intersections()
    self.max_depth = 1
    self.start_time = time()
    self.delta_t()
    
    self.start_time = time()
    cx.set_props(board=self.board, empty_board=self.empty_board, 
                 all_word_dict=self.all_word_dict, max_depth=self.max_depth, debug=False)
    cx.populate_words_graph(max_iterations=1000, length_first=False)  
    self.delta_t('time to populate grid') 
    pass
    # self.print_board()
    self.check_words()
    self.create_number_board()
    self.gui.build_extra_grid(self.gui.gs.DIMENSION_X, self.gui.gs.DIMENSION_Y, grid_width_x=1, grid_width_y=1,color='grey', line_width=1)
    while True:
      move = self.get_player_move(self.board)               
      finish = self.process_turn( move, self.board) 
      sleep(1)
      if self.game_over():
        break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
      
  def game_over(self):
    """ check for finished game   
    board matches solution"""
    return self.board == self.solution_board
  
  def initialise_board(self):
    
    word_lists = {}
    if self.word_dict:
      # get words and puzzle frame from dict
      for key, v in self.word_dict.items():
        if '_frame' in key:
         board = [row.replace("'", "") for row in v]
         board =  [row.split('/') for row in board]   
         name  = key.split('_')[0]         
         word_lists[name]  = [self.word_dict[name], board]
         
    self.puzzle = random.choice(list(word_lists))
    #self.puzzle = 'Puzzle11 38'
    self.all_words, self.board = word_lists[self.puzzle]
    self.all_words = [word.lower() for word in self.all_words]
    # parse board to get word objects
    self.length_matrix() 
               
    self.empty_board = self.copy_board(self.board)
    print(len(self.word_locations), 'words', self.min_length, self.max_length)    
       
  
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter, selection_row
    How to mark words as placed need to mark word fixed    
    """    
    if move:
      coord, letter, row = move
      r,c = coord
      if letter == 'Enter':
        # show all incorrect squares
        self.gui.set_prompt('Incorrect squares marked orange')
        self.update_board(hint=True, filter_placed=False)
        # now turn off marked squares
        sleep(2)
        for r, row in enumerate(self.board):
          for c, char_ in enumerate(row):
            if char_ != BLOCK and char_ != SPACE:
              if char_ != self.solution_board[r][c]:
                self.board_rc((r,c), self.board, self.empty_board[r][c])
        self.update_board(hint=False, filter_placed=False)
        return False
      elif coord == (None, None):
        return False
      elif letter == 'Finish':
        return True    
      elif letter != '':
        # select from list whether accross or down based upon selection row.
        # selection items is a directory, dont know which order.
        possibles = self.selection_items
        # get keys to establish down/across 
        directions = list(possibles)
        
        if self.get_board_rc(coord, board) != BLOCK:
          # selected across or down?          
          dirn = directions[0] if row < len(possibles[directions[0]]) else directions[1]
          
          for w in self.word_locations:
            if w.intersects(coord) and w.direction == dirn:
              w.update_grid(coord, self.board, letter)
              break
          if (w == letter):
              w.fixed = False
          #self.known_dict[no] = [letter, correct]
          self.update_board(filter_placed=False)
          return False 
        else:
          return False     
      return True
  
  
    
  def selection_list(self, coord):
      possibles = {}
      
      words_selected = [w for w in self.word_locations if w.intersects(coord)]
      """ if len(words_selected) == 1:
        word_length = words_selected[0].length
        direction = word_pos.direction
        possibles[direction] = sorted([word.word for word in self.word_locations if word.word and word.length == word_length])        
      else:"""
      for word_pos in words_selected:
          word_length = word_pos.length
          direction = word_pos.direction          
          possibles[direction] =[f'\t\t\t{direction.capitalize()}']
          possibles[direction].extend(sorted([word.word for word in self.word_locations if word.word and word.length == word_length]))
      self.selection_items = possibles  
      return possibles
             
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    #self.delta_t('start get move')
    
    if board is None:
        board = self.board
    prompt = (f"Select  position on board")
    # sit here until piece place on board   
    rc = self.wait_for_gui()
    # print('selection position',rc)
    #self.gui.set_prompt(f'selected {rc}')  
    if rc == (-1, -1):
      return (None, None), 'Enter', None # pressed enter button
    if rc == FINISHED:
      return (None, None), 'Finish', None # induce a finish
      
    if self.get_board_rc(rc, board) != BLOCK:
      # now got rc as move
      # now open list
      if board is None:
          board = self.board
      selected_ok = False
      possibles = self.selection_list(rc)
      
      prompt = f"Select from {len(possibles)} items"
      if len(possibles) == 0:
        raise (IndexError, "possible list is empty")
      # flatten dictionary values
      items  = [x for xs in possibles.values() for x in xs]
             
      #return selection
      self.gui.selection = ''
      selection = ''
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800,0))
        while self.gui.text_box.on_screen:    
          try:
            selection = self.gui.selection.lower()
            selection_row = self.gui.selection_row
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
            
        if selection in items:
          self.gui.selection =''
          if self.debug:
              print('letter ', selection, 'row', selection_row)
          return rc, selection, selection_row
        elif selection == "Cancelled_":
          return (None, None), None, None
        else:
          return (None, None), None, None     
       
  def restart(self):
    # TODO this does not always work. Find why
    self.gui.gs.close()
    self.__init__()
    self.run()   
      
if __name__ == '__main__':
  g = ZipWord()
  g.run()
  
  while(True):
    quit = g.wait()
    if quit:
      break
  


