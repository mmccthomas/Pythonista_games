"""
keyboard sets _output when return is pressed
menu gets result through queue and invokes function directly
fixed issues  by allowing placement of menu and moving keyboard to bottom
"""
import random
import dialogs
import sys
import ui
from objc_util import on_main_thread
from time import sleep
from Letter_game import LetterGame
from Utilities.change_screensize import get_screen_size
from gui.qwerty_keyboard import QWERTYKeyboard
from gui.gui_interface import Squares
# from setup_logging import logger
WordleList = ['wordlists/5000-more-common.txt']
# common starting words ['soare', 'roate', 'raise']
no_letters = 5
no_tries = 6


class Wordle(LetterGame):
  
  def __init__(self):
      LetterGame.__init__(self)
      self.gui.clear_messages()
      self.gui.set_top('Wordle')
      self.gui.remove_labels()
      self.first_letter = False
      self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                               'New ....': self.restart,
                               'Hint': self.hint,
                               'Reveal': self.reveal,
                               'Quit': self.quit})
      self.gui.set_start_menu({'New ....': self.restart,
                               'Quit': self.quit})
      x, y, w, h = self.gui.grid.bbox
      W, H = get_screen_size()
      self.gui.gs.menu_position = (0.75*W, 0.65*H)
      self.keyboard = QWERTYKeyboard(display_bar=True,  frame=(w+40, y+4*h/no_letters, W-w-100, 2*h/no_letters))
      self.gui.v.add_subview(self.keyboard)
      self.keyboard.set_required_length(no_letters)
      self.keyboard.q = self.gui.q

  def run(self):
    self.row = 0
    self.initialise_board()
    self.square_list = []

    while self.row < self.sizey:
        # 1. Refresh GUI state
        self.gui.clear_squares()
        self.print_board()
        
        # 2. Wait for Input (Manual or Menu)
        # If get_player_move returns None, hint() already handled the logic.
        move = self.get_player_move(self.board)
        
        if move is not None:
            # Standard keyboard entry path
            self.process_turn(move, self.board)
            self.print_square(move)
            self.row += 1
            
        # 3. Check for Win/Loss
        if self.game_over():
            break

    # Final cleanup
    self.print_board()
    self.gui.set_message2('')
    self.complete()
                        
  def get_size(self):
      LetterGame.get_size(self, f'{no_letters},{no_tries}')
    
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
          self.gui.clear_numbers()
      except (AttributeError):
          pass
      
      r = self.row
      for c in self.correct_positions:
          self.square_list.append(Squares((r, c), '', 'green', z_position=30, alpha=0.5))
         
      for c in self.correct_letters:
          self.square_list.append(Squares((r, c), '', 'orange', z_position=30, alpha=0.5))
      
      self.gui.add_numbers(self.square_list)
      return
 
  def get_player_move(self, board=None):
    self.turn_processed = False 
    self.keyboard.set_display(f"Select {no_letters} letters")

    while len(self.keyboard._output) < no_letters:
        sleep(0.1)
        
        # 1. Check if Hint/Menu handled the turn
        if self.turn_processed:
            self.gui.dismiss_menu()
            return None 

        # 2. Update keyboard visibility based on menu state
        if self.gui.v.scene.presented_scene is not None:
            self.wait_for_gui()
        else:            
            # Use the keyboard's internal output to detect completion
            if len(self.keyboard._output) == no_letters:
                break
                
    move = ''.join(self.keyboard._output)
    self.keyboard.reset_output()
    return move
    
  def process_turn(self, move, board):
    """ allows for duplicate letters """
    r = self.row
    move = move.lower()
    target = self.chosen_word.lower()
    
    # Initialize result sets
    self.correct_positions = set() # Green
    self.correct_letters = set()   # Orange
    self.incorrect_letters = set() # Gray
    
    # Track available letters in target for Orange logic
    target_pool = list(target)
    
    # First Pass: Find Greens
    for i in range(self.sizex):
        if move[i] == target[i]:
            self.correct_positions.add(i)
            target_pool[i] = None # Mark as consumed
            board[r][i] = move[i]

    # Second Pass: Find Oranges (remaining matches)
    for i in range(self.sizex):
        if i in self.correct_positions:
            continue
            
        if move[i] in target_pool:
            self.correct_letters.add(i)
            # Remove ONLY one instance of the letter from the pool
            target_pool[target_pool.index(move[i])] = None
        else:
            self.incorrect_letters.add(i)
        
        board[r][i] = move[i]
    self.gui.update(self.board)
    return move       
         
  def game_over(self):
      if self.row == self.sizey:
          dialogs.hud_alert(f' Word was {self.chosen_word}', duration=3)
          self.gui.set_message2(f' Word was {self.chosen_word}')
          return True
      if len(list(set(self.correct_positions))) == self.sizex:
          dialogs.hud_alert(f' Well done, you found  {self.chosen_word}', duration=3)
          self.gui.set_message2(f' Well done, you found  {self.chosen_word}')
          return True
          
  @on_main_thread       
  def hint(self):
    self.gui.dismiss_menu()
    # Logic to find a hint word
    five_letters = [word for word in self.wordlist if len(word) == self.sizex]
    random.shuffle(five_letters)            
    hint_word = next((w for w in five_letters if any(a == b for a, b in zip(w, self.chosen_word))), None)
    
    if hint_word:        
        # Process the turn immediately
        self.process_turn(hint_word, self.board)
        self.print_square(hint_word)
        self.print_board()
        self.row += 1
        
        # Critical: Tell the get_player_move loop to stop waiting
        self.turn_processed = True        
                
  def reveal(self):
      self.process_turn(self.chosen_word, self.board)
      self.print_square(self.chosen_word)       
      self.print_board()
      dialogs.hud_alert(f' Word was {self.chosen_word}', duration=3)
      self.gui.set_message2(f' Word was {self.chosen_word}')
      self.turn_processed = True   
      
if __name__ == '__main__':
    g = Wordle()
    g.run()
    while True:
        quit = g.wait()
        if quit:
            break





