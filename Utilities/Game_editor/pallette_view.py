# palette_view.py (Simplified)
import ui
import io
from PIL import Image


class PaletteView(ui.View):
 
    def __init__(self, sprite_manager, editor_view_delegate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sprite_manager = sprite_manager
        self.editor_view_delegate = editor_view_delegate  # To notify the editor of selection
        self.name = "Sprite Palette"
        self.background_color = '#333333'
        self.setup_palette()
        self.setup_list_dialog()
        
    def pil_to_ui(self, img):
        with io.BytesIO() as bIO:
         img.save(bIO, 'png')
         return ui.Image.from_data(bIO.getvalue())
         
    def ui_to_pil(self, img):
        return Image.open(io.BytesIO(img.to_png()))
         
    def scale(self, image, scale=2):
        img = self.ui_to_pil(image)
        w, h = img.size
        img = img.resize((int(scale * w), int(scale * h)))
        return self.pil_to_ui(img)
         
    def setup_list_dialog(self):
            
        itemlist = [{'image': self.scale(image, 2.5), 'title': char} for char, image in self.sprite_manager.get_all_sprites().items()]
        
        self.icon_list = ui.ListDataSource(items=itemlist)
        self.icon_list.number_of_lines = 10
    
    def setup_palette(self):
        x_offset = 10
        y_offset = 10
        button_size = 32
        padding = 5

        sorted_sprites = sorted(self.sprite_manager.get_all_sprites().items())
        # print(sorted_sprites)
        for char, image in sorted_sprites:
            btn = ui.Button(image=image)
            btn.frame = (x_offset, y_offset, button_size, button_size)
            btn.action = self.sprite_selected
            btn.char_value = char  # Store the character for later retrieval
            self.add_subview(btn)

            x_offset += button_size + padding
            if x_offset + button_size > self.width:
                x_offset = 10
                y_offset += button_size + padding

    def sprite_selected(self, sender):
        selected_char = sender.char_value
        print(f"Selected sprite: {selected_char}")
        if self.editor_view_delegate:
            self.editor_view_delegate.selected_sprite_char = selected_char

