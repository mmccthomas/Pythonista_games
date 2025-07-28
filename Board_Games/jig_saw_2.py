# basic jigsaw puzzle game.
# creates jigsaw from selected image
# creates random jigsaw each time, using bezier curves to change
# appearance of tabs
# Chris Thomas June 2025
from PIL import Image, ImageFilter
import ui
import io
import math
from time import sleep
from scene import *
import itertools
from operator import attrgetter
import numpy as np
import random
import console
import dialogs
import photos
import objc_util
from collections import Counter
import matplotlib.colors as mcolors
from time import sleep, time
from jigsaw_piece import Piece


class Jigsaw(Scene):

    def __init__(self, x=None, y=20, cell_size=50, image_name=None):
        """
        Args:
          x, y size of jigsaw if image_name supplied
               if not x, y is minimum size
          cell_size is used if imagename supplied, else it is 
                    calculated from x, y and screen size
          image_name in jpg or png format
          
        """
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.image_name = image_name
        
        self.fixed_time_step = 0.01
        self.finish_speed = .8
        
        self.check_timer = 2
        self.selected_piece = None
        self.background_color = 'white'
              
        self.setup_()
        
    def setup_(self):
        if self.x is None:
            sel=dialogs.list_dialog('Size', items=['Small(16)', 'Medium(36)','Large(100)', 'Giant(360)'])
            items={'Small(16)': 16, 'Medium(36)':36, 'Large(100)':100, 'Giant(360)':360} 
            xy = items[sel]
            self.x = self.y = int(math.sqrt(xy))
        
        original_image = self.process_image(self.image_name)                
        self.grid_off = (50,50)
        self.touch_tol = (self.cell_size / 2)
        #super().setup()
        #random choice of these 4 tab shapes
        params_types = [{'tab_depth': 0.3, 'tab_width_factor': 0.3, 
                         'bulge': 2, 'skeww': 0.2, 'skewh': 0.4, 'flat':1},
                        {'tab_depth': 0.4, 'tab_width_factor': 0.3, 
                         'bulge': 2, 'skeww': 0.0, 'skewh': 0.0, 'flat':0},
                        {'tab_depth': 0.3, 'tab_width_factor': 0.4, 
                         'bulge': 1.3, 'skeww': 0.0, 'skewh': 0.0, 'flat':1},
                        {'tab_depth': 0.3, 'tab_width_factor': 0.4, 
                         'bulge': 1, 'skeww': 0.0, 'skewh': 0.0, 'flat':-0.5}]
        params = random.choice(params_types)
        # params = params_types[3] # for testing
        # Root node for all game elements
        self.game_field = Node(parent=self)
        
        grid = self.solve_grid()        
               
        picture_size = (self.x * self.cell_size, self.y * self.cell_size)
        img_pil = self.ui2pil(original_image)
        sized = img_pil.resize(picture_size)
        img = self.pil2ui(sized)
        
        self.background_image = img
        back = self.build_background_grid()
        back.position = self.grid_off
        self.game_field.add_child(back)
        
        self.msg_label = LabelNode('Jigsaw Puzzle', color='black',position=(self.W/2, 25))
        self.game_field.add_child(self.msg_label)
        self.finish_button = SpriteNode('iob:arrow_right_c_256', scale=0.25, position=(32, 36),
                              parent=self.game_field)
        # create Pieces and show on grid
        self.jigsaw_pieces = []
        self.color_map = [
            random.choice(list(mcolors.CSS4_COLORS)) 
            for _ in self.pieces_dict]
        idx = 0
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                index = grid[r][c]
                type_ = self.pieces_dict[index]
                # Piece has a Bezier outline for the tabs
                piece = Piece(type_,
                              self.cell_size,
                              fill_color=self.color_map[index],
                              **params)
                              
                self.jigsaw_pieces.append(piece)
                piece.id = idx
                piece.img = img
                piece.pil = sized
                #extra is the length of an outie, always the same
                piece.order = self.locs.index((r,c))
                piece.row, piece.col = r, c
                tile = piece.shape
                piece.placed = False
                tile.alpha = .95
                tile.position = (self.grid_to_pos(r, c) 
                                 + self.grid_off 
                                 - piece.origin)
                self.game_field.add_child(tile)
                piece.fill_with_image()
                piece.image_position = (tile.position 
                                         + piece.origin 
                                         + Point(piece.extra, -piece.extra))
                piece.sprite.position = piece.image_position
                self.game_field.add_child(piece.sprite)

        
        # sort the piece list into order that the grid was generated, ie clockwise spiral
        self.jigsaw_pieces = sorted(self.jigsaw_pieces, key=attrgetter('order'))
        # now drop all the pieces in a heap
        # outside pieces will be on top
        for item in self.jigsaw_pieces[::-1]:
            posx =  (self.x + 1) * self.cell_size
            item.sprite.position = (posx + random.randint(0, int(self.W - posx)),
                                    random.randint(0, int(self.H - 100)))       
        # finally, release the hounds                                            
        self.paused = False
        
    def process_image(self, image_name):
        """ process image_name, else choose one from photos """
        
        if image_name:
           image_filename = image_name
           original_image = ui.Image.named(image_filename)
        else:
          all_assets = photos.get_assets()
          asset = photos.pick_asset(assets=all_assets)          
          img = Image.open(asset.get_image_data())
          original_image = self.pil2ui(img)
        
        aspect_ratio = original_image.size.h / original_image.size.w
        # make self.w and self.h fit the aspect ratio
        self.W, self.H = get_screen_size()
        min_xy = min(self.x, self.y)
        if aspect_ratio > 1:
            self.x = min_xy
            self.y = int(aspect_ratio * min_xy)         
            self.cell_size = int((self.H -50)/ (self.y + 0.5))
        else:
            self.x = int(self.y / aspect_ratio)
            # fill 2/3 of screen_width    
            self.cell_size = int(2*self.W/(3*self.x))
        return original_image
            
    def ui2pil(self, ui_img):
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
        row = self.y - 1 - row
        x = col * self.cell_size + self.cell_size / 2
        y = row * self.cell_size + self.cell_size / 2
        return Point(x, y)

    def build_background_grid(self):
        parent = Node()
        # Parameters to pass to the creation of ShapeNode
        params = {    
            "path": ui.Path.rect(0, 0, self.cell_size, self.cell_size * self.y),
            "fill_color": 'clear',
            "stroke_color": "darkgrey",
            "z_position": 1
        }
        if self.background_image:
            background = SpriteNode(Texture(self.background_image))
            background.size = (self.cell_size * self.x,
                               self.cell_size * self.y)
            background.position = (0, 0)
            background.anchor_point = (0, 0)
            parent.add_child(background)
        anchor = Vector2(0, 0)
        # Building the columns
        for i in range(self.x):
            n = ShapeNode(**params)
            pos = Vector2(0 + i * self.cell_size, 0)
            n.position = pos
            n.anchor_point = anchor
            parent.add_child(n)

        # Building the rows
        params["path"] = ui.Path.rect(0, 0, self.cell_size * self.x,
                                      self.cell_size)
        params['fill_color'] = 'clear'
        for i in range(self.y):
            n = ShapeNode(**params)
            pos = Vector2(0, 0 + i * self.cell_size)
            n.position = pos
            n.anchor_point = anchor
            parent.add_child(n)

        return parent

    def generate_all_pieces(self, letters='SIO', length=4):
        """ Generates all valid pieces"""
        # itertools.product generates tuples, so we join them to form strings
        permutations = [p for p in itertools.product(letters, repeat=length)]
        valid = []
        for p in permutations:
            #filter pieces with more than 2 straight sides
            c = Counter(p)
            if c['S'] > 2:
                continue
            # filter pieces with straights on opposite sides
            if c['S'] == 2:
                if p[0] == 'S' and p[3] == 'S':
                    valid.append(p)
                if 'SS' in ''.join(p):
                    valid.append(p)
            else:
                valid.append(p)
        # turn lists into strings
        perm_strings = [''.join(p) for p in valid]
        #create dict of number: string
        self.pieces_dict = {i: str_ for i, str_ in enumerate(perm_strings)}
        # and its inverse string:number
        self.inv_pieces_dict = {v: k for k, v in self.pieces_dict.items()}
        return perm_strings

    def solve_grid(self):
        """ given x, y grid, fit pieces """
        # start at (0,0) and proceed clockwise

        self.locs = self.spiral()
        all_pieces = self.generate_all_pieces()
        grid = np.full((self.y, self.x), ' ' * 4)
        for loc in self.locs:
            matches = self.rules(grid, loc, all_pieces)
            grid[loc] = random.choice(matches)

        number_grid = [[self.inv_pieces_dict[grid[r, c]]
                        for c in range(self.x)]
                            for r in range(self.y)]
        return number_grid

    def filter_(self, possibles, direction, element='S', require=False):
        """ either remove or include possible piece for a set of possibles """
        if require:
            return [poss for poss in possibles if poss[direction] == element]
        else:
            return [poss for poss in possibles if poss[direction] != element]

    def rules(self, grid, loc, all_pieces):
        """ Apply rules for joining pieces to 
            reduce all possible pieces to a set of valid ones
        """
        empty = ' ' * 4
        N, E, S, W = 0, 1, 2, 3

        def opp(a):
            return 'O' if a == 'I' else 'I'

        pieces = all_pieces.copy()
        r, c = loc
        # if first row, top must be S
        pieces = self.filter_(pieces, N, require=(r == 0))
        # if first column, left must be S
        pieces = self.filter_(pieces, W, require=(c == 0))
        # if last row, bottom must be S
        pieces = self.filter_(pieces, S, require=(r == self.y - 1))
        # ii last column, right must be S
        pieces = self.filter_(pieces, E, require=(c == self.x - 1))

        # top must be opp of upper row bottom
        if r > 0 and grid[r - 1][c] != empty:
            req = opp(grid[r - 1][c][S])
            pieces = self.filter_(pieces, N, element=req, require=True)
        # left must be opp of left column right
        if c > 0 and grid[r][c - 1] != empty:
            req = opp(grid[r][c - 1][E])
            pieces = self.filter_(pieces, W, element=req, require=True)
        # bottom must be opp of next row top
        if r < self.y - 1 and grid[r + 1][c] != empty:
            req = opp(grid[r + 1][c][N])
            pieces = self.filter_(pieces, S, element=req, require=True)
        # right must be opp of next col left
        if c < self.x - 1 and grid[r][c + 1] != empty:
            req = opp(grid[r][c + 1][W])
            pieces = self.filter_(pieces, E, element=req, require=True)
        # what remains are available valid pieces
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
            if top <= bottom:  # Check if there's still a row to traverse
                for col in range(right, left - 1, -1):
                    visited_order.append((bottom, col))
                bottom -= 1

            # Move up along the leftmost column (if applicable)
            if left <= right:  # Check if there's still a column to traverse
                for row in range(bottom, top - 1, -1):
                    visited_order.append((row, left))
                left += 1

        return visited_order
    
    def complete(self):
        """ complete the puzzle, placing the unplaced tiles
        using  action sequence to get smooth action """  
        # a list of actions becomes a single sequence
        self.unplaced = [piece for piece in self.jigsaw_pieces if not piece.placed]
        self.move_index=0
        animation=Action.sequence(
            Action.repeat(Action.sequence(Action.call(self.move_single_tile), 
            Action.wait(self.finish_speed + 0.01) ), len(self.unplaced)))   
        self.run_action(animation, 'tile_move') 
        return
    
    def move_single_tile(self):
      """ called by action sequence
      cannot pass parameters hence using class variables
      """      
      p = self.unplaced[self.move_index]
      xy = p.image_position         
      self.move_index += 1
      p.sprite.run_action(Action.move_to(*xy,self.finish_speed ))    
      p.placed = True
          
    def update(self):
        self.check_timer -= self.dt
        if self.check_timer < 0:
          self.check_timer = 2
          if all([piece.placed for piece in self.jigsaw_pieces]):
             self.game_over()
             
    def close_(self):
        try:
          self.view.close()
          sleep(1)
        except AttributeError:
          pass    
        
    @ui.in_background
    def game_over(self):      
        self.paused = True      
        sleep(1)    
        selection = dialogs.alert('New Puzzle?',
                                      '',
                                      button1='New',
                                      button2='Quit',
                                      hide_cancel_button=True)
        if selection == 1:
            self.paused = True
            self.close_() 
            run(Jigsaw(None, None, None ), LANDSCAPE, show_fps=False)                       
        else:
            # quit
            self.close_()
                           
    def touch_began(self, touch):
        if self.finish_button.bbox.contains_point(touch.location):
            self.complete()
            return         
        for piece in self.jigsaw_pieces:
            if piece.placed:
                self.selected_piece = None
                continue
            if piece.sprite.bbox.contains_point(touch.location):
                self.selected_piece = piece          
                break

    def touch_moved(self, touch):
        if self.selected_piece:
            self.selected_piece.sprite.position = touch.location

    def touch_ended(self, touch):
        if self.selected_piece:
            if self.selected_piece.close_to_target():
                extra = self.selected_piece.extra
                self.selected_piece.sprite.position = self.selected_piece.image_position   # shape.position + (
                    #extra, -extra) + self.selected_piece.origin
                self.selected_piece.placed = True


if __name__ == "__main__":
    run(Jigsaw(None, None, None ), LANDSCAPE, show_fps=False) # 'TBirds.jpeg'

