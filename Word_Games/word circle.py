# Wordsearch game - a classic
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
#sys.path.append(f'{parent}/gui')
from queue import Queue
from datetime import datetime
from time import sleep, time
import math
import random
import re
import traceback
import numpy as np
from  collections import Counter
from Letter_game import LetterGame, Player, Word
import Letter_game as lg
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
BLOCK = '#'
SPACE = ' '
WORDLIST = ["words_10000.txt"] #"5000-more-common.txt", "letters3.txt"]
GRIDSIZE ='4,4'
HINT = (-1, -1)    

def rle(inarray):
  """ run length encoding. Partial credit to R rle function. 
  Multi datatype arrays catered for including non Numpy
  returns: tuple (runlengths, startpositions, values) """
  ia = np.asarray(inarray)                # force numpy
  n = len(ia)
  if n == 0: 
    return (None, None, None)
  else:
    y = ia[1:] != ia[:-1]               # pairwise unequal (string safe)
    i = np.append(np.where(y), n - 1)   # must include last element posi
    z = np.diff(np.append(-1, i))       # run lengths
    p = np.cumsum(np.append(0, z))[:-1] # positions
    return(z, p, ia[i])
     
class WordCircle(LetterGame):
  
  def __init__(self):
    LetterGame.__init__(self)
    # allows us to get a list of rc locations
    self.SIZE = self.get_size()
    self.known_locs = []
    self.word_coords = {}
    self.min_length = 3
    self.max_length = 5
    self.load_words(0, file_list=WORDLIST) # creates self.wordset 
    self.partition_word_list()  # creates self.all_word_dict
    self.req_size = 5
    self.known_words = []
    self.word_selection = {}
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'Reveal ....': self.reveal,
                              'Quit': self.quit})
    
    
  def print_board(self):
    """
    Display the  players game board, we neve see ai
    indicate first 5 words of each word length
    """
    self.display_words = [] 
    for length in range(self.min_length, self.max_length + 1):
        self.display_words.extend(self.word_selection[length][:self.req_size])
    # set list to dashes for each letter
    msg_list = [] 
    for word in self.display_words:
      if word in self.known_words:
        msg_list.append(word)
      else:
        msg_list.append('-' * len(word)) 
    # msg_list = ['-' * len(word) for word in self.display_words]
    #display_words = [word.capitalize() for word in self.wordlist]
    if self.gui.gs.device.endswith('_landscape'):        
        self.gui.set_moves('\n'.join(msg_list), font=('Avenir Next', 25))
    elif self.gui.gs.device.endswith('_portrait'):
        msg = []
        for i, word in enumerate(msg_list):
          msg.append(f'{word}')
          msg.append('\n' if i % 3 == 0 else ' '*2)    
        msg = ''.join(msg)
        self.gui.set_moves(msg, font=('Avenir Next', 20))
    self.gui.update(self.board)  
    
  def get_size(self):
   return  LetterGame.get_size(self, GRIDSIZE)
  
  def initialise_board(self):        
    [self.board_rc((r,c,), self.board, SPACE) for c in range(self.sizex) for r in range(self.sizey)]
    found = False
    while not found:
      
      selected_words = {}
      base_word = random.choice(list(self.all_word_dict[self.max_length]))
      print(f'{base_word =}')
      for length in range(self.max_length, self.min_length - 1, -1):
        wordlist = []
        for word in self.all_word_dict[length]:
           if all([letter in base_word for letter in list(word)]) and base_word != word:
               wordlist.append(word)
        print(f'{base_word =}, {wordlist =}')
        if len(wordlist) < self.req_size:
          found = False
          break
        else:
          selected_words[length] = wordlist
          found = True
      #if not found:
      #  continue # choose another base_word
    selected_words[self.max_length].append(base_word)
    letters = list(base_word)   
    # place baseword in grid     
    random.shuffle(letters)  
    for rc in [(0, 1), (0, 3), (1, 0), (2, 3), (3, 1)]:
       self.board_rc(rc, self.board, letters.pop())
    
    self.word_selection = selected_words
    
    
    
  def get_words(self):
    ''' construct subsets of words for each required length
    Use setattr to construct named word sublists '''
    words = self.all_words
    for length in range(self.min_length, self.max_length +1):
      setattr(self, f'words_{length}', {w for w in words if len(w) == length})
      filelist = getattr(self, f'words_{length}')
      print(f'Wordlist length {length} is {len(filelist)}')
  
  def select_list(self):
      '''Choose which category'''
      items = [s.capitalize() for s in self.word_dict.keys()]
      #return selection
      self.gui.selection = ''
      selection = ''
      prompt = ' Select category'
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800,0))
        while self.gui.text_box.on_screen:    
          try:
            selection = self.gui.selection.lower()
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
            
        if len(selection) >1:
          self.wordlist = self.word_dict[selection]
          self.wordlist = [word.lower() for word in self.wordlist]
          self.gui.selection =''
          return True
        elif selection == "Cancelled_":
          return False
        else:
            return False  
             
  def process_turn(self, move, board):
    """ process the turn
    """
    #self.delta_t('start process turn')
    def uniquify(moves):
      """ filters list into unique elements retaining order"""
      return list(dict.fromkeys(moves))      
          
   # try to deal with directions 
    if isinstance(move, list):
        # lets count no of unique coordinates to see how long on each square
        move.pop(-1) # remove terminator
        # need to remove duplicates in sequence run length encoding?
        runlengths, startpositions, values = rle(move)
        #move = uniquify(move)        
        
        try:
            word = ''.join([board[rc[0]][rc[1]] for rc in move if isinstance(rc, tuple)])
            if self.debug:
                print(word)
            word = word.replace(' ', '')
            valid = word in self.all_words
            check = '\t\tValid word' if valid else '\t\tNot valid'
            self.gui.set_message(f'Word= {word} {check}')
            #self.delta_t('end process_turn')
        except(IndexError, AttributeError):
          """ all_words may not exist or clicked outside box"""
          if self.debug:
            print(traceback.format_exc())
        return move        
    else:
      
      
      return move
                  
  def match_word(self, move):
    """ match word to move"""      
    word = []
    for rc in move:
      if self.check_in_board(rc) and isinstance(rc, tuple):
        c = self.board[rc[0]][rc[1]]
        word.append(c)
    selected_word = ''.join(word)  
    selected_word = selected_word.replace(' ', '')  
    self.gui.clear_numbers(number_list=move)
    for word in self.display_words:
      kword = word.replace(' ', '')
      kword = kword.lower()
      if kword == selected_word:       
        self.known_words.append(selected_word)
        #self.gui.clear_numbers(move)
        
        #self.gui.draw_line([self.gui.rc_to_pos(lg.add(move[i], (-.5, .5))) for i in [0, -1]], line_width=8, color='red', alpha=0.5)
        #self.gui.add_numbers(square_list, clear_previous=False) 
        self.print_board()
        #display_words = [word.capitalize() for word in self.wordlist]
        #self.gui.set_moves('\n'.join(display_words), font=('Avenir Next', 25)) 
        break
      else:
        self.gui.clear_numbers(number_list=move)
        
  
  def reveal(self):
      #self.gui.clear_numbers()
      self.known_words = self.display_words
      self.print_board()
      sleep(5)
      self.gui.show_start_menu()
      
  def restart(self):
    """ reinitialise """ 
    self.gui.gs.close()
    self.__init__()
    self.run()
            
  def game_over(self):
    """
    Checks if the game is over
    """  
    return  self.wordlist == []
    
  def hint(self):
      """ illuminate the start letter of a random unplaced word """ 
      pass
             
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    self.gui.clear_numbers()    
    self.gui.clear_messages()
    self.gui.set_top('WordCircle')
    self.gui.set_enter('Hint')
    self.word_locations = []
    #success = self.select_list()
    process = self.initialise_board() 
    self.print_board()
    while True:
      move = self.get_player_move(self.board)  
      if move[0] == HINT:
        self.hint()             
      move = self.process_turn( move, self.board) 
      
      self.print_square(move, clear=False, alpha=0.2)
      sleep(1)
      self.match_word(move)
      # if finish:
      #  break
      if self.game_over():
       break
    
    self.gui.set_message2('Game over')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.show_start_menu()
    

if __name__ == '__main__':
  g = WordCircle()
  g.run()
 
  while(True):
    quit = g.wait()
    if quit:
      break
  
