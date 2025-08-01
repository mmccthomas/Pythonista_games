# sprite_manager.py (Simplified)
import ui
import io
from kye_config import lookup, image_dict
# imports image_dict

class SpriteManager:
    def __init__(self):
        self.sprite_map = {}
        self.load_sprites() # Load sprites
        
    def pil_to_ui(self, img):
        with io.BytesIO() as bIO:
         img.save(bIO, 'png')
         return ui.Image.from_data(bIO.getvalue())
         
    def ui_to_pil(img):
         return Image.open(io.BytesIO(img.to_png()))
    
    def load_sprites(self):
         for k, v in lookup.items():
            self.add_sprite(k, self.pil_to_ui(image_dict[v[0]]))
            
    
    def add_sprite(self, char, image_obj):
        if len(char) == 1:
            self.sprite_map[char] = image_obj
        else:
            print(f"Warning: '{char}' is not a valid single alphanumeric character for a sprite.")

    def get_sprite_image(self, char):
        return self.sprite_map.get(char)

    def get_all_sprites(self):
        return self.sprite_map

