# main.py (Simplified)
import ui
import dialogs
import os
import numpy as np
from time import sleep
from pathlib import Path
import base_path

base_path.add_paths(__file__)
from editor_view import EditorView
from level_manager import LevelManager
from sprite_manager import SpriteManager
from pallette_view import PaletteView
from File_Picker import file_picker_dialog

# Added Run button.
# to run the associated game with current file.
# when you exit the game, return to editor at same point
# e.g modify Kye.py to enter at main() with kwarg as file and level_name

# this runs module "run_module" which is imported in config_file
# TODO 
# deal with different sprite sizes
# establish base sprite size from greater number with same size.
# this will be used to scale the grid
# placing a larger sprite will cover more of the grid, but allow overlap
# since only the start of the sprite will occupy a character position

# fix kye again
# issue with trying to scroll table


class MainEditor:

    def __init__(self, config_file):
        self.game_view = ui.load_view()
        self.sprite_manager = SpriteManager(config_file)
        self.level_manager = LevelManager()
        self.editor_view = self.game_view['editor_view']
        
        self.editor_view.sprite_manager = self.sprite_manager
        self.editor_view.level_manager = self.level_manager
        self.icon_view = self.game_view['icon_view']
        self.icon_view.action = self.palette_action
        #self.setup_menu()
        self.palette_view = PaletteView(self.sprite_manager,  self.editor_view, self)
        self.palette_view.update_list_view() 
        self.game_view['back'].enabled = False
        
        self.pan_mode = False
        self.game_view['sprite_size'].text = f'grid:({int(self.sprite_manager.most_sizes.x)}, {int(self.sprite_manager.most_sizes.y)})'
        self.game_view.name = "Game Editor"
        self.game_view['zoom'].text = f'Zoom: x1'
        self.game_view.present('full_screen')
        self.run_module = self.sprite_manager.run_module 
        if self.run_module is None:
           self.game_view['run'].enabled = False       
        self.load_action(None)
        

    def setup_menu(self):
        
        self.load_action(None)

    @ui.in_background
    def palette_setup(self):
        self.icon_view.action = self.palette_action
        #self.icon_view.data_source = ui.ListDataSource([])
        #self.icon_view.delegate = self.icon_view.data_source
        #self.icon_view.data_source.action = self.palette_action
        
        
    def find_key(data, target_key):
        """
        Recursively searches a multilevel dictionary for a specific key and returns its value.            
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_key:
                    return value
                
                # If the value is a dictionary, recurse into it
                result = find_key(value, target_key)
                if result is not None:
                    return result
    
        # If the data is a list, iterate through its elements and search
        elif isinstance(data, list):
            for item in data:
                result = find_key(item, target_key)
                if result is not None:
                    return result        
        return None

    def update_controls(self, filepath):
        self.game_view['level'].title = self.level       
        self.game_view['textfield1'].text = self.level_manager.levels[self.level]['text1']
        self.game_view['textfield2'].text = self.level_manager.levels[self.level]['text2']
        self.game_view.name = Path(filepath).name
             
    def highlight(self, button, mode):
        # Highlight button if active, unhighlight if inactive
        if mode:
            button.background_color = '#4C4C4C'
            button.tint_color = 'white'
        else:
            button.background_color = (0, 0, 0, 0)
            button.tint_color = 'black'

    @ui.in_background
    def save_action(self, sender):
        initial_name = self.level_manager.filepath
        filepath = dialogs.input_alert('Save As', 'Enter file name',
                                       initial_name)
        if filepath:
            self.level_manager.levels[self.editor_view.current_level_name]['table'] = self.editor_view.current_level_data
            self.level_manager.save_levels(filepath)
            print(f"Levels saved to {filepath}")

    @ui.in_background
    def palette_action(self, sender):
        # modify to pass action to palletteview
        selected, sprite_size = self.palette_view.item_selected(sender)
        if selected:
            self.editor_view.selected_sprite_char = selected
                        
    def back_action(self, sender):
        self.palette_view.back_to_parent()

    def undo_action(self, sender):
        self.editor_view.undo()

    def zoomin_action(self, sender):
        self.editor_view.zoom_in()
        self.game_view[
            'zoom'].text = f'Zoom: x{self.editor_view.current_scale}'

    def zoomout_action(self, sender):
        self.editor_view.zoom_out()
        if self.editor_view.current_scale < 2:
           self.editor_view.pan_mode = False 
           self.highlight(self.game_view['place'], False)
           self.highlight(self.game_view['erase'], False)
           self.highlight(self.game_view['pan'], False)
        self.game_view['zoom'].text = f'Zoom: x{self.editor_view.current_scale}'

    @ui.in_background
    def level_action(self, sender):
        items =  ['New Level'] + list(self.level_manager.levels)
        level = dialogs.list_dialog('Select level',
                                    items=items)
        if level in self.level_manager.levels :
            self.editor_view.set_level(level)            
        else:
           level_name = dialogs.input_alert(title='Create new level', message='Enter level name')
           if level_name:
               level_name = level_name.upper()
               level_data = {'table': [[' ' for _ in range(self.editor_view.grid_width)] 
                                       for _ in range(self.editor_view.grid_height)],
               'text1': 'New level', 'text2': 'Additional text'}
               self.level_manager.add_level(level_name, level_data)
               self.editor_view.set_level(level_name)
               
        self.level = self.editor_view.current_level_name        
        self.update_controls(self.filepath)

    def place_action(self, sender):
        # set place mode
        self.editor_view.tool_mode = self.editor_view.place_sprite  
        self.editor_view.pan_mode = False 
        self.highlight(self.game_view['place'], True)
        self.highlight(self.game_view['erase'], False)
        self.highlight(self.game_view['pan'], False)

    def erase_action(self, sender):
        # set erase mode
        self.editor_view.tool_mode = self.editor_view.erase_sprite  
        self.editor_view.pan_mode = False 
        self.highlight(self.game_view['place'], False)
        self.highlight(self.game_view['erase'], True)
        self.highlight(self.game_view['pan'], False)
        
    def pan_action(self, sender):
        # set pan mode used in touch
        self.editor_view.pan_mode = True 
        self.highlight(self.game_view['place'], False)
        self.highlight(self.game_view['erase'], False)
        self.highlight(self.game_view['pan'], True)
        
    def text_action(self, sender):
        # change text
        if sender.name == 'textfield1':
            self.level_manager.levels[self.level]['text1'] = sender.text
        else:
            self.level_manager.levels[self.level]['text2'] = sender.text
        
    @ui.in_background    
    def raw_file_action(self, sender, reason='File contents'):
        # view current file and allow raw modification
        with open(self.filepath, 'r', encoding='utf-8') as f:
            contents = f.read()
        modified = dialogs.text_dialog(title=reason, text=contents, font=('Courier', 20) )
        if modified and modified != contents:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(modified)
                 
    @ui.in_background
    def load_action(self, sender):
        current_dir = os.path.dirname(os.path.realpath('.'))
        parent_dir = os.path.dirname(os.path.realpath(current_dir))
        filepath = file_picker_dialog('Select game file',
                                      root_dir=parent_dir,
                                      multiple=False,
                                      select_dirs=False)
        if filepath:
            self.filepath = filepath
            if self.level_manager.load_levels(filepath):
               self.editor_view.load_map()
               self.level = self.level_manager.current_level_name
               self.update_controls(filepath)
            else:
                text = self.level_manager.error_text
                self.raw_file_action(None, reason=text)
        else:
           #size = dialogs.input_alert('enter display size row, cols')
           #h, w = size.split(',')
           h, w = 10,20
           self.editor_view.grid_height = int(h)
           self.editor_view.grid_width = int(w)
           level_data = {'table': [[' ' for _ in range(self.editor_view.grid_width)] 
                                       for _ in range(self.editor_view.grid_height)],
               'text1': 'New level', 'text2': 'Additional text'}
           self.level_manager.add_level('New level', level_data)
           self.editor_view.set_level('New level')
            
    @ui.in_background      
    def run_action(self, sender):       
        # switch to program to run level. resume when program is closed
        # check if any modications made. Save if so
        existing_data = self.level_manager.levels[self.editor_view.current_level_name]['table']
        current_data = ["".join(line) for line in self.editor_view.current_level_data]                           
        if existing_data != current_data:           
           self.level_manager.levels[self.editor_view.current_level_name]['table'] = current_data
           self.level_manager.save_levels(self.filepath)
           dialogs.hud_alert('File saved')
           
        # close the editor view and wait
        self.game_view.close()
        sleep(1)
        
        game = self.run_module.main(file=self.filepath, level_name=self.level)
        # loop slowly until game closed
        while game.on_screen:
          sleep(1)
        # now show editor again         
        self.game_view.present('full_screen')        
        #self.setup_menu()
        

if __name__ == '__main__':
    editor_app = MainEditor('multigame_config')
    #editor_app = MainEditor('kye_config')

