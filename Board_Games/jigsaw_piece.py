import ui
from math import sin, cos, pi, isclose, hypot
from scene import Point, Size, ShapeNode, SpriteNode, Texture
from collections import namedtuple
import numpy as np
import objc_util
import io


class Piece():
    """ The Piece class contains everything to create a jigsaw piece.
    The parameters control the shape of the tabs, constructed using a
    quartic Bezier polynomial.
    The class also contains a reference to a correctly sized uiImage
    and a PIL Image for cropping and path-cutting into the image on the piece 
    shape_str if a 4 character string e.g. 'SIOS' for Straight, In, Out, Straight
    """
    def __init__(self,
                 shape_str,
                 cell_size=100,
                 fill_color='red',
                 tab_depth=0.2,
                 tab_width_factor=0.3,
                 bulge=2.0,
                 skeww=0.0,
                 skewh=0.0,
                 flat=1.0):

        self.X = cell_size
        self.tab_depth = tab_depth
        self.tab_width_factor = tab_width_factor
        self.bulge = bulge
        self.skeww = skeww
        self.skewh = skewh
        self.flat = flat
        self.bz_points = 20
        self.img = None
        self.pil = None

        # all possible pieces
        """
     self.pieces = {0: 'SSII', 1: 'SSIO', 2: 'SSOI', 3: 'SSOO', 4: 'SIIS',
                    5: 'SIII', 6: 'SIIO', 7: 'SIOS', 8: 'SIOI', 9: 'SIOO',
                    10: 'SOIS', 11: 'SOII', 12: 'SOIO', 13: 'SOOS', 14: 'SOOI',
                    15: 'SOOO', 16: 'ISSI', 17: 'ISSO', 18: 'ISII', 19: 'ISIO',
                    20: 'ISOI', 21: 'ISOO', 22: 'IISS', 23: 'IISI', 24: 'IISO',
                    25: 'IIIS', 26: 'IIII', 27: 'IIIO', 28: 'IIOS', 29: 'IIOI',
                    30: 'IIOO', 31: 'IOSS', 32: 'IOSI', 33: 'IOSO', 34: 'IOIS',
                    35: 'IOII', 36: 'IOIO', 37: 'IOOS', 38: 'IOOI', 39: 'IOOO',
                    40: 'OSSI', 41: 'OSSO', 42: 'OSII', 43: 'OSIO', 44: 'OSOI',
                    45: 'OSOO', 46: 'OISS', 47: 'OISI', 48: 'OISO', 49: 'OIIS',
                    50: 'OIII', 51: 'OIIO', 52: 'OIOS', 53: 'OIOI', 54: 'OIOO',
                    55: 'OOSS', 56: 'OOSI', 57: 'OOSO', 58: 'OOIS', 59: 'OOII',
                    60: 'OOIO', 61: 'OOOS', 62: 'OOOI', 63: 'OOOO'}
     """
        self.shape_str = shape_str
        
        self.path = self.create_path(self.shape_str)
        self.fill_color = fill_color
        self.shape = ShapeNode(path=self.path,
                               stroke_color='black',
                               fill_color=self.fill_color)
        self.sprite = SpriteNode(None, scale=1, z_position=10)  #empty for now  
        self.origin = self.get_origin() # centre offset to allow for tabs

        self.id = 0  # creation order
        self.row = 0  # grid row
        self.col = 0. # grid col
        self.order = 0  # order of placement in clockwise spiral
        self.placed = False  # set when piece is in correct position
        self.image_position = Point(0,0) # stores correct sprite position

    def to_path(self, path_points):
        #path_points = path_points * np.array([1, -1])
        pth = ui.Path()
        pth.move_to(*path_points[0])
        [pth.line_to(*p) for p in path_points[1:]]
        pth.close()
        return pth        
            
    def bezier_curve(self, p0, p1, p2, p3, p4,  t, pz=1.0):
        """Quartic Bézier curve function.
      Args:
          p0 and p4 are the start and end points of the curve.
          p1 and p3 are the control points that define the shape and curvature of the line.          
          p2 controls the flatness
          t is a parameter that varies from 0 to 1, tracing the curve.
             
             p1
                   p2      
                          p3            
           p0      |        p4
        """
        
        return (1 - t)**4 * p0 + 4 * (1 - t)**3 *t * p1 + 6 * (1 - t)**2 * t**2 * p2 + 4*t**3 * (1-t) * p3 + t**4 * p4
            
    def draw_jigsaw_piece(self, type_='IOOI'):
        """
      Draws a single jigsaw puzzle piece. 
      origin is top left, y goes downwards
      Use quartic Bezier curve,  with  control point in the centre
      to control flatness of top of tab
  
      Args:          
          cx, cy: Coordinates for the start of the piece (bottom left) #center of the piece.
          type_: 4 character string using O for  tab, I for blank and S for straight
          size: Overall size of the square base of the piece.
          tab_depth: How far the tab/blank extends from the square.
          tab_width_factor: Controls the width of the tab/blank relative to the side.
          bulge: controls width of tab 1< bulge < 5
          skeww: controls symmetry across -0.9 < skew < 0.9
          skewh: controls symmetry vertically -0.9 < skew < 0.9
          flat: controls squareness -0.5 < flat < 1.5 (1.0 is unchanged, 0 is square)
               < skewh >
               <     bulge        >           
          ^   p2                                  
      skewh  
          v            p1   ^          ^
                          flat
                                   p3 tab depth       
           p0           |    v  p4     v
            <   tab width  >     
      """
        size = self.X
        half_ = size / 2.0
        half_tab = size * self.tab_width_factor / 2.0
        self.tab_depth = self.tab_depth * size
        flat = self.flat
        dirn_ = {'I': 1.0, 'O': -1.0, 'S': 0.0}
        # Define the core square corners
        cx, cy = half_, half_
        p_tl = np.array([cx - half_, cy - half_])  # Top-left
        p_tr = np.array([cx + half_, cy - half_])  # Top-right
        p_br = np.array([cx + half_, cy + half_])  # Bottom-right
        p_bl = np.array([cx - half_, cy + half_])  # Bottom-left
        b1 = half_tab * self.bulge * (1 + self.skeww)
        b2 = half_tab * self.bulge * (1 - self.skeww)
        s1 = (1 + self.skewh) * self.tab_depth
        s2 = (1 - self.skewh) * self.tab_depth
        f1 = self.tab_depth * self.flat
        top = cy - half_
        bottom = cy + half_
        left = cx - half_
        right = cx + half_

        t_values = np.linspace(0, 1, self.bz_points)  # For smooth curves

        # get max y
        p0 = np.array([cx - half_tab, 0])
        p4 = np.array([cx + half_tab, 0])        
        p1 = np.array([cx - b2, s1])
        p2 = np.array([cx, f1])
        p3 = np.array([cx + b1, s2])        
        points = [self.bezier_curve(p0, p1, p2, p3, p4, t) for t in t_values]
        self.extra = max([p[1] for p in points])

        path_points = []
        # clockwise from top left
        # --- Side 1 (Top) ---
        # Start at top-left corner of the core square
        path_points.append(p_tl)
        dy = dirn_[type_[0]]
        # Define control points for the blank
        p0 = np.array([cx - half_tab, top])
        p4 = np.array([cx + half_tab, top])        
        p1 = np.array([cx - b2, top + dy * s1])
        p2 = np.array([cx, top + dy * f1])
        p3 = np.array([cx + b1, top + dy * s2])
        
        points = [self.bezier_curve(p0, p1, p2, p3, p4, t) for t in t_values]
        path_points.extend(points)

        # --- Side 2 (Right) ---
        # Continue to top-right corner of the core square
        path_points.append(p_tr)
        dx = -dirn_[type_[1]]  # Innie gies left

        # Define control points for the tab
        p0 = np.array([right, cy - half_tab])
        p4 = np.array([right, cy + half_tab])
        p1 = np.array([right + dx * s1, cy - b2])
        p2 = np.array([right + dx * f1, cy])
        p3 = np.array([right + dx * s2, cy + b1])        
        points = [self.bezier_curve(p0, p1, p2, p3, p4, t) for t in t_values]
        path_points.extend(points)

        # --- Side 3 (Bottom) ---
        path_points.append(p_br)
        dy = -dirn_[type_[2]]  # Innie goes up

        # Define control points for the blank
        p0 = np.array([cx + half_tab, bottom])
        p4 = np.array([cx - half_tab, bottom])
        p1 = np.array([cx + b1, bottom + dy * s2])
        p2 = np.array([cx, bottom + dy * f1])
        p3 = np.array([cx - b2, bottom + dy * s1])        
        points = [self.bezier_curve(p0, p1, p2, p3, p4, t) for t in t_values]
        path_points.extend(points)

        # --- Side 4 (Left) ---
        path_points.append(p_bl)
        dx = dirn_[type_[3]]

        # Define control points for the blank       
        p0 = np.array([left, cy + half_tab])
        p4 = np.array([left, cy - half_tab])
        p1 = np.array([left + dx * s2, cy + b1])
        p2 = np.array([left + dx * f1, cy])
        p3 = np.array([left + dx * s1, cy - b2])        
        points = [self.bezier_curve(p0, p1, p2, p3, p4, t) for t in t_values]
        path_points.extend(points)

        # Close the path by returning to the starting point (p_bl)
        path_points.append(p_tl)
        # Create a Path object from the points
        path_points = np.array(path_points)
        # create ui.Path
        return self.to_path(path_points)
        
    def pil2ui(self, pil_image):
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        return ui.Image.from_data(buffer.getvalue(), 1)
        
    def create_path(self, type_str='SOIS'):
        ui.set_color('red')
        path = self.draw_jigsaw_piece(type_=type_str)
        path.line_width = 2
        path.line_join_style = ui.LINE_JOIN_ROUND
        path.fill()
        return path
    
    def copy_path(self):
        # used for the transformation
        new = ui.Path()
        new.append_path(self.path)
        new.line_join_style = self.path.line_join_style
        new.line_width = self.path.line_width
        return new

    def move_path(self):
        # move the path to align with the image for cutting
        new_path = self.copy_path()
        transform = objc_util.CGAffineTransform(a=1,
                                                b=0,
                                                c=0,
                                                d=1,
                                                tx=self.extra,
                                                ty=self.extra)
        objcpath = objc_util.ObjCInstance(new_path)
        objcpath.applyTransform(transform)
        return new_path
        
    def cut_image_with_custom_path(self, img):
        
        # Load the image
        img_width, img_height = img.size
        # Create an ImageContext with the same size as the original image (or desired output size)
        # The image will be clipped to the path's bounds.
        with ui.ImageContext(img_width + 2 * self.extra,
                             img_height + 2 * self.extra) as ctx:
            # Create a copy of the path and shift it
            path_copy = self.move_path()
            path_copy.add_clip()
            img.draw(0, 0, img_width, img_height)
            # Get the new clipped image
            clipped_image = ctx.get_image()
            return clipped_image
            
    def fill_with_image(self):
        """ Fill the image sprite with cropped and filled image part
        """
        x, y = Point(self.col * self.X,
                     self.row  * self.X) - (self.extra, self.extra)
        w = h = self.X + 2 * self.extra
        img_part = self.pil.crop((x, y, x + w, y + h))
        img_ = self.pil2ui(img_part)
        # this is centred on piece
        img_part_ = self.cut_image_with_custom_path(img_)
        self.sprite.texture = Texture(img_part_)
        self.sprite.alpha = 1
        #self.sprite.position = self.grid_to_pos(
        #                self.row, self.col) + self.grid_off + (self.extra, -self.extra)      
        
    def close_to_target(self, tol=None):
        """ return True if shape position is close to
        sprite position
        """
        try:
            target_loc = self.shape.position
            piece_loc = self.sprite.position
            dist = hypot(*(target_loc - piece_loc))
            if tol is None:
                tol = self.X / 2
            return dist < tol
        except AttributeError:
            return False
                                 
    def get_origin(self):
        """
        compute the coordinate of the centre of the box relative to
        centre of bounding box
        """
        bbox = self.path.bounds
        oversizex = (bbox.w - self.X) / 2
        oversizey = (bbox.h - self.X) / 2
        origin = Point(0, 0)
        Shape = namedtuple('Shape', ['N', 'E', 'S', 'W'])
        tile = Shape(*self.shape_str)
        # all Innie or side
        if (isclose(oversizex, 0, abs_tol=1e-3)
                and isclose(oversizey, 0, abs_tol=1e-3)):
            origin += (0, 0)
        # Outie on left, right or both
        elif isclose(oversizey, 0, abs_tol=1e-3):
            if tile.E == 'O' and tile.W == 'O':
                origin += (0, 0)
            elif tile.E != 'O' and tile.W == 'O':
                origin += (oversizex, 0)
            else:
                origin += (-oversizex, 0)
        # Outie on top, bottom or both
        elif isclose(oversizex, 0, abs_tol=1e-3):
            if tile.N == 'O' and tile.S == 'O':
                origin += (0, 0)
            elif tile.N != 'O' and tile.S == 'O':
                origin = (0, oversizey)
            else:
                origin += (0, -oversizey)
        # outie on two sides
        else:
            if tile.N == 'O' and tile.S == 'O':
                origin += (0, 0)
            elif tile.N != 'O' and tile.S == 'O':
                origin += (0, oversizey)
            else:
                origin += (0, -oversizey)
            if tile.E == 'O' and tile.W == 'O':
                origin += (0, 0)
            elif tile.E != 'O' and tile.W == 'O':
                origin += (oversizex, 0)
            else:
                origin += (-oversizex, 0)
        return origin
