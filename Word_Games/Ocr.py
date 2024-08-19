# attempt to use text recognition to read a filled crossword puzzle
# problems with recognising single letters
#can use this to read lists of words though.
import photos
import objc_util
import os
import sys
import clipboard
import dialogs
from queue import Queue
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from types import SimpleNamespace
from gui.gui_interface import Gui, Coord
from Word_Games.Letter_game import LetterGame
from scene import *
import gui.gui_scene as gs
import numpy as np
savefile= 'Ocr_save.txt'

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
  img_data = objc_util.ns(asset.get_image_data().getvalue())

  with objc_util.autoreleasepool():
    req = VNRecognizeTextRequest.alloc().init().autorelease()
    #print(req.supportedRecognitionLanguagesAndReturnError_(None))
    req.setRecognitionLanguages_(['zh-Hant', 'en-US'])
    req.setRecognitionLevel_(0) # accurate
    req.setCustomWords_([x for x in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')]) # individual letters

    handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
    success = handler.performRequests_error_([req], None)
    
    if success:
        all_text = {}
        for result in req.results():
          cg_box = result.boundingBox()
          x, y = cg_box.origin.x, cg_box.origin.y
          w, h = cg_box.size.width, cg_box.size.height
          all_text[x, y, w, h] = str(result.text())
        return all_text

class OcrCrossword(LetterGame):
    def __init__(self, all_text_dict):
        self.load() # attempt to load temp file
        self.SIZE = self.get_size()        
        self.q = Queue()
        self.log_moves = False
        self.gui = Gui(self.board, Player())
        self.gui.gs.q = self.q 
        self.words = []
        self.letters_mode = False
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui(grid_fill='black')
        self.board = np.array(self.board)
        self.board[self.board == '-'] = ' ' # replace '-' by ' '
        self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.sizex]
        self.gui.build_extra_grid(self.sizex, self.sizey, grid_width_x=1, grid_width_y=1,
                              color='black', line_width=1)
        self.all_text_dict = all_text_dict
        self.x, self.y, self.w, self.h = self.gui.grid.bbox
        self.gui.clear_messages()
        self.box_positions()
        self.set_buttons()
        self.add_boxes()
        
    def box_positions(self):
      # positions of all objects for all devices
        x, y, w, h = self.gui.grid.bbox    
        position_dict = {
        'ipad13_landscape': {'rackpos': (10, 200), 'rackscale': 0.9, 'rackoff': h/8, 
        'button1': (w+20, 0), 'button2': (w+20, h/21), 'button3': (w+150, h/21),
        'button4': (w+20, 3 *h/21), 'button5': (w+150, 3*h/21),
        'button6': (w+20, 4 *h/21), 'button7': (w+150, 0), 'button8': (w + 20, 5*h/21),
        'box1': (w+5, 2*h/3-6), 'box2': (w+5, 6*h/21), 'box3': (w+5, 2*h/3),
        'box4': (w+5, h-50), 'font': ('Avenir Next', 10) },
                                           
        'ipad13_portrait': {'rackpos': (50-w, h+50), 'rackscale': 0.9, 'rackoff': h/8,
        'button1': (w/2, h+200), 'button2': (w/2, h+50), 'button3': (w/2, h+250),
        'button4': (w/2, h+100), 'button5': (w/2, h+150),
        'box1': (45, h+h/8+45), 'box2': (45, h+45), 'box3': (2*w/3, h+45),
        'box4': (2*w/3, h+200), 'font': ('Avenir Next', 24) },
        
        'ipad_landscape': {'rackpos': (10, 200), 'rackscale': 1.0, 'rackoff': h/8,
        'button1': (w+10, h/6), 'button2': (w+230, h/6), 'button3': (w+120, h/6),
        'button4': (w+230, h/6-50), 'button5': (w+120, h/6-50),
        'box1': (w+5, 200+h/8-6), 'box2': (w+5, 200-6), 'box3': (w+5, 2*h/3),
        'box4': (w+5, h-50), 'font': ('Avenir Next', 20) },
        
        'ipad_portrait': {'rackpos': (50-w, h+50), 'rackscale': 1.0, 'rackoff': h/8,
        'button1': (9*w/15, h+190), 'button2': (9*w/15, h+30), 'button3': (9*w/15, h+150),
        'button4': (9*w/15, h+70), 'button5': (9*w/15, h+110),
        'box1': (45,h+h/8+45), 'box2': (45, h+45),'box3': (3*w/4, h+35),
        'box4': (3*w/4, h+160), 'font': ('Avenir Next', 20)},
        
        'iphone_landscape': {'rackpos': (10, 200), 'rackscale': 1.5, 'rackoff': h/4,
        'button1': (w+10, h/6), 'button2': (w+230, h/6), 'button3': (w+120, h/6),
        'button4': (w+230, h/6-50), 'button5': (w+120, h/6-50),
        'box1': (w+5, 200+h/8-6), 'box2': (w+5, 200-6), 'box3': (w+5, 2*h/3),
        'box4': (w+5, h-50), 'font': ('Avenir Next', 15) },
        
        #'iphone_landscape': {'rackpos': (10, 0), 'rackscale': 1.5, 'rackoff': h/4,
        #'button1': (w+5, h), 'button2': (w+300, h-50), 'button3': (w+300, h-100),
        #'button4': (w+300, h-150), 'button5': (w+300, h-200),
        # 'box1': (w+5, h/4-6), 'box2': (w+5, -6), 'box3': (w+5, h/2),
        # 'box4': (w+5, h), 'font': ('Avenir Next', 15)},
        
        #'iphone_portrait': {'rackpos': (10, 200), 'rackscale': 1.5, 'rackoff': h/8,
        #'button1': (w, h/6), 'button2': (w+250, h/6), 'button3': (w+140, h/6),
        #'button4': (w/2, h+100), 'button5': (w/2, h+150),
        #'box1': (5, h+h/8-6), 'box2': (5, h-6), 'box3': (5, h),
        #'box4': (5, h-50),  'font': ('Avenir Next', 15)}
        'iphone_portrait': {'rackpos': (50-w, h+50), 'rackscale': 1.5, 'rackoff': h/8,
        'button1': (9*w/15, h+190), 'button2': (9*w/15, h+30), 'button3': (9*w/15, h+150),
        'button4': (9*w/15, h+70), 'button5': (9*w/15, h+110), 
        'box1': (45,h+h/8+45), 'box2': (45, h+45),'box3': (3*w/4, h+35),
        'box4': (3*w/4, h+160), 'font': ('Avenir Next', 15)},
         }
        self.posn = SimpleNamespace(**position_dict[self.gui.device])
           
    def add_boxes(self):
      """ add non responsive decoration boxes"""
      x, y, w, h = self.gui.grid.bbox 
      tsize = self.posn.rackscale * self.gui.gs.SQ_SIZE
      self.wordsbox = self.gui.add_button(text='', title='Words', position=self.posn.box1, 
                          min_size=(5 * tsize+10, tsize+10), 
                          fill_color='black')
      self.gui.set_props(self.wordsbox, font=('Courier New', 12))
      self.gridbox = self.gui.add_button(text='', title='Grid', position=self.posn.box2, 
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

    def create_grid(self):
      """ create string represention of board
          slashes separate each character
      """
      self.lines = ["'" + '/'.join(self.board[i, :]) + "'\n" 
                    for i in range(self.board.shape[0])]
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
          return 0
          
        elif letter == 'Clear':
           self.board = np.full((self.sizey, self.sizex), ' ')
           self.create_grid()
           self.gui.update(self.board)
           
        elif letter == 'Copy Text':
           clipboard.set('Puzzle:\n' + '\n'.join(self.words))
        
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
           try:
              os.remove(savefile)
           except OSError:
                pass
           
        elif letter == 'Copy both':
           self.create_grid()
           msg = 'Puzzle:\n' + '\n'.join(self.words) + 'Puzzle_frame:\n' + ''.join(self.lines)
           clipboard.set(msg)
           try:
              os.remove(savefile)
           except OSError:
                pass
           
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
                  for index, l in enumerate(letter):
                     self.board_rc(origin + (0, index), self.board, l.lower() )
              self.create_grid()   
              self.gui.update(self.board)       
          except (IndexError):
            pass 
                        
    def save(self): 
      with open(savefile, 'w') as f:
        f.write(''.join(self.lines))
          
    def load(self):
    	response = dialogs.alert('Load temporary file?', '', 'YES', 'NO', hide_cancel_button=True)
    	if response == 1:
	      try:
	        with open(savefile, 'r') as f:
	          lines = f.read()
	        lines = lines.split('\n')
	        self.lines = lines
	        rows = len(self.lines)
	        cols = (len(self.lines[0])-1)//2
	        self.board = np.full((rows, cols), ' ') 
	        for i, line in enumerate(lines):
	          row = line.strip("'").split('/')
	          self.board[i,:] = np.array(row)
	        
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
      
    def filter(self, max_length=None, min_length=None, sort_length=True, remove_numbers=False):
      if max_length:
         self.all_text_dict = {k:v for k, v in self.all_text_dict.items() if len(v) < max_length}
      if min_length:
         self.all_text_dict = {k:v for k, v in self.all_text_dict.items() if len(v) > min_length}
      if remove_numbers:
          self.all_text_dict = {k:v for k, v in self.all_text_dict.items() if v.isalpha() }
      
      
      # sort by length then by alphabet
      words = list(self.all_text_dict.values())

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
       all_text = text_ocr(asset)
    else:
      all_text = []
    ocr = OcrCrossword(all_text)
    if all_text:
       ocr.filter(max_length=None, min_length=None, sort_length=True, remove_numbers=True)
    ocr.run()
    
if __name__ == '__main__':
    main()










