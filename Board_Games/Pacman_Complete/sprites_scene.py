import pygame
from constants import *
import numpy as np
from animation import Animator
from scene import *
from PIL import Image
import io

BASETILEWIDTH = 16
BASETILEHEIGHT = 16
DEATH = 5
def convert_image(filepath):
  img = Image.open(filepath)
  data = np.array(img)
  r, g, b, a = data.T
  back_color = data[0][0][:3] #[r,g,b]

class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, sprite, row=0, col=0, **kwargs):
    #for k, v in kwargs.items():
    #  setattr(self, k, v)
    SpriteNode.__init__(self, sprite, **kwargs)
    self.sizew = TILEWIDTH
    self.sizeh = TILEHEIGHT
    self.anchor_point = (0.5, 0.5)
    self.set_pos(col, row)
  
  def set_pos(self, col=0, row=0):
    """
    Sets the position of the tile in the grid.
    """
    if col < 0:
      raise ValueError(f"col={col} is less than 0")
    
    if row < 0:
      raise ValueError(f"row={row} is less than 0")
    
    self.col = col
    self.row = row
    
    pos = Vector2()
    pos.x = col * self.sizew
    pos.y = (NROWS - 1 - row) * self.sizeh
    self.position = pos
      
class Spritesheet(object):
    def __init__(self):
        #convert_image("spritesheet_alpha.png")
        self.sheet = Texture(ui.Image.named("spritesheet_alpha.png"), alpha=1)
        self.image_dict = None
        #transcolor = self.sheet.get_at((0,0))
        #self.sheet.set_colorkey(transcolor)
        #width = int(self.sheet.get_width() / BASETILEWIDTH * TILEWIDTH)
        #height = int(self.sheet.get_height() / BASETILEHEIGHT * TILEHEIGHT)
        #self.sheet = pygame.transform.scale(self.sheet, (width, height))
        if self.image_dict is None:
           self.image_dict = self.split_images()
                 
    def split_images(self):
       # split spritesheet into individual tiles in a dictionary
       # use x,y index as key
        w, h = self.sheet.size
        scale = 2 # multiple of tilesize
        image_dict = {}
        for y in range(7):
          for x in range(11):
            yi = (6 - y) * scale
            xi = x * scale
            x1 = x * 16 * scale / w
            y1 = y * 16 * scale / h
            w1 = 16 * scale / w
            h1 = 16 * scale / h
            t = self.sheet.subtexture(Rect(x1, y1, w1, h1))
            image_dict.setdefault((xi,yi), t)
        return image_dict
        
    def getImage(self, x, y, width, height):
        return self.image_dict[(x, y)]


class PacmanSprites(Spritesheet):
    def __init__(self, entity):
        Spritesheet.__init__(self)
        self.entity = entity
        self.entity.image = self.getStartImage()         
        self.animations = {}
        self.defineAnimations()
        self.stopimage = (8, 0)

    def defineAnimations(self):
        self.animations[LEFT] = Animator(((8,0), (0, 0), (0, 2), (0, 0)))
        self.animations[RIGHT] = Animator(((10,0), (2, 0), (2, 2), (2, 0)))
        self.animations[UP] = Animator(((10,2), (6, 0), (6, 2), (6, 0)))
        self.animations[DOWN] = Animator(((8,2), (4, 0), (4, 2), (4, 0)))
        self.animations[DEATH] = Animator(((0, 12), (2, 12), (4, 12), (6, 12), (8, 12), (10, 12), (12, 12), (14, 12), (16, 12), (18, 12), (20, 12)), speed=6, loop=False)

    def update(self, dt):
        if self.entity.alive == True:
            if self.entity.direction == LEFT:
                self.entity.image = self.getImage(*self.animations[LEFT].update(dt))
                self.stopimage = (8, 0)
            elif self.entity.direction == RIGHT:
                self.entity.image = self.getImage(*self.animations[RIGHT].update(dt))
                self.stopimage = (10, 0)
            elif self.entity.direction == DOWN:
                self.entity.image = self.getImage(*self.animations[DOWN].update(dt))
                self.stopimage = (8, 2)
            elif self.entity.direction == UP:
                self.entity.image = self.getImage(*self.animations[UP].update(dt))
                self.stopimage = (10, 2)
            elif self.entity.direction == STOP:
                self.entity.image = self.getImage(*self.stopimage)
        else:
            self.entity.image = self.getImage(*self.animations[DEATH].update(dt))

    def reset(self):
        for key in list(self.animations.keys()):
            self.animations[key].reset()

    def getStartImage(self):
        return self.getImage(8, 0)

    def getImage(self, x, y):
        return Spritesheet.getImage(self, x, y, 2*TILEWIDTH, 2*TILEHEIGHT)


class GhostSprites(Spritesheet):
    def __init__(self, entity):
        Spritesheet.__init__(self)
        self.x = {BLINKY:0, PINKY:2, INKY:4, CLYDE:6}
        self.entity = entity
        self.entity.image = self.getStartImage()

    def update(self, dt):
        x = self.x[self.entity.name]
        if self.entity.mode.current in [SCATTER, CHASE]:
            if self.entity.direction == LEFT:
                self.entity.image = self.getImage(x, 8)
            elif self.entity.direction == RIGHT:
                self.entity.image = self.getImage(x, 10)
            elif self.entity.direction == DOWN:
                self.entity.image = self.getImage(x, 6)
            elif self.entity.direction == UP:
                self.entity.image = self.getImage(x, 4)
        elif self.entity.mode.current == FREIGHT:
            self.entity.image = self.getImage(10, 4)
        elif self.entity.mode.current == SPAWN:
            if self.entity.direction == LEFT:
                self.entity.image = self.getImage(8, 8)
            elif self.entity.direction == RIGHT:
                self.entity.image = self.getImage(8, 10)
            elif self.entity.direction == DOWN:
                self.entity.image = self.getImage(8, 6)
            elif self.entity.direction == UP:
                self.entity.image = self.getImage(8, 4)
               
    def getStartImage(self):
        return self.getImage(self.x[self.entity.name], 4)

    def getImage(self, x, y):
        return Spritesheet.getImage(self, x, y, 2*TILEWIDTH, 2*TILEHEIGHT)


class FruitSprites(Spritesheet):
    def __init__(self, entity, level):
        Spritesheet.__init__(self)
        self.entity = entity
        self.fruits = {0:(16,8), 1:(18,8), 2:(20,8), 3:(16,10), 4:(18,10), 5:(20,10)}
        self.entity.image = self.getStartImage(level % len(self.fruits))

    def getStartImage(self, key):
        return self.getImage(*self.fruits[key])

    def getImage(self, x, y):
        return Spritesheet.getImage(self, x, y, 2*TILEWIDTH, 2*TILEHEIGHT)
     
    
class LifeSprites(Spritesheet):
    def __init__(self, numlives):
        Spritesheet.__init__(self)
        self.resetLives(numlives)

    def removeImage(self):
        if len(self.images) > 0:
            self.images.pop(0)

    def resetLives(self, numlives):
        self.images = []
        for i in range(numlives):
            self.images.append(self.getImage(0,0))

    def getImage(self, x, y):
        return Spritesheet.getImage(self, x, y, 4*TILEWIDTH, 4*TILEHEIGHT)
        
    def render(self, screen):
      for i in range(len(self.images)):
            x = self.images[i].size[0] * (i * 2 + 1)
            y = -50 + self.images[i].size[1]
            SpriteNode(self.images[i], position=(x, y), scale=4, parent=screen)


class MazeSprites(Spritesheet):
    def __init__(self, mazefile, rotfile, screen):
        Spritesheet.__init__(self)
        self.data = self.readMazeFile(mazefile)
        self.rotdata = self.readMazeFile(rotfile)
        self.screen = screen
        
    def getImage(self, x, y):
        return Spritesheet.getImage(self, x, y, TILEWIDTH, TILEHEIGHT)

    def readMazeFile(self, mazefile):
        return np.loadtxt(mazefile, dtype='<U1')

    def constructBackground(self, background, y):
        edges = {'3': '┃', '1': '━', '2': '┓', '0': '┏', '4': '┗', '5': '┛', '=': '━'}
        tile_location = '../../gui/tileblocks/'
        ymax, xmax = self.data.shape
        for row in range(ymax):
            for col in range(xmax):
                if self.data[row][col].isdigit():
                    tile_pic = tile_location + edges[self.data[row][col]] + '_32m.png'
                    Tile(Texture(ui.Image.named(tile_pic)), row, col, 
                         size=(TILEWIDTH, TILEHEIGHT),
                         color='#737373', 
                         parent=self.screen)
                elif self.data[row][col] == '=':
                    Tile(Texture(ui.Image.named(tile_pic)), row, col, 
                         size=(TILEWIDTH, TILEHEIGHT),
                         color='white', 
                         parent=self.screen)

        return background

    def rotate(self, sprite, value):
        return pygame.transform.rotate(sprite, value*90)






