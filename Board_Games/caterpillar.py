""" derived from classic snake game
uses food icons and caterpillar theme
random walls make it more interesting
game finished when caterpillar eats itself
"""
import sys
import sound
import random
from random import uniform as rnd
from scene import Vector2, get_screen_size
from scene import *
from ui import Path
from math import pi
from itertools import cycle

sys.path.append('../')
from gui.game_menu import MenuScene

A = Action
ROWS = 20
COLUMNS = 20
EXTRA_WALLS = 10
screen_size = get_screen_size()
W = screen_size.w
H = screen_size.h
if W > 800:
	GRID_SIZE = 40
else:
	GRID_SIZE = 18

UI = {
	"LEFT_BTN": {"texture": 'typw:Left', "position": Vector2(W - 175, H/2)},
	"RIGHT_BTN": {"texture": 'typw:Right', "position": Vector2(W - 75, H/2)},
	"UP_BTN": {"texture": 'typw:Up',"position": Vector2(W - 125, H/2 + 50)},
	"DOWN_BTN": {"texture": 'typw:Down',"position": Vector2(W - 125, H/2 - 50)}
	}

GRID_POS = Vector2(10, 10)

COLORS = {
	"bg": "#232323",	"red": "#FF5555",	"grey": "#646473",	"blue": "#786CF5",	"orange": "#FF8C32",
	"green": "#327834","lime": "#92CA49","purple": "#bc36ff","cyan": "#a1ffff",	"yellow": "#ffff00"
}

INITIAL_SPEED = 0.5

foods =['emj:Red_Apple', 'emj:Peach', 'emj:Strawberry', 'emj:Shortcake', 'emj:Watermelon', 'emj:Ice_Cream',
'emj:Pile_Of_Poo', 'emj:Birthday_Cake', 'emj:Aubergine','emj:Candy','emj:Fish', 'emj:Poultry_Leg', 'emj:Tomato']

# iterator to select each food in turn
food_cycle = cycle(range(len(foods)))

right_angle = {"up": ['right','left'], "down": ['left','right'],"left": ['up','down'], "right": ['down','up'] } # used  for turning
# row,col delta for move prediction
new_pos = {"up": (1, 0), "down": (-1, 0), "left": (0, -1), "right": (0, 1)} # row,col
# used in touch processing, dont allow reversal of direction
opposite = {"left": 'right', "right": 'left', "up": 'down', "down": 'up'}

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
		"stroke_color":  0.2  # "lightgrey"
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
	def __init__(self, row=0, col=0, sprite='pzl:Gray3'):
		SpriteNode.__init__(self, sprite)
		self.size = (GRID_SIZE, GRID_SIZE)
		self.anchor_point = (0, 0)
		self.set_pos(row, col)
		self.last_posx = col
		self.last_posy = row
	
	def set_pos(self, row=0, col=0):
		"""
		Sets the position of the tile in the grid.
		"""
		col = clamp(col, 0, COLUMNS -1)	
		if col < 0:
			raise ValueError(f"col={col} is less than 0")
			
		row = clamp(row, 0, ROWS -1)
		if row < 0:
			raise ValueError(f"row={row} is less than 0")
		
		self.col = col
		self.row = row
		
		pos = Vector2()
		pos.x = col * self.size.w
		pos.y = row * self.size.h
		self.position = pos
		
class Head(Tile):
	""" head can move in response to direction """
	def __init__(self, position):
		row, col = position
		self.faces = [Texture('emj:Smiling_2'), Texture('emj:Smiling_3')]
		Tile.__init__(self, row, col, sprite=self.faces[0])	
		self.face_cycle = cycle(range(2))
	
	def next_position(self, direction):
		""" return predicted row and col in current direction """
		dy, dx = new_pos[direction]
		return  self.row + dy, self.col + dx
		
	def move(self, direction):
		""" move in current direction """
		self.last_posx, self.last_posy = self.col, self.row
		# TODO alternate faces ?
		# self.texture = self.faces[next(self.face_cycle)]
		
		self.row, self.col = self.next_position(direction)
		self.set_pos(self.row, self.col)			

	
class Body(Tile):
	""" body follows head """
	
	def __init__(self, position):
		row, col = position
		Tile.__init__(self, row, col,'spc:PowerupGreen') #'shp:RoundRect') # 'pzl:Green3')
		self.color = COLORS["green"]
		self.scale=1.0
		
		
class Border(Tile):
	def __init__(self, row=0, col=0):
		Tile.__init__(self, row, col, 'pzl:Gray3')


class Food(Tile):
	def __init__(self, position, sprite=None):
		row, col = position
		Tile.__init__(self, row, col, sprite)
		self.food_cycle = cycle(range(len(foods)))

								
class BodyControl ():
	"""
	An object that controls a group of tiles.
	"""
	def __init__(self, tiles=None):
		"""
		Constructs a new BodyControl.		
		Parameters:
			tiles: A list of Tile objects under the control of this object.
		"""
		if tiles is None:
			tiles = []
		self.tiles = tiles

	def reset(self, tiles=None):
		if tiles is None:
			tiles = []
		self.tiles = tiles
	
	def move(self, head):
		''' body parts follow the head'''
		for index, t in enumerate(self.tiles):
			t.last_posx, t.last_posy = t.col, t.row
			if index == 0:
				t.row, t.col = head.last_posy, head.last_posx
			else:
				t.row = self.tiles[index - 1].last_posy
				t.col = self.tiles[index - 1].last_posx
			t.set_pos(t.row, t.col)
			
	def add_segment(self, head, row=None, col=None):
		''' add new body segment behind the head'''
		if row is None and col is None:
			row = head.row
			col = head.col
		body_seg = Body((row, col))
		self.tiles.insert(0, body_seg) # insert at start of list		
		return body_seg
		
	def length(self):
		return len(self.tiles)

class Caterpillar(Scene):
	"""
	The main game code for Caterpillar
	"""
		
	def setup_ui(self):
		# Root node for UI elements
		self.ui_root = Node(parent=self)
	  # array of button objects, order is important
		self.buttons = [SpriteNode(**UI[k], parent=self.ui_root) for k in UI.keys()]
		for b in self.buttons:
			b.size = (GRID_SIZE * 2, GRID_SIZE * 2)
			
		self.score_label = LabelNode('0', font=('Avenir Next', 40),
																	position=(GRID_SIZE * COLUMNS + 100, GRID_SIZE * ROWS ),
																	parent=self)
		score_title = LabelNode('Score', font=('Avenir Next', 20), 
																		position=(GRID_SIZE * COLUMNS + 100, GRID_SIZE * ROWS +60),
																		parent=self)
																	
	def setup(self):
		self.background_color = COLORS["bg"]
	
		# Root node for all game elements
		self.game_field = Node(parent=self, position=GRID_POS)
		
		# Add the background grid
		self.bg_grid = build_background_grid()
		self.game_field.add_child(self.bg_grid)
		self.build_walls()	
		self.timer = INITIAL_SPEED
		initial_x = int(COLUMNS/2)
		initial_y = int(ROWS/2)
		self.head = Head((initial_y, initial_x))
		self.game_field.add_child(self.head)
		self.direction = 'up'
		# now add initial segments
		self.body = BodyControl()
		# initial body
		for i in reversed(range(1,3)):
			seg = self.body.add_segment(self.head, row=initial_y - i, col=initial_x)
			self.game_field.add_child(seg)
			
		self.spawn_food(no_items=2)
		self.score = 0
		self.level = 1
		# only set up fixed items once
		try:
			a = self.score_label.text
		except AttributeError:
			self.setup_ui()
			
	def random_location(self):
		posx = random.randint(1, COLUMNS - 2)
		posy = random.randint(1, ROWS - 2)
		return posy, posx
		
	def show_start_menu(self):
		self.pause()
		self.menu = MyMenu('New Game?', '', ['Play', 'Quit'])
		self.present_modal_scene(self.menu)
	
	def clear_tiles(self):
		for t in self.get_tiles():
			t.remove_from_parent()			
				
	def get_tiles(self, exclude=None):
		"""
		Returns an iterator over all tile objects
		"""
		if exclude is None:
			exclude = []
		for o in self.game_field.children:
			if isinstance(o, Tile) and o not in exclude:
				yield o
				
	def check_collision(self, tile_type):
		"""
		Returns tile if head would move over specified tile type
		or is already over the file type
		"""	
		for (y, x) in [self.head.next_position(self.direction),		
								   (self.head.row, self.head.col)]:
			for t in self.get_tiles(exclude=[self.head]):
				if isinstance(t, tile_type) and y == t.row and x == t.col:
					return t
		return None
	
	def update_score(self, increment=None):
		""" update score on basis of moves made,
		or input score increment"""			
		if increment is None:
			increment = 0
		self.score += increment
		self.score_label.text = str(self.score)
		
	def wall(self, start_row, start_col, direction, length):
		""" create a series of border tiles """
		y, x = start_row, start_col
		for l in range(length):
			if not self.tile_at(y,x):
				self.game_field.add_child(Border(y,x))
			dy, dx = new_pos[direction]
			y += dy
			x+= dx
			
	def build_walls(self):
		""" build bounding wall and others"""
		self.wall(0, 0, 'right', COLUMNS)
		self.wall(ROWS-1, 0, 'right', COLUMNS)
		self.wall(1, 0, 'up', ROWS-2)
		self.wall(1, COLUMNS-1, 'up', ROWS-2)
		
		# fixed walls
		self.wall(ROWS/2, 1, 'right', 9)
		self.wall(ROWS/4, COLUMNS-2, 'left', 5)
		self.wall(1, COLUMNS/4,'up', 6)
		# a few random walls
		for i in range(EXTRA_WALLS):
			self.wall(start_row=random.randrange(1, ROWS, 2),  # even number
								start_col=random.randrange(1, COLUMNS, 2),
								length=random.randint(2, int(COLUMNS/4)),
								direction=random.choice(['right', 'down'])
								)
		
		
	def eat_food(self, food):
		""" create extra body piece and remove food"""
		sound.play_effect('digital:Laser2')
		self.game_field.add_child(Explosion(food))
		food.remove_from_parent()
		self.update_score(10)
		# increase food items as body gets longer
		if int(self.body.length() % 8 )  == 0:
			self.spawn_food(2)
		else:
			self.spawn_food(1)
		
		body_seg = self.body.add_segment(self.head)
		self.game_field.add_child(body_seg)
		
		return 
		
	def tile_at(self, row, col):
		""" return tile at location, else None """
		for t in self.get_tiles():
			if t.row == row and t.col == col:
				return t
		return None
		
	def spawn_food(self, no_items=1):
		"""
		Spawns a new piece on an empty space on the  game field and adds it to game_field
		"""
		for _ in range(no_items):
			# self.print_map()
			choice = foods[next(food_cycle)]
			occupied = True
			while (occupied):
				position = self.random_location()
				posy, posx = position 
				if not self.tile_at(posy, posx):
					occupied = False
						
			new_food = Food(position, choice)
			self.game_field.add_child(new_food)
	
	def did_change_size(self):
		pass		
	
	def next_game(self):
		self.paused = True
		self.head.texture = Texture('emj:Confounded')
		self.show_start_menu()
		
	def hit_wall(self):
		""" if would hit a wall, check tile to left and right of direction
		if both clear, can randomly choose 
		if one side is clear and other blocked, then choose clear
		if both blocked, finish game
		"""
		#self.paused = True
		
		possible_direction = right_angle[self.direction] # a list
		clear = []
		# look clockwise or anticlockwise
		for d in possible_direction:
			y, x = self.head.next_position(d)		
			t = self.tile_at(y, x)	
			if not t or isinstance(t, Food):
				clear.append(d)
					
		if len(clear) == 2: # both directions
			d = random.randint(0,1)
			new_direction = right_angle[self.direction][d]
		elif len(clear) == 1: # only one possible
			new_direction = clear[0]
		else:
			self.next_game()
			self.paused = True
			new_direction = self.direction	 
		return new_direction
			
	def update(self):
		""" update the caterpillar every INITIAL_SPEED seconds
		dt is provided by Scene
		"""
		self.timer -= self.dt
		if self.timer <= 0:	
			self.timer = INITIAL_SPEED

			if self.check_collision(tile_type=Border):
				self.direction = self.hit_wall()
				
			if self.check_collision(tile_type=Body):
				self.next_game()
				
			# Check for intersection and spawn a new piece if needed
			t = self.check_collision(tile_type=Food)
			if t:
				self.eat_food(t)
				
			# now move in direction
			if not self.paused:
				self.head.move(self.direction)
				self.body.move(self.head)
				
				self.update_score()			
	
	def touch_began(self, touch):
		""" detect touch and find which button is pressed.
		button objects are stored in self.buttons, directory opposite stores keys and opposite directions
		if button in direction opposite to existing is pressed, this is ignored """
		# opposite = {"left": 'right', "right": 'left', "up": 'down', "down": 'up'}
		
		for button, dirn in zip(self.buttons, opposite): # get button object and direction
			if intersects_sprite(touch.location, button):				
				if self.direction != opposite[dirn]:
					self.direction = dirn
					break
		
	
	def touch_moved(self, touch):
		pass
	
	def touch_ended(self, touch):
		pass
		
	def menu_button_selected(self, title):
		if title.startswith('Play'):
			# start again
			self.dismiss_modal_scene()
			self.menu = None
			self.clear_tiles()
			self.paused = False
			self.setup()
			self.score_label.text = '0'
		else:
			# quit
			self.view.close()

	def print_map(self):
		""" text print map for test purposes """
		for y in range(ROWS):
			for x in range(COLUMNS):
				t = self.tile_at(y, x)
				if t is None:
					print('-',end=''),
				elif isinstance(t,Border):
					print('B', end=''),
				elif isinstance(t, Food):
					print('F', end=''),
				elif isinstance(t,Head):
					print('H',end=''),
				elif isinstance(t, Body):
					print('C', end=''),
			print()
					
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

class MyMenu(MenuScene):
	""" subclass MenuScene to move menu to right """
	def __init__(self, title, subtitle, button_titles):
		MenuScene.__init__(self, title, subtitle, button_titles)
		
	def did_change_size(self):
		# 834,1112 ipad portrait
		# 1112, 834 ipad landscape
		# 852, 393 iphone landscape

		self.bg.size = (1, 1)
		self.bg.position = self.size.w * 0.85, self.size.h / 2
		self.menu_bg.position = self.bg.position


if __name__ == '__main__':
	run(Caterpillar(), PORTRAIT, show_fps=True)
