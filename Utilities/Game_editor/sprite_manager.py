# sprite_manager.py
# requires a configuration python file
# to provide a lookup and image dictionary
import ui
import io
import importlib
from collections import Counter


class SpriteManager:
    def __init__(self, config_file):
        # get configuration file
        config_module = importlib.import_module(config_file)
        self.config = config_module.Config()
        self.image_dict = self.config.image_dict
        self.lookup = self.config.lookup
        self.rev_lookup = {v: k for k, v in self.lookup.items()}
        self.run_module = getattr(self.config, 'run_module', None)
        self.sprite_map = {}
        self.load_sprites()  # Load sprites
        sprite_sizes = [img.size for img in self.sprite_map.values()]
        sprint_size_str = [f'{int(sprite_size.x)}x{int(sprite_size.y)}' for sprite_size in sprite_sizes]
        
        # TODO this is not robust can end up with smallest size
        counter = Counter(sprint_size_str)
        self.most_sizes = max(counter, key=lambda key: counter[key])
        s = self.most_sizes.split('x')
        self.most_sizes = ui.Size(int(s[0]), int(s[1]))
        # allow config to set own gridsize
        if hasattr(self.config, 'min_size'):
           self.most_sizes = self.config.min_size            
               
        
    def pil_to_ui(self, img):
        with io.BytesIO() as bIO:
            img.save(bIO, 'png')
            return ui.Image.from_data(bIO.getvalue())
            
    def find_key(self, data, target_key):
       """
       Recursively searches a multilevel dictionary for a specific key and returns its value.
       """
       if isinstance(data, dict):
           for key, value in data.items():
               if key == target_key:
                   return value
               
               # If the value is a dictionary, recurse into it
               result = self.find_key(value, target_key)
               if result is not None:
                   return result
   
       # If the data is a list, iterate through its elements and search
       elif isinstance(data, list):
           for item in data:
               result = self.find_key(item, target_key)
               if result is not None:
                   return result       
       return None

    def load_sprites(self):
        for k, v in self.lookup.items():
            img = self.find_key(self.image_dict, v)            
            if img:
               self.add_sprite(k, self.pil_to_ui(img))
               
    def add_sprite(self, char, image_obj):
        if len(char) == 1:
            self.sprite_map[char] = image_obj
        else:
            print(f"Warning: '{char}' is not a valid single alphanumeric character for a sprite.")

    def get_sprite_image(self, char):
        return self.sprite_map.get(char)

    def get_all_sprites(self):
        return self.sprite_map
