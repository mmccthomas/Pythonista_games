# level_manager.py (Simplified)
# Uses  file format used by Kye
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

def rle(inarray):
  """ run length encoding. Partial credit to R rle function.
  Multi datatype arrays catered for including non Numpy
  returns: tuple (runlengths, startpositions, values) """
  ia = np.asarray(inarray)                # force numpy
  n = len(ia)
  if n == 0:
      return (None, None, None)
  else:
      y = ia[1:] != ia[:-1]               # pairwise unequal (string safe)
      i = np.append(np.where(y), n - 1)   # must include last element posi
      z = np.diff(np.append(-1, i))       # run lengths
      p = np.cumsum(np.append(0, z))[:-1]  # positions
      return (z, p, ia[i])

class LevelManager:
    def __init__(self):
        # Dictionary to hold levels: level_name: {'text1': level_hint, 'text2': level_finish, 'table': [chars, chars..]}
        self.levels = {}
        self.current_level_name = None
        self.filepath = None
        self.file_modified = False
        self.error_text = None

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
                self.current_level_name = list(self.levels.keys())[0]  # Set first level as current
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
            with open(filepath, 'w') as f:
                f.write(formatted_data)
            # print(f"Saved levels to {filepath}")
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
            self.file_modified = True
        else:
            print(f"Level '{level_name}' already exists.")

    def delete_level(self, level_name):
        if level_name in self.levels:
            del self.levels[level_name]
            print(f"Deleted level: {level_name}")
            if self.current_level_name == level_name:
                self.current_level_name = list(self.levels.keys())[0] if self.levels else None
            self.file_modified = True
        else:
            print(f"Level '{level_name}' not found.")

    def get_current_level_text_representation(self):
        if self.current_level_name and self.current_level_name in self.levels:
            return "\n".join(["".join(row) for row in self.levels[self.current_level_name]['table']])
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
          
    def format_file(self):
       no_sections = len(self.levels)
       file_contents = [f'{no_sections}']
       for name, data in self.levels.items():
          file_contents.append(f'{name}')
          file_contents.append(f'{data["text1"]}')
          file_contents.append(f'{data["text2"]}')
          file_contents.extend([f'{"".join(line)}' for line in data["table"]])
          
       file_contents.append('\n')
       
       return '\n'.join(file_contents)


if __name__ == '__main__':
  level = LevelManager()
  f= '/private/var/mobile/Containers/Data/Application/24BEC035-C28E-496A-A41A-CEC669E05513/Documents/Pythonista_games/Kye/levels/cmt.KYE'
  level.load_levels(f)
  #print(level.levels)
  new_data=  {'text1': 'Stay out of the road.', 'text2': "If you're this good - design some new levels.", 'table': ['555555555555555555555555555555', '5K   5553  1553 15c5         5', '5   c              155e5555e55', '55e55 7a55e5555e5a        c  5', '5   5 5           a55c5ll    5', '5   5 a               5U 5  75', '5   5 15e55555e55 759 5  e  55', '5   5           a 5 5 5  5  15', '5   1c55e555e55 5 e 5 5555   5', '5             5d5 5 e 1c55   5', '5555e55e555e555 5 5 a    5   5', '5c              5 e 159  5  75', '55 75e5555e5555a5 5   e  e  55', '55 c              5   5  5  15', '55 5 45e555555e55a55e53  5   5', '55 5      >             c5   5', '53 1c55e55555e55555e55  Ru v 5', '5            r            c5 5', '55c555559   75555559   75555*5', '555555555555555555555555555555']}
  level.add_level('ABC', new_data)
  level.save_levels('temp.txt')
