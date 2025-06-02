"""
To create a 2d tank game for Pythonista, with one tank controlled by AI and the tanks in a maze, we'll need to break this down into several components:
 * Maze Generation: We'll need a way to create a maze. A simple algorithm like Recursive Backtracking can work well.
 * Tank Representation: How to draw the tanks, handle their movement, and rotation.
 * Collision Detection: Tanks need to collide with maze walls and each other.
 * Bullet Mechanics: Firing bullets, their movement, and collision with tanks/walls.
 * AI for Tank: This is the most complex part. The AI tank needs to navigate the maze, find the player, and shoot. A simple state machine or a          basic pathfinding algorithm (like A*) could be used for movement.
 * Game Loop and UI: Pythonista's ui module will be used for rendering, and scene or SpriteKit could be used for more advanced graphics, but for simplicity, we'll stick to ui and direct drawing.
Here's a conceptual outline and some Pythonista-specific code snippets to get you started. This is a significant project, so I'll provide a framework rather than a fully complete, robust game.
""" 

import random
from random import random as rnd
import ui
import io
import math
import random
import time
from types import SimpleNamespace
from copy import copy
from scene import Point, Rect
import console
from time import sleep

from PIL import Image

class Maze:
    """ We'll represent the maze as a 2D grid. Each cell can have walls (top, right, bottom, left)."""
    def __init__(self, width, height, density=0.15):
        self.width = width
        self.height = height
        self.density = density
        self.thickness = 6
        self.grid = [[{'N': True, 'E': True, 'S': True, 'W': True, 'visited': False}
                      for _ in range(width)] for _ in range(height)]

    def generate(self, start_x, start_y):
        stack = [(start_x, start_y)]
        self.grid[start_y][start_x]['visited'] = True
        opp = {'N': 'S', 'S': 'N', 'E': 'W', 'W':'E', 'visited': 'visited'}
        while stack:
            cx, cy = stack[-1]
            neighbors = []

            # Check unvisited neighbors
            if cy > 0 and not self.grid[cy-1][cx]['visited']: # North
                neighbors.append((cx, cy-1, 'N', 'S'))
            if cx < self.width - 1 and not self.grid[cy][cx+1]['visited']: # East
                neighbors.append((cx+1, cy, 'E', 'W'))
            if cy < self.height - 1 and not self.grid[cy+1][cx]['visited']: # South
                neighbors.append((cx, cy+1, 'S', 'N'))
            if cx > 0 and not self.grid[cy][cx-1]['visited']: # West
                neighbors.append((cx-1, cy, 'W', 'E'))

            if neighbors:
                nx, ny, current_wall, neighbor_wall = random.choice(neighbors)
                self.grid[cy][cx][current_wall] = False # Remove wall in current cell
                self.grid[ny][nx][neighbor_wall] = False # Remove wall in neighbor cell
                self.grid[ny][nx]['visited'] = True
                stack.append((nx, ny))
            else:
                stack.pop()
        # remove a bunch of walls 
        for r, cell in enumerate(self.grid[1:-1]):
          for c, n in enumerate(cell[1:-1]):
            for d in n:
                if rnd() > self.density:
                    n[d] =  False 

                
        for r, row in enumerate(self.grid):
          for c, cell in enumerate(row):
            if cell['S']:
              if r+1 < len(self.grid):
                 self.grid[r+1][c]['N']= True
            if cell['E']:
              if c+1 < len(self.grid):
                 self.grid[r][c+1]['W']= True
            if cell['W']:
              if 0 < c-1 < len(self.grid):
                 self.grid[r][c-1]['E']= True
            if cell['N']:
              if 0 < c-1 < len(self.grid):
                 self.grid[r-1][c]['S']= True
    

    def draw(self, cell_size):
        # Draw maze walls
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                px = x * cell_size
                py = y * cell_size 

                if cell['N']: # North wall
                    
                      ui.set_color('blue')
                      ui.fill_rect(px, py, cell_size, self.thickness)
                if cell['E']: # East wall
                    
                      ui.set_color('blue')
                      ui.fill_rect(px + cell_size - self.thickness/2, py, self.thickness, cell_size)
                if cell['S']: # South wall
                    
                       ui.set_color('blue')
                       ui.fill_rect(px, py + cell_size - self.thickness/2, cell_size, self.thickness)
                if cell['W']: # West wall
                  
                       ui.set_color('blue')
                       ui.fill_rect(px, py, self.thickness, cell_size)


class Tank:
    def __init__(self, view, x, y, angle, color, size, is_ai=False):
        # x, y is tank centre
        self.x = x
        self.y = y
        self.angle = angle # in degrees
        self.color = color
        self.size = size
        self.speed = 3
        self.rotation_speed = 1
        self.bullets = []
        self.is_ai = is_ai
        self.health = 100
        self.last_shot_time = 0 # For AI shooting cooldown
        self.view = view
        
    def render_tank(self):
        # Draw tank body
        ui.set_color(self.color)
        path = ui.Path.rounded_rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size, 5)
        path.fill()
        # draw left track
        ui.set_color('black')    
        path = ui.Path.rounded_rect(self.x - self.size/2, self.y - self.size/2-1, self.size, self.size/4, 5)
        path.fill()
        if self.view.moving_forward:
           off1 = off2 = random.random()*10
        elif self.view.rotating_left:
          off1 =  random.random()*10
          off2 = -off1
        elif self.view.rotating_right:
          off1 =  -random.random()*10
          off2 = -off1
        elif self.view.moving_backward:
           off1 = off2 = -random.random()*10
        else:
          off1 = off2 = 0
        ui.set_color('white') 
        # moving tracks   
        for i in range(1,4):
            path = ui.Path.rounded_rect(self.x - self.size/2 + i*self.size/4 +off1, self.y - self.size/2-1, 2, self.size/4, 5)
            path.fill()
        # draw right track
        ui.set_color('black')    
        path = ui.Path.rounded_rect(self.x - self.size/2, self.y + self.size/4+1, self.size, self.size/4, 5)
        path.fill()
        ui.set_color('white')
        # moving tracks       
        for i in range(1,4):
            path = ui.Path.rounded_rect(self.x - self.size/2 + i*self.size/4+off2, self.y + self.size/4+1, 2, self.size/4, 5)
            path.fill()
        # Draw barrel
        ui.set_color('grey')                
        p = ui.Path()
        p.move_to(self.x, self.y)
        p.line_to(self.x + self.size * 0.7, self.y)
        p.line_width = self.size * 0.25
        p.line_cap_style = ui.LINE_CAP_ROUND
        p.stroke()
    
    def render_health(self):
        # Draw health bar (simple rectangle)
        health_bar_width = self.size
        health_bar_height = 5
        health_bar_x = self.x - self.size/2
        health_bar_y = self.y - self.size/2 - 10
        ui.set_color('red')
        ui.fill_rect(health_bar_x, health_bar_y, health_bar_width, health_bar_height)
        ui.set_color('green')
        ui.fill_rect(health_bar_x, health_bar_y, health_bar_width * (self.health / 100), health_bar_height)
        
    def draw(self):
        # draw tank and health with rotation
        with ui.GState():
            # Move the origin (0, 0) to the center of the rectangle and then back again
            ui.concat_ctm(ui.Transform.translation(self.x, self.y))
            # Rotate the coordinate system:
            ui.concat_ctm(ui.Transform.rotation(math.radians(self.angle)))
            ui.concat_ctm(ui.Transform.translation(-self.x, -self.y))
            self.render_tank()
            self.render_health()
        

    def move(self, direction):
        # direction: 1 for forward, -1 for backward
        old_x, old_y = self.x, self.y
        self.x += direction * self.speed * math.cos(math.radians(self.angle))
        self.y += direction * self.speed * math.sin(math.radians(self.angle)) 
        #print(f'new {self.x} {self.y} angle {self.angle}')
        return old_x, old_y # Return old position for collision rollback

    def rotate(self, direction):
        # direction: 1 for clockwise, -1 for counter-clockwise
        self.angle += direction * self.rotation_speed
        self.angle %= 360 # Keep angle between 0 and 359

    def shoot(self, current_time):
        # Add a cooldown to prevent rapid firing
        if current_time - self.last_shot_time > 0.5: # 0.5 second cooldown
            bullet = Bullet(self.x, self.y, self.angle, self.size * 0.2, 'black')
            self.bullets.append(bullet)
            self.last_shot_time = current_time

class Bullet:
    def __init__(self, x, y, angle, size, color):
        self.x = x
        self.y = y
        self.angle = angle
        self.size = size
        self.color = color
        self.speed = 10
        self.active = True

    def draw(self):
        if self.active:
            ui.set_color(self.color)
            ui.fill_rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)

    def update(self):
        if self.active:
            self.x += self.speed * math.cos(math.radians(self.angle))
            self.y += self.speed * math.sin(math.radians(self.angle))


def check_collision_with_walls(tank, maze, cell_size):
    """
    # Determine the cells the tank is currently occupying or about to enter
    This is crucial. You'll need to check if the tank's proposed new position overlaps with any maze walls or another tank.
    # Inside your main game view or a separate collision manager
    """
    tank_center_x_grid = int(tank.x / cell_size)
    tank_center_y_grid = int(tank.y / cell_size)
    """
    # Simplified check: just check the cell the tank center is in
    # A more robust solution would check all four corners of the tank's bounding box
    # relative to the walls of the surrounding cells.
    """

    collided = False
    if tank_center_x_grid < 0 or tank_center_x_grid >= maze.width or \
       tank_center_y_grid < 0 or tank_center_y_grid >= maze.height:
        collided = True # Out of bounds

    else:
        current_cell = maze.grid[tank_center_y_grid][tank_center_x_grid]
        #print(f'{current_cell=}')
        # Check for collision with current cell's walls
        # This is a very basic check. You'd need more precise geometry.
        if current_cell['N'] and tank.y - tank.size/2 < tank_center_y_grid * cell_size + 2:
            collided = True
        if current_cell['E'] and tank.x + tank.size/2 > (tank_center_x_grid + 1) * cell_size - 2:
            collided = True
        if current_cell['S'] and tank.y + tank.size/2 > (tank_center_y_grid + 1) * cell_size - 2:
            collided = True
        if current_cell['W'] and tank.x - tank.size/2 < tank_center_x_grid * cell_size + 2:
            collided = True

        # Check adjacent cells for walls that are close to the tank's edges
        # For example, if moving north and there's a wall in the cell above.
        if tank.y - tank.size/2 < tank_center_y_grid * cell_size and tank_center_y_grid > 0:
            if maze.grid[tank_center_y_grid-1][tank_center_x_grid]['S']: # Wall to the north
                collided = True
        if tank.x + tank.size/2 > (tank_center_x_grid + 1) * cell_size and tank_center_x_grid < maze.width - 1:
            if maze.grid[tank_center_y_grid][tank_center_x_grid+1]['W']: # Wall to the east
                collided = True
        if tank.y + tank.size/2 > (tank_center_y_grid + 1) * cell_size and tank_center_y_grid < maze.height - 1:
            if maze.grid[tank_center_y_grid+1][tank_center_x_grid]['N']: # Wall to the south
                collided = True
        if tank.x - tank.size/2 < tank_center_x_grid * cell_size and tank_center_x_grid > 0:
            if maze.grid[tank_center_y_grid][tank_center_x_grid-1]['E']: # Wall to the west
                collided = True

    return collided

def check_bullet_collision(bullet, tank, cell_size):
    # Simple circle-to-rectangle collision for bullet and tank body
    try:
        if not bullet.active:
            return False
    except AttributeError:
        return False
    
    # Calculate distance between bullet center and tank center
    dist_x = bullet.x - tank.x
    dist_y = bullet.y - tank.y
    distance = math.sqrt(dist_x**2 + dist_y**2)

    # If the distance is less than sum of their radii/half-sizes, they collide
    if distance < (bullet.size/2 + tank.size/2):
        try:
           bullet.active = False
        except AttributeError:
           pass
        tank.health -= 10 # Reduce tank health
        return True
    return False

def check_bullet_wall_collision(bullet, maze, cell_size):
    if not bullet.active:
        return False

    grid_x = int(bullet.x / cell_size)
    grid_y = int(bullet.y / cell_size)

    if grid_x < 0 or grid_x >= maze.width or grid_y < 0 or grid_y >= maze.height:
        bullet.active = False # Bullet out of bounds
        return True

    current_cell = maze.grid[grid_y][grid_x]

    # Check against walls in the current cell. Again, this is simplified.
    if current_cell['N'] and bullet.y - bullet.size/2 < grid_y * cell_size + 2:
        bullet.active = False
        return True
    if current_cell['E'] and bullet.x + bullet.size/2 > (grid_x + 1) * cell_size - 2:
        bullet.active = False
        return True
    if current_cell['S'] and bullet.y + bullet.size/2 > (grid_y + 1) * cell_size - 2:
        bullet.active = False
        return True
    if current_cell['W'] and bullet.x - bullet.size/2 < grid_x * cell_size + 2:
        bullet.active = False
        return True

    return False


def pos_to_grid(pos, cell_size, div=True):
        if div:
          return int(pos - cell_size/2) // cell_size
        else:
          return int(pos - cell_size/2) % cell_size
          
def grid_to_pos(pos, cell_size):
        return pos * cell_size + cell_size/2
        
class AITank(Tank):
    """
    This is where it gets interesting. A simple AI could:
    * Wander: Randomly move forward and turn when it hits a wall.
    * Target Player: Once the player is within a certain range or line of sight, try to move towards the player and shoot.
    * Pathfinding (Advanced): Use A* or a similar algorithm to find a path to the player through the maze.
    For a basic AI, let's start with a "wander and chase" approach:"""
    
    def __init__(self, view, x, y, angle, color, size, target_tank, maze, cell_size):
        super().__init__(view, x, y, angle, color, size, is_ai=True)
        self.target_tank = target_tank
        self.maze = maze
        self.cell_size = cell_size
        self.state = 'wander' # 'wander' or 'chase'
        
        self.wander_timer = 0
        self.chase_range = 600 # Distance to start chasing
        self.can_see = False
        self.speed = 10
        self.viewtank = []
        self.last_state = 'wander'
        
    
          
    def wall_follower(self, end_pos):
        # follow the wall, staying in centre of cells and moving only in 
        # N, S, E, W
        #  angle is zero for East, 90deg is N, 180 is W, 270 is S   
        dirn ={1:'right', 0:'fwd', -1:'left', 2:'rev'}        
        # Check right, then front, then left, then back
        # make a decision when reach the centre of the cell
        if (math.isclose(pos_to_grid(self.x, self.cell_size, div=False), 0, abs_tol=1) and
            math.isclose(pos_to_grid(self.y, self.cell_size, div=False), 0, abs_tol=1)):
            for robot_dir in [1, 0, -1, 2]:                          
                if self.can_move(robot_dir):                                        
                    self.angle += (robot_dir * 90)  # E is zero for move
                    self.angle = (self.angle + 180) % 360 - 180 #normalize
                    self.move(1)
                    break  
        else:
            old_x, old_y = self.move(1)
            if check_collision_with_walls(self, self.maze, self.cell_size):
                self.x, self.y = old_x, old_y # Rollback
              
    def draw(self):
      super().draw()
      for loc in self.viewtank:
           x = grid_to_pos(loc[0], self.cell_size)
           y = grid_to_pos(loc[1], self.cell_size)
           ui.set_color('green' if self.can_see else 'red')
           ui.fill_rect(x, y, 20,20)
                    
    def can_move(self, direction):
        # check walls of current cell
        # report if can turn in supplied direction
        dirn = {270: 'N', 0:'E', 90: 'S', 180: 'W', -90: 'N', -180: 'W'}
        x_grid = pos_to_grid(self.x, self.cell_size)
        y_grid = pos_to_grid(self.y, self.cell_size)
        if x_grid < 0 or x_grid >= self.maze.width or \
             y_grid < 0 or y_grid >= self.maze.height:
            return False # Out of bounds    
        current_cell = self.maze.grid[y_grid][x_grid]
        angle = (self.angle + 90 * direction)
        angle = (angle + 180) % 360 - 180  
        wall = current_cell[dirn[angle]]              
        return not wall             
      
    def update_ai(self, current_time):
        distance_to_player = math.sqrt((self.x - self.target_tank.x)**2 + (self.y - self.target_tank.y)**2)
        self.can_see = self.can_see_player()
        if distance_to_player < self.chase_range and self.can_see :
            self.state = 'chase'
            self.last_state = 'chase'
        else:
            if self.last_state == 'chase':
                # back into wander, reset angle and position
                self.angle = (self.angle+45) // 90 * 90
                self.x = grid_to_pos(pos_to_grid(self.x, self.cell_size), self.cell_size)             
                self.y = grid_to_pos(pos_to_grid(self.y, self.cell_size), self.cell_size)      
            self.state = 'wander'
            self.last_state = 'wander'

        if self.state == 'wander':
            self.wander_timer -= 0.016 # Decrement by frame time (approx 60 fps)
            if self.wander_timer <= 0:
                self.speed = 10
                self.wander_timer = 0.1             
                self.wall_follower((self.target_tank.x, self.target_tank.y))
            
        elif self.state == 'chase':
            self.speed = 3
            # Aim at the player
            dx = self.target_tank.x - self.x
            dy = self.target_tank.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            
            # Normalize angles for shortest rotation
            angle_diff = (target_angle - self.angle + 180) % 360 - 180

            if angle_diff > self.rotation_speed:
                self.rotate(1)
            elif angle_diff < -self.rotation_speed:
                self.rotate(-1)
            else:
                self.angle = target_angle # Snap to target angle

            # Move towards the player if not too close and no immediate wall
            old_x, old_y = self.move(1)
            if check_collision_with_walls(self, self.maze, self.cell_size):
                self.x, self.y = old_x, old_y # Rollback
            else:
                # If too close, don't move or move backward slightly
                if distance_to_player < self.size * 1.5:
                    self.x, self.y = old_x, old_y


            # Shoot at the player if aimed correctly and within range
            if abs(angle_diff) < 5 and distance_to_player < self.chase_range: # Aimed within 5 degrees
                self.shoot(current_time)
                
    @staticmethod
    def bresenham(x0, y0, x1, y1):
        """Yield integer coordinates on the line from (x0, y0) to (x1, y1).
        See en.wikipedia.org/wiki/Bresenham's_line_algorithm
    
        Input coordinates should be integers.
    
        The result will contain both the start and the end point.
        """
        dx = x1 - x0
        dy = y1 - y0
    
        xsign = 1 if dx > 0 else -1
        ysign = 1 if dy > 0 else -1
    
        dx = abs(dx)
        dy = abs(dy)
    
        if dx > dy:
            xx, xy, yx, yy = xsign, 0, 0, ysign
        else:
            dx, dy = dy, dx
            xx, xy, yx, yy = 0, ysign, xsign, 0
    
        D = 2*dy - dx
        y = 0
    
        for x in range(dx + 1):
            yield x0 + x*xx + y*yx, y0 + x*xy + y*yy
            if D >= 0:
                y += 1
                D -= 2*dx
            D += 2*dy
                
    def can_see_player(self):
        # use bresenham algorithm to get coords between player and eneny
        # Get grid coordinates of both tanks
        ax, ay = pos_to_grid(self.x, self.cell_size), pos_to_grid(self.y, self.cell_size)
        px, py = pos_to_grid(self.target_tank.x, self.cell_size), pos_to_grid(self.target_tank.y, self.cell_size)
        self.viewtank = list(self.bresenham(ax, ay, px, py))
        try:
          dirnx = self.viewtank[1][0] - self.viewtank[0][0]
          dirny = self.viewtank[1][1] - self.viewtank[0][1]        
          for x, y in self.viewtank:
              if dirnx == 1:
                if 0 <= x < self.maze.width and self.maze.grid[y][x]['E']: # Wall to the East
                    return False
              if dirnx == -1:
                if 0 <= x < self.maze.width and self.maze.grid[y][x]['W']: # Wall to the West
                  return False 
              if dirny == -1:              
                if 0 <= y < self.maze.height and self.maze.grid[y][x]['S']: # Wall to the South
                  return False
              if dirny == 1:
                 if 0 <= y < self.maze.height and self.maze.grid[y][x]['N']: # Wall to the North
                  return False
        except IndexError:
          return True
        return True
        
                  
class GameView(ui.View):
    def __init__(self):
        self.background_color = 'sandybrown'
        self.maze_width = 15 # Number of cells
        self.maze_height = 15
        self.cell_size = 60
        self.maze = Maze(self.maze_width, self.maze_height, density=0.3)
        self.maze.generate(0, 0) # Generate maze starting from (0,0)

        # Initialize tanks in random locations
        
        player_start_x = grid_to_pos(random.randint(0, self.maze_width//4), self.cell_size)
        player_start_y = grid_to_pos(random.randint(0, self.maze_height//4), self.cell_size)
        ai_start_x  = grid_to_pos(random.randint(self.maze_width//2, self.maze_width-1), self.cell_size)
        ai_start_y  = grid_to_pos(random.randint(0, self.maze_height//2), self.cell_size)
        

        self.player_tank = Tank(self, player_start_x, player_start_y, 45, 'green', 40)
        self.ai_tank = AITank(self, ai_start_x, ai_start_y, 270, 'red', 40, self.player_tank, self.maze, self.cell_size)

        self.last_update_time = time.time()
        self.game_over = False
        self.winner = None # 'Player' or 'AI'

        # Controls (touch based)
        self.touch_start_time = 0
        self.touch_start_point = None
        self.moving_forward = False
        self.moving_backward = False
        self.rotating_left = False
        self.rotating_right = False
        
        self.add_buttons()
        self.initial_touch = None
        self.update_interval = 1/60
        
    def add_buttons(self):
        # Add buttons for shooting (or use a dedicated shoot region)         
        #img = Image.open('iob:arrow_up_c_256')
        params = {'border_width': 3, 'border_color': 'black', 
                  'tint_color': 'black', 'corner_radius': 5}
        #im.rotate(45).show()
        self.shoot_button = ui.Button(title='Shoot', **params)
        self.shoot_button.bg_color = 'red'        
        self.shoot_button.action = self.shoot_player
        self.add_subview(self.shoot_button)
        
        btn_size = 100
        pos = Point(self.maze_width*self.cell_size +50, self.maze_height*self.cell_size/2)
        self.shoot_button.frame = (pos.x + btn_size*3.5,  pos.y, btn_size, btn_size) 
        self.buttons = {}
        for i, title in enumerate(['Left Fwd', 'Fwd', 'Right Fwd', 
                                   'Left', 'Stop', 'Right', 
                                   'Left Rev', 'Rev', 'Right Rev']):
          btn = ui.Button(title=title, **params)
          self.buttons[title] = btn
          #with io.BytesIO() as bIO:
          #  img1.rotate(random.random()*180).show()
          #  img1.save(bIO, img.format)
            # btn.image = ui.Image.from_data(bIO.getvalue())          
          
          btn.frame =  (pos.x + (i % 3) *btn_size, pos.y + (i//3) *btn_size, btn_size, btn_size)  
          btn.bg_color = 'lightgray'
          btn.touch_enabled=False
          btn.enabled=False
          self.add_subview(btn) 
          #btn.action = self.move_tank       

    def move_tank(self, sender):
      def stop():
          self.moving_forward = False
          self.moving_backward = False
          self.rotating_left = False
          self.rotating_right = False               
      
      match sender.title:        
        case 'Rev':
            self.moving_backward = True
        case 'Stop':
            stop()       
        case 'Fwd':
            self.moving_forward = True
        case 'Right':
            self.rotating_right = True            
        case 'Left':
             self.rotating_left = True
        case 'Left Fwd':
             self.rotating_left = True
             self.moving_forward = True
        case 'Right Fwd':
             self.rotating_right = True
             self.moving_forward = True
        case 'Left Rev':
             self.rotating_left = True
             self.moving_backward = True
        case 'Right Rev':
             self.rotating_right = True
             self.moving_backward = True
             
      #ui.delay(stop, 0.25)
             
    def layout_(self):
        # Adjust button position on layout changes
        self.shoot_button.frame = (self.maze_width*self.cell_size -50, self.maze_height*self.cell_size + 30, 80, 40) #self.maze_width*self.cell_size - 100, self.maze_height*self.cell_size + 150, 80, 40)
        
    def start_game_loop(self):
        # Use ui.set_interval for the game loop (approx 60 FPS)
        raise Exception
        if not hasattr(self, '_timer'):
            self._timer = ui.update_interval # 60 frames per second
            
    def draw(self):
        self.maze.draw(self.cell_size)
        self.player_tank.draw()
        self.ai_tank.draw()
        
        # Draw bullets
        for bullet in self.player_tank.bullets + self.ai_tank.bullets:
            bullet.draw()

        if self.game_over:
            ui.set_color('white')
            font_size = 50
            message = f"{self.winner} Wins!"
            
            # Calculate text size for centering
            text_width, text_height = ui.measure_string(message, font=('Courier', font_size))
            
            # Center the text
            text_x = (self.bounds.width - text_width) / 2 +300
            text_y = (self.bounds.height - text_height) / 2 -200
            
            ui.draw_string(message, (text_x, text_y, text_width, text_height), font=('Courier', font_size), alignment=ui.ALIGN_CENTER)
            ui.delay(self.restart, 3)
            
    def update(self):
        if self.game_over:
            return

        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        # Player movement
        if self.moving_forward:
            old_x, old_y = self.player_tank.move(1)
            if check_collision_with_walls(self.player_tank, self.maze, self.cell_size):
                self.player_tank.x, self.player_tank.y = old_x, old_y
            if check_bullet_collision(self.player_tank, self.ai_tank, self.cell_size):
                 self.player_tank.x, self.player_tank.y = old_x, old_y

        if self.moving_backward:
            old_x, old_y = self.player_tank.move(-1)
            if check_collision_with_walls(self.player_tank, self.maze, self.cell_size):
                self.player_tank.x, self.player_tank.y = old_x, old_y
            if check_bullet_collision(self.player_tank, self.ai_tank, self.cell_size):
                 self.player_tank.x, self.player_tank.y = old_x, old_y

        if self.rotating_left:
            self.player_tank.rotate(-1)
        if self.rotating_right:
            self.player_tank.rotate(1)

        # AI Tank update
        self.ai_tank.update_ai(current_time)
        
        # Bullet updates and collisions
        all_bullets = self.player_tank.bullets + self.ai_tank.bullets
        for bullet in all_bullets:
            bullet.update()
            if check_bullet_wall_collision(bullet, self.maze, self.cell_size):
                continue # Bullet hit a wall, no need to check tank collision

            if bullet.active: # Only check if bullet is still active
                if bullet in self.player_tank.bullets and check_bullet_collision(bullet, self.ai_tank, self.cell_size):
                    pass # Collision handled in check_bullet_collision
                elif bullet in self.ai_tank.bullets and check_bullet_collision(bullet, self.player_tank, self.cell_size):
                    pass # Collision handled

        # Remove inactive bullets
        self.player_tank.bullets = [b for b in self.player_tank.bullets if b.active]
        self.ai_tank.bullets = [b for b in self.ai_tank.bullets if b.active]
        
        # Check for tank-on-tank collision (simple)
        if self.check_tank_tank_collision(self.player_tank, self.ai_tank):
            # Push back tanks or apply damage
            # For simplicity, we'll just stop movement. A more realistic approach
            # would involve resolving the collision (e.g., pushing tanks apart).
            pass # Collision handled in movement to prevent overlapping

        # Check for game over
        if self.player_tank.health <= 0:
            self.game_over = True
            self.winner = 'AI'
        elif self.ai_tank.health <= 0:
            self.game_over = True
            self.winner = 'Player'

        self.set_needs_display() # Redraw the view

    def touch_began(self, touch):
        self.touch_start_point = touch.location
        self.touch_start_time = time.time()
        # Determine movement based on touch location
        if touch.location.y > self.height * 0.7: # Bottom part of screen for movement
            if touch.location.x < self.width * 0.3:                                
                self.rotating_left = True
            elif touch.location.x > self.width * 0.7:
                pass
                self.rotating_right = True
            else: # Middle for forward/backward
                self.moving_forward = True # Default to forward, could add a second touch for backward
                
        for name, btn in self.buttons.items():         
           if btn.frame.contains_point(touch.location):   
             self.move_tank(btn)
             break
            
    def touch_moved(self, touch):
        # Could implement joystick-like controls here
        pass

    def touch_ended(self, touch):
        self.moving_forward = False
        self.moving_backward = False
        self.rotating_left = False
        self.rotating_right = False
        self.touch_start_point = None
        

    def shoot_player(self, sender):
        if not self.game_over:
            self.player_tank.shoot(time.time())
            
    def check_tank_tank_collision(self, tank1, tank2):
        # Simple circle-to-circle collision for tank bodies
        dist_x = tank1.x - tank2.x
        dist_y = tank1.y - tank2.y
        distance = math.hypot(dist_x, dist_y)

        if distance < (tank1.size/2 + tank2.size/2):
            return True
        return False
        
    def restart(self):
       self.__init__()

# Main execution
if __name__ == '__main__':
    console.clear()
    v = GameView()
    v.present('full_screen')
    v.width = v.bounds.width # Set width and height from actual bounds
    v.height = v.bounds.height
    #v.layout() # Call layout once after setting frame
    # Start the update loop
    #ui.set_internal_property('PythonistaGameLoop', True) # Enable game loop in Pythonista
"""

Enhancements and Considerations
 * More Robust Collision: The collision detection, especially for maze walls, is simplified. A proper implementation would check the corners of the tank's bounding box against the specific wall segments. For tank-on-tank, you'd want to resolve the collision (push them apart) rather than just preventing movement.
 * A Pathfinding for AI:* For a truly intelligent AI, implementing A* pathfinding would allow the AI tank to navigate the maze efficiently to reach the player. This would involve converting your maze grid into a graph.
 * Improved AI Behavior:
   * Line of Sight: A proper raycasting algorithm to check if the AI can truly "see" the player through maze openings.
   * Shooting Accuracy: Make AI shooting less perfect, perhaps adding a small random spread to bullets.
   * Obstacle Avoidance: Beyond just hitting walls, the AI could try to avoid getting stuck in corners.
 * Graphics: Using Pythonista's scene module or SpriteKit (if you're on iOS and using Pythonista 3) would allow for more complex graphics, sprites, and animations.
 * Sound Effects: Add sounds for shooting, explosions, and movement.
 * Game State Management: More robust handling of game states (menu, playing, game over).
 * User Interface: Better on-screen controls, perhaps a virtual joystick.
 * Multiple Levels: Implement different maze layouts.
 * Power-ups: Add health packs, speed boosts, etc.
This provides a solid foundation for your tank game in Pythonista. Remember to test thoroughly and iterate on the features!
"""



        

