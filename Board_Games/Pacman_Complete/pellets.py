import pygame
from vector import Vector2
from constants import *
import numpy as np
from scene import *

class Pellet(object):
    def __init__(self, row, column):
        self.name = PELLET
        self.position = Vector2(column*TILEWIDTH, (NROWS - 1 - row) *TILEHEIGHT)
        self.color = RED
        self.radius = int(2 * TILEWIDTH / 16)
        self.collideRadius = 2 * TILEWIDTH / 16
        self.points = 1
        self.visible = True
        self.row = row
        self.col = column
        
    def render(self, screen):
        if self.visible:
            adjust = Vector2(TILEWIDTH, TILEHEIGHT) / 2
            p = self.position # + adjust
            ShapeNode(ui.Path.rounded_rect(0,0, 2*self.radius, 2*self.radius, self.radius), 
                      position=p, fill_color=self.color, parent=screen)            


class PowerPellet(Pellet):
    def __init__(self, row, column):
        Pellet.__init__(self, row, column)
        self.name = POWERPELLET
        self.radius = int(8 * TILEWIDTH / 16)
        self.points = 50
        self.flashTime = 0.2
        self.timer= 0
        
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.flashTime:
            self.visible = not self.visible
            self.timer = 0


class PelletGroup(object):
    def __init__(self, pelletfile):
        self.pelletList = []
        self.powerpellets = []
        self.createPelletList(pelletfile)
        self.numEaten = 0
        
        
    def update(self, dt):
        for powerpellet in self.powerpellets:
            powerpellet.update(dt)
                
    def createPelletList(self, pelletfile):
        data = self.readPelletfile(pelletfile)      
        
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                if data[row][col] in ['.', '+']:
                    self.pelletList.append(Pellet(row, col))
                elif data[row][col] in ['P', 'p']:
                    pp = PowerPellet(row, col)
                    self.pelletList.append(pp)
                    self.powerpellets.append(pp)
                    
    def readPelletfile(self, textfile):
        return np.loadtxt(textfile, dtype='<U1')
    
    def isEmpty(self):
        if len(self.pelletList) == 0:
            return True
        return False
    
    def render(self, screen, update_display=False):
        for pellet in self.pelletList:
            pellet.render(screen)


