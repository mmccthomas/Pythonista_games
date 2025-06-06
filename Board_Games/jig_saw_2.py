from PIL import Image, ImageFilter, ImageDraw
import ui
import io
from math import sin, cos, pi, radians
from scene import *
import itertools
import re
import numpy as np
import random
import objc_util
import matplotlib.pyplot as plt
from collections import namedtuple, Counter
import matplotlib.colors as mcolors
from  time import sleep
from jigsaw_piece import Piece

class Jigsaw(Scene):
   def __init__(self, x=20, y=20, cell_size=50):       
     #super().__init__(self)
     self.x, self.y = x, y
     self.cell_size = cell_size
     self.W, self.H = get_screen_size()
     self.touch_tol = cell_size
     self.grid_off = (self.cell_size/2, self.cell_size/2)
     #super().setup()
     self.fixed_time_step = 0.01
     self.background_color = 'white'
   
     # Root node for all game elements
     self.game_field = Node(parent=self)
     self.SQ_SIZE = self.cell_size
     self.DIMENSION_X = self.x
     self.DIMENSION_Y = self.y
     self.selected_piece = None
     grid = self.solve_grid()
     
     # now apply image    
     image_filename = 'Clarkson.jpeg' # Use the dummy image or your own
     original_image = ui.Image.named(image_filename)
     picture_size = (self.x * self.cell_size, self.y * self.cell_size)
     img_pil=  self.ui2pil(original_image)
     sized = img_pil.resize(picture_size)
     img = self.pil2ui(sized)
     self.background_image = img
     back = self.build_background_grid()
     back.position = self.grid_off
     self.game_field.add_child(back)
     
     # create Pieces and show on grid
     self.jigsaw_pieces = []       
     self.color_map = [random.choice(list(mcolors.CSS4_COLORS)) for _ in self.pieces_dict]    
     idx = 0 
     for r in range(len(grid)):
       for c in range(len(grid[0])):
         index = grid[r][c]
         type_ = self.pieces_dict[index]
         piece = Piece(type_, self.cell_size, 
                       fill_color = self.color_map[index])
         self.jigsaw_pieces.append(piece)
         piece.id = idx 
         #extra is the length of an outie, always the same         
         extra = piece.R*(1+cos(pi/2 - piece.off))
         piece.row, piece.col = r, c
         tile = piece.shape
         tile.alpha = .9
         tile.position = self.grid_to_pos(r,c) + self.grid_off - piece.origin 
         self.game_field.add_child(tile)
     
     if True:   
         # now deal with images   
         idx = 0
         for r in range(len(grid)):
           for c in range(len(grid[0])):       
             piece = self.jigsaw_pieces[idx]
             # need to position image for cropping
             x, y = Point(c* self.cell_size, r*self.cell_size) - (extra, extra)
             w = h = self.cell_size + 2* extra
             img_part = sized.crop((x,  y, x + w,  y + h))
             img_ = self.pil2ui(img_part)
             # this is centred on piece
             
             img_part_ = self.cut_image_with_custom_path(img_, piece, extra)                         
             piece.sprite = SpriteNode(Texture(img_part_), scale=1) 
             piece.sprite.alpha = 1
             piece.sprite.position = self.grid_to_pos(r,c)+ self.grid_off+ (extra, -extra)
             self.game_field.add_child(piece.sprite)         
             idx += 1
             
     for item in self.jigsaw_pieces:
          item.sprite.position = (1100 + random.randint(0, 250),    100 + random.randint(0, 800))
       
   def ui2pil(self,ui_img):
       png_data = ui_img.to_png()     
       img_out = Image.open(io.BytesIO(png_data))
       img_out = img_out.reduce(2)
       img_out.load()
       del png_data
       return img_out       

   def pil2ui(self, pil_image):
       buffer = io.BytesIO()
       pil_image.save(buffer, format='PNG')
       return ui.Image.from_data(buffer.getvalue(), 1)     
       
   def grid_to_pos(self, row, col):
     row = self.DIMENSION_Y - 1 - row
     x = col * self.SQ_SIZE + self.SQ_SIZE/2
     y = row * self.SQ_SIZE + self.SQ_SIZE/2
     return Point(x, y)
     
   def build_background_grid(self):
    parent = Node()        
    # Parameters to pass to the creation of ShapeNode
    params = {
      "path": ui.Path.rect(0, 0, self.SQ_SIZE, self.SQ_SIZE * self.DIMENSION_Y),
      "fill_color": 'clear',
      "stroke_color": "darkgrey" ,
      "z_position": 1
    }
    if self.background_image:
      background = SpriteNode(Texture(self.background_image))
      background.size = (self.SQ_SIZE * self.DIMENSION_X,
                         self.SQ_SIZE * self.DIMENSION_Y)
      background.position = (0, 0)
      background.anchor_point = (0, 0)
      parent.add_child(background)
    anchor = Vector2(0, 0)
    # Building the columns
    for i in range(self.DIMENSION_X):
      n = ShapeNode(**params)
      pos = Vector2(0 + i * self.SQ_SIZE, 0)
      n.position = pos
      n.anchor_point = anchor
      parent.add_child(n)
      
    # Building the rows
    params["path"] = ui.Path.rect(0, 0, self.SQ_SIZE * self.DIMENSION_X,
                               self.SQ_SIZE)
    params['fill_color'] = 'clear'
    for i in range(self.DIMENSION_Y):
      n = ShapeNode(**params)
      pos = Vector2(0, 0 + i * self.SQ_SIZE)
      n.position = pos
      n.anchor_point = anchor
      parent.add_child(n)
      
    return parent
    
   def copy_path(self, path):
     new = ui.Path()
     new.append_path(path)
     new.line_join_style = path.line_join_style
     new.line_width = path.line_width
     return new
     
   def move_path(self, path, delta):
       new_path = self.copy_path(path)
       transform = objc_util.CGAffineTransform(a=1, b=0, c=0, d=1, tx=delta[0], ty=delta[1])
       objcpath =  objc_util.ObjCInstance(new_path)
       objcpath.applyTransform(transform)
       return new_path
       
   def cut_image_with_custom_path(self, img, piece, extra):
        path = piece.path
        #extra=0
        # Load the image            
        img_width, img_height = img.size    
        # Create an ImageContext with the same size as the original image (or desired output size)
        translate =  Point(extra, extra)
        # The image will be clipped to the path's bounds.        
        with ui.ImageContext(img_width+2*extra, img_height+2*extra) as ctx:
            # Create a copy of the path and shift it
            path_copy = self.move_path(path, translate)
            path_copy.add_clip() # This is the crucial step: apply the path as a clipping mask 
            img.draw(0, 0, img_width, img_height)                
            # Get the new clipped image
            clipped_image = ctx.get_image()
            return clipped_image  

   def generate_all_pieces(self, letters ='SIO', length=4):
      """ Generates all valid pieces"""
      # itertools.product generates tuples, so we join them to form strings
      permutations = [p for p in itertools.product(letters, repeat=length)]            
      valid = []
      for p in permutations:
          #filter pieces with more than 2 straight sides
          c = Counter(p)
          if c['S']> 2:
            continue
          # filter pieces with straights on opposite sides
          if c['S'] == 2:
            if p[0] == 'S' and p[3] == 'S':
              valid.append(p)
            if  'SS'  in ''.join(p):
              valid.append(p)
          else:
            valid.append(p)
      # turn lists into strings
      perm_strings = [''.join(p) for p in valid]
      #create dict of number: string
      self.pieces_dict = {i: str_ for i, str_ in enumerate(perm_strings)}
      # and its inverse string:number
      self.inv_pieces_dict = {v:k for k, v in self.pieces_dict.items()}
      return perm_strings
    
   def solve_grid(self):
      """ given x, y grid, fit pieces """
      pass
      # start at (0,0) and proceed clockwise
      # need spiral routine
      # use recursion and finish when full
      
      locs = self.spiral()
      all_pieces = self.generate_all_pieces()  
      grid = np.full((self.y, self.x), ' '*4)
      for loc in locs:
        matches = self.rules(grid, loc, all_pieces)
        grid[loc] = random.choice(matches)
      
      no_grid = [[self.inv_pieces_dict[grid[r,c]] for c in range(self.x)]
                  for r in range(self.y)]
      return no_grid
        
   def filter_(self, possibles, direction, element='S', require=False):
       if require:
         return [poss for poss in possibles if poss[direction] == element]
       else:
         return [poss for poss in possibles if poss[direction] != element]
       
   def rules(self, grid, loc, all_pieces):          
      empty = ' '*4
      N, E, S, W = 0, 1, 2, 3
      def opp(a):
         return 'O' if a =='I' else 'I'
      pieces = all_pieces.copy()        
      r, c = loc
      # if r=0, top must be S     
      pieces = self.filter_(pieces, N, require=(r == 0))   
      # if c=0, left must be S   
      pieces = self.filter_(pieces, W, require=(c == 0))
      # if r = y-1, bottom must be S
      pieces = self.filter_(pieces, S, require=(r == self.y-1)) 
      # if c = x-1, right must be S
      pieces = self.filter_(pieces, E, require=(c == self.x-1)) 
          
      # (r,c) top must be opp of (r-1, c) bottom
      if r > 0 and grid[r-1][c] != empty:
          req = opp(grid[r-1][c][S]) 
          pieces = self.filter_(pieces, N, element=req, require=True) 
      # (r,c) left must be opp of (r, c-1) right
      if c > 0 and grid[r][c-1] != empty:
          req = opp(grid[r][c-1][E])
          pieces = self.filter_(pieces, W, element=req, require=True) 
      # if (r+1,c) bottom must be opp of (r+1, c) top  
      if r < self.y-1 and grid[r+1][c] != empty:
         req = opp(grid[r+1][c][N])
         pieces = self.filter_(pieces, S, element=req, require=True) 
      # if (r,c+1) right must be opp of (r, c+1) left            
      if c < self.x-1 and  grid[r][c+1] != empty:
          req = opp(grid[r][c+1][W])
          pieces = self.filter_(pieces, E, element=req, require=True)               
                    
      return pieces
      
   def spiral(self):
        """
        Traverses an NxM grid in spiral order starting from (0,0).
    
        Returns:
            A list of tuples, where each tuple (row, col) represents
            a visited square in spiral order.
        """
        N = self.y
        M = self.x
        if N <= 0 or M <= 0:
            return []
    
        visited_order = []
        
        # Initialize boundaries
        top = 0
        bottom = N - 1
        left = 0
        right = M - 1
    
        while top <= bottom and left <= right:
            # Move right along the top row
            for col in range(left, right + 1):
                visited_order.append((top, col))
            top += 1
    
            # Move down along the rightmost column
            for row in range(top, bottom + 1):
                visited_order.append((row, right))
            right -= 1
    
            # Move left along the bottom row (if applicable)
            if top <= bottom: # Check if there's still a row to traverse
                for col in range(right, left - 1, -1):
                    visited_order.append((bottom, col))
                bottom -= 1
    
            # Move up along the leftmost column (if applicable)
            if left <= right: # Check if there's still a column to traverse
                for row in range(bottom, top - 1, -1):
                    visited_order.append((row, left))
                left += 1
    
        return visited_order
        
   def close_to_target(self, piece, touch_tol=None):
       target_loc = piece.shape.position
       piece_loc = piece.sprite.position
       dist = math.hypot(*(target_loc-piece_loc))
       if touch_tol is None:
         touch_tol = self.touch_tol
       return  dist < touch_tol
        
   def update(self):
      pass
      for piece in self.jigsaw_pieces:
        if not self.close_to_target(piece):
          return
      self.game_over()
      
   def game_over(self):
     self.paused = True
     print('finished')  
      
   def touch_began(self, touch):
     for piece in self.jigsaw_pieces:
       if piece.sprite.bbox.contains_point(touch.location):
         self.selected_piece = piece
         break
         
     
   def touch_moved(self, touch):
      if self.selected_piece:
        self.selected_piece.sprite.position = touch.location
     
   def touch_ended(self, touch):
       if self.selected_piece:
         if self.close_to_target(self.selected_piece):
            extra = self.selected_piece.R*(1+cos(pi/2 - self.selected_piece.off))
            self.selected_piece.sprite.position = self.selected_piece.shape.position  +(extra, -extra) + self.selected_piece.origin
          

      
if __name__ == "__main__":
    run(Jigsaw(5, 5, 150), LANDSCAPE, show_fps=False)

