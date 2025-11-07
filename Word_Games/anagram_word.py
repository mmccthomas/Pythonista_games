""" This game is the classic Anagram grid puzzle
All the words have been replaced by an anagram
You have to guess the word
Chris Thomas June 2024

The games uses a 20k word dictionary
"""
import os
import sys
import random
import console
import dialogs
import re
import numpy as np
import traceback
from time import sleep, time
from queue import Queue
from collections import defaultdict
from Letter_game import LetterGame, Player, Word
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
from crossword_create import CrossWord
from  setup_logging import logger, is_debug_level

WordleList = [ 'wordlists/5000-more-common.txt', 'wordlists/words_20000.txt'] 
BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)
file = 'https://gist.githubusercontent.com/eyturner/3d56f6a194f411af9f29df4c9d4a4e6e/raw/63b6dbaf2719392cb2c55eb07a6b1d4e758cc16d/20k.txt'
file = 'https://www.mit.edu/~ecprice/wordlist.10000'
def get_word_file(location, filename):
  r = requests.get(name)
  with open('filename', 'w') as f:
    f.write(r.text)
    
def add(a,b):
  """ helper function to add 2 tuples """
  return tuple(p+q for p, q in zip(a, b))

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
  
def  get_board_rc(rc, board):
  return board[rc[0]][rc[1]]
  
def copy_board(board):
  return list(map(list, board))
  
def lprint(seq, n):
  if len(seq) > 2 * n:
      print(f'{seq[:n]}...........{seq[-n:]}')
  else:
      print(seq)        

class Anagram(LetterGame):
  
  def __init__(self):
    # allows us to get a list of rc locations
    self.log_moves = True
    #self.word_locations = []
    self.load_words_from_file('crossword_templates.txt')
    self.initialise_board() 
    # create game_board and ai_board
    self.SIZE = self.get_size() 
     
    # load the gui interface
    self.gui = Gui(self.board, Player())
    self.gui.Queue()
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='black', highlight='lightblue', z_position=30)
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=False) # SQ_SIZE=45)
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
          
    self.load_words(word_length=self.sizex)    
    self.min_length = 2 # initial min word length
    self.max_length = 15 # initial  maximum word length
    self.max_depth = 1 # search depth for populate         
      
  def generate_word_anagram_pairs(self):
    """ create 2 dictionaries
    solution contains complete number, letter pairs
    known_dict contains partial known items
    """
    anagrams = self.anagrams()
    self.solution_dict = {word: random.choice(anagrams[word]) for word in self.populate_order}
      
    
    self.known_dict={word: ' ' for word in self.populate_order}
    
    
  def create_anagram_board(self):
    """ redraws the board with  blank tiles for unknowns
    and letters for known"""          
    # start with empty board    
    self.anagram_board = copy_board(self.empty_board)
    self.board = [[" " if _char == "." else _char for c, _char in enumerate(row)] for r, row in enumerate(self.board)]
    self.solution_board = copy_board(self.board)
    self.board = copy_board(self.empty_board)
    # fill any unplaced tiles with block
    for r, row in enumerate(self.solution_board):
      for c, _char in enumerate(row):
        if _char == SPACE:
          self.board_rc((r, c), self.board, BLOCK)
    # set all words unplaced
    [word.set_fixed(False) for word in self.word_locations]
    # now choose a random short word to start
    known_word = random.choice([word for word in self.word_locations if word.length < 6])
    known_word.set_fixed(True)
    known_word.update_grid(None, self.board, known_word.word)
    self.update_board()
    
  def get_anagram(self,word):
      """ return anagram of word"""
      try: 
        return self.solution_dict[word]     
      except (KeyError):
        return word
          
  def update_board(self, hint=False, filter_placed=True):
    """ requires solution_dict from generate_word_anagram_pairs
                 solution_board from create_anagram_board 
    """
    LetterGame.update_board(self,hint, filter_placed)   
    
    def key_from_value(dict_, val, pos=0):
      for k, v in dict_.items():
        if v[pos] == val:
          return k
      return None
      
    # create text list       
    msg = []            
    #words=self.all_words
    # if filter_placed list only those words not yet on the board, else those words on the board
    words_placed = [word for word in self.word_locations if  word.fixed]    
    words_unplaced = [word for word in self.word_locations if  not word.fixed]    
    words = []
    for k in range(self.min_length, self.max_length):         
         if filter_placed:
           # sort unplaced words
           w = sorted([word.word for word in words_unplaced if word.length == k])
         else:
           # sort placed words
           w = sorted([word.word for word in words_placed if word.length == k])    
         if w:
           words.append(f'\nLEN={k}\n---------------\n')              
         words.extend([f'{self.get_anagram(word)}\n' if i %3 ==2 else f'{self.get_anagram(word)}  ' for i, word in enumerate(w)])     
    msg = ''.join(words)
    # set message box to be anchored at bottom left
    # TODO whats the right object here?
    x, y, w, h = self.gui.grid.bbox
    if self.gui.device.endswith('_landscape'):        
        position = ( w + 10, 50)
        fontsize = 20
    else:
        position = (40, h )
        fontsize = 15
    self.gui.set_moves(msg, font=('Avenir Next', fontsize), anchor_point=(0,0), position=position)
    # now have numbers in number board   
    #self.gui.add_numbers(square_list)  
    self.gui.update(self.board)         
  
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    def transfer_props(props):
       return  {k: getattr(self, k) for k in props}
    cx = CrossWord(self.gui, self.word_locations, self.all_words)
    self.gui.clear_messages()
    #self.word_locations = []
    #process = self.initialise_board() 
    #self.get_size()
    
    self.print_square(None) 
    self.partition_word_list() 
    self.compute_intersections()
    logger.debug(f'{self.word_locations}')
    cx.debug =  is_debug_level()  
    cx.set_props(**transfer_props(['board', 'empty_board', 'all_word_dict', 
                                   'max_depth']))
    self.board = cx.populate_words_graph(max_iterations=200, length_first=False, max_possibles=100, swordsmith_strategy='dfs')  
    self.populate_order = cx.populate_order
    # self.print_board()
    self.check_words()
    self.generate_word_anagram_pairs()
    self.create_anagram_board()
    self.gui.build_extra_grid(self.gui.DIMENSION_X, self.gui.DIMENSION_Y, grid_width_x=1, grid_width_y=1,color='grey', line_width=1)
    if is_debug_level():
      print(self.anagrams())
      [print(word, count) for word, count in self.word_counter.items() if count > 1]
    self.gui.set_message('')
    while True:
      move = self.get_player_move(self.board)               
      finish = self.process_turn( move, self.anagram_board) 
      sleep(1)
      if finish:
        break
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
    board = solution_board"""
    return self.board == self.solution_board

           
  def load_words(self, word_length, file_list=WordleList):
    LetterGame.load_words(self, word_length, file_list=file_list)
    
  def initialise_board(self):
    boards = {}
    if self.word_dict:
      # get words and puzzle frame from dict
      for key, v in self.word_dict.items():
        if '_frame' in key:
         board = [row.replace("'", "") for row in v]
         #board = [row.replace('"', '') for row in board]
         board =  [row.split('/') for row in board]   
         name  = key.split('_')[0]         
         boards[name]  = board
  
    #if not hasattr(self, 'puzzle'):        
    self.puzzle = random.choice(list(boards)[:5])
    # self.puzzle = 'Puzzle3'
    self.board = boards[self.puzzle]
    self.word_locations = []
    self.length_matrix()                  
    self.empty_board = copy_board(self.board)
    print(len(self.word_locations), 'words', self.min_length, self.max_length) 
    
  def print_square(self, process, color=None):
    """ render the empty grid with black and white squares """
    self.gui.clear_numbers()     
    self.square_list =[]
    for r, row in enumerate(self.board):
      for c, character in enumerate(row):
        if character == BLOCK:
          self.square_list.append(Squares((r, c), '', 'black' , z_position=30, alpha = .5)) 
        else:
          self.square_list.append(Squares((r, c), '', 'white' , z_position=30, alpha = .5))     
    self.gui.add_numbers(self.square_list)   
    return   
  
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter, selection_row
    """ 
    def key_from_value(dict_, val):
      for k, v in dict_.items():
        if v == val:
          return k
      return None
         
    if move:
      coord, letter, row = move
      r,c = coord
      if letter == 'Enter':
        # show all incorrect squares
        self.gui.set_prompt('Incorrect squares marked orange')
        self.update_board(hint=True)
        # now turn off marked squares
        sleep(2)
        self.gui.set_prompt('')
        for r, row in enumerate(self.board):
          for c, char_ in enumerate(row):
            if char_ != BLOCK and char_ != SPACE:
              if char_ != self.solution_board[r][c]:
                self.board_rc((r,c), self.board, self.empty_board[r][c])
        self.update_board(hint=False)
        return False
      elif coord == (None, None):
        return False
      elif letter == 'Finish':
        return True    
      elif letter != '':  # valid selection
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
              w.update_grid(coord, self.board, key_from_value(self.solution_dict,letter.lower()))
              if w.word == key_from_value(self.solution_dict,letter.lower()):
                w.set_fixed(True)
              break
          self.update_board()
          return False 
        else:
          return False     
      return False
  
  def selection_list(self, coord):
      possibles = {}
      words_unplaced = [word for word in self.word_locations if  not word.fixed]    
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
          w = sorted([self.get_anagram(w.word) for w in words_unplaced if w.length == word_length])
          possibles[direction].extend(w)
      self.selection_items = possibles  
      return possibles
      
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    #self.delta_t('start get move')
    self.gui.set_enter('Hint')
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
          logger.debug(f)'letter {selection}, row {selection_row}')
          return rc, selection, selection_row
        elif selection == "Cancelled_":
          return (None, None), None, None
        else:
          return (None, None), None, None     
                 
  def restart(self):
    self.gui.close()
    self.finished = False
    self.__init__()
    self.run() 

if __name__ == '__main__':
  g = Anagram()
  g.run()
  
  while(True):
    quit = g.wait()
    if quit:
      break
  


