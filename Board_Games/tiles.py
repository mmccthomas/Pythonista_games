""" Sliding tiles puzzle game
requires pip install slidingpuzzle
"""
import os
import sys
from scene import *
from ui import Path
import sound
import random
import math
from time import sleep
import time
from math import pi
import numpy as np
import photos
from PIL import Image
import logging
import slidingpuzzle as puzz
import io
from tile_config import *
sys.path.append('../')
from gui.game_menu import MenuScene

A = Action
logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
image_file = None

def A_star(init_state):
    #  "a*" "beam" "bfs" "dfs"
    # "greedy" "ida*" "iddfs"
    sol = puzz.search(init_state, weight=10)
    logger.debug(sol)
    path = puzz.solution_as_tiles(sol.board, sol.solution)
    return path
    
def pil2ui(imgIn):
  """ import a photo library image and convert to jpg in memory """
  with io.BytesIO() as bIO:
    imgIn.save(bIO, 'PNG')
    imgOut = ui.Image.from_data(bIO.getvalue())
  del bIO
  return imgOut
  
def slice_image_into_tiles(in_image, img_count_h, img_count_v=1):
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
   
def clamp(x, minimum, maximum):
  return max(minimum, min(x, maximum))

def intersects_sprite(point, sprite):
  norm_pos = Vector2()
  norm_pos.x = sprite.position.x - (sprite.size.w * sprite.anchor_point.x)
  norm_pos.y = sprite.position.y - (sprite.size.h * sprite.anchor_point.y)
  
  return (point.x >= norm_pos.x and point.x <= norm_pos.x + sprite.size.w) and (point.y >= norm_pos.y and point.y <= norm_pos.y + sprite.size.h)

def build_background_grid():
  parent = Node()

  # Parameters to pass to the creation of ShapeNode
  params = {
    "path": Path.rect(0, 0, GRID_SIZE, GRID_SIZE * SIZE),
    "fill_color": "clear",
    "stroke_color": "lightgrey"
  }
  
  anchor = Vector2(0, 0)
  
  # Building the columns
  for i in range(SIZE):
    n = ShapeNode(**params)
    pos = Vector2(i*GRID_SIZE, 0)
    
    n.position = pos
    n.anchor_point = anchor
    
    parent.add_child(n)
  
  # Building the rows
  params["path"] = Path.rect(0, 0, GRID_SIZE * SIZE, GRID_SIZE)
  for i in range(SIZE):
    n = ShapeNode(**params)
    pos = Vector2(0, i*GRID_SIZE)
    
    n.position = pos
    n.anchor_point = anchor
    
    parent.add_child(n)
    
  return parent

    
class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, tile, row=0, col=0):
    SpriteNode.__init__(self, tile)
    self.size = (GRID_SIZE, GRID_SIZE)
    self.anchor_point = 0,0 
    self.number = 1
    self.set_pos(col, row)
    
  def set_pos(self, col=0, row=0):
    """
    Sets the position of the tile in the grid.
    """
    if isinstance(col,Point):
      row, col  = col.y, col.x      
    if col < 0 or col >= SIZE:
      return
      #raise ValueError(f"col={col} is less than 0")    
    if row < 0 or row >= SIZE:
      return      
      # raise ValueError(f"row={row} is less than 0")   
    self.col = int(col)
    self.row = int(row)
    
    pos = Vector2()
    pos.x = col * self.size.w
    pos.y = row * self.size.h
    self.run_action(A.sequence(
      A.move_to(pos.x,pos.y, MOVE_SPEED), 
      A.wait(0.1), 
      A.remove))
    self.position = pos

class TileNo(LabelNode, Tile):
  """
  A single numbered tile on the grid.
  """
  def __init__(self, no, color=None,row=0, col=0):
    LabelNode.__init__(self, str(no), font=('Avenir Next', 50), position=(0,0)) 
    self.size = (GRID_SIZE, GRID_SIZE)
    self.anchor_point = 0,0 
    self.number = no
    if color:
      self.color=color
    self.set_pos(col, row)
    

class TileGame(Scene):
  """
  The main game code for Sliding Tiles game
  """
  def setup(self, first_time=True):
    logger.debug('start setup')
    self.background_color =  "#232323"
    # Root node for all game elements
    self.game_field = Node(parent=self, position=GRID_POS)
    self.clear_tiles()
    # Add the background grid
    self.bg_grid = build_background_grid()
    self.game_field.add_child(self.bg_grid)
    self.line_timer_current = 0
    self.t_elapsed = 0
    self.score = 0
    self.line_timer = INITIAL_LINE_SPEED
    self.t_move_time = MOVE_SPEED
    self.level = 1
    self.no_moves = 0
    self.arrays = []
    self.images = []
    if first_time:
      self.show_start_menu()
    logging.debug("setup ui")
    self.setup_ui(first_time)
    
    self.game_title.text = ""
    # produces solvable boards
    board = puzz.shuffle(puzz.new_board(SIZE, SIZE))
    self.compute_start(board)
    self.paused = False
    
    # only set up fixed items once
    try:
      a = self.score_label.text
    except AttributeError:
      pass      
        
  def setup_ui(self, first_time=True):
    # Root node for UI elements
    self.ui_root = Node(parent=self)
    if first_time:
      bbox = self.game_field.bbox
      x_origin, y_origin = bbox[2], bbox[3]
      LabelNode('Score', font=('Avenir Next', 30), position=(x_origin + 60, y_origin ), parent=self)  
      self.line_label = LabelNode(str(self.line_timer_current), font=('Avenir Next', 20), position=(x_origin + 50, y_origin - 40), parent=self) 
      LabelNode('Time', font=('Avenir Next', 30), position=(x_origin + 60, y_origin - 80 ), parent=self)
      self.time_label = LabelNode('0', font=('Avenir Next', 20), position=(x_origin + 50, y_origin - 120), parent=self) 
      self.game_title = LabelNode('Slider', font=('Avenir Next', 20), 
                                    position=(screen_width / 2, 10),
                                    parent=self)              
      self.pause_button = SpriteNode('iow:pause_32', position=(32, self.size.h-36), parent=self)
    logger.debug('setup pictures')
    if TILES == "pictures":
      if not image_file:
        # get random image from photo library
        all_assets = photos.get_favorites_album().assets
        asset = random.choice(all_assets)
        self.image_name = asset.get_image()
      else:
        self.image_name = image_file
      
      self.images = slice_image_into_tiles(self.image_name, img_count_h=SIZE, img_count_v=SIZE)
    
  def pick_image(self):
    all_assets = photos.get_favorites_album().assets
    asset = random.choice(all_assets)
    image_file = asset.get_image()
    return image_file
    
  def place_tiles(self, array):
    """ place tiles in same order as array
    need to flip as top left is (2,0) on grid
    """
    flipped = np.flipud(np.copy(array))
    for t in self.get_tiles():
      row_col = np.where(flipped == t.number)
      row = row_col[0][0]
      col = row_col[1][0]
      if (row, col) != (t.row, t.col):
        t.set_pos(col,row)
      
  def update_array(self):
    """ convert tile positions to array """
    array = np.zeros((SIZE, SIZE), dtype=int)
    for t in self.get_tiles():
      array[t.row][t.col] = t.number
    array = np.flipud(array)
    return array    
      
  def compute_start(self,board):
    """ set a new grid using numbers
    solution is tested to make sure it is solvable
    """
    self.start_array = board
    self.target_array = puzz.new_board(SIZE,SIZE)
    
    logger.debug(self.images)
    self.tiles = {}
    self.clear_tiles()
    # now place tiles according to start_array
    for index, no in enumerate(self.target_array.flatten()):
      color = COLORS[list(COLORS)[index // SIZE +1]]
      if no != 0:
        if TILES == "pictures":
          if self.images:
            t = Tile(Texture(pil2ui(self.images[no])), 0,0)
            LabelNode(str(no), font=('Avenir Next', 12), position=(10,10), parent=t)
          else:
            self.game_title.text = 'Invalid Image'
            t = TileNo(no,color,0,0)
        else:
          t = TileNo(no,color,0,0)
        self.game_field.add_child(t)
        t.number = no
      self.tiles.setdefault(no, t) # dictionary of tile objects
      
    logger.debug(" Initial array")
    for i in range(SIZE):
      logger.debug(self.start_array[i, :]) 
    logger.debug( "") 
      
    self.place_tiles(self.start_array)    
    self.start_array = self.update_array()  
                              
  def clear_tiles(self):
    for t in self.get_tiles():
      t.remove_from_parent()      
      
  def point_to_rc(self,point):
    """ covert touch point to Point object """    
    bbox = self.game_field.bbox # x,y,w,h
    col = int(SIZE * (point.x - bbox.x) / bbox.w)
    row = int(SIZE * (point.y - bbox.y) / bbox.h)
    return Point(col,row)
    
  def rc_to_pos(self,tile,col,row):
    """ covert col row  to Point object """
    bbox = self.game_field.bbox # x,y,w,h
    x = col * tile.size.w  # bbox.x 
    y = row * tile.size.h 
    return Point(x,y)
        
  def get_tiles(self):
    """
    Returns an iterator over all tile objects
    """
    for o in self.game_field.children:
      if isinstance(o, Tile) :
        yield o
  
  def tile_at(self, row, col=None):
    '''select tile'''
    if isinstance(row,Point):
      r,c = row.y, row.x
    else:
      r, c = row, col
    for t in self.get_tiles():
      if t.row == r and t.col == c :
        return t
    return None
  
  def update_score(self):   
    self.line_label.text = str(self.no_moves)   
  
  def did_change_size(self):
    pass
    
  def tile_move(self, initial_r,initial_c, final_r,final_c):
    """ move tile from initial to final rc"""
    tile = self.tile_at(initial_r,initial_c)
    if tile:
      return (tile.number, self.rc_to_pos(tile,final_c ,final_r))
      
  def tile_drop(self, touch, selected):
    """ move tile to new location 
        check that only moved one position
    """
    cr = self.point_to_rc(touch.location)
    old_cr = self.point_to_rc(self.last_t)  
    # dist is hypotenuse from subtraction of points
    dist = abs(cr-old_cr)
    if selected and not self.tile_at(cr) and dist < 1.1:
      logger.debug(f' move to {cr}')
      selected.set_pos(cr)
      self.start_array = self.update_array()  
      self.check_for_finish()
      self.no_moves += 1
      self.update_score(
        )
        
  def step_through(self, path):
    """ process path from A* to process list of tile number and new location"""

    self.move_array = []    
    if len(path) == 0:
      return        
    
    init_array = self.start_array
    # path is now a list of tile numbers
    for node in path:
      
      r_from, c_from = puzz.find_tile(init_array, node)
      new_arr = puzz.swap_tiles(init_array,node)
      r_to, c_to = puzz.find_tile(new_arr, node)
      tile_no =node         
      new_loc = self.rc_to_pos(self.tiles[tile_no],c_to, SIZE - 1-  r_to)
      self.move_array.append((tile_no, new_loc))
      init_array = new_arr
      self.no_moves += 1
    self.paused = False
    self.update_score()
    return
        
  def process_moves(self):
    """ animate the movements calculated """
    self.game_title.text = ''
    self.no_moves = len(self.move_array)  
    logger.debug(f"now processing {self.no_moves} moves")
    self.t_move_time = TOTAL_TIME / self.no_moves
    self.move_index = 0
    if self.no_moves == 0:
      return
    # a list of actions becomes a single sequence
    animation=A.sequence(
      A.repeat(A.sequence(A.call(self.move_single_tile), 
      A.wait(self.t_move_time + 0.01) ), self.no_moves),
      A.call(self.next_game))   
    self.run_action(animation, 'tile_move') 
    return
    
  def move_single_tile(self):
    """ called by action sequence
    cannot pass parameters hence using class variables
    """
    if self.move_array[self.move_index]:
      no, xy  = self.move_array[self.move_index]
      self.game_title.text = f'{self.move_index}/{self.no_moves} moving {no}'
      self.move_index += 1
      self.tiles[no].run_action(A.move_to(xy.x,xy.y,self.t_move_time))    
      
                                  
  def check_for_finish(self):
    """check if all pieces in correct order"""
    if np.array_equal(self.start_array,self.target_array):
      self.next_game()
    return False  
    
  def next_game(self):
    self.show_start_menu()
    self.t_move_time = MOVE_SPEED
    
  def solve(self):    
    path = A_star(self.start_array)
    logger.debug("finished solve")
    self.dismiss_modal_scene()
    self.step_through(path)
    self.process_moves()    
        
  def update(self):
    # dt is provided by Scene t is time since start
    self.line_timer -= self.dt
    if self.line_timer <= 0:
      self.line_timer = INITIAL_LINE_SPEED
      self.t_elapsed += 1
      self.time_label.text = str(self.t_elapsed)
  
  def touch_began(self, touch):

    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.tile_selected = None
      self.show_pause_menu()
      return
    t = touch.location
    self.last_t = t
    rc = self.point_to_rc(t)
    self.tile_selected = self.tile_at(rc)

    
  def touch_moved(self, touch):
    pass
  
  def touch_ended(self, touch):
    logger.debug('touch ended')
    if self.tile_selected:
      logger.debug(f'tile {self.tile_selected.number} to move')
      self.tile_drop(touch, self.tile_selected)
    self.tile_selected = None
    
  def show_pause_menu(self):
    self.menu = MyMenu('Paused', '', ['Continue', 'Solve', 'New Game', 'Quit'])
    self.present_modal_scene(self.menu)
    paused = True
    
  def show_start_menu(self):    
    self.menu = MyMenu('Completed','New Game?',
     ['2x2','3x3', '4x4', '5x5', '6x6', 'Numbers', 'Pictures','Play', 'Quit'], 
     layout=[5, 2, 1, 1])
    self.present_modal_scene(self.menu) 
    self.paused = True
    
  def set_size(sel, size):
    global SIZE, GRID_SIZE
    screen_width, screen_height = get_screen_size()
    SIZE = size
    GRID_SIZE= screen_width // (2*SIZE)     
    
  def set_tiles(self,tile):
    global image_file
    global TILES
    TILES = tile
    if TILES == 'pictures':
      if not image_file:
        # get random image from photo library
        all_assets = photos.get_favorites_album().assets
        asset = random.choice(all_assets)
        #self.image_name = all_assets[selection].get_image()
        #asset = photos.pick_asset(title='Pick an image file', multi=False)
        if asset:
           self.image_name = asset.get_image()
  
          
  def menu_button_selected(self, title):
    """ choose to play again or quit """
    sizes = ['2x2','3x3', '4x4', '5x5', '6x6']
    if  title.startswith('Play'):
      # start again
      self.dismiss_modal_scene()
      self.menu = None
      for o in self.game_field.children:
        o.remove_from_parent()
      
      self.clear_tiles()
      self.setup(first_time=False)
      self.game_title.text = ""
      self.paused = False
    elif title.startswith('New Game'):
      self.dismiss_modal_scene()
      self.show_start_menu()    
    elif title.startswith('Solve'):
      self.solve()
      self.dismiss_modal_scene()
    elif title.startswith('Continue') :
      self.dismiss_modal_scene()
      self.menu = None    
    elif title.startswith('Quit'):
      self.view.close()
    elif any([x in title for x in sizes]):
        self.set_size(int(title[0]))  
    elif title.startswith('Pictures'):
        self.set_tiles('pictures')
    elif title.startswith('Numbers'):
        self.set_tiles('Numbers')
    else:
      pass
      
      
class MyMenu(MenuScene):
  """ subclass MenuScene to move menu to right """
  def __init__(self, title, subtitle, button_titles, layout=None):
    MenuScene.__init__(self, title, subtitle, button_titles, layout)
    
  def did_change_size(self):
    # 834,1112 ipad portrait
    # 1112, 834 ipad landscape
    # 852, 393 iphone landscape
    self.bg.size = (1, 1)
    if self.size.h > self.size.w:
      self.bg.position = self.size.w * 0.5, self.size.h *0.6
    else:
      self.bg.position = self.size.w * 0.85, self.size.h * 0.5
    self.menu_bg.position = self.bg.position
    
        
def main():
    logging.basicConfig(format='%(asctime)s  %(funcName)s %(message)s',level=logging.WARNING)   
    run(TileGame(), DEFAULT_ORIENTATION, show_fps=True)
    
if __name__ == '__main__':
  main()


