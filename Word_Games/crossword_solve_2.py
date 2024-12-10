# module to zipword style  crossword template
# this involves finding words from a selected dictionary to
# fill a selected template.
# entry point is try_multiple
# some puzzles may be intractable so multiple tries are useful
# failing condition is usually multiple choice on first turn

from time import time
import random
import re
import numpy as np
import inspect
import base_path
base_path.add_paths(__file__)
from Letter_game import LetterGame
BLOCK = '#'
SPACE = ' '

    
class AlternativeSolve(LetterGame):
    """ This class has been used to fill Krossword efficiently
    lets see if it can do zipword
    swordsmith fails on populated zipword puzzles
    """
    
    def __init__(self, gui, board, word_locations, wordlist):
        self.debug = False
        self.gui = gui
        self.word_locations = word_locations
        self.wordlist = wordlist
        self.iteration_counter = 0
        self.placed = 0
        if board:
            self.board = np.array(board)          
            self.SIZE = max(self.board.shape)
            self.update_matches()
    
    def print_board(self, board, which=None):
        # fast printing from numpy array
        print('board:', which)
        print('\n'.join([' '.join(row)for row in np.char.upper(board)]))
          
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
        possible_words = [w for w in self.wordlist
                          if (m.search(w) and len(w) == word.length)]
        for possible in possible_words:
            if possible == word.match_pattern:
                return [(word, possible)]
            possibles.append((word, possible))
        return possibles
      
    def board_is_full(self):
        """test if all word objects have fixed flags set
        """
        all_words = all([word.fixed for word in self.word_locations])
        return all_words
    
    def fewest_matches(self):
        """Finds the slot that has the fewest possible matches,
         this is probably the best next place to look."""
          
        def score(word_obj):
            """produce a score for word solution
            if given list of (Word object, word), it scores
            length of list, length of Word, and number of alphanumerics in
            Word
            """
            length = 100
            if isinstance(word_obj, list):
                length = len(word_obj)
                word_obj = word_obj[0][0]
            elif isinstance(word_obj, tuple):
                word_obj = word_obj[0]
            return (word_obj.length
                    + 10 * sum([c.isalnum() for c in word_obj.match_pattern])
                    + int(1000 * (1 / length))
                    )
            
        all_possibles = [self.find_possibles(word_obj)
                         for word_obj in self.word_locations
                         if not word_obj.fixed]
            
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
            [print(f'{possible[0]}, match {possible[0][0].match_pattern}, len {len(possible)},score {score(possible)}')
             for possible in all_possibles[-5:]]
            print('Selecting', fewest_possibles[0])
           
        return fewest_possibles, fewest_matches
            
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
        # store a copy of the current board
        previous_board = self.board.copy()
            
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
            
    def try_multiple(self, filepath, board, n=5):
        # try to fill up to n times
        self.start_time = time()
        for iteration in range(n):
            self.board = np.array(board)
            self.update_matches()
            if iteration == n - 1:
                self.debug = True
            self.fill()
            print()
            self.print_board(self.board, which=f'final board {filepath},\n\t\t{self.iteration_counter} iterations for {self.placed} words')
            if self.board_is_full():
                break
            else:
                print(f'trying again, {iteration+1} {"="*30}')
                print()
        self.delta_t('elapsed')
        if self.gui:
        	  msg = f'Filled {self.placed}/ {len(self.word_locations)} words in {self.iteration_counter} iterations,  {(time()-self.start_time):.3f}secs'
        	  self.gui.set_message(msg)
        return self.board

                                            
if __name__ == '__main__':
    # try to solve all available puzzles
    obj = AlternativeSolve(None, None, None, None)
    obj.load_words_from_file('wordpuzzles.txt', no_strip=False)
    for filename in obj.word_dict:
        if filename.endswith('_frame'):
            continue
        obj.debug = False
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
     
        obj.try_multiple(filename, board, 10)


