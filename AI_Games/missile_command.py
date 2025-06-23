import ui
import io
from scene import Point, Rect, Size
from PIL import Image
import math
import random
import sound
from time import time
import console # For debugging

# --- Constants (Define these at the top of your file) ---
SCREEN_WIDTH, SCREEN_HEIGHT = ui.get_screen_size()
SCREEN_HEIGHT = SCREEN_HEIGHT -100
BASE_HEIGHT = 55
CITY_HEIGHT = 50
ENEMY_MISSILE_SPEED = 1 # Pixels per frame
PLAYER_MISSILE_SPEED = 3 # Pixels per frame
PLAYER_MISSILE_SIZE = 20
EXPLOSION_RADIUS_MAX = 80
EXPLOSION_DURATION = 30 # Frames
ADDITIONAL_MISSILE = 200 # add missile every score

def blend_images(images, size=(128, 128)):
   # combine a set of images linearly in x
   imgs = [Image.open(img).resize(size) for img in images]        
   img_size = Size(*size)
   blended = Image.new('RGBA', (len(imgs) * int(img_size.w), int(img_size.h)), 'black')
   # Paste the images (overlay)
   for i, img in enumerate(imgs):
      blended.paste(img, (i * int(img_size.w), 0))  # Paste img1 at the top-left
              
   img_byte_arr = io.BytesIO()
   blended.save(img_byte_arr, format='PNG')       
   return ui.Image.from_data(img_byte_arr.getvalue())
   
# --- Game Objects (Simple Classes) ---

class GameObject:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.alive = True

    def draw(self):
        ui.set_color(self.color)
        path = ui.Path.rect(self.x - self.width / 2, self.y - self.height, self.width, self.height)
        path.fill()

class Base(object):
    def __init__(self, x, y):
        #super().__init__(x, y, 60, BASE_HEIGHT, 'green')
        
        self.x = x
        self.y = y
        self.loc = ui.Point(self.x, self.y)
        self.alive = True
        self.h = 5
        self.color = 'orange'
        self.width = 100
        self.height = 70
        #self.base_img = blend_images(['spc:Gun6', 'spc:Gun7', 'spc:Gun6'])
        self.base_img = ui.Image('emj:Red_Triangle_1')
        self.missiles_left = 10 # Example: each base has limited missiles
        
    def status(self):
        # Display missile count
        ui.set_color('white')
        font_size = 14
        text_rect = ui.Rect(self.x - self.width/2, self.y  - 5, self.width, font_size)
        ui.draw_string(str(self.missiles_left), text_rect, color='white', font=('Helvetica Neue', font_size), alignment=ui.ALIGN_CENTER)
        
    def draw(self):
        ui.set_color(self.color)
        #for y_, w in enumerate([100, 80, 60, 40, 20]):
        #  path = ui.Path.rect(self.x - w/2, self.y - self.h * y_, w, self.h)
        #  path.fill()
        self.base_img.draw(self.x - self.width/2, self.y - self.height, self.width, self.height)
        self.status()
        
    def add_missile(self):
        self.missiles_left += 1
        

class City():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.loc = Point(self.x, self.y)
        self.alive = True
        self.w = 6
        self.width = 80
        self.height = 50
        
        self.city = blend_images( ['emj:Bank','emj:Office_Building', 'emj:Hospital'])
        pass
        
    def draw(self):
        ui.set_color('blue')
        # city shape
        #for x_, h in enumerate([50, 70, 100, 50, 80, 50, 80, 70, 50, 70, 50, 30]):
        #  path = ui.Path.rect(self.x + self.w * x_, self.y, self.w, -h/2)
        #  path.fill()
        self.city.draw(self.x, self.y-self.height, self.width, self.height)
        

class IncomingMissile:
    def __init__(self, start_x, start_y, target_x, target_y):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.x = start_x
        self.y = start_y
        self.loc = Point(self.x, self.y)
        self.color = 'red'
        self.alive = True
        self.speed = ENEMY_MISSILE_SPEED  # You might vary this

        # Calculate direction vector
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.hypot(dx, dy)
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.loc.x, self.loc.y = self.x, self.y
        # Check if it reached target or out of bounds (simplified check)
        if (self.vy > 0 and self.y >= self.target_y) or \
           (self.vy < 0 and self.y <= self.target_y) or \
           (self.vx > 0 and self.x >= self.target_x) or \
           (self.vx < 0 and self.x <= self.target_x):
            self.alive = False # Mark for explosion or impact

    def draw(self):
        if self.alive:
            ui.set_color(self.color)
            path = ui.Path()
            path.move_to(self.start_x, self.start_y)
            path.line_to(self.x, self.y)
            path.stroke()
            
            # Draw missile head (small dot)
            ui.set_color('orange')
            ui.Path.oval(self.x - 2, self.y - 2, 4, 4).fill()

class PlayerMissile:
    def __init__(self, start_x, start_y, target_x, target_y):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.target = Point(target_x, target_y)
        self.x = start_x
        self.y = start_y
        self.loc = ui.Point(self.x, self.y)
        self.color = 'yellow'
        self.alive = True
        self.exploding = False
        self.explosion_frame = 0
        self.ship = ui.Image.named('spc:PlayerLife3Green')
        
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.hypot(dx, dy)
        self.vx = (dx / dist) * PLAYER_MISSILE_SPEED 
        self.vy = (dy / dist) * PLAYER_MISSILE_SPEED 

    def update(self):
        if not self.exploding:
            self.x += self.vx
            self.y += self.vy
            self.loc.x, self.loc.y = self.x, self.y
            
            # Check if it reached target
            if (self.vy > 0 and self.y >= self.target_y) or \
               (self.vy < 0 and self.y <= self.target_y):
                self.exploding = True
                self.explosion_frame = 0
                sound.play_effect('explosion', 0.5) # Example sound
        else:
            self.explosion_frame += 1
            if self.explosion_frame > EXPLOSION_DURATION:
                self.alive = False # Explosion fades

    def draw(self):
        if self.alive:
            if not self.exploding:
                ui.set_color(self.color)
                path = ui.Path()
                path.move_to(self.start_x, self.start_y)
                path.line_to(self.x, self.y)
                path.stroke()
                self.draw_missile()                                
            else:
                # Draw explosion
                alpha = 1.0 - (self.explosion_frame / EXPLOSION_DURATION)
                ui.set_color((1.0, 0.5, 0.0, alpha)) # Orange fading to transparent
                radius = EXPLOSION_RADIUS_MAX * (self.explosion_frame / EXPLOSION_DURATION)
                path = ui.Path.oval(self.target_x - radius, self.target_y - radius, radius * 2, radius * 2)
                path.fill()
                
    def draw_missile(self):
        #raise Exception
        s = PLAYER_MISSILE_SIZE
        ship_rect = Rect(self.x - s/2, self.y - s/2, s, s)
        angle = -math.tan(self.vx / self.vy)
        # rotate the missile image to match direction
        with ui.GState():
            # Move the origin (0, 0) to the center of the rectangle and then back again
            ui.concat_ctm(ui.Transform.translation(*ship_rect.center()))
            # Rotate the coordinate system:
            ui.concat_ctm(ui.Transform.rotation(angle))
            ui.concat_ctm(ui.Transform.translation(*(ship_rect.center() * -1)))
            self.ship.draw(*ship_rect)

# --- Main Game View ---

class MissileCommandGame(ui.View):
    def __init__(self):
        self.name = 'Missile Command'
        self.background_color = 'black'
        self.flex = 'WH' # Make it flexible for different screen sizes

        self.bases = []
        self.cities = []
        self.incoming_missiles = []
        self.player_missiles = []
        self.score = 0
        self.game_over = False

        self.setup_game()

    def setup_game(self):
      
        # ground
        self.ground = GameObject(SCREEN_WIDTH/2, SCREEN_HEIGHT, SCREEN_WIDTH, 50, 'red')
    
        # Place bases (e.g., 3 bases)
        base_y = SCREEN_HEIGHT - BASE_HEIGHT +25
        self.bases.append(Base(SCREEN_WIDTH * 0.05, base_y))
        self.bases.append(Base(SCREEN_WIDTH * 0.5, base_y))
        self.bases.append(Base(SCREEN_WIDTH * 0.95, base_y))

        # Place cities (e.g., 6 cities between bases)
        city_y = SCREEN_HEIGHT - CITY_HEIGHT
        city_spacing = SCREEN_WIDTH / 10
        for i in [1,2,3,6, 7, 8]:
            self.cities.append(City(i * city_spacing + 50, city_y))

        self.start_time = time()
        self.last_missile_spawn_time = self.start_time
        self.missile_spawn_interval = 2.0 # Seconds
        self.update_interval = 1/60
        self.add_missile = False

    def did_enter_fullscreen(self):
        # This is called when the view appears on screen
        self.start_game_loop()

    def will_close_(self):
        # Stop the game loop when the view is closed
        if hasattr(self, '_timer'):
            self.update_interval = 0
            self._timer = None

    def start_game_loop(self):
        # Use ui.set_interval for the game loop (approx 60 FPS)
        if not hasattr(self, '_timer'):
            self._timer = ui.update_interval # 60 frames per second

    def update(self):
        if self.game_over:
            return

        current_time = time()
        
        # --- Spawn Incoming Missiles ---
        if current_time - self.last_missile_spawn_time > self.missile_spawn_interval:
            self.spawn_incoming_missile()
            self.last_missile_spawn_time = current_time
            # Gradually increase difficulty by reducing interval
            #self.missile_spawn_interval = max(0.5, self.missile_spawn_interval * 0.95)

        # --- Update Game Objects ---
        for missile in self.incoming_missiles:
            missile.update()
        for missile in self.player_missiles:
            missile.update()

        # --- Collision Detection (Simplified) ---
        # Player missile explosions hitting incoming missiles
        active_explosions = [pm for pm in self.player_missiles if pm.exploding]
        for incoming_m in self.incoming_missiles[:]: # Iterate over a copy
            if not incoming_m.alive: # Already hit or reached target
                continue
            for explosion in active_explosions:
                if explosion.alive:
                    dist = math.hypot(*(incoming_m.loc - explosion.target))
                    current_explosion_radius = EXPLOSION_RADIUS_MAX * (explosion.explosion_frame / EXPLOSION_DURATION)
                    if dist < current_explosion_radius:
                        incoming_m.alive = False
                        self.score += 100 # Award points
                        sound.play_effect('coin') # Small hit sound
                        break # This incoming missile is destroyed

        # Incoming missiles hitting cities or bases
        for incoming_m in self.incoming_missiles[:]:
            if incoming_m.alive and incoming_m.y >= SCREEN_HEIGHT - CITY_HEIGHT: # Check if it reached the ground level
                hit_something = False
                # Check cities
                for city in self.cities[:]:
                    if city.alive and abs(incoming_m.x - city.x) < city.width / 2: # Simple x-overlap check
                        city.alive = False
                        sound.play_effect('unpause') # City destroyed sound
                        hit_something = True
                        break
                # Check bases (if not hit city)
                if not hit_something:
                    for base in self.bases[:]:
                        if base.alive and abs(incoming_m.x - base.x) < base.width / 2:
                            base.alive = False
                            sound.play_effect('unpause') # Base destroyed sound
                            hit_something = True
                            break
                if hit_something:
                    incoming_m.alive = False # Mark as hit and destroyed

        # --- Clean Up Dead Objects ---
        self.incoming_missiles = [m for m in self.incoming_missiles if m.alive]
        self.player_missiles = [m for m in self.player_missiles if m.alive]
        self.cities = [c for c in self.cities if c.alive]
        self.bases = [b for b in self.bases if b.alive]

        # --- Check Game Over ---
        if not self.cities: # No cities left
            self.game_over = True
            sound.play_effect('error') # Game over sound
            sel = console.alert('Game Over!', f'Your Score: {self.score}', 'Quit', 'New Game', hide_cancel_button=True)
            if sel == 1:
               self.close()
            else:
              self.setup_game()
            #self.will_close() # Stop the game loop

        self.set_needs_display() # Request a redraw

    def spawn_incoming_missile(self):
        # Random start point at the top
        start_x = random.uniform(0, SCREEN_WIDTH)
        start_y = 0

        # Random target (a live city or a base)
        potential_targets = [c for c in self.cities if c.alive] + [b for b in self.bases if b.alive]
        if not potential_targets: # No targets left
            return # Don't spawn more missiles

        target = random.choice(potential_targets)
        self.incoming_missiles.append(IncomingMissile(start_x, start_y, target.x, target.y + target.height/2)) # Target mid-point of city/base

    def touch_began(self, touch):
        if self.game_over:
            return

        # Find the closest active base with missiles
        closest_base = None
        min_dist = float('inf')
        for base in self.bases:
            if base.alive and base.missiles_left > 0:
                
                dist = math.hypot(*(touch.location - base.loc))
                if dist < min_dist:
                    min_dist = dist
                    closest_base = base

        if closest_base:
            self.player_missiles.append(
                PlayerMissile(closest_base.x, closest_base.y, touch.location.x, touch.location.y)
            )
            closest_base.missiles_left -= 1
            sound.play_effect('pew') # Missile launch sound
            self.set_needs_display()

    def draw(self):
        self.ground.draw()
        # Draw bases
        for base in self.bases:
            if base.alive:
                base.draw()
                             

        # Draw cities
        for city in self.cities:
            if city.alive:
                city.draw()

        # Draw incoming missiles
        for missile in self.incoming_missiles:
            missile.draw()

        # Draw player missiles and explosions
        for missile in self.player_missiles:
            missile.draw()

        # Draw score
        ui.set_color('white')
        ui.draw_string(f'Score: {self.score}', ui.Rect(200, SCREEN_HEIGHT-50, 200, 30), color='white',font=('Helvetica Neue', 20))
        # new missile every 500 points
        
        try:
            self.sel_base = random.choice(self.bases)    
            if self.score % ADDITIONAL_MISSILE == 0:
              if self.add_missile :          
                self.sel_base.color = 'blue'   
                self.sel_base.add_missile()
                self.add_missile = False
            else:
                self.add_missile = True
                self.sel_base.color='orange'
        except IndexError:
           pass

        if self.game_over:
            ui.set_color((0.8, 0, 0, 0.7)) # Semi-transparent red
            path = ui.Path.rect(0, SCREEN_HEIGHT/2 - 50, SCREEN_WIDTH, 100)
            path.fill()
            ui.set_color('white')
            ui.draw_string('GAME OVER', ui.Rect(0, SCREEN_HEIGHT/2 - 40, SCREEN_WIDTH, 50), font=('Helvetica Neue', 48), alignment=ui.ALIGN_CENTER)
            ui.draw_string(f'FINAL SCORE: {self.score}', ui.Rect(0, SCREEN_HEIGHT/2 + 10, SCREEN_WIDTH, 30), font=('Helvetica Neue', 24), alignment=ui.ALIGN_CENTER)


# --- Run the Game ---
if __name__ == '__main__':
    v = MissileCommandGame()
    v.present('fullscreen', hide_title_bar=False, title_bar_color='black', title_color='white')
