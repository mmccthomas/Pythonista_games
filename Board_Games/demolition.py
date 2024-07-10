""" Demolition game from CBM PET c1981 
A very simple game with a moving block which can be drop by a touch on the screen.
Game finishes when block touches the top line of the game surface
"""
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from demolition_config import *
from scene import *
from gui.game_menu import MenuScene
from ui import Path
import sound
import random
from random import uniform as rnd
import math
from time import sleep
from math import pi
A = Action


def clamp(x, minimum, maximum):
	return max(minimum, min(x, maximum))


def intersects_sprite(point, sprite):
	norm_pos = Vector2()
	norm_pos.x = sprite.position.x - (sprite.size.w * sprite.anchor_point.x)
	norm_pos.y = sprite.position.y - (sprite.size.h * sprite.anchor_point.y)
	
	return (point.x >= norm_pos.x and point.x <= norm_pos.x + sprite.size.w) and (point.y >= norm_pos.y and point.y <= norm_pos.y + sprite.size.h)


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

		
class Tile(SpriteNode):
	"""
	A single tile on the grid.
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
	"""
	def __init__(self, color=None, row=0, col=0):
		Tile.__init__(self, color='#FFFFFF', row=ROWS - 1, col=0)
	

class DemolitionGame(Scene):
	"""
	The main game code for Tetris
	"""
		
	def setup_ui(self):
		# Root node for UI elements
		self.ui_root = Node(parent=self)
	
		self.score_label = LabelNode('0', font=('Avenir Next', 20),
																	position=(60, 10),
																	parent=self)
		self.line_label = LabelNode(str(self.line_timer_current), font=('Avenir Next', 20), position=(120, 10), parent=self)
		
		game_title = LabelNode('Demolition', font=('Avenir Next', 20), 
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

	def show_start_menu(self):
		self.pause_game()
		self.menu = MenuScene('New Game?', '', ['Play', 'Quit'])
		self.present_modal_scene(self.menu)
	
	def clear_tiles(self):
		for t in self.get_tiles():
			t.remove_from_parent()			
				
	def get_tiles(self):
		"""
		Returns an iterator over all tile objects
		"""
		for o in self.game_field.children:
			if isinstance(o, Tile) and not isinstance(o, Ball):
				yield o
				
	def check_ball_row_collision(self):
		"""
		Returns true if any of the tiles in self.control row-collide (is row-adjacent) 
		with the tiles on the field
		"""
		b = self.ball
		if b.row == 0:
			return True

		for gt in self.get_tiles():
			if b.row == gt.row  and b.col == gt.col:
				return True
		return False
		
	def check_edge_collision(self):
		"""
		Checks whether ball hits either side
		"""
		return self.ball.col == 0 or self.ball.col == COLUMNS - 1
		
	def delete_blocks(self):
		'''delete blocks around impact point'''	
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
		for p in range(0,COLUMNS):
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
			 self.ball_direction = - self.ball_direction
		if abs(self.ball_direction) == 2:
			b.set_pos(b.col, b.row - 1)
		else:
			b.set_pos(b.col +  self.ball_direction, b.row)
		
			
	def drop(self):
		self.ball_direction = 2
		self.fall_speed =  INITIAL_FALL_SPEED / 4		
																
	def check_for_finish(self):
		"""check if new piece is at start location when collision detected"""
		for t in self.get_tiles():
			if t.row >= ROWS-1:
				return True
		return False 
		
	def pause_game(self):
		self.paused = True
		'''
		self.ball_timer = 100000 # pause next ball move
		# store line timer
		self.line_timer_store = self.line_timer
		self.line_timer = 10000 # pause next line
		'''
	def resume_game(self):
		self.paused = False
		'''
		self.fall_speed = INITIAL_FALL_SPEED 
		self.ball_timer = self.fall_speed
		self.line_timer = self.line_timer_store
		'''
		
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
		
	def menu_button_selected(self, title):
		""" choose to play again or quit """
		if title.startswith('Play'):
			# start again
			self.dismiss_modal_scene()
			self.menu = None
			self.resume_game()
			self.clear_tiles()
			self.ball.remove_from_parent()	
			self.setup()
			self.score_label.text = '0'
		else:
			# quit
			self.view.close()

						
# Particle effect when row removed:
class Explosion (Node):
	def __init__(self, tile, *args, **kwargs):
		Node.__init__(self, *args, **kwargs)
		self.position = tile.position
		for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
			p = SpriteNode(tile.texture, scale=0.5, parent=self)
			p.position = tile.size.w/4 * dx, tile.size.h/4 * dy
			p.size = tile.size
			d = 0.4
			r = 30
			p.run_action(A.move_to(rnd(-r, r), rnd(-r, r), d))
			p.run_action(A.scale_to(0, d))
			p.run_action(A.rotate_to(rnd(-pi/2, pi/2), d))
		self.run_action(A.sequence(A.wait(d), A.remove()))


if __name__ == '__main__':
	run(DemolitionGame(), PORTRAIT, show_fps=False)
