# This file contains confiyration of sprites for
# kye. 
# require variables image_dict and lookup to be generated.
# lookup needs char : (spritename, ) at least. 
# other parameters are project specific
# format of .kye file
"""
number of levels (int) 
level name
hint text
completion text
game lines (20 for kye)
555555555555555555555555555555
5T   e       K*  a    d e   E5
5    b 455556        a  b    5
5    b dvvvvd           b    5
5    b dvvvvd          ab    5
5ebbbe eeBBee       c   ebbbe5
5               a            5
5 8rre                a ell8 5
5 5>>e      s  S        e<<5 5
5 5>>B                  B<<5 5
5 5>>B               b  B<<5 5
5 5>>e      S  s     U  e<<5 5
5 2rre               b  ell2 5
5                 bRbb       5
5ebbbe eeeeee  7555559  ebbbe5
5    b u^^^^u  5     5  b    5
5    b u^^^^u  5     5  b    5
5    b 455556  5     5  b    5
5C   e         e  [  e  e   ~5
555555555555555555555555555555
"""
# character to icon dictionary
# character (class string, image_name)

from collections import defaultdict
from PIL import Image
import base_path
base_path.add_paths(__file__)
import Kye.Kye

# this is the order in which sprites appear in the spritesheet
imagelist = [
'black_hole_1', 'black_hole_2', 'black_hole_3','black_hole_4',
'black_hole_swallow_1', 'black_hole_swallow_2',
'black_hole_swallow_3', 'black_hole_swallow_4',
'blank', 'blob_1', 'blob_2', 'blob_3', 'blob_4', 
'block', 'block_timer_0', 'block_timer_1', 'block_timer_2', 
'block_timer_3', 'block_timer_4', 'block_timer_5', 'block_timer_6',
'block_timer_7', 'block_timer_8', 'block_timer_9', 
'blocke', 'blockr',
'diamond_1', 'diamond_2', 'gnasher_1', 'gnasher_2',
'kye', 'kye_fading', 'kye_faint',
'oneway_down_1', 'oneway_down_2', 'oneway_left_1',
'oneway_left_2', 'oneway_right_1', 'oneway_right_2',
'oneway_up_1', 'oneway_up_2',
'rocky_down', 'rocky_left', 'rocky_right',
'rocky_shooter_down', 'rocky_shooter_left', 'rocky_shooter_right',
'rocky_shooter_up', 'rocky_up',
'sentry_down', 'sentry_left', 'sentry_right', 'sentry_up',
'slider_down', 'slider_left', 'slider_right',
'slider_shooter_down', 'slider_shooter_left',
'slider_shooter_right', 'slider_shooter_up', 
'slider_up', 'snake_1', 'snake_2',
'spike_1', 'spike_2',
'sticky_horizontal', 'sticky_vertical',
'turner_anticlockwise', 'turner_clockwise',
'twister_1', 'twister_2',
'wall1', 'wall2', 'wall3', 'wall4', 'wall5', 'wall6',
'wall7', 'wall8', 'wall9',  
] 
     
cell_lookup = {
        'K' : ("kye",'K'),
        '1' : ("wall1", ''),
        '2' : ("wall2", ''),
        '3' : ("wall3", ''),
        '4' : ("wall4", ''),
        '5' : ("wall5", '5'),
        '6' : ("wall6", ''),
        '7' : ("wall7", ''),
        '8' : ("wall8", ''),
        '9' : ("wall9", ''),
        'b' : ("block", 'B'),
        'B' : ("blockr", 'b'),
        'e' : ("blocke", 'e'),
        '*' : ("diamond_1",'*'),
        'a' : ("turner_clockwise", 'c'),
        'c' : ("turner_anticlockwise", 'a'),
        'D' : ("sentry_down", 'L'),
        'U' : ("sentry_up", 'R'),
        'L' : ("sentry_left", 'U'),
        'R' : ("sentry_right", 'D'),
        '[' : ("spike_1", 'E'),
        'E' : ("gnasher_1", 'T'),
        'T' : ("twister_1", '~'),
        '~' : ("snake_1", 'C'),
        'C' : ("blob_1", '['),
        's' : ("sticky_vertical", 'S'),
        'S' : ("sticky_horizontal", 's'),
        'u' : ("slider_up", 'r'),
        'd' : ("slider_down", 'l'),
        'l' : ("slider_left", 'u'),
        'r' : ("slider_right", 'd'),
        '^' : ("rocky_up", '>'),
        'v' : ("rocky_down", '<'),
        '<' : ("rocky_left", '^'),
        '>' : ("rocky_right", 'v'),
        'H' : ("black_hole_1", 'H'),
        '}' : ("block_timer_3", '|'), 
        '|' : ("block_timer_4", '{'), 
        '{' : ("block_timer_5", 'z'), 
        'z' : ("block_timer_6", 'y'), 
        'y' : ("block_timer_7", 'x'), 
        'x' : ("block_timer_8", 'w'), 
        'w' : ("block_timer_9", '}'), 
        'h' : ("oneway_down_1", 'g'),
        'i' : ("oneway_up_1", 'f'),
        'f' : ("oneway_right_1", 'h'),
        'g' : ("oneway_left_1", 'i'),
        'A' : ("slider_shooter_up", 'F'),
        'F' : ("rocky_shooter_up", 'A'),
        ' ' : ("blank", '')
        }
cell_lookup1 = {
        'K': ('Kye',),
        '1': ('Wall', 1),
        '2': ('Wall', 2),
        '3': ('Wall', 3),
        '4': ('Wall', 4),
        '5': ('Wall', 5),
        '6': ('Wall', 6),
        '7': ('Wall', 7),
        '8': ('Wall', 8),
        '9': ('Wall', 9),
        'b': ('Block', 0, False),
        'B': ('Block', 0, True),
        'a': ('Block', 1, False),
        'c': ('Block', -1, False),
        'e': ('Edible',),
        '*': ('Diamond',),
        'D': ('Sentry', 0, 1),
        'U': ('Sentry', 0, -1),
        'L': ('Sentry', -1, 0),
        'R': ('Sentry', 1, 0),
        '[': ('Monster', 2),
        'E': ('Monster', 0),
        'T': ('Monster', 1),
        '~': ('Monster', 3),
        'C': ('Monster', 4),
        's': ('Magnet', 0, 1),
        'S': ('Magnet', 1, 0),
        'u': ('Slider', 0, -11, False),
        'd': ('Slider', 0, 1, False),
        'l': ('Slider', -1, 0, False),
        'r': ('Slider', 1, 0, False),
        '^': ('Slider', 0, -1, True),
        'v': ('Slider', 0, 1, True),
        '<': ('Slider',-1, 0, True),
        '>': ('Slider', 1, 0, True),
        'H': ('BlackHole',),
        '}': ('Block', 0, False, 3),
        '|': ('Block', 0, False, 4),
        '{': ('Block', 0, False, 5),
        'z': ('Block', 0, False, 6),
        'y': ('Block', 0, False, 7),
        'x': ('Block', 0, False, 8),
        'w': ('Block', 0, False, 9),
        'h': ('OneWay', 0, 1),
        'i': ('OneWay', 0, -1),
        'f': ('OneWay', 1, 0),
        'g': ('OneWay',-1, 0),
        'A': ('Shooter', False),
        'F': ('Shooter', True),
        }

"""
        "diamond_1", "The object of the game is to collect all the diamonds." 
        "wall5", "These are solid walls.",
        "block", "These are blocks, which you can push.",
        "slider_right", "Sliders move in the direction of the arrow until they hit"},
        "		 an obstacle."
        "rocky_right", "Rockies move like sliders, but they roll around round"},
         "   		 objects, like rounded walls and other rockies."},
        "blocke", "Soft blocks you can destroy by moving into them."},
        "blob_1"), "Monsters kill you if they touch you."},
        "				 You do have 3 lives, though."},
        "gnasher_1",  ".     Gnasher"},
        "spike_1"),  ".     Spike"},
        "twister_1",  ".     Twister"},
        "snake_1",   ".     Snake"},
        "sentry_right",  "Sentries pace back and forward, and push other objects."},
        "black_hole_1", "Objects entering a black hole are destroyed." },
        "slider_shooter_right", 'title': "Shooters create new sliders or rockies."},
        "block_timer_5", "Timer blocks disappear when their time runs out." },
        "turner_clockwise",  "Turning blocks change the direction of sliders and rockies."},
        "sticky_horizontal",  "Magnets (also called sticky blocks) allow you to pull objects."},
        "oneway_right_1", "One-way doors only allow Kye though, and only in one direction."},

        """                
IMAGE_NAME = 'image.png'

lookup = defaultdict()
# combine the two dictionaries
for k, v in cell_lookup.items():
    if k in cell_lookup1:
       lookup[k] = tuple(list(v) + list(cell_lookup1[k]))
    else:
       lookup[k] = v   

def load_images():    
    # combined image
    spritesheet = Image.open(IMAGE_NAME)
    w, h = spritesheet.size
    # now have images list and spritesheet
    # 10 x 8 array gap of 0
    tsize = 16
    image_dict = {}
    for i, image in enumerate(imagelist):
        x = (i % 10) * tsize 
        y = int(i / 10) * tsize 
        w1 = tsize 
        h1 = tsize 
        t = spritesheet.crop((x, y, x+w1, y+h1))
        image_dict.setdefault(image, t)    
    return image_dict

image_dict = load_images() 
run_module = Kye.Kye 
          
if __name__ == '__main__':
   print(lookup)
   
