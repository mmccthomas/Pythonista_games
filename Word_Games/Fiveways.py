# Fiveways game
# first letter position is given
# choose word from list to fit in a direction
# game is to choose the direction to fill the grid
# This is a variant of KrossWord where ghere are multiple starting letters
import numpy as np
from Krossword import KrossWord
from gui.gui_interface import Squares, Coord
 
 
class FiveWays(KrossWord):
  
  def __init__(self):
    KrossWord.__init__(self)   # same as KrossWord
    self.debug = False
    self.max_iteration = 1000
    self.wordfile = 'fiveways.txt'
    self.strikethru = False 
  
  def initialise_board(self):
    """ initialise board and start_dict
    For Fiveways there are a number of start positions shown
    create start_dict with structure
    {: {words: [wordlist], coords: {Coord: [matches], Coord: [matches], ...}}"""
    
    board = [row.replace("'", "") for row in self.table]
    board = [row.split('/') for row in board]
    self.board = np.array(board)
    self.letter_board = self.board # not used in fiveways  
    # fill start_dict
    start_positions = np.argwhere(np.char.isalpha(self.board))
    self.start_dict = {}
    for pos in start_positions:
         letter = self.board[tuple(pos)]
         if letter in self.start_dict:
            # add new coordinate for letter
            self.start_dict[letter]['coords'][Coord(tuple(pos))] = ['' for _ in range(len(self.valid_dirns))]
         else:
            #start new letter
            self.start_dict[letter] = {'words': [], 'coords': {Coord(tuple(pos)): ['' for _ in range(len(self.valid_dirns))]}}
         
    # add coloured squares                  
    self.gui.add_numbers([Squares(Coord(tuple(pos)), '', 'yellow', z_position=30,
                                  alpha=0.5, font=('Avenir Next', 18),
                                  text_anchor_point=(-1.1, 1.2)) 
                          for pos in start_positions])
                          
    self.gui.update(self.board)   
    self.wordlist = self.create_wordlist_dictionary()
    self.all_words = [word for words in self.wordlist.values() for word in words]

    for word in self.all_words:
      self.start_dict[word[0]]['words'].append(word)
    # sort alphabetically    - was longest to shortest
    self.wordlist[None]  = sorted(self.wordlist[None]) #,key=len, reverse=True)
    self.update_matches() 
    
  def process_turn(self, move, board, test=None):
     KrossWord.process_turn(self, move, board, test=None)     
     # change the colour of a correct start letter to green 
     move = self.predict_direction(move)
     if move:
         if all([self.board[coord] == self.solution[coord]  for coord in move]):          
           items = self.gui.get_numbers(move[0])
           [v.update(color='orange') for v in items.values()]
           self.gui.put_numbers(items)
        
      
  def run(self):
    KrossWord.run(self)

if __name__ == '__main__':
  g = FiveWays()
  g.run()
