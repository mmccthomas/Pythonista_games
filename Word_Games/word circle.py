# Word circle game - a classic
# Find a random word and N words containing
# some or all of its letters
# find also N words for each shorter word
# click and drag touch to select letters
import os
from queue import Queue
from time import sleep
import ui
import math
import random
import traceback
from Letter_game import LetterGame, Player
import Letter_game as lg
from gui.gui_interface import Gui
from setup_logging import logger
SPACE = ' '
WORDLIST = ["wordlists/letters3_common.txt", "wordlists/words_20000.txt", "wordlists/5000-more-common.txt"]
GRIDSIZE = '7,7'
HINT = (-1, -1)


class WordCircle(LetterGame):
  
  def __init__(self):
      self.SIZE = self.get_size()
      self.min_length = 3
      self.max_length = 6
      self.req_size = 8
      
      # load the gui interface
      self.log_moves = True
      self.gui = Gui(self.board, Player())
      self.gui.q = Queue()
      self.gui.set_alpha(False)
      img = self.draw_circle()
      self.gui.set_grid_colors(img)
      self.gui.require_touch_move(False)
      self.gui.allow_any_move(True)
      self.gui.setup_gui(log_moves=True, 
                         grid_stroke_color='clear',
                         hover=self.letters_so_far)
      self.gui.remove_labels()
      
      piece_names = 'abcdefghijklmnopqrstuvwxyz'
      base_path = os.path.dirname(os.path.dirname(__file__))
      pieces = {k: os.path.join(base_path, 'gui', 'tileblocks', f'{k}.png') for k in piece_names}
      pieces[' '] = os.path.join(base_path, 'gui', 'tileblocks', 'clear.png')
      self.gui.set_board_images(pieces)
      
      img = self.draw_circle()
      self.gui.add_image(img)
      
      self.load_words(0, file_list=WORDLIST)  # creates self.wordset
      self.partition_word_list()  # creates self.all_word_dict
      
      self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu,
                               'Reveal ....': self.reveal,
                               'Quit': self.quit})
      self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})
    
  def print_known_words(self):
      """
      Display the  players game board, we neve see ai
      indicate first N words of each word length
      uses dictionary known_words
      """
      for length, word_list in self.known_words.items():
          # set list to dashes for each letter
          msg_list = ['-' * length] * self.req_size
          msg_list[:len(word_list)] = word_list
          b = getattr(self, f'box{length}')
          self.gui.set_text(b, '\n'.join(msg_list), font=('Avenir Next', 25))
    
  def get_size(self):
      return LetterGame.get_size(self, GRIDSIZE)
     
  def place_letter_boxes(self):
      x, y, w, h = self.gui.grid.bbox
      for i in range(self.min_length, self.max_length+1):
        if self.gui.device.endswith('_landscape'):
            position = (10 + w + (i-self.min_length)*90, h/2)
        else:
            position = (w / 4 + (i-self.min_length) * 90, h)
        setattr(self, f'box{i}', self.gui.add_button(text='', title=f'Word {i}',
                                                     position=position,
                                                     min_size=(90, h/4),
                                                     font=('Avenir Next', 20)))
                       
  def find_base_word(self):
      # find a word which has at least self.req_size sub words for each length
      found = False
      while not found:
        selected_words = {}
        base_word = random.choice(list(self.all_word_dict[self.max_length]))
        # print(f'{base_word =}')
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
      return selected_words, base_word
    
  def initialise_board(self):
      [self.board_rc((r, c), self.board, SPACE) for c in range(self.sizex) for r in range(self.sizey)]
      self.word_selection, base_word = self.find_base_word()
      
      letters = list(base_word)
      # place baseword in grid
      random.shuffle(letters)
      positions = [(1, 2), (1, 4), (3, 1), (3, 5),
                   (5, 2), (5, 4)]
      random.shuffle(positions)
      # pos = random.choices(positions, k=self.max_length)
      for letter in letters:
          self.board_rc(positions.pop(), self.board, letter)
      self.gui.update(self.board)
      
      self.known_words = {k: [] for k in range(self.min_length, self.max_length+1)}
      self.place_letter_boxes()
   
  def draw_circle(self):
      """draw segmented circle for placement of letters"""
      center = 150, 150
      outer_radius = 150
      inner_radius = 50
      segments = self.max_length
      
      # Calculate the sweep angle for one segment
      sweep = (2 * math.pi) / segments
      with ui.ImageContext(300, 300) as ctx:
          # 1. Draw the Segments
          start = -sweep/2
          for i in range(segments):
              path = ui.Path()
              ui.set_color('black')
              path.line_width = 10
              
              path.move_to(*center)
              path.add_arc(*center, outer_radius, start, start + sweep)
              path.close()
              path.stroke()
              
              ui.set_color('#adf4ff')
              path.fill()
              
              start += sweep
                                             
          # 2. Draw the Central Circle
          center_rect = (center[0]-inner_radius, center[1]-inner_radius, inner_radius*2, inner_radius*2)
          ui.set_color('black')
          center_node = ui.Path.oval(*center_rect)
          center_node.line_width = 2
          center_node.fill()
          img = ctx.get_image()
      
      return img
        
  def letters_so_far(self):
      # display word so far
      # need to remove duplicates in sequence run length encoding?
      img = None
      if self.coord_list:         
         
         if -1 in self.coord_list:
              self.coord_list.remove(-1)  # remove terminator
         runlengths, startpositions, values = lg.rle(self.coord_list)         
         vals = values[runlengths > 2]                                        
         word = [self.get_board_rc(rc, self.board) for rc in vals if self.check_in_board(rc)]
         word = ''.join(word)
         word = word.replace(' ', '')    
         # print(word)
         if word:
            word = word.upper() + '\n'
            rect= ui.measure_string(word, max_width=0, font=('Avenir Next', 50))
            with ui.ImageContext(*rect) as ctx:                 
                 ui.draw_string(word, (0,0,*rect), font=('Avenir Next', 50), color='yellow')
                 img = ctx.get_image()      
      return img
          
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board,
    returns the coordinates of the move
    Allows for movement over board"""
    # self.delta_t('start get move')
    if board is None:
        board = self.game_board
    self.coord_list = []
    # sit here until piece place on board
    items = 0
    
    while items < 1000:  # stop lockup
      
      move = self.wait_for_gui()
      # if items == 0:
      #     st = time()
      try:
        if self.log_moves:
          self.coord_list.append(move)
          self.letters_so_far()
          items += 1
          if move == -1:
            # self.delta_t('end get move')
            return self.coord_list
        else:
          break
      except (Exception) as e:
        print(traceback.format_exc())
        print('except,', move, e)
        self.coord_list.append(move)
        return self.coord_list
    return move
           
  def process_turn(self, move, board):
      """ process the turn
      """
      # lets count no of unique coordinates to see how long on each square
      vals = []
      try:
          move.pop(-1)  # remove terminator
          # need to remove duplicates in sequence run length encoding?
          
          if move:
            runlengths, startpositions, values = lg.rle(move)
            vals = values[runlengths > 2]
            
            word = [self.get_board_rc(rc, self.board) for rc in vals if self.check_in_board(rc)]
            word = ''.join(word)
            logger.debug(f'{word}')
            word = word.replace(' ', '')
            in_list = word in self.word_selection[len(word)]
            check = '\t\tValid word' if in_list else '\t\tNot valid'
            self.gui.set_message(f'Word= {word} {check}')
      except (IndexError, AttributeError, KeyError):
          """ all_words may not exist or clicked outside box"""
          logger.debug(f'{traceback.format_exc()}')
      return vals
                  
  def match_word(self, move):
      """ match word to move"""
      word = [self.get_board_rc(rc, self.board) for rc in move if self.check_in_board(rc)]
      selected_word = ''.join(word)
      selected_word = selected_word.replace(' ', '')
      if self.min_length > len(selected_word) or  len(selected_word) > self.max_length:
          return
      if not selected_word:
          return
      if selected_word in self.word_selection[len(selected_word)]:
          self.known_words[len(selected_word)].append(selected_word)
          self.print_known_words()
  
  def reveal(self):
      # fill known_words with random unique elements from word_selection
      for k, known_words in self.known_words.items():
         all_words = set(self.word_selection[k])
         unique = list(all_words.difference(known_words))
         items_to_add = self.req_size - len(known_words)
         self.known_words[k] = known_words + random.sample(unique, items_to_add)
      self.print_known_words()
      sleep(5)
      self.gui.show_start_menu()
      
  def restart(self):
      """ reinitialise """
      self.gui.close()
      self.__init__()
      self.run()
            
  def game_over(self):
      """
      Checks if the game is over when all boxes have req_size words
      """
      return all([len(v) == self.req_size for k, v in self.known_words.items()])
    
  def hint(self):
      """random unplaced word """
      while True:
          length = random.randint(self.min_length, self.max_length)
          word = random.choice(self.word_selection[length])
          if (word not in self.known_words[length]) and (len(self.known_words[length]) < self.req_size):
            self.known_words[length].append(word)
            break
      self.print_known_words()
             
  def run(self):
      """
      Main method that prompts the user for input
      """
      self.gui.clear_numbers()
      self.gui.clear_messages()
      self.gui.set_top('WordCircle')
      self.gui.set_enter('Hint ', fill_color='clear', font=('Avenir Next', 50))
    
      self.initialise_board()
      self.print_known_words()
      while True:
          move = self.get_player_move(self.board)
          if move[0] == HINT:
              self.hint()
          vals = self.process_turn(move, self.board)
          self.match_word(vals)
          if self.game_over():
              break
      
      self.gui.set_message2('Game over')
      self.complete()
    

if __name__ == '__main__':
  g = WordCircle()
  g.run()
 
  while (True):
    quit = g.wait()
    if quit:
      break
  
