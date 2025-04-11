from scene import Node, ShapeNode, Scene, Texture, SpriteNode
import ui
GRID_POS = (100, 85)
import io


def pil2ui(imgIn):
  with io.BytesIO() as bIO:
    imgIn.save(bIO, 'PNG')
    imgOut = ui.Image.from_data(bIO.getvalue())
  del bIO
  return imgOut
  
  
class Surface(Scene):
  def __init__(self, size=None):
    Scene.__init__(self)
    self.game_field = Node(parent=self, position=GRID_POS)
    
  def convert(self):
    return self
  def fill(self, color):
    pass
    
  def blit(self, sprite, pos):
    uimage = pil2ui(sprite)
    txture = Texture(uimage)
    self.game_field.add_child(SpriteNode(txture, position=pos))
    
  def set_mode(self,size, x, y):
    return self
  def update(self):
    pass
  
class Draw():
  def __init__(self, parent):
    self.parent = parent
    
  def circle(self, screen, color, point, radius):
    ShapeNode(ui.Path.rounded_rect(point[0], point[1], 2*radius, 2*radius, radius), fill_color=color, parent=self.parent)
    




