# palette_view.py (Simplified)
# lowest level structure should be {'image': ui.image, 'title': 'code {code} {size}'}
import ui
import io
from PIL import Image


class PaletteView(ui.View):
 
    def __init__(self, sprite_manager, editor_view, main_view, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sprite_manager = sprite_manager
        self.editor_view = editor_view  # To notify the editor of selection
        self.main_view = main_view
        self.name = "Sprite Palette"
        self.background_color = '#333333'       
        self.data = self.sprite_manager.image_dict
        self.history = []
        self.current_data = self.data
        self.update_list_view()
        
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

    def sprite_selected(self, sender):
        selected_char = sender.char_value
        if self.editor_view:
            self.editor_view.selected_sprite_char = selected_char
    
    def back_to_parent(self):
        """Goes up one level in the dictionary."""
        if self.history:
            self.current_data = self.history.pop()
            self.update_list_view()
            self.set_backbutton()
       
    #@ui.in_background
    def item_selected(self, sender):
        """Called when an item in the list view is selected."""
        selected_index = sender.selected_row        
        selected_key = list(self.current_data.keys())[selected_index]
        selected_value = self.current_data[selected_key]
        if isinstance(selected_value, dict):
            # If the selected item is a dictionary, navigate into it
            self.history.append(self.current_data)
            self.current_data = selected_value
            self.update_list_view()
            self.set_backbutton()
            return None, None
        else:                        
            try:
                selected = selected_value                         
                size = selected.size               
                selected = self.sprite_manager.rev_lookup[selected_key]
                self.main_view.game_view['spritename'].text = selected_key
            except Exception as e:
                selected = selected_value
                size = None
            return selected, size                
        
    def set_backbutton(self):        
        self.main_view.game_view['back'].enabled = self.history is not None
            
    def update_list_view(self):
        """Updates the list view with the current level of dictionary keys."""
        items = []
        for key in self.current_data.keys():
            value = self.current_data[key]
            if isinstance(value, dict):
                # This item is a nested dictionary, so it can be "expanded"
                items.append(key)
            else:
                # This item is a simple value
                try:
                    items.append({'image': self.scale(self.pil_to_ui(value),2), 'title': f'{self.sprite_manager.rev_lookup[key]} {value.size}'} )
                except  (AttributeError, KeyError):
                    pass
        self.main_view.icon_view.data_source = ui.ListDataSource(items) 
        self.main_view.icon_view.reload_data()            
