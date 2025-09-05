# An application to define and edit  levels of a 2D platform game
# loads sprites
# TODO fix run code 
# TODO fix change level code

import ui
import scene
import dialogs
import os
import numpy as np
from time import sleep
from pathlib import Path
import importlib
import base_path
base_path.add_paths(__file__)

from editor_view import EditorView  
from level_manager import LevelManager
from sprite_manager import SpriteManager
from pallette_view import PaletteView
from File_Picker import file_picker_dialog

# setting filepath, only stored in level_manager
#. 1. selecting file on startup
#  2. select new file
#. 3. use Save button to save everything to a new file

# TODO. change load to force filepath if not using existing
# TODO SORT OUT load and saving

# main game program may overlap background


class MainEditor:

    def __init__(self, config_file):
        self.gui = ui.load_view()
        self.sprite_manager = SpriteManager(config_file)
        self.level_manager = LevelManager()
        self.palette_view = PaletteView()                 
        self.editor_view = self.gui['editor_view']                            
        self.icon_view = self.gui['icon_view']
        self.icon_view.action = self.palette_action
        
        self.link_classes()
        
        self.gui['back'].enabled = False        
        self.pan_mode = False
        self.gui['sprite_size'].text = f'grid:({int(self.sprite_manager.most_sizes.x)}, {int(self.sprite_manager.most_sizes.y)})'
        self.gui.name = "Game Editor"
        self.gui['zoom'].text = f'Zoom: x1'
        
        self.run_module = self.sprite_manager.run_module 
        if self.run_module is None:
           self.gui['run'].enabled = False       
        self.load_action(None)                    
        self.palette_view.current_data = self.sprite_manager.image_dict              
        self.palette_view.update_list_view()          
        self.gui.present('full_screen')
                    
    def link_classes(self):
        # allow subclasses access to others
        self.editor_view.sprite_manager = self.sprite_manager
        self.editor_view.level_manager = self.level_manager
        self.editor_view.gui = self.gui
        self.editor_view.main_view = self  
                
        self.level_manager.editor_view = self.editor_view    
        self.level_manager.sprite_manager = self.sprite_manager   
        self.level_manager.gui = self.gui
        self.level_manager.main_view = self  
        
        self.palette_view.sprite_manager = self.sprite_manager
        self.palette_view.editor_view = self.editor_view
        self.palette_view.gui = self.gui
        self.palette_view.main_view = self           
                   

    def update_controls(self, filepath):
        self.gui['level'].title = self.level_manager.level       
        self.gui['textfield1'].text = self.level_manager.levels[self.level_manager.level]['text1']
        self.gui['textfield2'].text = self.level_manager.levels[self.level_manager.level]['text2']
        self.gui.name = Path(filepath).name
             
    def highlight(self, button, mode):
        # Highlight button if active, unhighlight if inactive
        if mode:
            button.background_color = '#4C4C4C'
            button.tint_color = 'white'
        else:
            button.background_color = (0, 0, 0, 0)
            button.tint_color = 'black'
    
    # actions from ui object interaction                                       
    @ui.in_background
    def save_action(self, sender):        
        self.level_manager.save_file()      
        
    def level_action(self, sender):
        self.level_manager.choose_level()        
        self.editor_view.get_level_data(self.level_manager.level_name)
          
    def text_action(self, sender):
        self.level_manager.change_text(sender)        
        
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
        self.gui[
            'zoom'].text = f'Zoom: x{self.editor_view.current_scale}'

    def zoomout_action(self, sender):
        self.editor_view.zoom_out()
        if self.editor_view.current_scale < 2:
           self.editor_view.pan_mode = False 
           self.highlight(self.gui['place'], False)
           self.highlight(self.gui['erase'], False)
           self.highlight(self.gui['pan'], False)
        self.gui['zoom'].text = f'Zoom: x{self.editor_view.current_scale}'    

    def place_action(self, sender):
        # set place mode
        self.editor_view.tool_mode = self.editor_view.place_sprite  
        self.editor_view.pan_mode = False 
        self.highlight(self.gui['place'], True)
        self.highlight(self.gui['erase'], False)
        self.highlight(self.gui['pan'], False)

    def erase_action(self, sender):
        # set erase mode
        self.editor_view.tool_mode = self.editor_view.erase_sprite  
        self.editor_view.pan_mode = False 
        self.highlight(self.gui['place'], False)
        self.highlight(self.gui['erase'], True)
        self.highlight(self.gui['pan'], False)
        
    def pan_action(self, sender):
        # set pan mode used in touch
        self.editor_view.pan_mode = True 
        self.highlight(self.gui['place'], False)
        self.highlight(self.gui['erase'], False)
        self.highlight(self.gui['pan'], True)
            
    @ui.in_background    
    def raw_file_action(self, sender, reason='File contents'):
        # view current file and allow raw modification
        with open(self.level_manager.filepath, 'r', encoding='utf-8') as f:
            contents = f.read()
        modified = dialogs.text_dialog(title=reason, text=contents, font=('Courier', 20) )
        if modified and modified != contents:
            with open(self.level_manager.filepath, 'w', encoding='utf-8') as f:
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
            self.level_manager.filepath = filepath
            if self.level_manager.load_levels(filepath):
               self.editor_view.load_map()
               levels = list(self.level_manager.levels)
               self.level_manager.all_used_sprites()
               self.level_manager.level_name = levels[0]
               #self.level = self.level_manager.current_level_name
               self.update_controls(filepath)
               self.sprite_manager.image_dict['Used Sprites'] = self.level_manager.used_dict
               
               self.palette_view.current_data = self.sprite_manager.image_dict    
               #self.sprite_manager.config.print_tree(self.palette_view.current_data)          
               self.palette_view.update_list_view()  
            
            else:
                text = self.level_manager.error_text
                self.raw_file_action(None, reason=text)
        else:
           fields = [  
                    {'type': 'number', 'key': 'filepath', 
                     'value': f'{os.curdir}/new_game.txt', 'title': 'File'},
                    {'type': 'number', 'key': 'rows', 
                     'value': '20', 'title': 'Y'},
                    {'type': 'number', 'key': 'columns', 
                     'value': '20', 'title': 'X'}]
           values = dialogs.form_dialog(title='File and Size', fields=fields)
           if values:
                h = int(values['rows'])
                w = int(values['columns'])
                self.level_manager.filepath = values['filepath']
           else:
              h, w = 20, 20
           
           self.editor_view.grid_height = h
           self.editor_view.grid_width = w
           level_data = {'table': [[' ' for _ in range(w)] 
                                   for _ in range(h)],
               'text1': 'level 1', 'text2': 'Additional text'}
           self.level_manager.add_level('level 1', level_data)
           self.editor_view.get_level_data('level 1')
           self.level_manager.save_levels(self.level_manager.filepath)
        
    @ui.in_background      
    def run_action(self, sender):       
        # switch to program to run level. resume when program is closed
        self.level_manager.save_if_changed()                
        # close the editor view and wait
        self.gui.close()
        
        sleep(1)  
        
        print(self.run_module)      
        
        module = importlib.import_module(self.run_module)
        game = module.main(file=self.level_manager.filepath, 
                           level_name=self.level_manager.level)
        # loop slowly until game closed
        while game.view.on_screen:
            sleep(1)
        # now show editor again         
        self.gui.present('full_screen')        
        

if __name__ == '__main__':
    editor_app = MainEditor('multigame_config2')
    #editor_app = MainEditor('kye_config')
