from scene import Vector2, get_screen_size
import numpy as np

COLUMNS = 10
ROWS = 20
STARTROW = ROWS - 1
STARTCOL = 3
GRID_POS = Vector2(10, 150)
GRID_SIZE= 20

COLORS = {
	"bg": "#232323",
	"red": "#FF5555",
	"grey": "#646473",
	"blue": "#786CF5",
	"orange": "#FF8C32",
	"green": "#327834",
	"lime": "#92CA49",
	"purple": "#bc36ff",
	"cyan": "#a1ffff",
	"yellow": "#ffff00"
}

UI = {
	"LEFT_BTN": {
		"texture": 'typw:Left',
		"size": (100,100),
		"position": Vector2(50, 100)
	},
	"RIGHT_BTN": {
		"texture": 'typw:Right',
		"size": (100,100),
		"position": Vector2(150, 100)
	},
	"ROTATE_BTN": {
		"texture": 'typw:Refresh',
		"size": (100,100),
		"position": Vector2(250, 100)
	},
	"DOWN_BTN": {
		"texture": 'typw:Down',		
		"size": (100,100),
		"position": Vector2(350, 100)
	}

}
# tiles are Row, Column
pieces = np.array([
    [[0,1],[0,0],[0,2],[0,3]],#I
    [[0,0],[0,1],[1,0],[1,1]],#O
    [[0,1],[0,0],[1,1],[0,2]],#T
    [[0,1],[1,0],[0,0],[0,2]],#J
    [[0,1],[1,0],[1,1],[0,2]],#Z
    [[0,1],[0,0],[1,1],[1,2]],#S
    [[0,1],[0,0],[0,2],[1,2]], #L
])
pieces_names = ['I', 'O', 'T', 'J', 'Z', 'S', 'L']
rot_matrix = np.array([[0,-1],[1,0]])
colours = [
	COLORS["cyan"], #I
	COLORS["yellow"],  #O
	COLORS["purple"],  #T
	COLORS["blue"], #J
	COLORS["red"] , #Z
	COLORS["green"],  #S
	COLORS["orange"] #L
]
scoring_points = [0, 100, 300, 500, 800]
INITIAL_FALL_SPEED = 1
LOCK_DELAY = 0.5
