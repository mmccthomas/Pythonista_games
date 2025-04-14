# convert run.py to use Pythonista scene on ios instead of Pygame
# TODO get this working again
from scene import *
import os
import sys
#current = os.path.dirname(os.path.realpath(__file__))
#parent = os.path.dirname(current)
#sys.path.append(current)
#sys.path.append(parent)
import pygame
from pygame.locals import *
from constants import *
from pacman import Pacman
from nodes import NodeGroup
from pellets import PelletGroup
from ghosts import GhostGroup
from fruit import Fruit
from pauser import Pause
from text import TextGroup
from sprites_scene import LifeSprites
from sprites_scene import MazeSprites
from sprites_scene import Tile
from mazedata import MazeData
from time import time
from queue import Queue, Empty
FRAME_RATE = 0.033
Q = Queue()


class GameController(Scene):
    def __init__(self):
        #pygame.init()
        Scene.__init__(self)
        self._timer = FRAME_RATE
        self.screen = Node(parent=self, position=GRID_POS) #pygame.display.set_mode(SCREENSIZE, 0, 32)
        self.background_color = 'black' # for ios
        self.background_norm = None
        self.background_flash = None
        #self.clock = pygame.time.Clock()
        self.fruit = None
        self.pause = Pause(True)
        self.level = 0
        self.lives = 5
        self.score = 0
        self.count = 0
        self.key = STOP
        self.textgroup = TextGroup()
        self.lifesprites = LifeSprites(self.lives)
        self.flashBG = False
        self.flashTime = 0.2
        self.flashTimer = 0
        self.fruitCaptured = []
        self.fruitNode = None
        self.mazedata = MazeData()
        self.startGame()

    def setBackground(self):
        #self.background_norm = pygame.surface.Surface(SCREENSIZE).convert()
        #self.background_norm.fill(BLACK)
        #self.background_flash = pygame.surface.Surface(SCREENSIZE).convert()
        #self.background_flash.fill(BLACK)
        self.background_norm = self.mazesprites.constructBackground(self.background_norm, self.level%5)
        #self.background_flash = self.mazesprites.constructBackground(self.background_flash, 5)
        self.flashBG = False
        self.background = self.background_norm

    def startGame(self):      
        self.mazedata.loadMaze(self.level)
        self.mazesprites = MazeSprites(self.mazedata.obj.name+".txt", self.mazedata.obj.name+"_rotation.txt", self.screen)
        self.setBackground()
        self.nodes = NodeGroup(self.mazedata.obj.name+".txt")
        self.mazedata.obj.setPortalPairs(self.nodes)
        self.mazedata.obj.connectHomeNodes(self.nodes)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart), queue=Q)
        self.pellets = PelletGroup(self.mazedata.obj.name+".txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)

        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(0, 3)))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(4, 3)))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 0)))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.mazedata.obj.denyGhostsAccess(self.ghosts, self.nodes)
        self.add_controls()
        self.textgroup.render(self.screen,False)
        self.fixed_nodes = len(self.screen.children)
        #test
        self.fruit = Fruit(self.nodes.getNodeFromTiles(9, 20), self.level)
        self.render()
        #self.pause = Pause(False)

    def startGame_old(self):      
        self.mazedata.loadMaze(self.level)#######
        self.mazesprites = MazeSprites("maze1.txt", "maze1_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup("maze1.txt")
        self.nodes.setPortalPair((0,17), (27,17))
        homekey = self.nodes.createHomeNodes(11.5, 14)
        self.nodes.connectHomeNodes(homekey, (12,14), LEFT)
        self.nodes.connectHomeNodes(homekey, (15,14), RIGHT)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(15, 26))
        self.pellets = PelletGroup("maze1.txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 0+14))
        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(0+11.5, 3+14))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(4+11.5, 3+14))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, LEFT, self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, RIGHT, self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.nodes.denyAccessList(12, 14, UP, self.ghosts)
        self.nodes.denyAccessList(15, 14, UP, self.ghosts)
        self.nodes.denyAccessList(12, 26, UP, self.ghosts)
        self.nodes.denyAccessList(15, 26, UP, self.ghosts)

    def add_controls(self):
      UI = {"LEFT_BTN": {"texture": 'typw:Left', "size": (100,100), "position": Vector2(800, 100)},
            "RIGHT_BTN": {"texture": 'typw:Right',"size": (100,100),"position": Vector2(900, 100)},
            "UP_BTN": {"texture": 'typw:Up',"size": (100,100),"position": Vector2(850, 150)},
            "DOWN_BTN": {"texture": 'typw:Down',    "size": (100,100),"position": Vector2(850, 50)},
            "PAUSE_BTN": {"texture": 'iow:pause_256',"size": (100,100),"position": Vector2(1000, 100)},
             }
      self.left_btn = SpriteNode(**UI["LEFT_BTN"], parent=self.screen)
      self.right_btn = SpriteNode(**UI["RIGHT_BTN"],parent=self.screen)
      self.down_btn = SpriteNode(**UI["DOWN_BTN"], parent=self.screen)
      self.up_btn = SpriteNode(**UI["UP_BTN"], parent=self.screen)   
      self.pause_btn = SpriteNode(**UI["PAUSE_BTN"], parent=self.screen)   
      
    @ui.in_background
    def update(self):
        #dt = self.clock.tick(30) / 1000.0
        self._timer -= self.dt
        if self._timer <= 0:      
            self._timer = FRAME_RATE
            ts = time()
            dt = FRAME_RATE
            if self.pacman.alive:
                if not self.pause.paused:
                    self.pacman.update(dt, self.key)
            else:
                self.pacman.update(dt, self.key)
            self.textgroup.update(dt)
            self.pellets.update(dt)
            if not self.pause.paused:
                self.ghosts.update(dt)      
                if self.fruit is not None:
                    self.fruit.update(dt)
                self.checkPelletEvents()
                self.checkGhostEvents()
                self.checkFruitEvents()
            
    
            if self.flashBG:
                self.flashTimer += dt
                if self.flashTimer >= self.flashTime:
                    self.flashTimer = 0
                    if self.background == self.background_norm:
                        self.background = self.background_flash
                    else:
                        self.background = self.background_norm
    
            afterPauseMethod = self.pause.update(dt)
            if afterPauseMethod is not None:
                afterPauseMethod()
            self.checkEvents()
            self.render(False)
            # print('elapsed', time() -  ts)
            
    def touch_began(self, touch):
        t = touch.location - GRID_POS       
        if self.pause_btn.bbox.contains_point(t):
          self.pause.flip()
          if self.pause.paused:
            self.textgroup.showText(PAUSETXT)
          else:
            self.textgroup.hideText()
          return
        elif self.left_btn.bbox.contains_point(t):
          self.key = LEFT
        elif self.right_btn.bbox.contains_point(t):
          self.key = RIGHT
        elif self.down_btn.bbox.contains_point(t):
          self.key = DOWN
        elif self.up_btn.bbox.contains_point(t):
          self.key = UP        
        Q.put(self.key)
        
    def touch_ended(self, touch):
      self.key = STOP
      Q.put(self.key)
      #self.pacman.direction = STOP
      
    def checkEvents(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                            #self.hideEntities()

    def checkPelletEvents(self):
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            print(f'eat pellet at {pellet.position} row {pellet.row} col {pellet.col}')
            self.pellets.numEaten += 1
            self.updateScore(pellet.points)
            if self.pellets.numEaten == 30:
                self.ghosts.inky.startNode.allowAccess(RIGHT, self.ghosts.inky)
            if self.pellets.numEaten == 70:
                self.ghosts.clyde.startNode.allowAccess(LEFT, self.ghosts.clyde)
            self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET:
                self.ghosts.startFreight()
            if self.pellets.isEmpty():
                self.flashBG = True
                self.hideEntities()
                self.pause.setPause(pauseTime=3, func=self.nextLevel)

    def checkGhostEvents(self):
        for ghost in self.ghosts:
            if self.pacman.collideGhost(ghost):
                if ghost.mode.current is FREIGHT:
                    self.pacman.visible = False
                    ghost.visible = False
                    self.updateScore(ghost.points)                  
                    self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(pauseTime=1, func=self.showEntities)
                    ghost.startSpawn()
                    self.nodes.allowHomeAccess(ghost)
                elif ghost.mode.current is not SPAWN:
                    if self.pacman.alive:
                        self.lives -=  1
                        self.lifesprites.removeImage()
                        self.pacman.die()               
                        self.ghosts.hide()
                        if self.lives <= 0:
                            self.textgroup.showText(GAMEOVERTXT)
                            self.pause.setPause(pauseTime=3, func=self.restartGame)
                        else:
                            self.pause.setPause(pauseTime=3, func=self.resetLevel)
                            
    @ui.in_background
    def checkFruitEvents(self):
        if self.pellets.numEaten == 30 or self.pellets.numEaten == 140:
            if self.fruit is None:
                self.fruit = Fruit(self.nodes.getNodeFromTiles(9, 20), self.level)
        if self.fruit is not None:
            if self.pacman.collideCheck(self.fruit):
                self.updateScore(self.fruit.points)
                self.textgroup.addText(str(self.fruit.points), WHITE, self.fruit.position.x, self.fruit.position.y, 8, time=1)
                fruitCaptured = False
                for fruit in self.fruitCaptured:
                    if fruit.get_offset() == self.fruit.image.get_offset():
                        fruitCaptured = True
                        break
                if not fruitCaptured:
                    self.fruitCaptured.append(self.fruit.image)
                self.fruit = None
            elif self.fruit.destroy:
                self.fruit = None

    def showEntities(self):
        self.pacman.visible = True
        self.ghosts.show()

    def hideEntities(self):
        self.pacman.visible = False
        self.ghosts.hide()

    def nextLevel(self):
        self.showEntities()
        self.level += 1
        self.pause.paused = True
        self.startGame()
        self.textgroup.updateLevel(self.level)

    def restartGame(self):
        self.lives = 5
        self.level = 0
        self.pause.paused = True
        self.fruit = None
        self.startGame()
        self.score = 0
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
        self.fruitCaptured = []

    def resetLevel(self):
        self.pause.paused = True
        self.pacman.reset()
        self.ghosts.reset()
        self.fruit = None
        self.textgroup.showText(READYTXT)

    def updateScore(self, points):
        self.score += points
        self.textgroup.updateScore(self.score)

    def render(self, update_display=True):
        #self.screen.blit(self.background, (0, 0))
        #self.nodes.render(self.screen)
        #clear pellets, pacman and ghosts
        
        for child in self.screen.children[self.fixed_nodes:]:
            child.remove_from_parent()
          
        self.pellets.render(self.screen)
        if self.fruit is not None:
            self.fruit.render(self.screen)
        self.pacman.render(self.screen)
        self.ghosts.render(self.screen)
        self.textgroup.render(self.screen, self.count > 0)
        self.lifesprites.render(self.screen)

        for i, item in enumerate(self.fruitCaptured):
            Tile(item, row=0, col=NCOLS - (i+1)*2, scale=4, parent=self.screen)
        
        self.count += 1
        


if __name__ == "__main__":
    run(GameController())
    











