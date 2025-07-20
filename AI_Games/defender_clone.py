# TODO add scanner
#.     add  terrain
#.     sort out direction and movement, reverse etc
#      add alien missiles
#      bombers and pods release swarms when hit

from scene import *
import ui
import sound
import console
import random
import time
import math
import numpy as np
from collections import defaultdict
from math import pi
from copy import copy
from itertools import cycle
from joystick import Joystick
import spritesheet

NAME = 'defender.png'
    #NAME = 'image.png'

sprite_names = ['mutant1', 'mutant2',
    'podexpl','swarmexpl',  
    'pod1', 'pod2',
    'humanoid1', 
    [f'bomber{i}' for i in range(1,6)],
    'purple circle',
    [f'bomb{i}' for i in range(1,5)], 
    'swarmer1', 'swarmer2',   
    [f'lander{i}' for i in range(1,4)],
    [f'bomber{i}' for i in range(6,9)],
    [f'lander{i}' for i in range(4,7)],
    [f'baiter{i}' for i in range(1,7)],
    'ship1', 'ship2',
    'ship3', 'ship4',   
    'littleship',
    'smartbomb',
    '2', '5', '0',
    '2', '5', '0',
    '500', '10', '00',
    '500', '10', '00', 
    [f'largefont{i}' for i in range(10)],
    '?',
    [f'largefont{i.upper()}' for i in 'abcdefghijklmnopqrstuvwxyz']]
      
    
# --- Configuration ---
SCREEN_WIDTH = 768  # Standard iPad portrait width
SCREEN_HEIGHT = 1024 # Standard iPad portrait height
JOYSTICK_DEAD_ZONE = 0.01
PLAYER_SPEED = 400
PLAYER_SIZE = 35
SPRITE_SCALE = 3
VERTICAL_SPEED = 10
PLAYER_FIRE_RATE = 0.1 # Seconds between shots
BULLET_SPEED = 700
MISSILE_SPEED = 350
SMARTBOMBS = 3
ENEMY_SPEED_MIN = 80
ENEMY_SPEED_MAX = 180
LANDER_ABDUCT_SPEED = 100 # Speed when carrying a human
HUMAN_FALL_SPEED = 300
SPRITE_CYCLE = 0.1

WORLD_WIDTH = 5000 # Large virtual world width (can be much larger)
PLAYER_SCREEN_X_CONSTRAINT = 0.3 # Player stays between 30% and 70% of screen width
PLAYER_SCREEN_X_MIN = SCREEN_WIDTH * PLAYER_SCREEN_X_CONSTRAINT
PLAYER_SCREEN_X_MAX = SCREEN_WIDTH * (1 - PLAYER_SCREEN_X_CONSTRAINT)

# UI
UI_TOP_MARGIN = 10
GROUND_Y_LEVEL = 0.1 # Percentage from bottom of screen

# --- Scanner Display Class ---
SCANNER_WIDTH = 500
SCANNER_HEIGHT = 150 # A wide, short rectangle
SCANNER_X = SCREEN_WIDTH / 2 # Centered horizontally
SCANNER_Y = SCREEN_HEIGHT  - SCANNER_HEIGHT / 2 - 20 # Below other UI, adjust as needed
SCANNER_PADDING = 10 # Padding inside the scanner border

SCANNER_PLAYER_COLOR = 'white' # White
SCANNER_ENEMY_COLOR = 'red'  # Red
SCANNER_HUMANOID_COLOR = 'green' # Green
SCANNER_ABDUCTED_HUMAN_COLOR = 'yellow' # Yellow (falling/abducted human)
# Enemy Spawning
MAX_ENEMIES_ON_SCREEN = 8
ENEMY_SPAWN_INTERVAL = 4.0 # How often to check for new spawns

# --- Asset Names (You MUST replace these with your own images for a good game) ---
PLAYER_IMAGE = 'player1a.png'
BULLET_IMAGE = 'spc:LaserRed8'
MISSILE_IMAGE = 'spc:LaserBlue16'
LANDER_IMAGE = 'spc:EnemyGreen2'
MUTANT_IMAGE = 'emj:Alien_Monster'
HUMAN_IMAGE = 'emj:Pedestrian' # Small human sprite


# --- Game Classes ---

class GameObject(SpriteNode):
    """Base class for all game entities that exist in the world."""
    def __init__(self, texture, world_position, game_scene, **kwargs):
        # We store world_position, and the actual screen position will be calculated by the World
        self.world_x = world_position.x
        self.world_y = world_position.y
        self.game_scene = game_scene # Reference to the main scene for adding/removing children
        super().__init__(texture, position=Point(0,0), parent=game_scene, **kwargs) # Position updated by World
        self.removed = False # Flag to mark if the object has been destroyed

    def update_screen_position(self, world_scroll_x):
        """Updates the sprite's screen position based on world scroll."""
        if not self.removed: # Only update if not removed
            self.position = Point(self.world_x - world_scroll_x, self.world_y)
     

    def is_offscreen(self):
        """Checks if the object is far off the visible screen based on world scroll."""
        if self.removed: return True # If already removed, consider offscreen
        
        # Calculate screen_x relative to the current visible viewport
        screen_x = self.world_x - self.game_scene.world.scroll_x
        
        # Determine the buffer zone based on screen width and sprite size
        # A sprite is off-screen if its entire width is past the left/right edge,
        # plus some extra buffer (e.g., its own width again)
        buffer_width = self.size.width * 2 # Or some other multiple if you want more buffer
        
        return screen_x < -buffer_width or screen_x > self.game_scene.size.width + buffer_width
               

    def destroy(self):
        """Removes the object from the scene and any tracking lists."""
        if not self.removed:
            self.remove_from_parent()
            self.removed = True
            
    def clip_bounds(self, world_x, world_y):
        # Simple bounds for all objects
        world_x = max(0, min(WORLD_WIDTH, world_x))
        world_y = max(self.size.y/8, min(self.game_scene.size.height - SCANNER_HEIGHT -self.size.y -50, world_y))
        return world_x, world_y
        
class ScannerDisplay(Node):
    def __init__(self, game_scene, world_manager, **kwargs):
        super().__init__(position=Point(SCANNER_X+SCANNER_WIDTH/2, SCANNER_Y), **kwargs)
        self.game_scene = game_scene
        self.world_manager = world_manager
        self.size = Size(SCANNER_WIDTH, SCANNER_HEIGHT)
        self.anchor_point = (0.5, 1.0) # Center aligned
        path=ui.Path.rect(0,0, *self.size)
        path.line_width = 5

        # Background for the scanner
        self.outline = ShapeNode(path=path, fill_color='#101010', size=self.size, parent=self, position=(0,0)) # Dark grey background
        self.outline.alpha = 0.7 # Semi-transparent
        self.outline.z_position = -0.1 # Just below the dots
        self.outline.stroke_color = 'blue'
        
        # Border (optional)
        path = ui.Path()
        path.move_to(0, 2*SCANNER_Y)
        path.line_to(SCREEN_WIDTH, 2*SCANNER_Y)
        path.line_width = 5
        self.border = ShapeNode(path, stroke_color='blue', parent=self, position=(0,-75))
        #self.border.z_position = -0.2 # Draw behind background

        # Calculate the playable area for dots within the scanner
        self.inner_width = self.size.width - SCANNER_PADDING * 2
        self.inner_height = self.size.height - SCANNER_PADDING * 2
        self.inner_left = -self.inner_width / 2
        self.inner_right = self.inner_width / 2
        self.inner_bottom = -self.inner_height / 2
        self.inner_top = self.inner_height / 2
        
        # add brackets
        for i in range(-1, 2, 2):
            path = ui.Path()
            path.move_to(0, 0)
            path.line_to(0, -i*10)
            path.line_to(50, -i*10)
            path.line_to(50, 0)
            path.line_width = 3
            ShapeNode(path=path, 
                      stroke_color='white', 
                      fill_color='clear',
                      position=(0, i*SCANNER_HEIGHT/2-i*5),
                      parent=self)
        

        # Create sub-nodes for each type of object to draw on the scanner
        # This helps manage them and clear them each frame
        self.player_dot = SpriteNode(color=SCANNER_PLAYER_COLOR, size=(5,5), parent=self)
        self.enemy_dots_layer = Node(parent=self)
        self.humanoid_dots_layer = Node(parent=self)
        path = self.game_scene.terrain.surface_path
        path.line_width = 1
        self.terrain = ShapeNode(path)   
        self.terrain.stroke_color = 'white'           
        self.terrain.fill_color = 'clear'        
        self.terrain.position=(0,-40)
        self.terrain.x_scale = SCANNER_WIDTH / path.bounds.w
        self.terrain.y_scale = 1        
        self.add_child(self.terrain)


    def update(self, dt):
        # Clear previous dots (except player's, which is a fixed sprite)
        self.game_scene.remove_all(self.enemy_dots_layer.children)
        self.game_scene.remove_all(self.humanoid_dots_layer.children)

        
        # TODO add brackets to show screen limits player_x +-683
        # TODO add terrain
        
        # Calculate scaling factor: how many world units per scanner pixel
        # We want the entire WORLD_WIDTH to fit into SCANNER_WIDTH
        world_to_scanner_scale = self.inner_width / self.world_manager.world_width

        # Player's position on scanner (fixed at center x)
        y = self.game_scene.player.world_y / 512 *SCANNER_HEIGHT/2 - SCANNER_HEIGHT/2
        self.player_dot.position = Point(0, y) # Relative to scanner's center (0,0)

        # Iterate through game entities and draw their dots
        # Enemies
        for enemy in self.game_scene.enemies:
            if enemy.removed: continue

            # Calculate relative world X position to player's world X
            # We want the enemy's position relative to the center of the world that the scanner represents
            # Which is player_world_x
            relative_world_x = enemy.world_x - self.world_manager.player_world_x
            relative_world_y = enemy.world_y #- self.world_manager.world_height/2
            
            # Scale this relative position to scanner coordinates
            scanner_x = relative_world_x * world_to_scanner_scale
            scanner_y = relative_world_y * world_to_scanner_scale -SCANNER_HEIGHT/2

            # Ensure dots stay within scanner bounds visually
            # This makes dots appear/disappear at the edges of the scanner
            if scanner_x < self.inner_left or scanner_x > self.inner_right:
                continue # Don't draw if outside scanner's visible range

            # Vertical position on scanner (simple - all enemies on one line)
            #scanner_y = self.inner_height / 4 # Place enemies in top quarter of inner height

            enemy_dot = SpriteNode(color=SCANNER_ENEMY_COLOR, size=(4,4), parent=self.enemy_dots_layer)
            enemy_dot.position = Point(scanner_x, scanner_y)


        # Humanoids
        for human in self.game_scene.humanoids:
            if human.removed: continue

            relative_world_x = human.world_x - self.world_manager.player_world_x
            relative_world_y = human.world_y #- self.world_manager.world_height/2
            scanner_x = relative_world_x * world_to_scanner_scale
            scanner_y = relative_world_y * world_to_scanner_scale -SCANNER_HEIGHT/2
            

            if scanner_x < self.inner_left or scanner_x > self.inner_right:
                continue # Don't draw if outside scanner's visible range

            human_color = SCANNER_HUMANOID_COLOR
            if human.abducted or human.falling:
                human_color = SCANNER_ABDUCTED_HUMAN_COLOR

            # Place humanoids slightly below enemies in the scanner
            #scanner_y = -self.inner_height / 4 # Place humanoids in bottom quarter of inner height

            human_dot = SpriteNode(color=human_color, size=(3,3), parent=self.humanoid_dots_layer)
            human_dot.position = Point(scanner_x, scanner_y)

class Player(GameObject):
    def __init__(self, world_position, game_scene):
        sprite = game_scene.sprites['ship2']
        #sprite = PLAYER_IMAGE
        super().__init__(sprite, world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.world_speed = 0 # Player's speed in world coordinates
        self.last_shot_time = 0.0
        
        self.lives = 3
        self.invincible_until = 0.0
        self.flash_interval = 0.1
        self._last_flash_time = 0.0
        self._visible_during_flash = True
        self.reverse = False
        self.smartbombs = SMARTBOMBS

    def update(self, dt):
        # Handle player's world speed based on touch input direction
        self.game_scene.world.set_player_world_speed(self.world_speed)
        match(self.reverse, self.world_speed != 0):
            case (True, True):
                ship = 'ship4'
            case (True, False):
                ship = 'ship3'
            case (False, True):
                ship = 'ship2'
            case (False, False):
                ship = 'ship1'
        self.texture = self.parent.sprites[ship]   
        self.scale = SPRITE_SCALE

        # Handle invincibility flashing
        if time.time() < self.invincible_until:
            if time.time() - self._last_flash_time > self.flash_interval:
                self._visible_during_flash = not self._visible_during_flash
                self.alpha = 1.0 if self._visible_during_flash else 0.3
                self._last_flash_time = time.time()
        else:
            self.alpha = 1.0
            self._visible_during_flash = True
            
        #self.world_x = self.world_x - self.game_scene.world.scroll_x
        self.position = Point(self.position.x, self.world_y)        
        self.world_x, self.world_y = self.clip_bounds(self.world_x, self.world_y)             

    def fire(self):
        current_time = time.time()        
        if current_time - self.last_shot_time >= PLAYER_FIRE_RATE:
            # Determine direction based on player's reverse state
            dir_x = -1  if self.reverse else 1
            
            # Calculate bullet's start position
            bullet_world_pos = Point()
            bullet_world_pos.x = self.parent.world.player_world_x + (self.size.width / 2) * dir_x
            bullet_world_pos.y = self.world_y # This is usually good enough for horizontal shots            
            
            # Pass the player's current 'reverse' state to the bullet so it knows its direction
            bullet = PlayerBullet(bullet_world_pos, self.game_scene, initial_reverse=self.reverse)
            self.game_scene.bullets.append(bullet)
            self.last_shot_time = current_time  
            sound.play_effect('arcade:Laser_1', 0.5)
                                

    def take_hit(self):
        if time.time() < self.invincible_until:
            return # Still invincible
        self.lives -= 1        
        sound.play_effect('arcade:Explosion_5') # Or a specific hit sound
        self.invincible_until = time.time() + 2.0 # 2 seconds invincibility
        self._last_flash_time = time.time() # Reset flash timer
        self._visible_during_flash = True # Start visible

        if self.lives <= 0:
            self.game_scene.game_over = True
            self.game_scene.restart()
            sound.play_effect('arcade:Powerup_2') # Game over sound


class PlayerBullet(GameObject):
    # Add initial_reverse parameter
    def __init__(self, world_position, game_scene, initial_reverse=False):
        super().__init__(BULLET_IMAGE, world_position, game_scene)
        self.scale = 0.5
        self.rotation = pi/2 # horizontal
        self.base_speed = BULLET_SPEED # Store base speed, direction will apply
        
        self.direction_x = -1 if initial_reverse else 1 # -1 for left, 1 for right
        self.speed_x = self.base_speed * self.direction_x                        
        # No vertical speed for horizontal bullets
        self.speed_y = 0

    def update(self, dt):
        # Move the bullet based on its calculated speed_x
        self.world_x += self.speed_x * dt       
        return self.is_offscreen() # Mark for removal if offsecreen      
        

class EnemyMissile(GameObject):
    def __init__(self, world_position, game_scene):
        super().__init__(MISSILE_IMAGE , world_position, game_scene)
        self.scale = 0.5
        self.speed = MISSILE_SPEED
        self.rotation = pi / 2
        self.reverse = game_scene.player.reverse

    def update(self, dt):
        if self.reverse:
           self.world_x -= self.speed * dt
           if self.world_x < self.game_scene.player.world_x -683: #self.game_scene.size.width - 50: # Off left screen
                return True # Mark for removal
        else:
            self.world_x += self.speed * dt
            if self.world_x > self.game_scene.player.world_x +683: #self.game_scene.size.width - 50: # Off right screen
                return True # Mark for removal
        return False

class Enemy(GameObject):
    def __init__(self, texture, world_position, game_scene, **kwargs):
        super().__init__(texture, world_position, game_scene, **kwargs)
        self.speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.target_humanoid = None
        self.state = 'IDLE' # 'IDLE', 'SEEKING_HUMAN', 'ABDUCTING', 'MUTATING', 'CHASING_PLAYER'
       
    def update(self, dt):
        # Base enemy movement (e.g., random wander or patrol)
        pass # To be overridden by specific enemy types
        
    def update_sprite(self, dt, update_rate=SPRITE_CYCLE):
        self.sprite_change -= dt
        if self.sprite_change <= 0:
           self.sprite_change = update_rate
           self.texture = self.parent.sprites[next(self.cycle)]
           self.scale = SPRITE_SCALE
           
    

class Pod(Enemy):
    # Pods collect as the game progresses. They have the highest
    # point value, and release Swarmers when hit.
    # The Pods, like the Bombers, are a passive enemy in that they
    # do not chase you or fire any weapons. They just float around.
    def __init__(self, world_position, game_scene):
        super().__init__(game_scene.sprites['pod1'], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.score = 1000
        self.sprite_change = SPRITE_CYCLE 
        
    def update(self, dt):
        if self.removed: return # Do nothing if removed

        # Aggressively chase the player
        player_world_x = self.game_scene.player.world_x
        player_world_y = self.game_scene.player.world_y

        if self.world_x < player_world_x:
            self.world_x += self.speed * dt
        elif self.world_x > player_world_x:
            self.world_x -= self.speed * dt

        if self.world_y < player_world_y:
            self.world_y += self.speed * dt
        elif self.world_y > player_world_y:
            self.world_y -= self.speed * dt

        self.world_x, self.world_y = self.clip_bounds(self.world_x, self.world_y)     
        
class Bomber(Enemy):
    # Bombers usually appear in sets of two or three but may
    # appear alone. They are actually sitting ducks. 
    # Bombers glide diagonally up or down the screen. They are
    # passive obstacles. They do not fire missiles but leave a very
    # active mine field in their wake. The mines cannot be de-
    # stroyed but eventually fade away.
    
    def __init__(self, world_position, game_scene):
        self.sprite_list = [f'bomber{i}' for i in range(1, 9)]
        self.cycle = cycle(self.sprite_list)
        super().__init__(game_scene.sprites[next(self.cycle)], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.score = 250
        self.sprite_change = 0
        
    def update(self, dt):
        if self.removed: return # Do nothing if removed
        self.update_sprite(dt, update_rate=0)
        # Aggressively chase the player
        player_world_x = self.game_scene.player.world_x
        player_world_y = self.game_scene.player.world_y

        if self.world_x < player_world_x:
            self.world_x += self.speed * dt
        elif self.world_x > player_world_x:
            self.world_x -= self.speed * dt

        if self.world_y < player_world_y:
            self.world_y += self.speed * dt
        elif self.world_y > player_world_y:
            self.world_y -= self.speed * dt

        self.world_x, self.world_y = self.clip_bounds(self.world_x, self.world_y)  
        
class Swarmer(Enemy):
    # Different numbers of Swarmers emerge from different Pods
    # when they are hit. There may only be 2, but even 6 or 7 or
    # more are possible. These Swarmers attack in a swarm and
    #are easier to hit than you think. They have their own unique
    #explosion sound track.

    def __init__(self, world_position, game_scene):
        self.sprite_list = ['swarmer1', 'swarmer2']
        self.cycle = cycle(self.sprite_list)
        super().__init__(game_scene.sprites[next(self.cycle)], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.score = 150
        self.sprite_change = SPRITE_CYCLE 
    
    def update(self, dt):
        if self.removed: return # Do nothing if removed
        self.update_sprite(dt)
        # Aggressively chase the player
        player_world_x = self.game_scene.player.world_x
        player_world_y = self.game_scene.player.world_y

        if self.world_x < player_world_x:
            self.world_x += self.speed * dt
        elif self.world_x > player_world_x:
            self.world_x -= self.speed * dt

        if self.world_y < player_world_y:
            self.world_y += self.speed * dt
        elif self.world_y > player_world_y:
            self.world_y -= self.speed * dt

        self.world_x, self.world_y =  self.clip_bounds(self.world_x, self.world_y)  
        
class Baiter(Enemy):
    # Baiters are troublesome; they can appear one after another
    # right in front of or behind you.
    # The Baiters interfere with your ability to only save Humanoids.
    #They zip across the screen right at you and act as an incen-
    # set y to player y
    
    def __init__(self, world_position, game_scene):
        self.sprite_list = [f'baiter{i}' for i in range(1, 7)]
        self.cycle = cycle(self.sprite_list)
        super().__init__(game_scene.sprites[next(self.cycle)], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.score = 200        
        self.sprite_change = SPRITE_CYCLE 
        self.speed = ENEMY_SPEED_MAX
        if self.world_x < self.game_scene.player.world_x: 
           dir = 1
        else: 
           dir = -1
        self.speed =  dir * ENEMY_SPEED_MAX * 1.5
    
    def update(self, dt):
        if self.removed: return # Do nothing if removed
        self.update_sprite(dt)
        # quickly speed towards player
        self.world_x += self.speed * dt                
        self.world_x, self.world_y = self.clip_bounds(self.world_x, self.world_y)  
        
          
class Lander(Enemy):
    def __init__(self, world_position, game_scene):
        self.sprite_list = [f'lander{i}' for i in range(1, 7)]
        self.cycle = cycle(self.sprite_list)
        super().__init__(game_scene.sprites[next(self.cycle)], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.captured_human = None
        self.abduction_point_y = game_scene.size.height * GROUND_Y_LEVEL + 20 # Just above ground
        self.score = 150                
        self.sprite_change = SPRITE_CYCLE 
        

    def update(self, dt):
        if self.removed: return # Do nothing if removed
        self.update_sprite(dt)

        if self.state == 'IDLE' or self.state == 'SEEKING_HUMAN':
            # Check if target_humanoid is valid and not removed
            if not self.target_humanoid or self.target_humanoid.removed or self.target_humanoid.abducted or self.target_humanoid.falling:
                # Find the nearest un-abducted, non-falling humanoid
                closest_human = None
                min_dist = float('inf')
                for human in self.game_scene.humanoids:
                    if not human.removed and not human.abducted and not human.falling:
                        dist = abs(self.world_x - human.world_x)
                        if dist < min_dist:
                            min_dist = dist
                            closest_human = human
                self.target_humanoid = closest_human

            if self.target_humanoid:
                self.state = 'SEEKING_HUMAN'
                # Move towards the human's X position
                if self.world_x < self.target_humanoid.world_x:
                    self.world_x += self.speed * dt
                elif self.world_x > self.target_humanoid.world_x:
                    self.world_x -= self.speed * dt

                # Move down to abduction height
                if self.world_y > self.abduction_point_y:
                    self.world_y -= self.speed * dt
                else:
                    self.world_y = self.abduction_point_y # Ensure it's exactly at ground level

            else: # No humanoids left, or none available, just wander
                # Simple horizontal wandering
                self.world_x += self.speed * random.choice([-1, 1]) * dt * 0.5
                self.world_y += self.speed * random.choice([-1, 1]) * dt * 0.1 # Slight vertical drift
                self.world_x = max(0, min(WORLD_WIDTH, self.world_x)) # Clamp to world bounds
                self.world_y = max(self.game_scene.size.height * 0.4, min(self.game_scene.size.height * 0.9, self.world_y))


        elif self.state == 'ABDUCTING':
            # TODO lander will shoot missile here
            # Ensure captured human is still valid
            if self.captured_human and not self.captured_human.removed:
                self.captured_human.world_x = self.world_x
                self.captured_human.world_y = self.world_y - self.size.height / 2 + self.captured_human.size.height / 2
                # Fly up to mutate
                self.world_y += LANDER_ABDUCT_SPEED * dt
                if self.world_y > self.game_scene.size.height * 0.95: # Reached top of screen to mutate
                    self.state = 'MUTATING'
                    self.game_scene.spawn_mutant(self.world_x, self.world_y)
                    self.captured_human.falling = True # Human drops
                    self.captured_human.abducted = False # No longer attached to lander
                    self.captured_human = None
                    self.destroy() # Lander is gone
            else: # Captured human was destroyed somehow, Lander reverts to seeking
                if self.captured_human: self.captured_human.abducted = False # Release if still exists
                self.captured_human = None
                self.state = 'IDLE' # Go back to seeking

class Mutant(Enemy):
    def __init__(self, world_position, game_scene):
        self.sprite_list = ['mutant1', 'mutant2']
        self.cycle = cycle(self.sprite_list)
        super().__init__(game_scene.sprites[next(self.cycle)], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.speed = ENEMY_SPEED_MAX * 1.5 # Faster than Landers
        self.score = 150
        self.sprite_change = SPRITE_CYCLE 
        
    def update(self, dt):
        if self.removed: return # Do nothing if removed
        self.update_sprite(dt)
        # Aggressively chase the player
        player_world_x = self.game_scene.player.world_x
        player_world_y = self.game_scene.player.world_y

        if self.world_x < player_world_x:
            self.world_x += self.speed * dt
        elif self.world_x > player_world_x:
            self.world_x -= self.speed * dt

        if self.world_y < player_world_y:
            self.world_y += self.speed * dt
        elif self.world_y > player_world_y:
            self.world_y -= self.speed * dt
        self.world_x, self.world_y = self.clip_bounds(self.world_x,self.world_y)  

                
class Humanoid(GameObject):
    def __init__(self, world_position, game_scene):
        super().__init__(game_scene.sprites['humanoid1'], world_position, game_scene)
        self.scale = SPRITE_SCALE
        self.abducted = False
        self.falling = False
        self.rescued = False
        self.ground_level_y = game_scene.size.height * GROUND_Y_LEVEL + self.size.height / 2

    def update(self, dt):
        if self.removed: return # Do nothing if removed

        if self.falling and not self.rescued:
            self.world_y -= HUMAN_FALL_SPEED * dt
            if self.world_y <= self.ground_level_y:
                self.world_y = self.ground_level_y
                self.falling = False
                # Human hit ground - remove or lose points
                if not self.rescued:
                    self.destroy()
                    # It's safer to remove from game_scene.humanoids in the main loop
                    # when iterating to avoid modifying list while iterating.
                    sound.play_effect('arcade:Jump_2') # Sound for lost human

    def destroy(self):
        super().destroy()


class WorldManager:
    """Manages the scrolling of the game world."""
    def __init__(self, scene_size, world_width, player_screen_min_x, player_screen_max_x):
        self.scene_size = scene_size
        self.world_width = world_width
        self.player_screen_min_x = player_screen_min_x
        self.player_screen_max_x = player_screen_max_x

        self.scroll_x = 0 # Current left-most world X displayed on screen
        self.player_world_x = world_width / 2 # Player's actual position in the vast world
        self.player_screen_x = scene_size.width / 2 # Player's visible screen position

        self._player_world_speed = 0 # How fast the player is trying to move in world coords

    def set_player_world_speed(self, speed):
        self._player_world_speed = speed

    def update(self, dt):
        # Update player's world position
        self.player_world_x += self._player_world_speed * dt

        # Clamp player's world position within world bounds
        self.player_world_x = max(self.scene_size.width / 2, min(self.world_width - self.scene_size.width / 2, self.player_world_x))

        # Adjust scroll_x to keep player within screen constraints
        target_scroll_x = self.player_world_x - self.player_screen_x # Ideal scroll position
        
        # Clamp scroll_x to world limits
        min_scroll_x = 0
        max_scroll_x = self.world_width - self.scene_size.width
        self.scroll_x = max(min_scroll_x, min(max_scroll_x, target_scroll_x))
        #print(self.scroll_x, self.player_world_x)

class Terrain(GameObject):
   def __init__(self, game_scene):
        self.game_scene = game_scene   
        self.landscape =  self.generate_planet_surface(height=50, num_points=1024, offset=None, dup=3)      
        
   def convert_to_line(self, landscape_array, startx=0, endx=None):
        # take the array or part of the array
        # startx and endx are in world coordinates
        inc_x = WORLD_WIDTH / len(landscape_array)
        if endx is None:
           end = len(landscape_array)  
        else:
           end = int(endx / inc_x)    
        
        start = int(startx / inc_x)
        path = ui.Path()
        path.line_width = 1
        
        path.move_to(start, landscape_array[start])        
        for x in range(start + 1, end):
            path.line_to(x, landscape_array[x])
                
        # Create line node from path
        self.surface_path = path
        self.surface = ShapeNode(path=self.surface_path, 
                                 position=(0, 100),
                                 stroke_color='white',
                                 fill_color='clear',
                                 x_scale=2*WORLD_WIDTH / len(landscape_array),
                                 y_scale=5,
                                 #size=(1000, 100),
                                 parent=self.game_scene)      
      
        
   def terrain_height(self, x):
       return self.landscape[int(x * len(self.landscape)/WORLD_WIDTH)]
        
   def generate_planet_surface(self, height, num_points=100, offset=None, dup=1):
        # TODO Math.cos(iteration / 5 & -11) produced a reasonably rugged mountain range while appearing to wrap infinitely:
        random.seed(100)
        surface_points = []
        # Simple random walk for terrain height
        current_y = height / 4        
        for i in range(num_points):
            surface_points.append(current_y)
            if i % dup == 0:
               current_y += random.uniform(-height/6, height/6) # Random elevation change
               
            if current_y < 0: current_y = 0
            if current_y > height / 2: current_y = height / 2        
        return surface_points    
    

# Main Game Scene

class DefenderGame(Scene):
    def setup(self):
        self.paused = True
        self.background_color = 'black' # Black space
        self.score = 0
        self.game_over = False
        
        w, h = get_screen_size()
        self.world = WorldManager(self.size, WORLD_WIDTH, PLAYER_SCREEN_X_MIN, PLAYER_SCREEN_X_MAX)
        self.joystick = Joystick((w-200, 200), color='red', alpha=.8, show_xy=True, msg='')
        self.get_sprites(NAME)
        
        self.moved = False
        self.add_child(self.joystick)
        # Player Setup
        initial_player_world_pos = Point(self.world.player_world_x, self.size.height * 0.2)
        self.player = Player(initial_player_world_pos, self)
        # Set player's screen position initially (doesn't move relative to screen center)
        self.player.position = Point(self.world.player_screen_x, initial_player_world_pos.y)

        # Game Object Lists 
        self.live_sprites = []
        self.score_sprites = []
        self.smartbomb_sprites = []
        self.bullets = [] # Player bullets
        self.enemies = [] # Landers, Mutants, etc.
        self.humanoids = [] # Humans on the ground
        self.explosions = [] # For explosion animations (not implemented yet)
        
        
        self.terrain = Terrain(self)        
        self.terrain.convert_to_line(self.terrain.landscape, self.world.scroll_x, self.world.scroll_x+683*2)                
        
        # Humanoid Spawning
        self.initial_humanoid_count = int(WORLD_WIDTH / 150) # Roughly one human every 150 world units
        for _ in range(self.initial_humanoid_count):
            human_world_x = random.uniform(0, WORLD_WIDTH)
            human_world_y = self.terrain.terrain_height(human_world_x) + self.size.height * GROUND_Y_LEVEL /2 + 10
            #human_world_y = self.size.height * GROUND_Y_LEVEL + 20 # Just above the ground
            human = Humanoid(Point(human_world_x, human_world_y), self)
            self.humanoids.append(human)
            
        # UI Layers and Labels ---
        # Create a dedicated UI layer so scanner and labels always draw on top
        self.ui_layer = Node(parent=self)
        self.ui_layer.z_position = 100 # Ensure it's drawn on top of game objects
 
        self.scanner_display = ScannerDisplay(self, self.world)
        self.ui_layer.add_child(self.scanner_display) # Add scanner to UI layer
        self.ship_pos = LabelNode(f'{self.player.position}', 
                                  position=(self.size.width*0.85, self.size.height-UI_TOP_MARGIN),
                                  parent=self.ui_layer)
        self.display_lives()
        self.display_smartbombs()
        self.display_score()
                
        # Spawning Logic
        self.last_enemy_spawn_time = time.time()
        self.paused = False
    
    @ui.in_background 
    def restart(self):
      response = console.alert('', message='Game Over', button1='Restart', button2='Quit')
      if response == 1:       
          self.remove_all(self.children)  
          self.setup()
      else:
          self.view.close()
           
    def get_sprites(self, filename):
       global sprite_names
       sorted_boxes, sprite_names =  spritesheet.separate_irregular_sprites(filename,
                               background_color=(0, 0, 0),
                               use_alpha=False, sprite_names=sprite_names, display=False)
       all_sprites = Texture(filename)
       W, H = all_sprites.size
       self.sprites = defaultdict()
       for k, name in zip(sorted_boxes, sprite_names):
           x1, y1, x2, y2 =  k         
           img = all_sprites.subtexture((x1/ W, (H-y2) / H, (x2-x1)/ W, (y2-y1) / H))          
           self.sprites[name] = img
    
    def remove_all(self, items):
        # remove all nodes in items
        try:
            for item in items:
                item.remove_from_parent()
        except AttributeError:
            pass  
                    
    def display_lives(self):
      # display lives a ship sprites
      self.remove_all(self.live_sprites)
      self.live_sprites = [SpriteNode(self.sprites['ship1'], 
                                      position=(i*64+100,  self.size.height-50), 
                                      scale=2,
                                      parent=self) 
                           for i in range(self.player.lives)]                           
    
    def display_smartbombs(self):
      # display lives a ship sprites      
      self.remove_all(self.smartbomb_sprites)                 
      self.smartbomb_sprites = [SpriteNode(self.sprites['smartbomb'], 
                                      position=(300,  self.size.height-50-i*16), 
                                      scale=2,
                                      parent=self) 
                           for i in range(self.player.smartbombs)]
                           
    def display_score(self):  
        self.remove_all(self.score_sprites)    
        self.score_sprites = [SpriteNode(self.sprites[f'largefont{n}'], 
                                      position=(i*(self.sprites[f'largefont{n}'].size.x+2)+100,  self.size.height-100), 
                                      scale=2,
                                      parent=self) 
                               for i, n in enumerate(str(self.score))]                                                                                 

    def update(self):
        dt = self.dt
        if self.game_over:
            # Check for restart touch
            if self.touches and len(self.touches) > 0:
                self.setup() # Simple restart
            return
        self.joystick.update()
        
        self.world.update(dt)
        if self.player.world_speed != 0:
            self.terrain.surface.remove_from_parent()
            self.terrain.convert_to_line(self.terrain.landscape , self.world.scroll_x, self.world.scroll_x+683*2)
 
        self.player.update(dt)
        # Player's actual position on screen is fixed, but its world_x updates in WorldManager
        # We only need to set its screen position once in setup, it stays there.
        
        self.scanner_display.update(dt)
        self.ship_pos.text = f'world x,y {int(self.world.player_world_x)}, {int(self.player.world_y)} scroll={int(self.world.scroll_x)}'
        # Update and Position Game Objects
        # Collect items to remove after iteration
        bullets_to_remove = []
        enemies_to_remove = []
        humanoids_to_remove = []

        # Bullets
        for bullet in self.bullets:
            if bullet.removed: continue # Skip if already marked for removal
            if bullet.update(dt) or bullet.is_offscreen(): # Update and check if off-screen
                bullets_to_remove.append(bullet)
            else:
                bullet.update_screen_position(self.world.scroll_x)

        # Enemies
        for enemy in self.enemies:
            enemy.update(dt)
            enemy.update_screen_position(self.world.scroll_x)
            # Remove enemies that went too far off-screen (e.g. if they randomly wander far away)
            if enemy.is_offscreen(): # Could make this more specific for different enemy types
                enemies_to_remove.append(enemy)


        # Humanoids
        for human in self.humanoids:
            human.update(dt)
            human.update_screen_position(self.world.scroll_x)
            if human.removed: # Humanoid decided to remove itself (e.g., hit ground)
                humanoids_to_remove.append(human)


        # Collision Detection
        bullets_to_remove_after_hit = [] # Bullets that hit something

        # Player Bullet vs. Enemy
        for bullet in self.bullets:
            if bullet.removed: continue # Skip if already marked for removal
            for enemy in self.enemies:
                if enemy.removed: continue # Skip if already marked for removal                
                if bullet.bbox.intersects(enemy.bbox):
                    sound.play_effect('arcade:Explosion_1', 0.8)
                    enemies_to_remove.append(enemy)
                    bullets_to_remove_after_hit.append(bullet)
                    self.score += enemy.score # Adjust points for different enemies
                    self.display_score()
                    # If Lander with human, make human fall
                    if isinstance(enemy, Lander) and enemy.captured_human:
                        # Ensure captured_human isn't already removed
                        if not enemy.captured_human.removed:
                            enemy.captured_human.falling = True
                            enemy.captured_human.abducted = False
                        enemy.captured_human = None # Clear reference from lander
                    break # Bullet hits only one enemy

        # Player vs. Enemy
        for enemy in self.enemies:
            if enemy.removed: continue
                        
            if self.player.bbox.intersects(enemy.bbox):
                self.player.take_hit()
                self.display_lives()
                
                enemies_to_remove.append(enemy) # Mark enemy for removal
                break # Player can only be hit by one enemy at a time

        # Lander vs. Humanoid (Abduction)
        # Iterate over a copy to avoid issues if 'self.enemies' is modified
        for lander in [e for e in self.enemies if isinstance(e, Lander) and e.state == 'SEEKING_HUMAN' and not e.removed]:
            for human in self.humanoids:
                # FIX 2: Check human.removed, human.abducted, human.falling before trying to abduct
                if not human.removed and not human.abducted and not human.falling:
                    
                    if lander.bbox.intersects(human.bbox):
                        lander.captured_human = human
                        human.abducted = True
                        lander.state = 'ABDUCTING'
                        sound.play_effect('arcade:Powerup_2') # Abduction sound
                        break # Lander can only abduct one human

        # Player vs. Falling Humanoid (Rescue)
        for human in [h for h in self.humanoids if h.falling and not h.rescued and not h.removed]:
            
            if self.player.bbox.intersects(human.bbox):
                human.rescued = True
                humanoids_to_remove.append(human) # Mark for removal
                self.score += 250 # Rescue bonus
                self.display_score()
                sound.play_effect('arcade:Jump_4') # Rescue sound


        # Clean up removed objects
        for bullet in bullets_to_remove_after_hit:
            if not bullet.removed: # Ensure it hasn't been removed (e.g., if off-screen)
                bullet.destroy()
                self.bullets = [b for b in self.bullets if not b.removed]
        for bullet in bullets_to_remove: # Bullets that went off screen
            if not bullet.removed:
                bullet.destroy()
                self.bullets = [b for b in self.bullets if not b.removed]
                
        for enemy in enemies_to_remove:
            if not enemy.removed:
                enemy.destroy()               
                self.enemies = [e for e in self.enemies if not e.removed]
  
        for human in humanoids_to_remove:
            if not human.removed:
                human.destroy()
                self.humanoids = [h for h in self.humanoids if not h.removed]


        # Enemy Spawning
        current_time = time.time()
        active_enemies_count = len([e for e in self.enemies if not e.removed]) # Count only active enemies
        if active_enemies_count < MAX_ENEMIES_ON_SCREEN and current_time - self.last_enemy_spawn_time > ENEMY_SPAWN_INTERVAL:
            spawn_world_x = self.world.player_world_x + random.uniform(-self.size.width * 0.8, self.size.width * 0.8)
            spawn_world_x = max(0, min(WORLD_WIDTH, spawn_world_x)) # Clamp to world bounds
            spawn_world_y = random.uniform(self.size.height * 0.7, self.size.height * 0.9) # Spawn high up                  

            # Decide what to spawn
            # Ensure there are still humanoids to abduct before spawning Landers
            active_humanoids = [h for h in self.humanoids if not h.removed and not h.abducted and not h.falling]
                                                
            alien = random.choices(['lander', 'mutant', 'pod', 'bomber', 'baiter'], k=1, weights=[7, 3, 1, 1, 4])[0]
            match alien:
                case 'lander':      
                    if len(active_humanoids) > 0:      
                        new_enemy = Lander(Point(spawn_world_x, spawn_world_y), self)
                case 'mutant':           
                    new_enemy = Mutant(Point(spawn_world_x, spawn_world_y), self)
                case 'pod':           
                    new_enemy = Pod(Point(spawn_world_x, spawn_world_y), self)
                case 'bomber':           
                    new_enemy = Bomber(Point(spawn_world_x, spawn_world_y), self)
                case 'baiter':           
                    new_enemy = Baiter(Point(spawn_world_x, self.player.world_y), self)

            self.enemies.append(new_enemy)
            self.last_enemy_spawn_time = current_time

    def spawn_mutant(self, world_x, world_y):
        mutant = Mutant(Point(world_x, world_y), self)
        self.enemies.append(mutant)
        sound.play_effect('arcade:Coin_2') # Or a specific mutation sound

    def touch_began(self, touch):
        self.moved = False
        if self.game_over:
            # Game over restart handled in update, but touch_began here is cleaner
            return
        if self.joystick.bbox.contains_point(touch.location):       
             self.joystick.touch_began(touch)        
        self.player.fire()   

    def touch_moved(self, touch):
        self.moved = True
        if self.game_over:
            return
        self.joystick.touch_moved(touch)      
        if self.joystick.x < -JOYSTICK_DEAD_ZONE:
            self.player.world_speed = PLAYER_SPEED * self.joystick.x * 2     
            self.player.reverse = True      
        elif self.joystick.x > JOYSTICK_DEAD_ZONE:
            self.player.world_speed = PLAYER_SPEED * self.joystick.x * 2
            self.player.reverse = False      
           
        if self.joystick.y < -JOYSTICK_DEAD_ZONE:           
            self.player.world_y -= VERTICAL_SPEED 
        elif self.joystick.y > JOYSTICK_DEAD_ZONE:           
            self.player.world_y += VERTICAL_SPEED

    def touch_ended(self, touch):
        # Stop player movement when touch ends
        self.joystick.touch_ended(touch)
        # Player fires when joystick is touched and not moving
        if not self.moved:
            self.player.fire()            
        self.player.world_speed = 0
                

# Run the Game
if __name__ == '__main__':
    # Use actual screen dimensions for the device if possible, or common iPad sizes
    # For a fixed screen, you can specify dimensions directly
    run(DefenderGame(), PORTRAIT, show_fps=True) # show_fps is useful for debugging performance
