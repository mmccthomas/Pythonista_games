"""
Claude generated galaxians from assembly code
I have converted drawing to SpriteNodes
explosion animation is replaced by Explosion class
removed many _draw methods as we only need to move and delete sprites
Flight and shooting logic has remained unchanged from assembly code

Galaxian – Pythonista/scene implementation with pixel-art sprites
Based on reverse engineering by Scott Tunstall (Namco 1979)

All sprites are defined as colour-index grids (see PALETTES + SPRITE_DATA).
make_sprite() builds a PIL image, registers it via scene.load_pil_image(),
and scene.image(texture_name) renders it each frame at zero GC cost.

Coordinate convention (Pythonista scene: y=0 at BOTTOM):
  sy increases upward.  Swarm sits near top (high sy), player at bottom (low sy).
  Inflight aliens start at swarm sy and DECREASE sy (dive downward toward player).
  Player bullet INCREASES sy (travels upward).
  Enemy bullets DECREASE sy (travel downward).
"""

import scene
import ui
import math
import random
from scene import (
    fill,
    text,
    rect,
    tint,
    background,
    ellipse,
    SpriteNode,
    Action,
    Texture,
    Node,
    Point,
    TIMING_SINODIAL
)
from PIL import Image as PILImage
import io
from math import pi
from random import uniform as rnd
from change_screensize import get_screen_size
import joystick
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s]: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # Set root logger level to DEBUG


def is_debug_level():
    return logging.getLevelName(logger.getEffectiveLevel()) == 'DEBUG'

# ─────────────────────────────────────────────────────────────────────────────
# Screen
# ─────────────────────────────────────────────────────────────────────────────


W, H = get_screen_size()
SW, SH = 3 * H // 4, H
JOYSTICK_DEAD_ZONE = 0.1
SPRITE_SCALE = 4  # logical px → screen px

# ─────────────────────────────────────────────────────────────────────────────
# Swarm layout
# ─────────────────────────────────────────────────────────────────────────────
SWARM_COLS = 10
SWARM_ROWS = 6
CELL_W = 60
CELL_H = 48
SWARM_LEFT = (SW - SWARM_COLS * CELL_W) // 2
SWARM_BASE_Y = SH - 308  # sy of row-0 (bottom blue row); rows stack upward

LIVES = 20
MAX_BULLETS = 10
HIT_BULLETS = True
DIVE_SPEED = 50  # 100
RETURN_SPEED = 95
BULLET_SPEED = 75  # 150
PLAYER_BULLET_SPEED = 640 #  430

PLAYER_BASE_Y = 58
ROW_TYPES = ["blue", "blue", "blue", "purple", "red", "flagship"]

# ─────────────────────────────────────────────────────────────────────────────
# Colour palette  (r, g, b, a)  –  index 0 = transparent
# ─────────────────────────────────────────────────────────────────────────────
_ = None  # transparent shorthand used in sprite grids

PAL = {
    # shared / neutral
    "T": None,  # 0 transparent
    "W": (1.00, 1.00, 1.00, 1.0),  # white
    "K": (0.00, 0.00, 0.00, 1.0),  # black (eye)
    "G": (0.55, 0.55, 0.55, 1.0),  # mid-grey wing detail
    "Y": (1.00, 1.00, 0.40, 1.0),  # yellow nose / highlight
    # blue alien
    "B": (0.20, 0.55, 1.00, 1.0),  # blue body
    "b": (0.10, 0.30, 0.75, 1.0),  # blue dark
    # purple alien
    "P": (0.80, 0.20, 1.00, 1.0),  # purple body
    "p": (0.50, 0.10, 0.70, 1.0),  # purple dark
    # red alien
    "R": (1.00, 0.22, 0.22, 1.0),  # red body
    "r": (0.70, 0.08, 0.08, 1.0),  # red dark
    # flagship
    "F": (1.00, 0.85, 0.00, 1.0),  # gold body
    "f": (0.80, 0.55, 0.00, 1.0),  # gold dark
    "C": (0.60, 0.90, 1.00, 1.0),  # cyan cockpit
    # player ship
    "S": (0.30, 1.00, 0.60, 1.0),  # ship green
    "s": (0.15, 0.65, 0.40, 1.0),  # ship dark green
    "A": (0.50, 1.00, 0.82, 1.0),  # cockpit aqua
    "E": (0.30, 0.70, 1.00, 1.0),  # engine blue
    # bullet / explosion
    "L": (1.00, 1.00, 0.40, 1.0),  # bullet yellow
    "l": (1.00, 0.80, 0.20, 1.0),  # bullet orange core
    "X": (1.00, 0.50, 0.00, 1.0),  # explosion orange
    "x": (1.00, 0.20, 0.00, 1.0),  # explosion red
    "O": (1.00, 1.00, 0.60, 1.0),  # explosion white-yellow
}

# ─────────────────────────────────────────────────────────────────────────────
# Sprite pixel grids
# Each grid is a list of rows (top→bottom), each row a list of palette keys.
# ─────────────────────────────────────────────────────────────────────────────

# ── Blue alien – 11 × 8, two wing-flap frames ────────────────────────────────
BLUE_F0 = [
    list("TTTTBTBTTTT"),  # antennae
    list("TTTTBTBTTTT"),
    list("BTTBBBBBTTB"),
    list("BBBBRBRBBBB"),  # body with dark underside
    list("TTTBBBBBTTT"),
    list("TbbbBBBbbbT"),  # wings closed (frame 0)
    list("bbbTBBBTbbb"),
    list("bbTTTBTTTbb"),
]

BLUE_F1 = [
    
    list("BTTTBTBTTTB"),  # antennae
    list("BTTBBBBBTTB"),
    list("TBBBRBRBBBT"),  # body with dark underside
    list("bTTBBBBBTTb"),
    list("bbbbBBBbbbb"),  # wings open (frame 1)
    list("TbbTBBBTbbT"),
    list("TTTTTBTTTTT"),
]
# ── Purple alien – 11 × 8, two frames ────────────────────────────────────────
PURPLE_F0 = [
    list("TTTTPTPTTTT"),  # antennae
    list("TTTTPTPTTTT"),
    list("PTTPPPPPTTP"),
    list("PPPPRPRPPPP"),  # body with dark underside
    list("TTTPPPPPTTT"),
    list("TbbbPPPbbbT"),  # wings closed (frame 0)
    list("bbbTPPPTbbb"),
    list("bbTTTPTTTbb"),
]
PURPLE_F1 = [
    # antennae
    list("PTTTPTPTTTP"),
    list("PTTPPPPPTTP"),
    list("TPPPRPRPPPT"),  # body with dark underside
    list("bTTPPPPPTTb"),
    list("bbbbPPPbbbb"),  # wings open (frame 1)
    list("TbbTPPPTbbT"),
    list("TTTTTPTTTTT"),
]

# ── Red alien – 13 × 9, two frames ───────────────────────────────────────────
RED_F0 = [
    list("TTTTRTRTTTT"),  # antennae
    list("TTTTRTRTTTT"),
    list("RTTRRRRRTTR"),
    list("RRRRYRYRRRR"),  # body with dark underside
    list("TTTRRRRRTTT"),
    list("TbbbRRRbbbT"),  # wings closed (frame 0)
    list("bbbTRRRTbbb"),
    list("bbTTTRTTTbb"),
]
RED_F1 = [
    # antennae
    list("RTTTRTRTTTR"),
    list("RTTRRRRRTTR"),
    list("TRRRYRYRRRT"),  # body with dark underside
    list("bTTRRRRRTTb"),
    list("bbbbRRRbbbb"),  # wings open (frame 1)
    list("TbbTRRRTbbT"),
    list("TTTTTRTTTTT"),
]
# ── Flagship – 16 × 10, two frames ───────────────────────────────────────────
FLAG_F0 = [
    list("TTTTTRTTTTT"),  # 15 wide
    list("bTTTRRRTTTb"),
    list("bTTRRRRRTTb"),
    list("bYRRYRYRRYb"),
    list("bYYYYRYYYYb"),
    list("bbYYYYYYYbb"),  # engine pods
    list("TbbYTYTYbbT"),
    list("TTbbTYTbbTT"),
    list("TTTbTYTbTTT"),
    list("TTTTTYTTTTT"),
    list("TTTTTYTTTTT"),
]
# Second frame: subtle engine glow shift
FLAG_F1 = [
    list("TTTTTRTTTTT"),  # 15 wide
    list("bTTTRRRTTTb"),
    list("bTTRRRRRTTb"),
    list("bYRRYRYRRYb"),
    list("bYYYYRYYYYb"),
    list("bbYYYYYYYbb"),  # engine pods
    list("TbbYTYTYbbT"),
    list("TTbbTYTbbTT"),
    list("TTTbTYTbTTT"),
    list("TTTTTYTTTTT"),
    list("TTTTTYTTTTT"),
]

# ── Player ship – 13 × 9 ─────────────────────────────────────────────────────
PLAYER_SPR = [
    # 12 wide  nose tip at top
    list("TTTTTYTTTTT"),
    list("TTTTTYTTTTT"),
    list("TTTTTYTTTTT"),
    list("TTTTRRRTTTT"),
    list("TTTRRRRRTTT"),
    list("TTRRRRRRRTT"),
    list("TTRRRRRRRTT"),
    list("TTRTTRTTRTT"),
    list("TTTTCRCTTTT"),
    list("TTTTCRCTTTT"),
    list("TTTTCRCTTTT"),
    list("CTTCCRCCTTC"),
    list("CTCCCRCCCTC"),
    list("CCCCCRCCCCC"),
    list("CTCTCRCTCTC"),
    list("CTTTCTCTTTC"),
    list("CTTTTTTTTTC"),
]

# ── Player bullet – 3 × 8 ────────────────────────────────────────────────────
BULLET_SPR = [
    list("TlT"),
    list("TLT"),
    list("LLL"),
    list("LLL"),
    list("LLL"),
    list("LLL"),
    list("TLT"),
    list("TlT"),
]

# ── Enemy bullet – 3 × 5 ─────────────────────────────────────────────────────
EBULLET_SPR = [
    list("LTL"),
    list("LlL"),
    list("LlL"),
    list("LlL"),
    list("TLT"),
]

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Sprite baker
# Build sprites as PIL RGBA images, register each with
# ─────────────────────────────────────────────────────────────────────────────

# Cache sprite pixel dimensions: name -> (w, h) in screen pixels
SPRITE_SIZES = {}


def pil_to_ui(img):
    with io.BytesIO() as bIO:
        img.save(bIO, "png")
        return ui.Image.from_data(bIO.getvalue())


def make_texture(grid, scale=SPRITE_SCALE):
    rows = len(grid)
    cols = max(len(r) for r in grid)
    pil = PILImage.new("RGBA", (int(cols * scale), int(rows * scale)), (0, 0, 0, 0))
    px = pil.load()
    for ri, row in enumerate(grid):
        for ci, key in enumerate(row):
            col = PAL.get(key)
            if not col:
                continue
            rgba = tuple(int(c * 255) for c in col)
            for dy in range(scale):
                for dx in range(scale):
                    px[ci * scale + dx, ri * scale + dy] = rgba
    return Texture(pil_to_ui(pil))


def flip_grid_h(grid):
    """Return a copy of a pixel grid mirrored horizontally."""
    return grid[::-1]


def make_sprites():
    """
    Bake every sprite into PIL images, register them, and return a dict
    mapping label -> texture-name string for use with scene.image().
    """

    s = {}
    pairs = [
        ("blue_0", BLUE_F0),
        ("blue_1", BLUE_F1),
        ("purple_0", PURPLE_F0),
        ("purple_1", PURPLE_F1),
        ("red_0", RED_F0),
        ("red_1", RED_F1),
        ("flag_0", FLAG_F0),
        ("flag_1", FLAG_F1),
    ]
    for name, grid in pairs:
        s[name] = make_texture(grid)
        s[name + "_flip"] = make_texture(flip_grid_h(grid))
    s["player"] = make_texture(PLAYER_SPR)
    # s['player_flip']      = make_texture(flip_grid_h(PLAYER_SPR))
    s["pbullet"] = make_texture(BULLET_SPR)
    s["ebullet"] = make_texture(EBULLET_SPR)

    return s


# ─────────────────────────────────────────────────────────────────────────────
# Game constants
# ─────────────────────────────────────────────────────────────────────────────
ALIEN_POINTS = {
    "blue": 30,
    "purple": 60,
    "red": 80,
    "flagship_solo": 150,
    "flagship_1esc": 300,
    "flagship_2esc": 800,
}

SCRIPT_ATTRACT = 0
SCRIPT_GAME = 1
SCRIPT_GAMEOVER = 2

SOL_PACKS_BAGS = 0
SOL_FLIES_ARC = 1
SOL_READY_ATTACK = 2
SOL_ATTACKING = 3
SOL_NEAR_BOTTOM = 4
SOL_PAST_PLAYER = 5
SOL_RETURNING = 6

ARC_TABLE = [
    (2, -3),
    (3, -2),
    (3, -1),
    (4, -1),
    (4, 0),
    (4, 0),
    (4, 1),
    (4, 1),
    (3, 2),
    (3, 2),
    (2, 3),
    (2, 3),
    (1, 3),
    (0, 3),
]
ARC_SCALE = 3.8

C_BG = (0.00, 0.00, 0.08)
C_WHITE = (1.00, 1.00, 1.00)
C_GREEN = (0.20, 1.00, 0.45)
C_GOLD = (1.00, 0.85, 0.00)
C_RED = (1.00, 0.22, 0.22)
C_PLAYER = (0.30, 1.00, 0.60)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


class GalaxianRNG:
    def __init__(self):
        self.state = 0xE0

    def next(self):
        self.state = ((self.state * 5) + 1) & 0xFF
        return self.state

    def flt(self):
        return self.next() / 255.0


rng = GalaxianRNG()


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────
class Alien:
    # __slots__=('row','col','alive','kind','frame','anim_t', 'sprite', 'parent', 'texture_name')
    def __init__(self, parent, row, col):
        self.row = row
        self.col = col
        self.alive = True
        self.kind = ROW_TYPES[row]
        self.frame = 0
        self.anim_t = 0.0
                
        self.parent = parent
        x = SWARM_LEFT + col * CELL_W
        y = SWARM_BASE_Y + row * CELL_H
        lookup = {
            "blue": "blue_0",
            "purple": "purple_0",
            "red": "red_0",
            "flagship": "flag_0",
        }
        self.texture_name = lookup[self.kind]
        self.sprite = SpriteNode(
            parent.textures[lookup[self.kind]], position=(x, y), parent=parent
        )

    def __del__(self):
        self.sprite.remove_from_parent()

    def pos(self):
        sx = SWARM_LEFT + self.col * CELL_W + CELL_W // 2 + self.parent.swarm_dx
        sy = SWARM_BASE_Y + self.row * CELL_H
        return sx, sy

    def move(self, x, y):
        self.sprite.position = (x, y)

    def toggle_texture(self):
        """ alternate sprite textures """
        def invert_suffix(s):
            if s.endswith('_0'):
                return s[:-2] + '_1'
            elif s.endswith('_1'):
                return s[:-2] + '_0'
            return s

        self.texture_name = invert_suffix(self.texture_name)
        self.sprite.texture = self.parent.textures[self.texture_name]

    def flip(self):
        texture_name = self.texture_name + "_flip"
        self.sprite.texture = self.parent.textures[texture_name]

    def explode(self, duration=0.55):
        self.sprite.remove_from_parent()
        self.parent.add_child(Explosion(self.sprite, duration=duration))


class InflightAlien:
    """an Alien in flight"""

    def __init__(self, src, sx, sy, clockwise=False):
        self.alien = src
        self.kind = src.kind
        self.sx = float(sx)
        self.sy = float(sy)
        self.active = True
        self.dying = False
        self.stage = SOL_PACKS_BAGS
        self.clockwise = clockwise
        self.arc_step = 0
        self.anim_f = 0.0
        self.pivot_sx = float(sx)
        self.pivot_dx = 0.0
        self.sortie = 0
        self.death_t = 0.0
        self.escort_ct = 0
        self.last_shoot_time = 0
        self.shoot_delay = 1.5  # Seconds between shots
        self._flip_h = clockwise  # mirror sprite when arcing right
        self.alien.sprite.position = (sx, sy)

    def __del__(self):
        self.alien.sprite.remove_from_parent()

    def move(self, sx, sy):
        self.alien.sprite.position = (sx, sy)

    def explode(self, duration=0.55):
        self.alien.explode(duration=duration)

    @property
    def flip_h(self):
        """The getter: returns the current horizontal flip state."""
        return self._flip_h

    @flip_h.setter
    def flip_h(self, value):
        """Updates the horizontal flip state with a smooth rotation animation."""
        if not isinstance(value, bool):
            raise ValueError("flip_h must be a boolean (True or False)")
        
        # Only trigger if the value actually changed to prevent redundant actions
        if self._flip_h != value:
            self._flip_h = value
            
            # Target angle: 180 degrees (pi) if True, 0 degrees if False
            target_angle = pi * int(self._flip_h)
            duration = 0.8  # Adjust for faster/slower flip
            
            # Run the rotation action
            self.alien.sprite.run_action(
                Action.rotate_to(target_angle, duration, TIMING_SINODIAL)
            )


class EnemyBullet:
    
    def __init__(self, parent, sx, sy, dsx):
        self.sx = float(sx)
        self.sy = float(sy)
        self.dsx = float(dsx)
        self.parent = parent
        self.active = True
        self.sprite = SpriteNode(
            parent.textures["ebullet"], position=(sx, sy), parent=parent
        )

    def __del__(self):
        self.sprite.remove_from_parent()

    def move(self, sx, sy):
        self.sx = sx
        self.sy = sy
        self.sprite.position = (sx, sy)
        
    def explode(self, duration=0.55):
        self.parent.add_child(Explosion(self.sprite, duration=duration))


class PlayerBullet:
    
    def __init__(self, parent, sx, sy):
        self.sx = float(sx)
        self.sy = float(sy)
        self.active = True
        self.sprite = SpriteNode(
            parent.textures["pbullet"], position=(sx, sy), parent=parent
        )

    def __del__(self):
        self.sprite.remove_from_parent()

    def move(self, sy):
        self.sy = sy
        self.sprite.position = (self.sx, sy)


class Player:
 
    def __init__(self, parent, sx, sy):
        self.sx = float(sx)
        self.sy = float(sy)
        self.active = True
        self.spawned = False
        self.dying = False
        self.death_t = 0.0
        self.parent = parent
        self.sprite = SpriteNode(
            parent.textures["player"], position=(sx, sy), parent=parent
        )

    def __del__(self):
        self.sprite.remove_from_parent()

    def move(self, sx):
        sx = clamp(sx, 20, SW-20)
        self.sx = sx
        self.sprite.position = (sx, self.sy)

    def explode(self, duration=0.55):
        self.parent.add_child(Explosion(self.sprite, duration=duration))
        
    def joystick_move(self, movement, dt):
        # movement is -1, 0, 1
        PLAYER_SPEED = 300
        # Move the player left or right
        new_x = self.sx + movement * PLAYER_SPEED * dt
        new_x = clamp(new_x, 20, SW-20)
        self.move(new_x)
        

class Star:
 
    def __init__(self):
        self.sx = random.random() * SW
        self.sy = random.random() * SH
        self.spd = random.uniform(8, 40)
        self.bri = random.uniform(0.3, 1.0)
        self.sz = random.uniform(5.0, 2.5)
        colours = [color for color in PAL.values() if color is not None]
        self.color = random.choice(colours)


class Explosion(Node):
    """Particle effect when row removed
    This is an advanced effect
    The game will work just fine without it
    """
    def __init__(self, tile, duration=0.8, radius=100, *args, **kwargs):
        Node.__init__(self, *args, **kwargs)
        self.position = tile.position

        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            p = SpriteNode(tile.texture, scale=0.5, parent=self)
            p.position = tile.size.w / 4 * dx, tile.size.h / 4 * dy
            p.size = tile.size
            p.run_action(
                Action.move_to(rnd(-radius, radius),
                               rnd(-radius, radius),
                               duration)
            )
            p.run_action(Action.scale_to(0, duration))
            p.run_action(Action.rotate_to(rnd(-pi / 2, pi / 2), duration))
        self.run_action(Action.sequence(Action.wait(duration), Action.remove()))


# to use self.add_child(Explosion(sprite))


# ─────────────────────────────────────────────────────────────────────────────
# Scene
# ─────────────────────────────────────────────────────────────────────────────
class GalaxianGame(scene.Scene):
    def setup(self):
        # use touch for movement or joystick
        self.use_touch = False

        # ── Multi-bullet setting ──────────────────────────────────────────────
        # Set max_player_bullets = 1 for classic single-shot behaviour.
        # Increase (e.g. 3) to allow multiple simultaneous player bullets.
        self.max_player_bullets = MAX_BULLETS
        # ─────────────────────────────────────────────────────────────────────
        
        # Bake all sprites once
        self.spr = make_sprites()
        self.textures = self.spr
        self.script = SCRIPT_ATTRACT
        self.tick = 0
        self.stars = [Star() for _ in range(80)]

        self.score = 0
        self.hi_score = 5000
        self.lives = LIVES
        self.level = 1
        self.bonus_threshold = 7000
        self.bonus_given = False
        self.diff_base = 2
        self.diff_extra = 0

          # ── Touch / input state ───────────────────────────────────────────────
        # Multitouch: we track each finger by its touch_id.
        #   move_touch_id  – the finger currently steering the ship (touch mode)
        #   active_touches – dict of touch_id -> latest x position
        # In touch mode the first finger down steers; any additional finger
        # (or a second tap while one is held) triggers an immediate shot.
        # In joystick mode any touch outside the joystick hitbox fires.
        self.move_touch_id = None   # ID of the steering finger (touch mode)
        self.active_touches = {}    # touch_id -> screen x
        self.joystick_touch_id = None  # ID of the finger on the joystick
        self.touched_sx = None      # current steering x (None = no movement)
        self.fire_btn = False       # one-frame fire pulse consumed by _move_player
        self.bullet_cd = 0.0
        # Player bullets are now stored as a list to support multiple
        # simultaneous bullets when max_player_bullets > 1.
        self.player_bullets = []

        self.swarm = []
        self.swarm_dx = 0.0
        self.swarm_dir = 1
        self.swarm_spd = 28.0
        self.halt_t = 0.0

        self.inflight = []
        self.enemy_bullets = []

        self.shock_flag = False
        self.shock_t = 0.0
        self.fs_atk_t = 2.5
        self.atk_counter = 8

        self.ai_target = SW / 2
        self.ai_fire_t = 0.8

        self.flash_t = 0.0
        self.blink_t = 0.0
        self.msg_text = ""
        self.msg_t = 0.0
        self.gameover_t = 0.0
        self.lvl_clear = False
        self.lvl_clear_t = 0.0
        
        self._reset_level()

    # ── swarm ────────────────────────────────────────────────────────────────
    def _init_swarm(self):
        self.swarm = []
        # for swarm.sprite in self.swarm: swarm.sprite.remove_from_parent()
        for row in range(SWARM_ROWS):
            for col in range(SWARM_COLS):
                if row == 5 and col not in (3, 6):
                    continue
                if row == 4 and not (2 <= col <= 7):
                    continue
                if row == 3 and not (1 <= col <= 8):
                    continue
                self.swarm.append(Alien(self, row, col))

    def _reset_level(self):
        for child in self.children:
            child.remove_from_parent()
        self.player = Player(self, SW / 2, PLAYER_BASE_Y)
        if not self.use_touch:
           # control joystick, press to fire
           self.joystick = joystick.Joystick(position=Point(0.9 * W, 0.1 * H),
                                             color='white',
                                             alpha=0.3,
                                             show_xy=False,
                                             msg='')
           self.add_child(self.joystick)
           self.moved = False
        
        self._init_swarm()
        self.inflight.clear()
        self.enemy_bullets.clear()
        self.player_bullets = []
        self.move_touch_id = None
        self.active_touches = {}
        self.touched_sx = None
        self.joystick_touch_id = None
        self.fire_btn = False
        self.swarm_dx = 0.0
        self.swarm_dir = 1
        self.halt_t = 0.0
        self.shock_flag = False
        self.shock_t = 0.0
        self.fs_atk_t = 2.5
        self.atk_counter = max(3, 9 - self.diff_base)
        self.lvl_clear = False
        self.lvl_clear_t = 0.0
        self.diff_extra = 0
        self.bonus_given = False
        self.player.spawned = True
        self.player.dying = False
        # place life sprites
        pname = self.textures.get("player")
        self.live_sprites = []
        if pname:
            pw, ph = pname.size
            sw2 = pw * 0.5 * 0.5
            sh2 = ph * 0.5 * 0.5
            for i in range(self.lives):
                self.live_sprites.append(
                    SpriteNode(
                        pname,
                        position=(20 + i * 22 - sw2, 25 - sh2),
                        scale=0.5,
                        parent=self,
                    )
                )

    def _start_game(self):
        self.script = SCRIPT_GAME
        self.score = 0
        self.lives = LIVES
        self.level = 1
        self.diff_base = 2
        self.diff_extra = 0
        self.bonus_given = False
        self._reset_level()

       # ── input ────────────────────────────────────────────────────────────────
    #
    # Multitouch scheme (use_touch=True):
    #   • The FIRST finger down becomes the "move touch" – it steers the ship
    #     by tracking its x position every frame.
    #   • Any ADDITIONAL finger that touches down fires immediately (one shot
    #     per new finger contact, subject to bullet_cd and max_player_bullets).
    #   • If the move finger lifts, the next still-active finger takes over
    #     as the new move touch seamlessly.
    #   • A lone quick tap (press + release with no second finger) both moves
    #     and fires, matching the classic feel.
    #
    # Joystick scheme (use_touch=False):
    #   • Touches inside the joystick bbox are forwarded to the joystick for
    #     movement exactly as before.
    #   • Any touch that lands OUTSIDE the joystick bbox fires immediately.
    #   • The old "moved" flag trick is preserved so a pure tap still fires.

    def touch_began(self, touch):
        if self.script != SCRIPT_GAME:
            self._start_game()
            return

        tid = touch.touch_id
        x   = touch.location.x

        if self.use_touch:
            self.active_touches[tid] = x

            if self.move_touch_id is None:
                # First finger: assign as move touch, warp ship to it, and
                # also fire (a tap always shoots).
                self.move_touch_id = tid
                self.touched_sx    = x
                self.player.move(x)
                self.fire_btn = True
            else:
                # Additional finger: fire only (don't hijack movement).
                self.fire_btn = True
        else:
            # Joystick mode: route by location on began, then track by ID.
            if self.joystick.bbox.contains_point(touch.location):
                self.joystick_touch_id = touch.touch_id
                self.joystick.touch_began(touch)
            else:
                # Tap anywhere outside joystick → shoot
                self.fire_btn = True

    def touch_moved(self, touch):
        tid = touch.touch_id
        x   = touch.location.x

        if self.use_touch:
            if tid in self.active_touches:
                self.active_touches[tid] = x
            if tid == self.move_touch_id:
                # Steering finger dragged – update ship position
                self.touched_sx = x
                self.player.move(
                    clamp(x, 20, SW - 20)
                )
        else:
            # Only forward to joystick if this is the joystick's own finger.
            if tid == self.joystick_touch_id:
                self.moved = True
                self.joystick.touch_moved(touch)
                self.joystick.update()
                movement = 0
                if self.joystick.x < -JOYSTICK_DEAD_ZONE:
                    movement = -1
                elif self.joystick.x > JOYSTICK_DEAD_ZONE:
                    movement = 1
                self.player.joystick_move(movement, self.dt)

    def touch_ended(self, touch):
        tid = touch.touch_id

        if self.use_touch:
            self.active_touches.pop(tid, None)

            if tid == self.move_touch_id:
                # Move finger lifted – hand off to another active finger if
                # one exists, otherwise stop tracking movement.
                if self.active_touches:
                    self.move_touch_id = next(iter(self.active_touches))
                    self.touched_sx    = self.active_touches[self.move_touch_id]
                else:
                    self.move_touch_id = None
                    self.touched_sx    = None
        else:
            if tid == self.joystick_touch_id:
                # The joystick finger lifted.
                self.joystick.touch_ended(touch)
                self.joystick_touch_id = None
                if not self.moved:
                    # Quick tap on joystick without dragging → fire
                    self.fire_btn = True
                self.moved = False
            else:
                # A non-joystick finger lifted → fire (tap-to-shoot).
                self.fire_btn = True
            
    # -----------update ───────────────────
    
    def update(self):
        dt = min(self.dt, 0.033)
        self.tick += 1
        self.flash_t += dt
        self.blink_t += dt
        self._upd_stars(dt)
        if self.script == SCRIPT_ATTRACT:
            self._upd_attract(dt)
        elif self.script == SCRIPT_GAME:
            self._upd_game(dt)
        elif self.script == SCRIPT_GAMEOVER:
            self._upd_gameover(dt)

    def _upd_stars(self, dt):
        for s in self.stars:
            s.sy -= s.spd * dt
            if s.sy < 0:
                s.sy = SH
                s.sx = random.random() * SW

    # -----------attract ───────────────────
    def _upd_attract(self, dt):
        self._upd_swarm(dt)
        self._upd_inflight(dt)
        self._upd_ebullets(dt)
        self._upd_pbullets(dt)
        self._handle_attacks(dt)
        self._attract_ai(dt)
        self._attract_fire(dt)
        self._check_level_clear()

    def _attract_ai(self, dt):
        dodge = False
        for b in self.enemy_bullets:
            if b.sy > self.player.sy and b.sy < self.player.sy + 130:
                diff = self.player.sx - b.sx
                if abs(diff) < 60:
                    self.ai_target = clamp(
                        self.player.sx + (70 if diff < 0 else -70), 25, SW - 25
                    )
                    dodge = True
                    break
        if not dodge:
            live = [a for a in self.swarm if a.alive]
            if live:
                cx = sum(
                    SWARM_LEFT + a.col * CELL_W + CELL_W // 2 + self.swarm_dx
                    for a in live
                ) / len(live)
                self.ai_target = clamp(cx, 25, SW - 25)
        dx = self.ai_target - self.player.sx
        self.player.move(
            clamp(self.player.sx + clamp(dx, -100 * dt, 100 * dt), 20, SW - 20)
        )

    def _attract_fire(self, dt):
        self.ai_fire_t -= dt
        if self.ai_fire_t <= 0:
            self.ai_fire_t = random.uniform(0.35, 1.1)
            self._shoot_player()
        # Attract mode never has a human pressing buttons; keep flag clear.
        self.fire_btn = False

    # -----------game ───────────────────
    def _upd_game(self, dt):
        if self.player.dying:
            self._upd_dying_player(dt)
            self._upd_swarm(dt)
            self._upd_inflight(dt)
            self._upd_ebullets(dt)
            return
        self._move_player(dt)
        self._upd_pbullets(dt)
        self._upd_swarm(dt)
        self._upd_inflight(dt)
        self._upd_ebullets(dt)
        if HIT_BULLETS:
           self._col_pb_ebullet()
        self._handle_attacks(dt)
        self._col_pb_swarm()
        self._col_pb_inflight()
        self._col_eb_player()
        self._col_ia_player()
        self._upd_difficulty(dt)
        self._check_level_clear()
        if self.lvl_clear:
            self._tick_level_clear(dt)

    def _move_player(self, dt):
        if not self.player.spawned:
            return
        # In touch mode the ship is moved directly in touch_moved/touch_began.
        # touched_sx is kept as a reference so we can do a small lerp catch-up
        # for the edge-clamp (avoids the ship sitting off-screen if a drag goes
        # beyond the play area boundary).
        if self.use_touch and self.touched_sx is not None:
            dx = self.touched_sx - self.player.sx
            self.player.move(
                clamp(self.player.sx + clamp(dx, -360 * dt, 360 * dt), 20, SW - 20)
            )

        self.bullet_cd -= dt
        # fire_btn is a one-frame pulse set by touch_began; consume it here.
        if self.fire_btn:
            if self.bullet_cd <= 0 and len(self.player_bullets) < self.max_player_bullets:
                self._shoot_player()
                self.bullet_cd = 0.32
            self.fire_btn = False   # always clear after checking

        # Engine flicker: slightly pulse alpha
        a = 0.85 + 0.15 * abs(math.sin(self.flash_t * 9))
        self.player.sprite.alpha = a

    def _shoot_player(self):
        # Only fire if under the bullet cap
        if len(self.player_bullets) < self.max_player_bullets:
            self.player_bullets.append(
                PlayerBullet(self, self.player.sx, self.player.sy + 18)
            )

    def _upd_pbullets(self, dt):
        """Advance all active player bullets upward; remove those off-screen."""
        for b in self.player_bullets:
            b.sy += PLAYER_BULLET_SPEED  * dt
            b.move(b.sy)
        self.player_bullets = [b for b in self.player_bullets if b.sy <= SH + 10]

    def _upd_dying_player(self, dt):
        self.death_t -= dt
        if self.death_t <= 0:
            self.player.dying = False
            self.lives -= 1
            try:
                self.live_sprites.pop().remove_from_parent()
            except IndexError:
                pass  # List was already empty, nothing to do
            if self.lives <= 0:
                self._game_over()
            else:
                self.player.spawned = True
                self.player_bullets = []
                self.inflight = [ia for ia in self.inflight if not ia.dying]

    def _game_over(self):
        if self.score > self.hi_score:
            self.hi_score = self.score
        self.script = SCRIPT_GAMEOVER
        self.player.spawned = False
        self.gameover_t = 5.0

    def _upd_gameover(self, dt):
        self._upd_swarm(dt)
        self.gameover_t -= dt
        if self.gameover_t <= 0:
            self.script = SCRIPT_ATTRACT
            self._reset_level()

    # -----------swarm movement ─────────────
    def _move_swarm(self, dt):
        self.swarm_dx += self.swarm_dir * 30 * dt
        # Reverse at edges
        if abs(self.swarm_dx) > 40:
            self.swarm_dir *= -1

        for a in self.swarm:
            base_x = SWARM_LEFT + a.col * CELL_W
            base_y = SWARM_BASE_Y + a.row * CELL_H
            a.move(base_x + self.swarm_dx, base_y)
            # Animation toggle
            if int(self.t * 2) % 2 == 0:
                a.toggle_texture()

    def _upd_swarm(self, dt):
        if self.player_bullets and self.halt_t <= 0:
            # Halt swarm if any bullet is in a column with live aliens
            for pb in self.player_bullets:
                col = int((pb.sx - SWARM_LEFT - self.swarm_dx) / CELL_W)
                if 0 <= col < SWARM_COLS:
                    if any(a for a in self.swarm if a.alive and a.col == col):
                        self.halt_t = 0.12
                        break
        if self.halt_t > 0:
            self.halt_t -= dt
            for a in self.swarm:
                if a.alive:
                    a.anim_t += dt
                    if a.anim_t > 0.45:
                        a.anim_t = 0
                        a.frame ^= 1
                        a.toggle_texture()
            return
        self.swarm_dx += self.swarm_dir * self.swarm_spd * dt
        live = [a for a in self.swarm if a.alive]
        if live:
            mn = min(a.col for a in live)
            mx = max(a.col for a in live)
            left = SWARM_LEFT + mn * CELL_W + self.swarm_dx
            right = SWARM_LEFT + (mx + 1) * CELL_W + self.swarm_dx
            if self.swarm_dir == 1 and right > SW - 8:
                self.swarm_dir = -1
            if self.swarm_dir == -1 and left < 8:
                self.swarm_dir = 1
        for a in self.swarm:
            if a.alive:
                a.anim_t += dt
                if a.anim_t > 0.4:
                    a.anim_t = 0
                    a.frame ^= 1
                    a.toggle_texture()
                sx, sy = a.pos()
                a.move(sx, sy)

    # -----------attack orchestration ────────────
    def _handle_attacks(self, dt):
        if self.shock_flag:
            self.shock_t -= dt
            if self.shock_t <= 0:
                self.shock_flag = False
            return
        self.fs_atk_t -= dt
        if self.fs_atk_t <= 0:
            self.fs_atk_t = max(1.2, 4.0 - self.diff_base * 0.4) + rng.flt() * 1.8
            self._launch_flagship()
        self.atk_counter -= 1
        if self.atk_counter <= 0:
            self.atk_counter = (
                max(2, 10 - self.diff_base - self.diff_extra) + rng.next() % 4
            )
            self._launch_single()

    def _launch_single(self):
        max_inf = clamp((self.diff_base + self.diff_extra) // 2 + 1, 1, 4)
        if sum(1 for ia in self.inflight if ia.active and not ia.dying) >= max_inf:
            return
        live = [
            a for a in self.swarm if a.alive and a.kind in ("blue", "purple", "red")
        ]
        if not live:
            return
        from_right = (self.tick // 60) % 2 == 0
        live.sort(key=lambda a: a.col, reverse=from_right)
        self._launch(live[0], from_right)

    def _launch_flagship(self):
        fships = [a for a in self.swarm if a.alive and a.kind == "flagship"]
        if not fships:
            return
        if any(
            ia
            for ia in self.inflight
            if ia.kind == "flagship" and (ia.active or ia.dying)
        ):
            return
        from_right = bool(rng.next() & 1)
        ia = self._launch(fships[0], from_right)
        if not ia:
            return
        ia.escort_ct = 0
        for r in [a for a in self.swarm if a.alive and a.kind == "red"][:2]:
            self._launch(r, from_right)
            ia.escort_ct += 1

    def _launch(self, alien, from_right):
        sx, sy = alien.pos()
        ia = InflightAlien(alien, sx, sy, clockwise=from_right)
        ia.last_shoot_time = self.t + 1
        alien.alive = False
        self.inflight.append(ia)
        return ia

    # -----------inflight lifecycle ──────────────
    def _upd_inflight(self, dt):
        dead = []
        for ia in self.inflight:
            if ia.dying:
                ia.death_t -= dt
                if ia.death_t <= 0:
                    ia.active = False
                    dead.append(ia)
            elif ia.active:
                self._upd_alive_ia(ia, dt)
            else:
                dead.append(ia)
        for ia in dead:
            self.inflight.remove(ia)

        for ia in self.inflight:
            if ia.active:
                frame = int(abs(ia.anim_f) / 5.0) % 2 == 0
                if frame:
                    ia.alien.toggle_texture()
                ia.move(ia.sx, ia.sy)

    def _upd_alive_ia(self, ia, dt):
        s = ia.stage
        if s == SOL_PACKS_BAGS:
            self._sol_packs(ia)
        elif s == SOL_FLIES_ARC:
            self._sol_arc(ia, dt)
        elif s == SOL_READY_ATTACK:
            self._sol_ready(ia)
        elif s == SOL_ATTACKING:
            self._sol_attack(ia, dt)
        elif s == SOL_NEAR_BOTTOM:
            self._sol_near(ia, dt)
        elif s == SOL_PAST_PLAYER:
            self._sol_past(ia)
        elif s == SOL_RETURNING:
            self._sol_return(ia, dt)

    def _sol_packs(self, ia):
        sx, sy = ia.alien.pos()
        ia.sx = sx
        ia.sy = sy
        ia.arc_step = 0
        ia.anim_f = 8.0 if ia.clockwise else -8.0
        ia.pivot_sx = sx
        ia.pivot_dx = 0.0
        ia.stage = SOL_FLIES_ARC

    def _sol_arc(self, ia, dt):
        if ia.arc_step < len(ARC_TABLE):
            dsy, dsx_mag = ARC_TABLE[ia.arc_step]
            ia.sy -= dsy * ARC_SCALE
            ia.sx += dsx_mag * ARC_SCALE * (1 if ia.clockwise else -1)
            ia.arc_step += 1
            ia.anim_f = lerp(ia.anim_f, 0.0, 0.15)
            ia.flip_h = ia.clockwise
        else:
            ia.stage = SOL_READY_ATTACK
        if ia.sx < -25 or ia.sx > SW + 25:
            ia.sx = clamp(ia.sx, 15, SW - 15)
            ia.sy = float(SWARM_BASE_Y + 10)
            ia.stage = SOL_READY_ATTACK

    def _sol_ready(self, ia):
        diff = self.player.sx - ia.sx
        ia.pivot_dx = clamp(diff / 2.0, -90.0, 90.0)
        ia.pivot_sx = ia.sx
        ia.anim_f = 0.0
        ia.flip_h = False
        ia.stage = SOL_ATTACKING

    def _sol_attack(self, ia, dt):
        spd = DIVE_SPEED + self.diff_extra * 14
        ia.sy -= spd * dt
        ia.pivot_sx += (self.player.sx - ia.pivot_sx) * 0.55 * dt
        ia.sx = ia.pivot_sx + ia.pivot_dx * math.sin((SWARM_BASE_Y - ia.sy) * 0.026)
        ia.sx = clamp(ia.sx, -40, SW + 40)
        # face toward player: flip sprite if target is to right
        ia.flip_h = self.player.sx > ia.sx
        ia.anim_f = clamp((self.player.sx - ia.sx) / 20.0, -10.0, 10.0)
        if ia.sy < self.player.sy + 80:
            ia.stage = SOL_NEAR_BOTTOM
        self._try_shoot(ia)

    def _sol_near(self, ia, dt):
        ia.sy -= (160 + self.diff_extra * 20) * dt
        ia.sx += (self.player.sx - ia.sx) * 2.2 * dt
        if ia.sy < PLAYER_BASE_Y - 45:
            ia.stage = SOL_PAST_PLAYER

    def _sol_past(self, ia):
        ia.sy = float(SWARM_BASE_Y + 30 + rng.next() % 50)
        ia.sx = clamp(self.player.sx + (rng.flt() - 0.5) * 140, 20, SW - 20)
        ia.sortie += 1
        live_cnt = sum(1 for a in self.swarm if a.alive)
        ia.stage = (
            SOL_ATTACKING
            if (live_cnt <= 3 or not self.player.spawned)
            else SOL_RETURNING
        )

    def _sol_return(self, ia, dt):
        if ia.alien not in self.swarm:
            ia.active = False
            return
        tx, ty = ia.alien.pos()
        spd = RETURN_SPEED + self.diff_extra * 8
        dsx = tx - ia.sx
        dsy = ty - ia.sy
        ia.sx += clamp(dsx, -spd * dt, spd * dt)
        ia.sy += clamp(dsy, -spd * dt, spd * dt)
        ia.flip_h = False
        if abs(dsx) < 4 and abs(dsy) < 4:
            ia.alien.alive = True
            ia.active = False

    # -----------enemy shooting ─────────────
    
    def _try_shoot(self, ia, mode='time'):
        # 1. Status checks
        if self.shock_flag or not ia.active:
            return
            
        # 2. Hard limit on total bullets on screen
        if len([b for b in self.enemy_bullets if b.active]) >= 6:
            return
        if mode == 'time':
            # 3. Precise Time-Based Control
            # 'self.t' is the elapsed time in Pythonista's Scene
            if self.t - ia.last_shoot_time > ia.shoot_delay:
                logger.debug(f'{ia} shooting at time {self.t:.2f}')
                ia.last_shoot_time = self.t  # Reset the timer
                self._spawn_ebullet(ia)
        else:
            sy_int = int(SWARM_BASE_Y - ia.sy)
            if sy_int > 0 and sy_int % 55 < 2:  # reduce number of shoots
                logger.debug(f'{ia} {sy_int} shooting')
                self._spawn_ebullet(ia)
                
    def _spawn_ebullet(self, ia):
        dist = ia.sy - self.player.sy
        if dist <= 0:
            return
        ratio = clamp((self.player.sx - ia.sx) / max(1, abs(dist)), -1.2, 1.2)
        drift = ratio * 160 + (rng.flt() - 0.5) * 55
        self.enemy_bullets.append(EnemyBullet(self, ia.sx, ia.sy, drift))

    def _upd_ebullets(self, dt):
        spd = BULLET_SPEED + self.diff_extra * 12
        for b in self.enemy_bullets:
            if not b.active:
                continue
            b.sy -= spd * dt
            b.sx += b.dsx * dt
            if b.sy < -20 or b.sx < -25 or b.sx > SW + 25:
                b.active = False
            b.move(b.sx, b.sy)
        self.enemy_bullets = [b for b in self.enemy_bullets if b.active]

    # -----------collision ─────────────────
    def _col_pb_swarm(self):
        """Check all player bullets against the swarm."""
        hits = []  # (bullet, alien) pairs
        for pb in self.player_bullets:
            for a in self.swarm:
                if not a.alive:
                    continue
                ax, ay = a.pos()
                if abs(pb.sx - ax) < CELL_W // 2 + 3 and abs(pb.sy - ay) < CELL_H // 2 + 3:
                    hits.append((pb, a))
                    break  # one alien per bullet
        for pb, a in hits:
            a.alive = False
            if pb in self.player_bullets:
                self.player_bullets.remove(pb)
            self._add_score(ALIEN_POINTS.get(a.kind, 30))
            a.explode()

    def _col_pb_inflight(self):
        """Check all player bullets against inflight aliens."""
        hits = []  # (bullet, inflight_alien) pairs
        for pb in self.player_bullets:
            for ia in self.inflight:
                if not ia.active or ia.dying:
                    continue
                if abs(pb.sx - ia.sx) < 14 and abs(pb.sy - ia.sy) < 14:
                    hits.append((pb, ia))
                    break  # one inflight alien per bullet
        for pb, ia in hits:
            ia.dying = True
            ia.death_t = 0.55
            if pb in self.player_bullets:
                self.player_bullets.remove(pb)
            pts = (
                self._flagship_pts(ia)
                if ia.kind == "flagship"
                else ALIEN_POINTS.get(ia.kind, 30)
            )
            self._add_score(pts)
            ia.explode(duration=0.55)
            if ia.kind == "flagship":
                self.shock_flag = True
                self.shock_t = 3.0
                 
    def _col_pb_ebullet(self):
        """Player bullets can intercept incoming enemy bullets.
        Both bullets are consumed on contact; no points are awarded."""
        pb_hits = set()
        eb_hits = set()
        for i, pb in enumerate(self.player_bullets):
            for j, eb in enumerate(self.enemy_bullets):
                if not eb.active:
                    continue
                if abs(pb.sx - eb.sx) < 8 and abs(pb.sy - eb.sy) < 10:
                    pb_hits.add(i)
                    eb_hits.add(j)
                    break  # one enemy bullet per player bullet
        # Remove in reverse index order so indices stay valid
        for j in sorted(eb_hits, reverse=True):
            self.enemy_bullets[j].active = False
            self.enemy_bullets[j].explode()
        for i in sorted(pb_hits, reverse=True):
            del self.player_bullets[i]
            
    def _col_eb_player(self):
        if not self.player.spawned or self.player.dying:
            return
        for b in self.enemy_bullets:
            if not b.active:
                continue
            if abs(b.sx - self.player.sx) < 15 and abs(b.sy - self.player.sy) < 15:
                b.active = False
                self._hit_player()
                return

    def _col_ia_player(self):
        if not self.player.spawned or self.player.dying:
            return
        for ia in self.inflight:
            if not ia.active or ia.dying:
                continue
            if abs(ia.sx - self.player.sx) < 19 and abs(ia.sy - self.player.sy) < 19:
                ia.dying = True
                ia.death_t = 0.4
                self._hit_player()
                return

    def _hit_player(self):
        self.player.dying = True
        self.player.spawned = False
        self.death_t = 1.6
        self.player_bullets = []
        self.move_touch_id = None
        self.joystick_touch_id = None
        self.active_touches = {}
        self.touched_sx = None
        self.fire_btn = False
        self.player.explode(duration=1.6)

    # ----------- scoring ─────────────────
    def _flagship_pts(self, ia):
        n = ia.escort_ct
        if n >= 2:
            return ALIEN_POINTS["flagship_2esc"]
        if n == 1:
            return ALIEN_POINTS["flagship_1esc"]
        return ALIEN_POINTS["flagship_solo"]

    def _add_score(self, pts):
        self.score += pts
        if self.score > self.hi_score:
            self.hi_score = self.score
        if not self.bonus_given and self.score >= self.bonus_threshold:
            self.bonus_given = True
            self.lives = min(self.lives + 1, 5)
            self.msg_text = "BONUS SHIP!"
            self.msg_t = 1.8

    # ----------- difficulty ─────────────────
    def _upd_difficulty(self, dt):
        if self.tick % 3600 == 0:
            self.diff_extra = min(self.diff_extra + 1, 7)

    # ----------- level clear ─────────────────
    def _check_level_clear(self):
        if self.lvl_clear:
            return
        # Dying aliens are mid-explosion and about to be removed; they must
        # not block the level-clear check or the wave never ends.
        if any(ia for ia in self.inflight if ia.active and not ia.dying):
            return
        if any(b for b in self.enemy_bullets if b.active):
            return
        if any(a for a in self.swarm if a.alive):
            return

        self.lvl_clear = True
        self.lvl_clear_t = 2.8

    def _tick_level_clear(self, dt):
        self.lvl_clear_t -= dt
        if self.lvl_clear_t <= 0:
            self.level += 1
            self.diff_base = min(self.diff_base + 1, 7)
            self.swarm_spd += 3
            self._reset_level()

    # ----------- draw ─────────────────
    def draw(self):
        background(*C_BG)
        self._draw_stars()
        self._draw_hud()
        self._draw_msg()
        if self.script == SCRIPT_ATTRACT:
            self._draw_attract_overlay()
        if self.script == SCRIPT_GAMEOVER:
            self._draw_gameover()
        if self.lvl_clear:
            self._draw_level_clear()

    # ----------- stars ─────────────────
    def _draw_stars(self):
        for s in self.stars:
            fill(*s.color)
            #fill(s.bri, s.bri, s.bri * 0.8, s.bri)
            ellipse(s.sx - s.sz / 2, s.sy - s.sz / 2, s.sz, s.sz)

    # ----------- HUD ─────────────────
    def _draw_hud(self):
        fill(*C_WHITE)
        text("1UP", font_size=11, x=28, y=SH - 16, alignment=5)
        fill(*C_GREEN)
        text(str(self.score).zfill(6), font_size=13, x=28, y=SH - 30, alignment=5)
        fill(*C_WHITE)
        text("HI-SCORE", font_size=11, x=SW // 2, y=SH - 16, alignment=5)
        fill(*C_GOLD)
        text(
            str(self.hi_score).zfill(6), font_size=13, x=SW // 2, y=SH - 30, alignment=5
        )
        fill(*C_WHITE)
        text(f"LV {self.level}", font_size=11, x=SW - 26, y=SH - 16, alignment=5)

        fill(0.2, 0.2, 0.45)
        rect(0, SH - 40, SW, 1)
        rect(0, 34, SW, 1)

    # ----------- messages ───────────────
    def _draw_msg(self):
        if self.msg_t > 0:
            self.msg_t -= self.dt
            tint(*C_WHITE)
            fill(*C_WHITE, min(1.0, self.msg_t))
            text(self.msg_text, font_size=20, x=SW // 2, y=SH // 2, alignment=5)

    # ----------- attract overlay ──────────────
    def _draw_attract_overlay(self):
        tint(*C_GOLD)
        text("✦ GALAXIAN ✦", font_size=22, x=SW // 2, y=SH - 64, alignment=5)
        tint(*C_WHITE, 0.65)
        text("WE ARE THE GALAXIANS", font_size=12, x=SW // 2, y=SH - 84, alignment=5)
        y0 = SH - 30
        tint(*C_WHITE)
        text("- SCORE ADVANCE TABLE -", font_size=11, x=SW // 2, y=y0, alignment=5)
        rows = [
            ("flag_0", "CONVOY CHARGER", "800/300/150"),
            ("red_0", "RED ALIEN", "80 PTS"),
            ("purple_0", "PURPLE ALIEN", "60 PTS"),
            ("blue_0", "BLUE ALIEN", "30 PTS"),
        ]
        for i, (skey, lbl, pts) in enumerate(rows):
            ey = y0 - 26 - i * 40
            SpriteNode(self.textures[skey], position=(58, ey), parent=self)
            # label colour matches alien

            ck = skey.split("_")[0]
            clr = {
                "flag": C_GOLD,
                "red": C_RED,
                "purple": (0.8, 0.2, 1.0, 1.0),
                "blue": (0.2, 0.55, 1.0, 1.0),
            }.get(ck, C_WHITE)
            tint(*clr)
            text(lbl, font_size=11, x=96, y=ey + 4, alignment=9)
            tint(*C_WHITE, 0.75)
            text(pts, font_size=11, x=SW - 12, y=ey + 4, alignment=7)
        if self.blink_t % 1.0 < 0.55:
            tint(*C_WHITE)
            text("TAP TO START", font_size=18, x=SW // 2, y=74, alignment=5)

    # ----------- game over ─────────────────
    def _draw_gameover(self):
        fill(0, 0, 0, 0.5)
        rect(0, 0, SW, SH)
        tint(*C_RED)
        text("GAME  OVER", font_size=30, x=SW // 2, y=SH // 2 + 18, alignment=5)
        tint(*C_WHITE, 0.75)
        text(
            f"SCORE  {self.score}", font_size=17, x=SW // 2, y=SH // 2 - 18, alignment=5
        )
        if self.score >= self.hi_score and self.score > 0:
            tint(*C_GOLD)
            text("NEW HI-SCORE!", font_size=14, x=SW // 2, y=SH // 2 - 46, alignment=5)
        if self.blink_t % 1.0 < 0.6:
            tint(*C_WHITE, 0.55)
            text("TAP TO PLAY AGAIN", font_size=13, x=SW // 2, y=70, alignment=5)

    # ----------- level clear ─────────────────
    def _draw_level_clear(self):
        tint(*C_GREEN, 0.9)
        text("STAGE  CLEAR!", font_size=26, x=SW // 2, y=SH // 2 + 12, alignment=5)
        tint(*C_WHITE, 0.7)
        text(
            f"LEVEL  {self.level}", font_size=17, x=SW // 2, y=SH // 2 - 22, alignment=5
        )


if __name__ == "__main__":
    scene.run(GalaxianGame(), scene.PORTRAIT, show_fps=True)
