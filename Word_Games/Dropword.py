""" This game is the classic Number grid puzzle
All the leters have been replaced by a random letter
You have to guess the letter
Chris Thomas May 2024

The games uses a 20k word dictionary
currntly fixed at 13 x 13 size due to needing to create grid manually
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
from time import sleep
import traceback
import numpy as np
from time import sleep, time
from queue import Queue
from collections import defaultdict
from Letter_game import LetterGame, Player, Word
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares, Coord
from crossword_create import CrossWord
from gui.gui_scene import Tile, BoxedLabel
import gui.gui_scene as gs
from ui import Image, Path, LINE_JOIN_ROUND, LINE_JOIN_MITER
from scene import Texture, Point
WordleList = [ '5000-more-common.txt', 'words_20000.txt'] 
BLOCK = '#'
SPACE = ' '
file = 'https://gist.githubusercontent.com/eyturner/3d56f6a194f411af9f29df4c9d4a4e6e/raw/63b6dbaf2719392cb2c55eb07a6b1d4e758cc16d/20k.txt'
file = 'https://www.mit.edu/~ecprice/wordlist.10000'
def get_word_file(location, filename):
  r = requests.get(name)
  with open('filename', 'w') as f:
    f.write(r.text)

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
  
def  get_board_rc(rc, board):
  return board[rc[0]][rc[1]]
  
def copy_board(board):
  return list(map(list, board))
  

class DropWord(LetterGame):
  
  def __init__(self):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = False
    #self.word_locations = []
    self.load_words_from_file('crossword_templates.txt')
    self.initialise_board() 
    # create game_board and ai_board
    self.SIZE = self.get_size() 
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex] 
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    #self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='white', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(grid_fill='black')
    
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
    _, _, w, h = self.gui.grid.bbox 
    if self.gui.device.endswith('_landscape'):
       self.gui.set_enter('Undo', position = (w+100, -50))           
  
  def create_number_board(self):
    """ redraws the board with numbered squares and blank tiles for unknowns
    and letters for known"""          
    # start with empty board    
    self.number_board = copy_board(self.empty_board)
    self.board = [[" " if _char == "." else _char for c, _char in enumerate(row)] for r, row in enumerate(self.board)]
    self.solution_board = copy_board(self.board)
    self.board = np.array(copy_board(self.empty_board))
    for r, row in enumerate(self.solution_board):
      for c, _char in enumerate(row):
        if _char == SPACE:
          self.board_rc((r, c), self.board, BLOCK)
    
  def drop_words(self):
    self.solution = self.board.copy()
    self.gui.update(self.board)
    sleep(3)
    self.board[self.board =='.'] = '#'
    self.gui.print_board(self.board, 'initial board')
    for r in range(self.sizey-1, 1, -1):
      for c in range(self.sizex):
        while True:
          # remove BLOCK at bottom of column until letter
          if self.board[r,c] == BLOCK:            
            above = self.board[:r, c]
            l = above.shape[0]
            self.board[1:l+1,c] = above
            self.board[0,c] = ' '
            self.gui.update(self.board, str(r))
          else:
            break
    # now reset centre column
    self.board[:, self.sizex//2] = self.solution[:, self.sizex//2]
    self.gui.print_board(self.board)
    self.gui.update(self.board)                
  
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    self.create_number_board()
    cx = CrossWord(self.gui, self.word_locations, self.all_words)
    self.gui.clear_messages()
    
    #self.print_square(None) 
    self.partition_word_list() 
    self.compute_intersections()
    if self.debug:
        print(self.word_locations)
    cx.set_props(board=self.board,
                 empty_board=self.empty_board, 
                 all_word_dict=self.all_word_dict, 
                 max_depth=self.max_depth)
    cx.populate_words_graph(max_iterations=200,
                            length_first=False,
                            max_possibles=100)  
    self.drop_words()
    self.check_words()
    self.gui.set_message('')
    
    while True:
      move = self.get_player_move(self.board)               
      finish = self.process_turn( move, self.board) 
      if finish:
        break
      #if self.game_over():
      #  break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
      
  def game_over(self):
    """ check for finished game   
    no more empty letters left in bosrd"""
    test = []
    for r, row in enumerate(self.number_board):
      for c, _char in enumerate(row):
        if isinstance(_char, int):
          test.append(self.board[r][c].isalpha())
    return all(test)
           
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
    self.puzzle = random.choice(list(boards))
    #self.puzzle = 'Puzzle'
    self.board = boards[self.puzzle]
    self.word_locations = []
    self.length_matrix()                  
    self.empty_board = copy_board(self.board)
    print(len(self.word_locations), 'words', self.min_length, self.max_length) 
    
  
  def undo(self):
    self.board = self.lastboard
    self.gui.update(self.board)
    
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter
    """    
    if move:
      coord, letter, row = move
      if move == ((None, None), None, None):
        return False
      r,c = coord
      if letter == 'Enter':
        self.undo()
        return False
        # show all incorrect squares
        self.gui.set_prompt('Incorrect squares marked orange')
        self.update_board(hint=True)
        # now turn off marked squares
        sleep(2)
        for k,v in self.known_dict.items():
          if not v[1]:
            self.known_dict[k] = [' ', False]
        self.update_board(hint=False)
        return False
      elif letter == 'Finish':
        return True    
      elif letter != '':
        # place a black square at location and move all tiles above it one square up
        no = self.board[r][c]
        if no != BLOCK:
          self.lastboard = self.board.copy()
          above = self.board[1:r+1, c]
          l = above.shape[0]
          self.board[:l,c] = above 
          #self.board[0:r-2, c] = self.board[1:r-1, c]
          self.board[r, c] = BLOCK
          self.gui.update(self.board)
          #self.update_board()
          return False 
        else:
          self.lastboard = self.board.copy()
          above = self.board[:r, c]
          l = above.shape[0]
          self.board[1:l+1,c] = above
          self.board[0,c] = ' '
          self.gui.update(self.board)
          #self.update_board()
          return False      
      return True
  
  def reveal(self):
    ''' skip to the end and reveal the board '''
    #self.board = self.solution
    self.gui.update(self.solution)
    #self.update_board()
    # This skips the wait for new location and induces Finished boolean to 
    # halt the run loop
    self.q.put((-10, -10)) 
        
  def get_player_move(self, board=None):
      """Takes in the user's input and performs that move on the board,
      returns the coordinates of the move
      Allows for movement over board"""
      
      move = LetterGame.get_player_move(self, self.board)
      self.gui.set_message(str(move))
      # deal with buttons. each returns the button text  
      if move == (-1, -1):
          return (None, None), 'Enter', None   
      if move == (-10, -10):
          return (None, None), 'Finish', None 
          
      point = self.gui.gs.start_touch - gs.GRID_POS
      # touch on board
      # Coord is a tuple that can support arithmetic
      rc_start = Coord(self.gui.gs.grid_to_rc(point))
      
      if self.check_in_board(rc_start):
          rc = Coord(move)
          return rc, self.get_board_rc(rc, self.board), rc_start
                             
      return (None, None), None, None
       
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    self.__init__()
    self.run() 

if __name__ == '__main__':
  g = DropWord()
  g.run()
  
  while(True):
    quit = g.wait()
    if quit:
      break
  







