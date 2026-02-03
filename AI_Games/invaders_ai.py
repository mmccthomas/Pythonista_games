# Simple Galaxian game for Pythonista using the scene module
# i am going to try to make this as accurate as possible
# - add more accurate flight paths
# - react to loss of flagship
# flagship flees to next wave (max 2)
# get more aggressive as wave increases.
# get more chargers as wave increases ( max 7 at any one time)
# Game logic taken from game disassembly https://seanriddle.com/galaxian.asm
import scene
import random
import math
from math import pi, sin, cos
from scene import Texture, Point
import sound
import ui
import numpy as np
from operator import attrgetter
from collections import defaultdict
from time import sleep
import objc_util
import ctypes
from time import time
import joystick
import spritesheet
from PIL import Image, ImageFont, ImageDraw
# --- Game Constants ---
# ADAPT to screen size
width, height = scene.get_screen_size()
# width device
devices = {393: {'device': 'iphone_portrait', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},
           744: {'device': 'ipad_mini_portrait', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},
           834: {'device': 'ipad_portrait', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},
           852: {'device': 'iphone_landscape', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},
           1024: {'device': 'ipad13_portrait', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},
           1112: {'device': 'ipad_landscape',  'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},           
           1133: {'device': 'ipad_mini_landscape', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 70},
           1366: {'device': 'ipad13_landscape', 'spc_x': 70, 'spc_y': 60, 'strt_y': 120, 'ply_s': 80, 'inv_s': 45}   
           }
  
# device size adjustable sizes         
SCREEN_WIDTH = min(768, width)
SCREEN_HEIGHT = height #min(1024, height)
JOYSTICK_DEAD_ZONE = 0.1
device_type = devices[int(width)]
SPACING_X = device_type['spc_x'] # Spacing between invaders in convoy
SPACING_Y = device_type['spc_y'] # Spacing between invaders in convoy
START_Y = SCREEN_HEIGHT - device_type['strt_y'] # Starting Y position for invader convoy
PLAYER_SIZE = device_type['ply_s']
INVADER_SIZE = device_type['inv_s']

SOUND = True  
PLAYER_Y = 150
PLAYER_SPEED = 300
PLAYER_SHOOT_COOLDOWN = 0.5
CONVOY_SPEED = 60
DIVE_SPEED = 0.5
RETURN_SPEED = 150
BULLET_SPEED = 250
ROWS = 5
COLUMNS = 10

CONVOY_MOVE_DIRECTION = 1 # 1 for right, -1 for left
CONVOY_MOVE_INTERVAL = 1.5 # Time before invaders change direction/move down
INVADER_MOVE_INTERVAL = 0.3 # Time before invaders change image
INTERVAL_CHARGE_INTERVAL = 3 # Time interval between charger
FLAGSHIP_LOST_PARALYSIS = 2 # time when chargers will not shoot
NEAR_BOTTOM_OF_SCREEN = 400 

FAST_FIRE = True
BULLET_SIZE = 10
INVADER_BULLET_SPEED = 250
INVADER_BULLET_SIZE = 15

# Invader states
STATE_CONVOY = 'convoy'
STATE_CHARGER = 'charging'
STATE_CHARGER_ARC = 'arc'
STATE_RETURNING = 'returning'
STATE_READY_TO_ATTACK = 'ready'
STATE_AGGESSIVE = 'aggressive'

STATE_CONVOY = 'convoy'
STATE_PACKS_BAGS = 'prepare'
STATE_FLIES_IN_ARC = 'arc'
STATE_READY_TO_ATTACK = 'ready'
STATE_ATTACKING_PLAYER = 'attacking'
STATE_NEAR_BOTTOM_OF_SCREEN = 'near_bottom'
STATE_REACHED_BOTTOM_OF_SCREEN = 'at bottom'
STATE_RETURNING_TO_SWARM = 'returning'
STATE_CONTINUING_ATTACK_RUN_FROM_TOP_OF_SCREEN = 'continue'
STATE_FULL_SPEED_CHARGE ='full_speed'
STATE_ATTACKING_PLAYER_AGGRESSIVELY = 'aggressive'
STATE_LOOP_THE_LOOP = 'loop'
STATE_COMPLETE_LOOP = 'finish loop'
LIVES = 30

# calculate midpoint between initial swarm and player
MIDPOINT_Y = (START_Y - ROWS * SPACING_Y - PLAYER_Y) / 2 + PLAYER_Y



def load_custom_font(file):
  #https://marco.org/2012/12/21/ios-dynamic-font-loading
  

  CTFontManagerRegisterFontsForURL = objc_util.c.CTFontManagerRegisterFontsForURL
  CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
  CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
  
  CFURLCreateWithString = objc_util.c.CFURLCreateWithString
  CFURLCreateWithString.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
  CFURLCreateWithString.restype = ctypes.c_void_p 
  UIFont = objc_util.ObjCClass("UIFont")
  font_url = CFURLCreateWithString(None, objc_util.ns(file), None)
  
  error = ctypes.c_void_p(None)
  success = CTFontManagerRegisterFontsForURL(objc_util.ObjCInstance(font_url), 0, ctypes.byref(error))
  print(objc_util.ObjCInstance(error))
  print("success:", success)
  
  font = UIFont.fontWithName_size_("PressStart2P-Regular", 15)
  print(font)  
# --- Game Classes ---

class Player(scene.SpriteNode):
    # player can shoot only one bullet at a time
    def __init__(self, position=(SCREEN_WIDTH/2, PLAYER_Y), parent=None, **kwargs):
        # Use a simple shape or color for the player (can replace with image)
        super().__init__(parent.sprites['player'], position=position, size=(PLAYER_SIZE, PLAYER_SIZE), **kwargs)
        #self.scale = .5
        self.speed = PLAYER_SPEED
        self.can_shoot = True
        self._shoot_timer = 0
        self.lives = LIVES

    def update(self, dt):
        # Handle shooting cooldown
        #if not self.can_shoot:
        #    self._shoot_timer += dt
        #    if self._shoot_timer >= PLAYER_SHOOT_COOLDOWN:
        #        self.can_shoot = True
        #        self._shoot_timer = 0
        pass

    def move(self, direction, dt):
        # Move the player left or right
        new_x = self.position.x + direction * self.speed * dt
        # Clamp the player position within screen bounds
        self.position = (max(PLAYER_SIZE/2, min(SCREEN_WIDTH - PLAYER_SIZE/2, new_x)), self.position.y)

    def shoot(self):
        # Create and return a new player bullet sprite
        if self.can_shoot:
            bullet = PlayerBullet(position=(self.position.x, self.position.y + PLAYER_SIZE/2))
            if not FAST_FIRE:
                self.can_shoot = False
            return bullet
        return None

class Invader(scene.SpriteNode):
    """
    ;stage of life the inflight alien is at, then call the appropriate function
      06 0D         ; $0D06                  ; INFLIGHT_ALIEN_PACKS_BAGS
      71 0D         ; $0D71                  ; INFLIGHT_ALIEN_FLIES_IN_ARC
      D1 0D         ; $0DD1                  ; INFLIGHT_ALIEN_READY_TO_ATTACK
      2B 0E         ; $0E2B                  ; INFLIGHT_ALIEN_ATTACKING_PLAYER
      6B 0E         ; $0E6B                  ; INFLIGHT_ALIEN_NEAR_BOTTOM_OF_SCREEN
      99 0E         ; $0E99                  ; INFLIGHT_ALIEN_REACHED_BOTTOM_OF_SCREEN
      07 0F         ; $0F07                  ; INFLIGHT_ALIEN_RETURNING_TO_SWARM
      3C 0F         ; $0F3C                  ; INFLIGHT_ALIEN_CONTINUING_ATTACK_RUN_FROM_TOP_OF_SCREEN 
      66 0F         ; $0F66                  ; INFLIGHT_ALIEN_FULL_SPEED_CHARGE 
      AF 0F         ; $0FAF                  ; INFLIGHT_ALIEN_ATTACKING_PLAYER_AGGRESSIVELY
      1F 10         ; $101F                  ; INFLIGHT_ALIEN_LOOP_THE_LOOP
      8E 10         ; $108E                  ; INFLIGHT_ALIEN_COMPLETE_LOOP
      91 10         ; $1091                  ; INFLIGHT_ALIEN_UNKNOWN_1091 set to INFLIGHT_ALIEN_FULL_SPEED_CHARGE
     """
    def __init__(self, position, convoy_position, invader_type, location=None, parent=None,**kwargs):
        
        scores = {'Blue': 30, 'Purple': 40, 'Red': 50, 'Flagship': 60}
        sprites = parent.sprites
        self.types = {'Blue': [sprites['blue1'], sprites['blue2']], 
                      'Purple': [sprites['purple1'], sprites['purple2']], 
                      'Red': [sprites['red1'], sprites['red2']],
                      'Flagship': [sprites['flagship'], sprites['flagship']]}
        
        
        self.alien_type = random.randint(0,1)
        shape = self.types[invader_type][self.alien_type]

        super().__init__(shape, position=position,color='white', size=(INVADER_SIZE, INVADER_SIZE), **kwargs)
        #self.scale = .5
        self.convoy_position = convoy_position # Original position in convoy
        self.invader_type = invader_type
        self.flank = None
        self.loc = (0,0)
        self.state = STATE_CONVOY
        #self.started_charge = False
        self.alien_timer = INVADER_MOVE_INTERVAL 
        self.charge_target = None # Player position when charge started
        self.return_target = None # Position to return to in convoy
        self.escort_no = 0 # escort 1, 2 or 0
        self.score_value = scores[invader_type] # Basic scoring based on type
        
        # These parameters taken from game disassembly https://seanriddle.com/galaxian.asm
        self.aggressive = False
        self.sortie_count = 0
        self.dive_speed = DIVE_SPEED
        self.dive_time = 0 # set to zero start of charge
        self.can_shoot = False
        
        self.pivot_value = 100 # how close to player invader aims
        self.clockwise = True # direction leaves convoy
        
        
    def direction_vector(self, target):
        # set dx, dy from vector
        distance = self.distance(self.position, target)
        d_x,  d_y = self.position - target
        return Point(-d_x / distance, -d_y / distance)
        #theta = math.atn2(d_x/ d_y)
           
    def normalize(self, a):
         # convert to -1, 0, 1
         return Point(*tuple([0 if x == 0 else int(x/abs(x)) for x in a]))
         
    def distance(self, point_a, point_b):
        return math.hypot(*(point_a - point_b))
        
    def bezier_curve(self, p0, p1, p2, p3, p4,  t):
        """Quartic Bézier curve function.
      Args:
          all p are numpy array(x,y)
          p0 and p4 are the start and end points of the curve.
          p1 p2 p3 are the control points that define the shape and curvature of the line.                    
          t is a parameter that varies from 0 to 1, tracing the curve.             
             p1
                   p2      
                          p3            
           p0               p4
        """        
        return (1 - t)**4 * p0 + 4 * (1 - t)**3 *t * p1 + 6 * (1 - t)**2 * t**2 * p2 + 4*t**3 * (1-t) * p3 + t**4 * p4
        
    def derivative_bezier_curve(self, p0, p1, p2, p3, p4,  t):
        """
        Calculates the derivative (tangent vector) of a quartic Bézier curve at a given parameter t.            
        Args:
            control_points  P0, P1, P2, P3, P4 where each point is a NumPy array (e.g., [x, y]).
            t (float): The parameter value (0 <= t <= 1).    
        Returns:
            angle of tangent in radians at parameter t            
        """  
        n = 4  # Degree of the Bézier curve
        # Calculate the new control points for 
        Q0 = n * (p1 - p0)
        Q1 = n * (p2 - p1)
        Q2 = n * (p3 - p2)
        Q3 = n * (p4 - p3)
    
        # The derivative curve is a cubic Bézier curve with control points Q0, Q1, Q2, Q3
        # Bernstein basis polynomials for degree 3
        B0_3 = (1 - t)**3
        B1_3 = 3 * (1 - t)**2 * t
        B2_3 = 3 * (1 - t) * t**2
        B3_3 = t**3
        vector = B0_3 * Q0 + B1_3 * Q1 + B2_3 * Q2 + B3_3 * Q3
        return math.atan2(*vector)     
     
    def leave_convoy(self, dirn):
        """Fixed half circle which leaves alien to
        left or right and one space below
        this is ip point 
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = INVADER_SIZE/2
        p0 = np.array(self.position) 
        p4 = np.array(self.position + Point(d*delta*2, -delta*2)) #below player
        p1 = np.array(self.position + Point(d*delta, delta)) # loop left or right
        p2 = np.array(self.position + Point(d*delta*2, 0))
        p3 = np.array(self.position + Point(d*delta*2, -delta)) # to left or right of player
        return p0, p1, p2, p3, p4
        
    def blue_attack(self, dirn):
        """Bezier based attack
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = SPACING_X
        p0 = np.array(self.position) 
        p4 = np.array(self.charge_target - Point(0,PLAYER_Y)) #below player
        p1 = np.array(self.position - Point(0, 2*delta)) # loop left or right
        p2 = np.array((SCREEN_WIDTH/2, MIDPOINT_Y))
        p3 = np.array(self.charge_target - d * Point(3*delta, 0)) # to left or right of player
        return p0, p1, p2, p3, p4
        
           
    def purple_attack(self, dirn):
        """Bezier based attack
        purple gets closer during dive
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = SPACING_X
        p0 = np.array(self.position) 
        p4 = np.array(self.charge_target - Point(0,PLAYER_Y)) #below player
        p1 = np.array(self.position - Point(0, 2*delta)) # loop left or right
        p2 = np.array((SCREEN_WIDTH/2, MIDPOINT_Y))
        p3 = np.array(self.charge_target - Point(d*2*delta, -delta/2)) # to left or right of player and above
        return p0, p1, p2, p3, p4
         
    def flag_attack(self, dirn):
        """Bezier based attack
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = SPACING_X
        p0 = np.array(self.position) 
        p4 = np.array(self.charge_target - Point(0,PLAYER_Y)) #below player
        p1 = np.array(self.position - Point(0, delta)) # loop left or right
        p2 = np.array((SCREEN_WIDTH/2, MIDPOINT_Y))
        p3 = np.array(self.charge_target - d * Point(2*delta, 0)) # to left or right of player
        return p0, p1, p2, p3, p4
        
    def red_attack(self, dirn):
        """Bezier based attack
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = SPACING_X
        p0 = np.array(self.position) 
        p4 = np.array(self.charge_target - Point(0,PLAYER_Y)) #below player
        p1 = np.array(self.position -  Point(0, 3*delta)) # loop left or right
        p2 = np.array((SCREEN_WIDTH/2, MIDPOINT_Y))
        p3 = np.array(self.charge_target - d * Point(2*delta, 0)) # to left or right of player
        return p0, p1, p2, p3, p4
        
    def aggressive1_attack(self, dirn):
        """zigzag direct to player
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = SPACING_X
        initial_point = Point(self.charge_target.x, MIDPOINT_Y)
        p0 = np.array(self.position) 
        p4 = np.array(initial_point) #at ip
      
        p1 = np.array(self.position - Point(-delta*d, 2*delta))# far left(right)
        p2 = np.array(self.position - Point(6*delta*d, delta)) # far right(left)
        p3 = np.array(initial_point - Point(-2*delta*d, -delta)) # far left or right of player
        return p0, p1, p2, p3, p4   
        
    def aggressive2_attack(self, dirn):
        """zigzag direct to player
        dirn is clockwise or anticlockwise"""
        d = 1 if dirn else -1
        delta = SPACING_X
        initial_point = Point(self.charge_target.x, MIDPOINT_Y)
        p0 = np.array(initial_point)
        p4 = np.array(self.charge_target-Point(0, 2*delta)) #at player
        p1 = np.array(initial_point - Point(d*2*delta, delta))# far left(right)
        p2 = np.array(initial_point + Point(d*6*delta, -delta))# far left(right)
        p3 = np.array(initial_point - Point(d*2*delta, 2*delta))# far left(right)
        return p0, p1, p2, p3, p4   
        
    def loop_the_loop(self, dirn):
        """make a loop
        dirn is clockwise or anticlockwise
        control points come from an AI generated optimisation
        apply rotation to match entry angle to loop to end of 1st
        vector
        --- Optimization Result ---
        radius is 0.2, with initial point at 0.0
         --- Optimization Result ---
        Optimized RMS Error: 0.0007"""
        d = 1 if dirn else -1
        theta = d * 0.3
        delta = 5 * SPACING_X * 3
        
        def rotate(point, theta):         
            # rotate a vector
            point = np.array(point)
            R = np.array([[cos(theta), -sin(theta)], 
                          [sin(theta), cos(theta)]])
            return Point(*np.dot(R, np.atleast_2d(point).T).reshape((1,2))[0])
            
        P0_P4 = [[0, 0],  
                 [-0.24222455 * d, -0.10665386],  # p1
                 [0.11748146 * d, -0.46737183],  # p2
                 [0.26380134 * d, 0.02033827],   # p3                                           
                 [0, 0]]         
        initial_point = Point(self.charge_target.x, MIDPOINT_Y)
        # rotate and scale        
        profile = [np.array(initial_point + delta*rotate(p, theta))   
                   for p in P0_P4]
        return tuple(profile)
        
    def aggressive_attack(self, dirn):
        # aggressive attack made up of 2 zizags and optional loop
        loop = random.choice([True, False])
        profile = [self.aggressive1_attack(dirn),
                   self.loop_the_loop(dirn) if loop else None,
                   self.aggressive2_attack(dirn)]
        return profile
        
    def speedup(self, factor):
        if self.position.y < NEAR_BOTTOM_OF_SCREEN:
            self.dive_speed = DIVE_SPEED * factor
        else:
            self.dive_speed = DIVE_SPEED   
        return self.dive_speed
        
    def time_shots(self, min_time=10, max_time=100, min_shots=1, max_shots=4):
        # produce a list of shot times
        # no_shots is random number berween min_shot, max_shots
        # first shot between min_time and max_time /2
        # subsequent shots between last shot and max_time
        no_shots = random.randint(min_shots, max_shots)
        tshots = [random.randint(min_time, max_time // 2)]
        for shot in range(no_shots-1):
             tshots.append(random.randint(tshots[-1], max_time))
        return tshots
                  
    def charger_setup(self):
        """ Each type has an attack profile, created  bezier curves to mimic original
        rotation given by tangent to profile. Possible to enable rotation later in profile
        # all perform initial 90deg arc up and l/r
        # after rotation get dx alien to player
        # target on player at this point
        # decide when to drop bomb
        # set up alien for attack
        # choose profile, aggressive 
        # and whether escorting flagship
        
        
        # original had some rotation also
        # all perform initial 90deg arc up and l/r
        # after rotation get dx alien to player
        # target on player at this point
        # decide when to drop bomb
        # wont shoot if flagship hit
        # When an alien is close to the horizontal plane where the player resides, it speeds up to zoom by (or into) the player
         
        # If the alien is not a flagship, it will always return to the top of the screen.
 
        # If no  charging aliens are aggressive  and have blue or purple the alien will rejoin the swarm.
        # Otherwise, if the criteria above is not satisfied, the alien will keep attacking the player.  
        #The aggressivd inflight alien is now going to fly at full speed and zigzag to make it harder to shoot. 
        #It won't drop bombs, but it will gravitate towards the player.
        
        # When the alien gets to the vertical (as the player sees it) centre of the screen, the alien will loop
        # the loop if there's enough space to do so. 
        
        #After the loop is complete, the alien will start shooting.
        # aggressive will also set if no invaders <8"""
        
        # TODO
        # calculate how far away from the player inflight aliens can be before they can start shooting at you.
        #The minimum shooting distance increases as more aliens are killed, making the aliens shoot more often.   
        if self.aggressive:
             self.profile  = self.aggressive_attack(self.clockwise)
             self.aggr_phase = 0 
             # shoots only in phase 2
             self.tshots = self.time_shots(min_shots=1, max_shots=4)        
             return
             
        match self.invader_type:
            case 'Blue':                             
                # When they charge, their maneuvers tend to be fairly simple
                # leave the convoy (takes roughly a second);
                # orient themselves on your position *after* that;
                # move in your direction at a set angle which isn't very wide;
                # typically drop 3 or 4 shots, which move in the same direction the alien does;
                # cannot turn around once their maneuver has begun;
                
                self.profile = self.blue_attack(self.clockwise)                
                self.tshots = self.time_shots(min_shots=1, max_shots=4)                               
                    
            case 'Purple':
                # move at much wider angles and also tend to turn around during their descend,
                #- slow down about halfway their maneuver and then turn in the other direction;
                #- will always perform this turn regardless of where your craft is;
                #- typically fire 4 shots, one or two of which fall during their turning point;
                #- aim all their shots in the direction they initially turned in;
                # - usually stop firing after they make their turn;
   
                self.profile = self.purple_attack(self.clockwise)
                self.tshots = self.time_shots(max_time=60, min_shots=3, max_shots=4)                
           
            case 'Red':
                # on their own
                # maneuvers which are not as wide as those of the purple Galaxians, but more erratic and harder to predict
                # need know escort=1, escort=2 or single escort=0     
                self.profile = self.red_attack(self.clockwise)     
                if self.parent.flagship:
                    self.tshots = self.time_shots(min_shots=1, max_shots=2)
                else:
                    self.tshots = self.time_shots(min_shots=3, max_shots=4)            
            case 'Flagship':         
                self.profile = self.flag_attack(self.clockwise)
                self.tshots = self.time_shots(min_shots=3, max_shots=4)                
       
        #print(self.invader_type, self.tshots)                             
            
    def charger_logic(self, dt):
        """ 
        # wont shoot if flagship hit
        # When an alien is close to the horizontal plane where the player resides, it speeds up to zoom by (or into) the player
         
        # If the alien is not a flagship, it will always return to the top of the screen.
 
        # If no  charging aliens are aggressive  and have blue or purple the alien will rejoin the swarm.
        # Otherwise, if the criteria above is not satisfied, the alien will keep attacking the player.  
        #The aggressivd inflight alien is now going to fly at full speed and zigzag to make it harder to shoot. 
        #It won't drop bombs, but it will gravitate towards the player.
        
        # When the alien gets to the vertical (as the player sees it) centre of the screen, the alien will loop
        # the loop if there's enough space to do so. 
        
        #After the loop is complete, the alien will start shooting.
        # aggressive will also set if no invaders <8
        """
        escort_offset = {0: Point(0, 0), 1: Point(0, -SPACING_Y), 2: Point(SPACING_X*.75, -SPACING_Y)}
        t = dt * self.t_charge*self.dive_speed
        
        if self.aggressive:
            # self.profile is a list of tuples                    
            p = self.profile[self.aggr_phase]
            if not p: # no loop
                self.aggr_phase += 1
                p = self.profile[self.aggr_phase]
            self.position = self.bezier_curve(*p, t)      
            self.rotation =  self.derivative_bezier_curve(*p, t)               
            if t > 1.0:
               self.aggr_phase += 1
               self.t_charge = 0                        
        else:
            match self.invader_type:
                case 'Blue': 
                    START_ROTATION = 50                                               
                    #self.dive_speed = self.speedup(factor=0.7)                           
                    self.position = self.bezier_curve(*self.profile, t)        
                    if self.t_charge > START_ROTATION:
                        self.rotation =  self.derivative_bezier_curve(*self.profile, t)                                                                     
              
                case 'Purple':                
                    self.position = self.bezier_curve(*self.profile, t)       
                    self.rotation = self.derivative_bezier_curve(*self.profile, t)                                
               
                case 'Red':                
                    if self.parent.flagship: # formate on flagship                                       
                        self.position = self.parent.flagship.position + escort_offset[self.escort_no]
                        self.rotation = self.parent.flagship.rotation  
                    else:
                        self.position = self.bezier_curve(*self.profile, t)
                        self.rotation = self.derivative_bezier_curve(*self.profile, t)                                        
                        
                case 'Flagship':                
                    self.position = self.bezier_curve(*self.profile, t)
                    self.rotation = self.derivative_bezier_curve(*self.profile, t)                                
                
        self.t_charge += 1
        #print(self.invader_type, self.t_charge, self.aggr_phase, self.tshots)
        # handle shots
        if self.aggressive and self.aggr_phase != 2:
            pass
        elif self.tshots and self.t_charge >= self.tshots[0]:            
            self.shoot()
            #print('shoot')
            self.tshots.pop(0) 
       
        if SOUND and self.sound:           
            self.sound.pitch=(0.01*(100-self.t_charge))
        
    def gone_offscreen(self):
       # trigger offscreen if charging and below convoy
       if self.bbox.min_y > MIDPOINT_Y:
          return False
       if self.bbox.min_y <= INVADER_SIZE/2:
          return True
       if self.bbox.min_x <= 0 or self.bbox.max_x > SCREEN_WIDTH:
          return True
       return False
                   
    def shoot(self):
        # spawn bullet
        # hold if flagship lost
        if self.parent.flagship_hit > 0:
           print('flagship lost', self.parent.flagship_hit, self.parent.t)
           if self.parent.t < self.parent.flagship_hit + FLAGSHIP_LOST_PARALYSIS:
              # dont shoot              
              return
           else:
               self.parent.flagship_hit = 0                       
        bullet = InvaderBullet(position=self.position,
                               parent=self.parent)
        self.parent.invader_bullets.append(bullet)
        
    def flagship_logic(self):
        # A flagship has gone off screen.
        # If the flagship had an escort, it will return to the top of the screen to fight again.
        # If the flagship had no escort, it will flee the level. 
        # A maximum of 2 fleeing flagships can be carried over to the next level.  
        if self.invader_type != 'Flagship':
            return False
        if self.parent.escorts:            
            self.start_return()
            return False
        else:
           self.parent.fled_flagships += 1
           return True # remove
         
                 
    #@ui.in_background   
    def update(self, dt, convoy_move_direction):
        # Update convoy position based on horizontal movement
        self.convoy_position = (self.convoy_position[0] + convoy_move_direction * CONVOY_SPEED * dt, self.convoy_position[1])
        if self.state == STATE_CONVOY:
            # Move horizontally in convoy
            self.position = (self.position.x + convoy_move_direction * CONVOY_SPEED * dt, self.position.y)
        
        elif self.state == STATE_CHARGER_ARC:
            # all invaders start with an arc of 1 second
            # this will result in invader upside down, positioned one
            # row bellow and one column left or right
            if self.started_charge:
                 self.profile = self.leave_convoy(self.clockwise)
                 self.dt_ = 0
                 self.started_charge = False             
            self.position = self.bezier_curve(*self.profile, self.dt_)  
            self.locations.append(self.position)    
            # rotate 180 degrees
            rot = 1 if self.clockwise else -1
            self.rotation = -rot*self.dt_ * math.pi
            self.dt_ += dt
            # finish after 1second
            if self.dt_ >= 1.0:
              self.state = STATE_READY_TO_ATTACK
              # self.started_charge= True         
              
        elif self.state == STATE_READY_TO_ATTACK:
            self.charger_setup()
            self.state = STATE_CHARGER
            #self.started_charge= True 
            self.t_charge = 0      
            if SOUND:       
                self.sound = sound.play_effect('game:Beep', looping=True)          
                
        elif self.state == STATE_CHARGER:
            # Move towards the charge target (player position when charge started)            
            if self.charge_target:
                self.charger_logic(dt)
                self.locations.append(self.position)
                # Check if invader is off-screen or passed the player
                if self.gone_offscreen():       
                    if SOUND:
                        sound.stop_effect(self.sound)
                    self.sortie_count +=1             
                    # If off-screen after charging, remove it (or make it return)
                    if self.flagship_logic(): 
                       return True
                    if self.aggressive:
                           #Called when aliens are aggressive and refuse to return to the swarm.
                           # During this time it won't shoot, but it will gravitate towards the player's horizontal position (as the player sees it). 
                         pass
                         #self.position = Point(self.return_target.x, SCREEN_HEIGHT - 50)
                         #self.start_charge(self.charge_target)
                    #self.plot_path()
                    self.start_return()
                    return True # Indicate removal
                    
        elif self.state == STATE_AGGESSIVE:
            # Called when aliens are aggressive and refuse to return to the swarm.
            # This routine makes the alien fly from the top of the screen for [TempCounter1] pixels vertically.
            # During this time it won't shoot, but it will gravitate towards the player's horizontal position (as the player sees it).
 
            # The trigger for this stage of life is when:
            #     HAVE_AGGRESSIVE_ALIENS is set OR 
            #     HAVE_NO_BLUE_OR_PURPLE_ALIENS flag is set 
            # The inflight alien is now going to fly at full speed and zigzag to make it harder to shoot. 
            # When the alien gets to the vertical (as the player sees it) centre of the screen, the alien will loop
            # the loop if there's enough space to do so. 
            #  After the loop is complete, the alien will start shooting.
            pass
        elif self.state == STATE_RETURNING:
            # Move back towards convoy position
            # appear at top and move down  to original position
            if self.return_target:
                # Simple linear return for now
                self.position = (self.position.x, self.position.y - RETURN_SPEED * dt)
                self.rotation = math.pi  * (1 +  self.parent.t-self.t0)
                self.locations.append(self.position)
                # Check if invader is close to convoy position
                if self.distance(self.position, self.convoy_position) < INVADER_SIZE*2: # Threshold
                    self.position = self.convoy_position # Snap to position
                    self.rotation = 0
                    self.state = STATE_CONVOY # Return to convoy state                    
                                        
        self.alien_timer -= dt
        if self.alien_timer <= 0:
              self.alien_timer = INVADER_MOVE_INTERVAL 
              self.alien_type = not self.alien_type
              self.texture = self.types[self.invader_type][self.alien_type]
              self.size=(INVADER_SIZE, INVADER_SIZE)
              # self.scale = .5
        return False # Indicate not removed
        
    # ui.in_background 
    def plot_path(self):
     from matplotlib import pyplot as plt
     self.paused=True
     xy = np.array(self.locations)
     fig1, ax = plt.subplots()
     x = xy[:, 0]
     y = xy[:, 1]
     ax.set_box_aspect(1)
     plt.plot(x,y)
     plt.show()
     self.parent.view.close()
   
    def start_charge(self, target_position):
        # Start the charging attack
        self.state = STATE_CHARGER_ARC
        self.started_charge = True
        self.locations = []
        self.charge_target = target_position
        # Remove from the main invaders list in the game scene to avoid convoy logic
        if self in self.parent.convoy:
            self.parent.convoy.remove(self)

    def start_return(self):
        # Start returning to convoy
        self.state = STATE_RETURNING
        self.t0 = self.parent.t
        self.return_target = Point(*self.convoy_position)
        # position at top of screen in line with convoy position
        self.position = Point(self.return_target.x, SCREEN_HEIGHT - 50)
        # Add back to the main convoy list in the game scene
        if self not in self.parent.convoy:
             self.parent.convoy.append(self)


class PlayerBullet(scene.SpriteNode):
    def __init__(self, position, **kwargs):
        # Use a simple shape or color for the player bullet
        super().__init__('spc:Fire19', position=position, color='#ffff00', size=(BULLET_SIZE, BULLET_SIZE), **kwargs)
        self.speed = BULLET_SPEED

    def update(self, dt):
        # Move the bullet upwards
        self.position = (self.position.x, self.position.y + self.speed * dt)

class InvaderBullet(scene.SpriteNode):
    def __init__(self, position, **kwargs):
        # Use a simple shape or color for the invader bullet
        super().__init__('spc:BoltBronze', position=position, size=(INVADER_BULLET_SIZE, INVADER_BULLET_SIZE), **kwargs)
        self.speed = INVADER_BULLET_SPEED

    def update(self, dt):
        # Move the bullet downwards
        self.position = (self.position.x, self.position.y - self.speed * dt)


# --- Main Game Scene ---

class Game(scene.Scene):
    def setup(self):
        self.font = ImageFont.truetype('PressStart2P-Regular.ttf',20)
        for child in self.children:
          child.remove_from_parent()
        # Set up the game scene
        self.background_color = '#000000' # Black background
        # Add a starry background (simple dots)
        self.stars = []
        for _ in range(100):
            star_size = random.uniform(1, 3)
            star_position = (random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT))
            star = scene.SpriteNode('spc:Star2', position=star_position, color='#ffffff', size=(star_size, star_size))
            self.add_child(star)
            self.stars.append(star)
            
        self.sprites = defaultdict()
        self.get_sprites('galaxians_all.png')
        # Create player
        self.player = Player(parent=self)
        self.add_child(self.player)

        # Create invaders in convoy
        self.convoy = [] # Invaders currently in convoy
        self.charging_invaders = [] # Invaders currently charging/returning
        self.invader_move_direction = CONVOY_MOVE_DIRECTION
        self.invader_convoy_move_timer = 0 # Timer to control invader horizontal movement
        self.invader_convoy_move_interval = CONVOY_MOVE_INTERVAL

        self.invader_charge_timer = 0 # Timer to control when invaders charge
        self.invader_charge_interval = 3.0 # Time before an invader might charge
        self.flagship_hit = 0
                   
        
        self.flagship = None
        self.fled_flagships = 0
        
        self.reset_wave()
        self.convoy_base = min(self.convoy, key=lambda inv: inv.position.y).position.y
        # List to hold active bullets
        self.player_bullets = []
        self.invader_bullets = []

        # Player movement state
        self.moving_left = False
        self.moving_right = False
        self.moved = False

        # Score
        self.score = 0
        self.score_label = scene.LabelNode(str(self.score), font=('Copperplate', 30),position=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 50), color='#ffffff')
        #self.score_label.font = self.font
        
         
        self.add_child(self.score_label)

        # Game state
        self.game_over = False
        self.game_over_label = None
        icon_size = PLAYER_SIZE / 2
        # Waves
        self.wave = 1
        self.wave_flags = [scene.SpriteNode('emj:Triangular_Flag', 
                                            size=(icon_size, icon_size),
                                            position=(800, 50)
                                            )]
        # Load sounds (replace with actual sound files if you have them)
        # scene.play_effect('arcade:Explosion_1') # Example sound effect
        # lives
        self.lives = LIVES
        self.life_icon = [scene.SpriteNode(self.sprites['player'],
                                           size=(icon_size, icon_size),
                                           position=(50+icon_size*life, 50),
                                           parent=self)
                          for life in range(self.lives)]
         
        # control joystick, press to fire
        self.joystick= joystick.Joystick(position = Point(SCREEN_WIDTH+125,  200), 
                                            color='white', 
                                            alpha=0.3,
                                            show_xy=True,
                                            msg='Tap to Fire')
        self.add_child(self.joystick)        
        
    def reset_wave(self): 
        self.paused = True
        for child in self.children:
          if isinstance(child,  Invader):
              child.remove_from_parent()  
        self.flagship_hit = 0     
        invader_locs = {'Blue': [(5-r, c) for c in range(COLUMNS) for r in range(3)], 
                        'Purple': [(2, c+1) for c in range(COLUMNS-2)],
                        'Red': [(1, c+2) for c in range(COLUMNS-4)],
                        'Flagship': [(0, 3), (0, COLUMNS-4)]
                        }
        if self.fled_flagships:
         for i in range(self.fled_flagships):
             invader_locs['Flagship'].append((0, 4+i))
             
        for type, locs in invader_locs.items():
            for loc in locs:
                row, col = loc            
                # Calculate convoy position
                convoy_x = (col - COLUMNS / 2 + 0.5) * SPACING_X + SCREEN_WIDTH / 2
                convoy_y = START_Y - row * SPACING_Y
                convoy_position = (convoy_x, convoy_y)

                invader = Invader(position=convoy_position, convoy_position=convoy_position, invader_type=type, parent=self)
                invader.flank = 'left' if col < COLUMNS / 2 else 'right'
                invader.loc = loc
                invader.clockwise = col >= COLUMNS / 2 
                self.add_child(invader)
                self.convoy.append(invader)
        self.paused = False     
        # .caf is a renamed mp3 file
        sound.play_effect('Galaxian1.caf')
    
    def get_sprites(self, filename):
       
       sprite_names =['blue1', 'purple1', 'blue2', 'purple2', 'red1', 'flagship', 'player', 'red2']
       sorted_boxes, sprite_names =  spritesheet.separate_irregular_sprites(filename,
                               background_color=(0, 0, 0),
                               use_alpha=False, sprite_names=sprite_names, display=False)
       all_sprites = Texture(filename)
       W, H = all_sprites.size
       
       for k, name in zip(sorted_boxes, sprite_names):
           x1, y1, x2, y2 =  k         
           img = all_sprites.subtexture((x1/ W, (H-y2) / H, (x2-x1)/ W, (y2-y1) / H))          
           self.sprites[name] = img
                  
    def list_invader_type(self, invader_type):
        # return subset of convoy invaders which match invader_type
        return [invader for invader in self.convoy if invader.invader_type == invader_type]   
        
    def select_ship(self, charger, flank) :
        """get rearmost ships from selected flank, outside listed first"""
        invaders = sorted(self.list_invader_type(charger), key=attrgetter('position.y'), reverse=True)
        invaders = [invader for invader in invaders if invader.flank == flank]
        invaders = sorted(invaders, key=attrgetter('position.x'), reverse=False if flank=='left' else True)       
        return invaders        
            
    def select_charger(self):
        escorts = []
        # select either blue or purple or flagship
        # red gets selected if no flagship         
        charger = random.choices(['Blue', 'Purple', 'Flagship'], weights=(10, 10, 3),  k=1)[0]                
        flank = random.choice(['right', 'left'])
        #charger, flank = 'Blue', 'right'
     
        match charger:
            case 'Blue' | 'Purple' | 'Red':
                # Find the outside and rearmost invaders in convoy of selected type       
                invaders = self.select_ship(charger, flank)                  
                if invaders:
                   invader = invaders[0]
                   invader.escort_no = 0 # only used  for Red
                   invader.aggressive = True
                   self.escorts =[]
                else:
                  return None, []
             
            case 'Flagship':                
                invaders = self.select_ship(charger, flank)  
                if invaders:
                   invader = invaders[0]
                   self.flagship = invader
                   # escorts
                   escorts = self.select_ship('Red', flank) 
                   if escorts:
                       # get max 2 escorts
                       self.escorts = escorts[:2]                       
                       for i, escort in enumerate(self.escorts):
                           escort.escort_no = i + 1                                          
                else:
                    # no flagship , try to send red instead
                    invaders = self.select_ship('Red', flank) 
                    if invaders:
                        return invaders[0], []
                    else:
                        return None, []                               
        return invader, self.escorts
    
    def handle_aggression(self):
        # If you have 3 aliens or less
        # in the swarm (inflight aliens don't count), the aliens are enraged and will be far more aggressive.
        # Any aliens that take flight to attack you (inflight aliens) will never return to the swarm and keep attacking
        no_aliens = len(self.convoy)
        self.no_blue_or_purple = not any([invader 
                                          for invader in self.convoy
                                          if invader.invader_type in ['Blue', 'Purple']])
        if no_aliens <= 3 or self.no_blue_or_purple:
            for invader in self.convoy:
                invader.aggressive = True
        
    def player_bullet_collision(self):
        # Player Bullet vs Invader (Formation and Diving)
          hit_invaders = []
          hit_player_bullets = []
          for bullet in self.player_bullets:
              # Check against invaders in convoy
              for invader in self.convoy + self.charging_invaders:
                  if bullet.frame.intersects(invader.frame):
                      hit_invaders.append(invader)
                      if SOUND:
                          try:
                              sound.stop_effect(invader.sound)
                          except (AttributeError, TypeError):
                              pass
                      hit_player_bullets.append(bullet)
                      self.handle_flagship_score()
                      self.score += invader.score_value  * (1+ int(invader.state == STATE_CHARGER)) # Increase score based on invader type
                      self.score_label.text = str(self.score)
                      if invader in self.charging_invaders and invader.invader_type == 'flagship':
                        self.flagship_hit = self.t # time when flagship hit
                        print('flagship lost', self.flagship_hit, self.t)
                      # sound.play_effect('arcade:Explosion_1') # Play hit sound
                      break # Bullet can only hit one invader                      
          return hit_invaders, hit_player_bullets
          
    def convoy_movement(self):
        # --- Invader Convoy Movement ---
        #* 1. Stops the swarm from moving if the player bullet gets too close to an alien in the swarm
        self.invader_convoy_move_timer += self.dt
        if self.invader_convoy_move_timer >= self.invader_convoy_move_interval:
            self.invader_convoy_move_timer = 0

            # Check if invaders in convoy hit screen edge
            hit_edge = False
            if self.convoy: # Only check if there are invaders in convoy
                # Find the leftmost and rightmost invaders in convoy
                leftmost_invader = min(self.convoy, key=lambda inv: inv.position.x)
                rightmost_invader = max(self.convoy, key=lambda inv: inv.position.x)

                if leftmost_invader.position.x <= INVADER_SIZE/2 or rightmost_invader.position.x >= SCREEN_WIDTH - INVADER_SIZE/2:
                    hit_edge = True

            if hit_edge:
                self.invader_move_direction *= -1 # Reverse direction
                
    def remove_invaders(self):
        # Update invaders (convoy and charging/returning)
        invaders_to_remove = []              
        for invader in self.convoy + self.charging_invaders:
            removed = invader.update(self.dt, self.invader_move_direction)
            if removed:
                invaders_to_remove.append(invader)

        # Remove invaders that went off-screen after charging
        for invader in invaders_to_remove:
            if invader in self.charging_invaders:
                self.charging_invaders.remove(invader)        
                
    def invader_charge(self):
        # --- Invader Diving Logic ---
        self.invader_charge_timer += self.dt
        if self.invader_charge_timer >= self.invader_charge_interval and self.convoy:
            # dont charge if in panic
            if self.flagship_hit > 0 and self.t < self.flagship_hit + FLAGSHIP_LOST_PARALYSIS:
               pass
            else:
               self.invader_charge_timer = -10
               charging_invader, escorts = self.select_charger()
               if charging_invader:
                   charging_invader.start_charge(self.player.position) # Dive towards current player position
                   self.charging_invaders.append(charging_invader) # Add to charging list
               if escorts:
                  for i, escort in enumerate(escorts):
                      escort.start_charge(self.player.position) # Dive towards current player position
                      self.charging_invaders.append(escort) # Add to charging list
                      
    def bullet_updates(self):
        # --- Bullet Updates ---
        player_bullets_to_remove = []
        for bullet in self.player_bullets:
            bullet.update(self.dt)
            # Remove bullets that go off-screen
            if bullet.position.y > SCREEN_HEIGHT:
                player_bullets_to_remove.append(bullet)

        invader_bullets_to_remove = []
        for bullet in self.invader_bullets:
            bullet.update(self.dt)
            # Remove bullets that go off-screen
            if bullet.position.y < 0:
                invader_bullets_to_remove.append(bullet)
                
        for bullet in set(player_bullets_to_remove + hit_player_bullets):
            if bullet in self.player_bullets:
                self.player_bullets.remove(bullet)
                bullet.remove_from_parent()
                self.player.can_shoot = True

        for bullet in set(invader_bullets_to_remove + hit_invader_bullets):
            if bullet in self.invader_bullets:
                self.invader_bullets.remove(bullet)
                bullet.remove_from_parent()
        return player_bullets_to_remove, invader_bullets_to_remove 
    
    
                                
    def update(self):
        """ from the ROM code, this implements:
         
         HANDLE_MAIN_GAME_LOGIC:
         0661: CD 37 08      call $0837               ; call HANDLE_PLAYER_MOVE
         0664: CD 98 08      call $0898               ; call HANDLE_PLAYER_BULLET
         0667: CD 74 0A      call $0A74               ; call HANDLE_ENEMY_BULLETS
         066A: CD C3 0C      call $0CC3               ; call HANDLE_INFLIGHT_ALIENS
         066D: CD BE 0B      call $0BBE               ; call HANDLE_INFLIGHT_ALIEN_SPRITE_UPDATE
         0670: CD 32 0A      call $0A32               ; call HANDLE_PLAYER_SHOOT
         0673: CD 0B 0B      call $0B0B               ; call HANDLE_SWARM_ALIEN_TO_PLAYER_BULLET_COLLISION_DETECTION
         0676: CD 77 0B      call $0B77               ; call HANDLE_PLAYER_TO_ENEMY_BULLET_COLLISION_DETECTION
         0679: CD 27 12      call $1227               ; call HANDLE_INFLIGHT_ALIEN_TO_PLAYER_BULLET_COLLISION_DETECTION
         067C: CD 9E 12      call $129E               ; call HANDLE_PLAYER_TO_INFLIGHT_ALIEN_COLLISION_DETECTION
         067F: CD E5 08      call $08E5               ; call HANDLE_PLAYER_BULLET_EXPIRED
         0682: CD 0C 14      call $140C               ; call HANDLE_FLAGSHIP_ATTACK
         0685: CD 44 13      call $1344               ; call HANDLE_SINGLE_ALIEN_ATTACK
         0688: CD E1 13      call $13E1               ; call SET_ALIEN_ATTACK_FLANK
         068B: CD F3 14      call $14F3               ; call HANDLE_LEVEL_DIFFICULTY
         068E: CD ED 12      call $12ED               ; call HANDLE_PLAYER_HIT
         0691: CD 27 13      call $1327               ; call HANDLE_PLAYER_DYING
         0697: CD 15 15      call $1515               ; call CHECK_IF_ALIEN_CAN_ATTACK
         069A: CD 55 15      call $1555               ; call UPDATE_ATTACK_COUNTERS
         069D: CD C3 15      call $15C3               ; call CHECK_IF_FLAGSHIP_CAN_ATTACK
         06A0: CD F4 15      call $15F4               ; call HANDLE_CALC_INFLIGHT_ALIEN_SHOOTING_DISTANCE
         06A3: CD 21 16      call $1621               ; call CHECK_IF_LEVEL_IS_COMPLETE
         06A6: CD 37 16      call $1637               ; call HANDLE_LEVEL_COMPLETE
         06A9: CD B8 16      call $16B8               ; call HANDLE_ALIEN_AGGRESSIVENESS
         06AC: CD 88 16      call $1688               ; call HANDLE_SHOCKED_SWARM

        # need to implement difficulty
        # reduce self.invader_charge_interval by 0.2 for each wave
        # If you have 3 aliens or less
        # in the swarm (inflight aliens don't count), the aliens are enraged and will be far more aggressive.
        # Any aliens that take flight to attack you (inflight aliens) will never return to the swarm and keep attacking
        """
        if self.game_over:
            return # Stop updating if game is over
        self.invader_charge_interval = INTERVAL_CHARGE_INTERVAL - 0.2 * self.wave
        
        # --- Player Update ---
        self.player.update(self.dt)
        self.joystick.update()
        move_direction = 0
        if self.moving_left:
            move_direction -= 1
        if self.moving_right:
            move_direction += 1
        self.player.move(move_direction, self.dt)
                                                  
        hit_invaders, hit_player_bullets = self.player_bullet_collision()           
        
        self.convoy_movement()

        self.remove_invaders()

        self.invader_charge()
        
                
        # --- Invader Shooting  ---
        # calculate how far away from the player inflight aliens can be before they can start shooting at you.
        #The minimum shooting distance increases as more aliens are killed, making the aliens shoot more often.
        self.no_aliens = len(self.convoy + self.charging_invaders)
        # shooting is handled in the Invader class
        
        self.handle_aggression()       

        # --- Bullet Updates ---
        player_bullets_to_remove = []
        for bullet in self.player_bullets:
            bullet.update(self.dt)
            # Remove bullets that go off-screen
            if bullet.position.y > SCREEN_HEIGHT:
                player_bullets_to_remove.append(bullet)

        invader_bullets_to_remove = []
        for bullet in self.invader_bullets:
            bullet.update(self.dt)
            # Remove bullets that go off-screen
            if bullet.position.y < 0:
                invader_bullets_to_remove.append(bullet)
                
        for bullet in set(player_bullets_to_remove + hit_player_bullets):
            if bullet in self.player_bullets:
                self.player_bullets.remove(bullet)
                bullet.remove_from_parent()
                self.player.can_shoot = True

        
        #return player_bullets_to_remove, invader_bullets_to_remove 
    
        #player_bullets_to_remove, invader_bullets_to_remove = self.bullet_updates()
        
        # --- Collision Detection ---                  
        # invader crashes into player        
        for invader in self.charging_invaders:
            inv_rect = invader.frame.inset(INVADER_SIZE/4, INVADER_SIZE/4)
            plyr_rect = self.player.frame.inset(PLAYER_SIZE/8, PLAYER_SIZE/8)
            if inv_rect.intersects(plyr_rect):
                hit_invaders.append(invader)  
                self.end_wave("hit")
                break

        # Invader Bullet vs Player
        hit_invader_bullets = []
        if not self.game_over: # Only check if player is alive
            for bullet in self.invader_bullets:
                if bullet.frame.intersects(self.player.frame):
                    hit_invader_bullets.append(bullet)
                    self.end_wave("hit")
                    # sound.play_effect('arcade:Explosion_2') # Play player hit sound
                    break # Player hit by one bullet is enough

        for bullet in set(invader_bullets_to_remove + hit_invader_bullets):
            if bullet in self.invader_bullets:
                self.invader_bullets.remove(bullet)
                bullet.remove_from_parent()
        # Remove hit invaders and bullets
        for invader in set(hit_invaders):
            if invader in self.convoy:
                self.convoy.remove(invader)
                # fast explosion
                self.explosion(invader.position, INVADER_SIZE*1.5, speed=0.03)
            elif invader in self.charging_invaders:
                 self.charging_invaders.remove(invader)
                 if invader.invader_type == 'Flagship':
                    self.flagship=None                  
                 self.explosion(invader.position, INVADER_SIZE*2, speed=.1)
            invader.remove_from_parent()

        


        # --- Check Game Over/Win Conditions ---
        if not self.convoy and not self.charging_invaders: # Win if all invaders are gone
            self.end_wave("complete")
        #print(f'{1000*(time()-t):.2f}ms')
        
    def handle_flagship_score(self):
        # if flagship is hit
        # not charging 60
        # solo charge 150
        # 1 escort 200
        
        # charging hit third 800
        pass
        
    def shoot(self, sender):
        # Shoot (can refine this to a specific area if needed)
        bullet = self.player.shoot()
        if bullet:
            self.add_child(bullet)
            self.player_bullets.append(bullet)
            # scene.play_effect('arcade:Laser_1') # Play shoot sound
            
    def touch_began(self, touch):
        # Handle touch input
        if self.joystick.bbox.contains_point(touch.location):       
             self.joystick.touch_began(touch)
             #self.shoot(None)
        
        self.touched = touch.location
        if self.game_over:
            # Restart game on touch if game over
            self.setup()
            return

    def touch_moved(self, touch):
        # Update movement based on touch location
        self.moved = True
        self.joystick.touch_moved(touch)
        if self.game_over:
            return
        # shoot button is a joystick        
        if self.joystick.x < -JOYSTICK_DEAD_ZONE:
           self.moving_left = True
           self.moving_right = False  
        elif self.joystick.x > JOYSTICK_DEAD_ZONE:
           self.moving_left = False
           self.moving_right = True   

    def touch_ended(self, touch):
        # Stop player movement when touch ends
        self.joystick.touch_ended(touch)
        if self.game_over:
            return
        if not self.moved:
           self.shoot(None)
        # Check if the touch ended in the area that was causing movement
        self.moving_left = False
        self.moving_right = False
        self.moved = False
            
    @ui.in_background     
    def explosion(self, pos, size, speed=0.1, color='white'):
       if SOUND:
            sound.play_effect('arcade:Explosion_4', volume=100) # Play hit sound
       expl = scene.SpriteNode('shp:Explosion01', color=color, anchor_point=(0.5, 0.5), position=pos, parent=self)
       expl.size=(size, size)
       for i in range(1,8):
           sleep(speed)
           expl.texture = Texture(f'shp:Explosion{i:02d}')
           expl.size=(size, size)
       expl.remove_from_parent()
     
    @ui.in_background
    def end_wave(self, reason=None):
        if reason == 'hit':
           self.player.lives -= 1
           self.explosion(self.player.position, PLAYER_SIZE*2, color='red')
           self.life_icon.pop().remove_from_parent()
           if self.player.lives == 0:
               self.game_over = True
               self.game_over_label = scene.LabelNode('Game Over', 
                                                      font=('Optima', 100),
                                                      position=(SCREEN_WIDTH/2,
                                                                SCREEN_HEIGHT/2),
                                                      color='#ffffff',
                                                      parent=self)            
        elif reason == 'complete':
            self.wave += 1
            self.wave_flags.append(scene.SpriteNode('emj:Triangular_Flag',
                                                    position=(SCREEN_WIDTH-100 + 20*self.wave, 50),
                                                    parent=self))
            self.reset_wave()                        
        
        # You could add a restart button here

# --- Run the game ---
if __name__ == '__main__':
    # Load the arcade font for a retro feel
    # url = os.path.dirname(os.path.realpath(__file__)) + '/PressStart2P-Regular.ttf'
    # load_custom_font(url) # Make sure you have this font file in Pythonista
    scene.run(Game(), orientation=scene.PORTRAIT, show_fps=True)
    
    

    

