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
from  collections import Counter
from scene import get_screen_size
from word_square_gen import create_word_search
from Letter_game import LetterGame, Player, Word
import Letter_game as lg
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
BLOCK = '#'
SPACE = ' '
WORDLIST = "wordsearch_list.txt"
GRIDSIZE ='16,16'
HINT = (-1, -1)    
  
class WordSearch(LetterGame):
  
  def __init__(self):
    
    # allows us to get a list of rc locations
    self.log_moves = True
    self.debug = False
    self.straight_lines_only = True
    self.SIZE = self.get_size() 
     
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=True)
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                             'Reveal': self.reveal,
                             'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.run, 
                            'Quit': self.quit})
    self.known_locs = []
    self.word_coords = {}
    
  def print_board(self):
    """
    Display the  players game board, we neve see ai
    """  
    display_words = [word.capitalize() for word in self.wordlist]
    if self.gui.gs.device.endswith('_landscape'):        
        self.gui.set_moves('\n'.join(display_words), font=('Avenir Next', 25))
    elif self.gui.gs.device.endswith('_portrait'):
        msg = []
        for i, word in enumerate(display_words):
          msg.append(f'{word}')
          msg.append('\n' if i % 3 == 0 else ' '*2)    
        msg = ''.join(msg)
        self.gui.set_moves(msg, font=('Avenir Next', 20))
    self.gui.update(self.board)  
    
  def get_size(self):
   return  LetterGame.get_size(self, GRIDSIZE)
  
  def initialise_board(self):        
    [self.board_rc((r,c,), self.board, SPACE) for c in range(self.sizex) for r in range(self.sizey)]
    self.board, words_placed, self.word_coords = create_word_search(self.wordlist, size=self.sizex)       
    self.wordlist = words_placed    
    self.all_words = [word.replace(' ', '') for word in self.wordlist]
    return 
  
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
              
  def match_word(self, move):
    """ match word to move"""      
    word = []
    for rc in move:
      if self.check_in_board(rc) and isinstance(rc, tuple):
        c = self.board[rc[0]][rc[1]]
        word.append(c)
    selected_word = ''.join(word)    
    self.gui.clear_numbers(number_list=move)
    for word in self.wordlist:
      kword = word.replace(' ', '')
      kword = kword.lower()
      if kword == selected_word:       
        self.wordlist.remove(word)
        self.known_locs.extend(move)
        #self.gui.clear_numbers(move)
        color = self.random_color()
        square_list =[Squares(rc, '', color, z_position=30, alpha = .5) for rc in move]
        self.gui.draw_line([self.gui.rc_to_pos(lg.add(move[i], (-.5, .5))) for i in [0, -1]], line_width=8, color='red', alpha=0.5)
        #self.gui.add_numbers(square_list, clear_previous=False) 
        self.print_board()
        #display_words = [word.capitalize() for word in self.wordlist]
        #self.gui.set_moves('\n'.join(display_words), font=('Avenir Next', 25)) 
        break
      else:
        self.gui.clear_numbers(number_list=move)
        
  
  def reveal(self):
      #self.gui.clear_numbers()
      for word, coords in self.word_coords.items():
         if coords:
           color = self.random_color()
           self.print_square(coords, color=color, clear=False, alpha=.5)           
         else:
           print(word)
      sleep(5)
      self.gui.show_start_menu()
          
  def game_over(self):
    """
    Checks if the game is over
    """  
    return  self.wordlist == []
    
  def hint(self):
      """ illuminate the start letter of a random unplaced word """ 
      word = random.choice(self.wordlist)
      word = word.replace(' ', '')
      coords = self.word_coords[word] 
      # note that if start and end letter are same this will fail, but OK
      coord = coords[0] if word[0] == lg.get_board_rc(coords[0], self.board) else coords[-1]  
      self.gui.add_numbers([Squares(coord, '', 'cyan', z_position=30, alpha = .5)], clear_previous=False)
             
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    self.gui.clear_numbers()    
    self.gui.clear_messages()
    self.gui.set_top('Wordsearch')
    self.gui.set_enter('Hint')
    self.word_locations = []
    self.load_words_from_file(WORDLIST)
    self.get_size()
    success = self.select_list()
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
  g = WordSearch()
  g.run()
 
  while(True):
    quit = g.wait()
    if quit:
      break
  