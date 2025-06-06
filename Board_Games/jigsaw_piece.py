import ui
from math import sin, cos, pi, radians
from scene import *
import numpy as np
from collections import namedtuple

class Piece():
   def __init__(self, shape_str, cell_size=100, fill_color='red'):
     self.X = cell_size
     self.R = self.X/6 
     self.off = 0.8   
     self.starts = [(0, 0), (self.X, 0), (self.X, self.X), (0, self.X)]
     self.lengths = [Size(1, 0), Size(0, 1), Size(-1, 0), Size(0, -1)]
     self.types = {'S': self.straight, 'O': self.outie, 'I': self.innie,
                   '0': self.outie, '1': self.innie}
     # all possible pieces
     self.pieces = {0: 'SSII', 1: 'SSIO', 2: 'SSOI', 3: 'SSOO', 4: 'SIIS', 
                    5: 'SIII', 6: 'SIIO', 7: 'SIOS', 8: 'SIOI', 9: 'SIOO', 
                    10: 'SOIS', 11: 'SOII', 12: 'SOIO', 13: 'SOOS', 14: 'SOOI', 
                    15: 'SOOO', 16: 'ISSI', 17: 'ISSO', 18: 'ISII', 19: 'ISIO', 
                    20: 'ISOI', 21: 'ISOO', 22: 'IISS', 23: 'IISI', 24: 'IISO', 
                    25: 'IIIS', 26: 'IIII', 27: 'IIIO', 28: 'IIOS', 29: 'IIOI', 
                    30: 'IIOO', 31: 'IOSS', 32: 'IOSI', 33: 'IOSO', 34: 'IOIS', 
                    35: 'IOII', 36: 'IOIO', 37: 'IOOS', 38: 'IOOI', 39: 'IOOO', 
                    40: 'OSSI', 41: 'OSSO', 42: 'OSII', 43: 'OSIO', 44: 'OSOI', 
                    45: 'OSOO', 46: 'OISS', 47: 'OISI', 48: 'OISO', 49: 'OIIS', 
                    50: 'OIII', 51: 'OIIO', 52: 'OIOS', 53: 'OIOI', 54: 'OIOO', 
                    55: 'OOSS', 56: 'OOSI', 57: 'OOSO', 58: 'OOIS', 59: 'OOII', 
                    60: 'OOIO', 61: 'OOOS', 62: 'OOOI', 63: 'OOOO'}
     self.shape_str = shape_str
     Shape = namedtuple('Shape', ['N', 'E', 'S', 'W'])
     self.t = Shape(*shape_str)
     self.path = self.create_path(self.shape_str)
     self.fill_color = fill_color
     self.shape = shape = ShapeNode(path=self.path, stroke_color='black', 
                                    fill_color=self.fill_color)
     self.origin = Point(0, 0)
     self.get_origin()
   
     self.id = 0
     self.edge_top =  self.t.N
     self.edge_right = self.t.E
     self.edge_bottom = self.t.S
     self.edge_left = self.t.W
     self.row = 0
     self.col = 0
     
   def create_path(self, type_str='SOIS', start=(0,0)):
     start= Point(*start)     
     ui.set_color('red')
     path = ui.Path()  
     path.line_width = 2    
     path.line_join_style = ui.LINE_JOIN_ROUND
     path.move_to(0,0)
     for dir, (type_, st) in enumerate(zip(type_str, self.starts)):               
        self.types[type_](path, start+st, rotation=dir*90)  
     path.close()     
     path.fill()          
     return path 
   
   def get_origin(self):
       #  compute the coordinate of the centre of the box relative to 
       # centre of bounding box
       bbox = self.path.bounds
       oversizex = (bbox.w - self.X)/2
       oversizey = (bbox.h - self.X)/2
       self.origin = Point(0,0)
       # all Innie or side
       if (math.isclose(oversizex, 0, abs_tol=1e-3) and
            math.isclose(oversizey, 0, abs_tol=1e-3)):
              self.origin += (0,0)
       # Outie on left, right or both
       elif math.isclose(oversizey, 0, abs_tol=1e-3):
           if self.t.E == 'O' and self.t.W == 'O':
               self.origin += (0, 0)
           elif self.t.E != 'O' and self.t.W == 'O':  
               self.origin += (oversizex, 0)
           else:
               self.origin += (-oversizex, 0)
       # Outie on top, bottom or both 
       elif math.isclose(oversizex, 0, abs_tol=1e-3):
           if self.t.N == 'O' and self.t.S == 'O':
               self.origin += (0, 0)
           elif self.t.N != 'O' and self.t.S == 'O':  
               self.origin = (0, oversizey)
           else:
               self.origin += (0, -oversizey)
       # outie on two sides  
       else:
           if self.t.N == 'O' and self.t.S == 'O':
               self.origin += (0, 0)
           elif self.t.N != 'O' and self.t.S == 'O':  
               self.origin += (0, oversizey)
           else:
               self.origin += (0, -oversizey)
           if self.t.E == 'O' and self.t.W == 'O':
               self.origin += (0, 0)
           elif self.t.E != 'O' and self.t.W == 'O':  
               self.origin += (oversizex, 0)
           else:
               self.origin += (-oversizex, 0)              
   
   def outie(self, path, start, rotation=0):
     off = pi/2 + self.off
     L = self.X/2
     x, y = start
     #path.move_to(*start)
     match rotation:
       case 0:
           cx, cy = x + L, y - self.R*sin(off-pi/2)
           path.line_to(x + L - self.R*cos(off-pi/2), y)                        
           path.add_arc(cx, cy, self.R, off, pi-off)
           path.line_to(x + self.X, y)
           pass
       case 90:
           cx, cy = x + self.R*cos(pi/2-self.off), y + L         
           path.line_to(x, y + L - self.R*sin(pi-self.off))
           path.add_arc(cx, cy, self.R, pi/2 +off, off)
           path.line_to(x, y + self.X)
           pass
       case 180:
           cx, cy = x - L, y + self.R*sin(off-pi/2)       
           path.line_to(x  -  L +self.R*cos(off-pi), y)
           path.add_arc(cx, cy, self.R, -pi+off, -off)
           path.line_to(x -self.X, y)
           pass
       case 270:
           cx, cy = x - self.R*cos(pi/2-self.off), y - L         
           path.line_to(x, y -L + self.R*sin(pi-self.off))
           path.add_arc(cx, cy, self.R, pi - off, pi+off)
           path.line_to(x,  y-self.X)
           pass
     return path
     
   def innie(self, path, start, rotation=0):
     off = pi/2 + self.off
     L = self.X/2
     x, y = start
     match rotation:
       case 0:
           cx, cy = x + L, y + self.R*sin(off-pi/2)  
           path.line_to(x + L - self.R*cos(off-pi/2), y)                          
           path.add_arc(cx, cy, self.R, -off, pi+off, False)
           path.line_to(x + self.X, y)
           pass
       case 90:
           cx, cy = x - self.R*cos(pi/2-self.off), y + L        
           path.line_to(x, y + L - self.R*sin(pi-self.off))
           path.add_arc(cx, cy, self.R, -off+pi/2, off-pi/2, False)
           path.line_to(x, y + self.X)
           pass
       case 180:
           cx, cy = x - L, y - self.R*sin(off-pi/2)        
           path.line_to(x  -  L +self.R*cos(off-pi), y)
           path.add_arc(cx, cy, self.R, pi-off, off, False)
           path.line_to(x -self.X, y)
           pass
       case 270:
           cx, cy = x + self.R*cos(pi/2-self.off), y - L              
           path.line_to(x, y -L + self.R*sin(pi-self.off))
           path.add_arc(cx, cy, self.R,  off  , pi/2 + off,  False)
           path.line_to(x,  y-self.X)
           pass
     return path
     
   def straight(self, path, start, rotation=0):
   
     path.line_to(*(start + self.lengths[rotation//90]*self.X))
     return path
     
   
