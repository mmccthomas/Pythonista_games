import ui
from PIL import Image
from scene import *

def load(spritename):
  image = Image.open(spritename)
  return Sprite_image(image)

class Sprite_image(Image.Image):
  def __init__(self, image):
    self.image = image
    self.clip = (0,0,16, 16)
    
  def convert(self):
    return self
    
  def get_at(self, coord):
    return 0
    
  def set_colorkey(self, transcolor):
    return 0
    
  def get_width(self):
      return self.image.width
      
  def get_height(self):
      return self.image.height
      
  def set_clip(self, rectangle):
      self.clip = rectangle
      
  def get_clip(self):
    return self.clip
    
  def subsurface(self, clip):
    #get rectangular section of image

    # The crop method from the Image module takes four coordinates as input.
    # The right can also be represented as (left+width)
    # and lower can be represented as (upper+height).
    x,y,w,h = clip
    crop_spec = (x,y, x+w, y+h)
    img = self.image.crop(crop_spec)
    return Sprite_image(img)
  


