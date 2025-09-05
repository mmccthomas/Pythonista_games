import scene
import math
import motion
import io
import ui

import random
import math
from collections import Counter, namedtuple
from types import SimpleNamespace
from time import time
from jumping_config import *
from level_manager import LevelManager
from player_movement import PlayerMove
from scene import *
import base_path
base_path.add_paths(__file__)
from joystick import Joystick 
TEXTURE_CHANGE = 0.25
ENEMY_DISABLE_TIME = 3
DEADZONE = 0.5
LEVEL = None
Status = namedtuple("Status", "x y  x_velocity y_velocity on_ground")
# Key has alternative sprite when acquired. allows key or lever
# any item can have list of alternative sprites
#
def pil_to_ui(img):
    with io.BytesIO() as bIO:
        img.save(bIO, 'png')
        return ui.Image.from_data(bIO.getvalue())

def sgn(x):
    return 1 if x >= 0 else -1
                                    
class GameObject():
     def __init__(self, sprite, alt_sprites=None):      
         self.sprite = sprite
         self.position = self.sprite.position
         self.extents = self.sprite.frame    
         # extent a little beyond extents for detection
         self.dirns = {'below': (0.5, 0.05), 'above': (0.5, 0.95) ,'right': (0.95, 0.5), 'left': (0.05, 0.5) }
         self.game = sprite.parent
         self.change_interval = 0.5
         self.change_timer = self.change_interval
         self.enabled_timer = 0
         self.enabled = True
         self.cycle_index = 0
         self.direction = 1
         self.speed = 0
         self.alt_sprites = alt_sprites
         
     def update(self, dt, *args):        
       # cycle thru sprite alternate images if any
       if self.change_timer > 0:
           self.change_timer -= dt
       else:
           self.change_timer = self.change_interval
           if self.alt_sprites: 
               alternative = self.alt_sprites[self.cycle_index]       
               self.cycle_index = (self.cycle_index + 1) % len(self.alt_sprites)
               self.change_texture(alternative)         
       # invoke countdown on object when hit_timer is initiated  
       if self.enabled_timer > 0:
           self.enabled = False
           self.enabled_timer -= dt
       else:
           self.enabled = True                  
      
     def change_texture(self, img_name):                     
            img_name = img_name + '.png'            
            img = self.sprite.parent.flat_dict[img_name]
            img_ui = pil_to_ui(img)
            size = self.sprite.size # old size           
            self.sprite.texture = Texture(img_ui) 
            self.sprite.size = size
            
     def collides(self, obj, dirn, delta=(0,0)):        
        # self collides with object
        # dirn is one of 'above', 'below', 'right', 'left'        
        offsets = self.dirns[dirn]
        # player collides with object
        point = Point(self.position.x + offsets[0] * self.extents.w + delta[0],
                      self.position.y + offsets[1] * self.extents.h + delta[1])
        return obj.extents.contains_point(point)       
        
     def on_platform(self, walls):
        # find if object falls off platform
        # find area of intersection of object shifted down by 20 pixels
        # with all other walls/platforms
        # reduce width of object by 2 pixels to prevent left/right intersections
        amount_to_shift_down = 20
        object_to_test = self.extents.inset(0,1).translate(0,-amount_to_shift_down)
        area = sum([math.prod(wall.extents.intersection(object_to_test).size) for wall in walls ])      
        return  area > 0.9 * object_to_test.w * amount_to_shift_down
     
     def moves_with_platform(self, walls):
         if self.on_platform(walls):
           
           for wall in walls:
              
              if self.collides(wall, 'below') and isinstance(wall, (PlatformSlippy, PlatformMoving)):
                 self.position.x += wall.speed * wall.direction
                 break  
              
              if self.collides(wall, 'below', delta=(0, -10)) and isinstance(wall, PlatformCollapsing):     
                 wall.contact(time())
                 break    
        
                  
class Player(GameObject):
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite)        
        self.on_ground = True        
        self.speed = 200        
        self.x_velocity = 0
        self.y_velocity = 0
        self.position = self.sprite.position
        self.half_height = self.extents.h / 2
        self.half_width = self.extents.x / 2
        self.alt_sprites = alt_sprites[0]
        self.cycle_index = 0
        self.countdown = 0
        self.bounce = False
        self.shield = False
        self.change_timer = TEXTURE_CHANGE
        for k, v in types.items():
          if v[0] == 'Player':
              self.sprite_name = k
        self.state = Status(self.position.x, self.position.y, 
                      self.x_velocity, self.y_velocity,
                      self.on_ground)    
    def jumping(self, dt):  
        if self.alt_sprites:       
            alternative = self.alt_sprites['jump']
            self.change_texture(alternative)  
            
    def walking(self, dt):
       if self.change_timer > 0:
           self.change_timer -= dt
           return
       self.change_timer = TEXTURE_CHANGE
       if self.alt_sprites:       
           alternative = self.alt_sprites['walk'][self.cycle_index]       
           self.cycle_index = (self.cycle_index + 1) % len(self.alt_sprites['walk'])
           self.change_texture(alternative)                                             
        
    def set_bounce(self):
        if self.bounce:
            pass
        else:
            pass
                  
    def update(self, dt, walls):
        if self.countdown < 0:
            self.bounce = False
            self.shield = False                   
        else:
            self.countdown -= dt                             
        
        self.position.x, self.position.y, self.x_velocity, self.y_velocity, self.on_ground = self.state
        self.position = Point(int(self.position.x), int(self.position.y))            
        if self.game.player_move.moving:
            self.walking(dt)
        elif not self.on_ground:
            self.jumping(dt)
        else:
            self.change_texture(self.sprite_name) #standing
            
        self.set_bounce()                          
        self.moves_with_platform(walls)
        self.check_walls(walls) 
        self.state = Status(self.position.x, self.position.y, 
                      self.x_velocity, self.y_velocity,
                      self.on_ground)    
        
        self.sprite.position = self.position
        self.extents = self.sprite.frame
            
    def check_walls(self, walls):
        """ check for collision with walls or platforms """
        #self.on_ground = False                        
        
        # print(f'position {self.position}, velocity {self.y_velocity}'
        
        self.on_ground = self.on_platform(walls)
        
        # Collision with  wall below
        for wall in walls:
            if self.collides(wall, 'below'):           
               self.position = Point(self.position.x, 
                                     max(self.position.y, wall.extents.max_y))
               # make player  stop on wall     
               if self.y_velocity <= 0:          
                  self.y_velocity = 0          
               break
        # Collision with right wall
        for wall in walls:
            if self.collides(wall, 'right'):        
                self.position = Point(min(self.position.x, wall.extents.min_x - self.extents.w), 
                                      self.position.y)
                self.x_velocity = -self.x_velocity  # Bounce horizontally
                break        
        # Collision with left wall
        for wall in walls:
           if self.collides(wall, 'left'):
               self.position = Point(max(self.position.x, wall.extents.max_x) , 
                                     self.position.y)
               self.x_velocity = -self.x_velocity   # Bounce uhorizontally
               break
        # Collision with  wall at top       
        for wall in walls:
            if self.collides(wall, 'above'):          
               if wall.extents.max_y > self.game.size.height -100:
                 self.position = Point(self.position.x, 
                                       wall.extents.min_y - self.extents.h)  
                 self.y_velocity = -self.y_velocity  # Bounce
                 break
        
        self.state = (self.position.x, self.position.y, 
                      self.x_velocity, self.y_velocity,
                      self.on_ground)         

# if enemy is hit, same enemy can not be hit for 3 seconds                
class EnemyStatic(GameObject):    
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite)
        self.change_interval = 0.25
        self.alt_sprites = alt_sprites        
           
    def update(self, dt, walls):
       super().update(dt, walls)                                              
       self.moves_with_platform(walls)
        
                                    
class EnemyVertical(GameObject):
    # vertical  enemies move up and down between walls or platform
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite) 
        self.alt_sprites = alt_sprites       
        self.speed = 2.5
        self.change_interval = 0.1        
        
    def update(self, dt, walls):
       super().update(dt, walls)
       self.position.y += self.speed * self.direction       
       self.sprite.position = Point(self.position.x, self.position.y)
       self.extents = self.sprite.frame
       for wall in walls: 
          if self.collides(wall, 'above'):
             self.direction = -1
             break
          if self.collides(wall, 'below'):
             self.direction = 1
             break
                                
                  
class EnemyHorizontal(GameObject):
    # horizontal enemies move back and forword on a wall or platform        
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite)        
        self.alt_sprites = alt_sprites
        self.speed = 0.5
                          
    def update(self, dt, walls):
       
       super().update(dt, walls)
       self.position.x += self.speed * self.direction
       self.moves_with_platform(walls)
       
       self.sprite.position = Point(self.position.x, self.position.y)
       self.extents = self.sprite.frame
       if not self.on_platform(walls):
            self.direction *= -3 # speed up
       else:
           self.direction = sgn(self.direction)       
           
       for wall in walls:             
           if self.collides(wall, 'right') or self.collides(wall, 'left'):
               self.direction *= -1
               break
                                                         
              
class Wall(GameObject): 
    def __init__(self, sprite):
        super().__init__(sprite)
       
                  
class PlatformStatic(GameObject):
    def __init__(self, sprite):
        super().__init__(sprite)
        
         
class PlatformMoving(GameObject):
    # group of sprites that move together
    def __init__(self, sprite):
        super().__init__(sprite)
        self.sprites = [sprite]
        self.positions = [sprite.position for sprite in self.sprites]
        self.speed = 1
        self.extents = self.get_overall_rect([sprite.frame for sprite in self.sprites])
        
    def add_sprite(self, sprite):
        self.sprites.append(sprite)
        self.extents = self.get_overall_rect([sprite.frame for sprite in self.sprites])
        self.positions = [sprite.position for sprite in self.sprites]

    def update(self, dt, walls):        
        for sprite, position  in zip(self.sprites, self.positions):
            position.x += self.speed * self.direction
            sprite.position = Point(position.x, position.y)            
            
        self.extents = self.get_overall_rect([sprite.frame for sprite in self.sprites])
        # reverse direction if hits anything                         
        for wall in walls: 
          if self.extents.inset(20, 0).intersects(wall.extents):          
             self.direction *= -1
             break        
         
    def get_overall_rect(self, rects):
        # assume
        if not rects:
            return None
    
        # Get the coordinates of the first rectangle to initialize min/max values
        first_rect = rects[0]        
        # Iterate through the rest of the rectangles to find the true min/max
        for rect in rects:            
            min_x = min(first_rect.x, rect.x)
            min_y = min(first_rect.y, rect.y)
            max_x = max(first_rect.max_x, rect.max_x)
            max_y = max(first_rect.max_y, rect.max_y)    
        # Return the new Rect object representing the overall bounds
        return Rect(min_x, min_y, max_x - min_x, max_y - min_y)

          
class PlatformSlippy(GameObject):
    # sprites that cause player to move
    def __init__(self, sprite, direction, alt_sprites=None):
        super().__init__(sprite)
        self.alt_sprites = alt_sprites
        self.speed = 2.5

class PlatformCollapsing(GameObject):
    # platform that will start to collapse when touched
    # 3 states full, half,collapsed
    def __init__(self, sprite, color, alt_sprites=None):
        super().__init__(sprite)
        #self.sprite.color = color
        self.sprite.alpha = 1
        self.alt_sprites = alt_sprites
        self.contact_time = 0.5 
        self.state_index = 0
        self.change_interval = 1e10
        self.t0 = 0
       
    def contact(self, time_):
        # if in contact for more than wall.contact_time
        # change state of wall
        if self.t0 == 0:
            self.t0 = time_      
        if time_ - self.t0 > 2.0:
           self.t0 = 0
           return          
        if time_ - self.t0 > self.contact_time:          
          self.t0 = 0
          self.state_index += 1
          if self.state_index == 1:
             self.change_texture(self.alt_sprites[1])
          elif self.state_index == 2: #remove 
             self.sprite.remove_from_parent()
             self.extents = Rect(0, 0, 0, 0)
 
                  
class Key(GameObject):
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite)
        self.alt_sprites = alt_sprites
        self.collected = False
        
    def collect(self):
        self.collected = True
        if self.alt_sprites:
            self.change_texture(self.alt_sprites[0])         
        else:
            self.sprite.remove_from_parent()
        
         
class DoorExit(GameObject):
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite) 
        self.alt_sprites = alt_sprites
        self.unlocked = False       
              
    def unlock(self):
        self.unlocked = all([key.collected for key in self.sprite.parent.keys])
        if self.alt_sprites and self.unlocked:
            self.change_texture(self.alt_sprites[0])       
        
              
class Prize(GameObject):
    # prizes have optionas powerups
    def __init__(self, sprite, alt_sprites=None):
        super().__init__(sprite)
        self.collected = False
        self.alt_sprites = alt_sprites
        
    def collect(self):
        self.collected = True
        self.sprite.remove_from_parent()
        if self.alt_sprites:
            powerup, duration = self.alt_sprites[0:2]
            if powerup == 'bounce':
               self.game.player.bounce = True
               self.game.player.countdown = duration
               print('bounce for', duration)
            elif powerup == 'shield':
               self.game.player.shield = True
               self.game.player.countdown = duration
               print('shield for', duration)


class Game(scene.Scene):
    def setup(self):
        self.paused = True
        self.background_color = '#000000'
        self.score = 0
        self.lives = 3
        self.score_label = scene.LabelNode('', font=('Helvetica', 20), 
                                           position=(100, self.size.height - 10))
        self.score_label.anchor_point=(0, 0.5)
        self.add_child(self.score_label)
        self.joystick = Joystick(position=Point(self.size.width-100, 100), 
                                 color='white', show_xy=False,
                                 deadzone_x=DEADZONE,
                                 deadzone_y=DEADZONE)
        self.add_child(self.joystick)
        
        self.current_level_index = 0
        # LEVEL and LEVEL_FILE are overriden if invoked externally
        self.level_manager = LevelManager()
        self.level_manager.load_levels(LEVEL_FILE)
        all_levels = self.level_manager.levels
        level_names = list(all_levels)
        if LEVEL is None:
            self.current_level = level_names[self.current_level_index]
        else:
            self.current_level = LEVEL
        self.level_data = all_levels[self.current_level]
        # get levels, dict of text1, text2 and table
        
        self.image_dict = config.image_dict
        self.lookup = config.lookup        
        self.flat_dict = config.flat_dict
        self.layout_map = self.make_layout_map()      
        self.orientation = self.get_orientation()
        
        self.load_level()
        self.all_platforms = self.walls + self.sliding_platforms + self.static_sliders + self.collapsing_platforms# Check all platform types
        self.keys_pressed = set()
        self.player_move = PlayerMove(*self.player.position)
        self.countdown = 0.25
        self.paused = False
        
    def get_orientation(self):
        with motion.MotionUpdates():           
            x, y, z = motion.get_gravity()
           
        if abs(x) > abs(y):
               orientation = 'LANDSCAPE, RIGHT' if x > 0 else 'LANDSCAPE, LEFT'
        else:
            if y < 0:
                orientation = 'PORTRAIT, LEFT'
            else:
                orientation = 'PORTRAIT, RIGHT'    
        return orientation
     
    def make_layout_map(self):
        # layout map is dict of character to pil image
        map = {k: self.flat_dict[v]
               for k, v in self.lookup.items()}            
        sprite_sizes = [img.size for img in map.values()]
        counter = Counter(sprite_sizes)
        self.most_sizes = counter.most_common(1)[0][0] # key of single most common item
        #self.most_sizes = max(counter, key=lambda key: counter[key])
        self.most_sizes = ui.Size(*self.most_sizes)
        # allow config to set own gridsize
        if hasattr(config, 'min_size'):
           self.most_sizes = config.min_size            
        return map                     
    
    def find_key(self, data, target_key):
       """
       DFS search a multilevel dictionary for a specific key and returns its value.
       """       
       if isinstance(data, dict):
           for key, value in data.items():
               if key == target_key:
                   return value
               self.path.append(key)
               # If the value is a dictionary, recurse into it
               result = self.find_key(value, target_key)
               if result is not None:
                   return result   
       # If the data is a list, iterate through its elements and search
       elif isinstance(data, list):
           for item in data:
               result = self.find_key(item, target_key)
               if result is not None:
                   return result       
       return None
               
    def load_level(self):
        # load the current level text and fill categories
        self.children.clear()
        self.add_child(self.score_label)
        # categories of object
        self.walls = []
        self.enemies = []
        self.door = None
        self.prizes = []
        self.keys = []
        self.sliding_platforms = []
        self.collapsing_platforms = []
        self.static_sliders = [] # New list for static sliders
        self.player = None
        self.new_platform = True
        
        level_grid = self.level_data['table']
        
        # compute tile size for screen
        X, Y = len(level_grid[0]), len(level_grid)
        if self.orientation == 'PORTRAIT':
            tile_size = self.size.width / X
        else:
            tile_size = self.size.height / Y
        tile_size *= 0.95
        max_y = self.size.height  - tile_size / 2 - 50
        # sprite base size
        base_size = self.most_sizes
        
        all_names = []
        for row_index, row in enumerate(level_grid):
            for col_index, char in enumerate(row):
                x = col_index * tile_size # + tile_size / 2
                y = max_y - (row_index * tile_size)
                
                if char in self.layout_map and self.layout_map[char]:
                    ui_img = pil_to_ui(self.layout_map[char])
                    rel_size = Size(ui_img.size.x / base_size.x, ui_img.size.x / base_size.x)
                    sprite = SpriteNode(Texture(ui_img), 
                                        position=(x, y),
                                        size=(rel_size.x * tile_size, rel_size.y *tile_size),
                                        anchor_point=(0,0)
                                        )
                    self.add_child(sprite)
                    # check image name in types list
                    sprite_name = self.lookup[char].removesuffix('.png')
                    all_names.append(sprite_name)
                    # print(sprite_name)
                    if sprite_name in types:
                        class_name = types[sprite_name][0]
                        alt_sprites = types[sprite_name][1:]
                    else:
                        class_name = None 
                        alt_sprites = None                   
                    # classobj = globals().get(types[sprite_name], None)
                    match class_name:
                      case 'Wall':
                         self.walls.append(Wall(sprite))
                         self.new_platform = True
                      case 'Player':
                         self.player = Player(sprite, alt_sprites)
                      case 'EnemyStatic':
                          self.enemies.append(EnemyStatic(sprite, alt_sprites))
                      case 'EnemyVertical':
                          self.enemies.append(EnemyVertical(sprite, alt_sprites))
                      case 'EnemyHorizontal':
                          self.enemies.append(EnemyHorizontal(sprite, alt_sprites))           
                      case 'PlatformStatic':
                          self.walls.append(PlatformStatic(sprite))
                          self.new_platform = True
                      case 'PlatformMoving':
                          # add item to platform until space, wall or another platform
                          if self.new_platform:
                              self.sliding_platforms.append(PlatformMoving(sprite))
                              self.new_platform = False
                          else:
                              self.sliding_platforms[-1].add_sprite(sprite)                              
                      case 'PlatformSlippy':
                          # add item to platform until space, wall or another platform
                         self.static_sliders.append(PlatformSlippy(sprite, direction=1, alt_sprites=alt_sprites))
                      case 'PlatformCollapsing':
                          # add item to platform until space, wall or another platform
                         self.collapsing_platforms.append(PlatformCollapsing(sprite, color='grey', alt_sprites=alt_sprites))
                      case 'Key':
                          self.keys.append(Key(sprite, alt_sprites))
                      case 'DoorExit':
                          self.door = DoorExit(sprite, alt_sprites)
                      case 'Prize':
                          self.prizes.append(Prize(sprite, alt_sprites))
                      case None:
                          self.new_platform = True       
                else:
                    self.new_platform = True                                                              
        print('icon names used:', set(all_names))          

    def update(self):
        self.joystick.update()        
        self.platforms_update()
        self.player_movement()
        self.enemies_update()
        self.check_collisions()
        self.update_info()        

    def update_info(self):
       if self.countdown > 0:
           self.countdown -= self.dt
           return
       self.countdown = 0.25
       shield = '\u2733' if self.player.shield else ''
       self.score_label.text = f"Score: {self.score} Lives: {self.lives} {shield}"
       #self.score_label.text = f'xv:{self.player.x_velocity:.3f} yv:{self.player.y_velocity:.2f} {self.orientation} '
       
    def touch_began(self, touch):
        # Touch controls for mobile
      if self.joystick.bbox.contains_point(touch.location):
          self.joystick.touch_began(touch)
                
    def touch_moved(self, touch):
        sense = DEADZONE
        if self.joystick.bbox.contains_point(touch.location):
            self.joystick.touch_moved(touch)        
            self.keys_pressed = self.joystick.keys_pressed
            if 'up' in self.keys_pressed:
                self.keys_pressed.add('jump')
            if 'down' in self.keys_pressed:
                self.keys_pressed.add('jump')
                         
        
    def touch_ended(self, touch):
        self.joystick.touch_ended(touch)        
        self.keys_pressed.clear()                                        
          
    def player_movement(self):
        # get update from PlayerMove and transfer to player                
        self.player.state = self.player_move.update(self.dt, [], self.keys_pressed, self.player.state)      
                   
        self.player.update(self.dt, self.all_platforms)         
                        
    def enemies_update(self):
        for enemy in self.enemies:
            enemy.update(self.dt, self.all_platforms)
            
    def platforms_update(self):
        for platform in self.sliding_platforms + self.collapsing_platforms:
            platform.update(self.dt, self.walls + self.static_sliders)      
                           
                    
    def check_collisions(self):
        # if enemy is hit it is disabled for a period
        for enemy in self.enemies:
            if self.player.extents.intersects(enemy.extents):
                if not self.player.shield and enemy.enabled: 
                    enemy.enabled_timer = ENEMY_DISABLE_TIME
                    self.score -= 100
                    self.lives -= 1                                             
                
        for prize in self.prizes:
            if self.player.extents.intersects(prize.extents):
                if not prize.collected:
                    prize.collect()               
                    self.score += 100
              
        for key in self.keys:
            if self.player.extents.intersects(key.extents):
              key.collect()
              self.door.unlock()              
              
        if self.player.extents.intersects(self.door.extents):
            if self.door.unlocked:
                self.score += 100
                print("Level Complete!")

def main(**kwargs):    
    try:
      LEVEL_FILE = kwargs['file']
      LEVEL = kwargs['level_name']
    except (KeyError, AttributeError):
      pass
    g = Game()
    # g.setup()
    run(g)
    
if __name__ == '__main__':
    main()
    
    
