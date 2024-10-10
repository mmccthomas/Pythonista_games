# Use VisionKit text recognition to read an image
# containing text.
# Provide a grid to generate crossword frame as text
import photos
import objc_util
import os
import sys
import clipboard
import dialogs
import traceback
from queue import Queue
import pandas as pd
from matplotlib import pyplot

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from types import SimpleNamespace
from gui.gui_interface import Gui, Coord, Squares
from Word_Games.Letter_game import LetterGame
from ui import LINE_CAP_ROUND
from scene import *
import gui.gui_scene as gs
import numpy as np
from PIL import Image
from io import BytesIO
import recognise
savefile= 'Ocr_save'




class Player():
  def __init__(self):
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  ='abcdefghijklmnopqrstuvwxyz0123456789. '
    self.PIECES = [f'../../gui/tileblocks/{k}.png' for k in self.PIECE_NAMES[:-2]]
    self.PIECES.append(f'../../gui/tileblocks/@.png')
    self.PIECES.append(f'../../gui/tileblocks/_.png')
    self.PLAYERS = None
 

class OcrCrossword(LetterGame):
    def __init__(self, all_text, board=None, board_size=None, asset=None):
        self.load() # attempt to load temp file
        self.SIZE = self.get_size(board=board, board_size=board_size)     
        self.asset = asset   
        self.q = Queue()
        self.log_moves = False
        self.gui = Gui(self.board, Player())
        self.gui.set_grid_colors(grid='black') # background is classic board
        self.gui.gs.q = self.q 
        self.words = []
        self.letters_mode = False
        self.direction_mode = False
        self.index_mode = False
        self.image_mode = False
        self.defined_area = None
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui()
        self.board = np.array(self.board)
        self.board[self.board == '-'] = ' ' # replace '-' by ' '
        self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
        self.gui.build_extra_grid(self.sizex, self.sizey, 
                                  grid_width_x=1, grid_width_y=1,
                                  color='black', line_width=1)
        self.all_text = all_text
        self.x, self.y, self.w, self.h = self.gui.grid.bbox
        self.gui.update(self.board)
        self.gui.clear_messages()
        self.box_positions()
        self.set_buttons()
        self.add_boxes()
        self.add_indexes()
        
        
    def get_size(self, board, board_size):
      if board is not None:
        response = dialogs.alert('Use decoded board?', '', 'YES', 'NO', hide_cancel_button=True)
        if response == 1:
          try:
            self.board = np.char.lower(board)            
          except (Exception) as e:
            print(e)      
      super().get_size(board_size)
    
    def draw_rectangles(self, rectangles):
        W, H = self.sizex, self.sizey
        for rect in rectangles:
          # bl, br, tl, tr
          box = [self.gui.rc_to_pos((H - p[1] * H - 1, p[0] * W)) for p in rect]        
          #box = [self.gui.rc_to_pos((p.y * H - 1, p.x * W)) for p in rect]        
          self.gui.draw_line(box)
          
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
        'button1': (w+20, 0), 'button2': (w+20, h/21), 'button3': (w+130, h/21),
        'button4': (w+20, 3 *h/21), 'button5': (w+110, 3*h/21),
        'button6': (w+20, 4 *h/21), 'button7': (w+130, 0), 'button8': (w+20, 5*h/21),
        'button9': (w+150, 5*h/21),   'button10': (w+250, 5*h/21), 'button11': (w+250, 4*h/21),
        'button12': (w+250, 3*h/21),   'button13': (w+250, 2*h/21),
        'box1': (w+5, 2*h/3-6), 'box2': (w+5, 6*h/21),  'box3': (w+105, 75),'font': ('Avenir Next', 15)},                                         

        'ipad_landscape': {'rackscale': 0.9,
        'button1': (w+20, 0), 'button2': (w+20, h/21), 'button3': (w+150, h/21),
        'button4': (w+20, 3*h/21), 'button5': (w+100, 3*h/21),
        'button6': (w+20, 4*h/21), 'button7': (w+150, 0), 'button8': (w+20, 5*h/21),
        'button9': (w+150, 5*h/21),   'button10': (w+250, 5*h/21), 'button11': (w+250, 4*h/21),
        'button12': (w+250, 3*h/21),
        'box1': (w+5, 2*h/3-6), 'box2': (w+5, 6*h/21), 'box3': (w+50, 75), 'font': ('Avenir Next', 12)}
        }        
        try:
           self.posn = SimpleNamespace(**position_dict[self.gui.device])
        except (KeyError):
           raise KeyError('Portrait mode  or iphone not supported')
           
    def add_boxes(self):
      """ add non responsive decoration boxes"""
      x, y, w, h = self.gui.grid.bbox 
      tsize = self.posn.rackscale * self.gui.gs.SQ_SIZE
      #self.wordsbox = self.gui.add_button(text='', title='Words', 
      #                    position=self.posn.box1, 
      #                    min_size=(5 * tsize+10, tsize+10), 
      #                    fill_color='black')
      #self.gui.set_props(self.wordsbox, font=('Courier New', 12))
      self.gridbox = self.gui.add_button(text='', title='Grid', 
                          position=self.posn.box2, 
                          min_size=(2* tsize+10, tsize+10), 
                          fill_color='black')
      self.gui.set_props(self.gridbox, font=('Courier New', 8))
      self.wordsbox = self.gui.scroll_text_box(x=self.posn.box3[0], 
                                               y=self.posn.box3[1],
                                               width=300, height=200,
                                               font=('Courier New', 12))
      
    def set_buttons(self):
      """ install set of active buttons
      Note: **{**params,'min_size': (80, 32)} overrides parameter
       """ 
      x, y, w, h = self.gui.grid.bbox       
      params = {'title': '', 'stroke_color': 'black', 'font': self.posn.font, 'reg_touch': True, 'color': 'black', 'min_size': (100, 32)}
      self.gui.set_enter('Quit', position=self.posn.button7,
                         fill_color='pink', **params)         
      self.gui.add_button(text='Fill bottom', position=self.posn.button2,
                          fill_color='yellow', **{**params,'min_size': (80, 32)})
      self.gui.add_button(text='Fill right', position=self.posn.button3,
                          fill_color='yellow', **params)                                                                   
      self.gui.add_button(text='Copy Text', position=self.posn.button4, 
                          fill_color='orange', **{**params,'min_size': (80, 32)})                                                                     
      self.gui.add_button(text='Copy grid', position=self.posn.button5,
                          fill_color='orange', **{**params,'min_size': (80, 32)})
      self.gui.add_button(text='Copy both', position=self.posn.button6,
                          fill_color='orange', **{**params,'min_size': (170, 32)})                 
      self.gui.add_button(text='Clear', position=self.posn.button1,
                          fill_color='pink', **params)                 
      self.letters = self.gui.add_button(text='Add letters', position=self.posn.button8,
                                         fill_color='cyan', **params)
      self.direction = self.gui.add_button(text='Across', position=self.posn.button9,
                                           fill_color='cyan', **params)      
      self.multi_character = self.gui.add_button(text='Indexes', position=self.posn.button10,
                                                 fill_color='cyan', **params)           
      self.images = self.gui.add_button(text='Image Mode', position=self.posn.button11,
                                        fill_color='cyan', **params)     
      self.gui.add_button(text='Recognise Area', position=self.posn.button12,
                          fill_color='cyan', **params)   
      self.gui.add_button(text='Recognise Pieceword', position=self.posn.button13,
                          fill_color='cyan', **params)                                                                     

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
           if self.image_mode:
               self.enter_image_mode()
               
        elif letter == 'Image Mode':
           self.image_mode = not self.image_mode
           self.gui.set_props(self.images, fill_color = 'red' if self.image_mode else 'cyan')    
           self.enter_image_mode()   
           
        elif letter == 'Recognise Area':
           if self.image_mode:
             self.recognise_area()   
             
        elif letter == 'Recognise Pieceword':
           if self.image_mode:
             self.recognise_pieceword() 
              
        elif letter != '':  # valid selection
          try:
              cell = self.get_board_rc(origin, self.board)
              if self.image_mode:
                  """select defined area"""
                  def r2(x):
                    """ round and scale"""
                    return round(x, 2)/self.sizex
                    
                  st_y, st_x = origin # / self.sizex
                  #st_y = 1.0 - st_y
                  end_y, end_x = coord # / self.sizex
                  # find which way we drew the box
                  x, y = min(st_x, end_x), max(st_y, end_y)
                  x1, y1 = max(st_x, end_x), min(st_y, end_y)
                  
                  #end_y = 1.0 - end_y
                  box = [self.gui.gs.rc_to_pos(y, x), 
                         self.gui.gs.rc_to_pos(y1-1, x), 
                         self.gui.gs.rc_to_pos(y1-1, x1+1), 
                         self.gui.gs.rc_to_pos(y, x1+1), 
                         self.gui.gs.rc_to_pos(y, x)]                      
                  params = {'line_width': 4, 'line_cap_style': LINE_CAP_ROUND, 'stroke_color': 'blue', 'z_position':1000}
                  self.gui.remove_lines(z_position=1000)
                  self.gui.draw_line(box, **params)        
                  # calculate region of interest
                  # need x, y relative to original asset
                  # 0,0 is lower left, 1,1 is upper right
                  x, y = r2(x), r2(self.sizey - 1 - y)
                  x1, y1 = r2(x1+1), r2(self.sizey - y1)                  
                  # this is for square image
                  w = abs(x1-x)
                  h = abs(y-y1)
                  if self.scale >= 1.0:
                    self.defined_area = ((x, y), (w, h))
                  else:
                    self.defined_area = ((y, x), (y, x))
                  
                  
              elif not self.letters_mode and not self.gui.long_touch:
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
      if hasattr(self, 'rectangles'):
        self.draw_rectangles()
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
         msg = self.format_cols(words, columns=4, width=12)
         #self.gui.set_text(self.wordsbox, msg)
         self.wordsbox.text=msg
      except:
        print(traceback.format_exc())
      self.words = words 
        
    def enter_image_mode(self):
        if self.asset is not None:
            filename, self.scale = recognise.convert_to_png(self.asset)
            self.gui.add_image(filename)
            self.rects, self.bboxes  = recognise.rectangles(self.asset)
            self.draw_rectangles(self.bboxes)
            self.board[self.board == ' '] = '-'
            self.gui.update(self.board)  
            all_text_dict = recognise.text_ocr(self.asset)
            try:
                #board, board_size = recognise.sort_by_position(all_text_dict)    
                all_text = list(all_text_dict.values())
            except (AttributeError):
                all_text = []
                
    def recognise_area(self):
        '''recognise text in defined area'''
        if self.defined_area:
          all_text_dict = recognise.text_ocr(self.asset, self.defined_area)
          self.rects, self.bboxes  = recognise.rectangles(self.asset, self.defined_area)
          self.draw_rectangles(self.rects)
          try:
             self.all_text = list(all_text_dict.values())
             self.filter(sort_alpha=False, max_length=None, min_length=None, sort_length=False, remove_numbers=False)
          except (AttributeError):
            self.gui.set_message(f'No text found in {self.defined_area}')
            
    def recognise_pieceword(self):            
        '''recognise pieceword grid in defined area'''
        if self.defined_area:  
          self.rects, self.bboxes  = recognise.rectangles(self.asset, self.defined_area)
          self.draw_rectangles(self.rects)
          try:
             board = recognise.pieceword_sort(self.asset, None, self.rects)
             self.wordsbox.font = ('Courier', 30)
             self.wordsbox.text=board
             return board            
          except (AttributeError):
            self.gui.set_message(f'No text found in {self.defined_area}')
               
def main():
    
    all_assets = photos.get_assets()
    asset = photos.pick_asset(assets=all_assets)
    if asset is not None:
       all_text_dict= recognise.text_ocr(asset) #, rects2[9])
       all_text = list(all_text_dict.values())
    else:
      all_text = []
      all_text_dict = {}
    
    ocr = OcrCrossword(all_text, asset=asset, board_size='25 25')
    if all_text:
       ocr.filter(sort_alpha=False, max_length=None, min_length=None, sort_length=False, remove_numbers=False)
    ocr.run()
    
if __name__ == '__main__':
    main()




























