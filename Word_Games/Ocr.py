# Use VisionKit text recognition to read an image
# containing text.
# Provide a grid to generate crossword frame as text
import photos
import objc_util
import os
import sys
import clipboard
import dialogs
from queue import Queue
import pandas as pd
from matplotlib import pyplot
import traceback
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from types import SimpleNamespace
from gui.gui_interface import Gui, Coord, Squares
from Word_Games.Letter_game import LetterGame
from scene import *
import gui.gui_scene as gs
import numpy as np
savefile= 'Ocr_save'

VNImageRequestHandler = objc_util.ObjCClass('VNImageRequestHandler')
VNRecognizeTextRequest = objc_util.ObjCClass('VNRecognizeTextRequest')
class Player():
  def __init__(self):
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  ='abcdefghijklmnopqrstuvwxyz0123456789. '
    self.PIECES = [f'../gui/tileblocks/{k}.png' for k in self.PIECE_NAMES[:-2]]
    self.PIECES.append(f'../gui/tileblocks/@.png')
    self.PIECES.append(f'../gui/tileblocks/_.png')
    self.PLAYERS = None
    
def text_ocr(asset):
  """Image recognition of text
  works best with full words or numbers
  individual letters not so great
  """
  img_data = objc_util.ns(asset.get_image_data().getvalue()) 
  with objc_util.autoreleasepool():
    req = VNRecognizeTextRequest.alloc().init().autorelease()
    req.setRecognitionLanguages_(['zh-Hant', 'en-US'])
    req.setRecognitionLevel_(0) # accurate
    handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
    success = handler.performRequests_error_([req], None)    
    if success:
        all_text = {}
        for result in req.results():
          cg_box = result.boundingBox()
          x, y = cg_box.origin.x, cg_box.origin.y
          w, h = cg_box.size.width, cg_box.size.height
          all_text[x, y, w, h] = str(result.text())
        
        results =  [result.text() for result in req.results()]
         
        return all_text #[str(result.text()) for result in req.results()]        

def sort_by_postion(all_text_dict):
    # use the box data to reorder text
    # attempts to reconstruct crossword letters
    
    #attempt to put dictionary into regular grid
    # all_text_dict has form (x, y, w, h): text
    #x, y, w, h are scaled 0-1.0
    
    df = pd.DataFrame(np.array(list(all_text_dict.keys())), columns=('x', 'y', 'w', 'h'))
    # scale 0-1000 and round to nearest 5
    df2 = df.multiply(1000).astype(int)    
    df3 = df2.divide(5.0).round().multiply(5).astype(int)
    # find sungle spacing
    df_diff = df3.diff()
    df_med = df_diff.median()['y']
    # scale to spacing
    df4 = df3.divide(-df_med).round().astype(int)
    #stitch text
    text_df = pd.DataFrame(np.array(list(all_text_dict.values())), columns =['text'])
    df = df4.join(text_df)   
    #sort by y then x
    sorted_df = df.sort_values(by=['y', 'x'], ascending=[False, True])
    print(sorted_df.to_string())
    # prepare board
    board =np.empty((df['y'].max()+1, df['x'].max()+1), dtype='U1')
    board[:,:] = ' '
    #fill board
    try:
        for _, row in sorted_df.iterrows():
    	      board[row['y'], row['x']: row['x']+len(row['text'])] = list(row['text'])
    except (ValueError) as e:
    	print(traceback.format_exc())
    # turn upside down
    board = np.flipud(board)
    # print it
    [print(''.join(row)) for row in board]

class OcrCrossword(LetterGame):
    def __init__(self, all_text):
        self.load() # attempt to load temp file
        self.SIZE = self.get_size()        
        self.q = Queue()
        self.log_moves = False
        self.gui = Gui(self.board, Player())
        self.gui.gs.q = self.q 
        self.words = []
        self.letters_mode = False
        self.direction_mode = False
        self.index_mode = False
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(grid_fill='black')
        self.board = np.array(self.board)
        self.board[self.board == '-'] = ' ' # replace '-' by ' '
        self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
        self.gui.build_extra_grid(self.sizex, self.sizey, 
                                  grid_width_x=1, grid_width_y=1,
                                  color='black', line_width=1)
        self.all_text = all_text
        self.x, self.y, self.w, self.h = self.gui.grid.bbox
        self.gui.clear_messages()
        self.box_positions()
        self.set_buttons()
        self.add_boxes()
        self.add_indexes()
        
    def add_indexes(self):
      if hasattr(self, 'indexes'):
          indexes = np.argwhere(self.indexes !=0)
          squares_list = []
          for index in indexes:
            i = self.indexes[tuple(index)]
            squares_list.append(Squares(index, str(i), 'yellow', z_position=30,
                                            alpha=0.5, font=('Avenir Next', 18),
                                            text_anchor_point=(-1.1, 1.2)))
          self.gui.add_numbers(squares_list) 
      else:
         self.indexes = np.zeros(self.board.shape, dtype=int)
         
    def box_positions(self):
      # positions of all objects for all devices
        x, y, w, h = self.gui.grid.bbox    
        position_dict = {
        'ipad13_landscape': {'rackscale': 0.9,
        'button1': (w+20, 0), 'button2': (w+20, h/21), 'button3': (w+150, h/21),
        'button4': (w+20, 3 *h/21), 'button5': (w+150, 3*h/21),
        'button6': (w+20, 4 *h/21), 'button7': (w+150, 0), 'button8': (w+20, 5*h/21),
        'button9': (w+150, 5*h/21),   'button10': (w+250, 5*h/21),
        'box1': (w+5, 2*h/3-6), 'box2': (w+5, 6*h/21), 'font': ('Avenir Next', 15)},                                         

        'ipad_landscape': {'rackscale': 0.9,
        'button1': (w+20, 0), 'button2': (w+20, h/21), 'button3': (w+150, h/21),
        'button4': (w+20, 3*h/21), 'button5': (w+150, 3*h/21),
        'button6': (w+20, 4*h/21), 'button7': (w+150, 0), 'button8': (w+20, 5*h/21),
        'button9': (w+150, 5*h/21),   'button10': (w+250, 5*h/21),
        'box1': (w+5, 2*h/3-6), 'box2': (w+5, 6*h/21), 'font': ('Avenir Next', 15)}
        }        
        try:
           self.posn = SimpleNamespace(**position_dict[self.gui.device])
        except (KeyError):
           raise KeyError('Portrait mode  or iphone not supported')
           
    def add_boxes(self):
      """ add non responsive decoration boxes"""
      x, y, w, h = self.gui.grid.bbox 
      tsize = self.posn.rackscale * self.gui.gs.SQ_SIZE
      self.wordsbox = self.gui.add_button(text='', title='Words', 
                          position=self.posn.box1, 
                          min_size=(5 * tsize+10, tsize+10), 
                          fill_color='black')
      self.gui.set_props(self.wordsbox, font=('Courier New', 12))
      self.gridbox = self.gui.add_button(text='', title='Grid', 
                          position=self.posn.box2, 
                          min_size=(2* tsize+10, tsize+10), 
                          fill_color='black')
      self.gui.set_props(self.gridbox, font=('Courier New', 12))
                
    def set_buttons(self):
      """ install set of active buttons """ 
      x, y, w, h = self.gui.grid.bbox       
      button = self.gui.set_enter('Quit', position=self.posn.button7,
                                  stroke_color='black', fill_color='pink',
                                  color='black', font=self.posn.font)   
      
      button = self.gui.add_button(text='Fill bottom', title='', position=self.posn.button2,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='yellow',
                                   color='black', font=self.posn.font)
      button = self.gui.add_button(text='Fill right', title='', position=self.posn.button3,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='yellow',
                                   color='black', font=self.posn.font)
      button = self.gui.add_button(text='Copy Text', title='', position=self.posn.button4, 
                                   min_size=(80, 32), reg_touch=True,
                                   stroke_color='black', fill_color='orange',
                                   color='black', font=self.posn.font) 
      button = self.gui.add_button(text='Copy grid', title='', position=self.posn.button5,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='orange',
                                   color='black', font=self.posn.font)
      button = self.gui.add_button(text='Copy both', title='', position=self.posn.button6,
                                   min_size=(230, 32), reg_touch=True,
                                   stroke_color='black', fill_color='orange',
                                   color='black', font=self.posn.font)                 
      button = self.gui.add_button(text='Clear', title='', position=self.posn.button1,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='pink',
                                   color='black', font=self.posn.font)                 
      self.letters = self.gui.add_button(text='Add letters', title='', position=self.posn.button8,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='cyan',
                                   color='black', font=self.posn.font)
      self.direction = self.gui.add_button(text='Across', title='', position=self.posn.button9,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='cyan',
                                   color='black', font=self.posn.font)      
      self.multi_character = self.gui.add_button(text='Indexes', title='', position=self.posn.button10,
                                   min_size=(100, 32), reg_touch=True,
                                   stroke_color='black', fill_color='cyan',
                                   color='black', font=self.posn.font)                                          

    def create_grid(self):
      """ create string represention of board
          slashes separate each character
      """
      self.lines = []
      for r in range(self.sizey):
        line = "'"
        for c in range(self.sizex):
          i = self.indexes[r, c]
          char = self.board[r, c]
          if i != 0 and char != ' ':
             item = str(i) + char
          elif i != 0:
             item = str(i)
          else:
             item = char       
          line = line + item + '/'
          
        line = line[:-1] + "'\n" 
        self.lines.append(line)
      
      # remove last \n
      self.lines[-1] = self.lines[-1].rstrip()
      self.gui.set_text(self.gridbox, ''.join(self.lines))
                       
    def get_player_move(self, board=None):
      """Takes in the user's input and performs that move on the board,
      returns the coordinates of the move
      Allows for movement over board"""
      
      move = LetterGame.get_player_move(self, self.board)
      
      # deal with buttons. each returns the button text    
      if move[0] < 0 and move[1] < 0:
          return (None, None), self.gui.gs.buttons[-move[0]].text, None 
          
      point = self.gui.gs.start_touch - gs.GRID_POS
      # touch on board
      # Coord is a tuple that can support arithmetic
      rc_start = Coord(self.gui.gs.grid_to_rc(point))
      
      if self.check_in_board(rc_start):
          rc = Coord(move)
          return rc, self.get_board_rc(rc, self.board), rc_start
                             
      return (None, None), None, None
       
    def process_turn(self, move, board):
      """ process the turn
      move is coord, new letter, selection_row
      """
      if move:
        coord, letter, origin = move
            
        if letter == 'Quit':
          self.gui.gs.close()
          sys.exit() 
          return 0
          
        elif letter == 'Clear':
           self.board = np.full((self.sizey, self.sizex), ' ')
           self.create_grid()
           self.gui.update(self.board)
           
        elif letter == 'Copy Text':
           clipboard.set('Puzzle:\n' + '\n'.join(self.words))
           self.gui.set_message('Data copied')   
        
        elif letter == 'Fill bottom':
          self.board[np.fliplr(np.flipud(self.board.copy()))=='#'] = '#'
          self.gui.update(self.board)
          self.create_grid()
        
        elif letter == 'Fill right':
           self.board[np.fliplr(self.board.copy())=='#'] = '#'     
           self.gui.update(self.board)
           self.create_grid()
           
        elif letter == 'Copy grid':
           self.create_grid()
           clipboard.set('Puzzle_frame:\n' + ''.join(self.lines))
           self.gui.set_message('Data copied')   
                   
        elif letter == 'Copy both':
           self.create_grid()
           msg = 'Puzzle:\n' + '\n'.join(self.words) + '\nPuzzle_frame:\n' + ''.join(self.lines)
           clipboard.set(msg)
           self.gui.set_message('Data copied') 
           
        elif letter == 'Across' or letter == 'Down':
           self.direction_mode = not self.direction_mode
           self.gui.set_text(self.direction, 'Down' if self.direction_mode else 'Across')     
           self.gui.set_props(self.direction, fill_color='lightblue' if self.direction_mode else 'cyan')     
                            
        elif letter == 'Indexes':
           self.index_mode = not self.index_mode           
           self.gui.set_props(self.multi_character, fill_color='lightblue' if self.index_mode else 'cyan')    
            
        elif letter == 'Add letters':
           self.letters_mode = not self.letters_mode
           self.gui.set_props(self.letters, fill_color = 'red' if self.letters_mode else 'cyan')       
           
        elif letter != '':  # valid selection
          try:
              cell = self.get_board_rc(origin, self.board)
              if not self.letters_mode and not self.gui.long_touch:
                  self.board_rc(origin, self.board, '#' if cell == ' ' else ' ')  
              else:
                try:
                   letter = dialogs.input_alert('Enter 1 or more letters')  
                except (KeyboardInterrupt):
                  return
                if letter:     
                  if self.index_mode and letter.isnumeric():
                    self.indexes[origin] = int(letter)
                    self.gui.add_numbers([Squares(origin, str(letter), 'yellow', z_position=30,
                                        alpha=0.5, font=('Avenir Next', 18),
                                        text_anchor_point=(-1.1, 1.2))], clear_previous=False)
                  elif len(letter) == 1:
                      self.board_rc(origin, self.board, letter)
                  else:             
                    for index, l in enumerate(letter):
                      
                      if self.direction_mode:                 
                        self.board_rc(origin + (index, 0), self.board, l.lower() )
                      else:
                        self.board_rc(origin + (0, index), self.board, l.lower() )
                      
              self.create_grid()   
              self.gui.update(self.board)       
          except (IndexError):
            pass 
                        
    def save(self):
      np.save(savefile, self.board) 
      np.save(savefile + '_indexes', self.indexes)
          
    def load(self):
      response = dialogs.alert('Load temporary file?', '', 'YES', 'NO', hide_cancel_button=True)
      if response == 1:
        try:
          self.board = np.load(savefile + '.npy')      
          self.indexes = np.load(savefile + '_indexes.npy')
        except (Exception) as e:
          print(e)    
        
    def run(self):
      self.create_grid()   
      self.gui.update(self.board)      
      while True:
        move = self.get_player_move()
        end = self.process_turn(move, self.board)
        self.save()
        if end == 0:
          break
      
    def filter(self, sort_alpha=True, max_length=None, min_length=None, sort_length=True, remove_numbers=False):
      
      words = self.all_text
      if max_length:
         words = [word for word in words if len(word) < max_length]
      if min_length:
         words = [word for word in words if len(word) > min_length]
      if remove_numbers:
          self.all_text = [word for word in words if word.isalpha()]
            
      # sort by length then by alphabet      
      if sort_alpha:
         words.sort() # sorts normally by alphabetical order
      if sort_length:
         words.sort(key=len)
      try:
         self.gui.set_text(self.wordsbox, self.format_cols(words, columns=4, width=12))
      except:
        pass
      self.words = words 
        
        
def main():
    all_assets = photos.get_assets()
    asset = photos.pick_asset(assets=all_assets)
    if asset is not None:
       all_text_dict= text_ocr(asset)
    else:
      all_text = []
    sort_by_postion(all_text_dict)
    
    all_text = list(all_text_dict.values())
    ocr = OcrCrossword(all_text)
    if all_text:
       ocr.filter(sort_alpha=False, max_length=None, min_length=None, sort_length=False, remove_numbers=False)
    ocr.run()
    
if __name__ == '__main__':
    main()
















