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
from time import sleep
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
    
    def draw_rectangles(self, rectangles, **kwargs):
        W, H = self.sizex, self.sizey
        for rect in rectangles:
          x, y, w, h = rect
          x1, y1 = x+w, y+h                 
          box = [self.gui.gs.rc_to_pos(H-y*H-1, x*W), 
                 self.gui.gs.rc_to_pos(H-y1*H-1, x*W), 
                 self.gui.gs.rc_to_pos(H-y1*H-1, x1*W), 
                 self.gui.gs.rc_to_pos(H-y*H-1, x1*W), 
                 self.gui.gs.rc_to_pos(H-y*H-1, x*W)]                                                  
          self.gui.draw_line(box, **kwargs)
          
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
        'button12': (w+250, 3*h/21),   'button13': (w+250, 2*h/21),  'button14': (w+250, 1*h/21),
        'box1': (w+5, 2*h/3-6), 'box2': (w+5, 6*h/21),  'box3': (w+105, 75),'font': ('Avenir Next', 15)},                                         

        'ipad_landscape': {'rackscale': 0.9,
        'button1': (w+20, 0), 'button2': (w+20, h/21), 'button3': (w+150, h/21),
        'button4': (w+20, 3*h/21), 'button5': (w+100, 3*h/21),
        'button6': (w+20, 4*h/21), 'button7': (w+150, 0), 'button8': (w+20, 5*h/21),
        'button9': (w+150, 5*h/21),   'button10': (w+250, 5*h/21), 'button11': (w+250, 4*h/21),
        'button12': (w+250, 3*h/21),   'button13': (w+250, 2*h/21),  'button14': (w+250, 1*h/21),
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
      self.gui.add_button(text='Recognise Crossword', position=self.posn.button14,
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
             
        elif letter == 'Recognise Crossword':
           if self.image_mode:
             self.recognise_crossword() 
              
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
                  #if self.scale >= 1.0:
                  self.defined_area = (x, y, w, h)
                  #else:
                  #  self.defined_area = ((y, x), (w, h)
                  
                  
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
            filename, self.scale, props = recognise.convert_to_png(self.asset)
            self.gui.set_message(f'{props}')
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
             #recognise.sort_by_position(all_text_dict, max_y=None)
             self.all_text = list(all_text_dict.values())
             self.draw_rectangles(list(self.all_word_dict))
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
            
    def split_defined_area(self, N=5):
      # split defined area into N x N overlapping areas
      # d defines amount of overlap
     
          x, y, w, h = self.defined_area         
          d = w / (N + 4) # overlap          
          subrects = []
          for i in range(N * N):
            div, mod = divmod(i, N)
            subrects.append((x + mod * (w / N) - d * (mod != 0), 
                             y + div * (h / N) - d * (div != 0), 
                             w / N + d,
                             h / N + d))
          return subrects
          
    def find_rects_in_area(self, subrect):
            """ find all rectangles in smaller area 
            then filter thos rectangles to remove outsize or undersize items
            """
            
            rects, bboxes  = recognise.rectangles(self.asset, subrect)
            
            #get areas and aspect of each rectangle
            areas = np.array([round(w * h, 3) for x, y, w, h in rects])
            aspects = np.array([round(h / w, 2) for x, y, w, h in rects])
            
            hist_area = np.histogram(areas, bins=10)
            hist_aspect = np.histogram(aspects, bins=10)
            
            area_span = np.linspace(min(areas), max(areas), num=10)
            d_area= np.digitize(areas, area_span, right=True)
            
            aspect_span = np.linspace(min(aspects), max(aspects), num=10)
            d_apect = np.digitize(aspects, aspect_span, right=True)
            
            #find greatest number of items  in area
            # TODO should we also use aspect?
            print('digitized', d_area)
            unique, counts = np.unique(d_area, return_counts=True)
            print('unique, counts', unique, counts)
            most = unique[np.argmax(counts)]

            filtered = [r for idx, r in enumerate(rects) if d_area[idx] == most ]
            print('filtered', len(filtered))
            
            params = {'line_width': 2, 'stroke_color': 'red', 'z_position':1000}
            self.draw_rectangles(filtered, **params)
            return filtered
            
    def filter_total(self, total_rects):
          total_rects = np.round(np.array(total_rects), decimals=2)
          print(len(total_rects))
          total_rects = np.unique(total_rects, axis=0)
          print(len(total_rects))
          inds = np.lexsort((total_rects[:,3],total_rects[:,2],total_rects[:,1],total_rects[:,0]))  
          total_rects = total_rects[inds]
          # now remove duplicate x,ys remove smaller of the duplicates
          diffs = np.diff(total_rects, axis=0)
          zero = np.zeros_like(diffs[:,0])   
          bigger = np.logical_or(diffs[:,2] > 0, 
                                 diffs[:,3] > 0)
          duplicates = ~np.logical_or(np.isclose(diffs[:,1], zero, atol=.01), 
                                      np.isclose(diffs[:,0], zero, atol=.01))
          idx = np.where(duplicates)
          is_bigger = bigger[idx]
          [print(diff) for diff in diffs]
          print(idx, is_bigger)
          total_rects = [tuple(item) for item in total_rects]
          return total_rects
      
    def recognise_crossword(self):
      """ process crossword grid """
      if self.defined_area:
          #subdivide selected area and find rectangles 
          total_rects = []
          for subrect in self.split_defined_area(N=5):
              total_rects.extend(self.find_rects_in_area(subrect))           
            
          total_rects = self.filter_total(total_rects)
          
          self.gui.remove_lines(z_position=1000)
          params = {'line_width': 5, 'stroke_color': 'red', 'z_position':1000}
          self.draw_rectangles(total_rects, **params)
          [print(x,y,w*h) for x,y,w,h in total_rects]
              
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

































