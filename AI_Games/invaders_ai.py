# Simple Galaxian game for Pythonista using the scene module

import scene
import random
import math

# --- Game Constants ---
SCREEN_WIDTH = 768
SCREEN_HEIGHT = 1024
PLAYER_SPEED = 300
PLAYER_SHOOT_COOLDOWN = 0.5

INVADER_FORMATION_SPEED = 60
INVADER_DIVE_SPEED = 300
INVADER_RETURN_SPEED = 150
INVADER_BULLET_SPEED = 250
INVADER_ROWS = 5
INVADER_COLUMNS = 8
INVADER_SPACING_X = 70 # Spacing between invaders in formation
INVADER_SPACING_Y = 60 # Spacing between invaders in formation
INVADER_START_Y = SCREEN_HEIGHT - 200 # Starting Y position for invader formation
INVADER_FORMATION_MOVE_DIRECTION = 1 # 1 for right, -1 for left
INVADER_FORMATION_MOVE_DOWN_AMOUNT = 30
INVADER_FORMATION_MOVE_INTERVAL = 1.5 # Time before invaders change direction/move down

BULLET_SIZE = 10
BULLET_SPEED = 250
PLAYER_SIZE = 60
INVADER_SIZE = 40
INVADER_BULLET_SIZE = 15

# Invader states
INVADER_STATE_FORMATION = 'formation'
INVADER_STATE_DIVING = 'diving'
INVADER_STATE_RETURNING = 'returning'


  
# --- Game Classes ---

class Player(scene.SpriteNode):
    def __init__(self, position=(SCREEN_WIDTH/2, 50), **kwargs):
        # Use a simple shape or color for the player (can replace with image)
        super().__init__('spc:PlayerShip1Blue', position=position, color='#00ff00', size=(PLAYER_SIZE, PLAYER_SIZE), **kwargs)
        self.speed = PLAYER_SPEED
        self.can_shoot = True
        self._shoot_timer = 0

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
    def __init__(self, position, formation_position, invader_type, **kwargs):
        # Use a simple shape or color based on invader type (can replace with images)
        colors = ['#ff0000', '#ffff00', '#00ffff', '#ff00ff'] # Red, Yellow, Cyan, Magenta
        shapes = ['spc:EnemyRed2', 'spc:EnemyBlue2', 'spc:EnemyGreen1', 'spc:EnemyRed2'] # Circle, Square, Triangle, Star
        color = colors[invader_type % len(colors)]
        shape = shapes[invader_type % len(shapes)]

        super().__init__(shape, position=position, color=color, size=(INVADER_SIZE, INVADER_SIZE), **kwargs)
        self.formation_position = formation_position # Original position in formation
        self.invader_type = invader_type
        self.state = INVADER_STATE_FORMATION
        self.dive_target = None # Player position when dive started
        self.return_target = None # Position to return to in formation
        self.score_value = (invader_type + 1) * 10 # Basic scoring based on type
        
    def normalize(self, a):
         # convert to -1, 0, 1
         return scene.Point(*tuple([0 if x == 0 else int(x/abs(x)) for x in a]))
         
    def update(self, dt, formation_move_direction):
        if self.state == INVADER_STATE_FORMATION:
            # Move horizontally in formation
            self.position = (self.position.x + formation_move_direction * INVADER_FORMATION_SPEED * dt, self.position.y)
            # Update formation position based on horizontal movement
            self.formation_position = (self.formation_position[0] + formation_move_direction * INVADER_FORMATION_SPEED * dt, self.formation_position[1])

        elif self.state == INVADER_STATE_DIVING:
            # Move towards the dive target (player position when dive started)
            if self.dive_target:
                move_vector = self.normalize(scene.Point(self.dive_target.x - self.position.x, self.dive_target.y - self.position.y))
                self.position = (self.position.x + move_vector.x * INVADER_DIVE_SPEED * dt, self.position.y + move_vector.y * INVADER_DIVE_SPEED * dt)

                # Check if invader is off-screen or passed the player
                if self.position.y < -INVADER_SIZE or self.position.y > SCREEN_HEIGHT + INVADER_SIZE or \
                   self.position.x < -INVADER_SIZE or self.position.x > SCREEN_WIDTH + INVADER_SIZE:
                    # If off-screen after diving, remove it (or make it return)
                    # For simplicity, let's remove for now. A real Galaxian would return.
                    self.remove_from_parent()
                    return True # Indicate removal

        elif self.state == INVADER_STATE_RETURNING:
            # Move back towards formation position
            if self.return_target:
                # Simple linear return for now
                move_vector = self.normalize(scene.Point(self.return_target[0] - self.position.x, self.return_target[1] - self.position.y))
                self.position = (self.position.x + move_vector.x * INVADER_RETURN_SPEED * dt, self.position.y + move_vector.y * INVADER_RETURN_SPEED * dt)

                # Check if invader is close to formation position
                if self.position.distance(scene.Point(*self.return_target)) < 10: # Threshold
                    self.position = scene.Point(*self.return_target) # Snap to position
                    self.state = INVADER_STATE_FORMATION # Return to formation state
                    self.return_target = None # Clear return target
                    self.formation_position = scene.Point(*self.return_target) # Reset formation position

        return False # Indicate not removed

    def move_down(self):
        # Move the invader down in formation
        self.position = (self.position.x, self.position.y - INVADER_FORMATION_MOVE_DOWN_AMOUNT)
        self.formation_position = (self.formation_position[0], self.formation_position[1] - INVADER_FORMATION_MOVE_DOWN_AMOUNT)

    def start_dive(self, target_position):
        # Start the diving attack
        self.state = INVADER_STATE_DIVING
        self.dive_target = target_position
        # Remove from the main invaders list in the game scene to avoid formation logic
        if self in self.parent.invaders:
            self.parent.invaders.remove(self)

    def start_return(self, target_position):
        # Start returning to formation
        self.state = INVADER_STATE_RETURNING
        self.return_target = target_position
        # Add back to the main invaders list in the game scene
        if self not in self.parent.invaders:
             self.parent.invaders.append(self)


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

        # Create invaders in formation
        self.invaders = [] # Invaders currently in formation
        self.diving_invaders = [] # Invaders currently diving/returning
        self.invader_move_direction = INVADER_FORMATION_MOVE_DIRECTION
        self.invader_formation_move_timer = 0 # Timer to control invader horizontal movement
        self.invader_formation_move_interval = INVADER_FORMATION_MOVE_INTERVAL

        self.invader_dive_timer = 0 # Timer to control when invaders dive
        self.invader_dive_interval = 3.0 # Time before an invader might dive

        for row in range(INVADER_ROWS):
            for col in range(INVADER_COLUMNS):
                # Calculate formation position
                formation_x = (col - INVADER_COLUMNS / 2 + 0.5) * INVADER_SPACING_X + SCREEN_WIDTH / 2
                formation_y = INVADER_START_Y - row * INVADER_SPACING_Y
                formation_position = (formation_x, formation_y)

                invader = Invader(position=formation_position, formation_position=formation_position, invader_type=row)
                self.add_child(invader)
                self.invaders.append(invader)

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

        # Load sounds (replace with actual sound files if you have them)
        # scene.play_effect('arcade:Explosion_1') # Example sound effect

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

        # --- Invader Formation Movement ---
        self.invader_formation_move_timer += self.dt
        if self.invader_formation_move_timer >= self.invader_formation_move_interval:
            self.invader_formation_move_timer = 0

            # Check if invaders in formation hit screen edge
            hit_edge = False
            if self.invaders: # Only check if there are invaders in formation
                # Find the leftmost and rightmost invaders in formation
                leftmost_invader = min(self.invaders, key=lambda inv: inv.position.x)
                rightmost_invader = max(self.invaders, key=lambda inv: inv.position.x)

                if leftmost_invader.position.x <= INVADER_SIZE/2 or rightmost_invader.position.x >= SCREEN_WIDTH - INVADER_SIZE/2:
                    hit_edge = True

            if hit_edge:
                self.invader_move_direction *= -1 # Reverse direction
                # Move all invaders (including diving/returning ones) down
                for invader in self.invaders + self.diving_invaders:
                    invader.move_down() # Move down


        # Update invaders (formation and diving/returning)
        invaders_to_remove = []
        for invader in self.invaders + self.diving_invaders:
            removed = invader.update(self.dt, self.invader_move_direction)
            if removed:
                invaders_to_remove.append(invader)

        # Remove invaders that went off-screen after diving
        for invader in invaders_to_remove:
            if invader in self.diving_invaders:
                self.diving_invaders.remove(invader)


        # --- Invader Diving Logic ---
        self.invader_dive_timer += self.dt
        if self.invader_dive_timer >= self.invader_dive_interval and self.invaders:
            self.invader_dive_timer = 0
            # Randomly select an invader from the formation to dive
            diving_invader = random.choice(self.invaders)
            diving_invader.start_dive(self.player.position) # Dive towards current player position
            self.diving_invaders.append(diving_invader) # Add to diving list

        # --- Invader Shooting (Simple: Diving invaders shoot) ---
        for invader in self.diving_invaders:
            # Simple random chance to shoot while diving
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
            # Check against invaders in formation
            for invader in self.invaders:
                if bullet.frame.intersects(invader.frame):
                    hit_invaders.append(invader)
                    hit_player_bullets.append(bullet)
                    self.score += invader.score_value # Increase score based on invader type
                    self.score_label.text = str(self.score)
                    # scene.play_effect('arcade:Explosion_1') # Play hit sound
                    break # Bullet can only hit one invader

            # Check against diving invaders
            for invader in self.diving_invaders:
                 if bullet.frame.intersects(invader.frame):
                    hit_invaders.append(invader)
                    hit_player_bullets.append(bullet)
                    self.score += invader.score_value * 2 # Maybe bonus for hitting diving invader
                    self.score_label.text = str(self.score)
                    # scene.play_effect('arcade:Explosion_1') # Play hit sound
                    break # Bullet can only hit one invader


        # Invader Bullet vs Player
        hit_invader_bullets = []
        if not self.game_over: # Only check if player is alive
            for bullet in self.invader_bullets:
                if bullet.frame.intersects(self.player.frame):
                    hit_invader_bullets.append(bullet)
                    self.end_game("Game Over!")
                    # scene.play_effect('arcade:Explosion_2') # Play player hit sound
                    break # Player hit by one bullet is enough


        # Remove hit invaders and bullets
        for invader in set(hit_invaders):
            if invader in self.invaders:
                self.invaders.remove(invader)
            elif invader in self.diving_invaders:
                 self.diving_invaders.remove(invader)
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
        if not self.invaders and not self.diving_invaders: # Win if all invaders are gone
            self.end_game("You Win!")
        else:
            # Check if invaders in formation reached player level
            if self.invaders:
                lowest_invader = min(self.invaders, key=lambda inv: inv.position.y)
                if lowest_invader.position.y <= self.player.position.y + PLAYER_SIZE/2:
                    self.end_game("Game Over!")


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


    def end_game(self, message):
        self.game_over = True
        self.game_over_label = scene.LabelNode(message, font=('Press Start 2P', 50), position=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2), color='#ffffff')
        self.add_child(self.game_over_label)
        # You could add a restart button here

# --- Run the game ---
if __name__ == '__main__':
    # Load the arcade font for a retro feel
    #scene.load_font('PressStart2P.ttf') # Make sure you have this font file in Pythonista
    scene.run(Game(), orientation=scene.PORTRAIT)
