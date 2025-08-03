# sprite_manager.py
# requires a configuration python file
# to provide a lookup and image dictionary
import ui
import io
import importlib


class SpriteManager:
    def __init__(self, config_file):
        # get configuration file
        config = importlib.import_module(config_file)
        self.image_dict = getattr(config, 'image_dict')
        self.lookup = getattr(config, 'lookup')
        self.run_module = getattr(config, 'run_module', None)
        self.sprite_map = {}
        self.load_sprites()  # Load sprites
        
    def pil_to_ui(self, img):
        with io.BytesIO() as bIO:
            img.save(bIO, 'png')
            return ui.Image.from_data(bIO.getvalue())
    
    def load_sprites(self):
        for k, v in self.lookup.items():
            self.add_sprite(k, self.pil_to_ui(self.image_dict[v[0]]))
               
    def add_sprite(self, char, image_obj):
        if len(char) == 1:
            self.sprite_map[char] = image_obj
        else:
            print(f"Warning: '{char}' is not a valid single alphanumeric character for a sprite.")

    def get_sprite_image(self, char):
        return self.sprite_map.get(char)

    def get_all_sprites(self):
        return self.sprite_map
