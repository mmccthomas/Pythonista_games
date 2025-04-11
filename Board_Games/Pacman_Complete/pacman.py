import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites_scene import PacmanSprites
from queue import Empty

class Pacman(Entity):
    def __init__(self, node, queue):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        self.q = queue

    def reset(self):
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()

    def die(self):
        self.alive = False
        self.direction = STOP

    def update(self, dt, key=None): 
        # for ios import key. key is STOP at end of touch
        self.sprites.update(dt)
        #if  key is not None:
        #    direction = key
        #else:
        direction = self.getValidKey()
        self.position += self.directions[self.direction]*self.speed*dt
 
        if self.overshotTarget():
            #print(self.position, 'moving', key)
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            if self.target is self.node:
                self.direction = STOP
            self.setPosition()
        else: 
            if self.oppositeDirection(direction):
                self.reverseDirection()

    def getValidKey(self):
    	
        #key_pressed = {K_UP: UP, K_DOWN: DOWN, K_LEFT: LEFT, K_RIGHT: RIGHT}
        #key_pressed = pygame.key.get_pressed()
        try:
          self.key_pressed = self.q.get(block=False)
          return self.key_pressed
        except Empty:                
          return self.key_pressed  

    def eatPellets(self, pelletList):
        for pellet in pelletList:
            if self.collideCheck(pellet):
                return pellet
        return None    
    
    def collideGhost(self, ghost):
        return self.collideCheck(ghost)

    def collideCheck(self, other):
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False


