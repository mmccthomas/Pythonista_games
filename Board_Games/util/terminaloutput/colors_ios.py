from console import set_color
# Text colors
def NO_COLOR():
   set_color(.2,.2,.2)		      # default color (white/black)
def GREEN_COLOR():
   set_color(0,1,1)	      # green
def YELLOW_COLOR():
   set_color(1,1,0)		  # yellow
def RED_COLOR():
   set_color(1,0,0)		      # red
def BLUE_COLOR():
   set_color(0,0,1)	      # blue
def DARK_PURPLE_COLOR():
   set_color(1,0,1)	  # dark purple
def GREY_COLOR():
   set_color(0.72, 0.73, 0.71)     	  # grey
def ORANGE_COLOR():
   set_color(1.0, 0.77, -0.04)   # orange (may not work on all systems)

# Background colors
def DARK_GREY_BACKGROUND():
   set_color(0.44, 0.45, 0.43)  # dark grey
