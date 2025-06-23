# This is a version of the old BattleTank wire-frame graphics game
# it was produced by Gemini AI with some fixes by me
# Chris Thomas June 2025
# scene_battlezone_game.py (main game file for Pythonista)

import scene
import ui
import math
import sound
import random
import colorsys
from collections import deque

# --- Vector Class for 3D Math ---
class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar):
        return self * scalar

    def __truediv__(self, scalar):
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self):
        length = self.length()
        if length == 0:
            return Vector3(0,0,0)
        return self / length

    def rotate_x(self, angle_rad):
        # Rotates around the X-axis (pitch)
        # Assuming vector (x, y, z)
        # New y' = y*cos(a) - z*sin(a)
        # New z' = y*sin(a) + z*cos(a)
        # x' = x
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        new_y = self.y * cos_a - self.z * sin_a
        new_z = self.y * sin_a + self.z * cos_a
        return Vector3(self.x, new_y, new_z)

    def rotate_y(self, angle_rad):
        # Rotates around the Y-axis (yaw)
        # Assuming vector (x, y, z)
        # New x' = x*cos(a) + z*sin(a)
        # New z' = -x*sin(a) + z*cos(a)
        # y' = y
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        new_x = self.x * cos_a + self.z * sin_a
        new_z = -self.x * sin_a + self.z * cos_a
        return Vector3(new_x, self.y, new_z)

    def rotate_z(self, angle_rad):
        # Rotates around the Z-axis (roll)
        # Assuming vector (x, y, z)
        # New x' = x*cos(a) - y*sin(a)
        # New y' = x*sin(a) + y*cos(a)
        # z' = z
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        new_x = self.x * cos_a - self.y * sin_a
        new_y = self.x * sin_a + self.y * cos_a
        return Vector3(new_x, new_y, self.z)

    def clone(self):
        return Vector3(self.x, self.y, self.z)

    def __repr__(self):
        return f"Vector3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


# Game Constants ---
# Colors (RGBA tuples 0-1)
COLOR_GREEN = (0, 1, 0, 1)
COLOR_RED = (1, 0, 0, 1)
COLOR_YELLOW = (1, 1, 0, 1)
COLOR_WHITE = (1, 1, 1, 1)
COLOR_CYAN = (0, 1, 1, 1)

# Game parameters
WORLD_SIZE = 1500 # Max X/Z coordinate
PLAYER_SPEED = 120 # units per second
PLAYER_ROT_SPEED = math.radians(90) # radians per second
BULLET_SPEED = 100
BULLET_LIFETIME = 3.0 # seconds
ENEMY_SPEED = 50
ENEMY_FIRE_RATE = 2 # seconds between shots
ENEMY_SPAWN_INTERVAL = 5.0 # seconds
MAX_ENEMIES = 5
HIT_EFFECT_DURATION = 0.15 # seconds
SCORE_PER_KILL = 100

# Camera/Projection settings
FOV = math.radians(60) # Field of View
FOCAL_LENGTH = 1.0 / math.tan(FOV / 2) # Calculated based on FOV
Z_NEAR = 10 # Minimum Z distance to draw (clip anything closer)
Z_FAR = 1000 # Maximum Z distance to draw (clip anything further)

# Utility Functions ---
def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def dist_2d(v1, v2):
    return math.sqrt((v1.x - v2.x)**2 + (v1.z - v2.z)**2)

# Part of scene_battlezone_game.py
# --- Base Wireframe Object ---
class WireframeObject:
    def __init__(self,  scale=1.0, color=COLOR_GREEN, **kwargs):
        self.position = kwargs.pop('position',  Vector3(0,0,0))
        # rotation_angles should be a Vector3 (pitch_x, yaw_y, roll_z) in radians
        self.rotation_angles = kwargs.pop('rotation_angles',  Vector3(0,0,0))
        
        self.scale = scale
        self.color = color
        self.original_vertices = [] # Stored in object's local space
        self.edges = []
        self.visible = True

        # These are used when a component is part of a larger object (like Tank)
        # They will be calculated in the parent's get_all_wireframe_objects
        self.position_in_world = self.position.clone()
        self.rotation_angles_in_world = self.rotation_angles.clone()
        

    def get_world_vertices(self):
        # Apply local scale, rotation, and then world position
        world_vertices = []
        for v_local in self.original_vertices:
            scaled_v = v_local * self.scale

            # Apply rotations in a specific order (e.g., Z-Y-X Euler angles: Roll, Yaw, Pitch)
            # This order is often used, but others exist (e.g., YXZ, XYZ).
            # Consistency is key.
            rotated_v = scaled_v.rotate_z(self.rotation_angles_in_world.z) # Roll
            rotated_v = rotated_v.rotate_y(self.rotation_angles_in_world.y) # Yaw
            rotated_v = rotated_v.rotate_x(self.rotation_angles_in_world.x) # Pitch

            world_vertices.append(self.position_in_world + rotated_v)
        return world_vertices

   

# Specific Wireframe Object Types ---
class WireCube(WireframeObject):
    def __init__(self, size_x=1.0, size_y=1.0, size_z=1.0, **kwargs):            
        hw = size_x / 2.0
        hh = size_y / 2.0
        hl = size_z / 2.0
        self.width = size_x
        self.height = size_y
        self.length = size_z
        
        #kwargs.pop('is_player', '')
        #kwargs.pop('size_x', 1.0)
        #kwargs.pop('size_y', 1.0)
        #kwargs.pop('size_z', 1.0)
        super().__init__(**kwargs)
        self.original_vertices = [
            # Bottom (y = -hh)
            Vector3(-hw, -hh, hl),   # 0: back-left-bottom
            Vector3(hw,  -hh, hl),   # 1: back-right-bottom
            Vector3(hw,  -hh, -hl), # 2: front-right-bottom (pulled back slightly)
            Vector3(-hw, -hh, -hl), # 3: front-left-bottom (pulled back slightly)

            # Top (y = hh)
            Vector3(-hw, hh, hl), # 4: back-left-top
            Vector3(hw,  hh, hl), # 5: back-right-top
            Vector3(hw,  hh, -hl),   # 6: front-right-top (extended forward for slope)
            Vector3(-hw, hh, -hl)    # 7: front-left-top (extended forward for slope)
        ]        
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), # Bottom square
            (4, 5), (5, 6), (6, 7), (7, 4), # Top square
            (0, 4), (1, 5), (2, 6), (3, 7)  # Connecting edges
        ]


        
class WirePyramid(WireframeObject):
    def __init__(self, base_size=1.0, height=1.0, **kwargs):
        super().__init__(**kwargs)
        half_base = base_size / 2.0
        self.original_vertices = [
            Vector3(-half_base, 0, -half_base),  # Base corners
            Vector3( half_base, 0, -half_base),
            Vector3( half_base, 0,  half_base),
            Vector3(-half_base, 0,  half_base),
            Vector3(0, height, 0) # Apex
        ]
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), # Base edges
            (0, 4), (1, 4), (2, 4), (3, 4)  # Edges to apex
        ]

class WireLine(WireframeObject):
    def __init__(self, start_pos, end_pos, color=COLOR_WHITE):
        super().__init__(position=Vector3(0,0,0), color=color) # Line is defined by absolute positions
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.original_vertices = [start_pos, end_pos] # Not used in traditional sense for this
        self.edges = [(0,1)] # Just one edge

    def get_world_vertices(self):
        # For a simple line, the "world vertices" are just its absolute points
        return [self.start_pos, self.end_pos]

class WireCylinder(WireframeObject):
    def __init__(self, radius=1.0, height=1.0, num_segments=8, **kwargs):
        
        super().__init__(**kwargs)
        self.radius = radius
        self.height = height
        self.num_segments = num_segments

        # Vertices for top and bottom circles
        # Now, cylinder's axis is along Y by default
        half_height = height / 2.0
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            # Top and bottom faces are parallel to XZ plane
            self.original_vertices.append(Vector3(x, half_height, z))  # Top circle
            self.original_vertices.append(Vector3(x, -half_height, z)) # Bottom circle

        # Edges (same as before)
        # Connect segments of top and bottom circles
        for i in range(num_segments):
            # Top circle edges
            self.edges.append((i * 2, (i * 2 + 2) % (num_segments * 2)))
            # Bottom circle edges
            self.edges.append((i * 2 + 1, (i * 2 + 3) % (num_segments * 2)))
            # Vertical edges
            self.edges.append((i * 2, i * 2 + 1))
            


class WireTankTurret(WireframeObject):
    def __init__(self, base_width=1.0, base_length=1.0, height=1.0, **kwargs):
        super().__init__(**kwargs)
        hw = base_width / 2.0
        hl = base_length / 2.0
        h = height

        # A more complex turret shape: a trapezoidal prism or similar
        self.original_vertices = [
            # Base rectangle (larger, on top of hull)
            Vector3(-hw * 1.0, -h/2, hl * 0.8), # 0: back-left-bottom
            Vector3( hw * 1.0, -h/2, hl * 0.8), # 1: back-right-bottom
            Vector3( hw * 1.0, -h/2, -hl * 0.4), # 2: front-right-bottom
            Vector3(-hw * 1.0, -h/2, -hl * 0.4), # 3: front-left-bottom

            # Top rectangle (smaller, slightly forward, creating a slope)
            Vector3(-hw * 0.8, h/2, hl * 0.7), # 4: back-left-top
            Vector3( hw * 0.8, h/2, hl * 0.7), # 5: back-right-top
            Vector3( hw * 0.6, h/2, -hl * 0.6), # 6: front-right-top
            Vector3(-hw * 0.6, h/2, -hl * 0.6)  # 7: front-left-top
        ]

        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), # Base
            (4, 5), (5, 6), (6, 7), (7, 4), # Top
            (0, 4), (1, 5), (2, 6), (3, 7)  # Connecting vertical/sloped edges
        ]


class WireTankHull(WireframeObject):
    def __init__(self, width=1.0, height=1.0, length=1.0, **kwargs):
        super().__init__(**kwargs)
        hw = width / 2.0
        hh = height / 2.0
        hl = length / 2.0
        self.width = width
        self.height = height
        self.length = length

        # Basic hull (stretched cube with sloped front)
        self.original_vertices = [
            # Bottom (y = -hh)
            Vector3(-hw, -hh, hl),   # 0: back-left-bottom
            Vector3(hw,  -hh, hl),   # 1: back-right-bottom
            Vector3(hw,  -hh, -hl*0.8), # 2: front-right-bottom (pulled back slightly)
            Vector3(-hw, -hh, -hl*0.8), # 3: front-left-bottom (pulled back slightly)

            # Top (y = hh)
            Vector3(-hw*0.9, hh, hl*0.9), # 4: back-left-top
            Vector3(hw*0.9,  hh, hl*0.9), # 5: back-right-top
            Vector3(hw*0.8,  hh, -hl),   # 6: front-right-top (extended forward for slope)
            Vector3(-hw*0.8, hh, -hl)    # 7: front-left-top (extended forward for slope)
        ]

        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), # Bottom outline
            (4, 5), (5, 6), (6, 7), (7, 4), # Top outline
            (0, 4), (1, 5), (2, 6), (3, 7), # Vertical connectors
            (2, 6), (3, 7) # Explicitly define sloped front edges if needed (already implicitly there)
        ]

# Game Specific Objects ---    
    
# Part of scene_battlezone_game.py (Modified Tank class)

class Tank: 
    def __init__(self, position=None, rotation_y=0.0, **kwargs):
        self.position = position if position else Vector3(0,0,0)
        self.rotation_y = rotation_y # Y-axis rotation in radians
        self.scale = 1.0 # Overall scale for the tank (components will use this)
        self.color = COLOR_GREEN # Base color for the tank components
        self.visible = True

        self.speed = PLAYER_SPEED # For player/enemy
        self.rotation_speed = PLAYER_ROT_SPEED
        self.health = 100
        self.max_health = 100
        self.is_player = kwargs.pop('is_player', False)
        self.last_fire_time = 0
        self.fire_rate = ENEMY_FIRE_RATE # For enemy
        self.hit_effect_timer = 0
        self.turret_relative_yaw = 0.0 # Turret relative to tank body
        self.barrel_pitch = 0.0 # relative to turrent
        self.components = [] # List to hold individual wireframe parts
        self._assemble_tank_components()
        
    def take_damage(self, amount):
        self.health -= amount
        self.hit_effect_timer = HIT_EFFECT_DURATION
        sound.play_effect('arcade:Explosion_2', 0.5, 1.0, 0.1) # Short explosion sound
        if self.health <= 0:
            sound.play_effect('arcade:Explosion_7', 1.0, 1.0, 0.5)
            self.visible = False
            return True # Died
        return False # Still alive
 
 
    def update(self, dt, player_pos=None):
        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= dt
            # Flash color to red when hit
            r_comp = 1.0
            g_comp = max(0.0, self.color[1] - (1 - self.hit_effect_timer / HIT_EFFECT_DURATION))
            b_comp = max(0.0, self.color[2] - (1 - self.hit_effect_timer / HIT_EFFECT_DURATION))
            self.color = (r_comp, g_comp, b_comp, 1)
        else:
            if not self.is_player:
                # Reset enemy color
                self.color = COLOR_YELLOW

        if not self.is_player and self.visible and player_pos:
            # Simple enemy AI: move towards player and fire
            direction_to_player = (player_pos - self.position).normalize()
            self.position += direction_to_player * self.speed * dt

            # Rotate towards player (approximate)
            angle_to_player = math.atan2(direction_to_player.x, direction_to_player.z)
            self.rotation_y = angle_to_player # Instant rotation for simplicity
               
    def _assemble_tank_components(self):
        # Hull (main body)
        hull_size_x = 20
        hull_size_y = 10
        hull_size_z = 30
        self.hull = WireTankHull(width=hull_size_x,
                                 height=hull_size_y, 
                                 length=hull_size_z,
                                 position=Vector3(0, 0, 0), # Local to tank origin
                                 color=self.color)
        self.components.append(self.hull)

        # Turret
        turret_base_width = 12
        turret_base_length = 15
        turret_height = 8
        # Turret sits on top of the hull. Hull's top is at +hull_size_y/2
        # Turret's base is at -turret_height/2
        turret_offset_y = hull_size_y / 2 + turret_height / 2 - 1 # Adjusted slightly to sit on top
        self.turret = WireTankTurret(base_width=turret_base_width,
                                     base_length=turret_base_length,
                                     height=turret_height,
                                     position=Vector3(0, turret_offset_y, 0),
                                     color=self.color)
        self.components.append(self.turret)

        # Barrel
        barrel_length = 20
        barrel_radius = 1.5
        # Barrel's local position relative to turret's origin.
        # Its default local orientation is along Y-axis for WireCylinder.
        # We want it to stick out along Z (forward) when the tank is facing Z.
        # So we need to rotate it locally by -pi/2 around X to make its length along Z.
        barrel_offset_z_local = -turret_base_length/2 * 0.6 # Front of turret
        barrel_offset_y_local = turret_height/2 - 1 # Slightly below top of turret
        
        self.barrel = WireCylinder(radius=barrel_radius, height=barrel_length, num_segments=20,
                                   position=Vector3(0, barrel_offset_y_local, barrel_offset_z_local),
                                   rotation_angles=Vector3(-math.pi/2, 0, 0), # Local pitch to make it horizontal along Z
                                   color=COLOR_RED)
        self.components.append(self.barrel)

        # Treads (two of them)
        tread_width = 5
        tread_height = 10
        tread_length = hull_size_z * 0.9 # Slightly shorter than hull
        tread_offset_x = hull_size_x / 2 + tread_width / 2 + 1 # Offset from hull side
        tread_offset_y = -hull_size_y / 2 # Sits on the ground level of hull
        
        self.left_tread = WireCube(size_x=tread_width,
                                   size_y=tread_height,
                                   size_z=tread_length,
                                   position=Vector3(-tread_offset_x, tread_offset_y, 0),
                                   color=COLOR_WHITE) # Grey treads
        self.components.append(self.left_tread)

        self.right_tread = WireCube(size_x=tread_width,
                                    size_y=tread_height,
                                    size_z=tread_length,
                                    position=Vector3(tread_offset_x, tread_offset_y, 0),
                                    color=COLOR_WHITE) # Grey treads
        self.components.append(self.right_tread)

        num_wheels = 4
        wheel_radius = 3
        wheel_height = 4
        wheel_spacing = tread_length / (num_wheels - 1)
        wheel_offset_z = -tread_length / 2
        
        for i in range(num_wheels):
            z = wheel_offset_z + i * wheel_spacing
            wheel_color = (0.3, 0.3, 0.3, 1)

            self.components.append(WireCylinder(radius=wheel_radius, height=wheel_height, num_segments=10,
                                                position=Vector3(-tread_offset_x, tread_offset_y, z),
                                                rotation_angles=Vector3(0, 0, math.pi/2), # Already horizontal with Y-axis. Rotating Y by 90deg makes it point to side. No, it should be X=0 Z=0. Just default.
                                                color=wheel_color)) # No local rotation needed for wheels if Y is height
            self.components.append(WireCylinder(radius=wheel_radius, height=wheel_height, num_segments=10,
                                                position=Vector3(tread_offset_x, tread_offset_y, z),
                                                rotation_angles=Vector3(0, 0, math.pi/2), # No local rotation needed for wheels
                                                color=wheel_color))

        

        

    def get_all_wireframe_objects(self):
        all_parts = []
        
        # Calculate turret's world rotation based on tank's rotation and its own relative yaw
        turret_world_yaw = self.rotation_y + self.turret_relative_yaw
        
        # Calculate barrel's world rotation based on turret's rotation and its own pitch
        # Remember, barrel's `rotation_angles` already has a local -pi/2 pitch to orient it horizontally.
        # We add the `self.barrel_pitch` to its X component (pitch).
        barrel_world_pitch = self.barrel.rotation_angles.x + self.barrel_pitch
        barrel_world_yaw = turret_world_yaw # Barrel inherits turret's yaw

        # Reconstruct barrel's rotation_angles_in_world
        barrel_world_rotation_angles = Vector3(-math.pi/2, 0, 0) # barrel_world_pitch, barrel_world_yaw) # No roll for tank parts


        for component in self.components:
            # Calculate component's world position (offset from tank origin + tank's world position)
            rotated_offset = component.position.rotate_y(self.rotation_y)
            component.position_in_world = self.position + rotated_offset

            # Calculate component's world rotation (tank's overall yaw + component's local rotations)
            component.rotation_angles_in_world = Vector3(
                component.rotation_angles.x, # Component's local pitch (e.g. barrel's initial horizontal alignment)
                self.rotation_y + component.rotation_angles.y, # Tank's yaw + component's local yaw
                component.rotation_angles.z # Component's local roll
            )

            # Special handling for Turret and Barrel, as their rotations are hierarchical
            if component is self.turret:
                component.rotation_angles_in_world.y = turret_world_yaw # Tank's yaw + turret's relative yaw
            elif component is self.barrel:
                component.rotation_angles_in_world = barrel_world_rotation_angles # Use the pre-calculated barrel world rotation

            # Set the component's color and visibility from the parent tank
            component.color = self.color
            if self.hit_effect_timer > 0:
                r_comp = 1.0
                g_comp = max(0.0, self.color[1] - (1 - self.hit_effect_timer / HIT_EFFECT_DURATION))
                b_comp = max(0.0, self.color[2] - (1 - self.hit_effect_timer / HIT_EFFECT_DURATION))
                component.color = (r_comp, g_comp, b_comp, 1)
            else:
                # Reset enemy color if not hit
                if not self.is_player and component is self.hull:
                    component.color = COLOR_YELLOW
                elif self.is_player and component is self.hull:
                    component.color = COLOR_GREEN

            component.visible = self.visible
            all_parts.append(component)
        return all_parts

    def update(self, dt, player_pos=None):
        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= dt
            # Color change is now handled per component in get_all_wireframe_objects
            
        # This part of update is purely for movement/AI/game logic
        if not self.is_player and self.visible and player_pos:
            # Simple enemy AI: move towards player and fire
            direction_to_player = (player_pos - self.position).normalize()
            self.position += direction_to_player * self.speed * dt

            # Rotate towards player (approximate)
            angle_to_player = math.atan2(direction_to_player.x, direction_to_player.z)
            self.rotation_y = angle_to_player # Instant rotation for simplicity
            self.turret.rotation_y = angle_to_player - self.rotation_y # Turret aims relative to tank body. For instant, just match it.
            # In a real game, turret would turn slower.


class Bullet(WireCube):
    def __init__(self, direction, speed, **kwargs):
        super().__init__(size_x=3,size_y=3,size_z=3, color=COLOR_RED, **kwargs)
        self.direction = direction.normalize() # Direction vector
        self.speed = speed
        self.lifetime = BULLET_LIFETIME
        self.fired_by_player = False # True if player fired, False if enemy fired

    def update(self, dt):
        self.position += self.direction * self.speed * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.visible = False # Mark for removal
            
            
class BattleZone(scene.Scene):
    def setup(self):
        self.paused = True
        self.background_color = (0.05, 0.05, 0.05) # Dark background

        self.player = Tank(position=Vector3(0, 0, 0), is_player=True)
        self.player.color = COLOR_GREEN

        self.camera_offset_y = 10 # Camera height above ground
        self.camera_pitch = 0 # Vertical camera angle

        # Game state variables
        self.forward_pressed = False
        self.backward_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False

        self.obstacles = []
        self.bullets = []
        self.enemies = []
        self.last_enemy_spawn_time = 0
        self.take_damage = 0
        self.score = 0
        self.game_over = False
                
        self.setup_world()        
        self.setup_hud_controls()
        self.paused = False
        
        
    def text(self, txt, font= ('HelveticaNeue-Bold', 30), x=0, y=0, color='COLOR_WHITE', alignment=5):
        # wraps scene_drawing.text to provide color and alignment
        scene.tint(color)
        scene.text(txt, font_name=font[0], font_size=font[1], x=x, y=y, alignment=alignment)
        
    def setup_world(self):
        # Ground plane lines
        grid_spacing = 100
        for i in range(-WORLD_SIZE // grid_spacing, WORLD_SIZE // grid_spacing + 1):
            z_val = i * grid_spacing
            self.obstacles.append(WireLine(Vector3(-WORLD_SIZE, 0, z_val), Vector3(WORLD_SIZE, 0, z_val), color=(0.1, 0.2, 0.1, 1)))
            x_val = i * grid_spacing
            self.obstacles.append(WireLine(Vector3(x_val, 0, -WORLD_SIZE), Vector3(x_val, 0, WORLD_SIZE), color=(0.1, 0.2, 0.1, 1)))

        # Random obstacles
        num_obstacles = 30
        for _ in range(num_obstacles):
            x = random.uniform(-WORLD_SIZE + 50, WORLD_SIZE - 50)
            z = random.uniform(-WORLD_SIZE + 50, WORLD_SIZE - 50)
            y = 0 # Always on the ground
            size = random.uniform(30, 80)
            obs_type = random.choice([WireCube, WirePyramid])
            if obs_type == WirePyramid:
                self.obstacles.append(WirePyramid(base_size=size, height=size, position=Vector3(x,y,z), color=COLOR_CYAN))
            elif obs_type == WireCube :
                self.obstacles.append(WireCube(size_x=size, size_y=size,size_z=size, position=Vector3(x,y,z), color=COLOR_CYAN))
            

    def setup_hud_controls(self):
        # Simple touch areas for movement and fire
        button_size = 100
        padding = 20

        # Left/Right for rotation
        self.left_button_rect = scene.Rect(padding, padding + button_size, button_size, button_size) # x, y, w, h
        self.right_button_rect = scene.Rect(self.size.w - padding - button_size, padding + button_size, button_size, button_size)

        # Up/Down for movement
        self.forward_button_rect = scene.Rect(self.size.w / 2 - button_size / 2, padding + button_size, button_size, button_size)
        self.backward_button_rect = scene.Rect(self.size.w / 2 - button_size / 2, padding, button_size, button_size)

        # Fire button
        self.fire_button_rect = scene.Rect(self.size.w - padding - button_size, padding, button_size, button_size)
        
        # Radar Settings ---
        self.radar_size = 150 # Diameter of the radar circle in pixels
        self.radar_padding = 20 # Padding from top-left corner
        self.radar_center_x = self.radar_padding + self.radar_size / 2
        self.radar_center_y = self.size.h - self.radar_padding - self.radar_size / 2
        self.radar_range = WORLD_SIZE * 0.7 # Max world distance shown on radar, adjust as needed
        # The above line is a good starting point. You might want to adjust
        # `radar_range` to show enemies closer or further, depending on WORLD_SIZE.
        self.radar_dot_size = 8
        

    def draw(self):
        scene.background(self.background_color[0], self.background_color[1], self.background_color[2])
        if self.game_over:
            self.text("GAME OVER", font=('HelveticaNeue-Bold', 80), x=self.size.w/2, y=self.size.h/2 + 50, color=COLOR_RED)
            self.text(f"SCORE: {self.score}", font=('HelveticaNeue-Bold', 40), x=self.size.w/2, y=self.size.h/2 - 20, color=COLOR_WHITE)
            self.text("Tap to Restart", font=('HelveticaNeue-Light', 30), x=self.size.w/2, y=self.size.h/2 - 80, color=COLOR_WHITE)
            return

        # Player position is origin for camera view
        camera_pos = Vector3(0, self.camera_offset_y, 0)
        camera_yaw = self.player.rotation_y
        camera_pitch = self.camera_pitch # For future vertical camera movement

        # All drawable objects
        # Get individual wireframe objects from the player and enemies
        all_objects = self.player.get_all_wireframe_objects() + self.obstacles + self.bullets
        for enemy in self.enemies:
            all_objects.extend(enemy.get_all_wireframe_objects())

        # Sort objects by Z-depth (further objects drawn first for proper overlap with lines)
        # This is a simple approximation; true 3D engines handle this with depth buffers.
        # Here, we sort by distance from player, but clipping is more important for wireframe.
        sorted_objects = sorted(all_objects, key=lambda obj: (obj.position_in_world - self.player.position).length(), reverse=True) # Use position_in_world for sorting
        # Or, even better, sort by their 'average' Z-coordinate in camera space *before* projection.
        # But for now, world-space distance is a decent approximation for wireframe.

        for obj in sorted_objects:
            if not obj.visible:
                continue            
            obj_world_vertices = obj.get_world_vertices()

            camera_space_vertices = []
            for v in obj_world_vertices:
                # Translate relative to camera (player's world position)
                v_rel_camera = v - self.player.position # Camera is always at player's origin
                # Rotate inverse of camera's Y-rotation (player's yaw)
                v_cam_rot_y = v_rel_camera.rotate_y(-camera_yaw)
                camera_space_vertices.append(v_cam_rot_y) # Using just Y rotation for now

            # Project camera-space vertices to 2D screen coordinates
            screen_points = []
            for v_cam in camera_space_vertices:
                # Clip points behind Z_NEAR or beyond Z_FAR
                if v_cam.z < Z_NEAR or v_cam.z > Z_FAR:
                    screen_points.append(None) # Mark as invisible
                    continue
                # Perspective projection
                screen_x = (v_cam.x * FOCAL_LENGTH / v_cam.z) * self.size.w + self.size.w / 2
                screen_y = (v_cam.y * FOCAL_LENGTH / v_cam.z) * self.size.h + self.size.h / 2
                screen_points.append(scene.Point(screen_x, screen_y))

            # Draw edges
            scene.stroke(*obj.color)
            scene.stroke_weight(2) # Adjust line thickness

            for i1, i2 in obj.edges:
                p1 = screen_points[i1]
                p2 = screen_points[i2]
                if p1 and p2: # Only draw if both points are visible
                    scene.line(p1.x, p1.y, p2.x, p2.y)

        # Draw HUD ---
        self.draw_hud_controls()
        self.draw_hud_info()
        self.draw_radar()

    
    def draw_hud_controls(self):
        # Draw translucent rectangles for controls
        scene.fill(0, 0, 0, 0.4) # Semi-transparent black

        # Movement buttons
        scene.rect(*self.left_button_rect)
        scene.rect(*self.right_button_rect)
        scene.rect(*self.forward_button_rect)
        scene.rect(*self.backward_button_rect)
        scene.rect(*self.fire_button_rect)

        # Draw icons/text on buttons
        color=(1, 1, 1, 0.8) # White, semi-transparent
        btn_font = ('HelveticaNeue-Bold', 30)
        btn_center_offset = 50 # Half button size

        self.text("<<", font=btn_font,
                  x=self.left_button_rect[0] + btn_center_offset,
                  y=self.left_button_rect[1] + btn_center_offset,
                  color=color)
        self.text(">>", font=btn_font, 
                  x=self.right_button_rect[0] + btn_center_offset, 
                  y=self.right_button_rect[1] + btn_center_offset, 
                  color=color)
        self.text("FWD", font=btn_font, 
                  x=self.forward_button_rect[0] + btn_center_offset, 
                  y=self.forward_button_rect[1] + btn_center_offset, 
                  color=color)
        self.text("BWD", font=btn_font, 
                  x=self.backward_button_rect[0] + btn_center_offset, 
                  y=self.backward_button_rect[1] + btn_center_offset, 
                  color=color)
        self.text("FIRE", font=btn_font, 
                  x=self.fire_button_rect[0] + btn_center_offset, 
                  y=self.fire_button_rect[1] + btn_center_offset, 
                  color=color)


    def draw_hud_info(self):
        # Health Bar
        health_bar_width = 200
        health_bar_height = 20
        health_x = 20
        health_y = self.size.h - 30

        scene.fill(0, 0, 0, 0.6)
        scene.rect(health_x, health_y, health_bar_width, health_bar_height)
        health_ratio = self.player.health / self.player.max_health
        health_color = (1 - health_ratio, health_ratio, 0, 1) # Green to Red
        scene.fill(health_color[0], health_color[1], health_color[2], health_color[3])
        scene.rect(health_x, health_y, health_bar_width * health_ratio, health_bar_height)
        self.text(f"HP: {int(self.player.health)}", font=('HelveticaNeue-Bold',16),  x=health_x + health_bar_width / 2, y=health_y + health_bar_height / 2, color=COLOR_WHITE)

        # Score
        self.text(f"SCORE: {self.score}", font=('HelveticaNeue-Bold',24), x=self.size.w - 100, y=self.size.h - 30, alignment=6)
        
    # Part of scene_battlezone_game.py (Add to BattleZone class)

    def draw_radar(self):
        # Draw radar background circle
        scene.fill(0, 0, 0, 0.6) # Semi-transparent black
        scene.ellipse(self.radar_center_x - self.radar_size / 2,
                   self.radar_center_y - self.radar_size / 2,
                   self.radar_size, self.radar_size)

        # Draw radar border
        scene.stroke(COLOR_GREEN[0], COLOR_GREEN[1], COLOR_GREEN[2], 0.8) # Green border
        scene.stroke_weight(2)
        scene.no_fill()
        scene.ellipse(self.radar_center_x - self.radar_size / 2,
                   self.radar_center_y - self.radar_size / 2,
                   self.radar_size, self.radar_size)
        scene.fill(1,1,1,1) # Reset fill for dots

        # Draw player dot (always at center, pointing up)
        scene.fill(COLOR_GREEN[0], COLOR_GREEN[1], COLOR_GREEN[2], 1)
        scene.ellipse(self.radar_center_x - self.radar_dot_size / 2,
                   self.radar_center_y - self.radar_dot_size / 2,
                   self.radar_dot_size, self.radar_dot_size)

        # Draw a small line for player's facing direction
        player_facing_x = self.radar_center_x
        player_facing_y = self.radar_center_y + self.radar_dot_size
        scene.line(self.radar_center_x, self.radar_center_y, player_facing_x, player_facing_y)

        # Draw enemy dots
        for enemy in self.enemies:
            if not enemy.visible:
                continue

            # Calculate relative position of enemy to player
            # Player is at (0,0) on the radar, facing up (positive Y)
            rel_pos = enemy.position - self.player.position

            # Rotate relative position inversely to player's rotation
            # This makes the radar always oriented with the player facing 'up'
            # (i.e., the world rotates around the player on the radar)
            cos_yaw = math.cos(-self.player.rotation_y)
            sin_yaw = math.sin(-self.player.rotation_y)

            rotated_x = rel_pos.x * cos_yaw + rel_pos.z * sin_yaw
            rotated_z = -rel_pos.x * sin_yaw + rel_pos.z * cos_yaw # Use Z as Y-axis on radar

            # Scale to radar size
            # Scale factor: radar_size / radar_range
            scale_factor = (self.radar_size / 2) / self.radar_range

            radar_x = rotated_x * scale_factor
            radar_y = rotated_z * scale_factor # Z in world space is Y on radar

            # Clamp enemies to radar edge if they are out of radar_range
            if math.sqrt(radar_x**2 + radar_y**2) > self.radar_size / 2:
                angle = math.atan2(radar_y, radar_x)
                radar_x = (self.radar_size / 2) * math.cos(angle)
                radar_y = (self.radar_size / 2) * math.sin(angle)

            # Convert to screen coordinates
            screen_radar_x = self.radar_center_x + radar_x
            screen_radar_y = self.radar_center_y + radar_y

            # Draw enemy dot
            scene.fill(COLOR_RED[0], COLOR_RED[1], COLOR_RED[2], 1) # Red for enemies
            scene.ellipse(screen_radar_x - self.radar_dot_size / 2,
                       screen_radar_y - self.radar_dot_size / 2,
                       self.radar_dot_size, self.radar_dot_size)

        # Reset fill/stroke
        scene.no_stroke()
        scene.fill(1,1,1,1)

        
    def update(self):
        dt = self.dt

        if self.game_over:
            return

        # Player movement
        forward_dir = Vector3(math.sin(self.player.rotation_y), 0, math.cos(self.player.rotation_y))
        
        if self.forward_pressed:
            self.player.position += forward_dir * self.player.speed * dt
        if self.backward_pressed:
            self.player.position -= forward_dir * self.player.speed * dt
        
        if self.left_pressed:
            self.player.rotation_y += self.player.rotation_speed * dt
            # Self-correction: if player rotates, turret/barrel need to stay aligned with direction of player,
            # or aim independently if that's the design. For now, tank rotation rotates turret and barrel.
            # If you want independent turret/barrel aiming, you'd adjust turret_relative_yaw and barrel_pitch here.
        if self.right_pressed:
            self.player.rotation_y -= self.player.rotation_speed * dt

        # Clamp player position to world bounds
        self.player.position.x = clamp(self.player.position.x, -WORLD_SIZE, WORLD_SIZE)
        self.player.position.z = clamp(self.player.position.z, -WORLD_SIZE, WORLD_SIZE)

        # Update bullets (no change here from before)
        bullets_to_remove = []
        for bullet in self.bullets:
            if bullet.visible:
                bullet.update(dt)
                if not bullet.visible:
                    bullets_to_remove.append(bullet)
            else:
                bullets_to_remove.append(bullet)
        
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)
        
        # Enemy spawning
        if self.t - self.last_enemy_spawn_time > ENEMY_SPAWN_INTERVAL and len(self.enemies) < MAX_ENEMIES:
            self.spawn_enemy()
            self.last_enemy_spawn_time = self.t

        # Update enemies (their internal components will update their position_in_world in get_all_wireframe_objects)
        enemies_to_remove = []
        for enemy in self.enemies:
            if enemy.visible:
                enemy.update(dt, self.player.position) # This updates enemy.position and enemy.rotation_y
                # Enemy AI for aiming (simplified): point turret and barrel at player
                if self.player.position:
                    dir_to_player_3d = self.player.position - enemy.position
                    
                    # Calculate desired yaw for turret
                    desired_turret_yaw_world = math.atan2(dir_to_player_3d.x, dir_to_player_3d.z)
                    enemy.turret_relative_yaw = desired_turret_yaw_world - enemy.rotation_y # Relative to tank body

                    # Calculate desired pitch for barrel
                    # We need the y-component and the horizontal distance for pitch
                    horizontal_dist = math.sqrt(dir_to_player_3d.x**2 + dir_to_player_3d.z**2)
                    desired_barrel_pitch = math.atan2(-dir_to_player_3d.y, horizontal_dist) # Negative y because +y is up, -pitch is down
                    enemy.barrel_pitch = desired_barrel_pitch
                    # Clamp barrel pitch to reasonable limits (e.g., -math.pi/4 to math.pi/4)
                    enemy.barrel_pitch = clamp(enemy.barrel_pitch, -math.pi/6, math.pi/4) # Example limits
                # Enemy firing
                if self.t - enemy.last_fire_time > enemy.fire_rate:
                    self.fire_bullet(enemy)
                    enemy.last_fire_time = self.t
            else:
                enemies_to_remove.append(enemy)

        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)

        # Collision Detection ---
        # Bullet-Enemy collisions (still use the Tank's main position for collision)
        for bullet in list(self.bullets):
            if not bullet.visible or not bullet.fired_by_player:
                continue
            
            for enemy in list(self.enemies):
                if not enemy.visible:
                    continue

                # Use a larger collision radius for the enemy tank, based on its overall size
                enemy_collision_radius = max(enemy.hull.width, enemy.hull.length) * enemy.scale / 2
                if (bullet.position - enemy.position).length() < (bullet.scale / 2 + enemy_collision_radius):
                    bullet.visible = False
                    if enemy.take_damage(25):
                        self.score += SCORE_PER_KILL

        # Enemy Bullet-Player collisions
        for bullet in list(self.bullets):
            if not bullet.visible or bullet.fired_by_player:
                continue

            # Use a larger collision radius for the player tank
            player_collision_radius = max(self.player.hull.width, self.player.hull.length) * self.player.scale / 2
            if (bullet.position - self.player.position).length() < (bullet.scale / 2 + player_collision_radius):
                bullet.visible = False
                if self.player.take_damage(20):
                    self.game_over = True
                    sound.play_effect('arcade:Explosion_1', 1.0, 1.0, 0.5)

        # Player-Enemy direct collision (could add damage here too)
        for enemy in self.enemies:
            if enemy.visible:
                enemy_collision_radius = max(enemy.hull.width, enemy.hull.length) * enemy.scale / 2
                player_collision_radius = max(self.player.hull.width, self.player.hull.length) * self.player.scale / 2
                if (self.player.position - enemy.position).length() < (player_collision_radius + enemy_collision_radius):
                    pass # Collision detected, implement push back or damage if desired
                    
    def fire_bullet(self, shooter_object):
        # Calculate bullet starting position and direction from the barrel's perspective
        
        # Get the shooter's barrel component
        barrel_component = None
        for comp in shooter_object.components:
            if isinstance(comp, WireCylinder) and comp is shooter_object.barrel:
                barrel_component = comp
                break
        
        if not barrel_component:
            print("Error: Barrel component not found for firing!")
            return

        # Calculate the barrel's tip in world coordinates
        # The barrel's local Z-axis points forward (after its initial -pi/2 pitch)
        # So the tip is at (0, 0, -barrel_length/2) in its *local* space (assuming it's centered)
        # We offset it by its local Z to get the end of the barrel.
        
        # Barrel's length is `height` property of WireCylinder
        barrel_local_tip_offset = Vector3(0, 0, -barrel_component.height / 2)

        # Apply barrel's full world rotation to this offset
        rotated_tip_offset = barrel_local_tip_offset.rotate_z(barrel_component.rotation_angles_in_world.z)
        rotated_tip_offset = rotated_tip_offset.rotate_y(barrel_component.rotation_angles_in_world.y)
        rotated_tip_offset = rotated_tip_offset.rotate_x(barrel_component.rotation_angles_in_world.x)

        # Add to barrel's world position
        bullet_start_pos = barrel_component.position_in_world + rotated_tip_offset

        # Bullet direction is simply the barrel's local Z-axis rotated by its world rotation
        bullet_direction = Vector3(0, 0, -1) # Local forward (negative Z for barrel, as it extends "out")
        bullet_direction = bullet_direction.rotate_z(barrel_component.rotation_angles_in_world.z)
        bullet_direction = bullet_direction.rotate_y(barrel_component.rotation_angles_in_world.y)
        bullet_direction = bullet_direction.rotate_x(barrel_component.rotation_angles_in_world.x)
        
        bullet = Bullet(
            position=bullet_start_pos,
            direction=bullet_direction,
            speed=BULLET_SPEED
        )
        bullet.fired_by_player = shooter_object.is_player
        self.bullets.append(bullet)
        sound.play_effect('digital:Laser1', 0.1, 1.0, 0.05)

    def spawn_enemy(self):
        # Spawn enemy somewhere far from player
        spawn_dist = WORLD_SIZE * 0.7 # Approx distance from center
        angle = random.uniform(0, 2 * math.pi)
        x = spawn_dist * math.cos(angle)
        z = spawn_dist * math.sin(angle)
        
        # Adjust for player's actual position
        spawn_pos = self.player.position + Vector3(x, 0, z)

        # Ensure enemy is within world bounds
        spawn_pos.x = clamp(spawn_pos.x, -WORLD_SIZE + 50, WORLD_SIZE - 50)
        spawn_pos.z = clamp(spawn_pos.z, -WORLD_SIZE + 50, WORLD_SIZE - 50)

        enemy = Tank(position=spawn_pos, color=COLOR_YELLOW)
        enemy.speed = ENEMY_SPEED
        enemy.fire_rate = ENEMY_FIRE_RATE * random.uniform(0.8, 1.2) # Vary enemy fire rate
        self.enemies.append(enemy)
        #print(f"Spawned enemy at {enemy.position}")


    def touch_began(self, touch):
        if self.game_over:
            # Restart game on tap if game over
            self.setup()
            return
        if self.left_button_rect.contains_point(touch.location):
            self.left_pressed = True
        elif self.right_button_rect.contains_point(touch.location):
            self.right_pressed = True
        elif self.forward_button_rect.contains_point(touch.location):
            self.forward_pressed = True
        elif self.backward_button_rect.contains_point(touch.location):
            self.backward_pressed = True
        elif self.fire_button_rect.contains_point(touch.location):
            self.fire_pressed = True
            self.fire_bullet(self.player)

    
    def touch_ended(self, touch):
        # Check all buttons that might have been released
        # This allows multi-touch for movement and fire simultaneously
        if self.left_button_rect.contains_point(touch.location):
            self.left_pressed = False
        elif self.right_button_rect.contains_point(touch.location):
            self.right_pressed = False
        elif self.forward_button_rect.contains_point(touch.location):
            self.forward_pressed = False
        elif self.backward_button_rect.contains_point(touch.location):
            self.backward_pressed = False
        if self.fire_button_rect.contains_point(touch.location):
            self.fire_pressed = False

    def touch_moved(self, touch):
        # We handle button presses on begin/end, so touch_moved isn't strictly needed for controls
        pass


if __name__ == '__main__':
    scene.run(BattleZone(), show_fps=True)
    
