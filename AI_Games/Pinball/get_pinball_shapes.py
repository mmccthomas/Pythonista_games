"""
# TODO list
# positioning not quite correct when size changes between sessions
# added did change size. objects correct, outline not correct
# consider whether to implement horizontal slingshot


   Combined Pinball Editor and Player
   
   Structure notes:
    
   There are two classes
   ProcessShapes
   PinballCreate
   
   also uses
   ball_physics.py
   feature_detection.py
   identify_shapes.py
   
   
   4 outlines are coded in outline_set.json along with bespoke backgrounds
   Ensure that the bottom of plunger channel is square

   shapes are extracted from two or more sprite sheets. Not all items on the sheets are used.
   
   Claude AI recommended a lookup catalogue for shape fingerprint
   A parameter in get_shapes_identified allows viewing and naming of sprites
   name each shape and assign to wall, bumper, flipper, guide, sling or switch
   The catalogue stores shape names and a digest of the shape coordinates

   if sprites are renamed, sprite_fingerprints.json will need to be modified
   this can be done manually
   
   save and load:
   extract important details of placed objects
   id, object name, placed centroid, scale, rotation, mirror, colour
   id is simply used to ensure objects are unique

   sprite names have been changed to be consistent:
   all begin with: guide sling guide wall switch button bumper flipper
   switch and button action are generated from sprite_name
   for switches and buttons, action is name after 'button' or 'switch'
   
   actions can access physics methods and receive switch object,
   e.g. allow deflection under some conditions (see def arrow(self, switch))

   all images stored in Shapes are on transparent background of size to allow rotation

Design Notes:
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
from PIL import Image
import numpy as np
from scene import Texture, SpriteNode, ShapeNode, Scene, run, LabelNode, Touch, Point, Action
import matplotlib.pyplot as plt
import io
import ui
import re
import uuid
import json
import console
import dialogs
from time import time, sleep
from change_screensize import get_screen_size

import base_path
base_path.add_paths(__file__)
from Utilities.scanning.feature_detection import FeatureExtract, FastContourDetector, Shape
from gui.custom_ui import TickedSliderView
from ball_physics import Physics, Wall, Flipper, Ball, Bumper, Switch
from identify_shapes import register_sprites, load_catalogue, identify_shape, list_registered_sprites
from identify_shapes import remove_from_catalogue


def pil_to_ui(img):
    with io.BytesIO() as bIO:
        img.save(bIO, "png")
        return ui.Image.from_data(bIO.getvalue())

                
class ProcessShapes():
    def __init__(self, outline_name):
        # take a spritesheet and decode the sprites
        # sprite names should begin with one of
        # flipper, guide, sling, wall, bumper, button, switch
        self.outline_name = outline_name
                
        self.WALL_SPRITES = {'guide_l': 1, 'guide_r': 1, 'sling_l': 1.1, 'sling_r': 1.1, 'wall short_h': 1,
                             'guide_r2': 1,  'wall_2': 1,
                             'wall_1': 1, 'wall grey_vert': 1, 'wall half_round': 1.2, 'wall_3': 1}
        self.SWITCH_SPRITES = ['button x5', 'button x3', 'button x2',
                               'switch vert', 'button red', 'button hole',
                               'switch arrow', 'switch yellow_arrow',
                               'button again', 'button blue_sparkle',
                               'button orange_trapeze', 'button triangle']
                         
        self.BUMPER_SPRITES = {'bumper x30': (1.1, 30), 'bumper x10': (1.1, 10),
                               'bumper x20': (1.1, 20), 'bumper star': (1.0, 50),
                               'bumper yellow_x50': (1.1, 50),
                               'bumper sparkle': (1.0, 10),
                               'bumper blue_x25': (1.1, 25),
                               'bumper red_x100': (1.1, 100)}
        self.FLIPPER_SPRITES = {'flipper_l': 1, 'flipper_r': 1}
        
        self.shapes = self.get_shapes_identified(registration_mode=False)
        self.outline = self.make_outline(outline_name)
    
    def build_physics_objects(self, placed_shapes, switch_callbacks):
        """
        Translate editor Shape objects into physics objects.
        score_callbacks: dict mapping sprite_name -> callable, supplied by the Scene.
        Returns walls, flippers, bumpers, switches — no Scene dependencies.
        """
                 
        walls = []
        switches = []
        bumpers = []
        flippers = []
        
        for shape in placed_shapes:
         
            name = shape.sprite_name
            
            if name in self.WALL_SPRITES:
                wall = Wall(shape.description, shape.centroid, shape.coordinates)
                wall.bounce = self.WALL_SPRITES[name]
                walls.append(wall)
                
            elif name in self.SWITCH_SPRITES:
                switch = Switch(shape.description, shape.centroid, shape.coordinates,
                                action=switch_callbacks.get(name, None), score=0)
                switch.angle = shape.angle
                switch.inside_wall = True
                switches.append(switch)
            elif name in self.BUMPER_SPRITES:
                bounce, score = self.BUMPER_SPRITES[name]
                bumper = Bumper(shape.description, shape.centroid, shape.radius,
                                score, bounce)
                bumpers.append(bumper)
                
            elif name in self.FLIPPER_SPRITES:
                flipper = Flipper(shape.description, shape.centroid, shape.pivot,
                                  shape.length, shape.coordinates,
                                  min_angle=0)
                flippers.append(flipper)
                
        return walls, flippers, bumpers, switches
            
    def get_shapes_identified(self, registration_mode: bool = False) -> list:
        """
        Extract shapes and identify them via fingerprints.
    
        Set registration_mode=True on first run (or when spritesheet changes)
        to interactively name each sprite and save fingerprints.
        Subsequent runs use the saved catalogue automatically.
        """
        NAME = "isolated-pinball-elements.png"
        NAME2 = 'pinball_parts2.png'
        list_registered_sprites()
        all_shapes = []
        for name in [NAME, NAME2]:
            shapes = self.extract_shapes(name, 0.1, 0.2, 2000, 4)
            all_shapes.extend(shapes)
        t = time()
        if registration_mode:
            catalogue = register_sprites(all_shapes)
        else:
            catalogue = load_catalogue()
            if not catalogue:
                print('No fingerprint catalogue found — run with registration_mode=True first.')
                return []
    
        identified = []
        unrecognised = []
    
        for shape in all_shapes:
            name = identify_shape(shape, catalogue)
            if name:
                shape.sprite_name = name
                identified.append(shape)
            else:
                unrecognised.append(shape)
        print(f'identify time {(time()-t)*1000:.2f}ms')
        if unrecognised:
            print(f'Warning: {len(unrecognised)} shapes were not recognised.')
            print('  Re-run with registration_mode=True to add them.')
    
        return identified
        
    def extract_shapes(self, image_path, canny_low, canny_high, edge_tries, size_reduction):
        image_process = FeatureExtract(
            image_path, None, canny_low, canny_high, edge_tries, size_reduction
        )
        # edges = image_process.edges
        # pil_image = Image.fromarray(edges.astype(np.uint8))
        # pil_image.show()
        detector = FastContourDetector(image_process=image_process)
    
        contours = detector.find_all_contours_ordered(100, None)
        shapes = detector.analyze_shapes(contours)
        shapes = detector.filter_duplicates(shapes, threshold=10)
            
        for i, shape in enumerate(shapes):
            is_teardrop = detector.process_teardrop(shape)
            if is_teardrop:
               # deal with flipper left, make it horizontal
               self.rotate_flipper(detector, image_process, shape)
            else:
                shape.image = image_process.crop_image(shape.coordinates)
                # put image onto square transparent background
                # this allows it to rotate without size change
                image = shape.transparent_rect()
                shape.set_image(image)
            shape.color_names = image_process.closest_colors(image)
            shape.quadrant = "_".join(image_process.quadrant(shape.centroid))
            shape.description = f"{shape.quadrant} {shape.color_names} {shape.shape}"
            # recentre to centre of shape and invert y since Scene uses 0,0 as bottom left
            # whereas shapes are referenced to top left
            shape.set_coordinates(shape.recentre().astype(int) * [1, -1])
            # decimate since we dont need so many points
            shape.set_coordinates(shape.coordinates[::10])
        return shapes
        
    def get_outlines(self):
        # dictionary to hold outline coordinates, background image and scale
        with open('outline_set.json', 'r') as f:
            outlines = json.load(f)
        return outlines
        
    def make_outline(self, outline_name):
        """ process shape data for the selected outline """
        outlines = self.get_outlines()
        self.outlines = list(outlines)
        points = outlines[outline_name]['coords']
        image_name = outlines[outline_name]['image']
        # scale not used
        # scale = outlines[outline_name]['scale']
        
        # make a dummy shape
        shape = Shape(centroid=(0, 0), circularity=0, coordinates=np.array(points), perimeter=1)
        outline_size = shape.bbox.size
        w, h = get_screen_size()
        # fit outline to screen vertical
        scale = 1.00 * h / outline_size.height
        shape.sprite_name = 'outline'
        shape.scale_path(scale)
        # just to get image
        f = FeatureExtract(image_name, canny_low=.8, canny_high=.8, edge_tries=1)
        bbox = shape.bbox
        # need to centre coordinates in image
        coord_centre = bbox.center()
        image_centre = Point(f.img.width/2, f.img.height/2)
        diff = image_centre - coord_centre
        shifted_coords = shape.coordinates + diff
        shape.image = f.img
        shape.set_image(f.crop_image(shifted_coords))
        # need to move coordinates to centre of image
        shape.recentre()
        # invert y since PIL coordinates are from topleft, whereas scene is bottomleft
        shape.set_coordinates(shape.coordinates * [1, -1])
        return shape
                            
    def plot_outline(self, coordinates, invert=True):
        # This is used during debug to plot and minimise outline points
        # x, y measured from top left, so invert y
        if invert:
            points = coordinates * np.array([1, -1])
        else:
            points = coordinates
        plt.cla()
        # Create the scatter plot
        plt.scatter(points[:, 0], points[:, 1], color='blue')
        
        # Label each point with its index number
        # enumerate gives both the index (i) and the coordinates (x, y)
        for i, (x, y) in enumerate(points):
            plt.annotate(
                str(i),                      # The text to display (index)
                (x, y),                      # The point to label
                textcoords="offset points",  # Position the text relative to the point
                xytext=(0, 10),              # Offset of 10 points above the point
                ha='center'                  # Horizontal alignment
            )
        plt.axis('equal')
        plt.minorticks_on()
        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.title('Plot of Points with Index Labels')
        plt.grid(True)
        plt.show()
    
    def rotate_flipper(self, detector, image_process, shape):
        """ Process the flipper image. rotate it to lie on x axis
            extract pivot offset from centre of image """
        shape.image = image_process.crop_image(shape.coordinates)
        # deal with flipper make it horizontal
        shape.coordinates, _, eigenvectors, shape.centroid = detector.pca(shape.coordinates)
        angle = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])
        
        shape.image = shape.transparent_rect()
        shape.set_image(shape.image.rotate(np.degrees(angle), expand=True))
        
        features = detector.calculate_shape_features(shape.coordinates)
        # compute pivot from radius of thicker end
        max_width = max(features['left_end_height'], features['right_end_height'])
        x1 = features['width'] / 2 - max_width / 2
        if features['left_end_height'] > features['right_end_height']:
            x1 = -x1
        shape.pivot = Point(x1, 0)  # rel to centre
        # length from pivot to thinner end
        shape.length = int(features['width'] - np.abs(x1))
                                                              
    def get_centre_line(self, coords, top=True):
        if top:
            y = np.max(coords[:, 1])
        else:
            y = np.min(coords[:, 1])
        
        top_points = coords[np.abs(coords[:, 1] - y) <= 2]
        # 3. Calculate the center (mean of x, keep max_y)
        center_x = np.mean(top_points[:, 0])
        return center_x
                                    

# ---------------Scene class
        
class PinballCreate(Scene):
    
    def setup(self):
        self.paused = True
        self.placed_shapes = []
        self.placed_objects = {}
        self.processed = ProcessShapes('outline4')
        self.shapes = self.processed.shapes
        self.outline_name = self.processed.outline_name
        w, h = self.size
        self.origin = Point(int(2 * w / 5), int(h / 2))
        self.palette_x = 0.95 * w
        self.grid_spacing = 50
        self.grid_snap = 5
        self.last_tap_time = 0
        self.double_tap_threshold = 0.3  # Seconds
        self.in_double_tap = False
        self.place_outline(self.processed.outline)
        self.create_scroll_palette()
        self.place_buttons()
        self.play = False
        self.edit = True
        
        self.message = LabelNode(text='message',
                                 position=(self.grid_box.bbox.max_x, 20),
                                 anchor_point=(0, 0),
                                 parent=self)
        self.restore(None)
        
    def send_message(self, text):
        self.message.text = text
        
    def place_buttons(self):
        # Create a native UI button
        def add_button(title, rect, image=None, action=None, color='cyan'):
            try:
                btn = ui.Button(title=title)
                if image:
                    btn.image = ui.Image.named(image)
                if isinstance(rect, int):
                   btn.frame = (rect, 10, 50, 50)
                else:
                    btn.frame = rect
                btn.background_color = 'clear'
                btn.tint_color = color
                if action:
                    btn.action = action
                self.view.add_subview(btn)
                return btn
            except AttributeError:
                print('no view yet')
        add_button(' Save', (30, 10, 50, 50), 'iow:ios7_upload_outline_256', self.save)
        add_button(' Load', (70, 10, 50, 50), 'iow:ios7_download_outline_256', self.restore)
        add_button(' Play', (30, 60, 50, 50), None, self.play_mode)
        add_button(' Edit', (70, 60, 50, 50), None, self.edit_mode)
        add_button(' Outline', (30, 110, 100, 50), None, self.select)
        
    def build_grid(self, alpha=0.8):
        """ define a grid to overlay on top of everything else
        allow offset to place grid at centre of square (e.g. go game)"""
        spc = self.grid_spacing
        grids_x = round(self.outline.bbox.width / spc)
        grids_y = round(self.outline.bbox.height / spc)

        with ui.ImageContext(grids_x * spc, grids_y * spc) as ctx:
            ui.set_color('lightgrey')
            for i in range(grids_y):
                # horizontal rectangle
                ui.Path.rect(0, i * spc, grids_x * spc, spc).stroke()
            for i in range(grids_x):
                # Vertical rectangle
                ui.Path.rect(i * spc, 0, spc, grids_y * spc).stroke()
                        
            img = ctx.get_image()
            
        return SpriteNode(Texture(img),
                          position=self.origin,
                          alpha=alpha,
                          parent=self)
 
    def set_score_node(self):
        # Draw Score
        self.score_node = LabelNode(text=f'SCORE: {self.score}',
                                    font=('Helvetica', 30),
                                    color='white',
                                    position=(self.grid_box.bbox.max_x, self.size.height-100),
                                    anchor_point=(0, 0),
                                    z_position=10,
                                    parent=self)
                                    
    def draw_(self, coords):
        # Draw coords
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        return path
        
    def place_plunger(self):
        """ define plunger box and place plunger image"""
        # place the plunger image
        outline_wall = Wall('outline', self.outline.centroid, self.outline.coordinates, inside_wall=False)
        plunger = outline_wall.get_plunger_channel()
        plunger_image = ui.Image.named('Plunger.jpeg')
        w, h = plunger_image.size
        
        xy = Point(int(plunger.x_min), int(plunger.y_min))
        x_scale = plunger.width / w
        # make plunger occupy 1/3 of channel
        y_scale = plunger.height / (3 * h)
        self.plunger_texture = Texture(plunger_image)
        position = self.origin + xy
        self.plunger_rect = plunger.rect.translate(*self.origin)
        self.plunger_y_scale = y_scale
        
        self.plunger = SpriteNode(self.plunger_texture,
                                  x_scale=x_scale, y_scale=y_scale,
                                  anchor_point=(0, 0),
                                  z_position=100,
                                  position=position,
                                  parent=self)
        
        self.plunger_outline = ShapeNode(ui.Path.rect(*self.plunger_rect),
                                         stroke_color='white',
                                         fill_color='clear',
                                         z_position=100,
                                         position=self.plunger_rect.center(),
                                         parent=self)
                              
    def place_outline(self, outline):
        # select and place outline
        w, h = self.size
                
        self.outline = outline
        self.outline.centroid = self.origin
        combined_image = self.outline.transparent_rect()
        self.outline_path = ShapeNode(path=self.draw_(self.outline.coordinates*[1, -1]),
                                      position=self.outline.centroid,
                                      z_position=10,
                                      fill_color="clear",
                                      stroke_color="green",
                                      parent=self)
        self.outline_node = SpriteNode(Texture(pil_to_ui(combined_image)),
                                       position=self.origin,
                                       parent=self)
        self.place_plunger()
        self.grid_box = self.build_grid()
        # self.placed_shapes.append(self.outline)

    def create_scroll_palette(self):
        sidebar_w = 200
        screen_w, screen_h = self.size
        
        self.scroll_container = ui.ScrollView()
        self.scroll_container.frame = (self.palette_x - sidebar_w, 0, sidebar_w, screen_h - 20)
        self.scroll_container.background_color = (0.4, 0.4, 0.4, 0.7)
        
        y_offset = 10
        item_h = 100  # Increased height to fit text
        # Arrangement of shapes in palette
        # The defined order of categories (the first word in the sprite name)
        category_order = ["flipper", "guide", "sling", "bumper", "wall", "button", "switch"]

        # Sort the shapes based on the index of their first word in the category_order list
        def get_shape_priority(shape):
            # 1. Extract the prefix (e.g., "flipper" from "flipper_l")
            prefix = re.split(r'[_ ]', shape.sprite_name)[0]
            
            # 2. Return the index if found, otherwise put it at the end
            if prefix in category_order:
                return category_order.index(prefix)
            return len(category_order)
        
        sorted_shapes = sorted(self.shapes, key=get_shape_priority)
               
        for shape in sorted_shapes:
            # 1. Create a container for this specific item
            container = ui.View(frame=(0, y_offset, sidebar_w, item_h))
            
            # 2. Setup the Sprite Image (Original Colors)
            ui_img = pil_to_ui(shape.image).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
            
            # The button acts as the visual sprite
            btn = ui.Button(frame=(10, 5, sidebar_w - 20, 65))
            btn.image = ui_img
            btn.shape_template = shape
            btn.action = self.spawn_from_tray
            
            # 3. Setup the Label
            lbl = ui.Label(frame=(0, 70, sidebar_w, 25))
            # Clean up the name (e.g., 'bumper_x10' -> 'Bumper X10')
            lbl.text = shape.sprite_name.replace('_', ' ').title()
            lbl.text_color = 'white'
            lbl.alignment = ui.ALIGN_CENTER
            lbl.font = ('<system-bold>', 15)
            
            # Add components to container, container to scrollview
            container.add_subview(btn)
            container.add_subview(lbl)
            self.scroll_container.add_subview(container)
            
            y_offset += item_h + 10
            
        self.scroll_container.content_size = (sidebar_w, y_offset)
        try:
            self.view.add_subview(self.scroll_container)
        except AttributeError:
            print('no view yet')

        # 2. Add the Collapse/Expand Button
        # Positioned just to the left of the tray
        self.tray_button = ui.Button(name='ToggleTray')
        self.tray_button.frame = (self.palette_x - sidebar_w - 45, 10, 40, 40)
        self.tray_button.background_color = (0.2, 0.2, 0.2, 0.8)
        self.tray_button.tint_color = 'white'
        self.tray_button.corner_radius = 20
        self.tray_button.image = ui.Image.named('iow:chevron_right_32')
        self.tray_button.action = self.toggle_tray
        try:
            self.view.add_subview(self.tray_button)
        except AttributeError:
            print('no view yet')

    def toggle_tray(self, sender):
        """Animates the tray sliding in and out."""
        sidebar_w = 200
        screen_w = self.size.w
        
        def animations():
            if self.scroll_container.hidden:
                # Slide In
                self.scroll_container.frame = (self.palette_x - sidebar_w, 0, sidebar_w, self.size.h - 100)
                self.tray_button.frame = (self.palette_x - sidebar_w - 45, 10, 40, 40)
                self.tray_button.image = ui.Image.named('iow:chevron_right_32')
            else:
                # Slide Out
                self.scroll_container.frame = (screen_w, 0, sidebar_w, self.size.h - 100)
                self.tray_button.frame = (screen_w - 45, 10, 40, 40)
                self.tray_button.image = ui.Image.named('iow:chevron_left_32')
                
        ui.animate(animations, duration=0.3)
        self.scroll_container.hidden = not self.scroll_container.hidden
        
    def select(self, sender):
        selection = dialogs.list_dialog(title='Select Outline', items=self.processed.outlines)
        if selection:
            self.outline_name = selection
            self.remove_placed_shapes()
            self.restore(None)
            self.refresh_layout()
            
    def remove_placed_shapes(self):
        for shape in self.placed_shapes:
            shape.node.remove_from_parent()
        self.placed_shapes = []
               
    def play_mode(self, sender):
        """ switch to play mode
        construct physics objects, initialise score
        and clean up editor
       
        switch_callbacks are the word following switch or button
        e.g. button x3 calls self.x3 """
         
        switch_callbacks = {}
        for shape in self.placed_shapes:
            # forget parameters after 2nd
            # a, b, *_  unpacks a tuple of any length and discards 3rd onwards
            shape_type, param, *_ = re.split(r'[_ ]', shape.sprite_name)
            if shape_type in ['switch', 'button']:
                action = getattr(self, param, None)  # set None if not found
                switch_callbacks[shape.sprite_name] = action
        
        outline_wall = Wall('outline', self.outline.centroid, self.outline.coordinates, inside_wall=False)
        walls, flippers, bumpers, switches = self.processed.build_physics_objects(self.placed_shapes, switch_callbacks)
        
        walls.insert(0, outline_wall)
        # Wire Scene nodes — stays in PinballCreate
        for flipper, shape in zip(flippers,
                                  [s for s in self.placed_shapes
                                   if s.sprite_name in self.processed.FLIPPER_SPRITES]):
            flipper.node = shape.node
            flipper.compute_anchor_point()
            
        self.ball = Ball(parent=self)
        self.ball.draw_()
        self.ball.node = SpriteNode(Texture('pzl:BallGray'),
                                    z_position=95,
                                    size=(self.ball.radius*2, self.ball.radius*2),
                                    parent=self)
        self.score = 0
        self.set_score_node()
        self.physics = Physics(self.ball, walls, flippers, bumpers, switches, self)
        
        # Hide the sidebar when playing and hide grid
        if hasattr(self, 'scroll_container'):
            self.scroll_container.hidden = True
        self.grid_box.alpha = 0
        
        try:
            self.physics.score_node = self.score_node
            self.physics.plunger_rect = self.plunger_rect
            self.play = True
            self.paused = False
            self.physics.emit_ball()
        except AttributeError as e:
            print('play mode', e)
            
    def edit_mode(self, sender):
        # Hide the sidebar when playing
        if hasattr(self, 'scroll_container'):
            self.scroll_container.hidden = False
        self.play = False
        if hasattr(self, 'score_node'):
            self.score_node.remove_from_parent()
        if hasattr(self, 'ball'):
           self.ball.node.remove_from_parent()
        self.grid_box.alpha = 0.8
         
    def recentre(self, coords):
        return coords - np.mean(coords, axis=0)
        
    def dots(self, shape,  size=10):
        # useful to visualse if coordinates are aligned with sprites
        coords = shape.coordinates.copy()
        coords = coords + shape.centroid
        for coord in coords:
            ShapeNode(path=ui.Path.oval(-size/2, -size/2, size, size),
                      position=coord, fill_color="red", parent=self)
        ShapeNode(path=ui.Path.oval(-5, -5, 10, 10),
                  position=shape.centroid, fill_color="green", parent=self)
        
        self.outline.node = SpriteNode(Texture(pil_to_ui(shape.image)),
                                       position=self.origin,
                                       parent=self)
        
        # Plunger and Grid setup remains relative to self.origin...
        self.grid_box = self.build_grid()
                                                                                                                                                                                                                                                                                                       
    def spawn_from_tray(self, sender):
        """Callback when an item in the tray is tapped."""
        
        z_order = {"flipper": 90, "sling": 50, "bumper": 30,
                   "button": 50, "switch": 50}
        template = sender.shape_template
        new_shape = template.get_copy()
        
        # Place it at the screen center for the user to then drag
        spawn_pos = self.origin
        
        sprite = SpriteNode(Texture(pil_to_ui(new_shape.image)), position=spawn_pos)
        base_name = re.split(r'[_ ]', new_shape.sprite_name)[0]
        sprite.z_position = z_order.get(base_name, 10)
        new_shape.node = sprite
        new_shape.centroid = spawn_pos
        new_shape.unique_id = str(uuid.uuid1())
        self.add_child(sprite)
        self.selected_shape = new_shape
        self.placed_shapes.append(new_shape)
        self.store(new_shape, position=spawn_pos)

    def redraw(self):
        
        # remove the sprites
        for shape in self.placed_shapes:
            shape.node.remove_from_parent()
            
        # remove the shapenodes
        for child in self.children:
            if isinstance(child, ShapeNode):
                child.remove_from_parent()
         
        # place the sprites
        for shape in self.placed_shapes:
            self.add_child(shape.node)
            
        self.grid_box = self.build_grid()
        
        # place the shapenodes
        # for shape in self.placed_shapes:
        #   self.dots(shape, 5)
                      
        self.save(None)
        
    def restore(self, sender):
        z_order = {"flipper": 90, "sling": 50, "bumper": 30,
                   "button": 50, "switch": 50, "hole": 50,
                   "red": 50}
        try:
            with open(f'{self.outline_name}.json', 'r') as f:
                self.placed_objects = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
           console.hud_alert(f'File {self.outline_name}.json not found')
           return
        self.send_message(f'Read {len(self.placed_objects)} items')
        # now decode placed objects
        # remove the existing sprites
        for placed in self.placed_shapes:
           if not placed.sprite_name.startswith('outline'):
              placed.node.remove_from_parent()
              
        self.placed_shapes = []
        
        for unique_id, object_data in self.placed_objects.items():
           # get shape from the palette which matches name
           try:
               for shape in self.shapes:
                  if shape.sprite_name == object_data['name']:
                     palette_shape = shape
                     break
               else:
                   continue
           except StopIteration:
              raise RuntimeError(f'{object_data["name"]} not found in self.shapes')
              
           try:
               shape = palette_shape.get_copy()
               if 'rotation' in object_data:
                   shape.image, shape.coordinates = shape.rotate(int(object_data['rotation']))
                   shape.set_image(shape.image)
                   
               if 'mirror' in object_data:
                   shape.image, shape.coordinates = shape.mirror(object_data['mirror'].lower())
                   shape.set_image(shape.image)
                   
               if 'scale' in object_data:
                   w, h = shape.image.size
                   scale = object_data['scale']
                   shape.image = shape.image.resize((int(scale * w), int(scale * h)))
                   shape.set_image(shape.image)
                   shape.scale_path(scale)
                   
               if 'colour' in object_data:
                   if object_data['colour'] is None:
                      lum = None
                      hue = None
                   elif object_data['colour'] == 360:
                      lum = 0.25
                      hue = object_data['colour'] % 360
                   else:
                      lum = None
                      hue = object_data['colour']
                   
                   shape.image = shape.recolor_image(target_hue=hue, target_lum=lum)
                   
               position = (object_data['position'][0] * self.size.w,
                           object_data['position'][1] * self.size.h)
               sprite = SpriteNode(Texture(pil_to_ui(shape.image)))
               
               # allow sprite types have different z order
               base_name = re.split(r'[_ ]', shape.sprite_name)[0]
               sprite.z_position = z_order.get(base_name, 10)
               
               sprite.position = position
               shape.centroid = position
               shape.unique_id = unique_id
               shape.node = sprite
               self.add_child(sprite)
               self.placed_shapes.append(shape)
           except Exception as e:
               print(f'Exception in restoring {str(e)} {unique_id} {object_data["name"]}')
        
    def save(self, sender):
        """ save basic information about objects
        id, object name, centroid, rotation, mirror, colour, scale"""
                
        with open(f'{self.outline_name}.json', 'w') as f:
            json.dump(self.placed_objects, f, indent=2)
    
    def store(self, shape, **kwargs):
        """ Update placed_objects and save """
        
        # positions are fraction of self.size
        shape_id = getattr(shape, 'unique_id', hex(id(shape)))
    
        # If the shape isn't in our tracking dict yet, initialize it
        if shape_id not in self.placed_objects:
            self.placed_objects[shape_id] = {
                'name': shape.sprite_name,
                'position': [round(shape.centroid.x / self.size.w, 3),
                             round(shape.centroid.y / self.size.h, 3)]
            }
        
        # Update only the changed metadata
        if kwargs:
            for key, value in kwargs.items():
                # Convert Point to list if position is being updated
                if key == 'position':
                    self.placed_objects[shape_id][key] = [round(value.x / self.size.w, 3),
                                                          round(value.y / self.size.h, 3)]
                else:
                    self.placed_objects[shape_id][key] = value
        self.save(None)
        
    def _snap(self, point):
        """ snap point to defined grid spacing """
        # 1. Calculate the distance from the origin
        rel_x, rel_y = point - self.origin
               
        # 2. Snap the relative distance to the grid
        snapped_rel_x = round(rel_x / self.grid_snap) * self.grid_snap
        snapped_rel_y = round(rel_y / self.grid_snap) * self.grid_snap
        
        # 3. Re-apply the fixed point offset
        return Point(snapped_rel_x, snapped_rel_y) + self.origin

    def _on_double_tap(self, touch, shape):
        """ open transform view """
        self.selected_shape = shape
        self.transform(self.selected_shape)
        self.in_double_tap = True
               
    def remove_shape(self, shape):
        """Clean helper to delete a shape from all tracking lists and the screen."""
        if shape in self.placed_shapes:
            self.placed_shapes.remove(shape)
        self.placed_objects.pop(shape.unique_id, None)
        if shape.node:
            shape.node.remove_from_parent()
        self.selected_shape = None
        self.save(None)
        
    def _get_shape_at(self, location):
        """Helper to find a placed shape at a specific point.
        to make selection better, reduce bbox towards centre"""
        for placed in self.placed_shapes:
            bbox = placed.node.bbox
            # sprite is always square
            inset = bbox.w / 3
            if not placed.sprite_name.startswith('outline') and placed.node.bbox.inset(inset, inset).contains_point(location):
                return placed
        return None

    def _draw_guide_line(self, pos, target_pos):
        """Draws a temporary crosshair or alignment line between two points
        horizontal line shows vertical alignment
        vertical line shows centre line.
        make lines relative to target"""
        # Remove previous guide if it exists
        if hasattr(self, 'active_guide') and self.active_guide:
            self.active_guide.remove_from_parent()
        if target_pos:
            # 1. Calculate the midpoint
            mid_x = (pos.x - target_pos.x) / 2
            
            path = ui.Path()
            # Draw the primary line rel to target
            path.move_to(0, 0)
            x = pos.x - target_pos.x
            y = target_pos.y - pos.y
            path.line_to(x, y)
            # Draw the vertical line from the midpoint
            path.move_to(mid_x, y)
            path.line_to(mid_x, -y)
            node = ShapeNode(path, parent=self)
            node.position = target_pos
            node.stroke_color = "green" if y == 0 else "white"
            node.anchor_point = (pos.x <= target_pos.x, pos.y >= target_pos.y)
        else:
            # Create the a cross path
            path = ui.Path()
            path.move_to(-100, 0)
            path.line_to(100, 0)
            path.move_to(0, -100)
            path.line_to(0, 100)
            node = ShapeNode(path, parent=self)
            node.position = pos
            node.anchor_point = (0.5, 0.5)
            node.stroke_color = 'white'
        node.line_width = 2
        self.active_guide = node
        self.active_guide.z_position = 100  # Ensure it's above sprites
                
    def _predict_alignment(self):
        """ decide if there is a similar item at similar level
        limit this to similar types, e.g. wall, guide, flipper etc"""
        if not self.selected_shape:
            return
    
        shape = self.selected_shape
        new_pos = shape.node.position
        base_name = re.split(r'[_ ]', shape.sprite_name)[0]
        
        # Calculate mirrored target point
        mirrored_x = self.origin.x + (self.origin.x - new_pos.x)
        mirrored_y = new_pos.y
        mirrored_target = Point(mirrored_x, mirrored_y)
        
        candidates = []
        
        for other in self.placed_shapes:
            if other == shape:
                continue
            
            # 1. Filter by base type (e.g., 'flipper', 'bumper')
            if not other.sprite_name.startswith(base_name):
                continue
                
            other_centroid = Point(*other.centroid)
            # returns euclidean distance between 2 Point objects
            dist = abs(other_centroid - mirrored_target)
            
            # 2. Check if within search radius
            if dist < 150:
                # We store: (is_exact_match, y_diff, distance, object)
                # Boolean exact match first so True (1) sorts after False (0)
                # actually, we want True first, so we use -1 or reverse
                candidates.append({
                    'exact': (other.sprite_name == shape.sprite_name),
                    'y_diff': abs(other_centroid.y - mirrored_y),
                    'dist': dist,
                    'obj': other
                })
    
        # 3. Sort logic:
        # Primary: Exact name matches first
        # Secondary: Smallest Y difference (alignment)
        # Tertiary: Overall closest distance
        candidates.sort(key=lambda x: (not x['exact'], x['y_diff'], x['dist']))
        
        # Extract just the shape objects for your sorted_shapes list
        sorted_shapes = [c['obj'] for c in candidates]
    
        # 4. Draw guide for the "Best Fit" (the first item in sorted list)
        if sorted_shapes:
            best_fit = sorted_shapes[0]
            self._draw_guide_line(new_pos, Point(*best_fit.centroid))
        else:
            self._draw_guide_line(new_pos, None)
        return sorted_shapes
        
    # --------------- Transform Panel
       
    def transform(self, shape):
        """ open transform view and initialise sliders
        This has been coded explicitly rather than pyui to permit simpler
        use of TickedSliderView class"""
        COLOUR_NAMES = [
                       "Red", "Vermilion", "Orange", "Golden Amber",
                       "Yellow", "Neon Lime", "Bright Chartreuse", "Leaf Green",
                       "Green", "Emerald", "Malachite Mint", "Aquamarine",
                       "Cyan", "Cerulean Blue", "Azure Ocean", "Sapphire",
                       "Blue", "Indigo", "Deep Violet", "Amethyst",
                       "Magenta", "Hot Pink", "Raspberry Rose", "Crimson", "Black"
                   ]
        self.colour_dict = {value: colour for colour, value in zip(COLOUR_NAMES, range(0, 375, 15))}
        
        # set transform panel manually
        self.transform_view = ui.View(frame=(5, 5, 420, 420))
        angle = TickedSliderView(min_val=0, max_val=360,
                                 num_ticks=24, major_ticks_every=3,
                                 labels=np.arange(0, 405, 45),
                                 action=self.angle_action,
                                 name='ticked_angle_slider',
                                 frame=(5, 36, 410, 77),
                                 color='red')
        self.transform_view.add_subview(angle)
        
        scale = TickedSliderView(min_val=0.5, max_val=2.0,
                                 num_ticks=15, major_ticks_every=5,
                                 labels=np.round(np.linspace(0.5, 2.0, 16), 1),
                                 name='ticked_scale_slider',
                                 action=self.scale_action,
                                 frame=(5, 210, 410, 77),
                                 color='blue')
        self.transform_view.add_subview(scale)
        
        colour = TickedSliderView(min_val=0, max_val=360,
                                  num_ticks=24, major_ticks_every=4,
                                  labels=['R', 'Y', 'G', 'Cy', 'B', 'Ma', 'BL'],
                                  action=self.colour_action,
                                  name='ticked_colour_slider',
                                  frame=(5, 310, 410, 77),
                                  color='green')
        self.transform_view.add_subview(colour)
        
        mirror = ui.SegmentedControl(name='Orientation',
                                     segments=['None', 'Vertical', 'Horizontal'],
                                     action=self.mirror_action,
                                     frame=(5, 150, 410, 40))
        self.transform_view.add_subview(mirror)
        
        self.transform_view.add_subview(ui.Button(
             name='Delete',
             title='Delete',
             action=self.delete_action,
             frame=(209, 6, 80, 32)))
                
        self.transform_view.add_subview(ui.Button(
            name='Cancel',
            title='Cancel',
            action=self.cancel_action,
            frame=(304, 6, 80, 32)))
                
        self.transform_view.add_subview(ui.Label(text='Mirror', frame=(5, 120, 150, 32)))
        
        # initialise angle, colour and scale
        shape_id = getattr(shape, 'unique_id', hex(id(shape)))
        if shape_id in self.placed_objects:
            existing_angle = self.placed_objects[shape_id].get('rotation', 0)
            angle.value = existing_angle
            angle.set_text(f'Rotation Angle CCW  {existing_angle}deg')
            
            existing_colour = self.placed_objects[shape_id].get('colour', 0)
            colour.value = existing_colour
            colour.set_text(f'Colour {self.colour_dict[existing_colour]}')
            
            existing_scale = self.placed_objects[shape_id].get('scale', 1)
            scale.value = existing_scale
            scale.set_text(f'Scale x{round(existing_scale, 1)}')
    
        self.transform_view.set_needs_display()
        self.transform_view.present("popover")
    
    def scale_action(self, sender):
        self.send_message(f'{sender.name} {sender.value}')
        shape = self.selected_shape
        if not shape:
            return
        self.in_double_tap = False
        
        scale = round(sender.value, 1)
        
        sender.set_text(f'Scale x{scale}')
        calc_scale = scale / shape.scale
        w, h = shape.image.size
        shape.image = shape.image.resize((int(calc_scale * w), int(calc_scale * h)),
                                         resample=Image.BICUBIC)
        shape.scale_path(calc_scale)
        shape.scale = scale

        self.store(shape, scale=scale)
        # Update the visual node without creating a new one
        shape.image_size = shape.image.size
        shape.node.texture = Texture(pil_to_ui(shape.image))
        
    def angle_action(self, sender):
        self.send_message(f'{sender.name} {sender.value}')
        shape = self.selected_shape
        self.in_double_tap = False
        if not shape:
            return

        angle = round(sender.value)
        sender.set_text(f'Rotation Angle CCW  {angle}deg')
        
        # gets original angle from shape
        shape.image, shape.coordinates = shape.rotate(angle)
        self.store(shape, rotation=angle)
        # Update the visual node without creating a new one
        shape.node.texture = Texture(pil_to_ui(shape.image))
                
    def colour_action(self, sender):
        shape = self.selected_shape
        self.in_double_tap = False
        if not shape:
            return
 
        colour_no = round(sender.value, 0)
        
        # change to black. 0.25 is above lum threshokd of 0.2
        target_lum = 0.25 if colour_no == 360 else 0.95
        target_hue = colour_no % 360
        sender.set_text(f'Colour {self.colour_dict[colour_no]}')
        shape.image = shape.recolor_image(target_hue, target_lum=target_lum)
        self.store(shape, colour=colour_no)
        # Update the visual node without creating a new one
        shape.node.texture = Texture(pil_to_ui(shape.image))
    
    def delete_action(self, sender):
        shape = self.selected_shape
        if not shape:
            return
        self.remove_shape(shape)
        sender.superview.close()
        
    def cancel_action(self, sender):
        sender.superview.close()
          
    def mirror_action(self, sender):
        """This function triggers whenever a user taps a tranform control or cancel
        it is used to transform a placed shape """
        
        shape = self.selected_shape
        if not shape:
            return
        self.in_double_tap = False
        
        value = sender.segments[sender.selected_index]
        if value != 'None':
            shape.image, shape.coordinates = shape.mirror(value.lower())
            self.store(shape, mirror=value.lower())
            # Update the visual node without creating a new one
            shape.image_size = shape.image.size
            shape.node.texture = Texture(pil_to_ui(shape.image))

    # -----------Touch Operation
    def _plunger_action(self, direction, y_loc=0):
        """ animate plunger compression and release """
        y_scale = self.plunger_y_scale
        scale_action = Action.scale_y_to(y_scale, 0.2)
        top_of_plunger = self.plunger_rect.height / 3 + self.plunger_rect.min_y
        
        if direction == 'compress':
            # diff from top of plunger image
            y_diff = top_of_plunger - y_loc
            ratio = 1 - 3 * y_diff / self.plunger_rect.height
            self.plunger.y_scale = abs(ratio) * y_scale
        else:
            scale_action = Action.scale_y_to(y_scale, 0.2)
            self.plunger.run_action(scale_action)
            
    def touch_began(self, touch):
        if self.play:
            self.start_touch_y = touch.location.y
            return self.physics.touch_start(touch)

        self.selected_shape = None
        self.in_double_tap = False
        current_time = time()
        
        # Only check placed shapes now, as palette is handled by UI buttons
        clicked_shape = self._get_shape_at(touch.location)
        if clicked_shape:
            if current_time - self.last_tap_time < self.double_tap_threshold:
                self._on_double_tap(touch, clicked_shape)
                self.last_tap_time = 0
            else:
                self.selected_shape = clicked_shape
                self.last_tap_time = current_time
                            
    def touch_moved(self, touch):
        if self.play:
            self.ball.pos = touch.location
            self.ball.update()
            self._plunger_action('compress', touch.location.y)
            
        elif self.selected_shape:
            new_pos = Point(*self._snap(touch.location))
            self.selected_shape.node.position = new_pos
            self._predict_alignment()
                        
    def touch_ended(self, touch):
        if self.play:
            self.physics.touch_end(touch)
            self._plunger_action('expand')
            return

        if not self.selected_shape or self.in_double_tap:
            return
        try:
            self.active_guide.remove_from_parent()
        except AttributeError:
            pass
        # Check if dropped on the Play Surface
        if touch.location.x < self.grid_box.bbox.max_x:
            snapped_pos = self._snap(touch.location)
            self.selected_shape.node.position = snapped_pos
            self.selected_shape.centroid = snapped_pos
            self.store(self.selected_shape, position=snapped_pos)
        else:
            # Dropped in dead space outside grid
            self.remove_shape(self.selected_shape)
  
    def did_change_size(self):
        
        w, h = get_screen_size()
        self.send_message(f'changing size {int(w)}. {int(h)}')
        # 1. Update the origin (anchor point for the table)
        self.origin = Point(int(w / 2.5), int(h / 2))
        
        # 2. Update the sidebar/tray position
        self.palette_x = 0.95 * w
        if hasattr(self, 'scroll_container'):
            sidebar_w = 200
            # If tray is currently open, snap it to the new right edge
            if not self.scroll_container.hidden:
                self.scroll_container.frame = (self.palette_x - sidebar_w, 0, sidebar_w, h - 20)
                self.tray_button.frame = (self.palette_x - sidebar_w - 45, 10, 40, 40)
            else:
                self.scroll_container.frame = (w, 0, sidebar_w, h - 20)
                self.tray_button.frame = (w - 45, 10, 40, 40)
    
        # 3. Refresh the board layout
        self.refresh_layout()
    
    def refresh_layout(self):
        w, h = get_screen_size()
        # Reposition the outline sprite and grid
        for object in [self.outline_path,  self.outline_node,
                       self.plunger_outline, self.plunger,
                       self.grid_box]:
            object.remove_from_parent()
        self.outline = self.processed.make_outline(self.outline_name)
        # rebuild the outline, plunger and grid
        self.place_outline(self.outline)
        # Reposition all placed objects based on their stored relative positions
        for shape in self.placed_shapes:
            shape_id = shape.unique_id
            if shape_id in self.placed_objects:
                rel_pos = self.placed_objects[shape_id]['position']
                # Re-calculate absolute position based on new screen size
                new_pos = Point(rel_pos[0] * w, rel_pos[1] * h)
                
                shape.centroid = new_pos
                shape.node.position = new_pos
            
    # ------------------------------------- Play section -------
    
    def update(self):
        if self.play:
            self.physics.update(self.dt)
           
    # ---------Switch actions    
              
    def x2(self, switch):
        self.score *= 2
        
    def x3(self, switch):
        self.score *= 3
        
    def x5(self, switch):
        self.score *= 5
        
    def hole(self, switch):
        self.score += 100
        # trap ball for 1 second
        # self.ball.vel = [0, 0]
        self.physics.ball.pos = switch.centroid
        self.ball.node.alpha = 0
        self.paused = True
        sleep(1)
        self.paused = False
        self.ball.node.alpha = 1
                        
    def red(self, switch):
        self.score += 10
        
    def vert(self, switch):
        self.score += 10
        
    def again(self, switch):
       self.physics.emit_ball()
       
    def arrow(self, switch):
      # make the arrow block if ball direction not in  arrow direction
      self.send_message('roll over arrow')
      # for arrow, left is 0 , 270 is vertical
      # need up to be 90 for vertical
      vx, vy = self.physics.ball.vel
      ball_angle = np.degrees(np.arctan2(vy, vx))
      switch_angle = (switch.angle - 180) % 360
      if abs(ball_angle - switch_angle) > 20:
          self.physics.collide_wall(switch)
                                           
                                    
# ------------------ testing functions
                                
def test_place_flippers(game):
    # move flipper left and right
    icons = list(game.palette_rects)
    l_flip = icons[1].center()
    r_flip = icons[12].center()
    round_ = icons[3].center()
    t = Touch(*l_flip, 0, 0, 0)
    game.touch_began(t)
    t1 = Touch(387.50, 161.00, *l_flip, 0)
    game.touch_ended(t1)
    sleep(0.5)
    game.touch_began(Touch(*r_flip, 0, 0, 1))
    sleep(0.5)
    game.touch_moved(Touch(*r_flip, 0, 0, 1))
    game.touch_ended(Touch(490.50, 148.50, *r_flip, 1))
    game.touch_began(Touch(*round_, 0, 0, 2))
    sleep(0.5)
    game.touch_ended(Touch(480, 300, *round_, 1))


def test_play(game):
    game.physics.touch_start(Touch(490.50, 148.50, 0, 0, 1))
    sleep(0.5)
    game.physics.update(0.02)
    sleep(0.5)
    game.physics.touch_end(Touch(490.50, 148.50, 490.50, 148.50, 1))
    game.physics.update(0.02)
    game.physics.touch_start(Touch(715, 200, 0, 0, 2))
    sleep(0.5)
    game.physics.touch_end(Touch(715, 500, 0, 0, 2))
    game.physics.update(0.02)

        
def test_rotate(game):
   # grab centre shape and rotate it
   game.touch_began(Touch(*game.origin, 0, 0, 1))
   shape = game.selected_shape
   game.transform(shape)
   # sleep(0.1)
   # game.touch_began(Touch(*game.origin, 0, 0, 1))
   shape.image, shape.coordinates = game.selected_shape.rotate(int(90))
   shape.image, shape.coordinates = game.selected_shape.rotate(int(135))
   shape.image, shape.coordinates = game.selected_shape.rotate(int(45))
   pass


def test_move(game):
   # grab centre shape and move it
   game.touch_began(Touch(675, 512, 0, 0, 1))
   sleep(0.5)
   game.touch_moved(Touch(*(game.origin+Point(230, 0)), 0, 0, 1))
   game.touch_ended(Touch(*(game.origin+Point(250, 0)), 0, 0, 1))
   pass

                
if __name__ == "__main__":
    # processed = ProcessShapes('outline3')
    game = PinballCreate()
    #
    # game.setup()
    # test_place_flippers(game)
    #
    #
    #
    # game.select(None)
    # game.restore(None)
    
    # game.colour_action(None)
    # test_rotate(game)
    # game.play_mode(None)
    # test_play(game)
    # test_move(game)
    pass
    run(game)
