import random
import console
import dialogs
import ui
import base_path
base_path.add_paths(__file__)
from time import sleep
from queue import Queue
from Letter_game import LetterGame, Player
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
WordleList = ['wordlists/5000-more-common.txt'] 


class Wordle(LetterGame):
  
  def __init__(self):
    LetterGame.__init__(self)
    self.first_letter = False
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              #'Hint': self.hint,
                              #'Reveal': self.reveal,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    self.correct_positions = []
    self.correct_letters = []
    self.incorrect_letters = []
    self.possibles = []
    self.row = 0
    self.square_list = []
    self.print_square(1)
    self.initialise_board()    
    self.finished = False
    move = ''
    while True:
      self.gui.clear_squares()           
      self.print_board()
      self.possibles = self.possible_words(move)
      move = self.get_player_move(self.board)               
      move = self.process_turn( move, self.board) 
      self.print_square(move)
      self.print_board()
      self.row += 1  
      if self.game_over():
        break                  
    self.print_board()
    self.gui.set_message2('')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.gs.show_start_menu()   
    
  def get_size(self):
    LetterGame.get_size(self, '5, 6')
    
  def load_words(self, word_length, file_list=WordleList):
    LetterGame.load_words(self, word_length, file_list=file_list)
     
  def initialise_board(self):
    
    five_letters = [word for word in self.wordlist if len(word) == self.sizex]
    self.chosen_word = random.choice(five_letters)
    if self.first_letter:
      self.board[0][0] = self.chosen_word[0]
      self.correct_positions = [0]
    
    
  def print_square(self, moves, color=None):
    #
    try: 
      self.gui.gs.clear_numbers()
    except (AttributeError):
      pass
    
    r = self.row
    for c in self.correct_positions:
      self.square_list.append(Squares((r, c), '', 'green' , z_position=30, alpha = .5)) 
       
    for c in self.correct_letters:
      self.square_list.append(Squares((r, c), '', 'orange' , z_position=30, alpha = .5))
    
    self.gui.add_numbers(self.square_list)   
    return
  
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    #self.delta_t('start get move')
    
    if board is None:
        board = self.board
    selected_ok = False
    #prompt = f"Select from {len(self.possibles)} items"
    prompt = "Select 5 letters"
    if len(self.possibles) == 0:
      raise (IndexError, "possible list is empty")
    #selection = dialogs.list_dialog(prompt, list(self.possibles))
    items = sorted(list(self.possibles)) 
    
    # first move insert common starting words
    if len(self.possibles) == len(self.wordlist):
      items = ['soare', 'roate', 'raise'] + items
    x, y, w, h = self.gui.grid.bbox 
    #return selection
    while self.gui.selection == '':
      self.gui.input_letters(prompt=prompt, position=(w+150, h/4), items=None, allows_multiple_selection=True)
      self.gui.text_box = self.gui.letter_panel
      #self.gui.input_text_list(prompt=prompt, items=items, position=(w+250, 0))
      while self.gui.text_box.on_screen:
          sleep(.2)
          try:
              selection = self.gui.selection.lower()
              selection_row = self.gui.selection_row                
          except (AttributeError):  # got a list
              selection = ''.join(self.gui.selection)
              selection_row = self.gui.selection_row
          except (Exception) as e:
              print(e)
              print(traceback.format_exc())              
      self.gui.selection = ''              
      print('letter ', selection)
      if len(selection) == self.sizex:
         return selection #, selection_row
      
    
  def process_turn(self, move, board):
    """ process the turn
    """
    if self.row == self.sizey:
        self.game_over()
    if move:
      r = self.row
      # TODO modify to take account of double letter. correct position can getcounted twice
      self.correct_positions = {c for c in range(len(move)) if move[c] == self.chosen_word[c]}
      self.correct_letters = {c for c in range(len(move)) if move[c] in self.chosen_word}
      self.correct_letters = self.correct_letters - self.correct_positions
      
      self.incorrect_letters = [c for c in range(len(move)) if move[c] not in self.chosen_word]     
      
      for c in range(self.sizex):
        board[r][c] = move[c]     
      
    return move
    
  def possible_words(self, move):
    if self.possibles == []:
      possibles = self.wordset
    else:
      possibles = self.possibles

    #Sublist = words where character in position matches known
    if move:
      for c in self.correct_positions:        
        incorrect_words = {word for word in self.correct_words if move[c] != word[c]}
        self.correct_words = self.correct_words - incorrect_words
      for c in self.incorrect_letters:        
        incorrect_words = {word for word in self.correct_words if move[c] in word}
        self.correct_words = self.correct_words - incorrect_words
    elif self.first_letter == True:       
      incorrect_words = {word for word in possibles if self.board[0][0] != word[0]}
      self.correct_words = possibles - incorrect_words
    else:
      self.correct_words = possibles
      
    try:
      self.correct_words.remove(move)
    except (ValueError, KeyError):
      pass
       
    return self.correct_words
     
  def game_over(self):
    if self.row == self.sizey:
      dialogs.hud_alert(f' Word was {self.chosen_word}', duration=3)
      self.gui.set_message2(f' Word was {self.chosen_word}')      
      return True
    if len(list(set(self.correct_positions))) == self.sizex:
      dialogs.hud_alert(f' Well done, you found  {self.chosen_word}', duration=3)
      self.gui.set_message2(f' Well done, you found  {self.chosen_word}')
      return True  
      
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    g = Wordle()
    g.run()
            
    
if __name__ == '__main__':
  g = Wordle()
  g.run()
  while(True):
    quit = g.wait()
    if quit:
      break





