""" Demolition game from CBM PET c1981 
A very simple game with a moving block which can be dropped by a touch on the screen.
Game finishes when block touches the top line of the game surface
"""
from demolition_config import *
from scene import *
import console
from ui import Path, in_background
import sound
import random
from random import uniform as rnd
import math
from time import sleep
from math import pi

A = Action


def build_background_grid():
    """ This function builds the playing grid """
    # parent is the starting node for the grid.
    # all the grid lines
    # belong to this parent

    parent = Node()

    # Building the columns
    # these are rectangles with width GRID_SIZE and height GRID_SIZE * ROWS
    for i in range(COLUMNS):
        n = ShapeNode(path=Path.rect(0, 0, GRID_SIZE, GRID_SIZE * ROWS),
                      fill_color="clear",
                      stroke_color="lightgrey",
                      anchor_point=(0, 0),
                      position=Vector2(i * GRID_SIZE, 0))
        parent.add_child(n)

    # Building the rows
    # these are rectangles with width  GRID_SIZE * ROWS and height GRID_SIZE
    for i in range(ROWS):
        n = ShapeNode(path=Path.rect(0, 0, GRID_SIZE * COLUMNS, GRID_SIZE),
                      fill_color="clear",
                      stroke_color="lightgrey",
                      anchor_point=(0, 0),
                      position=Vector2(0, i * GRID_SIZE))
        parent.add_child(n)

    return parent


class Tile(SpriteNode):
    """
  A single tile on the grid.
  This is defined so that positions can be converted
  between row and column number and position on the screen
  """

    def __init__(self, color, row=0, col=0):
        SpriteNode.__init__(self, 'pzl:Gray3')
        self.color = color
        self.size = (GRID_SIZE, GRID_SIZE)
        self.anchor_point = (0, 0)
        self.set_pos(col, row)

    def set_pos(self, col=0, row=0):
        """
    Sets the position of the tile in the grid.
    """
        if col < 0:
            return
            #raise ValueError(f"col={col} is less than 0")

        if row < 0:
            return
            # raise ValueError(f"row={row} is less than 0")

        self.col = col
        self.row = row

        pos = Vector2()
        pos.x = col * self.size.w
        pos.y = row * self.size.h
        self.position = pos


class Ball(Tile):
    """
  A ball on the grid.
  Ball is just another Tile 
  """

    def __init__(self, color=None, row=0, col=0):
        Tile.__init__(self, color='#FFFFFF', row=ROWS - 1, col=0)


class DemolitionGame(Scene):
    """
  The main game code for Demolition
  """

    def setup_ui(self):
        # Root node for UI elements
        # This is the starting node for the entire game
        self.ui_root = Node(parent=self)

        self.score_label = LabelNode('0',
                                     font=('Avenir Next', 20),
                                     position=(60, 10),
                                     parent=self)
        self.line_label = LabelNode(str(self.line_timer_current),
                                    font=('Avenir Next', 20),
                                    position=(120, 10),
                                    parent=self)

        game_title = LabelNode('Demolition',
                               font=('Avenir Next', 20),
                               position=(screen_width / 2, 10),
                               parent=self)

    def setup(self):
        self.background_color = COLORS["bg"]

        # Root node for all game elements
        self.game_field = Node(parent=self, position=GRID_POS)

        # Add the background grid
        self.bg_grid = build_background_grid()
        self.game_field.add_child(self.bg_grid)
        self.fall_speed = INITIAL_FALL_SPEED
        self.ball_timer = self.fall_speed

        self.line_timer = INITIAL_LINE_SPEED
        self.line_timer_store = INITIAL_LINE_SPEED
        self.line_timer_current = INITIAL_LINE_SPEED
        self.index = 1
        self.ball = Ball()
        self.game_field.add_child(self.ball)
        self.ball_direction = 1
        self.spawn_line()
        self.spawn_ball()
        self.score = 0
        self.level = 1
        self.coloured_line = True
        # only set up fixed items once
        try:
            a = self.score_label.text
        except AttributeError:
            self.setup_ui()

    @ui.in_background
    def show_start_menu(self):
        """ This function needs to be the background else the console.alert will not
    work correctly 
    """
        self.pause_game()
        selection = console.alert('New Game?',
                                  '',
                                  button1='Play',
                                  button2='Quit')
        if selection == 1:
            self.resume_game()
            self.clear_tiles()
            self.ball.remove_from_parent()
            self.setup()
            self.score_label.text = '0'
        else:
            # quit
            self.view.close()

    def clear_tiles(self):
        for tile in self.get_tiles():
            tile.remove_from_parent()

    def get_tiles(self):
        """
        Returns an iterator over all tile objects
        Every time we call it, it returns the next object
        """
        for obj in self.game_field.children:
            if isinstance(obj, Tile) and not isinstance(obj, Ball):
                yield obj

    def check_ball_row_collision(self):
        """
        Returns true if any of the tiles in self.control row-collide (is row-adjacent) 
        with the tiles on the field
        """
        if self.ball.row == 0:
            return True

        for tile in self.get_tiles():
            if self.ball.row == tile.row and self.ball.col == tile.col:
                return True
        return False

    def check_edge_collision(self):
        """
        Checks whether ball hits either side
        """
        return self.ball.col == 0 or self.ball.col == COLUMNS - 1

    def delete_blocks(self):
        '''delete blocks around impact point'''
        # Explosion effect is optional
        self.game_field.add_child(Explosion(self.ball))
        sound.play_effect('rpg:KnifeSlice2')
        for t in self.get_tiles():
            for index in pieces:
                if t.row == self.ball.row + index[0] and t.col == self.ball.col + index[1]:
                    t.remove_from_parent()
                    self.score += 1
                    # speed up lines every 50 points
                    if self.score % 50 == 0:
                        self.line_timer_current -= 0.25

    def shift_up_tiles(self):
        '''shift up tiles'''
        for t in self.get_tiles():
            t.set_pos(row=t.row + 1, col=t.col)
        self.index += 1

    def update_score(self):
        self.score_label.text = str(self.score)
        self.line_label.text = str(self.line_timer_current)

    def create_line(self, index):
        """new row """
        color = colours[index]
        tile = []
        for p in range(0, COLUMNS):
            t = Tile(color, col=p)
            self.game_field.add_child(t)
            tile.append(t)
        return tile

    def spawn_ball(self):
        # reposition  ball
        self.ball_direction = 1
        self.ball.set_pos(0, ROWS - 1)

    def spawn_line(self):
        """
    Spawns a new line on the game field 
    """
        self.shift_up_tiles()
        tiles = self.create_line(self.index % 4)

    def did_change_size(self):
        pass

    def ball_move(self):
        """ move ball in direction 1=right, -1=left, 2=down)"""
        b = self.ball
        bd = self.ball_direction
        if self.check_edge_collision():
            self.ball_direction = -self.ball_direction
        if abs(self.ball_direction) == 2:
            b.set_pos(b.col, b.row - 1)
        else:
            b.set_pos(b.col + self.ball_direction, b.row)

    def drop(self):
        self.ball_direction = 2
        self.fall_speed = INITIAL_FALL_SPEED / 4

    def check_for_finish(self):
        """check if new piece is at start location when collision detected"""
        for t in self.get_tiles():
            if t.row >= ROWS - 1:
                return True
        return False

    def pause_game(self):
        self.paused = True

    def resume_game(self):
        self.paused = False

    def next_game(self):
        self.pause_game()
        self.show_start_menu()

    def explode(self):
        self.pause_game()
        if self.check_for_finish():
            self.next_game()
        else:
            self.delete_blocks()
            self.update_score()
            self.resume_game()

    def update(self):
        # dt is provided by Scene
        self.ball_timer -= self.dt
        self.line_timer -= self.dt
        if self.ball_timer <= 0:
            self.ball_timer = self.fall_speed
            self.ball_move()
            # Check for intersection and spawn a new piece if needed
            if self.check_ball_row_collision():
                self.explode()
                self.spawn_ball()
        # line creation
        if self.line_timer <= 0:
            self.line_timer = self.line_timer_current
            if self.index % 4 == 0:
                self.coloured_line = not self.coloured_line
            if self.coloured_line:
                self.spawn_line()
            else:
                self.shift_up_tiles()

    def touch_began(self, touch):
        self.drop()

    def touch_moved(self, touch):
        pass

    def touch_ended(self, touch):
        pass


class Explosion(Node):
    """Particle effect when row removed
    This is an advanced effect
    The game will work just fine without it
    """
    def __init__(self, tile, *args, **kwargs):
        Node.__init__(self, *args, **kwargs)
        self.position = tile.position
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            p = SpriteNode(tile.texture, scale=0.5, parent=self)
            p.position = tile.size.w / 4 * dx, tile.size.h / 4 * dy
            p.size = tile.size
            d = 0.4
            r = 30
            p.run_action(A.move_to(rnd(-r, r), rnd(-r, r), d))
            p.run_action(A.scale_to(0, d))
            p.run_action(A.rotate_to(rnd(-pi / 2, pi / 2), d))
        self.run_action(A.sequence(A.wait(d), A.remove()))


if __name__ == '__main__':
    run(DemolitionGame(), PORTRAIT, show_fps=False)
