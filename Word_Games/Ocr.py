# attempt to use text recognition to read a filled crossword puzzle
# problems with recognising single letters
#can use this to read lists of words though.
import photos
import objc_util
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from gui.gui_interface import Gui
from Word_Games.Letter_game import LetterGame
from scene import *
import gui.gui_scene as gs
import numpy as np

VNImageRequestHandler = objc_util.ObjCClass('VNImageRequestHandler')
VNRecognizeTextRequest = objc_util.ObjCClass('VNRecognizeTextRequest')
class Player():
  def __init__(self):
    
    #images = slice_image_into_tiles('Letters_blank.jpg', 6, 5)
    characters ='__abcd_efghijklmnopqrstuv wxyz*'
    #IMAGES ={characters[j]:pil2ui(images[j]) for j in range(1,30)}
    # test
    #for d,i in IMAGES.items():
    # print(d), i.show()
    self.PLAYER_1 = ' '
    self.PLAYER_2 = '@'
    self.EMPTY = ' '
    self.PIECE_NAMES  ='abcdefghijklmnopqrstuvwxyz0123456789. '
    self.PIECES = [f'../gui/{k}.png' for k in self.PIECE_NAMES[:-2]]
    self.PIECES.append(f'../gui/@.png')
    self.PIECES.append(f'../gui/_.png')
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
        self.SIZE = self.get_size('13,13')         
        self.gui = Gui(self.board, Player())
        self.gui.setup_gui(grid_fill='black')
        self.all_text_dict = all_text_dict
        self.x, self.y, self.w, self.h = self.gui.grid.bbox
        print(self.gui.grid.bbox)
        
    def scale_box(self, box, offset):
      scaled_x = (box[0] - offset[0]) * self.w * self.scale[0] * .5 + self.w/2
      scaled_y = (box[1] - offset[1]) * self.h * self.scale[1] * .5 + self.h/2
      scaled_w = box[2] * self.w
      scaled_h = box[3] * self.h
      return (scaled_x, scaled_y, scaled_w, scaled_h)
      
    def filter(self, max_length=None, min_length=None, sort_length=True, remove_numbers=False):
      if max_length:
         self.all_text_dict = {k:v for k, v in self.all_text_dict.items() if len(v) < max_length}
      if min_length:
         self.all_text_dict = {k:v for k, v in self.all_text_dict.items() if len(v) > min_length}
      if remove_numbers:
          self.all_text_dict = {k:v for k, v in self.all_text_dict.items() if v.isalpha() }
      boxes = np.array(list(self.all_text_dict.keys())) 
      
      # compute centres of each box
      x = boxes[:,0] + boxes[:,2] / 2 
      y = boxes[:,1] + boxes[:,3] / 2 
      centres = np.transpose(np.vstack((x,y)))
      # sort by length then by alphabet
      words = list(self.all_text_dict.values())

      #words.sort() # sorts normally by alphabetical order
      if sort_length:
         words.sort(key=len)
      try:
         self.gui.set_moves(self.format_cols(words, columns=2, width=10))
      except:
        pass
      for word in words:
        print(word)
      
      def reject_outliers(data, m=2):
          return np.all(abs(data - np.median(data, axis=0)) < m * np.std(data, axis=0), axis=1)
          
      allow = reject_outliers(centres)     
      self.all_text_dict = {k:v for i, (k,v) in enumerate(self.all_text_dict.items()) if allow[i]}
      median = np.mean(centres[allow], axis=0)
      
      self.scale = 1.0 / np.ptp(centres[allow], axis=0)

      #print('offset', offset)
      self.all_text_dict = {self.scale_box(k, median):v for k,v in self.all_text_dict.items()}      
      
      
    def plot_chars(self):
      for box, letter in self.all_text_dict.items():
        t=ShapeNode(ui.Path.rect(0,0,box[2], box[3]), 
                   fill_color='clear',  position=(box[0], box[1]), 
                 stroke_color='white',
                  parent=self.gui.game_field)
        t=LabelNode(letter,  position=(box[0], box[1]), 
                    color='white',
                    parent=self.gui.game_field)
            
          
      
        
def main():
    all_assets = photos.get_assets()
    asset = photos.pick_asset(assets=all_assets)
    if asset is None:
        return
    all_text = text_ocr(asset)
    ocr = OcrCrossword(all_text)
    ocr.filter(max_length=None, min_length=None, sort_length=False, remove_numbers=True)
    ocr.plot_chars()
    
if __name__ == '__main__':
    main()
