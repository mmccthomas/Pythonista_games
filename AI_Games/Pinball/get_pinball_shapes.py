# read a spritesheet (irregular) and extract coordinates of each sprite
# they are ordered in y then x
# need to loose sort so that small differences in y do not affect order
# rather than calling pinball.py, i have extracted the ball physics from that module
# for save and load
# extract important details of placed objects
# id, object name, placed centroid, rotation, mirror
# id is simply used to ensure objects are unique

# affects triangle etc
# adjust SpriteNode anchor point

# TODO list
# modify ball emit to use touch pojnt on ball to get strength

from PIL import Image
import numpy as np
from scene import Rect, Texture, SpriteNode, ShapeNode, Scene, run, LabelNode, Vector2, Touch, Point
import matplotlib.pyplot as plt
import io
import ui
import re
import uuid
import json
import console
from time import time, sleep
import base_path
base_path.add_paths(__file__)
from Utilities.scanning.feature_detection import FeatureExtract, FastContourDetector, Shape
from ball_physics import Physics, Wall, Flipper, Ball, Bumper, Switch

# take a spritesheet and decode the sprites
selected_outline = 'outline1'
mirror_lr = '\u21c4'
mirror_up = '\u2144'


def pil_to_ui(img):
    with io.BytesIO() as bIO:
        img.save(bIO, "png")
        return ui.Image.from_data(bIO.getvalue())


def plot_outline(coordinates, invert=True):
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


def rotate_flipper(detector, image_process, shape):
    """ Process the flipper image. rotate it to lie on x axis
        extract pivot offset from centre of image """
    image = image_process.crop_image(shape.coordinates)
    # deal with flipper make it horizontal
    shape.coordinates, _, eigenvectors, shape.centroid = detector.pca(shape.coordinates)
    angle = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])
    shape.image = image.rotate(np.degrees(angle), expand=True)
    
    features = detector.calculate_shape_features(shape.coordinates)
    # compute pivot from radius of thicker end
    max_width = max(features['left_end_height'], features['right_end_height'])
    x1 = features['width'] / 2 - max_width / 2
    if features['left_end_height'] > features['right_end_height']:
        x1 = -x1
    shape.pivot = Point(x1, 0)  # rel to centre
    # length from pivot to thinner end
    shape.length = int(features['width'] - np.abs(x1))

                        
def extract_shapes(image_path, canny_low, canny_high, edge_tries, size_reduction):
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
           rotate_flipper(detector, image_process, shape)
        else:
            image = image_process.crop_image(shape.coordinates)
            shape.image = image
        shape.image_size = image.size
        shape.color_names = image_process.closest_colors(image)
        shape.quadrant = "_".join(image_process.quadrant(shape.centroid))
        shape.description = f"{shape.quadrant} {shape.color_names} {shape.shape}"
        # recentre to centre of shape and invert y since Scene uses 0,0 as bottom left
        # whereas shapes are referenced to top left
        shape.coordinates = shape.recentre().astype(int) * [1, -1]
        shape.coordinates = shape.coordinates[::10]
    return shapes


def transparent_rect(shape):
    """take a shape, paste its irregular image into rectangular image on transparent background"""
    combined_img = Image.new("RGBA", shape.image.size, (0, 0, 0, 0))
    # Paste the irregular image onto the background
    # x, y = int(shape.image_size[0] / 2), int(shape.image_size[1] / 2)
    combined_img.paste(shape.image, (0, 0), shape.image)
    return combined_img


def get_shapes():
    NAME = "pinball-elements.png"
    NAME = "isolated-pinball-elements.png"

    sprite_names = {
        "guide_r": 2, "guide_l": 3, "wall_1": 4, "sling_r": 5,
        "bumper x30": 6, "bumper x20": 7,  "bumper x10": 8,
        "flipper_l": 9, "short_wall_h": 10,
        "bumper star": 11,  "flipper_r": 12, "half round": 13,
        "red_button": 17, "grey wall vert": 18,  "button 2x": 19,
        "button 3x": 21, "button 5x": 22, "switch vert": 24,
        "hole black": 27,
    }

    shapes = extract_shapes(NAME, 0.1, 0.2, 2000, 4)
    filtered_shapes = []
    for i, shape in enumerate(shapes):
        if i in sprite_names.values():
            filtered_shapes.append(shape)
            shape.sprite_name = {v: k for k, v in sprite_names.items()}[i]
            # make all coordinates relative to (0,0) centre of bounding box
            # shape.coordinates = shape.recentre()
            # shape.image.show()
            # When creating the shape
            shape.original_image = shape.image.copy()
            shape.original_coords = shape.coordinates.copy()
    shape = next(shape for shape in filtered_shapes if shape.sprite_name == "sling_r")
    shape.triangle_vertices = find_triangle_vertices_batched(shape.coordinates)

    # replicate right slingshot
    new_shape = shape.get_copy()
    new_shape.sprite_name = "sling_l"
    new_shape.image, new_shape.coordinates = new_shape.mirror("vertical")
    new_shape.triangle_vertices = find_triangle_vertices_batched(new_shape.coordinates)
    # new_shape.image.show()
    filtered_shapes.append(new_shape)
    return filtered_shapes


# dictionary to hold outline coordinates, background image and scale
outlines = {'outline1': {'coords': np.array(
                                   [[269, 18], [301, 19], [333, 24], [365, 34],
                                    [389, 45], [410, 56], [428, 70], [445, 85],
                                    [461, 101], [475, 119], [487, 139], [498, 160],
                                    [508, 190], [515, 222], [517, 254], [517, 286],
                                    [518, 318], [530, 338], [541, 359], [553, 379],
                                    [565, 400], [565, 784], [542, 784],
                                    [534, 784], [534, 416], [529, 412], [521, 412],
                                    [518, 416], [517, 441], [514, 631], [498, 647],
                                    [354, 795], [203, 795], [59, 644],
                                    [44, 626], [44, 242],
                                    [48, 210], [56, 178], [67, 151], [79, 131],
                                    [92, 112], [106, 94], [122, 78], [140, 64],
                                    [159, 51], [180, 40], [209, 29], [241, 21]]),
                         'image': 'Desert.png',
                         'scale': 1.1},
            'outline2': {'coords': np.array(
                                [[56, 34], [407, 34], [428, 43], [436, 64],
                                 [436, 442], [434, 469], [428, 481], [407, 481],
                                 [400, 471], [401, 444], [401, 309], [402, 282],
                                 [402, 66], [397, 66], [397, 165], [396, 408],
                                 [395, 489], [394, 516], [391, 543], [379, 558],
                                 [359, 568], [332, 573], [305, 579], [278, 585],
                                 [251, 591], [224, 593], [197, 593], [170, 590],
                                 [143, 584], [116, 578], [89, 572], [62, 567],
                                 [44, 556], [33, 538], [32, 511], [31, 484],
                                 [31, 403], [30, 376], [30, 160], [29, 133],
                                 [29, 79], [32, 52], [45, 38]]),
                         'image': 'Space.png',
                         'scale': 1.5},
            'outline3': {'coords': np.array(
                                [[238, 28], [253, 29], [268, 30], [283, 33],
                                 [298, 38], [313, 43], [323, 48], [332, 54],
                                 [341, 60], [350, 66], [358, 73], [365, 81],
                                 [372, 89], [379, 97], [385, 106], [391, 115],
                                 [396, 125], [401, 138], [406, 153], [409, 168],
                                 [411, 183], [412, 198], [412, 529], [376, 529],
                                 [376, 518], [376, 488], [376, 169], [364, 169],
                                 [364, 488], [362, 488], [261, 552], [249, 557],
                                 [234, 557], [219, 557], [204, 557], [99, 495],
                                 [90, 489], [81, 483], [74, 475], [70, 461],
                                 [70, 446], [70, 431], [70, 416], [74, 402],
                                 [81, 394], [88, 386], [96, 379], [103, 371],
                                 [111, 364], [118, 356], [122, 344], [123, 329],
                                 [119, 315], [113, 306], [106, 298], [98, 291],
                                 [91, 283], [83, 276], [77, 267], [74, 252],
                                 [74, 237], [74, 222], [74, 207], [74, 192],
                                 [75, 177], [78, 162], [81, 147], [87, 132],
                                 [92, 121], [97, 111], [103, 102], [110, 94],
                                 [116, 85], [124, 78], [131, 70], [140, 64],
                                 [148, 57], [158, 52], [167, 46], [179, 41],
                                 [194, 36], [209, 32], [224, 29]]),
                         'image': 'Undersea.PNG',
                         'scale': 1.5},
            'outline4': {'coords': np.array(
                               [[308, 25], [360, 25], [412, 25], [464, 27],
                                [516, 38], [562, 56], [596, 74], [625, 97],
                                [652, 122], [676, 150], [696, 182], [714, 219],
                                [729, 271], [735, 323], [735, 1035], [673, 1035],
                                [673, 311], [662, 259], [644, 216], [624, 184],
                                [599, 157], [573, 171], [593, 204], [614, 235],
                                [631, 279], [637, 331], [637, 747], [616, 778],
                                [356, 1040], [308, 1040],
                                [178, 910], [15, 708],
                                [15, 344], [18, 292], [29, 240], [47, 195],
                                [66, 162], [88, 132], [114, 106], [143, 83],
                                [174, 62], [214, 44], [265, 30]]),
                         'image': 'Fairground.png',
                         'scale': 0.9}
            }

               
def get_centre_line(coords, top=True):
    if top:
        y = np.max(coords[:, 1])
    else:
        y = np.min(coords[:, 1])
    
    top_points = coords[np.abs(coords[:, 1] - y) <= 2]
    # 3. Calculate the center (mean of x, keep max_y)
    center_x = np.mean(top_points[:, 0])
    return center_x
     
               
def make_outline(points, name, image_name, scale):
    # make a dummy shape
    shape = Shape(centroid=(0, 0), circularity=0, coordinates=points, perimeter=1)
    shape.sprite_name = name
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
    shape.image = f.crop_image(shifted_coords)
    # need to move coordinates to centre of image
    shape.recentre()
    # invert y since PIL coordinates are. from topleft, whereas scen is bottomleft
    shape.coordinates = shape.coordinates * [1, -1]
    return shape

  
def find_triangle_vertices_batched(coords):
    """Find the 3 dominant vertices from a rounded triangle's coordinates."""

    coords = np.asarray(coords)
    n = len(coords)
    best_area = 0
    best_trio = None

    for i in range(n):
        p1 = coords[i]
        # Remaining points to avoid redundant calculations
        others = coords[i + 1:]
        if len(others) < 2:
            continue

        # Vectors from p1 to all other points
        # Shape: (m, 2) where m = n-(i+1)
        diffs = others - p1

        # Outer product to get all pairs of cross products
        # cross = x1*y2 - y1*x2
        x = diffs[:, 0]
        y = diffs[:, 1]

        # Vectorized 2D cross product for all pairs (j, k)
        # Using broadcasting: (m, 1) and (1, m)
        areas = np.abs(np.outer(x, y) - np.outer(y, x)) / 2

        max_idx = np.argmax(areas)
        current_max = areas.flat[max_idx]

        if current_max > best_area:
            best_area = current_max
            # map flat index back to the 'others' array
            j_rel, k_rel = np.unravel_index(max_idx, areas.shape)
            best_trio = (p1, others[j_rel], others[k_rel])

    return best_trio


def segment_length(p1, p2):
    return np.linalg.norm(np.array(p2) - np.array(p1))


def point_to_segment_distance(point, p1, p2):
    """Shortest distance from a point to a line segment."""
    point, p1, p2 = map(np.array, [point, p1, p2])
    seg = p2 - p1
    t = np.clip(np.dot(point - p1, seg) / np.dot(seg, seg), 0, 1)
    closest = p1 + t * seg
    return np.linalg.norm(point - closest)


def touched_longest_side(coords, touch_point, tolerance=10.0):
    """
    Returns True if touch_point is on the longest side of the triangle.

    coords      - list of (x, y) tuples forming the rounded triangle
    touch_point - (x, y) where the object made contact
    tolerance   - max distance to consider "touching" a side
    """
    v1, v2, v3 = find_triangle_vertices_batched(coords)

    sides = [(v1, v2), (v2, v3), (v1, v3)]
    lengths = [segment_length(*s) for s in sides]
    longest_side = sides[np.argmax(lengths)]

    distances = [point_to_segment_distance(touch_point, *s) for s in sides]
    closest_side_idx = np.argmin(distances)

    is_longest = np.array_equal(
        sides[closest_side_idx][0], longest_side[0]
    ) and np.array_equal(sides[closest_side_idx][1], longest_side[1])
    is_touching = distances[closest_side_idx] <= tolerance

    return is_longest and is_touching


def draw_(coords):
    # Draw coords
    path = ui.Path()
    path.line_width = 3
    path.move_to(*coords[0])
    [path.line_to(*p) for p in coords[1:]]
    path.close()
    return path
    
    
class PinballCreate(Scene):
 
    def setup(self):
        self.placed_shapes = []
        self.placed_objects = {}
        
        self.shapes = get_shapes()
        
        w, h = self.size
        self.origin = Point(int(w / 3), int(h / 2))
        self.palette_x = 0.95 * w
        self.grid = 50
        self.grid_snap = 5
        self.last_tap_time = 0
        self.double_tap_threshold = 0.3  # Seconds
        self.in_double_tap = False
        self.place_outline()
        self.create_scroll_palette()
        self.place_buttons()
        self.play = False
        self.edit = True
                
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
        add_button(' Save', 100, 'iow:ios7_upload_outline_256', self.save)
        add_button(' Load', 150, 'iow:ios7_download_outline_256', self.restore)
        add_button(' Play', 200, None, self.play_mode)
        add_button(' Edit', 250, None, self.edit_mode)
        
    def play_mode(self, sender):
        # Hide the sidebar when playing
        if hasattr(self, 'scroll_container'):
            self.scroll_container.hidden = True
        
        self.grid_box.alpha = 0
        self.set_objects()
        self.score = 0
        self.set_score_node()
        self.physics = Physics(self.ball, self.walls, self.flippers, self.bumpers, self.switches, self)
        try:
            self.physics.score_node = self.score_node
            self.physics.plunger_rect = self.plunger_rect
            self.play = True
            self.physics.emit_ball()
        except AttributeError as e:
            print('play mode', e)
            
    def edit_mode(self, sender):
        # Hide the sidebar when playing
        if hasattr(self, 'scroll_container'):
            self.scroll_container.hidden = False
        self.play = False
        self.score_node.remove_from_parent()
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
    
        combined_img = transparent_rect(shape)
        self.outline.centroid = self.origin
        self.outline.node = SpriteNode(Texture(pil_to_ui(combined_img)),
                                       position=self.origin,
                                       parent=self)
        
        # Plunger and Grid setup remains relative to self.origin...
        self.grid_box = self.build_grid()
                                                                                                                                                
    def place_outline(self):
        # select and place outline
        w, h = self.size
        outline_coords = outlines[selected_outline]['coords']
        image_file = outlines[selected_outline]['image']
        scale = outlines[selected_outline]['scale']
        
        self.outline = make_outline(outline_coords, selected_outline, image_file, scale)
        combined_img = transparent_rect(self.outline)
                        
        self.outline.centroid = self.origin
        
        ShapeNode(path=draw_(self.outline.coordinates*[1, -1]),
                  position=self.outline.centroid,
                  z_position=10,
                  fill_color="clear",
                  stroke_color="green",
                  parent=self)
        self.outline.node = SpriteNode(Texture(pil_to_ui(combined_img)),
                                       position=self.origin,
                                       parent=self)
        # place the plunger image
        b = Ball()
        plunger = b.get_plunger_channel(self.outline.coordinates)
        plunger_image = ui.Image.named('Plunger.jpeg')
        w, h = plunger_image.size
        
        xy = Point(int(plunger.x_min), int(plunger.y_min))
        x_scale = plunger.width / w
        # make plunger occupy 1/3 of channel
        y_scale = plunger.height / (3 * h)
        self.plunger_texture = Texture(plunger_image)
        position = self.origin + xy
        self.plunger_rect = plunger.rect.translate(*self.origin)
        
        self.plunger = SpriteNode(self.plunger_texture,
                                  x_scale=x_scale, y_scale=y_scale,
                                  anchor_point=(0, 0),
                                  z_position=100,
                                  position=position,
                                  parent=self)
        ShapeNode(ui.Path.rect(*self.plunger_rect),
                  stroke_color='white',
                  fill_color='clear',
                  z_position=100,
                  position=self.plunger_rect.center(),
                  parent=self)
        self.grid_box = self.build_grid()
        self.placed_shapes.append(self.outline)
        
    def spawn_from_tray(self, sender):
        """Callback when an item in the tray is tapped."""
        template = sender.shape_template
        new_shape = template.get_copy()
        
        # Place it at the screen center for the user to then drag
        spawn_pos = self.origin
        
        combined_img = transparent_rect(new_shape)
        sprite = SpriteNode(Texture(pil_to_ui(combined_img)), position=spawn_pos)
        new_shape.node = sprite
        new_shape.centroid = spawn_pos
        new_shape.unique_id = str(uuid.uuid1())
        self.add_child(sprite)
        self.selected_shape = new_shape
        self.placed_shapes.append(new_shape)
        self.store(new_shape)

    def create_scroll_palette(self):
        sidebar_w = 240
        screen_w, screen_h = self.size
        
        self.scroll_container = ui.ScrollView()
        self.scroll_container.frame = (self.palette_x - sidebar_w, 0, sidebar_w, screen_h - 100)
        self.scroll_container.background_color = (0.4, 0.4, 0.4, 0.7)
        
        y_offset = 10
        item_h = 100  # Increased height to fit text
        
        sprite_order = ["flipper_l", "flipper_r", "guide_l", "guide_r",
                        "sling_l", "sling_r", "bumper x30", "bumper x20",
                        "bumper x10", "button 5x", "button 3x", "button 2x",
                        "bumper star", "short_wall_h", "wall_1",
                        "grey wall vert", "half round", "switch vert",
                        "red_button", "hole black"]

        sorted_shapes = (shape for order in sprite_order
                         for shape in self.shapes
                         if shape.sprite_name == order)
        
        for shape in sorted_shapes:
            # 1. Create a container for this specific item
            container = ui.View(frame=(0, y_offset, sidebar_w, item_h))
            
            # 2. Setup the Sprite Image (Original Colors)
            ui_img = pil_to_ui(transparent_rect(shape)).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
            
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
        sidebar_w = 120
        screen_w = self.size.w
        
        # Check current state
        is_hidden = self.scroll_container.frame.x >= screen_w
        
        def animations():
            if is_hidden:
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
        try:
            with open(f'{selected_outline}.json', 'r') as f:
                self.placed_objects = json.load(f)
        except FileNotFoundError:
           console.hud_alert(f'File {selected_outline}.json not found')
           return
        # now decode placed objects
        # remove the sprites
        for placed in self.placed_shapes:
           if not placed.sprite_name.startswith('outline'):
              placed.node.remove_from_parent()
              
        self.placed_shapes = []
        
        for unique_id, object_data in self.placed_objects.items():
           # get shape from the palette which matches name
           palette_shape = next(shape
                                for shape in self.shapes
                                if shape.sprite_name == object_data['name'])
           try:
               shape = palette_shape.get_copy()
               if 'rotation' in object_data:
                   shape.image, shape.coordinates = shape.rotate(int(object_data['rotation']))
               if 'mirror' in object_data:
                   shape.image, shape.coordinates = shape.mirror(object_data['mirror'].lower())
               if 'colour' in object_data:
                   shape.image = shape.change_dominant_color(object_data['colour'])
               if 'scale' in object_data:
                   w, h = shape.image.size
                   scale = object_data['scale']
                   shape.image = shape.image.resize((int(scale * w), int(scale * h)))
                   shape.scale_path(scale)
               
               combined_img = transparent_rect(shape)
               sprite = SpriteNode(Texture(pil_to_ui(combined_img)))
               sprite.position = object_data['position']
               shape.centroid = object_data['position']
               shape.unique_id = unique_id
               shape.node = sprite
               self.add_child(sprite)
               self.placed_shapes.append(shape)
           except Exception as e:
               print(f'Exception {e} from reading json')
               
        # self.redraw()
        
    def save(self, sender):
        """ save basic information about objects
        id, object name, centroid, rotation, mirror, colour, scale"""
                
        with open(f'{selected_outline}.json', 'w') as f:
            json.dump(self.placed_objects, f, indent=2)
    
    def store(self, shape, **kwargs):
        # Use the hex address as the unique key
        shape_id = getattr(shape, 'unique_id', hex(id(shape)))
    
        # If the shape isn't in our tracking dict yet, initialize it
        if shape_id not in self.placed_objects:
            self.placed_objects[shape_id] = {
                'name': shape.sprite_name,
                'position': list(shape.centroid)
            }
        
        # Update only the changed metadata
        if kwargs:
            for key, value in kwargs.items():
                # Convert Point to list if position is being updated
                if key == 'position':
                    self.placed_objects[shape_id][key] = [float(value.x), float(value.y)]
                else:
                    self.placed_objects[shape_id][key] = value
        self.save(None)
        
    def snap(self, point):
        # 1. Calculate the distance from the origin
        rel_x, rel_y = point - self.origin
               
        # 2. Snap the relative distance to the grid
        snapped_rel_x = round(rel_x / self.grid_snap) * self.grid_snap
        snapped_rel_y = round(rel_y / self.grid_snap) * self.grid_snap
        
        # 3. Re-apply the fixed point offset
        return Point(snapped_rel_x, snapped_rel_y) + self.origin

    def on_double_tap_(self, touch):
        placed = self.get_shape_at(touch.location)
        self.transform(placed)
                
    def remove_shape(self, shape):
        """Clean helper to delete a shape from all tracking lists and the screen."""
        if shape in self.placed_shapes:
            self.placed_shapes.remove(shape)
        self.placed_objects.pop(hex(id(self.selected_shape)), None)
        if shape.node:
            shape.node.remove_from_parent()
        self.selected_shape = None
        self.save(None)
        
    def _get_shape_at(self, location):
        """Helper to find a placed shape at a specific point."""
        for placed in self.placed_shapes:
            if not placed.sprite_name.startswith('outline') and placed.node.bbox.contains_point(location):
                return placed
        return None

    def draw_guide_line(self, pos, target_pos):
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
        
    def on_double_tap(self, touch, shape):
        self.selected_shape = shape
        self.selected_shape.node.position = touch.location
        self.transform(self.selected_shape)
        self.in_double_tap = True

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
                self.on_double_tap(touch, clicked_shape)
                self.last_tap_time = 0
            else:
                self.selected_shape = clicked_shape
                self.last_tap_time = current_time
            
    def touch_moved(self, touch):
        if self.play:
            y_diff = self.start_touch_y - touch.location.y
            self.plunger.y_scale = y_diff / self.plunger_rect.height
            self.plunger.texture = self.plunger_texture
        elif self.selected_shape:
            new_pos = Point(*self.snap(touch.location))
            self.selected_shape.node.position = new_pos
            self.predict_alignment()
                        
    def touch_ended(self, touch):
        if self.play:
            self.physics.touch_end(touch)
            self.plunger.y_scale = 1/3
            return

        if not self.selected_shape or self.in_double_tap:
            return
        try:
            self.active_guide.remove_from_parent()
        except AttributeError:
            pass
        # Check if dropped on the Play Surface
        if touch.location.x < self.grid_box.bbox.max_x:
            snapped_pos = self.snap(touch.location)
            self.selected_shape.node.position = snapped_pos
            self.selected_shape.centroid = snapped_pos
            self.store(self.selected_shape, position=snapped_pos)
        else:
            # Dropped in dead space outside grid
            self.remove_shape(self.selected_shape)
                
    def predict_alignment(self):
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
            self.draw_guide_line(new_pos, Point(*best_fit.centroid))
        else:
            self.draw_guide_line(new_pos, None)   
        return sorted_shapes
                   
    def transform(self, shape):
        ui.load_view("transform_item.pyui").present("sheet")
    
    def segment_changed(self, sender):
        # This function triggers whenever a user taps a segment or cancel
        # it is used to transform a placed shape
        shape = self.selected_shape
        if not shape:
            return
        self.in_double_tap = False
        if sender.name == "Cancel":
            sender.superview.close()
            return
            
        if sender.name == "Delete":
            self.remove_shape(shape)
            sender.superview.close()
            return
            
        value = sender.segments[sender.selected_index]
        shape.sprite_name = f"{shape.sprite_name}"
        match sender.name:
            case "Angle":
                angle = int(value)
                shape_id = getattr(shape, 'unique_id', hex(id(shape)))
                
                # If the shape is in our tracking dict, get existing angle
                if shape_id in self.placed_objects:
                    existing_angle = self.placed_objects[shape_id].get('rotation', 0)
                    angle -= existing_angle
                    
                shape.image, shape.coordinates = shape.rotate(angle)
                self.store(shape, rotation=angle)

            case "Orientation":
                shape.image, shape.coordinates = shape.mirror(value.lower())
                self.store(shape, mirror=value.lower())
            case "Colour":
                colours = {
                    "Red": 0, "Green": 120, "Blue": 240,
                    "Purple": 300, "Cyan": 180, "Yellow": 60,
                    "Orange": 30, "Chartreuse Green": 90,
                    "Spring Green": 150, "Azure": 210, "Rose": 330,
                }
                shape.image = shape.change_dominant_color(colours[value])
                self.store(shape, colour=colours[value])

            case "Scale":
                scale = float(value.removeprefix("x"))
                w, h = shape.image.size
                shape.image = shape.image.resize((int(scale * w), int(scale * h)))
                shape.scale_path(scale)
                self.store(shape, scale=scale)
        # Update the visual node without creating a new one
        shape.image_size = shape.image.size
        combined_img = transparent_rect(shape)
        shape.node.texture = Texture(pil_to_ui(combined_img))
        # just save the state
        self.save(None)
        
    def build_grid(self):
        """ define a grid to overlay on top of everything else
        allow offset to place grid at centre of square (e.g. go game)"""
        bbox = self.outline.bbox
                               
        grids_x = round(bbox.width / self.grid)
        grids_y = round(bbox.height / self.grid)

        with ui.ImageContext(grids_x * self.grid, grids_y * self.grid) as ctx:
            ui.set_color('lightgrey')
            for i in range(grids_y):
               # horizontal rectangle
               ui.Path.rect(0, i * self.grid, grids_x * self.grid, self.grid).stroke()
            for i in range(grids_x):
               # Vertical rectangle
               ui.Path.rect(i * self.grid, 0, self.grid, grids_y * self.grid).stroke()
                        
            img = ctx.get_image()
            
        return SpriteNode(Texture(img),
                          position=self.origin,
                          alpha=0.8,
                          parent=self)
    
    # ------------------------------------- Play section
    
    def update(self):
        if self.play:
           self.physics.update(self.dt)
                                 
    def set_objects(self):
        # Process placed shapes
        # --------------- Define shape properties
        shapes = self.placed_shapes
        # list of shapes decoded as wall and its bounce value
        # for switches, define actions
        wall_list = {'guide_l': 1, 'guide_r': 1, 'sling_l': 1.1, 'sling_r': 1.1, 'short_wall_h': 1,
                     'wall_1': 1, 'grey wall vert': 1, 'half round': 1.2}
        switch_list = {'button 5x': 'x5', 'button 3x': 'x3', 'button 2x': 'x2',
                       'switch vert': None, 'red_button': None, 'hole black': None}
        bumper_list = {'bumper x30': (1.2, 30), 'bumper x10': (1.2, 10), 'bumper x20': (1.2, 20), 'bumper star': (1.3, 50)}
        flipper_list = {'flipper_l': 1, 'flipper_r': 1}
           
        self.walls = [Wall('outline', self.outline.centroid, self.outline.coordinates, inside_wall=False)]
        self.switches = []
        self.bumpers = []
        self.flippers = []
        
        for shape in shapes:
            # keep coordinates relative to centroid       
            if shape.sprite_name in wall_list:
                           
                wall = Wall(f'{shape.description}', shape.centroid, shape.coordinates)
                wall.bounce = wall_list[shape.sprite_name]
                self.walls.append(wall)
            elif shape.sprite_name in switch_list:
                
                switch = Switch(f'{shape.description}', shape.centroid, shape.coordinates,
                                switch_list[shape.sprite_name], score=0)
                self.switches.append(switch)
            elif shape.sprite_name in bumper_list:
                bounce, score = bumper_list[shape.sprite_name]
                bumper = Bumper(f'{shape.description}', shape.centroid, shape.radius,
                                score, bounce)
                self.bumpers.append(bumper)
            elif shape.sprite_name in flipper_list:
                flipper = Flipper(f'{shape.description}', shape.centroid, shape.pivot,
                                  shape.length, shape.coordinates,
                                  min_angle=-25)
                flipper.node = shape.node
                flipper.compute_anchor_point()
                self.flippers.append(flipper)
        
        self.ball = Ball(parent=self)
        self.ball.draw_()
        self.ball.node = SpriteNode(Texture('pzl:BallGray'),
                                    z_position=10,
                                    size=(self.ball.radius*2, self.ball.radius*2),
                                    parent=self)
                                    
    def set_score_node(self):
        # Draw Score
        self.score_node = LabelNode(text=f'SCORE: {self.score}',
                                    font=('Helvetica', 30),
                                    color='white',
                                    position=(100, self.size.height-100),
                                    z_position=10,
                                    parent=self)

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
   # sleep(0.1)
   # game.touch_began(Touch(*game.origin, 0, 0, 1))
   image, coordinates = game.selected_shape.rotate(int(90))
   pass


def test_move(game):
   # grab centre shape and move it
   game.touch_began(Touch(675, 512, 0, 0, 1))
   sleep(0.5)
   game.touch_moved(Touch(*(game.origin+Point(230, 0)), 0, 0, 1))
   game.touch_ended(Touch(*(game.origin+Point(250, 0)), 0, 0, 1))
   pass

                
if __name__ == "__main__":
    
    game = PinballCreate()
    #
    # game.setup()
    # test_place_flippers(game)
    #
    # 
    #,game.restore(None)
    # test_rotate(game)
    # game.play_mode(None)
    # test_play(game)
    # test_move(game)
    pass
    run(game)
    
