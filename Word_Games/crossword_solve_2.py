# module to fill crossword template
# this involves finding words from a selected dictionary to
# fill a selected template.
# entry point is fill

from time import sleep, time
import traceback
import random
import re
import numpy as np
import traceback
import inspect
from time import time
from  collections import Counter
import matplotlib.colors as mcolors
from collections import defaultdict
from types import SimpleNamespace as sname
import base_path
base_path.add_paths(__file__)
from gui.gui_interface import Coord
from Letter_game import LetterGame
BLOCK = '#'
SPACE = ' '

def lprint(seq, n):
  if len(seq) > 2 * n:
      return f'{seq[:n]}...........{seq[-n:]}'
  else:
      return(seq)
           
  
class AlternativeSolve(LetterGame):
    """ This class has been used to fill Krossword efficiently    
    lets see if it can do zipword
    swordsmith fails on populated zipword puzzles
    """
    
    def __init__(self, gui, board, word_locations, wordlist):
        self.debug = True
        self.gui = gui
        self.word_locations = word_locations 
        self.wordlist = wordlist        
        self.iteration_counter = 0
        self.placed = 0  
        if board:
          self.board = np.array(board)
          
          self.SIZE = max(self.board.shape)
          self.convert_to_start_dict()
          self.update_matches()
    
    def print_board(self, board, which=None):
        print('board:', which)
        for j, row in enumerate(board):
          for i, col in enumerate(row):
            print(board[j][i], end=' ')
          print() 
          
    def set_props(self, **kwargs):
      for k, v in kwargs.items():
        setattr(self, k, v)
                   
    def update_matches(self):
      """update match pattern in word object
      """
      for word_obj in self.word_locations:
          match = [self.board[coord] if self.board[coord].isalnum() else '.' 
                   for coord in word_obj.coords]
          word_obj.match_pattern = ''.join(match) 
 
    def find_possibles(self, word, pos=None):
       """ iterate thru all positions matching to all words"""
       possibles = []  
       m = re.compile(word.match_pattern)
       possible_words = [w for w in self.wordlist if (m.search(w) and len(w) == word.length)]
       for possible in possible_words:
           if possible == word.match_pattern:
               return [(word, possible)]
           possibles.append((word, possible))                   
       return  possibles
      
    def board_is_full(self):
        """test if all word objects have fixed flags set
        """
        all_words = all([word.fixed for word in self.word_locations])

        #print('board is full', all_words)
        return all_words
      
    def fewest_matches(self):
            """Finds the slot that has the fewest possible matches, 
            this is probably the best next place to look."""
            
            def score(word_obj):
                length = 100
                max_length = 100
                if isinstance(word_obj, list):
                   max_length = len(word_obj)
                   length = len(word_obj)
                   word_obj = word_obj[0][0]                     
                elif isinstance(word_obj, tuple):
                   word_obj = word_obj[0]
                return (word_obj.length + 
                        10 * sum([c.isalnum() for c in word_obj.match_pattern]) +
                        int(1000 * (1/ length))
                       )            
            fewest_matches = 100
            fewest_possibles = []
            all_possibles = [self.find_possibles(word_obj)  
                             for word_obj in self.word_locations if not word_obj.fixed]
            
            nil_matches = [word_obj
                           for word_obj, possible in zip(self.word_locations, all_possibles) 
                           if not word_obj.fixed and not possible]
            all_possibles = [possible for possible in all_possibles if possible]
            
            # sort by list length,  number of match letters and word length
            all_possibles.sort(key=score) 
            # catch end case when no possibles left
            if len(all_possibles) == 0:
                return None, 0
            if any(nil_matches):
               if self.debug:         
                   print(f'{nil_matches=}')                
                   word_obj = nil_matches.pop(0) 
                   print(f'No Possibles for {word_obj} {word_obj.match_pattern}')
               return (None, 0)
               
            fewest_possibles = all_possibles[-1]
            fewest_matches = len(fewest_possibles)   
            if self.debug:                
                [print(f'{possible[0]}, {len(possible)=}, match {possible[0][0].match_pattern}, score {score(possible)}') for possible in all_possibles[-5:]]      
                print('Selecting', fewest_possibles[0])      
            
            return fewest_possibles, fewest_matches           
            """
            for word_obj in self.word_locations:
                 if word_obj.fixed:
                     continue  
                 possibles = self.find_possibles(word_obj)
                 
                 if len(possibles) == 0:
                     # if there is a position with no matches, induce a backtrack
                     # to last choice
                     if self.debug:                          
                         print(f'No possibles for {word_obj} {word_obj.match_pattern}')
                     return (None, 0)
                                  
                 # if min length choose it
                 if len(possibles) < fewest_matches:
                        fewest_matches = len(possibles)
                        fewest_possibles = possibles.copy()                        
                        fewest_score = score(word_obj)
                        
                 elif len(possibles) == fewest_matches:
                        # we'd like to choose best choice otherwise'
                        if possibles != fewest_possibles:
                         # score = length + 10 * no matching letters
                         if score(word_obj) > fewest_score:
                            fewest_possibles = possibles.copy() 
                            fewest_score = score(word_obj)       
            """                                               
                  
             
    def place_word(self, possible, previous=False):
          """ fill board
          if previous is True, fill with match """      
          word_obj, word = possible          
         
          if self.debug:
             msg = f'{"Removed" if previous else "Placed"} {word_obj}'
             if self.gui:
                 self.gui.set_message(msg)
                 print(msg)
          if not previous:
              for posn, l in zip(word_obj.coords, word):
                  self.board_rc(posn, self.board, l)
              word_obj.word = word
              word_obj.fixed = True
              try:                              
                  self.wordlist.remove(word)                  
              except (ValueError):
                print(f'{word} not in wordlist')
              self.placed += 1          
          else:
              # board has already reverted
        
              self.wordlist.append(word)
              word_obj.word = ''
              word_obj.fixed = False              
              self.placed -= 1
              
          if self.debug:            
             self.print_board(self.board, f'stack depth= {len(inspect.stack(0))}')     
             if self.gui:   
                 self.gui.update(self.board)
             print('\n\n')
             
          self.update_matches()      
                                   
    def fill(self):
            self.iteration_counter += 1
            
            # if the grid is filled, succeed if every word is valid and otherwise fail
            if self.board_is_full():
                return True
    
            # choose position with fewest matches
            possibles, num_matches = self.fewest_matches()
            
            if num_matches == 0:
              if self.debug:
                print('no matches, backing up')
              return False
            
            # iterate through all possible matches in the fewest-match slot
            #store a copy of the current board
            previous_board = self.board.copy()
            
            if self.debug:
                #print('remaining words', self.wordlist)
                print(possibles)
                
            # randomising choices allows different solve path on each run
            # can solve failures
            random.shuffle(possibles)
            for i, possible in enumerate(possibles):
                if self.debug:
                    print(f'trying no {i} {possible[1]} in choices {[w[1] for w in possibles]}')
                self.place_word(possible)
                # now proceed to next fewest match
                if self.fill():
                    return True
                # back here if match failed
                # if no match works, restore previous word and board
                self.board = previous_board
                self.update_matches()
                
                # cancel the placement
                self.place_word(possible, previous=True)
    
            return False
            
    def try_multiple(self, filepath, tries=5):
     self.start_time=time()
     for iteration in range(tries):   
       if iteration == tries - 2:
          self.debug = True    
       self.fill()
       print()
       self.print_board(self.board, f'final board {filepath},\n\t\t{self.iteration_counter} iterations for {self.placed} words')
       if self.board_is_full():
           break
       else:
           print(f'trying again, {iteration} {"="*50}')            
           print()
     self.delta_t('elapsed')
     return self.board
                      
if __name__ == '__main__':
   #filename_ = 'Puzzle3'
   filename_ = ''
   obj = AlternativeSolve(None, None, None, None)
   obj.debug=False
   obj.load_words_from_file('wordpuzzles.txt', no_strip=False)
   for filename in obj.word_dict:
     if filename.endswith('_frame'):
        continue
     obj.debug=False
     obj.iteration_counter = 0
     obj.placed = 0  
     wordlist = sorted(obj.word_dict[filename], key=len, reverse=True)
     wordlist = [word.replace(' ', '') for word in wordlist]
     obj.wordlist = [word.lower() for word in wordlist]             
     board = obj.word_dict[filename + '_frame']
     board = [row.replace("'", "") for row in board]
     board = [row.split('/') for row in board]     
     
     obj.board = np.array(board)
     obj.SIZE = max(obj.board.shape)
     obj.length_matrix()
     obj.compute_intersections()
     obj.update_matches()
     obj.try_multiple(filename)        


