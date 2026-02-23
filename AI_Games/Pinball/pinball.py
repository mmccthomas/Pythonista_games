# TODO
# get ball moving. DONE
# test ball loss. DONE
# test flipper action
# test wall action DONE
# test bounce action DONE
# test hole action

# core program produced by ai
# obtained pinball image
"""
2. Active Scoring Objects
These are "hot" components that react physically when struck.
• Pop Bumpers: Circular mushrooms that kick the ball away with high force when touched. Usually found in groups of three.
• Slingshots: The triangular bumpers located just above the flippers. They kick the ball horizontally to keep it in play.
• Spinners: Metal gates on a hinge that spin rapidly when hit, often used to build up "multipliers" or "miles."
• Drop Targets: Rectangular targets that physically retract into the playfield when hit. Clearing a bank of these often awards a bonus or opens a path.
That image shows a vibrant, somewhat stylized table layout. Based on standard pinball conventions, here is how those specific objects would likely react when the ball interacts with them:
1. The Launch and Lower Playfield
• The Plunger (Bottom Right): You’d pull this back to launch the ball up the right-hand Shooter Lane. The ball would then travel around the top arc (the Orbit) to enter the playfield.
• Flippers (Bottom Center): These are your primary controllers. You'd trigger them to hit the ball back up the table. In this specific design, they look positioned to easily feed the ball toward the central star target.
• Slingshots (The Black Triangular Blocks): Located just above the flippers, these usually have "kick" solenoids. If the ball hits the side of these, they will fire the ball horizontally with high velocity toward the opposite side of the table.
2. Mid-Field Interaction
• The Blue Bumpers/Rails: The long blue diagonal pieces appear to be Static Rails or Passive Bumpers. They likely guide the ball toward the center or provide a solid surface for the ball to ricochet off of to reach the upper targets.
• The Center Star Disc: This is a classic "Bash Toy" or Target Disc. In many games, hitting this might rotate the disc, light up a letter, or add a multiplier to your score.
• Orange Arrows: These are Roll-over Indicators. They tell the player where to aim. If the ball rolls over the light at the tip of the arrow, it usually triggers a specific game mode or "locks" a ball for multiball.
3. The Upper Scoring Zone
• Pop Bumpers (Small Circular Studs): The yellow, orange, and light blue circles spread across the top are likely Pop Bumpers. When touched, they would "pop" (kick) the ball away in a random direction, racking up quick points.
• The "Sun" Target (Top Center): The large pink and white circular object at the very top functions as a Top Bumper or a Sinkhole. If it's a hole, the ball would drop in, trigger a "Mystery Bonus," and then be kicked back out onto the playfield.
• Rollover Lanes (Points 10, 25, 50): At the very top, these three lanes award points based on which one the ball rolls through. Usually, if you light up all three, you get a "Bonus X" multiplier.
4. The "Danger" Zones
• Outlanes (Far Left and Right): The narrow paths on the outer edges (marked with the blue and red triangles) are the "drains." If the ball enters these, it's usually gone unless you have a "Kickback" activated.
• Inlanes: The paths directly next to the black slingshots are "safe" lanes that roll the ball cleanly down to your flipper for a controlled shot.

"""
from scene import Vector2, Rect, Scene, Texture, SpriteNode, ShapeNode, LabelNode
from scene import background, run
import math
import ui
import io
from time import time
import random
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
import json
import pathlib
import matplotlib.colors as mcolors
from change_screensize import get_screen_size



class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    
    
def get_bounding_box(coords):
    """ Computes x, y, w, h from a numpy array of  coordinates.
    """
    min_xy = np.min(coords, axis=0)
    max_xy = np.max(coords, axis=0)
    # Compute width and height
    wh = max_xy - min_xy
    return Rect(*min_xy, *wh)


class Wall:

    def __init__(self, name, centroid, coordinates, inside_wall=True):
        self.name = name
        self.centroid = Vector2(*centroid)
        self.coordinates = coordinates
        self.node = None
        self.inside_wall = inside_wall
        self.bbox = get_bounding_box(self.coordinates)
        self.pos = self.bbox.center()
        self.bounce = 0.7

    def draw_(self):
        # Draw Wall
        coords = np.array([1, -1]) * self.coordinates
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        self.path = path
        return path
   




class Switch:

    def __init__(self, name, centroid, coordinates, action, score):
        self.name = name
        self.centroid = Vector2(*centroid)
        self.coordinates = coordinates
        self.score = score
        self.action = action
        self.node = None
        self.bbox = get_bounding_box(self.coordinates)
        self.pos = self.bbox.center()
        self.bounce = 0
        self.logged = False

    def draw_(self):
        coords = np.array([1, -1]) * (self.coordinates - self.pos)
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        self.path = path
        return path


class Flipper:

    def __init__(self, name, centroid, pivot,
                 length, coordinates,
                 min_angle=-20, max_angle=30, side=1):
        self.name = name
        self.pivot = pivot
        self.length = length
        self.inside_wall = True
        self.centroid = Vector2(*centroid)
        self.bounce = 1.2
        #self.min_angle = min_angle * side
        #self.max_angle = max_angle * side
        self.side = side
        self.is_active = False
        self.angular_vel = 0
        self.coordinates = coordinates
        self.coordinates = coordinates
        
        self.node = None
        self.bbox = get_bounding_box(self.coordinates)
        self.pos = self.bbox.center()
        self.original_coordinates = np.copy(coordinates)  # ADD THIS
        self.original_center = np.array(self.bbox.center())  # ADD THIS
        # colour of flipper
        colordict = mcolors.CSS4_COLORS  # a curated list of colors
        colour_name = name.split(' ')[1]
        first_colour = colour_name.split('/')[0]
        self.color = colordict[first_colour]
        x, y = pivot - self.pos
        self.initial_angle = -math.degrees(math.atan(y/x))                                     
        # Angle limits are always expressed as offsets from initial_angle.
        # side flips the direction of travel so left and right behave the same.
        self.min_angle = self.initial_angle + min_angle * side
        self.max_angle = self.initial_angle + max_angle * side
        self.angle = self.min_angle
        print(f'{name=} {self.initial_angle=:.1f} {self.min_angle=:.1f} {self.max_angle=:.1f}')
        
    def draw_(self):
        coords = np.array([1, -1]) * (self.coordinates - self.pos)
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        self.path = path
        return path        
    
    def update(self):
        
        prev_angle = self.angle
        if self.is_active:
            self.angle = min(self.angle + 25, self.max_angle)            
        else:
            self.angle = max(self.angle - 12, self.min_angle)
        self.angular_vel = self.angle - prev_angle

        # always update, even though it takes time (<100us)                             
        self.node.rotation = np.radians(self.angle)
        
        # Always transform from ORIGINAL coordinates, not current
        position, _ = self.transform_perimeter(
             self.original_center,
             self.original_center,
             np.array(self.pivot),
             np.radians(self.angle))
 
        self.node.position = position
 
        self.coordinates, _ = self.transform_perimeter(
             self.original_coordinates,     # ← use originals
             self.original_center,          # ← use original center
             np.array(self.pivot),
             np.radians(self.angle)) 
        
 
 
    def rotation_matrix(self, angle_rad: float) -> np.ndarray:
        c, s = np.cos(angle_rad), np.sin(angle_rad)
        return np.array([[c, -s], [s,  c]])

    def rotate_point(self, point: np.ndarray, centre: np.ndarray, angle_rad: float) -> np.ndarray:
        """Rotate `point` around `centre` by `angle_rad`."""
        R = self.rotation_matrix(angle_rad)
        return centre + R @ (point - centre)
    
    def pivot_correction_translation(self, pivot: np.ndarray, centre: np.ndarray,
                                     angle_rad: float) -> np.ndarray:
        """
        Returns the translation vector T such that, after rotating all flipper
        points around `centre` by `angle_rad`, adding T keeps `pivot` stationary.
    
        Derivation
        ----------
        After rotation the pivot lands at:
            pivot' = centre + R @ (pivot - centre)
    
        We need every point shifted by T = pivot - pivot',
        which cancels the displacement of the pivot exactly.
        """
        pivot_rotated = self.rotate_point(pivot, centre, angle_rad)
        return pivot - pivot_rotated
    
    def transform_perimeter(self,
                            perimeter: np.ndarray,        # (N, 2) array of points
                            centre: np.ndarray,           # rotation centre
                            pivot: np.ndarray,            # stationary pivot point
                            angle_rad: float
                        ) -> tuple[np.ndarray, np.ndarray]:
        """
        Rotate all perimeter points around `centre`, then translate so `pivot`
        stays fixed.
    
        Returns
        -------
        transformed : (N, 2)  final positions of all perimeter points
        T           : (2,)    the single translation vector applied to every point
        """
        R = self.rotation_matrix(angle_rad)
        # Step 1 – rotate every point around the centre
        rotated = (centre + (R @ (perimeter - centre).T).T)
        # Step 2 – compute & apply pivot-correction translation
        T = self.pivot_correction_translation(pivot, centre, angle_rad)
        transformed = rotated + T
        return transformed, T
        
    def pil_to_ui(self, img):
        with io.BytesIO() as bIO:
          img.save(bIO, 'png')
          return ui.Image.from_data(bIO.getvalue())      
          
    def remove_image_under_flipper(self, obj):
     
        X, Y, W, H = obj.back_image.bbox
        w1, h1 = obj.img.size
        scale = np.array([W / w1, H / h1])
        offset = np.array([X, Y + H])
        scale_length = min(W / w1, H / h1)
        # x -> x, y -> H -y
        invert = np.array([1, -1])        
            
        def inverse_convert_function(transformed):
            return (transformed - offset) / invert / scale 
            
        # it would be nice to make the flipper have part of the image, and to null
         # original centroid 691, 1376
         # first coord 762, 1322                     
         # scaled centroid 755, 144
         # first 797, 144                 
        # out the base image in that location                
        # Create a mask for the polygon region
        coords = inverse_convert_function(np.copy(self.coordinates))
        # Apply (x, H - y)
        
        mask = Image.new('L', obj.img.size, 0)
        boundary = [tuple(p) for p in coords]
        ImageDraw.Draw(mask).polygon(boundary, outline=255, fill=255)        
     
        # Method 2: Crop to bounding box of the polygon        
        bbox = (*np.min(coords, axis=0), 
                *np.max(coords, axis=0))
        
        # Crop both image and mask
        cropped_img = obj.img.crop(bbox)
        cropped_mask = mask.crop(bbox)
        
        # Apply mask to cropped image
        cropped_rgba = cropped_img.convert('RGBA')
        cropped_rgba_array = np.array(cropped_rgba)
        cropped_mask_array = np.array(cropped_mask)
        cropped_rgba_array[:, :, 3] = cropped_mask_array
        
        result_cropped = Image.fromarray(cropped_rgba_array)
        result_cropped.show()
        #result_cropped = result_cropped.reduce(int(h1/H))
        # logger.debug(f"Cropped image size: {result_cropped.size}")
        #self.node.texture = Texture(self.pil_to_ui(result_cropped))
        return result_cropped
        
    def get_endpoints(self):
        rad = math.radians(self.angle * self.side)
        # For the right flipper, we flip the X direction
        tip_x = self.pivot.x + math.cos(rad) * self.length * self.side
        tip_y = self.pivot.y + math.sin(rad) * self.length * self.side
        return self.pivot, Vector2(tip_x, tip_y)
    

class Bumper:

    def __init__(self, name, centroid, radius, score, bounce):
        self.name = name
        self.pos = np.array(centroid)
        self.radius = radius
        self.score = score
        self.bounces = True
        self.bounce = bounce
        self.node = None
        self.coordinates = self.circle_points()

    def draw_(self):
        # Draw Bumper
        color = (1, 0.2, 0.5) if self.score % 100 < 50 else (0.2, 1, 0.5)
        ui.set_color(color)
        path = ui.Path.oval(*(self.pos- self.radius),
                            self.radius * 2, self.radius * 2)
        path.line_width = 3
        path.fill()
        self.path = path
        return path

    def circle_points(self, n=90):
       angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
       x = self.pos[0] + self.radius * np.cos(angles)
       y = self.pos[1] + self.radius * np.sin(angles)
       return np.column_stack((x, y))


class Ball:

    def __init__(self, pos=(500, 900), radius=12):
        self.pos = np.array(pos)
        self.vel = np.array([0, 12])
        self.radius = radius
        self.node = None
        self.start_pos = pos
        self.plunger_channel = None
        
    def update(self):
       self.node.position = self.pos
       
    def place_start(self, objects):
        y_vel = random.randint(21,35)
        self.vel = np.array([0, y_vel])
        plunger = self.plunger_channel # a Rect
        
        
        self.start_pos = np.array(plunger.center())
        #self.start_pos=np.array([600, 900])
        #self.vel= np.array([0, -1])
        
    def draw_(self):
        # Draw Ball
        path = ui.Path.oval(*(self.pos - self.radius),
                            self.radius * 2, self.radius * 2)
        path.line_width = 3
        self.path = path
        return path

    def circle_points(self, n=9, arc=np.pi/2):
        # provide an arc of points around the direction vector
        # Calculate the magnitude (speed)
        magnitude = np.linalg.norm(self.vel)
        
        # Handle the case where the ball isn't moving
        if magnitude == 0:
            base_angle = 0.0
        else:
            # Get the angle of the velocity vector
            base_angle = np.arctan2(self.vel[1], self.vel[0])
        
        # Generate angles centered around the direction vector
        angles = np.linspace(base_angle - arc / 2, base_angle + arc / 2, n)
        x = self.pos[0] + self.radius * np.cos(angles)
        y = self.pos[1] + self.radius * np.sin(angles)
        return np.column_stack((x, y))

    def touch_point(self):
        # Calculate the magnitude (speed)
        magnitude = np.linalg.norm(self.vel)
        
        # Handle the case where the ball isn't moving
        if magnitude == 0:
            point  = self.ball.pos
        else: 
            # Normalize and scale by radius
            point = self.pos + self.radius * self.vel / magnitude 
        return point
        
    def get_plunger_channel(self, coords, x_tolerance=3):
        """ Attempt to identify plunger channel
        coords: Numpy array of [x, y] points of the table outline.
        x_tolerance: Max pixels x can drift while still being 'vertical'.
        """
        # 1. Isolate the right-side points
        x_outer = np.max(coords[:, 0])
        right_points = coords[coords[:, 0] > (x_outer -20)]
        
        # 2. Sort by Y descending (bottom to top)
        # Note: In most image systems, 'bottom' is the HIGHEST Y value.
        sorted_pts = right_points[right_points[:, 1].argsort()[::-1]]
        x_diffs = np.diff(sorted_pts, axis=0)
        indexes = np.where(np.abs(x_diffs[:,0]) < x_tolerance)
        y = sorted_pts[indexes]
        y_min = min(y[:,1])
        y_max = max(y[:,1])        
                        
        # 1. Define the expected lane width (approximate)
        # Most plunger lanes are very narrow.
        expected_width_range = (20, 60) # pixels, adjust based on image scale
        
        # 2. Search for points that fall within the same Y-range 
        # but are slightly to the left of our outer wall.
        inner_wall_candidates = coords[
            (coords[:, 1] >= y_min) & 
            (coords[:, 1] <= y_max) & 
            (coords[:, 0] > x_outer - expected_width_range[1]) &
            (coords[:, 0] < x_outer - 10) # At least 10px to the left
        ]
        # no inner wall found, use default
        if len(inner_wall_candidates) == 0:
            x_inner = x_outer - expected_width_range[1]
        else:
            # 3. Find the most frequent X-coordinate in this subset (the inner wall)        
            values, counts = np.unique(inner_wall_candidates[:, 0], return_counts=True)
            max_index = np.argmax(counts)    
            # Return the value at that index
            x_inner = values[max_index]        
        
        results = dotdict({
            "x_range": (x_inner, x_outer),
            "x_min": x_inner,
            "y_min": y_min,
            "height": (y_max -  y_min),
            "width": x_outer - x_inner,
            "rect": Rect(x_inner, y_min, x_outer - x_inner, y_max -  y_min)
        })
        self.plunger_channel = results.rect
        return results
                
class Pinball(Scene):

    def __init__(self, pinball_image):
        Scene.__init__(self)
        self.score = 0
        self.timer = .02
        self.gravity = np.array([0, -0.1])
        self.image = pinball_image
        self.json = self.image.with_suffix('.json')
        
        self.back_image = self.draw_image()
        self.locations = self.extract_coordinates_from_json()
        self.set_objects()
        self.create_shapes()

    # @ui.in_background
    def draw_image(self):
        w, h = get_screen_size()
        img = Image.open(self.image)
        
        
        self.map_image = ui.Image.named(self.image.name)
        back_image = SpriteNode(Texture(self.map_image),
                                position=(w / 2, h / 2),
                                parent=self)
        back_image.anchor_point = (0.5, 0.5)
        back_image.z_position = 1
        i_w, i_h = self.map_image.size
        back_image.x_scale = h / i_h
        back_image.y_scale = h / i_h
        self.img = img # img.resize((int(img.size[0] * h / i_h), int(img.size[1] * h / i_h)))
        back_image.alpha = 0.5
        return back_image

    def print_centroids(self):
        for category in self.objects.values():
            for name, item in category.items():
                parameter = "centroid"
                if parameter in item:
                    print(name, item[parameter])

    def extract_coordinates_from_json(self):
        """ Structure is
         "image": {"name": {"reduction", "image_size"},
        "outline": {"name": {"centroid", coordinates"}...,
        "bumper": {"name": {"centroid","radius","score", "bounce"}...,
        "switch": {"name": {"centroid","coordinates","action", "score"}...,
        "flipper": {"name": {"centroid","coordinates", "pivot","length"}...,
         "wall" : {"name": {"centroid", "coordinates"}...}
        """
        with open(self.json, 'r') as f:
            self.objects = json.load(f)
        
        image_section = self.objects.get("image", {})    
        for name_key, values in image_section.items():                
            w1, h1 = values.get("image_size", self.map_image.size)
                                       
        
        X, Y, W, H = self.back_image.bbox
        
        scale = np.array([W / w1, H / h1])
        offset = np.array([X, Y + H])
        scale_length = min(W / w1, H / h1)
        # x -> x, y -> H -y
        invert = np.array([1, -1])

        def convert_function(coords):
            # x -> x * W/w + X
            # y -> (H - y)* H/h + Y
            arr = np.array(coords)
            transformed = arr * invert * scale + offset
            return transformed.astype(int)
            
        def inverse_convert_function(transformed):
            return (transformed - offset) / invert / scale 
            
        def convert_length(length):
            return int(length * scale_length)
        
        # scale to image representation
        for category in self.objects.values():
            for item in category.values():
                for parameter in ["coordinates", "centroid", "pivot"]:
                    if parameter in item:
                        item[parameter] = convert_function(item[parameter])
                for parameter in ["radius", "length"]:
                    if parameter in item:
                        item[parameter] = convert_length(item[parameter])


    def emit_ball(self):
        self.ball.place_start(self.objects)
        self.ball.pos = self.ball.start_pos
        self.ball.update()

    def set_objects(self):
        # Process standard objects using dictionary unpacking
        self.walls = [
            Wall(name, **data) for name, data in self.objects['wall'].items()
        ]
        self.walls.extend([
            Wall(name, inside_wall=False, **data)
            for name, data in self.objects['outline'].items()
        ])
        
        self.switches = [
            Switch(name, **data)
            for name, data in self.objects['switch'].items()
        ]
        self.bumpers = [
            Bumper(name, **data)
            for name, data in self.objects['bumper'].items()
        ]

        self.flippers = [
            Flipper(name,
                    min_angle=-20,
                    side=(1 if 'left' in name.lower() else -1),
                    **data) for name, data in self.objects['flipper'].items()
        ]
        # check only 2 flippers
        # create dict with side as key. this keeps them unique
        unique_flippers = {f.side: f for f in self.flippers}
        self.flippers = list(unique_flippers.values())
        self.left_flip = unique_flippers[1]
        self.right_flip = unique_flippers[-1]

        self.ball = Ball()

    def create_shapes(self):
        # create on screen shapes
        background(0.05, 0.05, 0.1)
        # Note: **{**params,'min_size': (80, 32)} overrides parameter
        params = {
            'anchor_point': (0.5, 0.5),
            'z_position': 10,
            'parent': self,
            'fill_color': 'clear',
            'stroke_color': 'green'
        }

        for wall in self.walls:
            path = wall.draw_()
            wall.node = ShapeNode(path=path, position=wall.pos, **params)
            
        for wall in self.walls:
           if wall.inside_wall is False:
            outline = wall
            break        
        
        channel = self.ball.get_plunger_channel(outline.coordinates, x_tolerance=3)
        self.ball.plunger_channel = channel.rect
        path = ui.Path.rect(*channel.rect)
        ShapeNode(path=path, position=channel.rect.center(),  **{**params,
                          'stroke_color': 'black'})
        
        for bumper in self.bumpers:
            path = bumper.draw_()
            bumper.node = ShapeNode(path=path,
                                    position=bumper.pos,
                                    **{**params,
                                       'stroke_color': 'red'})

        for switch in self.switches:
            path = switch.draw_()
            switch.node = ShapeNode(path=path, position=switch.pos, **params)

        for flipper in self.flippers:
            path = flipper.draw_()
            flipper.node = ShapeNode(path=path, position=flipper.pos,
             **{**params, 'fill_color': flipper.color,
                          'stroke_color': 'white'})
            size=10 
            path = ui.Path().oval(*(flipper.pivot - size/2),size, size)                                           
            ShapeNode(path=path, position=flipper.pivot,
             **{**params, 'fill_color': 'white',
                          'stroke_color': 'white'})
                          
            # flipper.remove_image_under_flipper(self)           
  
        path = self.ball.draw_()
        self.ball.node = SpriteNode(Texture('pzl:BallGray'),
                                    anchor_point=(0.5, 0.5),
                                    z_position=10, 
                                    size=(self.ball.radius*2, self.ball.radius*2),
                                    parent=self) 
                               
        #self.ball.node = ShapeNode(path=path,
        #                           **{**params, 'fill_color': (1.0, 1.0, 1.0, 0.9),
        #                              'stroke_color': 'white'})
        self.emit_ball()

        # Draw Score
        self.score_node = LabelNode(text=f'SCORE: {self.score}',
                                    font=('Helvetica', 30),
                                    color='white',
                                    position=(100,self.size.h - 200),
                                    z_position=10,
                                    parent=self)

    def update(self):
        self.timer -= self.dt        
        if self.timer <= 0:
            self.timer = .02
            
            self.ball.vel = self.ball.vel + self.gravity
            self.ball.pos = self.ball.pos + self.ball.vel
            self.ball.update()
                    
            # 1. Reset if out of bounds
            min_y = [wall.bbox for wall in self.walls if not wall.inside_wall][0][1] +10
            if self.ball.touch_point()[1]< min_y:
                self.emit_ball()
                  
            for flipper in self.flippers:
                flipper.update()                                
        
            for flipper in self.flippers:
                self.collide_flipper(flipper)
    
            for wall in self.walls:
                self.collide_wall(wall)
    
            for bumper in self.bumpers:
                self.collide_bumper(bumper)
                
            for switch in self.switches:
                self.collide_switch(switch) 
                                
            self.score_node.text = f'SCORE: {self.score}'                        

    def hit_test(self, path, point, inside=True):
        """
        Determines if a point is inside a polygon path.
        
        Args:
            path (np.ndarray): Array of shape (N, 2) representing (x, y) vertices.
            point (np.ndarray): Array of shape (2,) representing the (x, y) point.
            
        Returns:
            bool: True if the point is inside the path.
        """
        x, y = point
        # Ensure the path is closed by connecting the last point to the first
        # This creates the edges: (p0, p1), (p1, p2) ... (pN, p0)
        v1 = path
        v2 = np.roll(path, -1, axis=0)        
        dy = v2[:, 1] - v1[:, 1]        
        # Avoid division by zero; horizontal edges are excluded by the straddle check anyway
        safe_dy = np.where(dy == 0, 1, dy)
        
        straddle = (v1[:, 1] > y) != (v2[:, 1] > y)
        intersect = x < (v2[:, 0] - v1[:, 0]) * (y - v1[:, 1]) / safe_dy + v1[:, 0]
        # Check if the point's Y-coordinate is between the Y-coordinates of the edge vertices
        # and if the point is to the left of the edge's horizontal intersection
        mask = straddle & intersect
        # If the number of intersections is odd, the point is inside
        return np.sum(mask) % 2 == int(inside)                        

    def get_closest_vectors(self, path, point):
        # all vectors are numpy arrays
        # 1. Clean path (remove consecutive duplicates)
        mask = np.any(np.diff(path, axis=0, append=path[:1]), axis=1)
        clean_path = path[mask]
        
        # 2. Winding order for outward normal
        x, y = clean_path[:, 0], clean_path[:, 1]
        area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
        is_ccw = area > 0
    
        v1 = clean_path
        v2 = np.roll(clean_path, -1, axis=0)
        
        # Segment vectors and squared lengths
        segments = v2 - v1
        seg_sq_lens = np.sum(segments**2, axis=1)
        
        # 3. Find projection factor 't' for each segment
        # t is the progress along the segment from 0.0 to 1.0
        p_minus_v1 = point - v1
        dot_products = np.sum(p_minus_v1 * segments, axis=1)
        
        # Avoid division by zero for any remaining degenerate segments
        t = np.zeros_like(dot_products)
        nonzero = seg_sq_lens > 1e-12
        t[nonzero] = dot_products[nonzero] / seg_sq_lens[nonzero]
        t = np.clip(t, 0, 1) # Keep projection within the segment bounds
        
        # 4. Calculate closest point on each segment
        closest_points = v1 + t[:, np.newaxis] * segments
        
        # 5. Find the segment with the minimum distance
        distances_sq = np.sum((point - closest_points)**2, axis=1)
        best_idx = np.argmin(distances_sq)
        
        actual_closest_point = closest_points[best_idx]
        
        # 6. Derive Tangent and Outward Normal
        seg_vec = segments[best_idx]
        seg_len = np.sqrt(seg_sq_lens[best_idx])
        
        tangent = seg_vec / seg_len
        tx, ty = tangent
        
        # CCW: Outward is (ty, -tx) | CW: Outward is (-ty, tx)
        normal = np.array([ty, -tx]) if is_ccw else np.array([-ty, tx])
            
        return actual_closest_point, tangent, normal
        
    def deflect_ball(self, point, object, closest, normal):
        """ Deflect a ball based on its location, object type, 
            closest object point and normal vector """
        if object is self.left_flip or object is self.right_flip :
                pass 
                                    
        # Ensure normal points away from wall toward ball center
        to_ball = point - closest
        vector = np.dot(to_ball, normal)
        #print('normal', np.degrees(np.arctan2(normal[1], normal[0])))
        if vector < 0:
            normal = -normal  # cleaner negation 
        #print('normal', np.degrees(np.arctan2(normal[1], normal[0])))
        # print('ball velocity', np.degrees(np.arctan2(self.ball.vel[1], self.ball.vel[0])))
        # Recompute dist as the actual penetration depth to be safe
        dist = self.ball.radius - np.linalg.norm(to_ball) # penetration amount
        
        if dist > 0:
            # Push ball out along normal by exact penetration depth
            self.ball.pos = self.ball.pos - normal * dist
        
        # Reflect velocity along normal, apply restitution
        vel_along_normal = np.dot(self.ball.vel, normal)
        if vel_along_normal > 0:  # only reflect if moving INTO the wall
        
            self.ball.vel = self.ball.vel - (1 + object.bounce) * vel_along_normal * normal
    
        # Add flipper kick
        if isinstance(object, Flipper):
          #print('hit flipper')
          f_vel = object.angular_vel
          if f_vel > 0:
              self.ball.vel = self.ball.vel + normal * f_vel * object.bounce
                                                  
    def collide_wall(self, wall):
        """ detect wall crossing and deflect """               
        coords = wall.coordinates
        for point in self.ball.circle_points():
            if self.hit_test(coords, point, inside=wall.inside_wall):                            
                closest, tangent, normal = self.get_closest_vectors(coords, point)
                self.deflect_ball(point, wall, closest, normal)
                        
    
    def collide_bumper(self, bumper):
        """ detect bumper hit, deflect and score """   
        coords = bumper.coordinates    
        for point in self.ball.circle_points():
            if self.hit_test(coords, point, inside=True):                 
                closest, tangent, normal = self.get_closest_vectors(coords, point)
                
                self.deflect_ball(point, bumper, closest, normal)       
                self.score += bumper.score
                break
                
    def collide_flipper(self, flipper):
        """Detect flipper collision using distance to line segment."""
        coords = flipper.coordinates
        
        # Find the two endpoints of the flipper (the longest diagonal)
        # Use the pivot and the tip (furthest point from pivot)
        pivot = np.array(flipper.pivot)
        distances_from_pivot = np.linalg.norm(coords - pivot, axis=1)
        tip = coords[np.argmax(distances_from_pivot)]
        
        # Find closest point on the pivot->tip line segment to ball center
        segment = tip - pivot
        seg_len_sq = np.dot(segment, segment)
        
        if seg_len_sq < 1e-12:
            return  # Degenerate flipper
        
        # Project ball center onto segment, clamp to [0,1]
        t = np.dot(self.ball.pos - pivot, segment) / seg_len_sq
        t = np.clip(t, 0.0, 1.0)
        closest = pivot + t * segment
        
        # Vector and distance from closest point to ball center
        to_ball = self.ball.pos - closest
        dist = np.linalg.norm(to_ball)
        
        # Flipper half-thickness (adjust to match your visual flipper width)
        flipper_thickness = 8  
        
        if dist < self.ball.radius + flipper_thickness:
            # Normal points from flipper surface toward ball
            if dist > 1e-9:
                normal = to_ball / dist
            else:
                # Ball exactly on segment - use perpendicular to segment
                seg_norm = segment / np.sqrt(seg_len_sq)
                normal = np.array([-seg_norm[1], seg_norm[0]])
            
            # Push ball out of flipper
            penetration = (self.ball.radius + flipper_thickness) - dist
            self.ball.pos += normal * penetration
            
            # Reflect velocity
            vel_along_normal = np.dot(self.ball.vel, normal)
            if vel_along_normal < 0:  # Moving toward flipper
                self.ball.vel -= (1 + flipper.bounce) * vel_along_normal * normal
            
            # Add angular kick from flipper motion
            if flipper.angular_vel > 0:
                # Scale kick by position along flipper (more kick near tip)
                kick_scale = t  # 0 at pivot, 1 at tip
                self.ball.vel += normal * flipper.angular_vel * flipper.bounce * kick_scale
                                  
    def collide_switch(self, switch):
        # switch does some action and/or scores poiints
        # it does not deflect
        # shoukd only register once until ball is outside
        coords = switch.coordinates                         
        for point in self.ball.circle_points():
          if self.hit_test(coords, point):
            if not switch.logged:
               switch.logged = True
               try:
                 switch.action()
               except TypeError as e:
                 pass
                 #print(f'action {switch.action} is missing {e}')
          else:
               switch.logged = False
          
                      
    def touch_began(self, touch):
        if touch.location.x < self.size.w / 2:
            self.left_flip.is_active = True
        else:
            self.right_flip.is_active = True

    def touch_ended(self, touch):
        self.left_flip.is_active = False
        self.right_flip.is_active = False

def main(image_name):     
     g = Pinball(pathlib.Path(image_name))
     run(g)
     return g
     
 
if __name__ == '__main__':
    main('pinball1.png')

