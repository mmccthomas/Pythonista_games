#    Kye - classic puzzle game
#    Copyright (C) 2005, 2006, 2007, 2010 Colin Phipps <cph@moria.org.uk>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

"""kye.common - Common utility functions and classes.
Exposed constants:
xsize, ysize - size of the game playing area.
version - version number of this release of the game.
kyepaths - the list of paths that we will try for opening levels
given on the command line,
and for searching for tilesets.
image_dict
"""

from os.path import exists, join, isfile
from PIL import Image
import ui
import codecs
import numpy as np
from scene import Texture, Rect
from os import listdir
import zipfile

xsize = 30
ysize = 20
tsize = 16
interval = 0.1  # 0.067
IMAGE_NAME = 'image.png'


def device_size():
	w, h = ui.get_screen_size()
	device = None
	if w > 1200 and h > 1000:
		device = 'ipad13_landscape'
	elif w > 1000:
		device = 'ipad_landscape'
	elif w > 800 and h > 1000:
		device = 'ipad_portrait'
	elif w > 800 and h < 400:
		device = 'iphone_landscape'
	elif w < 400 and h > 800:
		device = 'iphone_portrait'
	else:
		device = None
	return device


version = "1.0"

kyepaths = ["levels", "more_levels"]


def combine_images(columns, space, images):
    """combines all tiles into one"""
    rows = len(images) // columns
    if len(images) % columns:
        rows += 1
    width_max = max([Image.open(image).width for image in images])
    height_max = max([Image.open(image).height for image in images])
    background_width = width_max*columns + (space*columns)-space
    background_height = height_max*rows + (space*rows)-space
    background = Image.new('RGBA', (background_width, background_height),
                           (255, 255, 255, 255))
    x = 0
    y = 0
    for i, image in enumerate(images):
        img = Image.open(image)
        x_offset = int((width_max-img.width)/2)
        y_offset = int((height_max-img.height)/2)
        background.paste(img, (x+x_offset, y+y_offset))
        x += width_max + space
        if (i+1) % columns == 0:
            y += height_max + space
            x = 0
    background.save(IMAGE_NAME)


def load_images():
    '''open a single file containing all images
    allow single zip file to get names'''
    try:
       images = sorted(listdir('images'))
    except FileNotFoundError:
        zip = zipfile.ZipFile('images.zip')
        images = zip.namelist()[1:]
        
    # remove any other files
    for i in images:
        if i.split('.')[1] not in ['png', 'gif']:
          images.remove(i)
    if '/' in images[0]:
        images = [i.split('/')[1] for i in images]
    images2 = ['images/' + i for i in images]
    images = [i.split('.')[0] for i in images]
    # combine_images(10,0,images2)

    # combined image
    combined = Texture(ui.Image.named(IMAGE_NAME))
    w, h = combined.size
    # now have images list and image.png
    # 10 x 8 array gap of 0
    image_dict = {}
    for i, image in enumerate(images):
        x = (i % 10) * tsize / w
        y = (7 - int(i / 10)) * tsize / h
        w1 = tsize / w
        h1 = tsize / h
        t = combined.subtexture(Rect(x, y, w1, h1))
        image_dict.setdefault(image, t)
    return image_dict


def tryopen(filename, paths):
    """Returns a reading file handle for filename,
    searching through directories in the supplied paths."""
    if isfile(filename):
        return filename
    else:
        for path in paths:
            if isfile(join(path, filename)):
              return join(path, filename)
  
    raise KGameFormatError("Unable to find file "+filename)


def findfile(filename):
  """Looks for filename, searching a built-in list of directories;
  returns the path where it finds the file.
  for _, dirs, files in os.walk(".")
    for name in dirs:
      print("dir ",name)
      if filename == name:
        return filename
    for file in files:
      print("file ", file)
      if file == name:
        return filename"""
  return 'kye/images'


image_dict = load_images()


class KyeImageDir():
    """Class for retrieving images from a tileset tar.gz."""
    def __init__(self, filename):
        self.tiles = {}
        self.tiles[tilename] = ui.Image.named(filename)

    def get_tile(self, tilename):
        """Returns the image file data for the requested tile."""
        return self.tiles[tilename]

                
class KyeFile():
  """ class to parse kye file"""
  
  def __init__(self, filename):
    self.file_contents = []
    self.file_lines = []  
    # read the while file
    if isinstance(filename, str):
      with codecs.open(filename, "r", "utf-8") as f:
        self.file_contents = f.read()
    else : # file object already open
      self.file_contents = filename.read()
      filename.close()
    try:
    	#stringlist=[x.decode('utf-8') for x in self.file_contents]
    	self.file_lines = self.file_contents.split('\n')
    	self.file_lines =[line.strip() for line in self.file_lines]
    except (Exception) as e:
    	raise (Exception, " decode error in file, strange unicode?")
 
    
    self.level_names = self.get_level_names()
    self.current_level = self.level_names[0]
    self.hint = ''
    self.exitmsg = ''
    self.levelno = 0
    
			
  def get_no_levels(self):
    try:
      return int(self.file_lines[0].strip())
    except (Exception) as e:
      raise KGameFormatError(f'Error {e} in file, no level number found')
    
  def get_level_names(self):
    """ get a list of level names  last one is always empty"""
    try:
      level_names = self.file_lines[1::23][:-1]
      if any([level is None for level in level_names]):
        raise KGameFormatError(f'Error in file, empty level number found')
        return None
      else:
      	self.level_names = level_names
      	return level_names
    except (Exception) as e:
        raise KGameFormatError(f'Error {e} in file, empty level number found')
        return None
    
  def _select_level(self, levelname=None):
    """ return and index to line number containing
    levelname
    if levelname is None try to get from current level
    if that is also None, select first level
    """
    if levelname == '' or levelname is None:
    	levelname = self.current_level
    	
    levelnames = self.get_level_names()
    try:
      # skip first line (no of levels)
      index = self.file_lines.index(levelname, 1)
      self.current_level = levelname
      self.hint = self.file_lines[index + 1]
      self.exitmsg = self.file_lines[index + 2]
      return index
    except (Exception) as e:
     	raise (KyeGameRuntimeError, f'no level {levelname} in file')
     	 
    else:
      self.current_level = None
      return None
  		
  def get_level(self, levelname):
    """ return the gamefield for this level """
    index = self._select_level(levelname)
    if index:
      self.game_field = self.file_lines[index + 3: index +  23]  
      return self.game_field		
    else:
      return None

  def get_next_level(self):
    """ get level name for next level if any """    
    try:
      index = self.level_names.index(self.current_level)
      return self.level_names[index + 1]
    except (IndexError):
      return self.level_names[0]
      
  def get_grid(self, levelname):
    """ return as 20 x 30 single character array"""
    game_field = self.get_level(levelname)
    return np.array([np.fromiter(line, '<U1') for line in game_field])    
  		
  def get_level_number(self):
  	return self.level_names.index(self.current_level) + 1
		
  def find_kye(self):
    """ find kye in gamefield """
    for row, line in enumerate(self.game_field):
      if 'K' in line:
        return (line.index('K'), row)
    return None   	
  	
class KyeGameRuntimeError(Exception):
  def __init__(self, message):
    print(message)

class KGameFormatError(Exception):
    def __init__(self, message):
      print(message)   
    
if __name__ == "__main__":
	#a= KyeFile('levels/intro.kye')
	#print(a.get_no_levels())
	#print(a.get_level_names())
	#print(a.get_level('LOGO'))
	#print(a.get_level('PACMAN'))
	#print(a.find_kye())
	# a troublesome file
	a = KyeFile('levels/Original.kye')
	print(a.get_grid('19'))
	print(a.get_next_level())
	print(a.get_grid('20'))
	#print(a.get_next_level())
	
