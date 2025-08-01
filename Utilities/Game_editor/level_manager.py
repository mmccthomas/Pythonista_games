# level_manager.py (Simplified)
# Uses  file format used by Kye
"""
number of levels (int) 
level name
hint text
completion text
game lines (20 for kye)
555555555555555555555555555555
5T   e       K*  a    d e   E5
5    b 455556        a  b    5
5    b dvvvvd           b    5
5    b dvvvvd          ab    5
5ebbbe eeBBee       c   ebbbe5
5               a            5
5 8rre                a ell8 5
5 5>>e      s  S        e<<5 5
5 5>>B                  B<<5 5
5 5>>B               b  B<<5 5
5 5>>e      S  s     U  e<<5 5
5 2rre               b  ell2 5
5                 bRbb       5
5ebbbe eeeeee  7555559  ebbbe5
5    b u^^^^u  5     5  b    5
5    b u^^^^u  5     5  b    5
5    b 455556  5     5  b    5
5C   e         e  [  e  e   ~5
555555555555555555555555555555
"""
from collections import defaultdict
import numpy as np

class LevelManager:
    def __init__(self):
        # Dictionary to hold levels: level_name: {'hint': level_hint, 'finish': level_finish, 'table': [chars, chars..]}
        self.levels = {} 
        self.current_level_name = None
        self.filepath = None

    def load_levels(self, filepath):
        try:
            self.levels = self.get_file(filepath)        
            self.filepath = filepath    
            #print(f"Loaded levels from {filepath}")
            if self.levels:
                self.current_level_name = list(self.levels.keys())[0] # Set first level as current
            return True
        except Exception as e:
            print(f"Error loading levels: {e}")
            return False

    def save_levels(self, filepath):
        try:
            formatted_data = self.format_file()
            with open(filepath, 'w') as f:
                f.write(formatted_data)
            #print(f"Saved levels to {filepath}")
            return True
        except Exception as e:
            print(f"Error saving levels: {e}")
            return False

    def get_level_data(self, level_name):
        try:
            level_strings = self.levels.get(level_name)['table']
            level_data = np.array([[c for c in level_string] for level_string in level_strings])
            return level_data
        except (KeyError, TypeError):
            return None

    def add_level(self, level_name, level_data=None):
        if level_name not in self.levels:
            if level_data is None:
                # Create an empty 20x15 level by default
                level_data = [[' ' for _ in range(20)] for _ in range(15)]
            self.levels[level_name] = level_data
            self.current_level_name = level_name
            print(f"Added new level: {level_name}")
        else:
            print(f"Level '{level_name}' already exists.")

    def delete_level(self, level_name):
        if level_name in self.levels:
            del self.levels[level_name]
            print(f"Deleted level: {level_name}")
            if self.current_level_name == level_name:
                self.current_level_name = list(self.levels.keys())[0] if self.levels else None
        else:
            print(f"Level '{level_name}' not found.")

    def get_current_level_text_representation(self):
        if self.current_level_name and self.current_level_name in self.levels:
            return "\n".join(["".join(row) for row in self.levels[self.current_level_name]['table']])
        return "No level selected or level data empty."            

    def get_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
          game_data = f.read().splitlines()
        no_levels = int(game_data[0])
        level_dict = defaultdict()
        index = 1
        for level in range(no_levels):
          level_name, level_hint, level_finish  = game_data[index: index + 3]
          index += 3
          row = game_data[index] # we know this is table data
          table = [row]
          index += 1
          # assume that level name does NOT have length of data
          while len(game_data[index]) == len(row):
             table.append(game_data[index])
             index += 1
             if index == len(game_data):
                break
                
          level_dict[level_name] = {'hint': level_hint, 'finish': level_finish, 'table': table}
        return level_dict
          
    def format_file(self):
       no_sections = len(self.levels)
       file_contents = [f'{no_sections}']
       for name, data in self.levels.items():
          file_contents.append(f'{name}')
          file_contents.append(f'{data["hint"]}')
          file_contents.append(f'{data["finish"]}')
          file_contents.extend([f'{line}' for line in data['table']])
       return '\n'.join(file_contents)

if __name__ == '__main__':
  level = LevelManager()
  level.load_levels('DEFAULT.KYE')
  print(level.levels)
  level.save_levels('temp.txt')
