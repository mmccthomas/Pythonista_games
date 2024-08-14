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
from scene import Texture, Point
from gui.gui_interface import Gui, Squares
WordleList = ['5000-more-common.txt'] 
HSIZE = 4
VSIZE = 9
clues =  ['2 Bill too low a price',
					'4 Very small freshwater fish or a person with little influence Standard word-ending',
					'6 Claiming for yourself Old laundry machine',
					'8 Bland Particular period',
					'10 Mark (an item) for attention Flexible. Large loose hood, part of a monks habit',
					'12 Layer of cartilage between two vertebrae',
					'• Last match in a competition',
					'• Something owed',
					'14 Temporary shelter Structure and rules of language',
					'16 Sequence of hereditary rulers',
					'• Accomplish',
					'18 Stale, smelly. Chilly',
					'20 Person paying ground or other rent on a property'
				 ]

class PieceWord(LetterGame):
  
  def __init__(self):
    LetterGame.__init__(self)
    self.first_letter = False
    # self.gui.build_extra_grid(5, 7, grid_width_x=3, grid_width_y=3, color='white', line_width=2)
    self.image_name = Image.open('Pieceword1.jpg')
    self.images = self.slice_image_into_tiles(self.image_name, img_count_h=HSIZE, img_count_v=VSIZE)
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
    self.posn = SimpleNamespace(**position_dict[self.gui.device])
    self.rack = self.display_rack()
    self.gui.set_moves('\n'.join(clues))
    
    #self.gui.gs.IMAGES = {i:self.pil2ui(image) for i, image in enumerate(self.rack.values())}
    
    
  def run(self):
    #LetterGame.run(self)
    """
    Main method that prompts the user for input
    """
    
    
    self.row = 0
    self.square_list = []
    #self.print_square(1)
    #self.initialise_board()    
    self.finished = False
    move = ''
    while True:
      self.gui.clear_squares()           
      #self.print_board()
      move = self.get_player_move(self.board)               
      move = self.process_turn( move, self.board) 
      #self.print_square(move)
      if self.game_over():
        break
      self.row += 1               
    #self.print_board()
    self.gui.set_message2('')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    
    sleep(4)
    self.finished = True
    self.gui.gs.show_start_menu()
    
  @ui.in_background
  def pick_image(self):
    asset = photos.pick_asset(title='Pick an image file', multi=False)
    image_file = asset.get_image()
    image_file = self.pil2ui(image_file)
    return image_file
  
  def display_rack(self, y_off=0):
    """ display players rack
    y position offset is used to select player_1 or player_2
    """   
    parent = self.gui.game_field
    _, _, w, h = self.gui.grid.bbox        
    x, y = self.posn.rackpos
    y = y + y_off
    rack = {}
    self.rack2 = []
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
      #tile.position = (c * sqsize, (self.gui.gs.DIMENSION_Y - 1 - r) * sqsize)      
      #t.position = (w + x + n%4 * sqsize,  h - y - n//4 * sqsize)
      t.number = n
      #rack[t.bbox] = tile
      self.rack2.append(t)
      parent.add_child(t)     
    return rack          
          
  def get_size(self):
    LetterGame.get_size(self, '5, 7')
    
  def load_words(self, word_length, file_list=WordleList):
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
    
  def print_square(self, moves, color=None):
    #
    try: 
      self.gui.gs.clear_numbers()
    except (AttributeError):
      pass
    
    r = self.row
    for c in self.correct_positions:
      self.square_list.append(Squares((r, c), '', 'green' , z_position=30, alpha = .5)) 
       
    for c in self.correct_letters:
      self.square_list.append(Squares((r, c), '', 'orange' , z_position=30, alpha = .5))
    
    self.gui.add_numbers(self.square_list)   
    return
    
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move
    Allows for movement over board"""
    move = LetterGame.get_player_move(self, self.board)
    
    if move[0] == (-1, -1):
       return (None, None), 'Enter', None # pressed enter button
      
    point = self.gui.gs.start_touch - gscene.GRID_POS
    # get letter from rack
    #for index, k in enumerate(self.rack):
    #    if k.contains_point(point):
    #        letter = index
    #        rc = move[-2]
    #        return rc, letter, index
            
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
        #r, c = coord
        #sqsize = self.gui.gs.SQ_SIZE
        #self.board[r][c] = letter 
        tile_move = self.rack[origin]        
        tile_existing = self.rack[coord]
                          
        #tile_move.row, tile_move.col = coord  
        tile_move.set_pos(coord)  
        tile_existing.set_pos(origin)       
        #tile_move.position = (c * sqsize, (self.gui.gs.DIMENSION_Y - 1 - r) * sqsize)            
                          
        #tile_existing.row, tile_existing.col = origin  
        # now update rack        
        self.rack[origin] = tile_existing
        self.rack[coord] = tile_move
        #tile_existing.position = (origin_col * sqsize, (self.gui.gs.DIMENSION_Y - 1 - origin_row) * sqsize)            
                    
      
    return 0   
            
  
  def game_over(self):
    return 
    
      
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    self.SIZE = self.get_size() 
    self.gui = Gui(self.board, Player())
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui(q=self.q)
    self.run() 
    
    
    
if __name__ == '__main__':
  g = PieceWord()
  g.run()
  while(True):
    quit = g.wait()
    if quit:
      break










