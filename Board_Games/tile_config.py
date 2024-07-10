from scene import Vector2, get_screen_size
import numpy as np
screen_width, screen_height = get_screen_size()
GRID_POS = Vector2(10, 40)
SIZE = 7
GRID_SIZE= screen_width // (2*SIZE) 
TILES = ""
INITIAL_LINE_SPEED = 1
MOVE_SPEED = .3
TOTAL_TIME = 20.0


COLORS = {
	"bg": "#232323",
	"red": "#FF5555",
	"blue": "#786CF5",
	"green": "#327834",
	"cyan": "#a1ffff",
	"orange": "#FF8C32",
	"purple": "#bc36ff",
	"lime": "#92CA49",
	"yellow": "#ffff00",
		"grey": "#646473",
}
