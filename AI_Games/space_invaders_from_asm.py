# space_invaders.py
# ─────────────────────────────────────────────────────────────────────────────
# Space Invaders for Pythonista (scene module)
#
# Architecture derived from the original Taito 8080 assembly (1978):
#   • 11×5 alien fleet with per-column firing (squiggly / plunger / rolling shots)
#   • UFO saucer on a countdown timer
#   • 4 shield bunkers with pixel-level erosion
#   • Three-life player with explode animation
#   • Score / Hi-Score / lives display
#   • Fleet speed increases as aliens are killed (original "speedup" table logic)
#
# Controls (touch):
#   Left half of screen  → move left
#   Right half of screen → move right
#   Tap centre band      → fire
#   (On-screen buttons are drawn for convenience)
# ─────────────────────────────────────────────────────────────────────────────
# removed lines in blocks
# move wave in hud
# added sounds 
# finish explosion in dead aliens

import scene
import sound
import random
import math
from scene import *

# ── Palette ──────────────────────────────────────────────────────────────────
BLACK   = Color(0, 0, 0, 1)
WHITE   = Color(1, 1, 1, 1)
GREEN   = Color(0.2, 1, 0.3, 1)
RED     = Color(1, 0.2, 0.2, 1)
CYAN    = Color(0.2, 0.9, 1, 1)
YELLOW  = Color(1, 0.95, 0.1, 1)
MAGENTA = Color(1, 0.2, 1, 1)
ORANGE  = Color(1, 0.55, 0.1, 1)

# ── Alien sprite bitmaps (11×8 pixels each, two animation frames) ─────────────
# Row 0 = top alien (squid), Row 1 = middle (crab), Row 2 = bottom (octopus)
# Each entry: list of two 8-row strings of 11 chars ('X' = on)
ALIEN_SPRITES = [
    # Squid  (top row, 30 pts)
    [
        ["   XXXXX   ",
         " XXXXXXXXX ",
         "XX  XXX  XX",
         "XXXXXXXXXXX",
         " X XXXXX X ",
         "  XX   XX  ",
         " X  X  X X ",
         "X  X   X  X"],
        ["   XXXXX   ",
         " XXXXXXXXX ",
         "XX  XXX  XX",
         "XXXXXXXXXXX",
         " X XXXXX X ",
         "  XX   XX  ",
         "X X     X X",
         " X       X "]
    ],
    # Crab  (middle rows, 20 pts)
    [
        [" X       X ",
         "  X     X  ",
         " XXXXXXXXX ",
         "XXX XX XXX ",
         "XXXXXXXXXXX",
         "X XXXXXXX X",
         "X X     X X",
         "  XX   XX  "],
        [" X       X ",
         "X X     X X",
         "X XXXXXXX X",
         "XXX XX XXX ",
         "XXXXXXXXXXX",
         " XXXXXXXXX ",
         " X       X ",
         "X         X"]
    ],
    # Octopus  (bottom rows, 10 pts)
    [
        ["  XXXXXXX  ",
         "XXXXXXXXXXX",
         "XX X X X XX",
         "XXXXXXXXXXX",
         " XXXXXXXXX ",
         "  X     X  ",
         " X X   X X ",
         "X   X X   X"],
        ["  XXXXXXX  ",
         "XXXXXXXXXXX",
         "XX X X X XX",
         "XXXXXXXXXXX",
         " XXXXXXXXX ",
         " XX     XX ",
         "X X X X X X",
         " X       X "]
    ],
]

ALIEN_COLORS = [CYAN, GREEN, YELLOW]   # squid / crab / octopus
ALIEN_SCORES = [30, 20, 10]
UFO_SCORE_TABLE = [100, 150, 100, 300, 100, 150, 100, 300,
                   100, 150, 200, 300, 200, 150, 100, 150, 200]

CELL_W  = 40 # spacing
CELL_H  = 32
COLS    = 11
ROWS    = 5

BULLET_SPEED    = 420   # px/s  (player bullet)
ALIEN_SHOT_SPEED= 200   # px/s
UFO_SPEED       = 110   # px/s

SHIELD_PIXEL    = 4     # size of one shield "pixel"
SHIELD_W_PX     = 22    # shield width in pixels
SHIELD_H_PX     = 16

GROUND_Y        = 60    # y coord of ground line
PLAYER_Y        = 80
PLAYER_SPEED    = 180

HUD_H           = 40


# ── Helper: render a bitmap sprite into a list of (x,y,color) rects ──────────
def bitmap_rects(rows, pixel_size, cx, cy, col):
    rects = []
    h = len(rows)
    w = len(rows[0])
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == 'X':
                x = cx - (w * pixel_size) / 2 + c * pixel_size
                y = cy - (h * pixel_size) / 2 + (h - 1 - r) * pixel_size
                rects.append((x, y, pixel_size, pixel_size, col))
    return rects


# ── Shield bitmap (classic bunker shape) ──────────────────────────────────────
# 22×16 grid; bottom 3 rows have notch cut out
def make_shield_pixels():
    pixels = []
    for r in range(SHIELD_H_PX):
        for c in range(SHIELD_W_PX):
            # top arch
            if r >= SHIELD_H_PX - 5:
                if c < 3 or c >= SHIELD_W_PX - 3:
                    continue
            # bottom notch (player cannon gap)
            if r < 4 and 7 <= c <= 14:
                continue
            pixels.append([c, r, True])  # [col, row, alive]
    return pixels


# ─────────────────────────────────────────────────────────────────────────────
class SpaceInvaders(scene.Scene):

    def setup(self):
        self.background_color = 'black'
        self.reset_game()

    # ── Game state initialisation ─────────────────────────────────────────────
    def reset_game(self):
        W, H = self.size
        self.score      = 0
        self.hi_score   = getattr(self, 'hi_score', 0)
        self.lives      = 3
        self.game_over  = False
        self.win        = False
        self.paused     = False
        self.wave       = getattr(self, 'wave', 1)
        self.sounds     = 1
        # Fleet
        self.aliens = []   # dict per alien
        fleet_x0 = W / 2 - (COLS * CELL_W) / 2
        fleet_y0 = H - HUD_H - CELL_H * 1.5 - (ROWS - 1) * CELL_H
        for row in range(ROWS):
            atype = 0 if row == 0 else (1 if row < 3 else 2)
            for col in range(COLS):
                self.aliens.append({
                    'row': row, 'col': col,
                    'x': fleet_x0 + col * CELL_W,
                    'y': fleet_y0 + (ROWS - 1 - row) * CELL_H,
                    'type': atype,
                    'alive': True,
                    'frame': 0,
                    'exploding': 0,
                })

        self.fleet_dx   = CELL_W * 0.6  # step size
        self.fleet_dir  = 1             # 1 = right, -1 = left
        self.fleet_move_timer  = 0
        self.fleet_move_period = self._fleet_period()
        

        # Player
        self.player_x   = W / 2
        self.player_dead_timer = 0
        self.player_alive = True

        # Bullets
        self.player_bullet = None   # {'x','y','active'}
        self.alien_bullets = []     # list of {'x','y','type','frame','timer'}

        # UFO saucer
        self.ufo_active = False
        self.ufo_x      = 0
        self.ufo_dir    = 1
        self.ufo_timer  = self._ufo_period()
        self.ufo_score_idx = 0
        self.ufo_flash  = 0

        # Shields (4 bunkers)
        self.shields = []
        gap = W / 5
        for i in range(4):
            cx = gap * (i + 1)
            self.shields.append({'cx': cx, 'cy': GROUND_Y + 65,
                                 'pixels': make_shield_pixels()})

        # Touch state
        self.touch_left  = False
        self.touch_right = False
        self.touch_fire  = False
        self._fire_held  = False

        # Alien shot timer
        self.alien_shot_timer = 0
        self.alien_shot_period = 1.1

        # Score popup
        self.score_popups = []  # {'x','y','text','timer'}

        # Level start flash
        self.start_flash = 1.5

    def _fleet_period(self):
        alive = sum(1 for a in self.aliens if a['alive']) if hasattr(self, 'aliens') else COLS * ROWS
        # Original: speed table based on number alive (55 → 1, faster as fewer remain)
        t = max(0.04, 0.05 + alive * 0.013)
        return t / max(1, self.wave * 0.15 + 0.85)

    def _ufo_period(self):
        return random.uniform(15, 28)

    # ── Main update loop ──────────────────────────────────────────────────────
    def update(self):
        if self.game_over or self.win:
            return
        if self.start_flash > 0:
            self.start_flash -= self.dt
            return

        W, H = self.size
        dt = self.dt

        self._update_player(dt, W)
        self._update_player_bullet(dt, H)
        self._update_alien_shots(dt, H)
        self._update_fleet(dt, W, H)
        self._update_ufo(dt, W)
        self._update_collisions(W)
        self._tick_popups(dt)

        # Win condition
        if all(not a['alive'] for a in self.aliens):
            self.win = True
            self.wave += 1

        # Lose condition – fleet reached ground
        for a in self.aliens:
            if a['alive'] and a['y'] < GROUND_Y + 30:
                self.game_over = True

    # ── Player movement & fire ────────────────────────────────────────────────
    def _update_player(self, dt, W):
        if not self.player_alive:
            self.player_dead_timer -= dt
            if self.player_dead_timer <= 0:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                else:
                    self.player_alive = True
            return

        if self.touch_left:
            self.player_x = max(20, self.player_x - PLAYER_SPEED * dt)
        if self.touch_right:
            self.player_x = min(W - 20, self.player_x + PLAYER_SPEED * dt)

        if self.touch_fire and not self._fire_held:
            self._fire_held = True
            if self.player_bullet is None:
                self.player_bullet = {'x': self.player_x, 'y': PLAYER_Y + 18, 'active': True}
                if self.sounds:
                    sound.play_effect('digital:HighDown')
        if not self.touch_fire:
            self._fire_held = False

    # ── Player bullet ─────────────────────────────────────────────────────────
    def _update_player_bullet(self, dt, H):
        if self.player_bullet is None:
            return
        b = self.player_bullet
        b['y'] += BULLET_SPEED * dt
        if b['y'] > H:
            self.player_bullet = None

    # ── Alien shots ───────────────────────────────────────────────────────────
    def _update_alien_shots(self, dt, H):
        # Move existing
        for s in self.alien_bullets:
            s['y'] -= ALIEN_SHOT_SPEED * dt
            s['timer'] -= dt
            if s['timer'] <= 0:
                s['timer'] = 0.12
                s['frame'] = (s['frame'] + 1) % 4

        self.alien_bullets = [s for s in self.alien_bullets if s['y'] > GROUND_Y - 10]

        # Spawn new shot
        self.alien_shot_timer -= dt
        if self.alien_shot_timer <= 0:
            self.alien_shot_timer = self.alien_shot_period * random.uniform(0.7, 1.3)
            alive = [a for a in self.aliens if a['alive']]
            if alive:
                shooter = random.choice(alive)
                stype = random.randint(0, 2)
                self.alien_bullets.append({
                    'x': shooter['x'] + CELL_W / 2,
                    'y': shooter['y'],
                    'type': stype,
                    'frame': 0,
                    'timer': 0.12,
                })

    # ── Fleet marching ────────────────────────────────────────────────────────
    def _update_fleet(self, dt, W, H):
        self.fleet_move_timer -= dt
        if self.fleet_move_timer > 0:
            return
        if self.sounds:
            # play bump sound
            sound.play_effect('rpg:Footstep05', volume=0.5)
            
        self.fleet_move_period = self._fleet_period()
        self.fleet_move_timer = self.fleet_move_period

        alive = [a for a in self.aliens if a['alive']]
        
        # finish explosion in dead aliens
        dead = [a for a in self.aliens if not a['alive']]
        for a in dead:
            a['exploding'] = 0
            
        # Advance animation frame
        for a in alive:
            a['frame'] ^= 1
            if a['exploding'] > 0:
                a['exploding'] -= self.fleet_move_period

        # Check wall collision
        xs = [a['x'] for a in alive]
        if not xs:
            return
        min_x, max_x = min(xs), max(xs)

        if self.fleet_dir == 1 and max_x + CELL_W > W - 10:
            self.fleet_dir = -1
            for a in self.aliens:
                a['y'] -= CELL_H * 0.5
        elif self.fleet_dir == -1 and min_x < 10:
            self.fleet_dir = 1
            for a in self.aliens:
                a['y'] -= CELL_H * 0.5
        else:
            for a in self.aliens:
                a['x'] += self.fleet_dir * self.fleet_dx

    # ── UFO saucer ────────────────────────────────────────────────────────────
    def _update_ufo(self, dt, W):
        if self.ufo_active:
            self.ufo_x += self.ufo_dir * UFO_SPEED * dt
            if self.ufo_flash > 0:
                self.ufo_flash -= dt
            if self.ufo_x < -40 or self.ufo_x > W + 40:
                self.ufo_active = False
                self.ufo_timer = self._ufo_period()
        else:
            self.ufo_timer -= dt
            if self.ufo_timer <= 0:
                self.ufo_active = True
                self.ufo_dir = random.choice([-1, 1])
                self.ufo_x = -30 if self.ufo_dir == 1 else W + 30
                self.ufo_flash = 0

    # ── Collision detection ───────────────────────────────────────────────────
    def _update_collisions(self, W):
        pb = self.player_bullet

        # Player bullet vs aliens
        if pb:
            for a in self.aliens:
                if not a['alive']:
                    continue
                if (abs(pb['x'] - (a['x'] + CELL_W / 2)) < CELL_W * 0.45 and
                        abs(pb['y'] - a['y']) < CELL_H * 0.55):
                    a['alive'] = False
                    if self.sounds:
                        sound.play_effect('arcade:Explosion_5')
                    a['exploding'] = 0.4
                    pts = ALIEN_SCORES[a['type']]
                    self.score += pts
                    self.hi_score = max(self.hi_score, self.score)
                    self.score_popups.append({'x': a['x'], 'y': a['y'],
                                              'text': str(pts), 'timer': 0.7})
                    self.player_bullet = None
                    break

        # Player bullet vs UFO
        if pb and self.ufo_active and self.ufo_flash <= 0:
            if abs(pb['y'] - (self.size[1] - HUD_H - 20)) < 20 and abs(pb['x'] - self.ufo_x) < 30:
                pts = UFO_SCORE_TABLE[self.ufo_score_idx % len(UFO_SCORE_TABLE)]
                self.ufo_score_idx += 1
                self.score += pts
                self.hi_score = max(self.hi_score, self.score)
                self.score_popups.append({'x': self.ufo_x, 'y': self.size[1] - HUD_H - 20,
                                          'text': str(pts), 'timer': 1.0})
                self.ufo_flash = 1.0
                self.ufo_active = False
                self.ufo_timer = self._ufo_period()
                self.player_bullet = None

        # Player bullet vs shields
        if pb:
            for sh in self.shields:
                hit = self._bullet_vs_shield(pb['x'], pb['y'], sh, going_up=True)
                if hit:
                    self.player_bullet = None
                    break

        # Alien shots vs player
        if self.player_alive:
            for s in self.alien_bullets:
                if abs(s['x'] - self.player_x) < 16 and abs(s['y'] - PLAYER_Y) < 14:
                    self.player_alive = False
                    if self.sounds:
                        sound.play_effect('arcade:Explosion_4')
                    self.player_dead_timer = 1.5
                    self.alien_bullets.remove(s)
                    break

        # Alien shots vs shields
        for s in self.alien_bullets[:]:
            for sh in self.shields:
                if self._bullet_vs_shield(s['x'], s['y'], sh, going_up=False):
                    self.alien_bullets.remove(s)
                    break

    def _bullet_vs_shield(self, bx, by, sh, going_up):
        """Returns True if bullet hits shield and erodes a pixel."""
        ox = bx - sh['cx']
        oy = by - sh['cy']
        col = int((ox + (SHIELD_W_PX * SHIELD_PIXEL) / 2) / SHIELD_PIXEL)
        row = int((oy + (SHIELD_H_PX * SHIELD_PIXEL) / 2) / SHIELD_PIXEL)
        if col < 0 or col >= SHIELD_W_PX or row < 0 or row >= SHIELD_H_PX:
            return False
        for px in sh['pixels']:
            if px[0] == col and px[1] == row and px[2]:
                px[2] = False
                # Erode neighbours
                for px2 in sh['pixels']:
                    if abs(px2[0] - col) <= 1 and abs(px2[1] - row) <= 1 and random.random() < 0.4:
                        px2[2] = False
                return True
        return False

    def _tick_popups(self, dt):
        self.score_popups = [p for p in self.score_popups
                             if (p.__setitem__('timer', p['timer'] - dt) or True) and p['timer'] > 0]

    # ── Touch handling ────────────────────────────────────────────────────────
    def touch_began(self, touch):
        self._handle_touch(touch)

    def touch_moved(self, touch):
        self._handle_touch(touch)

    def touch_ended(self, touch):
        W, H = self.size
        self.touch_left  = False
        self.touch_right = False
        self.touch_fire  = False

        if self.game_over or self.win:
            self.game_over = False
            self.win = False
            if self.lives <= 0 or self.game_over:
                self.lives = 3
                self.wave = 1
                self.score = 0
            self.reset_game()

    def _handle_touch(self, touch):
        W, H = self.size
        x, y = touch.location
        btn_y  = 35
        btn_h  = 50
        L_cx   = W * 0.18
        R_cx   = W * 0.5
        F_cx   = W * 0.82
        btn_w  = W * 0.25

        self.touch_left  = abs(x - L_cx) < btn_w / 2 and abs(y - btn_y) < btn_h / 2
        self.touch_right = abs(x - R_cx) < btn_w / 2 and abs(y - btn_y) < btn_h / 2
        self.touch_fire  = abs(x - F_cx) < btn_w / 2 and abs(y - btn_y) < btn_h / 2

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw(self):
        W, H = self.size
        background('black')

        self._draw_hud(W, H)
        self._draw_ground(W)
        self._draw_shields()
        self._draw_aliens()
        self._draw_ufo(H)
        self._draw_player(W)
        self._draw_bullets()
        self._draw_popups()
        self._draw_buttons(W)

        if self.start_flash > 0:
            self._draw_centered_text("GET READY!", H / 2, GREEN, 36)

        if self.game_over:
            self._draw_centered_text("GAME OVER", H / 2 + 20, RED, 42)
            self._draw_centered_text("Tap to restart", H / 2 - 30, WHITE, 22)

        if self.win:
            self._draw_centered_text("WAVE CLEARED!", H / 2 + 20, YELLOW, 38)
            self._draw_centered_text("Tap to continue", H / 2 - 30, WHITE, 22)

    def _draw_hud(self, W, H):
        # Score
        fill(*WHITE)
        text(f"SCORE  {self.score:05d}", 'Courier', 18, 10, H - 22, alignment=9)
        text(f"HI  {self.hi_score:05d}", 'Courier', 18, W / 2, H - 22, alignment=5)
        # Lives
        for i in range(self.lives):
            self._draw_player_icon(W - 90 + i * 26, H - 22)
        # Wave
        text(f"WAVE {self.wave}", 'Courier', 16, W - 100, H - 22, alignment=3)

    def _draw_ground(self, W):
        fill(*GREEN)
        rect(0, GROUND_Y, W, 2)

    def _draw_shields(self):
        for sh in self.shields:
            cx, cy = sh['cx'], sh['cy']
            fill(*GREEN)
            
            for px in sh['pixels']:
                if px[2]:
                    x = cx - (SHIELD_W_PX * SHIELD_PIXEL) / 2 + px[0] * SHIELD_PIXEL
                    y = cy - (SHIELD_H_PX * SHIELD_PIXEL) / 2 + px[1] * SHIELD_PIXEL
                    rect(x, y, SHIELD_PIXEL - 0, SHIELD_PIXEL - 0)

    def _draw_aliens(self):
        ps = 3  # pixel size for alien sprites
        for a in self.aliens:
            if a['exploding'] > 0:
                # Draw explosion cross
                fill(*WHITE)
                ex, ey = a['x'] + CELL_W / 2, a['y']
                for dx, dy in [(-8,0),(8,0),(0,-8),(0,8),(-5,-5),(5,-5),(-5,5),(5,5)]:
                    rect(ex + dx - 2, ey + dy - 2, 4, 4)                                
                continue
            if not a['alive']:
                continue
            sprite_rows = ALIEN_SPRITES[a['type']][a['frame']]
            col = ALIEN_COLORS[a['type']]
            fill(*col)            
            cx = a['x'] + CELL_W / 2
            cy = a['y']
            for r, row in enumerate(sprite_rows):
                for c, ch in enumerate(row):
                    if ch == 'X':
                        px = cx - (11 * ps) / 2 + c * ps
                        py = cy - (8 * ps) / 2 + (7 - r) * ps
                        rect(px, py, ps - 0.0, ps - 0.0) # was 0.5

    def _draw_ufo(self, H):
        if not self.ufo_active:
            return
        if self.ufo_flash > 0:
            if int(self.ufo_flash * 8) % 2 == 0:
                return
        uy = H - HUD_H - 20
        fill(*MAGENTA)
        # Saucer body
        rect(self.ufo_x - 22, uy - 5, 44, 10)
        rect(self.ufo_x - 14, uy + 4, 28, 8)
        rect(self.ufo_x - 6, uy + 11, 12, 6)
        # Lights
        fill(*RED)
        for dx in [-14, -7, 0, 7, 14]:
            rect(self.ufo_x + dx - 2, uy - 2, 4, 4)

    def _draw_player(self, W):
        if not self.player_alive:
            if int(self.player_dead_timer * 6) % 2 == 0:
                self._draw_explosion(self.player_x, PLAYER_Y)
            return
        fill(*GREEN)
        # Cannon base
        rect(self.player_x - 18, PLAYER_Y - 8, 36, 8)
        rect(self.player_x - 12, PLAYER_Y, 24, 8)
        rect(self.player_x - 3, PLAYER_Y + 8, 6, 8)

    def _draw_player_icon(self, x, y):
        fill(*GREEN)
        rect(x - 9, y - 4, 18, 4)
        rect(x - 6, y, 12, 4)
        rect(x - 1.5, y + 4, 3, 4)

    def _draw_explosion(self, x, y):
        
        fill(*ORANGE)
        for i in range(8):
            angle = i * math.pi / 4
            r = 12
            ex = x + r * math.cos(angle)
            ey = y + r * math.sin(angle)
            rect(ex - 3, ey - 3, 6, 6)
        fill(*YELLOW)
        rect(x - 4, y - 4, 8, 8)

    def _draw_bullets(self):
        # Player bullet
        if self.player_bullet:
            fill(*WHITE)
            rect(self.player_bullet['x'] - 1.5, self.player_bullet['y'], 3, 10)

        # Alien shots (three types: squiggly, plunger, rolling)
        for s in self.alien_bullets:
            fill(*RED)
            t = s['type']
            f = s['frame']
            x, y = s['x'], s['y']
            if t == 0:  # squiggly
                offsets = [(-3,0),(3,4),(-3,8),(3,12)]
                for ox, oy in offsets:
                    rect(x + ox - 1, y + oy, 3, 4)
            elif t == 1:  # plunger
                rect(x - 2, y, 4, 12)
                rect(x - 4, y + f * 3, 8, 2)
            else:  # rolling
                rect(x - 3, y, 6, 3)
                rect(x - 1, y + 3, 2, 6)
                rect(x - 3, y + 9, 6, 3)

    def _draw_popups(self):
        for p in self.score_popups:
            alpha = min(1.0, p['timer'] * 2)
            fill(1, 1, 0, alpha)
            text(p['text'], 'Courier', 16, p['x'], p['y'], alignment=5)

    def _draw_buttons(self, W):
        # Transparent on-screen control buttons
        fill(0.3, 0.3, 0.3, 0.4)
        btn_y  = 10
        btn_h  = 50
        btn_w  = W * 0.25
        L_cx   = W * 0.18
        R_cx   = W * 0.5
        F_cx   = W * 0.82
        for cx, label in [(L_cx, "◀"), (R_cx, "▶"), (F_cx, "FIRE")]:
            rect(cx - btn_w / 2, btn_y, btn_w, btn_h)
        fill(*WHITE)
        for cx, label in [(L_cx, "◀"), (R_cx, "▶"), (F_cx, "FIRE")]:
            text(label, 'Courier', 18, cx, btn_y + btn_h / 2, alignment=5)

    def _draw_centered_text(self, msg, y, col, size):
        W, H = self.size
        fill(*col)
        text(msg, 'Courier', size, W / 2, y, alignment=5)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    run(SpaceInvaders(), PORTRAIT, show_fps=True)
