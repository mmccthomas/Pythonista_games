""" This game is the classic Scrabble grid puzzle
Chris Thomas July 2024

The games uses a 20k word dictionary
"""
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
import traceback
from time import sleep
from queue import Queue
import requests
from random import shuffle
from Letter_game import LetterGame
import gui.gui_scene as gscene
from ui import Image, Path, LINE_JOIN_ROUND, LINE_JOIN_MITER
from gui.gui_scene import Tile, BoxedLabel
from scene import Texture, Point
from gui.gui_interface import Gui, Coord
#from scrabble_ai_main.UI import scrabble_renderer
import scrabble_ai_main.Game.scrabble_game as scrabble_game
import scrabble_ai_main.Game.scrabble_objects as scrabble_objects
wordlists =['scrabble.txt', # official scrabble dict
            'scrabble_ai_main/Data/lang/en/3000_oxford_words.txt',
            '5000-more-common.txt',
            'words_10000.txt']
# select wordlist by index
wordlist = wordlists[0]

BLOCK = '#'
SPACE = ' '
FINISHED = (-10, -10)

def get_word_file(location, filename):
  r = requests.get(location)
  with open(filename, 'w') as f:
    f.write(r.text)
    
def fn_piece(piece):
      return f's_{piece}'  
              
class PPlayer():
  def __init__(self):
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  =' abcdefghijklmnopqrstuvwxyz0123456789.'
    self.PIECES = [f'../gui/s_{k}.png' for k in self.PIECE_NAMES]
    self.PIECES.append('../gui/s_@.png')
    self.PLAYERS = None
    
    
class Scrabble(LetterGame):
  
  def __init__(self):
    self.debug = False
    # allows us to get a list of rc locations
    self.log_moves = True
    self.SIZE = self.get_size('15,15') 
     
    # load the gui interface
    self.q = Queue()
    self.gui = Gui(self.board, PPlayer())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='Scrabble.jpg') # background is classic board
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(log_moves=True)
    self.gamestate = scrabble_game.GameState('scrabble_ai_main/Data/multipliers.txt',
                                             'scrabble_ai_main/Data/lang/en/tiles.txt')
    self.gameengine = scrabble_game.GameEngine(self.gamestate, wordlist)
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Options': self.options,
                              'Autoplay': self.ai_move,
                              'Complete Game': self.complete_game,
                              'Quit': self.quit})
    self.gui.set_start_menu({'New Game': self.restart, 'Quit': self.quit})    
    x, y, w, h = self.gui.grid.bbox    
    
    # positions of all objects for all devices
    position_dict = {
    'ipad13_landscape': {'rackpos': (10, 200), 'rackscale': 0.9, 'rackoff': h/8, 
    'button1': (w+20, h/6), 'button2': (w+250, h/6), 'button3': (w+140, h/6),
    'button4': (w+250, h/6-50), 'button5': (w+140, h/6-50),
    'box1': (w+5, 200+h/8-6), 'box2': (w+5, 200-6), 'box3': (w+5, 2*h/3),
    'box4': (w+5, h-50), 'font': ('Avenir Next', 24) },
                                       
    'ipad13_portrait': {'rackpos': (50-w, h+50), 'rackscale': 0.9, 'rackoff': h/8,
    'button1': (w/2, h+200), 'button2': (w/2, h+50), 'button3': (w/2, h+250),
    'button4': (w/2, h+100), 'button5': (w/2, h+150),
    'box1': (45, h+h/8+45), 'box2': (45, h+45), 'box3': (2*w/3, h+45),
    'box4': (2*w/3, h+200), 'font': ('Avenir Next', 24) },
    
    'ipad_landscape': {'rackpos': (30, 200), 'rackscale': 0.9, 'rackoff': h/8,
    'button1': (w+20, h/6), 'button2': (w+250, h/6), 'button3': (w+140, h/6),
    'button4': (w+250, h/6-50), 'button5': (w+140, h/6-50),
    'box1': (w+5, 200+h/8-6), 'box2': (w+5, 200-6), 'box3': (w+5, 2*h/3),
    'box4': (w+5, h-50), 'font': ('Avenir Next', 20) },
    
    'ipad_portrait': {'rackpos': (10, 200), 'rackscale': 0.9, 'rackoff': h/8,
    'button1': (w+20, h/6), 'button2': (w+250, h/6), 'button3': (w+140, h/6),
    'button4': (w/2, h+100), 'button5': (w/2, h+150),
    'box1': (w+5, 200+h/8-6), 'box2': (w+5, 200-6),'box3': (w+5, 2*h/3),
    'box4': (w+5, h-50), 'font': ('Avenir Next', 20)},
    
    'iphone_landscape': {'rackpos': (10, 0), 'rackscale': 1.5, 'rackoff': h/4,
    'button1': (w+300, h), 'button2': (w+300, h-50), 'button3': (w+300, h-100),
    'button4': (w+300, h-150), 'button5': (w+300, h-200),
    'box1': (w+5, h/4-6), 'box2': (w+5, -6), 'box3': (w+5, h/2),
    'box4': (w+5, h), 'font': ('Avenir Next', 15)},
    
    'iphone_portrait': {'rackpos': (10, 200), 'rackscale': 1.5, 'rackoff': h/8,
    'button1': (w, h/6), 'button2': (w+250, h/6), 'button3': (w+140, h/6),
    'button4': (w/2, h+100), 'button5': (w/2, h+150),
    'box1': (5, h+h/8-6), 'box2': (5, h-6), 'box3': (5, h),
    'box4': (5, h-50),  'font': ('Avenir Next', 15)}
     }
    self.posn = position_dict[self.gui.device] 
    self.time_delay = 1

    
    
  def add_boxes(self):
      """ add non responsive decoration boxes"""
      x, y, w, h = self.gui.grid.bbox 
      tsize = self.posn['rackscale'] * self.gui.gs.SQ_SIZE
      self.gui.add_button(text='', title='Computer', position=self.posn['box1'], 
                          min_size=(7 * tsize+10, tsize+10), 
                          fill_color='red')
      self.gui.add_button(text='', title='Player', position=self.posn['box2'], 
                          min_size=(7 * tsize+10, tsize+10), 
                          fill_color='blue')
      self.scores = self.gui.add_button(text='', title='Scores', position=self.posn['box3'], 
                                        min_size=(50, 50),
                                        fill_color='clear',
                                        font=self.posn['font'])
      self.gui.set_props(self.scores, font=self.posn['font'])
      self.turn = self.gui.add_button(text='Your Turn', title='Turn', position=self.posn['box4'], 
                                        min_size=(50, 50), 
                                        fill_color='clear',
                                        )
      self.gui.set_props(self.turn, font=self.posn['font'])
    
  def set_buttons(self):
    """ install set of active buttons """ 
    x, y, w, h = self.gui.grid.bbox       
    button = self.gui.set_enter('Play', position=self.posn['button1'],
                                stroke_color='black', fill_color='yellow',
                                color='black', font=self.posn['font'])   
    button = self.gui.add_button(text='Autoplay', title='', position=self.posn['button2'], 
                                 min_size=(80, 32), reg_touch=True,
                                 stroke_color='black', fill_color='yellow',
                                 color='black', font=self.posn['font']) 
    button = self.gui.add_button(text='Shuffle', title='', position=self.posn['button3'],
                                 min_size=(100, 32), reg_touch=True,
                                 stroke_color='black', fill_color='yellow',
                                 color='black', font=self.posn['font'])
    button = self.gui.add_button(text='Swap', title='', position=self.posn['button4'],
                                 min_size=(100, 32), reg_touch=True,
                                 stroke_color='black', fill_color='orange',
                                 color='black', font=self.posn['font'])
    button = self.gui.add_button(text='Options', title='', position=self.posn['button5'],
                                 min_size=(100, 32), reg_touch=True,
                                 stroke_color='black', fill_color='orange',
                                 color='black', font=self.posn['font'])

    
  def display_rack(self, tiles, y_off=0):
    """ display players rack
    y position offset is used to select player_1 or player_2
    """   
    parent = self.gui.game_field
    _, _, w, h = self.gui.grid.bbox        
    x, y = self.posn['rackpos']
    y = y + y_off
    rack = {}
    for n, tile in enumerate(tiles):    
      t = Tile(Texture(Image.named(f'../gui/s_{tile}.png')), 0,  0, sq_size=self.gui.gs.SQ_SIZE*self.posn['rackscale'])   
      t.position = (w + x + n * self.gui.gs.SQ_SIZE*self.posn['rackscale'], y)
      rack[t.bbox] = tile
      parent.add_child(t)     
            
    if y_off == 0:
       self.rack_player1 = rack
    else:
       self.rack_player2 = rack    
          
  def update_board(self, hint=False, filter_placed=True):
    """ requires solution_dict from generate_word_anagram_pairs
                 solution_board from create_anagram_board 
    """  
    board = self.sync_board() 
    self.gui.update(board)        
    x, y, w, h = self.gui.grid.bbox     
    self.display_rack(self.computer_rack, y_off=self.posn['rackoff'])
    self.display_rack(self.human_rack) 
    self.gui.set_text(self.scores, f'Computer score: {self.gamestate.player_2.score}\nHuman score: {self.gamestate.player_1.score}\nTiles left {self.gamestate.pouch.tiles_amount()}')   
    try:
       self.gui.set_message2('\n'.join(self.gameengine.logs[-2:]))
    except (IndexError):
       pass   
       
  def update_rack(self, player='human'):
    if player=='human':
        return [tile.letter.lower() if tile else '@' for tile in self.gamestate.player_1.rack.tiles] 
    else:
        return [tile.letter.lower() if tile else '@' for tile in self.gamestate.player_2.rack.tiles ] 
        
  def shuffle_tiles(self):
      """ shuffle tiles of human player"""
      shuffle(self.human_rack)      
         
  def run(self):    
    """
    Main method that prompts the user for input
    """    
    self.gui.clear_messages()
    self.set_buttons()
    self.human_rack = self.update_rack('human')
    self.computer_rack = self.update_rack('computer')          
    self.add_boxes()
    self.update_board()
    self.letters_used = []  
    while True:
      self.gui.set_text(self.turn, 'Your Turn')
      pieces_used = 0
      while pieces_used == 0:
        move = self.get_player_move(self.board)         
        pieces_used = self.process_turn( move, self.board)         
        self.update_board()
      if self.game_over(): break      
      self.human_rack = self.update_rack('human')
      self.update_board()
      self.gui.set_text(self.turn, 'AI Turn')
      sleep(self.time_delay)
      self.ai_move()      
      if self.game_over(): break       
   
  def game_over(self):
    """ check for finished game """
    return self.gamestate.game_ended  
    
  def sync_board(self):
    """ constuct board from gamestate"""
    return [[cell.tile.letter.lower() if cell.tile else '-' for cell in row] for row in self.gamestate.board.board]
    
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter, selection_row
    """ 
    rack = self.rack_player1 if self.gamestate.current_player().name == 'Human' else self.rack_player2
    player = self.gamestate.current_player()
    if move:
      coord, letter, row = move
      r,c = coord
      if letter == 'Enter':
        # confirm placement
        result = self.gameengine.play_draft()
        
        no_pieces_used = len(self.letters_used)
        self.sync_board()         
        if not result:
            self.human_rack = self.update_rack('human')
            return 0
        else:
            return no_pieces_used
            
      elif letter == 'Autoplay':
        self.ai_move()
        
      elif letter == 'Shuffle':
        self.shuffle_tiles()
      
      elif letter == 'Swap':
         self.handle_swap_button()
         
      elif letter == 'Options':
         self.options()
          
      elif coord == (None, None):
        return 0
        
      elif letter == 'Finish':
        return 0 
           
      elif letter != '':  # valid selection
        try:
            r,c = coord
            cell = self.gamestate.board.board[r][c]
            # get point value of selected tile
            point = player.rack.tiles[row].point
            cell.tile = scrabble_objects.Tile(letter.upper(),point=point) 
            cell.tile.draft = True
            self.gamestate.player_1.rack.tiles[row].draft = True
            self.human_rack[row] = '@'
            self.update_board()
            self.letters_used.append(letter)            
        except (IndexError):
          pass             
    return 0   
      
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    move = LetterGame.get_player_move(self, self.board)
    
    rack = self.rack_player1 if self.gamestate.current_player().name == 'Human' else self.rack_player2
    
    if move[0] == (-1, -1):
       return (None, None), 'Enter', None # pressed enter button
    # deal with buttons. each returns the button text
    elif move[0] < (0,0):
      return (None, None), self.gui.gs.buttons[-move[0][0]].text, None
    
    point = self.gui.gs.start_touch - gscene.GRID_POS
    # get letter from rack
    for index, k in enumerate(rack):
       if k.contains_point(point):
          letter = rack[k]
          rc = move[-2]
          return rc, letter, index
    return (None, None), None, None    
    
  def restart(self):
    """ reinitialise """ 
    self.gui.gs.close()
    self.__init__()
    self.run() 
    
  def ai_move(self):
    # find best move and play it
    try:
        if self.gamestate.current_player().name == 'Human':
            self.gui.set_text(self.turn, 'Your Turn')
            self.gameengine.ai_make_move(gui=self.gui) 
            self.human_rack = self.update_rack('human')
            self.update_board() 
            if self.game_over():
               self.gui.set_message2('Game Over')
               return
            self.gui.set_text(self.turn, 'AI Turn')
            sleep(self.time_delay)
            self.ai_move() # make computer move, not recursive
        else:
            self.gui.set_text(self.turn, 'AI Turn')
            self.gameengine.ai_make_move(gui=self.gui) 
            self.computer_rack = self.update_rack('computer')
            self.update_board()
            sleep(self.time_delay)
            self.gui.set_text(self.turn, 'Your Turn')
            return None
    except (Exception):
      print(traceback.format_exc())
  
  def complete_game(self):
    while True:
      self.ai_move() # human then ai
      if self.game_over():
        self.gui.set_message2('Game Over')
        break
    print('\n'.join(self.gameengine.logs))
  
  def handle_swap_button(self):
      '''will swap out letters placed on board
      if none placed will swap out all tiles
      ''' 
      drafts = [tile.draft for  tile in self.gamestate.player_1.rack.tiles]
      all_tiles = not any(drafts) 
      self.gameengine.swap_draft(all_tiles)
      self.sync_board() 
      self.human_rack = self.update_rack('human')
      self.update_board()
      sleep(self.time_delay)
      self.ai_move() 
 
  def options(self):
      x, y, w, h = self.gui.grid.bbox   
      self.gameengine.ai_handle_turn()
      self.gui.input_text_list('Play options', items=self.gameengine.ai_possible_move_ids, position=(w,h))
      while self.gui.text_box.on_screen:    
          try:
            selection = self.gui.selection
            selection_row = self.gui.selection_row
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
            
      if selection_row is not None:      
          idx = selection_row
          self.gameengine.play_option(idx)
          self.sync_board() 
          self.human_rack = self.update_rack('human')
          self.update_board()
          sleep(self.time_delay)
          self.ai_move() 
          
                  
class Renderer():    




    def on_change(self, option_item):
        self.gameengine.clear_draft()
        for cell, tile in self.gameengine.ai_possible_moves[option_item[1]].items():
            cell.tile = tile
            tile.draft = True

    def handle_play_selection_button(self):
        drop_down_widget = self.ai_possible_moves_sec.get_widget('poss_moves')
        _, selected_idx = drop_down_widget.get_value()

        if selected_idx != -1:
            self.gameengine.play_option(selected_idx)
        
        drop_down_widget.reset_value()
        drop_down_widget.update_items([])
        
if __name__ == '__main__':
  g = Scrabble()
  g.run()

  

