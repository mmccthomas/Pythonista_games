# this file should be copied to Python Modules/site_packages(user)
#
import os
import sys
# find the path to current file
# back up until Pythonista_games
# add subdirectories to sys path

def add_paths(filename):
    current = os.path.dirname(os.path.realpath(filename))
    path_item = current
    while not path_item.endswith('Pythonista_games') and not path_item.endswith('Documents'):
        path_item = os.path.dirname(path_item)
    paths = []
    try:
        paths.append(path_item)    
        for f in ['gui', 'Board_Games', 'Word_Games', 'Card_Games']:
        	  paths.append(path_item + '/' + f)
        [sys.path.append(d) for d in paths]
        return paths
        #dirs = [d.path for d in  os.scandir(path_item) if d.is_dir()]

    except (Exception) as e:
      print(e)
      
if __name__ == '__main__':
    add_paths(__file__)

