# level_manager.py (Simplified)
# Uses  file format used by Kye
# deals with everything relating to files and levels
# TODO current level should be kept here
# do i want to always create new empty level?
"""
number of levels (int)
level name
hint text
completion text
game lines (20 for kye)
"""
from collections import defaultdict, Counter
import numpy as np
import operator
import ui
import os
import dialogs

def rle(inarray):
  """ run length encoding. Partial credit to R rle function.
  Multi datatype arrays catered for including non Numpy
  returns: tuple (runlengths, startpositions, values) """
  inputarray = np.asarray(inarray)                # force numpy
  n = len(inputarray)
  if n == 0:
      return (None, None, None)
  else:
      y = inputarray[1:] != inputarray[:-1]  # pairwise unequal (string safe)
      i = np.append(np.where(y), n - 1)   # must include last element posi
      runlengths = np.diff(np.append(-1, i))  # run lengths
      startpositions = np.cumsum(np.append(0, runlengths))[:-1]  # positions
      return (runlengths, startpositions, inputarray[i])

class LevelManager:
    def __init__(self):
        # Dictionary to hold levels: level_name: {'text1': level_hint, 'text2': level_finish, 'table': [chars, chars..]}
        self.levels = {}
        self.filepath = None
        self.file_modified = False
        self.error_text = None
        self.level_name = None    

    def load_levels(self, filepath):
        # maybe return more suitable data
        try:
            self.levels = self.get_file(filepath)
            # check all levels valid
            # size of  table should all be identical
            for k, v in self.levels.items():
              table = v['table']
              lengths = [len(row) for row in table]
              counts = Counter(lengths)
              # Find the item with a count of 1
              for number, count in counts.items():
                 if count == 1:         
                    where = lengths.index(number)         
                    self.error_text = f'invalid line length  in section {k} on {where}th line'                              
                    raise ValueError(f'invalid line length  in section {k} on {where}th line')                
              
            self.filepath = filepath
            # print(f"Loaded levels from {filepath}")
            if self.levels:
                self.level_name = list(self.levels.keys())[0]  # Set first level as current
                
            return True
        except ValueError as e:
            print(f"Error loading levels in file {filepath} {e}")
            return False
        except Exception as e:
            print(f"Error loading levels in file {filepath} {e}")
            return False

    def save_levels(self, filepath):
        try:
            formatted_data = self.format_file()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
            # print(f"Saved levels to {filepath}")
            return True
        except Exception as e:
            print(f"Error saving levels: {e}")
            return False

    def get_level_data(self, level_name):
        try:
            level_strings = self.levels.get(level_name)['table']
            level_data = np.array([[char 
                                    for char in level_string] 
                                  for level_string in level_strings])
            return level_data
        except (KeyError, TypeError):
            return None
            
    @ui.in_background      
    def choose_level(self):
        items =  ['New Level'] + list(self.levels)
        level = dialogs.list_dialog('Select level',
                                    items=items)
        if level in self.levels: # existing level
            # TODO why editor_view?
            level_data = self.get_level_data(level)     
            self.level_name = level           
        else: # new level
           level_name = dialogs.input_alert(title='Create new level', 
                                            message='Enter level name')
           if level_name:
               level_name = level_name.upper()
               level_data = {'table': [[' ' for _ in range(self.editor_view.grid_width)] 
                                       for _ in range(self.editor_view.grid_height)],
               'text1': 'New level', 'text2': 'Additional text'}
               self.add_level(level_name, level_data)
               
               self.level_name = level_name
          
        if hasattr(self, 'filename'):
            self.update_controls(self.filepath)
        else:
            self.save_file()
            self.update_controls(self.filepath)
                      
    def create_new_level(self, filepath):
        self.levels[self.level_name]['table'] = self.editor_view.current_level_data
        self.save_levels(filepath)
        self.filepath  = filepath
        print(f"Levels saved to {filepath}")
        
    def add_level(self, level_name, level_data=None):
        if level_name not in self.levels:
            if level_data is None:
                # Create an empty 20x15 level by default
                level_data = [[' ' for _ in range(20)] for _ in range(15)]
            self.levels[level_name] = level_data
            self.level_name = level_name
            print(f"Added new level: {level_name}")
            self.file_modified = True
        else:
            print(f"Level '{level_name}' already exists.")

    def delete_level(self, level_name):
        if level_name in self.levels:
            del self.levels[level_name]
            print(f"Deleted level: {level_name}")
            if self.level_name == level_name:
                self.level_name = list(self.levels.keys())[0] if self.levels else None
            self.file_modified = True
        else:
            print(f"Level '{level_name}' not found.")

    def get_current_level_text_representation(self):
        if self.level_name and self.level_name in self.levels:
            return "\n".join(["".join(row) for row in self.levels[self.level_name]['table']])
        return "No level selected or level data empty."

    def get_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
          game_data = f.read().splitlines()
        if not game_data:
            raise ValueError('File has Empty data')
        #game_data = game_data[:-1] # dont count final CR
        no_levels = int(game_data[0])
        # catch extra blank line in middle or at end
        for index, line in enumerate(game_data):
            if line == "":
                 raise ValueError(f'Blank line at line {index}')
        # find if remaining file is divisble by number of levels
        n, modulo = divmod(len(game_data)-1 , no_levels)
        if  modulo != 0:
          lengths = [len(row) for row in game_data]
          z, p, ia = rle(lengths)
          counts = Counter(lengths)
          # the tables will have the maximum count
          max_length = max(counts.items(), key=operator.itemgetter(1))[0]
          # use Run Length Encoding to get lengths of each line, grouped
          # by same length
          z, places, length_values = rle(lengths) 
          print(f'Incorrect structure. Table line length is {max_length}')
          print(f'length profile is {z}')
          self.error_text = f'Incorrect structure. use the length profile to find line'
          raise ValueError(f'Incorrect structure. use the length profile to find line')
        
        level_dict = defaultdict()
        index = 1
        for level in range(no_levels):
          level_name, level_hint, level_finish = game_data[index: index + 3]
          table = game_data[index + 3: index + n]
          index += n   
          level_dict[level_name] = {'text1': level_hint, 'text2': level_finish, 'table': table}
        return level_dict
    
    def all_used_sprites(self):
        #all_names = set()
        self.used_dict = {}
        # raise Exception
        for level_name, level  in self.levels.items():
           level_grid = level['table']           
           for row in level_grid:
               for char in row:                
                   if char in self.sprite_manager.lookup:                    
                       #all_names.add(self.sprite_manager.lookup[char])
                       self.used_dict[self.sprite_manager.lookup[char]] = self.sprite_manager.sprite_map[char]                               
        print('icon names used:', self.used_dict.keys())               
        return self.used_dict        
                
    def format_file(self):
        no_sections = len(self.levels)
        file_contents = [f'{no_sections}']
        for name, data in self.levels.items():
           file_contents.append(f'{name}')
           file_contents.append(f'{data["text1"]}')
           file_contents.append(f'{data["text2"]}')
           file_contents.extend([f'{"".join(line)}' for line in data["table"]])          
        #file_contents.append('\n')       
        return '\n'.join(file_contents)
       
    @ui.in_background
    def save_file(self):        
        initial_name = getattr(self, 'filepath', f'{os.curdir}/')
        if initial_name is None:
           initial_name = f'{os.curdir}/'
        filepath = dialogs.input_alert('Save As', 'Enter file name',
                                       initial_name)        
        if filepath:
            self.create_new_level(filepath)
            
    @ui.in_background       
    def save_if_changed(self):        
        # check if any modications made. Save if so
        existing_data = self.levels[self.level_name]['table']
        current_data = ["".join(line) for line in self.gui.current_level_data]     
        # print(existing_data)                  
        # print(current_data)
        if existing_data != current_data:           
           self.levels[self.level_name]['table'] = current_data
           self.save_levels(self.filepath)
           dialogs.hud_alert('File saved')
           
    def change_text(self, sender):
        # change text
        if sender.name == 'textfield1':
            self.levels[self.level_name]['text1'] = sender.text
        else:
            self.levels[self.level_name]['text2'] = sender.text
            
if __name__ == '__main__':
  # testing
  level = LevelManager()
  f= '/private/var/mobile/Containers/Data/Application/24BEC035-C28E-496A-A41A-CEC669E05513/Documents/Pythonista_games/Kye/levels/cmt.KYE'
  level.load_levels(f)
  #print(level.levels)
  new_data=  {'text1': 'Stay out of the road.', 'text2': "If you're this good - design some new levels.", 'table': ['555555555555555555555555555555', '5K   5553  1553 15c5         5', '5   c              155e5555e55', '55e55 7a55e5555e5a        c  5', '5   5 5           a55c5ll    5', '5   5 a               5U 5  75', '5   5 15e55555e55 759 5  e  55', '5   5           a 5 5 5  5  15', '5   1c55e555e55 5 e 5 5555   5', '5             5d5 5 e 1c55   5', '5555e55e555e555 5 5 a    5   5', '5c              5 e 159  5  75', '55 75e5555e5555a5 5   e  e  55', '55 c              5   5  5  15', '55 5 45e555555e55a55e53  5   5', '55 5      >             c5   5', '53 1c55e55555e55555e55  Ru v 5', '5            r            c5 5', '55c555559   75555559   75555*5', '555555555555555555555555555555']}
  level.choose_level()
  level.add_level('ABC', new_data)
  level.save_levels('temp.txt')
