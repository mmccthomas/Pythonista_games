# proof of concept module to roll a ball around a tilting
# table with correct physics
# definitely Work in Progress
import motion
from time import sleep
from scene import *
import math
from ui import Path
import numpy as np
GRID_POS = (10,10)
GRID_SIZE = 39
ROWS = 26
COLUMNS = 35
FRAME = .03
MAX_X = (COLUMNS - 1) * GRID_SIZE
MAX_Y = (ROWS - 1) * GRID_SIZE
M = 0.001
G = 9.81

def hitTest(x1,y1,size1,x2,y2,size2,output=0):
	if x1+size1>=x2 and x1<=x2+size2:
				if y1+size1>=y2 and y1<=y2+size2:
					output=1
	if output:
		#Calculate origins
		ox1=x1+(size1/2)
		oy1=y1+(size1/2)
		ox2=x2+size2/2
		oy2=y2+size2/2
		#Difference between origins to locate the direction
		difx=ox1-ox2
		dify=oy1-oy2
		if difx<=0: output1=1#hit from r
		else: output1=2#hit from l
		if dify<=0: output2=1#hit from t
		else: output2=2#hit from b
		#check which is most important
		if dify<0:dify*=-1
		if difx<0:difx*=-1
		if difx>dify: output=output1
		else: output=output2+2
	return output
	
def build_background_grid():
  parent = Node()

  # Parameters to pass to the creation of ShapeNode
  params = {
    "path": Path.rect(0, 0, GRID_SIZE, GRID_SIZE * ROWS),
    "fill_color": "clear",
    "stroke_color": "lightgrey"
  }
  
  anchor = Vector2(0, 0)
  
  # Building the columns
  for i in range(COLUMNS):
    n = ShapeNode(**params)
    pos = Vector2(i*GRID_SIZE, 0)
    
    n.position = pos
    n.anchor_point = anchor
    
    parent.add_child(n)
  
  # Building the rows
  params["path"] = Path.rect(0, 0, GRID_SIZE * COLUMNS, GRID_SIZE)
  for i in range(ROWS):
    n = ShapeNode(**params)
    pos = Vector2(0, i*GRID_SIZE)
    
    n.position = pos
    n.anchor_point = anchor
    
    parent.add_child(n)
    
  return parent
  
class Roll(Scene):
  def setup(self):
    self.background_color = 'white'
  
    # Root node for all game elements
    self.game_field = Node(parent=self, position=GRID_POS)
    
    # Add the background grid
    self.bg_grid = build_background_grid()
    self.game_field.add_child(self.bg_grid)
    
    x,y,self.w, self.h = self.bg_grid.bbox
    #self.xa_label = LabelNode('0', font=('Avenir Next', 20),
    #                              position=(50, self.h-50), color='black',
    #                              parent=self.game_field)
    #self.ya_label = LabelNode('0', font=('Avenir Next', 20), position=(300,self.h-100), color='black', parent=self.game_field)
    #self.c_label = LabelNode('0', font=('Avenir Next', 20),
    #                              position=(250, self.h-50), color='black',
    #                              parent=self.game_field)
    #self.r_label = LabelNode('0', font=('Avenir Next', 20), position=(350,self.h-50), color='black', parent=self.game_field)
    #self.block_label = LabelNode('0', font=('Avenir Next', 20), position=(600,self.h-50), color='black', z_position=500, parent=self.game_field)
    
    self.ball=SpriteNode(Texture('emj:Black_Circle'), 
                         size=(GRID_SIZE,GRID_SIZE),
                         parent=self.game_field)
    
    self.sx = self.w / 2
    self.sy = self.h / 4
    self.ball.position = (self.sx, self.sy)
    self.ball_timer = FRAME
    self.xu = 0.0
    self.yu = 0.0
    self.construct_walls('maze1.txt')
    motion.start_updates()
    
  def construct_walls(self, textfile):
        params = {
                  "path": Path.rect(0, 0, GRID_SIZE, GRID_SIZE),
                  "fill_color": "cyan",
                  "stroke_color": "black"
                  }
        self.data =  np.loadtxt(textfile, dtype='<U1')
        edges = {'3': '┃', '1': '━', '2': '┓', '0': '┏', '4': '┗', '5': '┛', '=': '━'}
        wall_coords = np.argwhere(np.char.isnumeric(self.data))
        self.walls = [ShapeNode(**params, 
                                position=(col*GRID_SIZE, (ROWS - row) * GRID_SIZE), 
                                anchor_point=(0.5, 0.5),
                                parent=self.game_field) 
                      for row, col in wall_coords]

  def check_x_collisions(self):
     # check for collision with vertical wall
     ball_next = self.sx + self.x_incr, self.sy
     ball_next_extent = Rect(self.sx + self.x_incr-GRID_SIZE/2, self.sy, GRID_SIZE, GRID_SIZE)
     for wall in self.walls:
       # will next frame intersect with same accn?
       if ball_next_extent.intersects(wall.bbox):                  
         if self.xu >= 0: # left
           self.sx = max(self.sx, wall.bbox.x-GRID_SIZE)           
         else:
           self.sx = min(self.sx, wall.bbox.x+wall.bbox.w+GRID_SIZE/2)
         self.x_incr = 0
         self.xu = 0
 
  def check_y_collisions(self):
       # check for collision with horizontal wall
       ball_next = self.sx, self.sy + self.y_incr
       ball_next_extent = Rect(self.sx, self.sy+self.y_incr-GRID_SIZE/2, GRID_SIZE, GRID_SIZE)
       for wall in self.walls:
         # will next frame intersect with same accn?
         if ball_next_extent.intersects(wall.bbox):                  
           if self.yu >= 0: # top
             self.sy = max(self.sy, wall.bbox.y-GRID_SIZE)           
           else:
             self.sy = min(self.sy, wall.bbox.y+wall.bbox.h+GRID_SIZE/2)
           self.y_incr = 0
           self.yu = 0       
    
  def clip_boundary(self):    
      self.sx = max(GRID_SIZE, min(self.sx, MAX_X))
      self.sy = max(GRID_SIZE,min(self.sy, MAX_Y))
              
  def update(self):
      self.ball_timer -= self.dt
      if self.ball_timer <= 0:
        self.ball_timer = FRAME
        y,x,z = motion.get_attitude()
        # f = ma and f = x*sin(x/2/math.pi)*9.81
        # v = u + at
        # s = ut + 1/2 att
        self.xa = G * math.sin(-x / (2 * math.pi)) / M        
        self.xu = self.xu + self.xa * FRAME        
        self.x_incr = self.xu * FRAME + 0.5 * self.xa * FRAME * FRAME              
        self.check_x_collisions()
        self.sx = self.sx + self.x_incr      
        
        self.ya = G * math.sin(-y / (2 * math.pi)) / M        
        self.yu = self.yu + self.ya * FRAME         
        self.y_incr = self.yu * FRAME + 0.5 * self.ya * FRAME * FRAME  
        self.check_y_collisions()
        self.sy = self.sy + self.y_incr     
             
        self.clip_boundary()               
        self.ball.position = (self.sx, self.sy)
                    
  
      
if __name__ == '__main__':
  run(Roll(), LANDSCAPE)
  #motion.stop_updates()


















