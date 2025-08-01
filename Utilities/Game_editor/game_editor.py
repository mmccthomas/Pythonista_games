# main.py (Simplified)
import ui
import dialogs
from time import sleep
from pathlib import Path
import base_path
base_path.add_paths(__file__)
from editor_view import EditorView
from level_manager import LevelManager
from sprite_manager import SpriteManager
from pallette_view import PaletteView
from File_Picker import file_picker_dialog

class MainEditor:
    def __init__(self):
        self.game_view = ui.load_view()
        self.sprite_manager = SpriteManager()
        self.level_manager = LevelManager()        
        self.editor_view = self.game_view['editor_view'] #EditorView()         
        self.palette_view = PaletteView(self.sprite_manager, self.editor_view)
        #self.editor_view.add_subview(self.palette_view) # Or present it as a separate sheet                
        self.editor_view.sprite_manager = self.sprite_manager
        self.editor_view.level_manager = self.level_manager
        self.icon_view = self.game_view['icon_view']
        self.game_view.name = "Game Editor"
        self.game_view.present('full_screen')
        sleep(1)
        self.setup_menu()

    def setup_menu(self):
                
        self.palette_setup()
        self.game_view['zoom'].text = f'Zoom: x1'
        # More menu items would be added here (Load, Zoom, Pan, Levels)
        self.load_action(None)
        
    @ui.in_background     
    def palette_setup(self):
        items = self.palette_view.icon_list
        self.icon_view.action = self.palette_action
        self.icon_view.data_source = items
        self.icon_view.delegate = items
        self.icon_view.data_source.action = self.palette_action
        self.icon_view.reload_data()
        
    @ui.in_background  
    def save_action(self, sender):
        initial_name = self.level_manager.filepath
        filepath = dialogs.input_alert('Save As', 'Enter file name', initial_name)
        
        if filepath:
            self.level_manager.save_levels(filepath)
            print(f"Levels saved to {filepath}")          
              
    @ui.in_background  
    def palette_action(self, sender):        
        sel_index = sender.selected_row
        sel = list(sender.items)[sel_index]['title']
        self.editor_view.selected_sprite_char = sel
                 
    def undo_action(self, sender):
        self.editor_view.undo() 
        
    def zoomin_action(self, sender):
      self.editor_view.zoom_in()
      self.game_view['zoom'].text = f'Zoom: x{self.editor_view.current_scale}'      
      
    def zoomout_action(self, sender):
      self.editor_view.zoom_out()
      self.game_view['zoom'].text = f'Zoom: x{self.editor_view.current_scale}'      
    
    @ui.in_background 
    def level_action(self, sender):      
      level = dialogs.list_dialog('Select level', items=list(self.level_manager.levels))
      if level:
          self.editor_view.set_level(level)
          sender.title = level
      
    def place_action(self, sender):
      self.editor_view.tool_mode = self.editor_view.place_sprite #
      self.highlight(self.game_view['place'], True)
      self.highlight(self.game_view['erase'], False)      
      
    def erase_action(self, sender):
      self.editor_view.tool_mode = self.editor_view.erase_sprite #
      self.highlight(self.game_view['place'], False)
      self.highlight(self.game_view['erase'], True)
              
    #@ui.in_background
    def load_action(self, sender):
        current_dir = os.path.dirname(os.path.realpath('.'))
        parent_dir = os.path.dirname(os.path.realpath(current_dir))
        filepath = file_picker_dialog('Select game file', root_dir=parent_dir, multiple=False, select_dirs=False)
        #filepath = '/private/var/mobile/Containers/Data/Application/24BEC035-C28E-496A-A41A-CEC669E05513/Documents/Pythonista_games/Utilities/Game_editor/DEFAULT.KYE'
        print(f'{filepath=}')
        if filepath:
            self.level_manager.load_levels(filepath)
            self.editor_view.load_map()
            self.game_view['level'].title = self.level_manager.current_level_name
            self.game_view.name = Path(filepath).name
            
            
    def highlight(self, button, mode):       
       # Highlight button if active, unhighlight if inactive
       if mode:
          button.background_color = '#4C4C4C'
          button.tint_color = 'white'
       else:
           button.background_color = (0, 0, 0, 0)
           button.tint_color = 'black' 
    

if __name__ == '__main__':
    editor_app = MainEditor()


