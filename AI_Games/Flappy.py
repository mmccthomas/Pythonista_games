import scene
import random
import sound
import math
import ui

class FlappyBird(scene.Scene):
    def setup(self):
        self.background_color = '#7ED2FF' # Light blue sky
        self.bird = scene.SpriteNode('emj:Baby_Angel', parent=self)
        self.bird.y_scale = -1.0
        self.bird.position = self.size.w / 4, self.size.h / 2
        self.bird.scale = 0.5
        self.bird_velocity_y = 0
        self.gravity = -250 # Pixels per second squared
        self.jump_strength = 250 # Pixels per second

        self.pipes = []
        self.pipe_speed = 150 # Pixels per second
        self.pipe_gap_size = 200 # Vertical gap
        self.pipe_width = 80
        self.edge_gap = 0
        self.time_since_last_pipe = 0
        self.pipe_spawn_interval = 2.0 # Seconds between pipes

        self.score = 0
        self.game_over = True

        self.score_label = scene.LabelNode(str(self.score), font=('HelveticaNeue-Bold', 40), parent=self)
        self.score_label.position = self.size.w / 2, self.size.h - 50
        self.score_label.z_position = 10 # Make sure it's on top

        self.game_over_label = scene.LabelNode('GAME OVER', font=('HelveticaNeue-Bold', 60), parent=self)
        self.game_over_label.position = self.size.w / 2, self.size.h / 2 + 50
        self.game_over_label.z_position = 10
        self.game_over_label.hidden = True
        #self.position_label = scene.LabelNode('abc', 
        #                                      font=('HelveticaNeue-Bold', 40),
        #                                      position=(50, self.size.h-100),
        #                                      anchor_point=(0,0),
        #                                      parent=self)
        self.restart_label = scene.LabelNode('Tap to Restart', font=('HelveticaNeue-Bold', 30), parent=self)
        self.restart_label.position = self.size.w / 2, self.size.h / 2 - 20
        self.restart_label.z_position = 10
        self.restart_label.hidden = True

        # Ground
        self.ground = scene.SpriteNode('plc:Grass_Block', parent=self, size=(self.size.w, 100))
        self.ground.anchor_point = (0.5, 0)
        self.ground.position = self.size.w / 2, 0
        self.ground.z_position = -1 # Behind everything else

        # Sounds (Pythonista supports sound playback)
        try:
            self.sound_wing = sound.load_effect('arcade:Powerup_3') # Example sound
            self.sound_hit = sound.load_effect('arcade:Explosion_4')
            self.sound_score = sound.load_effect('arcade:Coin_5')
        except Exception as e:
            print(f"Could not load sounds: {e}. Sounds will be silent.")
            self.sound_wing = None
            self.sound_hit = None
            self.sound_score = None

  
    def update(self):
        dt = self.dt

        if self.game_over:
            self.paused=True

        # Bird movement
        self.bird_velocity_y += self.gravity * dt
        self.bird.position = self.bird.position.x, self.bird.position.y + self.bird_velocity_y * dt

        # Bird rotation based on velocity
        angle_rad = math.atan2(self.bird_velocity_y, self.pipe_speed) # Angle based on y velocity and forward speed
        #self.bird.rotation = -angle_rad # Rotate to point upwards/downwards

        # Ground collision
        if self.bird.position.y < self.ground.size.h / 2:
            self.bird.position = self.bird.position.x, self.ground.size.h / 2
            self.bird_velocity_y = 0
            self.game_over = True
            if self.sound_hit: self.sound_hit.play()

        # Ceiling collision
        if self.bird.position.y > self.size.h:
            self.bird.position = self.bird.position.x, self.size.h
            self.bird_velocity_y = 0

        # Pipe generation
        self.time_since_last_pipe += dt
        if self.time_since_last_pipe > self.pipe_spawn_interval:
            self.spawn_pipes()
            self.time_since_last_pipe = 0

        # Pipe movement and collision
        pipes_to_remove = []
        bird_rect = self.bird.bbox
        self.hit = None
        for i, pipe_pair in enumerate(self.pipes):
            upper_pipe, lower_pipe, scored = pipe_pair
            upper_pipe.position = upper_pipe.position.x - self.pipe_speed * dt, upper_pipe.position.y
            lower_pipe.position = lower_pipe.position.x - self.pipe_speed * dt, lower_pipe.position.y
            # self.position_label.text = f'{int(self.bird.position.y)}, {int(upper_pipe.bbox.min_y)}, {int(lower_pipe.bbox.max_y)} {i}'
            # Collision detection
            if bird_rect.intersects(upper_pipe.bbox):               
               self.hit = upper_pipe.bbox
               self.game_over = True
               #raise Exception
            elif  bird_rect.intersects(lower_pipe.bbox):                
                self.hit = lower_pipe.bbox
                self.game_over = True
                # raise Exception
            if self.sound_hit: self.sound_hit.play()

            # Scoring
            if not scored and lower_pipe.position.x + self.pipe_width / 2 < self.bird.position.x:
                self.score += 1
                self.score_label.text = str(self.score)
                pipe_pair[2] = True # Mark as scored
                if self.sound_score: self.sound_score.play()

            # Remove off-screen pipes
            if lower_pipe.position.x < -self.pipe_width / 2:
                pipes_to_remove.append(pipe_pair)

        for pipe_pair in pipes_to_remove:
            pipe_pair[0].remove_from_parent()
            pipe_pair[1].remove_from_parent()
            self.pipes.remove(pipe_pair)

        if self.game_over:
            self.game_over_label.text = 'GAME OVER '
            self.restart_label.text = f'Tap to Restart'

    def touch_began(self, touch):
        if self.game_over:
            self.reset_game()
        else:
            self.bird_velocity_y = self.jump_strength
            if self.sound_wing: self.sound_wing.play()

    def spawn_pipes(self):
        min_y = self.ground.size.h + self.pipe_gap_size / 2 + self.edge_gap # Ensure pipes are above ground
        max_y = self.size.h - self.pipe_gap_size / 2 - self.edge_gap # Ensure pipes are below ceiling
        gap_center_y = random.uniform(min_y, max_y)

        upper_pipe_height = self.size.h - self.edge_gap - (gap_center_y + self.pipe_gap_size / 2)
        lower_pipe_height = gap_center_y - self.pipe_gap_size / 2 - self.ground.size.h - self.edge_gap

        # Use a simple rectangular sprite for pipes, or a custom image if you have one
        # For simplicity, we'll create new SpriteNodes for each pipe visually
        # You might want to pre-load a 'pipe' image if you have one.
        # As we don't have pipe images, we'll create simple green rectangles.
        upper_pipe = scene.SpriteNode(
            None, #'plc:Brown_Block',
            color=(0.44, 0.35, 0.26),
            parent=self,
            size=(self.pipe_width, upper_pipe_height)
        )
        upper_pipe.anchor_point = (0.5, 1) # Anchor at top-center
        upper_pipe.position = self.size.w + self.pipe_width / 2, self.size.h - self.edge_gap

        lower_pipe = scene.SpriteNode(
            None, # 'plc:Brown_Block',
            color=(0.44, 0.35, 0.26),
            parent=self,
            size=(self.pipe_width, lower_pipe_height)
        )
        lower_pipe.anchor_point = (0.5, 0) # Anchor at bottom-center
        lower_pipe.position = self.size.w + self.pipe_width / 2, self.ground.size.h + self.edge_gap

        self.pipes.append([upper_pipe, lower_pipe, False]) # False indicates not yet scored

    def reset_game(self):
        self.game_over = False
        self.game_over_label.text = ''
        self.restart_label.text = ''
        self.score = 0
        self.score_label.text = str(self.score)
        self.bird.position = self.size.w / 4, self.size.h / 2
        self.bird_velocity_y = 0

        for pipe_pair in self.pipes:
            pipe_pair[0].remove_from_parent()
            pipe_pair[1].remove_from_parent()
        self.pipes = []
        self.time_since_last_pipe = 0
        self.paused = False

# To run the game in Pythonista, simply call:
if __name__ == '__main__':
    scene.run(FlappyBird(), scene.LANDSCAPE) # Or scene.PORTRAIT depending on preference
