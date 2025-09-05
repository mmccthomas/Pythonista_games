# This file contains configuration of sprites for
# a new game.
# require variables image_dict and lookup to be generated.
# lookup needs char : (spritename, ) at least.
# other parameters are project specific
# format of .kye file
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
5 5>>B               b  B<<5 5()
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
# character to icon dictionary
# character (class string, image_name)

from PIL import Image
import io
import base_path

base_path.add_paths(__file__)
import zipfile
from collections import Counter
# if called from game_editor
#import Game_editor.jumping_game as jumping_game

class Config():

    def __init__(self):
        # can load multiple zip files.
        # to do this, the sprite sizes must be compatible
        zip_files = {
            'platformer deluxe': 'kenney_platformer-art-deluxe.zip',
            #'minimap': 'kenney_minimap-pack.zip'
            'physics': 'kenney_physics-assets.zip'
        }
        self.image_dict = {}
        self.flat_dict = {}
        file_list = []
        for zip_file_name, zip_file_path in zip_files.items():
            image_dict, files = self.create_dict_from_zip(zip_file_path)
            self.image_dict[zip_file_name] = image_dict
            file_list.extend(files)

        names = [file_name.split('/')[-1] for file_name in file_list]
        counter = Counter(names)
        unique_names = [
            k for k, v in counter.items() if v == 1 and k.endswith('.png')
        ]
        self.lookup = {
            chr(9472 + i): unique_name
            for i, unique_name in enumerate(unique_names)
        }
        self.run_module = 'Game_editor.jumping_game'

    def get_image(self, zip_file, imagename):
        with zip_file.open(imagename) as f:
            image_stream = io.BytesIO(f.read())
            # Open the image data with PIL
            try:
                return Image.open(image_stream)
            except IOError:
                return None

    def remove_empty_dicts(self, d):
        """
    Recursively removes empty dictionaries from a nested dictionary.
    """
        if not isinstance(d, dict):
            return d

        # Iterate over a copy of the items to allow modification of the original dict
        for key, value in list(d.items()):
            if isinstance(value, dict):
                # Recursively call the function on the nested dictionary
                self.remove_empty_dicts(value)
                # After the call, check if the nested dictionary is now empty
                if not value:
                    del d[key]
        return d

    def create_dict_from_zip(self, zip_file_path=None):
        """
      Given a zip file path, this function produces a Python dictionary 
      with the same directory and file structure.
  
      Args:
          zip_file_path (str): The path to the zip file.
  
      Returns:
          dict: A dictionary representing the file structure of the zip file,
                or None if the file cannot be opened.
      """

        def contains(exc_list):
            for exclude in exc_list:
                if exclude in component:
                    return True
            return False

        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                root_dict = {}
                all_names = []

                for path in file_list:
                    # Split the path into components
                    components = path.split('/')

                    # Get a reference to the current level of the dictionary
                    current_dict = root_dict

                    # Iterate through the components to build the nested dictionary
                    for i, component in enumerate(components):
                        if not component:
                            continue  # Skip empty strings from split, e.g., 'dir/'

                        # If it's the last component, it's a file or an empty directory
                        if i == len(components) - 1:
                            if path.endswith('/'):  # It's an empty directory
                                if component not in current_dict:

                                    current_dict[component] = {}
                            else:  # It's a file
                                if component in [
                                        'Tilemap', 'Vector', 'license.txt',
                                        'sample.png', 'preview.png',
                                        'Thumbs.db', 'sheet.png'
                                ]:
                                    continue
                                if contains([
                                        '.url', 'tilemap', 'spritesheet',
                                        'txt', '.svg', '.swf', 'Preview',
                                        'Sample'
                                ]):
                                    continue
                                # its a duplicate
                                while component in all_names:
                                    component = '_' + component

                                all_names.append(component)
                                current_dict[component] = self.get_image(
                                    zip_ref,
                                    path)  # Use None to represent a file
                                self.flat_dict[component] = current_dict[component]
                        else:
                            # It's a directory, so create a new dictionary if it doesn't exist
                            if component not in current_dict:
                                if contains(
                                    ['Tilemap', 'Vector', 'Spritesheet']):
                                    continue
                                current_dict[component] = {}

                            # Move to the next level of the dictionary
                            current_dict = current_dict[component]
                # remove empty dicts

                root_dict = self.remove_empty_dicts(root_dict)
                return root_dict, all_names
        except zipfile.BadZipFile:
            print(f"Error: {zip_file_path} is not a valid zip file.")
            return None
        except FileNotFoundError:
            print(f"Error: The file {zip_file_path} was not found.")
            return None

    def print_tree(self, d, indent="", is_last=True):
        """
      Recursively prints a dictionary to show its tree structure.
  
      Args:
          d (dict): The dictionary to print.
          indent (str): The current indentation string.
          is_last (bool): True if the current item is the last one in its parent.
      """
        # Get the keys and sort them for consistent output
        keys = list(d.keys())
        keys.sort()
        space = '    '
        branch = '│   '
        tee = '├── '
        last = '└── '
        for i, key in enumerate(keys):
            is_last_item = (i == len(keys) - 1)

            # Determine the prefix for the current item
            prefix = last if is_last_item else tee
            print(indent + prefix + key)

            # Calculate the new indentation for the next level
            next_indent = indent + (space if is_last_item else branch)

            value = d[key]

            # If the value is a dictionary, recurse
            if isinstance(value, dict):
                self.print_tree(value, next_indent, is_last_item)

    #
    def load_images(self):
        # combined image
        zip_file = zipfile.ZipFile('Metal_sprites.zip')
        images = sorted(zip.namelist()[1:])
        # remove any other files
        images = [img for img in images if img.split('.')[1] in ['png', 'gif']]
        image_dict = {}
        for i, imagename in enumerate(images):
            with zip_file.open(imagename) as f:
                image_stream = io.BytesIO(f.read())
                # Open the image data with PIL
                try:
                    img = Image.open(image_stream)
                    image_dict.setdefault(
                        imagename.split('/')[1].split('.')[0], img)
                except IOError:

                    print(
                        f"Warning: Could not open {imagename} as a PIL Image.")

        return image_dict


if __name__ == '__main__':
    config = Config()
    config.print_tree(config.image_dict)

