import scene
import sound
import random
import colorsys
sound_dict ={'pong': 'game:Click_1', 'score': 'game:Ding_1',
             'opp_hit': 'game:Ding_2', 'player_hit': 'game:Ding_3',
             'error': 'game:Beep', 'chime': '8ve:8ve-beep-piano'}
             
class Paddle(scene.SpriteNode):
    def __init__(self, icon,position, color, is_player=True, *args, **kwargs):
        super().__init__(icon, parent=kwargs.pop('parent', None), *args, **kwargs)
        self.size = scene.Size(20, 100)
        self.position = position
        self.color = color
        self.is_player = is_player
        self.speed = 10 # For AI paddle

    def update(self):
        if not self.is_player:
            # Simple AI for the computer paddle
            ball = self.parent.ball
            if ball.position.y > self.position.y + self.size.height / 4:
                self.position += (0, self.speed)
            elif ball.position.y < self.position.y - self.size.height / 4:
                self.position -= (0, self.speed)

            # Keep AI paddle within bounds
            if self.position.y + self.size.height / 2 > self.parent.size.height:
                self.position = (self.position.x, self.parent.size.height - self.size.height / 2)
            elif self.position.y - self.size.height / 2 < 0:
                self.position = (self.position.x, self.size.height / 2)


class Ball(scene.SpriteNode):
    def __init__(self, position, color, *args, **kwargs):
        super().__init__('pzl:BallBlue', parent=kwargs.pop('parent', None), *args, **kwargs)
        self.size = scene.Size(50, 50)
        self.position = position
        self.color = color
        self.dx = 0
        self.dy = 0
        self.speed = 8 # Initial ball speed
        self.reset_ball()
        

    def reset_ball(self):
        self.position = self.parent.size / 2 # Center of the screen
        self.speed = 8 # Reset speed
        self.dx = random.choice([-1, 1]) * self.speed
        self.dy = random.uniform(-1, 1) * self.speed # Random initial vertical direction
        

    def update(self):
        self.position += (self.dx, self.dy)
        # Wall collisions
        if self.position.y + self.size.height / 2 > self.parent.size.height or \
           self.position.y - self.size.height / 2 < 0:
            self.dy *= -1
            sound.play_effect(sound_dict['pong']) # Assuming you have a 'pong' sound file

        # Paddle collisions (done in PongGame update)

class PongGame(scene.Scene):
    def setup(self):
        self.background_color = '#000000' # Black background
        self.paused = True
        self.player_score = 0
        self.opponent_score = 0
        self.game_over = False
        self.winning_score = 5

        # Scores display
        self.player_score_label = scene.LabelNode(str(self.player_score), font=('HelveticaNeue-Bold', 60),
                                                   position=(self.size.width / 4, self.size.height * 0.85),
                                                   color='white', parent=self)
        self.opponent_score_label = scene.LabelNode(str(self.opponent_score), font=('HelveticaNeue-Bold', 60),
                                                     position=(self.size.width * 0.75, self.size.height * 0.85),
                                                     color='white', parent=self)

        # Paddles
        self.player_paddle = Paddle('pzl:PaddleBlue', position=scene.Point(self.size.width * 0.1, self.size.height / 2),
                                     color='blue', is_player=True, parent=self)
        self.opponent_paddle = Paddle('pzl:PaddleRed', position=scene.Point(self.size.width * 0.9, self.size.height / 2),
                                       color='red', is_player=False, parent=self)

        # Ball
        self.ball = Ball(position=self.size / 2, color='white', parent=self)

        # Game over label
        self.game_over_label = scene.LabelNode('', font=('HelveticaNeue-Bold', 80),
                                                position=self.size / 2,
                                                color='white', parent=self)
        self.game_over_label.alpha = 0 # Hidden initially
        self.paused = False

    def update(self):
        if self.game_over:
            return
        self.player_paddle.update()
        self.opponent_paddle.update()
        self.ball.update()

        # Ball and paddle collision detection
        if self.ball.bbox.intersects(self.player_paddle.bbox):
            # Check if ball hits paddle from the front (right side of player paddle)
            if self.ball.position.x > self.player_paddle.position.x:
                self.ball.dx *= -1 # Reverse horizontal direction
                # Adjust ball's vertical direction based on where it hit the paddle
                relative_hit_y = (self.ball.position.y - self.player_paddle.position.y) / (self.player_paddle.size.height / 2)
                self.ball.dy = relative_hit_y * self.ball.speed
                self.ball.speed += 0.5 # Increase ball speed slightly
                sound.play_effect(sound_dict['player_hit'])

        if self.ball.bbox.intersects(self.opponent_paddle.bbox):
            # Check if ball hits paddle from the front (left side of opponent paddle)
            if self.ball.position.x < self.opponent_paddle.position.x:
                self.ball.dx *= -1
                relative_hit_y = (self.ball.position.y - self.opponent_paddle.position.y) / (self.opponent_paddle.size.height / 2)
                self.ball.dy = relative_hit_y * self.ball.speed
                self.ball.speed += 0.5
                sound.play_effect(sound_dict['opp_hit'])

        # Scoring
        if self.ball.position.x < 0: # Ball goes past player paddle
            self.opponent_score += 1
            self.opponent_score_label.text = str(self.opponent_score)
            self.ball.reset_ball()
            sound.play_effect('score') # Assuming you have a 'score' sound 'game:Ding_1'
        elif self.ball.position.x > self.size.width: # Ball goes past opponent paddle
            self.player_score += 1
            self.player_score_label.text = str(self.player_score)
            self.ball.reset_ball()
            sound.play_effect(sound_dict['score'])
        
        # Check for game over
        if self.player_score >= self.winning_score:
            
            self.game_over_label.text = 'Player Wins!'
            self.game_over_label.alpha = 1
            self.game_over = True
            sound.play_effect(sound_dict['chime']) # Example sound for 'game:Ding_1'
        elif self.opponent_score >= self.winning_score:
            self.game_over_label.text = 'Computer Wins!'
            self.game_over_label.alpha = 1
            self.game_over = True
            sound.play_effect(sound_dict['error']) # Example sound for losing

    def touch_moved(self, touch):
        if self.game_over:
              return

        # Move player paddle with touch
        # Limit paddle movement to the screen height
        new_y = touch.location.y
        paddle_half_height = self.player_paddle.size.height / 2
        if new_y + paddle_half_height > self.size.height:
            new_y = self.size.height - paddle_half_height
        elif new_y - paddle_half_height < 0:
           new_y = paddle_half_height

        self.player_paddle.position = (self.player_paddle.position.x, new_y)
        

    def touch_began(self, touch):
        if self.game_over:
            # Restart game on touch if game is over
            self.player_score = 0
            self.opponent_score = 0
            self.player_score_label.text = '0'
            self.opponent_score_label.text = '0'
            self.game_over = False
            self.game_over_label.alpha = 0
            self.ball.reset_ball()


if __name__ == '__main__':
    scene.run(PongGame(), show_fps=True)
