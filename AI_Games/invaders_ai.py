# Simple Galaxian game for Pythonista using the scene module
# i am going to try to make this as accurate as possible
# - add more accurate flight paths
# - react to loss of flagship
# flagship flees to next wave (max 2)
# get more aggressive as wave increases.
# get more chargers as wave increases ( max 7 at any one time)

import scene
import random
import math
from scene import Texture
import ui
from operator import attrgetter
from time import sleep

# --- Game Constants ---
SCREEN_WIDTH = 768
SCREEN_HEIGHT = 1024
PLAYER_SPEED = 300
PLAYER_SHOOT_COOLDOWN = 0.5

CONVOY_SPEED = 60
DIVE_SPEED = 300
RETURN_SPEED = 150
BULLET_SPEED = 250
ROWS = 5
COLUMNS = 10
SPACING_X = 70 # Spacing between invaders in convoy
SPACING_Y = 60 # Spacing between invaders in convoy
START_Y = SCREEN_HEIGHT - 120 # Starting Y position for invader convoy
CONVOY_MOVE_DIRECTION = 1 # 1 for right, -1 for left
CONVOY_MOVE_DOWN_AMOUNT = 0 # the convoy does mot move down
CONVOY_MOVE_INTERVAL = 1.5 # Time before invaders change direction/move down
INVADER_MOVE_INTERVAL = 0.3 # Time before invaders change image

BULLET_SIZE = 10
INVADER_BULLET_SPEED = 250
PLAYER_SIZE = 80
INVADER_SIZE = 70
INVADER_BULLET_SIZE = 15

# Invader states
STATE_CONVOY = 'convoy'
STATE_CHARGER = 'charging'
STATE_RETURNING = 'returning'

LIVES = 3
  
# --- Game Classes ---

class Player(scene.SpriteNode):
    def __init__(self, position=(SCREEN_WIDTH/2, 150), **kwargs):
        # Use a simple shape or color for the player (can replace with image)
        super().__init__('ship.png', position=position, size=(PLAYER_SIZE, PLAYER_SIZE), **kwargs)
        self.speed = PLAYER_SPEED
        self.can_shoot = True
        self._shoot_timer = 0
        self.lives = LIVES

    def update(self, dt):
        # Handle shooting cooldown
        if not self.can_shoot:
            self._shoot_timer += dt
            if self._shoot_timer >= PLAYER_SHOOT_COOLDOWN:
                self.can_shoot = True
                self._shoot_timer = 0

    def move(self, direction, dt):
        # Move the player left or right
        new_x = self.position.x + direction * self.speed * dt
        # Clamp the player position within screen bounds
        self.position = (max(PLAYER_SIZE/2, min(SCREEN_WIDTH - PLAYER_SIZE/2, new_x)), self.position.y)

    def shoot(self):
        # Create and return a new player bullet sprite
        if self.can_shoot:
            bullet = PlayerBullet(position=(self.position.x, self.position.y + PLAYER_SIZE/2))
            self.can_shoot = False
            return bullet
        return None

class Invader(scene.SpriteNode):
 
    def __init__(self, position, convoy_position, invader_type, location=None, **kwargs):
        
        scores = {'Blue': 30, 'Purple': 40, 'Red': 50, 'Flagship': 60}
        self.types = {'Blue': [Texture('galax1a.png'), Texture('galax1b.png')], 
                      'Purple': [Texture('galax2a.png'), Texture('galax2b.png')], 
                      'Red': [Texture('galax3a.png'), Texture('galax3b.png')], 
                      'Flagship': [Texture('galax5.png'), Texture('galax5.png')]}
        
        
        self.alien_type = random.randint(0,1)
        shape = self.types[invader_type][self.alien_type]

        super().__init__(shape, position=position,color='white', size=(INVADER_SIZE, INVADER_SIZE), **kwargs)
        self.convoy_position = convoy_position # Original position in convoy
        self.invader_type = invader_type
        self.state = STATE_CONVOY
        self.started_charge = False
        self.alien_timer = INVADER_MOVE_INTERVAL 
        self.charge_target = None # Player position when charge started
        self.return_target = None # Position to return to in convoy
        self.escort = 0 # escort 1, 2 or 0
        self.score_value = scores[invader_type] # Basic scoring based on type

           
    def normalize(self, a):
         # convert to -1, 0, 1
         return scene.Point(*tuple([0 if x == 0 else int(x/abs(x)) for x in a]))
         
    def distance(self, point_a, point_b):
        return math.hypot(*(point_a - point_b))
        
    def bezier_curve(self, p0, p1, p2, p3, p4,  t, pz=1.0):
        """Quartic Bézier curve function.
      Args:
          all p are numpy array(x,y)
          p0 and p4 are the start and end points of the curve.
          p1 and p3 are the control points that define the shape and curvature of the line.          
          p2 controls the flatness
          t is a parameter that varies from 0 to 1, tracing the curve.
             
             p1
                   p2      
                          p3            
           p0      |        p4
        """
        
        return (1 - t)**4 * p0 + 4 * (1 - t)**3 *t * p1 + 6 * (1 - t)**2 * t**2 * p2 + 4*t**3 * (1-t) * p3 + t**4 * p4
            
    def charger_logic(self, dt):
        # TODO Modify attack strategies for each type
        # use bezier curves to mimic original
        # original had some rotation also
        escort_offset = {0: scene.Point(0, 0), 1: scene.Point(0, -SPACING_Y), 2: scene.Point(SPACING_X*.75, -SPACING_Y)}
        # move vector is set at beginning only
        if self.started_charge:
            self.move_vector = self.normalize(self.charge_target - self.position)
            self.started_charge = False
        match self.invader_type:
            case 'Blue':
                # When they charge, their maneuvers tend to be fairly simple
                # leave the convoy (takes roughly a second);
                # orient themselves on your position *after* that;
                # move in your direction at a set angle which isn't very wide;
                # typically drop 3 or 4 shots, which move in the same direction the alien does;
                # cannot turn around once their maneuver has begun;
                self.position = self.position + self.move_vector * DIVE_SPEED * dt
                #self.rotation = math.pi/2
            case 'Purple':
                # move at much wider angles and also tend to turn around during their descend,
                #- slow down about halfway their maneuver and then turn in the other direction;
                #- will always perform this turn regardless of where your craft is;
                #- typically fire 4 shots, one or two of which fall during their turning point;
                #- aim all their shots in the direction they initially turned in;
                # - usually stop firing after they make their turn;
                self.position = self.position + self.move_vector * DIVE_SPEED * dt
                #print(self.invader_type, self.position)
            case 'Red':
                # on their own
                # maneuvers which are not as wide as those of the purple Galaxians, but more erratic and harder to predict
                # need know escort=1, escort=2 or single escort=0            
                if self.parent.flagship: # formate on flagship                                       
                    self.position = self.parent.flagship.position + escort_offset[self.escort]
                else:
                    self.position = self.position + self.move_vector * DIVE_SPEED * dt  
            case 'Flagship':                
                self.position = self.position + self.move_vector * DIVE_SPEED * dt
                
        
    def gone_offscreen(self):
       # trigger offscreen if charging and below convoy
       if self.bbox.min_y > self.parent.convoy_base:
          return False
       if self.bbox.min_y <= INVADER_SIZE/2:
          return True
       if self.bbox.min_x <= 0 or self.bbox.max_x > SCREEN_WIDTH:
          return True
       return False
                   
        
    def update(self, dt, convoy_move_direction):
        # Update convoy position based on horizontal movement
        self.convoy_position = (self.convoy_position[0] + convoy_move_direction * CONVOY_SPEED * dt, self.convoy_position[1])
        if self.state == STATE_CONVOY:
            # Move horizontally in convoy
            self.position = (self.position.x + convoy_move_direction * CONVOY_SPEED * dt, self.position.y)
            
            
        elif self.state == STATE_CHARGER:
            # Move towards the charge target (player position when charge started)            
            if self.charge_target:
                self.charger_logic(dt)
                # Check if invader is off-screen or passed the player
                if self.gone_offscreen():                    
                    # If off-screen after charging, remove it (or make it return)
                    self.start_return()
                    return True # Indicate removal

        elif self.state == STATE_RETURNING:
            # Move back towards convoy position
            # appear at top and move down  to original position
            if self.return_target:
                # Simple linear return for now
                self.position = (self.position.x, self.position.y - RETURN_SPEED * dt)

                # Check if invader is close to convoy position
                if self.distance(self.position, self.convoy_position) < INVADER_SIZE*2: # Threshold
                    self.position = self.convoy_position # Snap to position
                    self.state = STATE_CONVOY # Return to convoy state
                    
        self.alien_timer -= dt
        if self.alien_timer <= 0:
              self.alien_timer = INVADER_MOVE_INTERVAL 
              self.alien_type = not self.alien_type
              self.texture = self.types[self.invader_type][self.alien_type]
              self.size=(INVADER_SIZE, INVADER_SIZE)
        return False # Indicate not removed

   
    def start_charge(self, target_position):
        # Start the charging attack
        self.state = STATE_CHARGER
        self.started_charge = True
        self.charge_target = target_position
        # Remove from the main invaders list in the game scene to avoid convoy logic
        if self in self.parent.convoy:
            self.parent.convoy.remove(self)

    def start_return(self):
        # Start returning to convoy
        self.state = STATE_RETURNING
        self.return_target = scene.Point(*self.convoy_position)
        # position at top of screen in line with convoy position
        self.position = scene.Point(self.return_target.x, SCREEN_HEIGHT - 50)
        # Add back to the main convoy list in the game scene
        if self not in self.parent.convoy:
             self.parent.convoy.append(self)


class PlayerBullet(scene.SpriteNode):
    def __init__(self, position, **kwargs):
        # Use a simple shape or color for the player bullet
        super().__init__('spc:Fire19', position=position, color='#ffff00', size=(BULLET_SIZE, BULLET_SIZE), **kwargs)
        self.speed = BULLET_SPEED

    def update(self, dt):
        # Move the bullet upwards
        self.position = (self.position.x, self.position.y + self.speed * dt)

class InvaderBullet(scene.SpriteNode):
    def __init__(self, position, **kwargs):
        # Use a simple shape or color for the invader bullet
        super().__init__('spc:BoltBronze', position=position, size=(INVADER_BULLET_SIZE, INVADER_BULLET_SIZE), **kwargs)
        self.speed = INVADER_BULLET_SPEED

    def update(self, dt):
        # Move the bullet downwards
        self.position = (self.position.x, self.position.y - self.speed * dt)


# --- Main Game Scene ---

class Game(scene.Scene):
    def setup(self):
        for child in self.children:
          child.remove_from_parent()
        # Set up the game scene
        self.background_color = '#000000' # Black background
        # Add a starry background (simple dots)
        self.stars = []
        for _ in range(100):
            star_size = random.uniform(1, 3)
            star_position = (random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT))
            star = scene.SpriteNode('spc:Star2', position=star_position, color='#ffffff', size=(star_size, star_size))
            self.add_child(star)
            self.stars.append(star)


        # Create player
        self.player = Player()
        self.add_child(self.player)

        # Create invaders in convoy
        self.convoy = [] # Invaders currently in convoy
        self.charging_invaders = [] # Invaders currently charging/returning
        self.invader_move_direction = CONVOY_MOVE_DIRECTION
        self.invader_convoy_move_timer = 0 # Timer to control invader horizontal movement
        self.invader_convoy_move_interval = CONVOY_MOVE_INTERVAL

        self.invader_charge_timer = 0 # Timer to control when invaders charge
        self.invader_charge_interval = 3.0 # Time before an invader might charge
        self.reset_wave()
                   
        self.convoy_base = min(self.convoy, key=lambda inv: inv.position.y).position.y
        self.flagship = None
        # List to hold active bullets
        self.player_bullets = []
        self.invader_bullets = []

        # Player movement state
        self.moving_left = False
        self.moving_right = False

        # Score
        self.score = 0
        self.score_label = scene.LabelNode(str(self.score), font=('Press Start 2P', 30), position=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 50), color='#ffffff')
        self.add_child(self.score_label)

        # Game state
        self.game_over = False
        self.game_over_label = None
        
        # Waves
        self.wave = 1
        self.wave_flags = [scene.SpriteNode('emj:Triangular_Flag', position=(800, 50), parent=self)]
        # Load sounds (replace with actual sound files if you have them)
        # scene.play_effect('arcade:Explosion_1') # Example sound effect
        # lives
        self.lives = LIVES
        self.life_icon = [None] * LIVES
        for life in range(self.lives):
         self.life_icon[life] = scene.SpriteNode('ship.png', size=(50,50), position=(50+60*life, 50), parent=self)
         
    def reset_wave(self): 
        for child in self.children:
          if isinstance(child,  Invader):
              child.remove_from_parent()  
              
        invader_locs = {'Blue': [(5-r, c) for c in range(COLUMNS) for r in range(3)], 
                        'Purple': [(2, c+1) for c in range(COLUMNS-2)],
                        'Red': [(1, c+2) for c in range(COLUMNS-4)],
                        'Flagship': [(0, 3), (0, COLUMNS-4)]
                        }
        for type, locs in invader_locs.items():
            for loc in locs:
                row, col = loc            
                # Calculate convoy position
                convoy_x = (col - COLUMNS / 2 + 0.5) * SPACING_X + SCREEN_WIDTH / 2
                convoy_y = START_Y - row * SPACING_Y
                convoy_position = (convoy_x, convoy_y)

                invader = Invader(position=convoy_position, convoy_position=convoy_position, invader_type=type)
                self.add_child(invader)
                self.convoy.append(invader)
            
    def select_invader_type(self, invader_type):
        # return subset of convoy invaders which match invader_type
        return [invader for invader in self.convoy if invader.invader_type == invader_type]   
            
    def select_charger(self):
        # select either blue or purple or flagship
        # find leftmost& backmost and rightmost& backmost                    
        charger = random.choices(['Blue', 'Purple', 'Flagship'], weights=(10,10,3),  k=1)[0]
        
        if charger == 'Flagship' and self.select_invader_type(charger) is None:
            self.flagship = None
            charger = 'Red'
        escorts = []
        leftright = random.choice([False, True])
        match charger:
            case 'Blue' | 'Purple' | 'Red':
                # Find the outside and rearmost invaders in convoy of selected type
                invaders = sorted(self.select_invader_type(charger), key=attrgetter('position.y'), reverse=True)
                invaders = sorted(invaders, key=attrgetter('position.x'), reverse=leftright)
                if invaders:
                   invader = invaders[0]
                   invader.escort = 0 # just for Red
                else:
                  return None, []
             
            case 'Flagship':
                invaders = self.select_invader_type(charger)
                invaders = sorted(invaders, key=attrgetter('position.x'), reverse=leftright)
                if invaders:
                   invader = invaders[0]
                   self.flagship = invader
                   # escorts
                   escorts = self.select_invader_type('Red')
                   if escorts:
                       # get max 2 escorts
                       escorts = sorted(escorts, key=attrgetter('position.x'), reverse=leftright)[:2]
                else:
                  return None, []                               
        return invader, escorts
     
    def update(self):
        if self.game_over:
            return # Stop updating if game is over

        # --- Player Update ---
        self.player.update(self.dt)
        move_direction = 0
        if self.moving_left:
            move_direction -= 1
        if self.moving_right:
            move_direction += 1
        self.player.move(move_direction, self.dt)

        # --- Invader Convoy Movement ---
        self.invader_convoy_move_timer += self.dt
        if self.invader_convoy_move_timer >= self.invader_convoy_move_interval:
            self.invader_convoy_move_timer = 0

            # Check if invaders in convoy hit screen edge
            hit_edge = False
            if self.convoy: # Only check if there are invaders in convoy
                # Find the leftmost and rightmost invaders in convoy
                leftmost_invader = min(self.convoy, key=lambda inv: inv.position.x)
                rightmost_invader = max(self.convoy, key=lambda inv: inv.position.x)

                if leftmost_invader.position.x <= INVADER_SIZE/2 or rightmost_invader.position.x >= SCREEN_WIDTH - INVADER_SIZE/2:
                    hit_edge = True

            if hit_edge:
                self.invader_move_direction *= -1 # Reverse direction

        # Update invaders (convoy and charging/returning)
        invaders_to_remove = []
      
      
        for invader in self.convoy + self.charging_invaders:
            removed = invader.update(self.dt, self.invader_move_direction)
            if removed:
                invaders_to_remove.append(invader)

        # Remove invaders that went off-screen after charging
        for invader in invaders_to_remove:
            if invader in self.charging_invaders:
                self.charging_invaders.remove(invader)


        # --- Invader Diving Logic ---
        self.invader_charge_timer += self.dt
        if self.invader_charge_timer >= self.invader_charge_interval and self.convoy:
            self.invader_charge_timer = 0
            charging_invader, escorts = self.select_charger()
            if charging_invader:
                charging_invader.start_charge(self.player.position) # Dive towards current player position
                self.charging_invaders.append(charging_invader) # Add to charging list
            if escorts:
               for i, escort in enumerate(escorts):
                   escort.escort = i + 1
                   escort.start_charge(self.player.position) # Dive towards current player position
                   self.charging_invaders.append(escort) # Add to charging list
                
        # --- Invader Shooting (Simple: Diving invaders shoot) ---
        for invader in self.charging_invaders:
            # Simple random chance to shoot while charging
            if random.random() < 0.005: # Adjust probability
                bullet = InvaderBullet(position=invader.position)
                
                self.add_child(bullet)
                self.invader_bullets.append(bullet)


        # --- Bullet Updates ---
        player_bullets_to_remove = []
        for bullet in self.player_bullets:
            bullet.update(self.dt)
            # Remove bullets that go off-screen
            if bullet.position.y > SCREEN_HEIGHT:
                player_bullets_to_remove.append(bullet)

        invader_bullets_to_remove = []
        for bullet in self.invader_bullets:
            bullet.update(self.dt)
            # Remove bullets that go off-screen
            if bullet.position.y < 0:
                invader_bullets_to_remove.append(bullet)

        # --- Collision Detection ---

        # Player Bullet vs Invader (Formation and Diving)
        hit_invaders = []
        hit_player_bullets = []
        for bullet in self.player_bullets:
            # Check against invaders in convoy
            for invader in self.convoy:
                if bullet.frame.intersects(invader.frame):
                    hit_invaders.append(invader)
                    hit_player_bullets.append(bullet)
                    self.score += invader.score_value # Increase score based on invader type
                    self.score_label.text = str(self.score)
                    # scene.play_effect('arcade:Explosion_1') # Play hit sound
                    break # Bullet can only hit one invader

            # Check against charging invaders
            for invader in self.charging_invaders:
                 if bullet.frame.intersects(invader.frame):
                    hit_invaders.append(invader)
                    hit_player_bullets.append(bullet)
                    self.score += invader.score_value * 2 # Maybe bonus for hitting charging invader
                    self.score_label.text = str(self.score)
                    # scene.play_effect('arcade:Explosion_1') # Play hit sound
                    break # Bullet can only hit one invader


        # Invader Bullet vs Player
        hit_invader_bullets = []
        if not self.game_over: # Only check if player is alive
            for bullet in self.invader_bullets:
                if bullet.frame.intersects(self.player.frame):
                    hit_invader_bullets.append(bullet)
                    self.end_wave("hit")
                    # scene.play_effect('arcade:Explosion_2') # Play player hit sound
                    break # Player hit by one bullet is enough


        # Remove hit invaders and bullets
        for invader in set(hit_invaders):
            if invader in self.convoy:
                self.convoy.remove(invader)
            elif invader in self.charging_invaders:
                 self.charging_invaders.remove(invader)
            invader.remove_from_parent()

        for bullet in set(player_bullets_to_remove + hit_player_bullets):
            if bullet in self.player_bullets:
                self.player_bullets.remove(bullet)
                bullet.remove_from_parent()

        for bullet in set(invader_bullets_to_remove + hit_invader_bullets):
            if bullet in self.invader_bullets:
                self.invader_bullets.remove(bullet)
                bullet.remove_from_parent()


        # --- Check Game Over/Win Conditions ---
        if not self.convoy and not self.charging_invaders: # Win if all invaders are gone
            self.end_wave("complete")
        


    def touch_began(self, touch):
        # Handle touch input
        if self.game_over:
            # Restart game on touch if game over
            self.setup()
            return

        # Determine player movement based on touch location
        if touch.location.x < SCREEN_WIDTH / 2:
            self.moving_left = True
            self.moving_right = False
        else:
            self.moving_right = True
            self.moving_left = False

        # Shoot (can refine this to a specific area if needed)
        bullet = self.player.shoot()
        if bullet:
            self.add_child(bullet)
            self.player_bullets.append(bullet)
            # scene.play_effect('arcade:Laser_1') # Play shoot sound


    def touch_moved(self, touch):
        # Update movement based on touch location
        if self.game_over:
            return
        if touch.location.x < SCREEN_WIDTH / 2:
            self.moving_left = True
            self.moving_right = False
        else:
            self.moving_right = True
            self.moving_left = False

    def touch_ended(self, touch):
        # Stop player movement when touch ends
        if self.game_over:
            return
        # Check if the touch ended in the area that was causing movement
        if (self.moving_left and touch.location.x < SCREEN_WIDTH / 2) or \
           (self.moving_right and touch.location.x >= SCREEN_WIDTH / 2):
            self.moving_left = False
            self.moving_right = False
            
    @ui.in_background     
    def explosion(self, pos):
      expl = scene.SpriteNode('shp:Explosion01', position=pos, parent=self)
      for i in range(1,8):
       sleep(.1)
       imgname= f'shp:Explosion{i:02d}'
       expl.texture = Texture(imgname)
      expl.remove_from_parent()
     
    @ui.in_background
    def end_wave(self, reason=None):
        if reason == 'hit':
           self.player.lives -= 1
           self.explosion(self.player.position)
           self.life_icon.pop().remove_from_parent()
           if self.player.lives == 0:
               self.game_over = True
               self.game_over_label = scene.LabelNode('Game Over', font=('Press Start 2P', 50), position=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2), color='#ffffff', parent=self)
            
        elif reason == 'complete':
            self.wave += 1
            self.wave_flags.append(scene.SpriteNode('emj:Triangular_Flag', position=(800+20*self.wave, 50), parent=self))
            self.reset_wave()
        
        # add lives code
        
        
        
        # You could add a restart button here

# --- Run the game ---
if __name__ == '__main__':
    # Load the arcade font for a retro feel
    #scene.load_font('PressStart2P.ttf') # Make sure you have this font file in Pythonista
    scene.run(Game(), orientation=scene.PORTRAIT)
