# ============================================================
#  DEFENDER  –  Pythonista/scene port
#  Based on the mechanics of the original 1981 Williams arcade
#  game (Motorola 6809 assembly, Eugene Jarvis & Sam Dicker).
#
#  Controls (touch):
#    Left  half of screen  → thrust left / fire (tap)
#    Right half of screen  → thrust right / fire (tap)
#    Two-finger tap        → Smart Bomb
#    Three-finger tap      → Hyperspace
#    Drag up / down        → vertical movement
#
#  Keyboard (simulator):
#    A / D   – thrust left / right
#    W / S   – up / down
#    SPACE   – fire
#    B       – smart bomb
#    H       – hyperspace
# ============================================================
# CMT changes Mar 2026
# fixed line drawing, colour setting, line_width
# Color() parameters
# changed dist2 to accept objects with wx, wy attibutes
# fixed retrace line in terrain by blocking sx < 0
# removed vertical terrain lines
# rename self.touches to self.multi_touches sunce it clashes with scene.py

import scene
import sound
import random
import math

# ── palette (Williams CRT feel) ──────────────────────────────
BLACK   = scene.Color(0.00, 0.00, 0.00, 1)
GREEN   = scene.Color(0.00, 1.00, 0.20, 1)
YELLOW  = scene.Color(1.00, 0.95, 0.00, 1)
RED     = scene.Color(1.00, 0.15, 0.10, 1)
CYAN    = scene.Color(0.00, 0.95, 1.00, 1)
ORANGE  = scene.Color(1.00, 0.55, 0.00, 1)
WHITE   = scene.Color(1.00, 1.00, 1.00, 1)
PURPLE  = scene.Color(0.75, 0.10, 1.00, 1)
GREY    = scene.Color(0.45, 0.45, 0.45, 1)
DKGREEN = scene.Color(0.00, 0.40, 0.10, 1)

# ── world constants ──────────────────────────────────────────
WORLD_W      = 3200          # total horizontal world width (pixels)
TERRAIN_SEGS = 64            # landscape segments
NUM_HUMANOIDS = 10
MAX_BULLETS  = 12
MAX_ENEMY_BULLETS = 20
BULLET_SPEED = 700
PLAYER_ACCEL = 900
PLAYER_MAX_SPEED_X = 420
PLAYER_MAX_SPEED_Y = 320
GRAVITY      = 0             # weightless ship
LANDER_SPEED = 55
MUTANT_SPEED = 130
BAITER_SPEED = 200
SWARMER_SPEED = 160
BOMBER_SPEED  = 45

# radar strip dimensions (fraction of screen height)
RADAR_H_FRAC = 0.12

# ── helpers ──────────────────────────────────────────────────
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def dist2(a, b):
    # a and b are objects with wx, wy attributes    
    return (a.wx - b.wx)**2 + (a.wy - b.wy)**2

def norm(dx, dy):
    l = math.hypot(dx, dy)
    return (dx/l, dy/l) if l else (0, 0)

# ── terrain generation (matches original: pixelwide surface) ─
def build_terrain(world_w, seg_count, screen_h, base_frac=0.22):
    seg_w = world_w / seg_count
    base  = screen_h * base_frac
    pts   = [base]
    for _ in range(seg_count):
        pts.append(clamp(pts[-1] + random.uniform(-30, 30), base*0.4, base*1.8))
    xs = [i * seg_w for i in range(seg_count+1)]
    return xs, pts          # parallel lists of world-x, world-y heights

def terrain_y_at(world_x, xs, pts):
    world_x = world_x % xs[-1]
    for i in range(len(xs)-1):
        if xs[i] <= world_x <= xs[i+1]:
            t = (world_x - xs[i]) / (xs[i+1] - xs[i])
            return pts[i]*(1-t) + pts[i+1]*t
    return pts[0]

# ============================================================
#  Entity classes
# ============================================================

class Entity:
    def __init__(self, wx, wy):
        self.wx  = float(wx)   # world x
        self.wy  = float(wy)   # world y (screen-space y)
        self.vx  = 0.0
        self.vy  = 0.0
        self.alive = True
        self.node  = None      # scene node

    def world_pos(self):
        return scene.Point(self.wx, self.wy)


class Player(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.facing    = 1       # +1 right, -1 left
        self.lives     = 3
        self.score     = 0
        self.smart_bombs = 3
        self.carrying  = None    # humanoid being rescued
        self.invincible = 0.0    # seconds remaining
        self.hyperspace_cooldown = 0.0

    def is_dead(self): return self.lives <= 0


class Bullet(Entity):
    def __init__(self, wx, wy, vx):
        super().__init__(wx, wy)
        self.vx = vx
        self.lifetime = 0.8

    def update(self, dt):
        self.wx += self.vx * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False


class EnemyBullet(Entity):
    def __init__(self, wx, wy, tx, ty):
        super().__init__(wx, wy)
        dx, dy = norm(tx-wx, ty-wy)
        spd = 160
        self.vx = dx * spd
        self.vy = dy * spd
        self.lifetime = 2.5

    def update(self, dt):
        self.wx += self.vx * dt
        self.wy += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False


class Humanoid(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.captured_by = None
        self.falling     = False
        self.fall_vy     = 0.0
        self.on_ground   = True
        self.walk_timer  = random.uniform(0, 3)

    def update(self, dt, terrain_xs, terrain_pts):
        if self.captured_by:
            return
        if self.falling:
            self.fall_vy -= 220 * dt
            self.wy += self.fall_vy * dt
            gnd = terrain_y_at(self.wx, terrain_xs, terrain_pts) + 10
            if self.wy <= gnd:
                self.wy = gnd
                self.falling  = False
                self.fall_vy  = 0
                self.on_ground = True
        else:
            # gentle random walk along surface
            self.walk_timer -= dt
            if self.walk_timer <= 0:
                self.vx = random.choice([-20, 0, 20])
                self.walk_timer = random.uniform(1, 3)
            self.wx += self.vx * dt
            self.wx %= WORLD_W
            gnd = terrain_y_at(self.wx, terrain_xs, terrain_pts) + 10
            self.wy = gnd


class Lander(Entity):
    IDLE    = 'idle'
    DIVING  = 'diving'
    LIFTING = 'lifting'

    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.state   = self.IDLE
        self.target  = None        # humanoid
        self.shoot_timer = random.uniform(1, 3)
        self.drift_timer = random.uniform(0.5, 2)
        self.vx = random.uniform(-30, 30)

    def update(self, dt, humanoids, screen_h, terrain_xs, terrain_pts, player, enemy_bullets):
        if self.state == self.IDLE:
            # drift, occasionally pick a humanoid target
            self.drift_timer -= dt
            self.wx += self.vx * dt
            self.wx %= WORLD_W
            if self.drift_timer <= 0:
                self.vx = random.uniform(-40, 40)
                self.drift_timer = random.uniform(1, 3)
                # pick nearest unguarded humanoid
                candidates = [h for h in humanoids if h.alive and h.on_ground and h.captured_by is None]
                if candidates:
                    self.target = min(candidates, key=lambda h: dist2(self, h))
                    self.state  = self.DIVING

        elif self.state == self.DIVING:
            if not self.target or not self.target.alive or not self.target.on_ground:
                self.state  = self.IDLE
                self.target = None
                return
            dx = self.target.wx - self.wx
            # wrap
            if abs(dx) > WORLD_W/2:
                dx -= math.copysign(WORLD_W, dx)
            dy = self.target.wy - self.wy
            d  = math.hypot(dx, dy)
            if d < 8:
                # grab!
                self.target.captured_by = self
                self.target.on_ground   = False
                self.state = self.LIFTING
            else:
                spd = LANDER_SPEED
                self.wx += (dx/d) * spd * dt
                self.wy += (dy/d) * spd * dt
                self.wx %= WORLD_W

        elif self.state == self.LIFTING:
            if not self.target or not self.target.alive:
                self.state  = self.IDLE
                self.target = None
                return
            self.wy += LANDER_SPEED * dt
            self.target.wx = self.wx
            self.target.wy = self.wy
            if self.wy >= screen_h * 0.88:
                # reached top → humanoid becomes mutant (handled in game)
                return   # signal stays as LIFTING so game can detect it

        # shooting
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(1.5, 4)
            if player and player.alive:
                enemy_bullets.append(EnemyBullet(self.wx, self.wy, player.wx, player.wy))


class Mutant(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.shoot_timer = random.uniform(0.5, 2)
        self.erratic_timer = 0.3

    def update(self, dt, player, enemy_bullets):
        if not player:
            return
        dx = player.wx - self.wx
        if abs(dx) > WORLD_W/2:
            dx -= math.copysign(WORLD_W, dx)
        dy = player.wy - self.wy
        # deliberate offset: avoid lining up (original behaviour)
        dy += math.sin(self.wx * 0.01) * 18
        nx, ny = norm(dx, dy)
        self.wx += nx * MUTANT_SPEED * dt
        self.wy += ny * MUTANT_SPEED * dt
        self.wx %= WORLD_W
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(0.8, 2.5)
            enemy_bullets.append(EnemyBullet(self.wx, self.wy, player.wx, player.wy))


class Bomber(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.vx = random.choice([-1, 1]) * BOMBER_SPEED
        self.mine_timer = random.uniform(1, 2.5)

    def update(self, dt, mines):
        self.wx += self.vx * dt
        self.wx %= WORLD_W
        self.mine_timer -= dt
        if self.mine_timer <= 0:
            self.mine_timer = random.uniform(1.5, 3)
            mines.append(Mine(self.wx, self.wy))


class Mine(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.lifetime = 6.0

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False


class Pod(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-10, 10)

    def update(self, dt):
        self.wx += self.vx * dt
        self.wy += self.vy * dt
        self.wx %= WORLD_W

    def burst(self, swarmers):
        for _ in range(random.randint(3, 6)):
            swarmers.append(Swarmer(self.wx + random.uniform(-20,20),
                                    self.wy + random.uniform(-20,20)))


class Swarmer(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)
        self.angle = random.uniform(0, math.tau)
        self.shoot_timer = random.uniform(1, 3)

    def update(self, dt, player, enemy_bullets):
        if not player:
            return
        dx = player.wx - self.wx
        if abs(dx) > WORLD_W/2:
            dx -= math.copysign(WORLD_W, dx)
        dy = player.wy - self.wy
        nx, ny = norm(dx, dy)
        # zigzag evasion
        self.angle += dt * 4
        nx += math.cos(self.angle) * 0.4
        ny += math.sin(self.angle) * 0.4
        self.wx += nx * SWARMER_SPEED * dt
        self.wy += ny * SWARMER_SPEED * dt
        self.wx %= WORLD_W
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(1, 3)
            enemy_bullets.append(EnemyBullet(self.wx, self.wy, player.wx, player.wy))


class Baiter(Entity):
    def __init__(self, wx, wy):
        super().__init__(wx, wy)

    def update(self, dt, player, enemy_bullets):
        if not player:
            return
        dx = player.wx - self.wx
        if abs(dx) > WORLD_W/2:
            dx -= math.copysign(WORLD_W, dx)
        dy = player.wy - self.wy
        nx, ny = norm(dx, dy)
        self.wx += nx * BAITER_SPEED * dt
        self.wy += ny * BAITER_SPEED * dt
        self.wx %= WORLD_W


# ============================================================
#  Drawing helpers (pure scene.draw_* calls, no SpriteNodes)
# ============================================================

def screen_x(wx, camera_wx, screen_w):
    """World x → screen x, wrapping."""
    sx = (wx - camera_wx) % WORLD_W
    if sx > WORLD_W / 2:
        sx -= WORLD_W
    return sx

def draw_ship(sx, sy, facing, flash):
    """Defender-style ship: simple angular polygon."""
    c = WHITE if not flash else RED
    scene.stroke(*c)
    scene.stroke_weight(2)
    # fuselage
    # changed facing to face correct way
    if facing < 0:
        pts = [(sx-16,sy), (sx+16,sy+4), (sx+16,sy-4)]
        # engine flare
        scene.line(sx-16,sy+3, sx-22,sy)
        scene.line(sx-16,sy-3, sx-22,sy)
        # cockpit
        scene.line(sx-2,sy+4, sx+8,sy+8)
    else:
        pts = [(sx+16,sy), (sx-16,sy+4), (sx-16,sy-4)]
        scene.line(sx+16,sy+3, sx+22,sy)
        scene.line(sx+16,sy-3, sx+22,sy)
        scene.line(sx+2,sy+4, sx-8,sy+8)
    # draw triangle outline
    for i in range(len(pts)):
        a, b = pts[i], pts[(i+1)%len(pts)]
        scene.line(a[0],a[1],b[0],b[1])

def draw_lander(sx, sy):
    # classic lander shape: box body + 3 legs
    scene.stroke(*CYAN)
    scene.stroke_weight(2)
    scene.line(sx-8,sy+6, sx+8,sy+6)
    scene.line(sx-8,sy-2, sx+8,sy-2)
    scene.line(sx-8,sy+6, sx-8,sy-2)
    scene.line(sx+8,sy+6, sx+8,sy-2)
    # legs
    scene.line(sx-8,sy-2, sx-12,sy-8)
    scene.line(sx,  sy-2, sx,   sy-8)
    scene.line(sx+8,sy-2, sx+12,sy-8)
    # dome
    scene.line(sx-4,sy+6, sx,sy+10)
    scene.line(sx+4,sy+6, sx,sy+10)

def draw_mutant(sx, sy):
    # spiky, agitated shape
    spikes = 6
    scene.stroke(*RED)
    scene.stroke_weight(2)
    for i in range(spikes):
        a0 = i     * math.tau/spikes
        a1 = (i+0.5) * math.tau/spikes
        x0 = sx + math.cos(a0)*8
        y0 = sy + math.sin(a0)*8
        x1 = sx + math.cos(a1)*14
        y1 = sy + math.sin(a1)*14
        x2 = sx + math.cos(a0+math.tau/spikes)*8
        y2 = sy + math.sin(a0+math.tau/spikes)*8
        
        scene.line(x0,y0,x1,y1)
        scene.line(x1,y1,x2,y2)

def draw_bomber(sx, sy):
    scene.stroke(*ORANGE)
    scene.stroke_weight(2)
    scene.line(sx-10,sy, sx+10,sy)
    scene.line(sx,sy-6, sx,sy+6)
    scene.line(sx-7,sy-7, sx+7,sy+7)
    scene.line(sx-7,sy+7, sx+7,sy-7)

def draw_pod(sx, sy):
    r = 10
    sides = 6
    scene.stroke(*PURPLE)
    scene.stroke_weight(2)
    for i in range(sides):
        a0 = i*math.tau/sides
        a1 = (i+1)*math.tau/sides
        scene.line(sx+math.cos(a0)*r, sy+math.sin(a0)*r,
                        sx+math.cos(a1)*r, sy+math.sin(a1)*r)

def draw_swarmer(sx, sy):
    scene.stroke(*YELLOW)
    scene.stroke_weight(2)
    scene.line(sx-5,sy-5, sx+5,sy-5)
    scene.line(sx+5,sy-5, sx+5,sy+5)
    scene.line(sx+5,sy+5, sx-5,sy+5)
    scene.line(sx-5,sy+5, sx-5,sy-5)

def draw_baiter(sx, sy):
    scene.stroke(*GREEN)
    scene.stroke_weight(2)
    scene.line(sx-12,sy, sx+12,sy)
    scene.line(sx-6,sy-5, sx+6,sy-5)
    scene.line(sx-6,sy+5, sx+6,sy+5)
    scene.line(sx-12,sy, sx-6,sy-5)
    scene.line(sx-12,sy, sx-6,sy+5)
    scene.line(sx+12,sy, sx+6,sy-5)
    scene.line(sx+12,sy, sx+6,sy+5)

def draw_humanoid(sx, sy, captured=False):
    col = YELLOW if not captured else ORANGE
    scene.stroke(*col)
    scene.stroke_weight(2)
    # stick figure
    scene.line(sx,sy+10, sx,sy+2)   # body
    scene.line(sx,sy+10, sx,sy+14)   # head stub
    scene.line(sx-5,sy+6, sx+5,sy+6) # arms
    scene.line(sx,sy+2, sx-4,sy-4)   # left leg
    scene.line(sx,sy+2, sx+4,sy-4)   # right leg

def draw_mine(sx, sy):
    scene.stroke(*ORANGE)
    scene.stroke_weight(2)
    scene.line(sx-4,sy, sx+4,sy)
    scene.line(sx,sy-4, sx,sy+4)


# ============================================================
#  Main Scene
# ============================================================

class DefenderGame(scene.Scene):

    # ── setup ────────────────────────────────────────────────
    def setup(self):
        self.state = 'attract'   # 'attract' | 'playing' | 'gameover'
        self._init_game()

    def _init_game(self):
        w, h = self.size
        self.screen_w = w
        self.screen_h = h
        self.radar_h  = h * RADAR_H_FRAC

        # terrain
        self.terrain_xs, self.terrain_pts = build_terrain(WORLD_W, TERRAIN_SEGS, h)

        # player
        mid_h = h * 0.5
        self.player = Player(WORLD_W//2, mid_h)
        self.camera_wx = self.player.wx - w/2  # left edge of viewport

        # entities
        self.bullets       = []
        self.enemy_bullets = []
        self.mines         = []
        self.humanoids     = []
        self.landers       = []
        self.mutants       = []
        self.bombers       = []
        self.pods          = []
        self.swarmers      = []
        self.baiters       = []
        self.explosions    = []   # list of (sx,sy,r,life,maxlife,col)

        self.level         = 1
        self.baiter_timer  = 20.0
        self.level_clear   = False
        self.planet_alive  = True

        self._spawn_level()

        # input state
        self.keys    = set()
        self.multi_touches = {}
        self.fire_cooldown   = 0.0
        self.planet_explode_timer = 0.0

    def _spawn_level(self):
        h = self.screen_h
        # humanoids
        self.humanoids = []
        for i in range(NUM_HUMANOIDS):
            wx = random.uniform(0, WORLD_W)
            wy = terrain_y_at(wx, self.terrain_xs, self.terrain_pts) + 10
            self.humanoids.append(Humanoid(wx, wy))

        # landers
        n_landers = min(4 + self.level, 14)
        for _ in range(n_landers):
            wx = random.uniform(0, WORLD_W)
            wy = random.uniform(h*0.55, h*0.82)
            self.landers.append(Lander(wx, wy))

        # bombers (start level 2+)
        if self.level >= 2:
            for _ in range(min(self.level-1, 4)):
                wx = random.uniform(0, WORLD_W)
                wy = random.uniform(h*0.5, h*0.8)
                self.bombers.append(Bomber(wx, wy))

        # pods
        if self.level >= 3:
            for _ in range(min(self.level//2, 4)):
                wx = random.uniform(0, WORLD_W)
                wy = random.uniform(h*0.5, h*0.8)
                self.pods.append(Pod(wx, wy))

        self.baiter_timer = max(10.0, 20.0 - self.level)
        self.level_clear  = False
        self.planet_alive = True
        self.planet_explode_timer = 0.0

    def _all_enemies(self):
        return (self.landers + self.mutants + self.bombers +
                self.pods + self.swarmers + self.baiters)

    def _explosion(self, wx, wy, col=WHITE, r=18):
        sx = screen_x(wx, self.camera_wx, self.screen_w)
        self.explosions.append([sx, wy, 2, r, 0.4, col])

    # ── update ───────────────────────────────────────────────
    def update(self):
        dt = self.dt
        if self.state == 'attract':
            return
        if self.state == 'gameover':
            return

        p  = self.player
        h  = self.screen_h
        w  = self.screen_w

        # ── player input ─────────────────────────────────────
        thrust_x = 0
        thrust_y = 0
        if 'a' in self.keys or 'left' in self.keys:
            thrust_x = -1
        if 'd' in self.keys or 'right' in self.keys:
            thrust_x = 1
        if 'w' in self.keys or 'up' in self.keys:
            thrust_y = 1
        if 's' in self.keys or 'down' in self.keys:
            thrust_y = -1

        # touch input
        for tid, t in self.multi_touches.items():
            if t.get('type') == 'move':
                if t['x'] < w/2:
                    thrust_x = -1
                else:
                    thrust_x = 1
                thrust_y = t.get('dy', 0) * 3   # drag vertical

        if thrust_x:
            p.facing = int(math.copysign(1, thrust_x))
            p.vx += thrust_x * PLAYER_ACCEL * dt
        else:
            p.vx *= 0.88   # drag
        if thrust_y:
            p.vy += thrust_y * PLAYER_ACCEL * dt
        else:
            p.vy *= 0.88

        p.vx = clamp(p.vx, -PLAYER_MAX_SPEED_X, PLAYER_MAX_SPEED_X)
        p.vy = clamp(p.vy, -PLAYER_MAX_SPEED_Y, PLAYER_MAX_SPEED_Y)

        p.wx = (p.wx + p.vx * dt) % WORLD_W
        p.wy = clamp(p.wy + p.vy * dt,
                     terrain_y_at(p.wx, self.terrain_xs, self.terrain_pts) + 14,
                     h * 0.90)

        # camera follows player
        self.camera_wx = (p.wx - w/2) % WORLD_W

        # fire
        self.fire_cooldown -= dt
        if ('space' in self.keys or 'fire' in self.keys) and self.fire_cooldown <= 0:
            if len(self.bullets) < MAX_BULLETS:
                bvx = p.facing * BULLET_SPEED
                self.bullets.append(Bullet(p.wx, p.wy, bvx))
                self.fire_cooldown = 0.18

        # smart bomb
        if 'b' in self.keys and p.smart_bombs > 0:
            self.keys.discard('b')
            p.smart_bombs -= 1
            self._smart_bomb()

        # hyperspace
        if 'h' in self.keys and p.hyperspace_cooldown <= 0:
            self.keys.discard('h')
            p.wx = random.uniform(0, WORLD_W)
            p.wy = random.uniform(h*0.3, h*0.75)
            p.vx = p.vy = 0
            p.hyperspace_cooldown = 2.0
            # small chance of instant death (as in original)
            if random.random() < 0.05:
                self._kill_player()
        p.hyperspace_cooldown = max(0, p.hyperspace_cooldown - dt)
        p.invincible = max(0, p.invincible - dt)

        # ── bullets ──────────────────────────────────────────
        for b in self.bullets:
            b.update(dt)
            b.wx %= WORLD_W
        for b in self.enemy_bullets:
            b.update(dt)
            b.wx %= WORLD_W
        self.bullets       = [b for b in self.bullets       if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

        # ── humanoids ────────────────────────────────────────
        for hum in self.humanoids:
            hum.update(dt, self.terrain_xs, self.terrain_pts)

        # ── landers ──────────────────────────────────────────
        for lnd in self.landers:
            lnd.update(dt, self.humanoids, h, self.terrain_xs, self.terrain_pts,
                       p, self.enemy_bullets)
            # lander reached top with humanoid → mutant
            if lnd.state == Lander.LIFTING and lnd.wy >= h * 0.88 and lnd.target:
                hum = lnd.target
                hum.alive = False
                lnd.target = None
                lnd.alive  = False
                self.mutants.append(Mutant(lnd.wx, lnd.wy))
                self._check_planet_explode()

        # ── mutants ──────────────────────────────────────────
        for m in self.mutants:
            m.update(dt, p, self.enemy_bullets)

        # ── bombers & mines ───────────────────────────────────
        for bom in self.bombers:
            bom.update(dt, self.mines)
        for mn in self.mines:
            mn.update(dt)
        self.mines = [mn for mn in self.mines if mn.alive]

        # ── pods & swarmers ───────────────────────────────────
        for pod in self.pods:
            pod.update(dt)
        for sw in self.swarmers:
            sw.update(dt, p, self.enemy_bullets)

        # ── baiters ───────────────────────────────────────────
        self.baiter_timer -= dt
        if self.baiter_timer <= 0:
            self.baiter_timer = 8.0
            self.baiters.append(Baiter(random.uniform(0, WORLD_W),
                                       random.uniform(h*0.4, h*0.8)))
        for bt in self.baiters:
            bt.update(dt, p, self.enemy_bullets)

        # ── collision detection ───────────────────────────────
        self._check_bullet_hits()
        self._check_player_hits()
        self._check_rescue()

        # ── cleanup dead ─────────────────────────────────────
        self.landers   = [e for e in self.landers   if e.alive]
        self.mutants   = [e for e in self.mutants   if e.alive]
        self.bombers   = [e for e in self.bombers   if e.alive]
        self.pods      = [e for e in self.pods      if e.alive]
        self.swarmers  = [e for e in self.swarmers  if e.alive]
        self.baiters   = [e for e in self.baiters   if e.alive]
        self.humanoids = [e for e in self.humanoids if e.alive]

        # ── explosions ────────────────────────────────────────
        new_exp = []
        for ex in self.explosions:
            ex[5 if len(ex)==6 else 5]  # col is index 5
            ex[4] -= dt
            if ex[4] > 0:
                new_exp.append(ex)
        self.explosions = new_exp

        # ── level clear ───────────────────────────────────────
        if not self._all_enemies() and not self.level_clear:
            self.level_clear = True
            self.level += 1
            # bonus for survivors
            for hum in self.humanoids:
                if hum.alive and hum.on_ground:
                    p.score += 100 * self.level
            # replenish humanoids every 5 levels
            if self.level % 5 == 0:
                for hum in self.humanoids:
                    hum.alive = True
            self._spawn_level()

        # ── game over check ───────────────────────────────────
        if p.lives <= 0:
            self.state = 'gameover'

    # ── collision helpers ────────────────────────────────────
    def _check_bullet_hits(self):
        p = self.player
        hit_r2 = 16**2
        for b in self.bullets:
            for group, pts, col in [
                (self.landers,  500, WHITE),
                (self.mutants,  150, RED),
                (self.bombers,  200, ORANGE),
                (self.pods,     1000, PURPLE),
                (self.swarmers, 100, YELLOW),
                (self.baiters,  200, GREEN),
            ]:
                for e in group:
                    if e.alive and dist2(e, b) < hit_r2:
                        if e in self.pods:
                            e.burst(self.swarmers)
                        elif hasattr(e, 'target') and e.target:
                            # lander carrying human – drop it
                            e.target.captured_by = None
                            e.target.falling     = True
                            e.target.fall_vy     = 0
                            e.target.on_ground   = False
                        e.alive = False
                        b.alive = False
                        p.score += pts
                        self._explosion(e.wx, e.wy, col)
                        break

        # mines
        for b in self.bullets:
            for mn in self.mines:
                if mn.alive and dist2(mn, b) < 12**2:
                    mn.alive = False
                    b.alive  = False
                    p.score += 50
                    self._explosion(mn.wx, mn.wy, ORANGE, 10)

    def _check_player_hits(self):
        p = self.player
        if p.invincible > 0:
            return
        pr = 12**2
        for group in [self.landers, self.mutants, self.bombers,
                      self.pods, self.swarmers, self.baiters]:
            for e in group:
                if e.alive and dist2(e, p) < pr:
                    self._kill_player()
                    return
        for b in self.enemy_bullets:
            if b.alive and dist2(b, p) < 10**2:
                b.alive = False
                self._kill_player()
                return
        for mn in self.mines:
            if mn.alive and dist2(mn, p) < 14**2:
                mn.alive = False
                self._kill_player()
                return

    def _kill_player(self):
        p = self.player
        self._explosion(p.wx, p.wy, WHITE, 30)
        if p.carrying:
            p.carrying.falling   = True
            p.carrying.fall_vy   = 0
            p.carrying.on_ground = False
            p.carrying.captured_by = None
            p.carrying = None
        p.lives -= 1
        if p.lives > 0:
            p.wx  = (self.camera_wx + self.screen_w/2) % WORLD_W
            p.wy  = self.screen_h * 0.55
            p.vx  = p.vy = 0
            p.invincible = 3.0

    def _check_rescue(self):
        p = self.player
        for hum in self.humanoids:
            if not hum.alive:
                continue
            if hum.falling and dist2(hum, p) < 20**2:
                hum.falling = False
                hum.fall_vy = 0
                p.carrying  = hum
                hum.captured_by = None
                p.score += 500
        # drop humanoid if on ground
        if p.carrying:
            gnd = terrain_y_at(p.wx, self.terrain_xs, self.terrain_pts) + 14
            if p.wy <= gnd + 5:
                p.carrying.wx = p.wx
                p.carrying.wy = gnd
                p.carrying.on_ground = True
                p.carrying.falling   = False
                p.carrying = None
                p.score += 250

    def _smart_bomb(self):
        self._explosion(self.player.wx, self.player.wy, WHITE, 60)
        for group in [self.landers, self.mutants, self.bombers,
                      self.pods, self.swarmers, self.baiters,
                      self.enemy_bullets, self.mines]:
            for e in group:
                e.alive = False
        self.player.score += 200

    def _check_planet_explode(self):
        living = [h for h in self.humanoids if h.alive]
        if not living:
            self.planet_alive = False
            # all remaining landers → mutants
            for lnd in self.landers:
                self.mutants.append(Mutant(lnd.wx, lnd.wy))
            self.landers.clear()

    # ── draw ─────────────────────────────────────────────────
    def draw(self):
        scene.background('black') #*BLACK)
        w, h = self.screen_w, self.screen_h
        cam  = self.camera_wx
        p    = self.player

        if self.state == 'attract':
            self._draw_attract(w, h)
            return
        if self.state == 'gameover':
            self._draw_gameover(w, h)
            return

        radar_top = h - self.radar_h

        # ── starfield ────────────────────────────────────────
        random.seed(42)
        
        for _ in range(80):
            sx = random.uniform(0, w)
            sy = random.uniform(self.radar_h + 4, radar_top - 2)
            r  = random.uniform(0.5, 1.5)
            scene.stroke_weight(r)
            scene.stroke(0.7, 0.7, 0.7, 0.6)
            scene.line(sx-r, sy, sx+r, sy)
        random.seed()

        # ── terrain ──────────────────────────────────────────
        col_t = DKGREEN if self.planet_alive else RED
                  
        scene.stroke(*col_t)
        prev_sx = None
        prev_sy = None
        for i, (wx, wy) in enumerate(zip(self.terrain_xs, self.terrain_pts)):
            sx = screen_x(wx, cam, w)
            sy = wy
            if prev_sx is not None and sx >= 0:
                scene.stroke_weight(3)      
                scene.line(prev_sx, prev_sy, sx, sy)
                # fill under terrain
                scene.stroke_weight(1)
                # vertical terrain line
                # scene.line(prev_sx, 0, prev_sx, prev_sy)
                
            prev_sx, prev_sy = sx, sy
        

        # ── humanoids ────────────────────────────────────────
        for hum in self.humanoids:
            if not hum.alive:
                continue
            sx = screen_x(hum.wx, cam, w)
            if -20 < sx < w+20:
                draw_humanoid(sx, hum.wy, captured=hum.captured_by is not None)

        # ── enemies ──────────────────────────────────────────
        for lnd in self.landers:
            sx = screen_x(lnd.wx, cam, w)
            if -20 < sx < w+20:
                draw_lander(sx, lnd.wy)

        for m in self.mutants:
            sx = screen_x(m.wx, cam, w)
            if -20 < sx < w+20:
                draw_mutant(sx, m.wy)

        for bom in self.bombers:
            sx = screen_x(bom.wx, cam, w)
            if -20 < sx < w+20:
                draw_bomber(sx, bom.wy)

        for pod in self.pods:
            sx = screen_x(pod.wx, cam, w)
            if -20 < sx < w+20:
                draw_pod(sx, pod.wy)

        for sw in self.swarmers:
            sx = screen_x(sw.wx, cam, w)
            if -20 < sx < w+20:
                draw_swarmer(sx, sw.wy)

        for bt in self.baiters:
            sx = screen_x(bt.wx, cam, w)
            if -20 < sx < w+20:
                draw_baiter(sx, bt.wy)

        for mn in self.mines:
            sx = screen_x(mn.wx, cam, w)
            if -20 < sx < w+20:
                draw_mine(sx, mn.wy)

        # ── enemy bullets ────────────────────────────────────
        for b in self.enemy_bullets:
            sx = screen_x(b.wx, cam, w)
            scene.stroke(*ORANGE)
            scene.stroke_weight(2)
            scene.line(sx-3, b.wy, sx+3, b.wy)

        # ── player bullets ───────────────────────────────────
        for b in self.bullets:
            sx = screen_x(b.wx, cam, w)
            scene.stroke(*WHITE)
            scene.stroke_weight(2)
            scene.line(sx, b.wy-2, sx+p.facing*18, b.wy+2)

        # ── player ───────────────────────────────────────────
        flash = int(p.invincible * 8) % 2 == 1
        if p.lives > 0:
            draw_ship(w/2, p.wy, p.facing, flash)

        # ── explosions ───────────────────────────────────────
        for ex in self.explosions:
            sx, sy, r0, rmax, life, col = ex[0], ex[1], ex[2], ex[3], ex[4], ex[5]
            frac = 1 - life/0.4
            r    = r0 + (rmax - r0) * frac
            alpha = max(0, life/0.4)
            scene.stroke(col[0], col[1], col[2], alpha)
            scene.stroke_weight(1.5)
            for ang in range(0, 360, 30):
                a = math.radians(ang)
                scene.line(sx, sy,
                                sx + math.cos(a)*r,
                                sy + math.sin(a)*r,
                                )

        # ── radar strip ──────────────────────────────────────
        scene.stroke(0.3, 0.3, 0.3, 1)
        scene.stroke_weight(1)
        scene.line(0, radar_top, w, radar_top)
        # radar background
        scene.stroke(0,0,0,1)
        scene.stroke_weight(self.radar_h*2)
        scene.line(0, h, w, h)

        radar_scale = w / WORLD_W

        def radar_sx(wx):
            return ((wx - cam) % WORLD_W) * radar_scale

        # terrain on radar
        scene.stroke(*DKGREEN)
        scene.stroke_weight(1)
        for i in range(len(self.terrain_xs)-1):            
            rx0 = radar_sx(self.terrain_xs[i])
            rx1 = radar_sx(self.terrain_xs[i+1])
            ry  = radar_top + (self.terrain_pts[i]/self.screen_h) * self.radar_h * 0.5
            if rx0 >= 0:
              § scene.line(rx0, ry, rx1, ry)

        # humanoids on radar
        scene.stroke(*YELLOW)
        scene.stroke_weight(2)
        for hum in self.humanoids:
            if hum.alive:
                rx = radar_sx(hum.wx)
                scene.line(rx, radar_top+2, rx, radar_top+5)

        # enemies on radar
        scene.stroke(*CYAN)
        scene.stroke_weight(2)
        for e in self._all_enemies():
            rx = radar_sx(e.wx)
            scene.line(rx-1, radar_top+4, rx+1, radar_top+4+4)

        # player on radar
        rx = radar_sx(p.wx)
        scene.stroke(*WHITE)
        scene.stroke_weight(3)
        scene.line(rx-2, radar_top+1, rx+2, radar_top+8)

        # ── HUD ──────────────────────────────────────────────
        scene.tint(*WHITE)
        scene.text(f'SCORE  {p.score:07d}',
                        x=w*0.02, y=h*0.96, font_size=14)
        scene.text(f'LEVEL {self.level}',
                        x=w*0.42, y=h*0.96, font_size=14)
        scene.tint(*RED)                
        scene.text(f'LIVES {"♥ " * p.lives}',
                        x=w*0.62, y=h*0.96, font_size=14)
        scene.tint(*ORANGE)                
        scene.text(f'BOMBS {p.smart_bombs}',
                        x=w*0.84, y=h*0.96, font_size=14)

        if not self.planet_alive:
            scene.tint(*RED)
            scene.text('PLANET DESTROYED – KILL THEM ALL!',
                            x=w*0.15, y=h*0.50, font_size=18)

        if p.invincible > 0:
            scene.tint(*CYAN)
            scene.text('RESPAWNING...',
                            x=w*0.35, y=h*0.60, font_size=16)

    def _draw_attract(self, w, h):
        scene.tint(*GREEN)
        scene.text('DEFENDER',
                        x=w*0.5, y=h*0.65, font_size=52)
        scene.tint(*CYAN)                
        scene.text('Williams Electronics  1981',
                        x=w*0.5, y=h*0.52, font_size=18)
        scene.tint(*YELLOW)                
        scene.text('Protect the humanoids!',
                        x=w*0.5, y=h*0.42, font_size=16)
        scene.tint(*WHITE)                
        scene.text('TAP anywhere to start',
                        x=w*0.5, y=h*0.30, font_size=24)
        scene.text('Touch left/right  →  thrust',
                        x=w*0.5, y=h*0.20, font_size=18)
        scene.text('Drag up/down  →  altitude',
                        x=w*0.5, y=h*0.14, font_size=18)
        scene.text('2-finger tap → Smart Bomb   3-finger → Hyperspace',
                        x=w*0.5, y=h*0.08, font_size=18)

    def _draw_gameover(self, w, h):
        scene.tint(*RED)
        scene.text('GAME OVER',
                        x=w*0.25, y=h*0.62, font_size=48)
        scene.tint(*WHITE)               
        scene.text(f'SCORE: {self.player.score}',
                        x=w*0.32, y=h*0.48, font_size=28)
        scene.tint(*YELLOW)
        scene.text('TAP to play again',
                        x=w*0.30, y=h*0.34, font_size=20)

    # ── input ────────────────────────────────────────────────
    # renamed self.touches to self.multi_touches CMT
    def touch_began(self, touch):
        if self.state in ('attract', 'gameover'):
            self._init_game()
            self.state = 'playing'
            return
        n = len(self.multi_touches)
        self.multi_touches[touch.touch_id] = {
            'x': touch.location.x,
            'y': touch.location.y,
            'dy': 0,
            'type': 'tap'
        }
        if n == 1:   # second finger = smart bomb
            if self.player.smart_bombs > 0:
                self.player.smart_bombs -= 1
                self._smart_bomb()
        elif n >= 2: # third finger = hyperspace
            self.keys.add('h')

        # fire tap
        self.keys.add('fire')

    def touch_moved(self, touch):
        if touch.touch_id in self.multi_touches:
            t = self.multi_touches[touch.touch_id]
            old_y = t['y']
            t['x'] = touch.location.x
            t['y'] = touch.location.y
            t['dy'] = touch.location.y - old_y
            t['type'] = 'move'

    def touch_ended(self, touch):
        if touch.touch_id in self.multi_touches:
           self.multi_touches.pop(touch.touch_id)
        
        if not self.multi_touches:
            self.keys.discard('fire')
            self.keys.discard('h')

    def key_up(self, key):
        self.keys.discard(key)

    def key_down(self, key):
        self.keys.add(key)


# ── launch ───────────────────────────────────────────────────
scene.run(DefenderGame(), scene.LANDSCAPE, show_fps=True)
