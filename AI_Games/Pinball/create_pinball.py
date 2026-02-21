
# extract pinball image using utils/scanning/feature_detection
# this gives a series of shape objects
# with position, colour and shape names
# this program must produce a json file
# this program should  process each shape to produce file
# it should allow skipping shapes and classifying as one of the below
# this should be a gui
# TODO provide means to check what is committed
# modified to add tabbed view to be able to adjust edge view
# much improved speed by reducing image size
""" "image": {"name": {"reduction", "image_size"},
    "outline": {"name": {"centroid", coordinates"}...,
    "bumper": {"name": {"centroid","radius","score", "bounce"}...,
    "switch": {"name": {"centroid","coordinates","action", "score"}...,
    "flipper": {"name": {"centroid","coordinates", "pivot","length"}...,
     "wall" : {"name": {"centroid", "coordinates"}...}
     
An outline contains ball within its borders
A bumper bounces the ball with a force given by bounce, and score given by score
A switch does not stop the ball, but performs action and score
A flipper is controlled to flip the ball
A wall reflects the ball

centroid is added to all objects to allow between similarly named objects
"""
        
import numpy as np
from PIL import Image
import json
import ui
import os
import io
import console
import dialogs
import logging
from time import sleep
from pathlib import Path
import base_path
base_path.add_paths(__file__)
from Utilities.scanning.feature_detection import FeatureExtract, FastContourDetector


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s %(message)s',
    datefmt='%H:%M:%S'  # This removes the year, month, and day
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set root logger level to DEBUG


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

                
class Pinball():
    def __init__(self):
       self.select_file(None)
       self.max_points = 100
       #self.image_name = image
       self.size_reduction = 1
       self.output = {"image": {},
                      "outline": {}, "bumper": {},
                      "switch": {}, "flipper": {},
                      "wall": {}}
       self.json_file = self.pinball_image.with_suffix('.json')
       self.read_json()
       
       self.setup_gui()
       #self.fetch_shapes(None)
       self.main.present('sheet')
       
    def show_status(self):
       CR = '\n'
       display = f'Image has {len(self.shapes)}objects{CR} JSON File has {CR}'
       sections = {section: len(elements) for section, elements in self.output.items()}
       display += '\n'.join([f'{k}, length {v}' for k, v in sections.items()])
       display += f'{CR}total {sum([v for v in sections.values()])}'
        
       console.alert(display, button1='OK', hide_cancel_button=True)
                      
    def pil_to_ui(self, img):
        with io.BytesIO() as bIO:
          img.save(bIO, 'png')
          return ui.Image.from_data(bIO.getvalue())

    def create_tabview(self):
        # 1. Main Container
        main_view = ui.load_view('create_pinball_main.pyui')
        main_view.background_color = 'white'
        
        # 2. Content Area (where different "pages" appear)
        self.content_area = main_view['content_area']
        self.content_area.flex = 'WH'  # Auto-resize
   
        self.gui = ui.load_view('create_pinball.pyui')
        self.parameters = ui.load_view('create_pinball2.pyui')
        
        # Initialize first tab
        self.tab_changed(main_view['content_type'])
        return main_view
        
    def open_image(self):
        pil_image = Image.open(self.pinball_image)
        pil_image = pil_image.reduce(self.size_reduction)
        return pil_image
        
    def setup_gui(self):
        self.main = self.create_tabview()
        self.main.name = self.pinball_image.name                                
        self.parameters['image'].image = self.pil_to_ui(self.open_image())
        self.parameters['processed'].background_color = 'red'
        # allow gui objects to be accessed with dot notation
        self.widgets = dotdict({subview.name: subview for subview in self.gui.subviews})
    
    # --------------- Button actions ------------   
    
    def select_file(self, sender):
        
        # Define your directory and patterns
        path = Path('.')
        patterns = ['*.jpg', '*.png', '*.PNG', '*.JPEG']
        # Flatten the results into a single list
        files = [f for p in patterns for f in path.glob(p)]
        filename =  dialogs.list_dialog(title='', items=files, multiple=False)
        self.pinball_image = filename

        
    def set_canny(self, sender):
        canny = sender.value  * 0.32 + 0.01
        self.parameters['canny_low'].text = f'{canny:.2f}'
        self.parameters['canny_high'].text = f'{(canny*2):.2f}'
        self.parameters['canny_val'].text = f'Canny: {canny:.2f}'
        
        
    def next_shape(self, sender):
        self.index = (self.index + 1) % len(self.shapes)
        self.decimate = 1
        self.shape = self.shapes[self.index]
        self.process_shape(self.shape)
        
    def previous_shape(self, sender):
        self.index = (self.index - 1) % len(self.shapes)
        self.decimate = 1
        self.shape = self.shapes[self.index]
        self.process_shape(self.shape)
        
    def undo(self, sender):
       pass         

    def decimate_coordinates(self, sender):
        self.decimate = int(sender.value * 99) + 1
        self.widgets.decimate_indicator.text = f'{self.decimate}'
        decimated = self.shape.coordinates[::self.decimate, :]
        self.widgets.no_coords.text = f'{len(decimated)}'
        self.plot_coords(decimated, centroid=self.shape.centroid)
                
    def fetch_shapes(self, sender):
        try:
            edges = None
            self.shapes = None
            self.parameters['processed'].background_color = 'red'
            self.parameters['shapes'].background_color = 'red'
            canny_low = float(self.parameters['canny_low'].text)  # Lower = more edges (more noise)
            canny_high = float(self.parameters['canny_high'].text)  # Lower = more edges (more noise)
            edge_tries = int(self.parameters['edge_tries'].text)
            segs = self.parameters['size_reduction'].segments 
            self.size_reduction = int(segs[self.parameters['size_reduction'].selected_index])
            
            self.min_contour_length = int(self.parameters['min_contour_length'].text)
            if self.parameters['max_contour_length'].text == 'None':
               self.max_contour_length = None
            else:
                self.max_contour_length = int(self.parameters['max_contour_length'].text)
            self.min_spacing = int(self.parameters['min_spacing'].text)
            image_path = self.pinball_image
            output_dir = None
            #sleep(0.1)
            self.image_process = FeatureExtract(image_path, output_dir,
                                                canny_low, canny_high, edge_tries, self.size_reduction)
            edges = self.image_process.edges
            pil_image = Image.fromarray(edges.astype(np.uint8))
            pil_image = pil_image.reduce(self.size_reduction)
            self.parameters['image'].image = self.pil_to_ui(pil_image)
            self.parameters['processed'].background_color = 'green'
            if sender:
                self.shapes = self.get_shapes()
                while not self.shapes:
                    self.parameters['shapes'].background_color = 'red'
                    sleep(1)
                self.parameters['shapes'].background_color = 'green'
                self.parameters['no_shapes'].text = f'{len(self.shapes)} shapes'      
        except Exception as e:
              logging.debug(f'fetch shapes {e}')    
           
    def commit(self, sender):
        """ save object to output dictionary, and hence to json file
        Need to check if object already exist. if so, replace it """
        
        object_type = self.widgets.object_type.text
        name = self.widgets.object_name.text
        coordinates = self.shape.coordinates[::self.decimate, :].tolist()
        centroid = tuple(self.shape.centroid)
        radius = self.widgets.radius.text
        score = self.widgets.score.data_source.items[self.widgets.score.selected_row[1]]
        bounce = self.widgets.bounce.text
        if self.shape.pivot is not None:
           pivot = self.shape.pivot.tolist()
        try:
            match object_type:
                case "outline":
                    object = {"centroid": centroid, "coordinates": coordinates}
                                    
                case "bumper":
                    if not radius:
                       radius = int(np.mean(np.linalg.norm(coordinates - np.array(centroid), axis=1)))
                    object = {"centroid": centroid,
                              "radius": int(radius), "score": int(score), "bounce": float(bounce)}
                case "switch":
                    object = {"centroid": centroid, "coordinates": coordinates,
                              "score": int(score), "action": bounce}
                case "flipper":
                    object = {"centroid": centroid, "coordinates": coordinates,
                              "pivot": pivot, "length": self.shape.length}
                case "wall":
                    object = {"centroid": centroid, 'coordinates': coordinates}
                case _:
                    object = None
        except Exception  as e:
             raise e        
        if object:
            self.output[object_type][name] = object                        
        
        self.next_shape(None)
        self.write_json(None)
        self.read_json()
             
    def write_json(self, sender):
        self.output['image'][self.pinball_image.name] = {"reduction": self.size_reduction, "image_size": self.image.size}
        with open(self.json_file, 'w') as f:
           json.dump(self.output, f, indent=None)
        print('written', self.json_file)
        # console.quicklook(json_file)

    def change_type(self, sender):
       selected_type = sender.selected_index
       text = sender.segments[selected_type].lower()
       self.widgets.object_type.text = text
       if text == "switch":
          self.widgets.action.text = 'Action'
          self.widgets.bounce.text = ''
       else:
          self.widgets.action.text = 'Bounce'
       if text == 'bumper':
           if not self.shape.radius:
               coords = self.shape.coordinates
               centroid = eval(self.widgets.location.text)
               radius = int(np.mean(np.linalg.norm(coords - np.array(centroid), axis=1)))
               self.widgets.radius.text = f'{radius}'
           self.widgets.bounce.text = str(1.0)

    def tab_changed(self, sender):
        # 3. Define the Tabs
        tab_data = {'Edges': self.parameters, 'Objects': self.gui}
        # Clear existing view
        for sub in self.content_area.subviews:
            self.content_area.remove_subview(sub)
            
        # Add new view based on selected title
        tab_name = sender.segments[sender.selected_index]
        active_view = tab_data[tab_name]
        active_view.frame = self.content_area.bounds
        active_view.flex = 'WH'
        self.content_area.add_subview(active_view)
        self.image =  self.open_image()
        if tab_name == 'Objects':
            if not self.shapes:
                self.shapes = self.get_shapes()
                while not self.shapes:
                    self.parameters['shapes'].background_color = 'red'
                    sleep(1)
           
            self.widgets.image.image = self.pil_to_ui(self.image)
            self.index = 0
            self.shape = self.shapes[self.index]
            self.process_shape(self.shape)
           
           
    # -------------Functions                                                                              
    def find_shape_name(self, output_dict, shape_name):
        for section, elements in output_dict.items():
            if shape_name in elements:
               return section
        return None
            
    def read_json(self):
       if os.path.exists(self.json_file):
           with open(self.json_file, 'r') as f:
               self.output = json.load(f)             
           
    def populate_from_shape(self, shape):
        self.widgets.shape_number.background_color = 'clear'
        self.widgets.location.text = f'{shape.centroid}'
        self.widgets.no_coords.text = f'{shape.no_points // self.decimate}'
        shape_types = {'outline': 0, 'circle': 1, 'rounded rectangle': 3, 'teardrop': 2, 'shape': 3, 'rectangle': 3}
        self.widgets.item_type.selected_index = shape_types[shape.shape]
        # assumes that first item is probably an outline
        # if its not, it doesn't really matter
        if self.index == 0:
            self.widgets.item_type.selected_index = 0
        if shape.shape == 'circle':
           self.widgets.radius.text = f'{shape.radius}'
           self.widgets.bounce.text = f'{1}'
           self.widgets.score.selected_row = (0, 1)
        else:
           self.widgets.radius.text = ''
        self.widgets.decimate_indicator.text = f'{self.decimate}'
        self.widgets.decimate.value = 1 / self.decimate
        self.widgets.object_type.text = self.widgets.item_type.segments[self.widgets.item_type.selected_index].lower()
            
    def populate_from_file(self, shape, section, object_name):
        
        object_data = dotdict(self.output[section][object_name])
        self.widgets.shape_number.background_color = 'cyan'
        try:
           self.decimate = int(len(shape.coordinates) / len(object_data.coordinates))
           self.widgets.no_coords.text = f'{shape.no_points // self.decimate}'
           slider_value = (self.decimate - 1) / 99
           self.widgets.decimate.value = slider_value
           self.widgets.decimate_indicator.text = f'{self.decimate}'
        
        except (TypeError, AttributeError):
           self.decimate = 1
           self.widgets.no_coords.text = f'{shape.no_points // self.decimate}'
           
        match section:
            case 'outline':
                # {"name","centroid", "coordinates"}
                self.widgets.item_type.selected_index = 0

            case 'bumper':
                # {"name","centroid", "radius","score", "bounce"}
                self.widgets.item_type.selected_index = 1
                self.widgets.radius.text = f'{object_data.radius}'
                self.widgets.bounce.text = f'{object_data.bounce}'
                self.widgets.score.selected_row = (0, 1)
                
            case 'switch':
                # {"name","centroid", "coordinates","action", "score"}
                self.widgets.item_type.selected_index = 3
                self.widgets.bounce.text = f'{object_data.action}'
                  
            case 'flipper':
                # {"name", "centroid", "coordinates", "pivot","length"}
                self.widgets.item_type.selected_index = 2
                
            case 'wall':
                # {"name", "centroid", "coordinates"}
                self.widgets.item_type.selected_index = 3
                
            case _:
                self.widgets.item_type.selected_index = 4
           
    def process_shape(self, shape):
        # get data from self.shape to populate self.widgets
        # if item exists in self.existing, populate from that instead
        # if name exists but centroid is different, add index to the name
        object_name = f"{shape.quadrant} {shape.color_names.split('/')[0]} {shape.shape}"
                
        self.decimate = max(1, shape.no_points // self.max_points)
        
        # shape details
        self.widgets.shape_number.text = f'{self.index}/{len(self.shapes)}'
        self.widgets.shape_image.image = self.pil_to_ui(shape.image)
        self.widgets.shape_image.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.widgets.shape_image.clips_to_bounds = True
        self.widgets.shape_name.text = shape.shape
        self.widgets.description.text = shape.description
        self.widgets.location.text = f'{shape.centroid}'
                        
        self.widgets.object_name.text = object_name
        
        section = self.find_shape_name(self.output, object_name)
        
        if section:
            centroid = tuple(self.output[section][object_name]['centroid'])
            if centroid == shape.centroid:
                self.populate_from_file(shape, section, object_name)
            else:
                self.widgets.object_name.text = f'{object_name}_{self.index}'
        else:
            self.populate_from_shape(shape)
            
        self.plot_coords(shape.coordinates, centroid=shape.centroid)
    
    def plot_coords(self, coords, color='green', centroid=None):
        width, height = self.image.size
        with ui.ImageContext(width, height) as ctx:
            # Draw an existing ui.Image first
            bg_img = self.pil_to_ui(self.image)
            # Draw image at a specific point or rect
            bg_img.draw(0, 0, width, height)
            
            ui.set_color(color)
            path = ui.Path()
            path.line_width = 10 / self.size_reduction
            path.move_to(*coords[0])
            [path.line_to(x, y) for x, y in coords[1:]]
            path.close()
            path.stroke()
            if centroid:
                ui.set_color('blue')
                size = 10
                path = ui.Path().oval(centroid[0] - size/2, centroid[1] - size/2, size, size)
                path.fill()
            self.widgets.image.image = ctx.get_image()    
            
    #@ui.in_background
    def get_shapes(self):
        try:
            detector = FastContourDetector(image_process=self.image_process)
            logger.debug("Finding ordered contours...")
            ordered_contours = detector.find_all_contours_ordered(self.min_contour_length,
                                                                  self.max_contour_length)
            shapes = detector.analyze_shapes(ordered_contours)
            shapes = detector.filter_duplicates(shapes, threshold=self.min_spacing)
            logger.debug(f"Found {len(ordered_contours)} ordered contours")
            
            logger.debug(f"Found {len(shapes)} filtered contours")
            for i, shape in enumerate(shapes):
                # test_plot(shape.coordinates)
                detector.process_teardrop(shape)
                image = self.image_process.crop_image(shape.coordinates)
                shape.image = image
                shape.image_size = image.size
                shape.color_names = self.image_process.closest_colors(image)
                shape.quadrant = '_'.join(self.image_process.quadrant(shape.centroid))
                shape.description = f"{shape.quadrant} {shape.color_names} {shape.shape}"
                logger.debug(f"{i}: {shape}")
      
            # detector.plot_contours(shapes, color=None, linewidth=10)
            # marked_filename = os.path.join(output_dir, 'contours_detected.png')
            # console.quicklook(marked_filename)
            
            return shapes
        except Exception as e:
           logger.debug(f'get_shapes {e}')
    
# cProfile.run('Pinball2(pinball_image)', sort='cumulative')
# Example Usage
Pinball()

# features, processed_img = process_pinball_features('table.png')
# print(f"Found {len(features)} distinct shapes/circles.")
