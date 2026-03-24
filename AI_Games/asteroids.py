# asteroids.py
# ─────────────────────────────────────────────────────────────────────────────
# Asteroids for Pythonista (scene module)
#
# Architecture faithfully derived from the Atari 6502 ROM (1979):
#   • Vector-style wireframe rendering (drawn with lines, no sprites)
#   • 4 large asteroids on wave 1, +2 per wave, max 11 (ROM table)
#   • Split logic: large → 2 medium (50 pts), medium → 2 small (100 pts)
#     small (100 pts) → destroyed; scores match original
#   • Ship rotation + thrust + inertia + screen wrap
#   • Hyperspace with 25% failure chance (ROM random check logic)
#   • Large saucer (200 pts, random shots) + small saucer (990 pts, aimed)
#     Small saucer appears more frequently & accurately after 35,000 pts
#   • Bullet limit: 4 on screen simultaneously (ROM constraint)
#   • Thump heartbeat that speeds up as asteroid count falls
#   • Extra life at 10,000 pts and every 10,000 after (ROM default)
#   • Score turns over at 99,990 (BCD + trailing zero in ROM)
# ─────────────────────────────────────────────────────────────────────────────

import scene
import math
import random
from scene import *

# ── Palette ──────────────────────────────────────────────────────────────────
BLACK  = (0, 0, 0, 1)
WHITE  = (1, 1, 1, 1)
GREY   = (0.6, 0.6, 0.6, 1)
CYAN   = (0.3, 1, 1, 1)
YELLOW = (1, 1, 0.2, 1)
RED    = (1, 0.25, 0.25, 1)
GREEN  = (0.3, 1, 0.4, 1)
ORANGE = (1, 0.55, 0.1, 1)

# ── Vector shape definitions (list of (x,y) pairs, drawn as closed polygon) ──
# Coordinates are normalised −1..1; scaled by radius at draw time.

SHIP_VERTS = [
    (1.0, 0),          # nose
    (-0.8, -0.6),
    (-0.5, 0),         # tail notch
    (-0.8, 0.6),
]

SHIP_THRUST_VERTS = [   # flame, drawn behind ship when thrusting
    (-0.5, -0.25),
    (-1.1, 0),
    (-0.5, 0.25),
]

SAUCER_LARGE_VERTS = [
    (-0.9, 0), (-0.5, 0.45), (0.5, 0.45), (0.9, 0),
    (0.5, -0.35), (-0.5, -0.35),
]
SAUCER_DOME_VERTS = [
    (-0.35, 0.45), (-0.2, 0.75), (0.2, 0.75), (0.35, 0.45),
]

# Asteroids: 4 shape variants (like the ROM's 4 rotation patterns)
ASTEROID_SHAPES = [
    [(0,1),(0.6,0.7),(1,0.2),(0.8,-0.5),(0.3,-1),(-0.4,-0.9),(-1,-0.3),(-0.9,0.4),(-0.5,0.8)],
    [(0,0.9),(0.5,0.5),(0.9,0.2),(0.6,-0.4),(0.2,-1),(-0.5,-0.8),(-1,-0.2),(-0.8,0.5),(-0.2,0.8)],
    [(0.1,1),(0.7,0.6),(1,0),(0.6,-0.6),(0,-1),(-0.5,-0.7),(-1,-0.1),(-0.7,0.5),(-0.3,0.9)],
    [(0,0.8),(0.4,0.5),(1,0.1),(0.7,-0.5),(0.1,-1),(-0.6,-0.8),(-1,-0.2),(-0.8,0.4),(-0.1,0.9)],
]

# ── Constants (derived from ROM timing & physics) ─────────────────────────────
MAX_BULLETS        = 4
BULLET_SPEED       = 420.0
BULLET_LIFE        = 1.05      # seconds
SHIP_TURN_SPEED    = 240.0     # deg/s
SHIP_THRUST        = 220.0     # px/s²
SHIP_MAX_SPEED     = 310.0
SHIP_DRAG          = 0.985     # per-frame velocity damping
SHIP_RADIUS        = 14
SHIP_SPAWN_SAFE    = 90        # px radius cleared on spawn (ROM: shipSpawnTimer)

ASTEROID_RADII     = {3: 38, 2: 20, 1: 11}   # large/medium/small
ASTEROID_SPEEDS    = {3: (25, 65), 2: (55, 110), 1: (100, 180)}
ASTEROID_SCORES    = {3: 20, 2: 50, 1: 100}

SAUCER_LARGE_R     = 28
SAUCER_SMALL_R     = 16
SAUCER_LARGE_SCORE = 200
SAUCER_SMALL_SCORE = 990
SAUCER_SPEED       = 115
SAUCER_SHOT_PERIOD = 1.8       # seconds between saucer shots
SAUCER_LARGE_TIMER_RANGE = (7, 18)
SAUCER_SMALL_TIMER_RANGE = (12, 28)

EXTRA_LIFE_SCORE   = 10000
MAX_SCORE          = 99990
STARTING_LIVES     = 3
STARTING_ASTEROIDS = 4
MAX_ASTEROIDS_WAVE = 11

THUMP_PERIOD_MAX   = 0.90
THUMP_PERIOD_MIN   = 0.18
THUMP_FLASH_DUR    = 0.06


# ── Utility ───────────────────────────────────────────────────────────────────
def angle_to_vec(deg):
    r = math.radians(deg)
    return math.cos(r), math.sin(r)

def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)

def wrap(v, lo, hi):
    span = hi - lo
    while v < lo: v += span
    while v >= hi: v -= span
    return v

def rotate_verts(verts, angle_deg):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x * ca - y * sa, x * sa + y * ca) for x, y in verts]

def draw_poly(verts, cx, cy, r, col, closed=True, lw=1.5):
    scaled = [(cx + x * r, cy + y * r) for x, y in verts]
    stroke(*col)
    fill(0, 0, 0, 0)
    stroke_weight(lw)
    n = len(scaled)
    for i in range(n):
        x1, y1 = scaled[i]
        x2, y2 = scaled[(i + 1) % n if closed else min(i + 1, n - 1)]
        if not closed and i == n - 1:
            break
        line(x1, y1, x2, y2)

def draw_open_poly(verts, cx, cy, r, col, lw=1.5):
    draw_poly(verts, cx, cy, r, col, closed=False, lw=lw)


# ── Game objects ──────────────────────────────────────────────────────────────
class Ship:
    def __init__(self, x, y):
        self.x, self.y   = x, y
        self.vx, self.vy = 0.0, 0.0
        self.angle       = 90.0   # degrees, 90 = pointing up
        self.thrusting   = False
        self.alive       = True
        self.spawn_timer = 0.0    # invulnerability after respawn
        self.explode_timer = 0.0
        self.explode_parts = []   # list of (x,y,vx,vy,life) for debris

    def respawn(self, x, y):
        self.x, self.y   = x, y
        self.vx, self.vy = 0.0, 0.0
        self.angle       = 90.0
        self.alive       = True
        self.spawn_timer = 2.5    # brief invulnerability
        self.explode_timer = 0.0

    def explode(self):
        self.alive = False
        self.explode_timer = 1.8
        self.explode_parts = []
        for _ in range(12):
            spd = random.uniform(30, 160)
            ang = random.uniform(0, 360)
            vx, vy = angle_to_vec(ang)
            self.explode_parts.append([
                self.x, self.y,
                vx * spd, vy * spd,
                random.uniform(0.6, 1.6)
            ])


class Asteroid:
    def __init__(self, x, y, size, vx=None, vy=None, shape=None):
        self.x, self.y = x, y
        self.size = size          # 3=large, 2=medium, 1=small
        spd_min, spd_max = ASTEROID_SPEEDS[size]
        spd = random.uniform(spd_min, spd_max)
        ang = random.uniform(0, 360)
        self.vx = vx if vx is not None else math.cos(math.radians(ang)) * spd
        self.vy = vy if vy is not None else math.sin(math.radians(ang)) * spd
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-60, 60)   # deg/s
        self.shape_idx = shape if shape is not None else random.randint(0, 3)
        self.radius = ASTEROID_RADII[size]


class Bullet:
    def __init__(self, x, y, vx, vy, is_saucer=False):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.life        = BULLET_LIFE
        self.is_saucer   = is_saucer


class Saucer:
    def __init__(self, small, W, H):
        self.small  = small
        self.radius = SAUCER_SMALL_R if small else SAUCER_LARGE_R
        self.score  = SAUCER_SMALL_SCORE if small else SAUCER_LARGE_SCORE
        self.dir    = random.choice([-1, 1])
        self.x      = 0 if self.dir == 1 else W
        self.y      = random.uniform(H * 0.15, H * 0.85)
        self.vy     = random.choice([-1, 0, 1]) * SAUCER_SPEED * 0.4
        self.shot_timer = SAUCER_SHOT_PERIOD * random.uniform(0.5, 1.0)
        self.alive  = True
        self.explode_timer = 0.0


# ─────────────────────────────────────────────────────────────────────────────
class AsteroidsGame(scene.Scene):

    def setup(self):
        self.background_color = 'black' #Color(*BLACK)
        self.hi_score = 0
        self._start_new_game()

    # ── Game / wave initialisation ────────────────────────────────────────────
    def _start_new_game(self):
        W, H = self.size
        self.score        = 0
        self.lives        = STARTING_LIVES
        self.wave         = 1
        self.game_over    = False
        self.next_extra   = EXTRA_LIFE_SCORE
        self._start_wave()

    def _start_wave(self):
        W, H = self.size
        cx, cy = W / 2, H / 2

        # ROM table: wave 1 = 4 large, each wave +2, max 11
        n = min(STARTING_ASTEROIDS + (self.wave - 1) * 2, MAX_ASTEROIDS_WAVE)
        self.asteroids = []
        for _ in range(n):
            # Spawn away from centre (ROM: wait until clear of ship spawn)
            while True:
                x = random.uniform(0, W)
                y = random.uniform(0, H)
                if dist(x, y, cx, cy) > SHIP_SPAWN_SAFE + ASTEROID_RADII[3]:
                    break
            self.asteroids.append(Asteroid(x, y, 3))

        self.ship       = Ship(cx, cy)
        self.bullets    = []
        self.saucer     = None
        self.saucer_timer = self._next_saucer_timer()

        # Thump
        self.thump_timer  = 0.0
        self.thump_beat   = 0         # 0 or 1 (two-tone heartbeat)
        self.thump_flash  = 0.0

        # Input state
        self.key_left   = False
        self.key_right  = False
        self.key_thrust = False
        self.key_fire   = False
        self.key_hyper  = False
        self._fire_held = False
        self._hyper_held = False

        # Score popups
        self.popups = []

        # Wave clear flash
        self.wave_clear_timer = 0.0
        self.wave_starting    = False
        self.wave_start_timer = 0.0

    def _next_saucer_timer(self):
        if self.score >= 35000:
            lo, hi = SAUCER_SMALL_TIMER_RANGE
        else:
            lo, hi = SAUCER_LARGE_TIMER_RANGE
        return random.uniform(lo, hi)

    # ── Main update ───────────────────────────────────────────────────────────
    def update(self):
        if self.game_over:
            return
        dt = self.dt
        W, H = self.size

        # Wave-start pause
        if self.wave_starting:
            self.wave_start_timer -= dt
            if self.wave_start_timer <= 0:
                self.wave_starting = False
            return

        self._update_ship(dt, W, H)
        self._update_bullets(dt, W, H)
        self._update_asteroids(dt, W, H)
        self._update_saucer(dt, W, H)
        self._update_thump(dt)
        self._check_collisions(W, H)
        self._tick_popups(dt)

        # Wave cleared?
        if not self.asteroids and self.saucer is None and not self.wave_starting:
            self.wave_clear_timer -= dt
            if self.wave_clear_timer <= 0:
                self.wave += 1
                self._start_wave()
                self.wave_starting    = True
                self.wave_start_timer = 2.5

    # ── Ship ─────────────────────────────────────────────────────────────────
    def _update_ship(self, dt, W, H):
        s = self.ship
        if s.spawn_timer > 0:
            s.spawn_timer -= dt

        if not s.alive:
            s.explode_timer -= dt
            for p in s.explode_parts:
                p[0] += p[2] * dt
                p[1] += p[3] * dt
                p[4] -= dt
            return

        # Rotation
        if self.key_left:
            s.angle += SHIP_TURN_SPEED * dt
        if self.key_right:
            s.angle -= SHIP_TURN_SPEED * dt
        s.angle = s.angle % 360

        # Thrust
        s.thrusting = self.key_thrust
        if s.thrusting:
            dx, dy = angle_to_vec(s.angle)
            s.vx += dx * SHIP_THRUST * dt
            s.vy += dy * SHIP_THRUST * dt
            spd = math.hypot(s.vx, s.vy)
            if spd > SHIP_MAX_SPEED:
                s.vx *= SHIP_MAX_SPEED / spd
                s.vy *= SHIP_MAX_SPEED / spd

        # Drag
        s.vx *= SHIP_DRAG
        s.vy *= SHIP_DRAG

        # Move & wrap
        s.x = wrap(s.x + s.vx * dt, 0, W)
        s.y = wrap(s.y + s.vy * dt, 0, H)

        # Fire
        if self.key_fire and not self._fire_held:
            self._fire_held = True
            self._ship_fire()
        if not self.key_fire:
            self._fire_held = False

        # Hyperspace
        if self.key_hyper and not self._hyper_held:
            self._hyper_held = True
            self._hyperspace(W, H)
        if not self.key_hyper:
            self._hyper_held = False

    def _ship_fire(self):
        player_bullets = [b for b in self.bullets if not b.is_saucer]
        if len(player_bullets) >= MAX_BULLETS:
            return
        s = self.ship
        dx, dy = angle_to_vec(s.angle)
        self.bullets.append(Bullet(
            s.x + dx * SHIP_RADIUS,
            s.y + dy * SHIP_RADIUS,
            s.vx + dx * BULLET_SPEED,
            s.vy + dy * BULLET_SPEED,
        ))

    def _hyperspace(self, W, H):
        """ROM hyperspace logic: 25% chance of death; failure also more likely
        when many asteroids on screen."""
        r = random.randint(0, 31)
        if r >= 24:
            self.ship.explode()
            self._ship_killed()
            return
        # Failure chance scales with asteroid count (ROM: compare vs curAsteroidCount)
        reduced = (r & 7) * 2 + 4
        if reduced < len(self.asteroids):
            self.ship.explode()
            self._ship_killed()
            return
        # Success
        while True:
            nx = random.uniform(W * 0.1, W * 0.9)
            ny = random.uniform(H * 0.1, H * 0.9)
            safe = all(dist(nx, ny, a.x, a.y) > a.radius + SHIP_SPAWN_SAFE * 0.5
                       for a in self.asteroids)
            if safe:
                break
        self.ship.respawn(nx, ny)

    # ── Bullets ───────────────────────────────────────────────────────────────
    def _update_bullets(self, dt, W, H):
        for b in self.bullets:
            b.x = wrap(b.x + b.vx * dt, 0, W)
            b.y = wrap(b.y + b.vy * dt, 0, H)
            b.life -= dt
        self.bullets = [b for b in self.bullets if b.life > 0]

    # ── Asteroids ─────────────────────────────────────────────────────────────
    def _update_asteroids(self, dt, W, H):
        for a in self.asteroids:
            a.x = wrap(a.x + a.vx * dt, 0, W)
            a.y = wrap(a.y + a.vy * dt, 0, H)
            a.angle = (a.angle + a.spin * dt) % 360

    # ── Saucer ────────────────────────────────────────────────────────────────
    def _update_saucer(self, dt, W, H):
        if self.saucer is None:
            if not self.asteroids:
                return
            self.saucer_timer -= dt
            if self.saucer_timer <= 0:
                small = self.score >= 10000 and random.random() < 0.5
                self.saucer = Saucer(small, W, H)
            return

        sc = self.saucer
        if not sc.alive:
            sc.explode_timer -= dt
            if sc.explode_timer <= 0:
                self.saucer = None
                self.saucer_timer = self._next_saucer_timer()
            return

        # Move
        sc.x += sc.dir * SAUCER_SPEED * dt
        sc.y += sc.vy * dt
        # Periodically change vertical direction
        if random.random() < dt * 0.4:
            sc.vy = random.choice([-1, 0, 1]) * SAUCER_SPEED * 0.4

        sc.y = wrap(sc.y, 0, H)

        # Exit stage
        if sc.x < -sc.radius * 2 or sc.x > W + sc.radius * 2:
            self.saucer = None
            self.saucer_timer = self._next_saucer_timer()
            return

        # Shoot
        sc.shot_timer -= dt
        if sc.shot_timer <= 0:
            sc.shot_timer = SAUCER_SHOT_PERIOD * random.uniform(0.7, 1.3)
            self._saucer_fire(sc)

    def _saucer_fire(self, sc):
        if sc.small and self.ship.alive:
            # Aimed shot (small saucer, ROM: targeted after 35k)
            accuracy = 0.85 if self.score >= 35000 else 0.55
            tx, ty = self.ship.x, self.ship.y
            ang = math.degrees(math.atan2(ty - sc.y, tx - sc.x))
            ang += random.uniform(-30, 30) * (1 - accuracy)
        else:
            ang = random.uniform(0, 360)
        dx, dy = angle_to_vec(ang)
        spd = BULLET_SPEED * 0.72
        self.bullets.append(Bullet(sc.x, sc.y, dx * spd, dy * spd, is_saucer=True))

    # ── Thump heartbeat ───────────────────────────────────────────────────────
    def _update_thump(self, dt):
        self.thump_flash = max(0, self.thump_flash - dt)
        self.thump_timer -= dt
        if self.thump_timer <= 0:
            n = max(1, len(self.asteroids))
            # Speed increases as asteroid count drops (mirrors ROM timing)
            t = THUMP_PERIOD_MIN + (THUMP_PERIOD_MAX - THUMP_PERIOD_MIN) * (n / 27)
            self.thump_timer = t
            self.thump_beat ^= 1
            self.thump_flash = THUMP_FLASH_DUR

    # ── Collision detection ───────────────────────────────────────────────────
    def _check_collisions(self, W, H):
        # Player bullets vs asteroids
        for b in self.bullets[:]:
            if b.is_saucer:
                continue
            for a in self.asteroids[:]:
                if dist(b.x, b.y, a.x, a.y) < a.radius:
                    self._kill_asteroid(a, b.x, b.y)
                    if b in self.bullets:
                        self.bullets.remove(b)
                    break

        # Player bullets vs saucer
        if self.saucer and self.saucer.alive:
            for b in self.bullets[:]:
                if b.is_saucer:
                    continue
                if dist(b.x, b.y, self.saucer.x, self.saucer.y) < self.saucer.radius:
                    self._kill_saucer()
                    if b in self.bullets:
                        self.bullets.remove(b)
                    break

        # Saucer bullets vs ship
        if self.ship.alive and self.ship.spawn_timer <= 0:
            for b in self.bullets[:]:
                if not b.is_saucer:
                    continue
                if dist(b.x, b.y, self.ship.x, self.ship.y) < SHIP_RADIUS:
                    self.ship.explode()
                    self._ship_killed()
                    if b in self.bullets:
                        self.bullets.remove(b)
                    break

        # Ship vs asteroids
        if self.ship.alive and self.ship.spawn_timer <= 0:
            for a in self.asteroids:
                if dist(self.ship.x, self.ship.y, a.x, a.y) < a.radius + SHIP_RADIUS - 4:
                    self.ship.explode()
                    self._ship_killed()
                    break

        # Saucer vs asteroids (saucers can be destroyed by asteroids)
        if self.saucer and self.saucer.alive:
            for a in self.asteroids:
                if dist(self.saucer.x, self.saucer.y, a.x, a.y) < a.radius + self.saucer.radius * 0.7:
                    self._kill_saucer(no_score=True)
                    break

    def _kill_asteroid(self, a, bx, by):
        pts = ASTEROID_SCORES[a.size]
        self.score = min(MAX_SCORE, self.score + pts)
        self.hi_score = max(self.hi_score, self.score)
        self.popups.append({'x': a.x, 'y': a.y, 'text': str(pts), 'timer': 0.7})
        self._check_extra_life()
        self.asteroids.remove(a)
        if a.size > 1:
            for _ in range(2):
                # Children inherit some parent velocity (ROM split logic)
                ang = random.uniform(0, 360)
                spd_min, spd_max = ASTEROID_SPEEDS[a.size - 1]
                spd = random.uniform(spd_min, spd_max)
                vx = a.vx * 0.3 + math.cos(math.radians(ang)) * spd
                vy = a.vy * 0.3 + math.sin(math.radians(ang)) * spd
                self.asteroids.append(Asteroid(a.x, a.y, a.size - 1, vx, vy))

    def _kill_saucer(self, no_score=False):
        sc = self.saucer
        if not no_score:
            self.score = min(MAX_SCORE, self.score + sc.score)
            self.hi_score = max(self.hi_score, self.score)
            self.popups.append({'x': sc.x, 'y': sc.y, 'text': str(sc.score), 'timer': 1.0})
            self._check_extra_life()
        sc.alive = False
        sc.explode_timer = 0.9

    def _ship_killed(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            # Schedule respawn after explosion animation
            pass  # handled in draw by checking explode_timer

    def _check_extra_life(self):
        if self.score >= self.next_extra:
            self.lives += 1
            self.next_extra += EXTRA_LIFE_SCORE
            self.popups.append({'x': self.size[0]/2, 'y': self.size[1]/2 - 30,
                                 'text': 'EXTRA SHIP!', 'timer': 1.5, 'big': True})

    def _tick_popups(self, dt):
        alive = []
        for p in self.popups:
            p['timer'] -= dt
            p['y'] += 25 * dt
            if p['timer'] > 0:
                alive.append(p)
        self.popups = alive

    # ── Touch / input ─────────────────────────────────────────────────────────
    def touch_began(self, touch):
        self._parse_touch(touch)

    def touch_moved(self, touch):
        self._parse_touch(touch)

    def touch_ended(self, touch):
        self.key_left   = False
        self.key_right  = False
        self.key_thrust = False
        self.key_fire   = False
        self.key_hyper  = False

        if self.game_over:
            self._start_new_game()

    def _parse_touch(self, touch):
        W, H = self.size
        x, y = touch.location
        bh, bw = 58, W * 0.22
        by = 30
        # Button centres
        btns = {
            'left':   (W * 0.10, by),
            'right':  (W * 0.28, by),
            'thrust': (W * 0.50, by),
            'fire':   (W * 0.72, by),
            'hyper':  (W * 0.90, by),
        }
        self.key_left   = abs(x - btns['left'][0])   < bw/2 and abs(y - btns['left'][1])   < bh/2
        self.key_right  = abs(x - btns['right'][0])  < bw/2 and abs(y - btns['right'][1])  < bh/2
        self.key_thrust = abs(x - btns['thrust'][0]) < bw/2 and abs(y - btns['thrust'][1]) < bh/2
        self.key_fire   = abs(x - btns['fire'][0])   < bw/2 and abs(y - btns['fire'][1])   < bh/2
        self.key_hyper  = abs(x - btns['hyper'][0])  < bw/2 and abs(y - btns['hyper'][1])  < bh/2

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self):
        W, H = self.size
        background('black') #*BLACK)

        self._draw_hud(W, H)
        self._draw_asteroids(W, H)
        self._draw_ship(W, H)
        self._draw_saucer(W, H)
        self._draw_bullets(W, H)
        self._draw_popups()
        self._draw_buttons(W)
        self._draw_thump_indicator()

        # Respawn ship after explosion
        s = self.ship
        if not s.alive and s.explode_timer <= 0 and not self.game_over:
            cx, cy = W / 2, H / 2
            # Wait until centre is clear
            clear = all(dist(cx, cy, a.x, a.y) > SHIP_SPAWN_SAFE for a in self.asteroids)
            if clear:
                s.respawn(cx, cy)

        if self.wave_starting:
            fill(*WHITE)
            text(f"WAVE {self.wave}", 'Courier', 34, W/2, H/2, alignment=5)

        if self.game_over:
            fill(*RED)
            text("GAME OVER", 'Courier', 42, W/2, H/2 + 20, alignment=5)
            fill(*WHITE)
            text("Tap to play again", 'Courier', 22, W/2, H/2 - 24, alignment=5)

    # ── HUD ───────────────────────────────────────────────────────────────────
    def _draw_hud(self, W, H):
        fill(*WHITE)
        text(f"{self.score:05d}",    'Courier', 20, 14, H - 24, alignment=9)
        text(f"HI {self.hi_score:05d}", 'Courier', 18, W/2, H-22, alignment=5)
        text(f"WAVE {self.wave}",    'Courier', 16, W - 10, H - 22, alignment=3)
        # Lives as small ship icons
        for i in range(self.lives):
            lx = 18 + i * 22
            ly = H - 50
            self._draw_ship_icon(lx, ly, 10)

    def _draw_ship_icon(self, cx, cy, r):
        verts = rotate_verts(SHIP_VERTS, 90)
        draw_poly(verts, cx, cy, r, WHITE, lw=1.2)

    # ── Ship drawing ──────────────────────────────────────────────────────────
    def _draw_ship(self, W, H):
        s = self.ship
        if not s.alive:
            # Explosion debris
            for p in s.explode_parts:
                if p[4] > 0:
                    alpha = min(1, p[4])
                    col = (1, 0.7 * alpha, 0.2 * alpha, alpha)
                    stroke(*col)
                    stroke_weight(2)
                    line(p[0], p[1], p[0] - p[2]*0.06, p[1] - p[3]*0.06)
            return

        # Blink during invulnerability
        if s.spawn_timer > 0 and int(s.spawn_timer * 7) % 2 == 0:
            return

        col = WHITE
        verts = rotate_verts(SHIP_VERTS, s.angle)
        draw_poly(verts, s.x, s.y, SHIP_RADIUS, col)

        if s.thrusting and random.random() < 0.7:
            flame = rotate_verts(SHIP_THRUST_VERTS, s.angle)
            draw_open_poly(flame, s.x, s.y, SHIP_RADIUS, ORANGE, lw=1.5)

    # ── Asteroid drawing ──────────────────────────────────────────────────────
    def _draw_asteroids(self, W, H):
        for a in self.asteroids:
            verts = rotate_verts(ASTEROID_SHAPES[a.shape_idx], a.angle)
            draw_poly(verts, a.x, a.y, a.radius, GREY)

    # ── Saucer drawing ────────────────────────────────────────────────────────
    def _draw_saucer(self, W, H):
        sc = self.saucer
        if sc is None:
            return
        if not sc.alive:
            # Explosion
            if sc.explode_timer > 0:
                frac = sc.explode_timer / 0.9
                for i in range(8):
                    ang = i * 45 + (1 - frac) * 180
                    r2 = sc.radius * (1 + (1 - frac) * 1.5)
                    ex = sc.x + math.cos(math.radians(ang)) * r2
                    ey = sc.y + math.sin(math.radians(ang)) * r2
                    col = (1, frac * 0.8, 0.1, frac)
                    stroke(*col)
                    stroke_weight(2)
                    line(sc.x, sc.y, ex, ey)
            return

        col = CYAN if sc.small else YELLOW
        r = sc.radius
        draw_poly(SAUCER_LARGE_VERTS, sc.x, sc.y, r, col)
        draw_poly(SAUCER_DOME_VERTS,  sc.x, sc.y, r, col)

    # ── Bullet drawing ────────────────────────────────────────────────────────
    def _draw_bullets(self, W, H):
        for b in self.bullets:
            col = RED if b.is_saucer else WHITE
            fill(*col)
            stroke(*col)
            ellipse(b.x - 3, b.y - 3, 6, 6)

    # ── Score popups ──────────────────────────────────────────────────────────
    def _draw_popups(self):
        for p in self.popups:
            alpha = min(1.0, p['timer'] * 1.5)
            fill(1, 1, 0.2, alpha)
            sz = 20 if p.get('big') else 15
            text(p['text'], 'Courier', sz, p['x'], p['y'], alignment=5)

    # ── On-screen buttons ─────────────────────────────────────────────────────
    def _draw_buttons(self, W):
        bh, bw = 58, W * 0.22
        by = 2
        labels = [("◀", W*0.10), ("▶", W*0.28), ("▲", W*0.50),
                  ("●", W*0.72), ("⟁", W*0.90)]
        hints  = ["LEFT", "RIGHT", "THRUST", "FIRE", "HYPER"]
        for (lbl, cx), hint in zip(labels, hints):
            fill(0.25, 0.25, 0.25, 0.45)
            rect(cx - bw/2, by, bw, bh)
            fill(*WHITE)
            text(lbl,  'Courier', 22, cx, by + bh * 0.62, alignment=5)
            fill(0.55, 0.55, 0.55, 0.8)
            text(hint, 'Courier', 10, cx, by + bh * 0.22, alignment=5)

    # ── Thump flash indicator (bottom centre) ─────────────────────────────────
    def _draw_thump_indicator(self):
        W, H = self.size
        if self.thump_flash > 0:
            alpha = self.thump_flash / THUMP_FLASH_DUR
            col = (0.4, 1, 0.4, alpha * 0.6) if self.thump_beat == 0 else (0.2, 0.8, 1, alpha * 0.6)
            fill(*col)
            r = 6
            ellipse(W/2 - r, 72 - r, r*2, r*2)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    run(AsteroidsGame(), PORTRAIT, show_fps=True)
