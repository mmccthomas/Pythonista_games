# Wordsearch game - a classic
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from time import sleep
import random
import traceback
import numpy as np
from Letter_game import LetterGame
BLOCK = '#'
SPACE = ' '
WORDLIST = ['letters3_common.txt', '5000-more-common.txt']
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
  
class Player():
  def __init__(self):
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  ='abcdefghijklmnopqrstuvwxyz0123456789. '
    self.PIECES = [f'../gui/{k}.png' for k in self.PIECE_NAMES[:-2]]
    self.PIECES.append('../gui/@.png')
    self.PIECES.append('../gui/s_.png')
    self.PLAYERS = None    
    
    
class WordCircle(LetterGame):
  
  def __init__(self):
    LetterGame.__init__(self)
    # allows us to get a list of rc locations
    self.SIZE = self.get_size()
    self.word_coords = {}
    self.min_length = 3
    self.max_length = 6
    self.load_words(0, file_list=WORDLIST) # creates self.wordset 
    self.partition_word_list()  # creates self.all_word_dict
    
    self.known_words = []
    self.word_selection = {}
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'Reveal ....': self.reveal,
                              'Quit': self.quit})
    self.req_size = 8
    
  def print_board(self):
    """
    Display the  players game board, we neve see ai
    indicate first N words of each word length
    """
    self.all_possible_words = []
    self.display_words = [] 
    for length in range(self.min_length, self.max_length + 1):
        self.display_words.extend(self.word_selection[length][:self.req_size])
        self.all_possible_words.extend(self.word_selection[length])
        
    # set list to dashes for each letter       
    msg_list = [word if word in self.known_words else '-' * len(word) for word in self.display_words]
  
    
    for i in range(self.min_length, self.max_length+1):
        b = getattr(self, f'box{i}')
        msg =[m for m in msg_list if len(m) == i]
        self.gui.set_text(b, '\n'.join(msg), font=('Avenir Next', 25))        
            
    if self.gui.gs.device.endswith('_landscape'):
      pass
    self.gui.update(self.board)  
    
  def get_size(self):
   return  LetterGame.get_size(self, GRIDSIZE)
  
  def initialise_board(self):        
    [self.board_rc((r,c,), self.board, SPACE) for c in range(self.sizex) for r in range(self.sizey)]
    found = False
    # find a word which has at least self.req_size
    while not found:
      selected_words = {}
      base_word = random.choice(list(self.all_word_dict[self.max_length]))
      #print(f'{base_word =}')
      for length in range(self.max_length, self.min_length - 1, -1):
        wordlist = []
        for word in self.all_word_dict[length]:
           if all([letter in base_word for letter in list(word)]) and base_word != word:
               wordlist.append(word)
     
        if len(wordlist) < self.req_size:
          found = False
          break
        else:
          selected_words[length] = wordlist
          found = True
    
    selected_words[self.max_length].append(base_word)
    letters = list(base_word)   
    # place baseword in grid     
    random.shuffle(letters)  
    for rc in [(0, 1), (0, 3), (1, 0), (2, 3), (3, 1)]:
       self.board_rc(rc, self.board, letters.pop())
    
    self.word_selection = selected_words
    if self.gui.gs.device.endswith('_landscape'):
      pass
    x, y, w, h = self.gui.grid.bbox
    for i in range(self.min_length, self.max_length+1):
      if self.gui.gs.device.endswith('_landscape'):
          position = (10 + w +  (i-self.min_length)*90, h/2)
      else:
          position = (w/4+ (i-self.min_length)*90, h)
      setattr(self, f'box{i}', self.gui.add_button(text='', title=f'Word {i}', 
                                                   position=position, 
                                                   min_size=(90, h/4), 
                                                   font=('Avenir Next', 20)))
    
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
    # lets count no of unique coordinates to see how long on each square               
    try:
        move.pop(-1) # remove terminator
        # need to remove duplicates in sequence run length encoding?
        runlengths, startpositions, values = rle(move)
        vals = values[runlengths>2]   
        
        word = [self.get_board_rc(rc, self.board) for rc in vals  if self.check_in_board(rc)]
        word = ''.join(word)
        if self.debug:
            print(word)
        word = word.replace(' ', '')
        valid = word in self.all_possible_words
        in_list = word in self.display_words
        check = '\t\tValid word' if valid else '\t\tNot valid'
        self.gui.set_message(f'Word= {word} {check}\t\t {in_list =}')
    except(IndexError, AttributeError):
        """ all_words may not exist or clicked outside box"""
        if self.debug:
            print(traceback.format_exc())
    return vals        
                  
  def match_word(self, move):
    """ match word to move"""      
    word = [self.get_board_rc(rc, self.board) for rc in move  if self.check_in_board(rc)]
    selected_word = ''.join(word)  
    selected_word = selected_word.replace(' ', '')  
    
    for kword in self.display_words:
      if kword == selected_word:       
        self.known_words.append(selected_word)       
        self.print_board()      
        break        
  
  def reveal(self):    
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
    return  self.known_words == self.display_words
    
  def hint(self):
      """ reveal  a random unplaced word
      TODO could do better """ 
      self.known_words.append(random.choice(self.display_words))
      self.print_board()
             
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
    self.initialise_board() 
    self.print_board()
    while True:
      move = self.get_player_move(self.board)  
      if move[0] == HINT:
          self.hint()             
      vals = self.process_turn( move, self.board) 
      self.match_word(vals)
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
 
  
