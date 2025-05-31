# https://gist.github.com/anonymous/a03bfdab757c1d978061

from scene import *
from random import randint, uniform, choice
import sound
from math import pi, hypot
#sound.play_effect('Explosion_1')

statusY = 900
statusSizeY = 68
PLAYER_SIZE = 80
ENEMY_SIZE = 40
ENEMY_PER_WAVE = 5
FONTSIZE = 32


# Draws status info
def status(self):
  #fill('black')
  #rect(0,statusY,1024,statusSizeY)
  #scene.text(txt, font_name='Helvetica', font_size=16.0, x=0.0, y=0.0, alignment=5)
  text(f'Wave: {self.wave} Enemies: {len(self.enemies)}\n'
       f'Health: {int(self.player.health)}\nShield: {max(0, int(self.player.shield))}\n'
       f'Bonus: {int(self.bullet_special_timer)}',
        'Chalkduster', FONTSIZE, 50, statusY+FONTSIZE*3,  3)

  
  
# Just combines set_volume and play_effect
def playSound(name,volume):
  sound.set_volume(volume)
  sound.play_effect(name)
 
# Bullet class.
class Bullet (object):
  def __init__(self, position, velocity, type, owner='player'):
    self.pos = position
    self.vel = velocity
    self.type = type
    self.owner = owner
    self.special = 0 #Used for missiles
    
  def render(self):
    match self.type:
      case 0:
          fill('white')  #Bullet color 'bullet'
      case 1:
          fill('green') #Bullet: 'missile'          
      case 2:
          fill('green') #Bullet: 'cluster'     
      case 11:
          fill('red') #Enemy bullet = red: 'missile'
      case 12:
          fill('yellow') #Enemy bullet = yellow: 'bullet'
      case _:
          fill(0.38, 1.0, 0.75)    #Bullet color = spindrift: 'cluster bomb'
          
  def plot(self):
      # plot bullet
      ellipse(self.pos.x-2, self.pos.y-2, 4, 4)

#Exploding bullet particles
class BulletParticle (object):
  def __init__(self, position, velocity):
    self.pos = position
    self.vel = velocity
    
#Exploding bullet effect
class BulletExplosion (object):
  def __init__(self, position, velocity,ship=False):
    self.ship = ship
    self.particles = set()
    self.alpha = 1
    if ship: 
        loop=15
        velocity.x*=-.1
    else: 
        loop=2
    for i in range(loop):
      if ship: 
        divide = (i+1)/3.
      else: 
        divide = i+3
      self.particles.add(BulletParticle(Point(position.x, position.y), 
                                        Point( (velocity.x+randint(-1,1)) / divide,
                                               (velocity.y+randint(-1,4)) / divide ) ) )
class Bonus(object):
    def __init__(self, scene, position):
      self.pos = Point(*(position-(ENEMY_SIZE/2, ENEMY_SIZE/2)))
      self.vel = Point(5, 0)
      self.size_ = Point(ENEMY_SIZE, ENEMY_SIZE)
      self.powerup = SpriteNode('spc:Star3', #'spc:PowerupBlueBolt', 
                                   size=(ENEMY_SIZE, ENEMY_SIZE),
                                   position=self.pos)
      scene.add_child(self.powerup)
      
    def hit(self, player):
        #Hit test function used for bullets
        return self.powerup.bbox.intersects(player.ship.bbox)
        
    def render(self):
        self.powerup.position = self.pos
        #fill('blue')
        #ellipse(*self.pos, *self.size_)
        
        
class Player(object):
    def __init__(self, scene, position, shield=0):
        self.pos = Point(*position)
        self.target = Point(position.x, position.y)
        self.health = 100
        self.stun = 0 #This timer is also aesthetic and makes the scene look strange when hit
        self.shield_max = 100
        self.shield = shield # 'current'.  Shield recharges.
        self.off = Point(-17.5, 45)
        self.bulletLoop = 0
        self.size_ = Point(PLAYER_SIZE, PLAYER_SIZE)
        self.ship = SpriteNode('spc:PlayerShip3Blue', size=self.size_, position=self.pos, z_position=10)
        self.ship.rotation = -pi / 2
        scene.add_child(self.ship)
        self.shield_image = SpriteNode(None, color='black', size=self.size_, position=self.pos)
        self.shield_image.rotation = -pi / 2
        scene.add_child(self.shield_image)
        
    def hit(self, bullet):
        #Hit test function used for bullets
        return self.ship.frame.contains_point(bullet)

            
    def set_position(self, pos):      
      self.position = pos # - self.size_ / 2
      self.ship.position = self.position
      self.shield_image.position = self.position
      if self.health < 50:
         self.ship.color='red'
      else:
          self.ship.color='white'
      self.healthBar()
      
    def powerup(self, set=True):
       if set:
           self.ship.texture = Texture('spc:PlayerShip2Orange')
       else:
           self.ship.texture = Texture('spc:PlayerShip3Blue')
       
    def update_shield(self, hit=False):
       if hit:         
           if self.shield > 0: 
               self.shield -= 20
           else: 
               self.health -= 10
               self.stun = -1
               
       if self.shield < self.shield_max:
          self.shield += .1
       shields = [None, 'spc:Shield1', 'spc:Shield2', 'spc:Shield3']
       icon_no = int(self.shield / (1+self.shield_max/4))
       self.shield_image.texture = Texture(shields[icon_no]) if icon_no>0 else None
       self.shield_image.color = 'white' if icon_no else 'black'
       
    # Draws a healthbar
    def healthBar(self):      
      loc = self.position + self.off
      fill('red') #Damaged
      rect(*loc, 33, 5)
      if self.health > 0:
        fill('green') #Health
        rect(*loc, self.health/3, 5)
      if self.shield > 0:
        fill('blue') #Shield
        rect(*loc, self.shield/3, 5)
                
class Enemy (Player):
  def __init__(self, scene, position, velocity=Point(4, 4), type=0, shield=0):
    
    ships = ['spc:EnemyBlue1', 'spc:EnemyBlue3', 'spc:EnemyRed1', 'spc:EnemyRed4', 'spc:EnemyBlue2']
    self.pos = Point(*position)
    self.vel = velocity
    self.target = Point(position.x, position.y)
    self.type = type
    self.health = 100
    self.shield = shield #0 is 'max', 1 is 'current'.  Shield recharges.
    self.off = Point(-17.5, 25)
    self.shield_max = 100
    self.bulletLoop = 0
    self.ship = SpriteNode(ships[self.type], size=(ENEMY_SIZE, ENEMY_SIZE), position=self.pos)
    self.ship.rotation = -pi / 2
    self.size_ = Point(ENEMY_SIZE, ENEMY_SIZE)
    self.shield_image = SpriteNode('spc:BackgroundBlack', size=self.size_, scale=0.5, position=self.pos)
    self.shield_image.rotation = pi / 2
    scene.add_child(self.shield_image)
  

       
class MyScene (Scene):
  #def should_rotate(self,orientation):
  # return False
  def setup(self):
    self.wave = 0 # The more waves, the harder the game becomes.
    self.speed = 20 # How quickly player moves
    self.vel = Point(0, 0) # Velocity
    self.pos = Point(100, 384) # Position
    self.target = Point(*self.pos) #Touch target
    self.bullets = set() # A set containing all active bullets. 
    self.bulletLoop = 0  # Used to determine when to shoot bullets
    self.bulletSpeed = 7 # The rate bullets are fired.
    self.bullet_special_timer = 0 # When the player gets a bonus, this is used as a timer
    self.bulletType = 0#randint(0,2) # 0=normal.  1=missile.  2=cluster bullet
    self.bullet_explosions = set() # Exploding bullets.  Purely aesthetic.
    self.bonus = set() # Bonuses the player can collect to change bulletType and bullet_special_timer
    self.enemies = set() # A set containing all active enemies
    #self.stun = 0 #This timer is also aesthetic and makes the scene look strange when hit
    self.mute = False # Used for muting sound.  May increase performance?
    self.screen = 1 # If screen=0, play scene.  Otherwise, draw screens.
    self.player = Player(scene=self, position=self.pos, shield=50)
    self.play_area = Rect(50, 50, self.size.w-120, self.size.h-120)     
    
  def process_enemies(self):
    # ENEMIES
    enemiesShoot = False #Used for sound
    for enemy in self.enemies:
      if not self.play_area.contains_point(enemy.pos):
         if enemy.pos.y > self.play_area.max_y or enemy.pos.y < self.play_area.min_y: 
            enemy.pos.y = max(self.play_area.min_y, min(enemy.pos.y, self.play_area.max_y))
            enemy.vel.y *= -1
      if enemy.pos.x > enemy.target.x:
        enemy.pos.x = ((enemy.pos.x*800) + enemy.target.x) / 801
      if enemy.bulletLoop > 200:
        enemy.bulletLoop = 0
        enemyShoot = True
        self.bullets.add(Bullet(Point(*enemy.pos),
                         Point(-8,0), randint(11,12), owner='enemy'))
      else: 
          enemy.bulletLoop += 1
          
      enemy.pos.y += enemy.vel.y
      enemy.set_position(enemy.pos)
      enemy.update_shield()
      
    return enemiesShoot
    
  def process_explosions(self):
    # EXPLOSIONS
    deadExplosions=set()
    for explosion in self.bullet_explosions:
      explosion.alpha -= .01
      if explosion.alpha > 0:
        for particle in explosion.particles:
          particle.pos += particle.vel
          if explosion.ship: 
            fill('red', explosion.alpha)
            ellipse(particle.pos.x-(explosion.alpha*5), particle.pos.y-(explosion.alpha*5),
                     (explosion.alpha*10),  (explosion.alpha*10))
          else: 
            fill('white', explosion.alpha)
            rect(particle.pos.x-1, particle.pos.y-1, 2, 2)
      else: deadExplosions.add(explosion)
    self.bullet_explosions -= deadExplosions
    
  def process_bonuses(self):
      # BONUSES
      deadBonus = set()
      bonusSound = False
      for bonus in self.bonus:
        bonus.render()
        
        bonus.pos.x -= 4
        if bonus.pos.x < 0: 
           deadBonus.add(bonus)
        elif bonus.hit(self.player):
          bonusSound = True
          self.player.powerup(True)
          deadBonus.add(bonus)
          randBullet = randint(1,5)
          match randBullet:
              case 1: # fast bullet
                  self.bulletType = 1
                  self.bullet_special_timer = 800
                  self.bulletSpeed = 5
              case 2: #cluster
                  self.bulletType = 2
                  self.bullet_special_timer = 1000
                  self.bulletSpeed = 20
              case 3: # cluster
                  self.bulletType = 2
                  self.bullet_special_timer = 150
                  self.bulletSpeed = 5
              case 4: # 
                  self.bulletType = 1
                  self.bullet_special_timer = 400
                  self.bulletSpeed = 2
              case 5: # normal
                  self.bulletType = 0
                  self.bullet_special_timer = 600
                  self.bulletSpeed = 1
      self.bonus -= deadBonus
      return bonusSound, deadBonus
    
  def clear_enemies(self):
    for en in self.enemies:
      en.ship.remove_from_parent()
      en.shield_image.remove_from_parent()
      
  def count_down_bonus(self):
      # bullet_special_timer is turned on by hitting 'bonus' items.  
      if self.bullet_special_timer >= 0:
        self.bullet_special_timer -= 1
        if self.bullet_special_timer < 0:
          self.player.powerup(False)
          self.bulletType = 0
          self.bullet_special_timer = 0
          self.bulletSpeed = 7
                
  def draw(self):    
    #Stun is the background.  To create the stun effect, simply don't draw a full
    #background. Leave some parts transparent so it only overlaps the last draw()
    background('black')
    if self.player.stun<0:
      # fill(0,0,0,self.player.stun+1) #Replace with background for trippy effects
      # rect(0,0,1024,768)
      self.player.stun+=.005
      
    
    #Start with screens.
    if self.screen:
      if self.screen==1:
        text('eliskan space shooter v1.0\n   \"They shoot, you die.\"', 'Chalkduster', 25., 512, 384,  2)
      elif self.screen==2:
        text('That had to hurt! Ouch...\n     Click to restart.', 'Chalkduster', 25., 512, 384,  2)
      return
          
    # Move towards touch
    if self.pos.y < self.target.y - 1 or self.pos.y > self.target.y + 1:
      self.pos.y = ((self.pos.y*self.speed) + self.target.y) / (self.speed + 1)
      
    # Draw a blue box for player
    self.player.set_position(self.pos)    
    
    #Handle shield and health bar
    self.player.update_shield()    
    
    self. count_down_bonus()
    
    # SHOOT BULLETS
    self.bulletLoop += 1
    if self.bulletLoop > self.bulletSpeed:
      self.bulletLoop = 0
      self.bullets.add(Bullet(Point(*self.pos),
                              Point(8,0),self.bulletType,
                              owner='player'))
      
    # NEW WAVE
    if len(self.enemies) == 0:
      self.bullets = set()
      self.player.health = 100
      self.bullet_explosions = set()
      self.wave += 1
      for i in range(self.wave+ENEMY_PER_WAVE):
        enemy = Enemy(self,
                         position=Point(self.play_area.max_x,
                                        randint(self.play_area.min_y,
                                                self.play_area.max_y)),
                         type=randint(0,4))
        enemy.target.x = randint(300,600)
        self.enemies.add(enemy)
        self.add_child(enemy.ship)
      
    #BULLETS
    deadBullets = set()
    newBullets = set()
    deadEnemies = set()
    bulletHit = False #Used for sound
    bulletHitPlayer = False #Used for sound
    
    for bull in self.bullets:
      smallestDif = 300
      bull.render()
      if bull.owner == 'player':
          #bull.render()
        
          for enemy in self.enemies:
            if bull.type == 1:
                d = enemy.pos - bull.pos
                difference = hypot(*d)
                if difference < smallestDif:
                    smallestDif = difference
                    target = enemy
              
            #Hit enemies
            if enemy.hit(bull.pos): 
              if bull.type == 2: #Cluster bombs spawn missiles when they hit enemy
                for i in range(10):
                  #tempInt=randint(0,2)
                  newBullets.add(Bullet(bull.pos - (20,0),
                                   Point((bull.vel.x+uniform(-2., 2.))*-1,
                                         (bull.vel.y+uniform(-2., 2.))*-1), 1, owner='player'))
          
              bulletHit = True
              deadBullets.add(bull)
                
              self.bullet_explosions.add(BulletExplosion(bull.pos, bull.vel))
              enemy.update_shield(hit=True)
              if enemy.health <= 0:
                  deadEnemies.add(enemy)
                  self.bullet_explosions.add(BulletExplosion(enemy.pos,enemy.vel,True))
                  if randint(1,3)==1: #Random chance to drop a bonus.
                    self.bonus.add(Bonus(scene=self, position=enemy.pos))
      else: #Bullet is used by enemy
        if bull.type == 11:
          #bull.render()
          d = self.pos - bull.pos
          difference = hypot(*d)

          if difference < smallestDif:
              smallestDif = difference
              target = self.player
        else: 
          #bull.render()
          smallestDif = 300
        
        # Damaging the player
        if self.player.hit(bull.pos):
          bulletHitPlayer = True
          self.player.update_shield(hit=True)
          
          deadBullets.add(bull)
          self.bullet_explosions.add(BulletExplosion(bull.pos,bull.vel))
          if self.player.health <= 0:
            self.screen = 2
          
      if bull.type == 1 or bull.type == 11: #Missiles
        if smallestDif != 300:
          if bull.type == 1: fill (0, 0.70, 0.10)  # Bullet color = clover: 'missile activated'
          else: fill('purple') #Enemy bullet = purple: 'missile activated'
          if bull.special < 125:
            bull.special += 1
          else: 
            deadBullets.add(bull)
            self.bullet_explosions.add(BulletExplosion(bull.pos,bull.vel))
          mod = 20
          bull.vel += (target.pos - bull.pos) / difference
          
          if bull.vel.x>10 or bull.vel.x<-10: 
              bull.vel.x/=1.1
          if bull.vel.y>10 or bull.vel.y<-10: 
              bull.vel.y/=1.1
      bull.pos += bull.vel

      if not self.play_area.contains_point(bull.pos):
          deadBullets.add(bull)
          
      bull.plot()
      
    # remove bullets and enemies 
    self.bullets -= deadBullets
    for newBullet in newBullets:
      if len(self.bullets) < 50 - self.wave: 
          self.bullets.add(newBullet)
    self.enemies -= deadEnemies
    for enemy in deadEnemies:
        enemy.ship.remove_from_parent()
        enemy.shield_image.remove_from_parent()
    
            
    enemiesShoot = self.process_enemies()    
    self.process_explosions()
    bonusSound, deadBonus = self.process_bonuses()
    for bonus in deadBonus:
        bonus.powerup.remove_from_parent()
    
    
    #Sounds
    if not self.mute:
      if deadEnemies:
        playSound('Hit_2', 0.1)
      elif bonusSound:
        playSound('Jump_3',0.1)
      elif enemiesShoot:
        playSound('Laser_4', 0.1)
      elif bulletHitPlayer:
        playSound('Powerup_3', 0.1)
      elif self.bulletLoop==0:
        playSound('Laser_6', 0.05)
      elif bulletHit:
        playSound('Hit_1', 0.1)
    
    #Status
    status(self)
    
  def reset(self):
      self.clear_enemies()
      self.bonus = set()
      self.bullets = set()
      self.enemies = set()
      self.bullet_explosions = set()
      self.wave = 0
      self.player.shield = 100
      self.player.health = 100
        
  def touch_began(self, touch):
    self.target = touch.location
  def touch_moved(self, touch):
    self.target = touch.location
  def touch_ended(self, touch):
    if self.screen:
      #if self.screen == 1:
      if self.screen == 2:
         self.reset()
      self.screen = 0
    self.target = touch.location

run(MyScene(), LANDSCAPE, 2)

