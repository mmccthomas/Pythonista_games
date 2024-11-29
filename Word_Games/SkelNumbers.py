""" This game is the classic Number grid puzzle
All the leters have been replaced by a random letter
You have to guess the letter
This version requires you to also decide where the blocks are
Chris Thomas Sept 2024

The games uses a 20k word dictionary
"""
import os
import sys
import base_path
base_path.add_paths(__file__)
import random
from time import sleep
import traceback
import numpy as np
from NumberWord import CrossNumbers
import dialogs
from gui.gui_interface import Squares
from crossword_create import CrossWord
BLOCK = '#'
SPACE = ' '
# use other characters to represent blocks
BLOCKS = '¥&€█'

class SkelNumbers(CrossNumbers):
  
  def __init__(self):
    CrossNumbers.__init__(self)
    self.max_items = 15 # items in decode list column
  
  def initialise_board(self):  
  	  # dont allow filled crossword
  	  # only list items beginning with 'Puzzle'
  	  CrossNumbers.initialise_board(self, non_filled_only=True)
  	
  def generate_word_number_pairs(self):
    """ create 2 dictionaries
    solution contains complete number, letter pairs
    known_dict contains partial known items
    add 4 characters to represent group of blocks (used ¥&€ and u'\u2588')
    """
    self.letters = [letter for letter in (BLOCKS + 'abcdefghijklmnopqrstuvwxyz')]
    numbers = list(range(1,31))
    shuffled = random.sample(self.letters, k=len(self.letters))
    self.solution_dict = {number:[letter, True] for number, letter in zip(numbers, shuffled)}
    #self.solution_dict[' '] = [' ', False]
    #self.solution_dict['.'] = ['.', False]
    choose_three = random.choices(numbers, k=3)
    self.known_dict={number: [' ', False] for number in numbers}
    for no in choose_three:
      self.known_dict[no] =[self.solution_dict[no][0], True]
    #self.known_dict[' '] = [' ', False]
    #self.known_dict['.'] = ['.', False]
    self.letters = self.letters[3:]     
    
  def create_number_board(self):
    """ redraws the board with numbered squares and blank tiles for unknowns
    and letters for known"""          
    # start with empty board    
    self.empty_board =np.array(self.empty_board)
    self.board = np.array(self.board) 
    if not hasattr(self, 'solution_board'):
       self.solution_board = self.board.copy()    
    # allow for incomplete board, change space and dot to block
    self.solution_board[self.solution_board == '.'] = BLOCK
    self.solution_board[self.solution_board == SPACE] = BLOCK
    self.board = np.full(self.solution_board.shape, SPACE)
    # find all blocks
    blocks = np.argwhere(self.solution_board==BLOCK).tolist()
    # need to divide blocks into 4 groups
    # each group have some symmetry
    # try to sort into quads, else pairs
    groups = []
    while blocks:
      group = []
      item = blocks.pop(0)
      r,c = tuple(item)
      group.append(item)
      for mirror in [[r, self.sizex - 1 - c], 
                     [self.sizey - 1 - r, c], 
                     [self.sizey - 1 - r, self.sizex - 1 - c]]:
        try:
          # if mirror in blocks, remove it and add to group
          item = blocks.pop(blocks.index(mirror))
          group.append(item)
        except (IndexError, ValueError):
          continue      
      groups.append(group)
      
    for i, group in enumerate(groups):
      for item in group:
       self.solution_board[tuple(item)] = BLOCKS[i % 4]
    CrossNumbers.create_number_board(self) 
    #self.number_board = np.zeros(self.board.shape, dtype=int)
    # letter list for player selection
    #self.letters = [letter for letter in (BLOCKS[-1] + 'abcdefghijklmnopqrstuvwxyz')]    
             
  def restart(self):
        self.gui.gs.close()
        self.finished = False
        g = SkelNumbers()
        g.run() 
        while (True):
            quit = g.wait()
            if quit:
              break
                
if __name__ == '__main__':
  g = SkelNumbers()
  g.run()  
  while(True):
    quit = g.wait()
    if quit:
      break
