""" This game is the classic Scrabble grid puzzle
Chris Thomas July 2024

The games uses a 20k word dictionary
"""
import os
import traceback
from time import sleep
from queue import Queue
import requests
from types import SimpleNamespace
from random import shuffle
from Letter_game import LetterGame
import gui.gui_scene as gscene
from ui import Image, Path, LINE_JOIN_ROUND, LINE_JOIN_MITER
from gui.gui_scene import Tile, BoxedLabel
from scene import Texture, Point
from gui.gui_interface import Gui, Coord
from setup_logging import logger
#from scrabble_ai_main.UI import scrabble_renderer
from scrabble_ai_main import Game
from scrabble_ai_main.Game import scrabble_game, scrabble_objects
wordlists =['wordlists/scrabble.txt', # official scrabble dict
            'scrabble_ai_main/Data/lang/en/3000_oxford_words.txt',
            'wordlists/5000-more-common.txt',
            'wordlists/words_10000.txt']
# select wordlist by index
wordlist = wordlists[2]

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
    self.PIECES = [f'../gui/tileblocks/s_{k}.png' for k in self.PIECE_NAMES]
    self.PIECES.append('../gui/tileblocks/s_@.png')
    self.PLAYERS = None
    
    
class Scrabble(LetterGame):
  
  def __init__(self):
    # allows us to get a list of rc locations
    self.log_moves = True
    self.SIZE = self.get_size('15,15') 
     
    # load the gui interface
    self.gui = Gui(self.board, PPlayer())
    self.gui.q = Queue()
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
    W, H = self.gui.get_device_screen_size()
    # positions of all objects for all devices
    # convert to scaled positions
    orientation = 'portrait' if H > W else 'landscape'
    fontsize = self.gui.get_fontsize()
    spc = self.gui.gs.spacing
    position_dict = {
     # 1366, 1024
     # all positions are relatve to grid size, so scale with screen size
     # only need to select on portrait
     'landscape': {'rackpos': (0.75*spc*w, h/4), 'rackscale': 0.9, 'rackoff': h/8, 
                   'button1': (w+spc*w, h/6), 
                   'button2': (w+12*spc*w, h/6), 
                   'button3': (w+6*spc*w, h/6),
                   'button4': (w+12*spc*w, h/10), 
                   'button5': (w+6*spc*w, h/10),
                   'box1': (w+0.5*spc*w, h/4+h/8-0.25*spc*h), 
                   'box2': (w+0.5*spc*w, h/4-0.25*spc*h), 
                   'box3': (w+0.5*spc*w, 2*h/3),
                   'box4': (w+0.5*spc*w, h-50), 'font': ('Avenir Next', fontsize)},
    
    'portrait':  {'rackpos': (2*spc*w-w, h+2*spc*h), 'rackscale': 0.9, 'rackoff': h/8,
                  'button1': (w/2, h+8*spc*h), 
                  'button2': (w/2, h+2*spc*h), 
                  'button3': (w/2, h+10*spc*h),
                  'button4': (w/2, h+4*spc*h), 
                  'button5': (w/2, h+6*spc*h),
                  'box1': (1.75*spc*w, h+h/8+1.75*spc*h), 
                  'box2': (1.75*spc*w, h+1.75*spc*h), 
                  'box3': (2*w/3, h+2*spc*h),
                  'box4': (2*w/3, h+9*spc*h), 
                  'font': ('Avenir Next', fontsize)}}        

    self.posn = SimpleNamespace(**position_dict[orientation])
    self.time_delay = 1    
    
  def add_boxes(self):
      """ add non responsive decoration boxes"""
      x, y, w, h = self.gui.grid.bbox 
      tsize = self.posn.rackscale * self.gui.SQ_SIZE
      
      spc = self.gui.gs.spacing
      tspc = 8 * spc * tsize
      box = self.gui.add_button(text='', title='Computer', position=self.posn.box1, 
                          min_size=(7 * tsize+tspc, tsize+tspc), 
                          fill_color='red')
      self.gui.set_props(box, font=self.posn.font)
      box = self.gui.add_button(text='', title='Player', position=self.posn.box2, 
                          min_size=(7 * tsize+tspc, tsize+tspc), 
                          fill_color='blue')
      self.gui.set_props(box, font=self.posn.font)
      self.scores = self.gui.add_button(text='', title='Scores', position=self.posn.box3, 
                                        min_size=(50, 50),
                                        fill_color='clear')
      self.gui.set_props(self.scores, font=self.posn.font)
      self.turn = self.gui.add_button(text='Your Turn', title='Turn', position=self.posn.box4, 
                                        min_size=(50, 50), 
                                        fill_color='clear' )
      self.gui.set_props(self.turn, font=self.posn.font)
    
  def set_buttons(self):
    """ install set of active buttons """ 
    x, y, w, h = self.gui.grid.bbox 
    fontsize = self.gui.get_fontsize()      
    button = self.gui.set_enter('Play', position=self.posn.button1,
                                min_size=(2*fontsize, fontsize),
                                stroke_color='black', fill_color='yellow',
                                color='black', font=self.posn.font)   
    button = self.gui.add_button(text='Autoplay', title='', position=self.posn.button2, 
                                 min_size=(2*fontsize, fontsize), 
                                 reg_touch=True,
                                 stroke_color='black', fill_color='yellow',
                                 color='black', font=self.posn.font) 
    button = self.gui.add_button(text='Shuffle', title='', position=self.posn.button3,
                                 min_size=(2*fontsize, fontsize), 
                                 reg_touch=True,
                                 stroke_color='black', fill_color='yellow',
                                 color='black', font=self.posn.font)
    button = self.gui.add_button(text='Swap', title='', position=self.posn.button4,
                                 min_size=(2*fontsize, fontsize),  
                                 reg_touch=True,
                                 stroke_color='black', fill_color='orange',
                                 color='black', font=self.posn.font)
    button = self.gui.add_button(text='Options', title='', position=self.posn.button5,
                                 min_size=(2*fontsize, fontsize), 
                                 reg_touch=True,
                                 stroke_color='black', fill_color='orange',
                                 color='black', font=self.posn.font)

    
  def display_rack(self, tiles, y_off=0):
    """ display players rack
    y position offset is used to select player_1 or player_2
    """   
    parent = self.gui.game_field
    _, _, w, h = self.gui.grid.bbox        
    x, y = self.posn.rackpos
    y = y + y_off
    rack = {}
    for n, tile in enumerate(tiles):    
      t = Tile(Texture(Image.named(f'../gui/tileblocks/s_{tile}.png')), 0,  0, sq_size=self.gui.SQ_SIZE*self.posn.rackscale)   
      t.position = (w + x + n * self.gui.SQ_SIZE*self.posn.rackscale, y)
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
    self.display_rack(self.computer_rack, y_off=self.posn.rackoff)
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
    self.complete()       
   
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
    elif move[0][0] < 0 and move[0][1] < 0:
      return (None, None), self.gui.buttons[-move[0][0]].text, None
      
    point = self.gui.start_touch - self.gui.grid_pos
    # get letter from rack
    for index, k in enumerate(rack):
        if k.contains_point(point):
            letter = rack[k]
            rc = move[-2]
            return rc, letter, index
    return (None, None), None, None    
    
  def restart(self):
    """ reinitialise """ 
    self.gui.close()
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

  

