from tetris_config import *
from scene import *
import os
import sys

sys.path.append('../')
from gui.game_menu import MenuScene
from ui import Path
import sound
import random
from random import uniform as rnd
import math
from time import sleep
from math import pi
try:
    from change_screensize import get_screen_size
except ImportError:
    from scene import get_screen_size
w, h = get_screen_size()

GRID_SIZE = h // 27
A = Action


def clamp(x, minimum, maximum):
  return max(minimum, min(x, maximum))


def intersects_sprite(point, sprite):
  norm_pos = Vector2()
  norm_pos.x = sprite.position.x - (sprite.size.w * sprite.anchor_point.x)
  norm_pos.y = sprite.position.y - (sprite.size.h * sprite.anchor_point.y)
  
  return (point.x >= norm_pos.x and point.x <= norm_pos.x + sprite.size.w) and (point.y >= norm_pos.y and point.y <= norm_pos.y + sprite.size.h)


def build_background_grid():
  parent = Node()
  global GRID_SIZE
  # Parameters to pass to the creation of ShapeNode
  params = {
    "path": Path.rect(0, 0, GRID_SIZE, GRID_SIZE * ROWS),
    "fill_color": "clear",
    "stroke_color": "lightgrey"
  }
  
  anchor = Vector2(0, 0)
  
  # Building the columns
  for i in range(COLUMNS):
    n = ShapeNode(**params)
    pos = Vector2(i*GRID_SIZE, 0)
    
    n.position = pos
    n.anchor_point = anchor
    
    parent.add_child(n)
  
  # Building the rows
  params["path"] = Path.rect(0, 0, GRID_SIZE * COLUMNS, GRID_SIZE)
  for i in range(ROWS):
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
  global GRID_SIZE
  def __init__(self, color, row=0, col=0):
    SpriteNode.__init__(self, 'pzl:Gray3')
    self.color = color
    self.size = (GRID_SIZE, GRID_SIZE)
    self.anchor_point = (0, 0)
    self.set_pos(col, row)
  
  def set_pos(self, col=0, row=0):
    """
    Sets the position of the tile in the grid.
    """
    if col < 0:
      raise ValueError(f"col={col} is less than 0")
    
    if row < 0:
      raise ValueError(f"row={row} is less than 0")
    
    self.col = col
    self.row = row
    
    pos = Vector2()
    pos.x = col * self.size.w
    pos.y = row * self.size.h
    self.position = pos
    

class PieceControl ():
  """
  An object that controls a group of tiles.
  """
  def __init__(self, tiles=[]):
    """
    Constructs a new PieceControl.
    
    Parameters:
      tiles: A list of Tile objects under the control of this object.
    """
    self.tiles = tiles

  def piece_coords(self):
    '''create np array of piece positions'''
    return np.array([[t.row, t.col] for t in self.tiles])
  
  def set_from_coords(self, coords):
    for tile, pos in zip(self.tiles, coords):
      tile.set_pos(row=pos[0], col=pos[1])
    
  def rotate_piece(self, choice, exclude=None):
    """rotate a piece.
        get an array of coordinates, translate back to origin of first tile = (0,0)
        multiply each coord  by rotation matrix, then shift back to position"""
        
    coords = self.piece_coords()  
    origin = coords[0]
    translated_tile = coords - origin
    rotated_tile=np.array([np.matmul(xy,rot_matrix) for xy in translated_tile])
    coords = rotated_tile + origin
    if np.any(np.where(coords < 0)) or np.any(np.where(coords[:, 1] >= COLUMNS)):
      return
    self.set_from_coords(coords)    
    return

  def reset(self, tiles=[]):
    self.tiles = tiles
  
  def move(self, d_col=0, d_row=0):
    for t in self.tiles:
      col = clamp(t.col + d_col, 0, COLUMNS - 1)
      row = clamp(t.row + d_row, 0, ROWS - 1)
      t.set_pos(col, row)


class TetrisGame(Scene):
  """
  The main game code for Tetris
  """
  global GRID_SIZE 
  def setup_ui(self):
    # Root node for UI elements
    self.ui_root = Node(parent=self)
    self.left_btn = SpriteNode(**UI["LEFT_BTN"], parent=self.ui_root)
    self.right_btn = SpriteNode(**UI["RIGHT_BTN"],parent=self.ui_root)
    self.down_btn = SpriteNode(**UI["DOWN_BTN"], parent=self.ui_root)
    self.rot_btn = SpriteNode(**UI["ROTATE_BTN"], parent=self.ui_root)
    self.score_label = LabelNode('0', font=('Avenir Next', 40),
                                  position=(GRID_SIZE * COLUMNS + 100, GRID_SIZE * ROWS + 20),
                                  parent=self)
    next_label = LabelNode('Next Tile', font=('Avenir Next', 20),
                                  position=(GRID_SIZE * COLUMNS + 100, GRID_SIZE * ROWS +160),
                                  parent=self)
    score_title = LabelNode('Score', font=('Avenir Next', 20), 
                                    position=(GRID_SIZE * COLUMNS + 100, GRID_SIZE * ROWS +60),
                                    parent=self)
                                  
  def setup(self):
    self.background_color = COLORS["bg"]
  
    # Root node for all game elements
    self.game_field = Node(parent=self, position=GRID_POS)
    
    # Add the background grid
    self.bg_grid = build_background_grid()
    self.game_field.add_child(self.bg_grid)
        
    self.drop_timer = INITIAL_FALL_SPEED
    self.tetris_gen = self.bag_of_tiles()
    self.choice = next(self.tetris_gen)
    
    self.control = PieceControl([])
    self.spawn_piece()
    self.score = 0
    self.level = 1
    self.full_rows = []
    # only set up fixed items once
    try:
      a = self.score_label.text
    except AttributeError:
      self.setup_ui()

  def show_start_menu(self):
    self.pause()
    self.menu = MenuScene('New Game?', '', ['Play', 'Quit'])
    self.present_modal_scene(self.menu)
  
  def clear_tiles(self):
    for t in self.get_tiles():
      t.remove_from_parent()      
        
  def get_tiles(self, exclude=[]):
    """
    Returns an iterator over all tile objects
    """
    for o in self.game_field.children:
      if isinstance(o, Tile) and o not in exclude:
        yield o
        
  def check_control_row_collision(self):
    """
    Returns true if any of the tiles in self.control row-collide (is row-adjacent) 
    with the tiles on the field
    """
    for t in self.control.tiles:
      if t.row == 0:
        return True
      
      for gt in self.get_tiles(exclude=self.control.tiles):
        if t.row == gt.row + 1 and t.col == gt.col:
          return True
    return False
    
  def check_left_collision(self):
    """
    Checks the left side of the control piece for collision
    """
    for t in self.control.tiles:
      if t.col == 0:
        return True
    
      for gt in self.get_tiles(exclude=self.control.tiles):
        if t.col == gt.col + 1 and t.row == gt.row:
          return True
    return False
    
  def check_right_collision(self):
    """
    Check the right side of the control piece for collision
    """
    for t in self.control.tiles:
      if t.col == COLUMNS - 1:
        return True
      
      for gt in self.get_tiles(exclude=self.control.tiles):
        if t.col == gt.col - 1 and t.row == gt.row:
          return True
    return False
  
  def check_complete_row(self):
    """ check if any rows are complete
        iterate through all tiles and count items in each row.
        if count = COLUMNS then mark row for deletion"""
    row_count = np.zeros(ROWS,dtype=np.uint8)
    for t in self.get_tiles(exclude=self.next_tile):
      row_count[t.row] += 1
      if row_count[t.row] == COLUMNS:
        self.full_rows.append(t.row)
    return
    
  def delete_full_rows(self):
    '''delete child tiles in any full row'''
    if self.full_rows is  None:
      return
  
    for t in self.get_tiles(exclude=self.next_tile):
      if t.row in self.full_rows:
        t.remove_from_parent()
        self.game_field.add_child(Explosion(t))
        sound.play_effect('rpg:KnifeSlice2')
        
  def shift_down_tiles(self):
    '''shift down tiles into empty rows'''
    if self.full_rows is None:
      return
      
    for row in sorted(self.full_rows, reverse=True):
      for t in self.get_tiles(exclude=self.next_tile):
        if t.row > row:
          t.set_pos(row=t.row - 1, col=t.col)
  
  def update_score(self, increment=None):
    """ update score on basis of number of full rows cleared,
    or input score increment"""     
    if increment is None:
      increment = scoring_points[len(self.full_rows)] * self.level
    self.score += increment
    self.score_label.text = str(self.score)
      
  def bag_of_tiles(self): 
    """yield a random choice from bag of 7
        create new bag when exhausted """
    tiles = list(range(6))
    while True:
      random.shuffle(tiles)
      for tile in tiles:
        yield tile
          
  def choose_new_and_next_tile(self):
    """ select new tile and show next tile"""
    
    tetris = self.choice
    # delete previous next tile
    for t in self.get_tiles():
      if t in self.next_tile:
        t.remove_from_parent()
        
    self.next = next(self.tetris_gen)
    self.next_tile = self.create_piece(self.next,row=STARTROW -1, 
                                        col=STARTCOL+10)
                                        
    # store next choice for next time round 
    self.choice = self.next
    return tetris
    
  def create_piece(self, index, row=STARTROW, col=STARTCOL):
    """ create tetromino"""
    positions = pieces[index] + [row, col]
    color = colours[index]
    tile = []
    for p in positions:
      t = Tile(color, *p)
      self.game_field.add_child(t)
      tile.append(t)
    return tile
    
  def spawn_piece(self):
    """
    Spawns a new piece on the game field and adds it to self.control
    """
    choice = self.choose_new_and_next_tile()
    tiles = self.create_piece(choice)
    self.control.reset(tiles)
  
  def did_change_size(self):
    pass
  
  def drop(self):
    """iterate update quickly until collision"""
    while(True):
      if self.update():
        break
                        
  def remove_tiles(self):
    """ remove completed row and shift remaining tiles down"""
    self.check_complete_row()
    self.delete_full_rows()
    self.shift_down_tiles()
          
  def check_for_finish(self):
    """check if new piece is at start location when collision detected"""
    for t in self.control.tiles:
      if t.row >= ROWS-2:
        return True
    return False
    
  def reset_full_rows(self):
    self.full_rows = []
  
  def next_game(self):
    self.drop_timer = 10000 # pause next spawn
    self.show_start_menu()
          
  def update(self):
    # dt is provided by Scene
    self.drop_timer -= self.dt
    if self.drop_timer <= 0:
      self.control.move(d_row=-1)
      self.drop_timer = INITIAL_FALL_SPEED
      # Check for intersection and spawn a new piece if needed
      if self.check_control_row_collision():
        self.remove_tiles()
        self.update_score()
        self.reset_full_rows()
        if self.check_for_finish():
          self.next_game()
        else:   
          self.spawn_piece()
        return True
      return False
  
  def touch_began(self, touch):
    if intersects_sprite(touch.location, self.left_btn) and not self.check_left_collision():
      self.control.move(-1)
    elif intersects_sprite(touch.location, self.right_btn) and not self.check_right_collision():
      self.control.move(1)
    elif intersects_sprite(touch.location, self.down_btn):
      self.drop()
    elif intersects_sprite(touch.location, self.rot_btn):
      self.control.rotate_piece(self.choice, exclude=1)
  
  def touch_moved(self, touch):
    pass
  
  def touch_ended(self, touch):
    pass
    
  def menu_button_selected(self, title):
    if title.startswith('Play'):
      # start again
      self.dismiss_modal_scene()
      self.menu = None
      self.clear_tiles()
      self.setup()
      self.score_label.text = '0'
    else:
      # quit
      self.view.close()

            
# Particle effect when row removed:
class Explosion (Node):
  def __init__(self, tile, *args, **kwargs):
    Node.__init__(self, *args, **kwargs)
    self.position = tile.position
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
      p = SpriteNode(tile.texture, scale=0.5, parent=self)
      p.position = tile.size.w/4 * dx, tile.size.h/4 * dy
      p.size = tile.size
      d = 0.4
      r = 30
      p.run_action(A.move_to(rnd(-r, r), rnd(-r, r), d))
      p.run_action(A.scale_to(0, d))
      p.run_action(A.rotate_to(rnd(-pi/2, pi/2), d))
    self.run_action(A.sequence(A.wait(d), A.remove()))


if __name__ == '__main__':
  run(TetrisGame(), PORTRAIT, show_fps=True)

