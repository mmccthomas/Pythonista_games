import random
import console
import dialogs
from time import sleep
from queue import Queue
from PIL import Image
import ui
import photos
import io
from types import SimpleNamespace
from Letter_game import LetterGame, Player
import gui.gui_scene as gscene
from gui.gui_scene import Tile, BoxedLabel
from scene import Texture, Point, LabelNode
from gui.gui_interface import Gui, Squares
PUZZLELIST = "pieceword.txt"


class PieceWord(LetterGame):
  
  def __init__(self):
    LetterGame.__init__(self)
    self.first_letter = False
    self.load_words_from_file(PUZZLELIST)
    self.select_list()
    # self.gui.build_extra_grid(5, 7, grid_width_x=3, grid_width_y=3, color='white', line_width=2)
    self.image_name = Image.open(self.image)
    vsize, hsize = self.image_dims
    self.images = self.slice_image_into_tiles(self.image_name, img_count_h=hsize, img_count_v=vsize)
    x, y, w, h = self.gui.grid.bbox    
    
    # positions of all objects for all devices
    position_dict = {
    'ipad13_landscape': {'rackpos': (10, 130), 'rackscale':.25, 'rackoff': h/8, 
    'button1': (w+20, h/6), 'button2': (w+250, h/6), 'button3': (w+140, h/6),
    'button4': (w+250, h/6-50), 'button5': (w+140, h/6-50),
    'box1': (w+5, 200+h/8-6), 'box2': (w+5, 200-6), 'box3': (w+5, 2*h/3),
    'box4': (w+5, h-50), 'font': ('Avenir Next', 24) },
                                       
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
    
    'iphone_portrait': {'rackpos': (50-w, h+50), 'rackscale': 1.5, 'rackoff': h/8,
    'button1': (9*w/15, h+190), 'button2': (9*w/15, h+30), 'button3': (9*w/15, h+150),
    'button4': (9*w/15, h+70), 'button5': (9*w/15, h+110),
    'box1': (45,h+h/8+45), 'box2': (45, h+45),'box3': (3*w/4, h+35),
    'box4': (3*w/4, h+160), 'font': ('Avenir Next', 15)},
     }
    self.gui.set_pause_menu({'Continue': self.gui.dismiss_menu, 
                              'New ....': self.restart,
                              'Quit': self.quit})
    self.selection = self.select_list()
    self.posn = SimpleNamespace(**position_dict[self.gui.device])
    self.rack = self.display_rack()
    self.gui.set_moves('\n'.join(self.wordlist), position=(w+50, h/2))
    
    #self.gui.gs.IMAGES = {i:self.pil2ui(image) for i, image in enumerate(self.rack.values())}
    
    
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """     
    move = ''   
    while True:
      move = self.get_player_move(self.board)               
      move = self.process_turn( move, self.board) 
      if self.game_over():
        break           
    self.gui.set_message2('')
    self.gui.set_message('') 
    self.gui.set_prompt('')    
    sleep(2)
    self.finished = True
    self.gui.gs.show_start_menu()
    
  def select_list(self):
      '''Choose which category'''
      items = [s.capitalize() for s in self.word_dict.keys()]
      items = [item for item in items if not item.endswith('_text')]
      # return selection
      self.gui.selection = ''
      selection = ''
      prompt = ' Select category'
      while self.gui.selection == '':
        self.gui.input_text_list(prompt=prompt, items=items, position=(800, 0))
        while self.gui.text_box.on_screen:
          try:
            
            selection = self.gui.selection.lower()
          except (Exception) as e:
            print(e)
            print(traceback.format_exc())
        print(selection)   
        if len(selection) > 1:
          self.wordlist = self.word_dict[selection]
          if selection + '_text' in self.word_dict:
             self.table = self.word_dict[selection + '_text']
             self.image = self.wordlist[0]
             self.image_dims = [int(st) for st in self.wordlist[1].split(',')]
             self.solution = self.wordlist[2]
          self.wordlist = [word for word in self.table if word]
          self.gui.selection = ''
          return selection
        elif selection == "Cancelled_":
          return False
        else:
            return False
  
  def display_rack(self, y_off=0):
    """ display players rack
    y position offset is used to select player_1 or player_2
    """   
    parent = self.gui.game_field
    _, _, w, h = self.gui.grid.bbox        
    x, y = self.posn.rackpos
    y = y + y_off
    rack = {}
    sqsize = self.gui.gs.SQ_SIZE*3*self.posn.rackscale
    for n, tile in enumerate(self.images.values()):   
      if n == self.sizex * self.sizey:
        break 
      r = n // self.sizex
      c = n % self.sizex
      
      sqsize = self.gui.gs.SQ_SIZE  
        
      t = Tile(Texture(self.pil2ui(tile)), r,  c, sq_size=sqsize, dims=(self.gui.gs.DIMENSION_Y,self.gui.gs.DIMENSION_X) )   
      t.row, t.col = r, c   
      rack[(r,c)] = t  
      t.number = n
      
      parent.add_child(t)  
      
      for i in range(self.sizey*3) : 
        t = LabelNode(str(i+1), parent=parent )   
        t.position = (w+10, h -20 - i *sqsize/3) #- sqsize*2//3)
    return rack          
          
  def get_size(self):
    LetterGame.get_size(self, '5, 7')
    
  def load_words(self, word_length, file_list=PUZZLELIST):
    return
    LetterGame.load_words(self, word_length, file_list=file_list)
     
  def initialise_board(self):    
    pass
      
  def pil2ui(self,imgIn):
    """ import a photo library image and convert to jpg in memory """
    with io.BytesIO() as bIO:
      imgIn.save(bIO, 'PNG')
      imgOut = ui.Image.from_data(bIO.getvalue())
    del bIO
    return imgOut
  
  def slice_image_into_tiles(self, in_image, img_count_h, img_count_v=1):
    """ take an image name or image object, 
    crop into tile and add to dictionary"""
    
    if isinstance(in_image, str):
      img = Image.open(in_image)
    else:
      img = in_image
    w, h = img.size  # get the size of the big image
    w /= img_count_h      # calculate the size of smaller images
    h /= img_count_v
    index = 0
    images = {}
    try:
      for y in range(img_count_v) :
        for x in range(img_count_h):
          index += 1
          img2 = img.crop((x * w, y * h, (x + 1) * w, (y + 1) * h))
          images.setdefault(index, img2)
    except(OSError) as e:
      logger.info(f'image load error {e}')
    return images      
    
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    move = LetterGame.get_player_move(self, self.board)
    
    if move[0] == (-1, -1):
       return (None, None), 'Enter', None # pressed enter button
      
    point = self.gui.gs.start_touch - gscene.GRID_POS               
    # touch on board 
    rc_start = self.gui.gs.grid_to_rc(point)
    r_start, c_start = rc_start
    if self.check_in_board(rc_start):
        r, c  = move[-2]
        t = self.rack[(r_start, c_start)]         
        return (r, c), t.number, rc_start                        
    return (None, None), None, None   
       
  def process_turn(self, move, board):
    """ process the turn
    move is coord, new letter, selection_row
    """ 
    rack = self.rack 
    if move:
      coord, letter, origin = move
      r,c = coord
      
      self.gui.set_message(f'{origin}>{coord}={letter}')  
      if coord == (None, None):
        return 0
        
      elif letter == 'Finish':
        return 0 
      elif letter != '':
        # swap tiles 
        # take tile at end coord and move it to start coord
        tile_move = self.rack[origin]        
        tile_existing = self.rack[coord]
        tile_move.set_pos(coord)  
        tile_existing.set_pos(origin)               
                  
        # now update rack        
        self.rack[origin] = tile_existing
        self.rack[coord] = tile_move                          
    return 0               
  
  def game_over(self):
    # compare placement with solution    
    state = ''
    for r in range(self.sizey):
      for c in range(self.sizex):
        no = f'{self.rack[(r, c)].number:2}'
        state += no
    print(state)
    print()
    if state.strip() == self.solution:
      self.gui.set_message('Game over')
      return True      
    return False    
      
  def restart(self):
    self.gui.gs.close()
    self.__init__()
    self.run() 
       
    
if __name__ == '__main__':
  g = PieceWord()
  g.run()
  while(True):
    quit = g.wait()
    if quit:
      break
















