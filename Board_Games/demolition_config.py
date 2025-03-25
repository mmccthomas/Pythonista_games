from scene import Vector2, get_screen_size
screen_width, screen_height = get_screen_size()
GRID_POS = Vector2(10, 40)
GRID_SIZE= 20

COLUMNS = int(screen_width / GRID_SIZE) - 5 # 20
ROWS = int(screen_height / GRID_SIZE) - 4 #30
STARTROW = ROWS - 1
STARTCOL = 3


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
# row, col
pieces =[[0,0], 
				[-1,0],
		 [0,-1], [0, 1],
		 [1,-1], [1, 1],
		[1,-2],[1,2],
		[2, -2], [2,-1], [2,0], [2, 1], [2,2]]
# tiles are Row, Column

colours = [
	COLORS["cyan"],COLORS["yellow"], COLORS["purple"],  
	COLORS["blue"], COLORS["red"] , COLORS["green"],  
	COLORS["orange"]
]
scoring_points = [0, 100, 300, 500, 800]
INITIAL_FALL_SPEED = .1
if COLUMNS > 20:
	 INITIAL_FALL_SPEED = 0.05
INITIAL_LINE_SPEED = 5
LOCK_DELAY = 0.5
