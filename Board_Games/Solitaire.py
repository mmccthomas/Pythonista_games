""" Solitaire
"""
import os
import sys
import base_path
base_path.add_paths(__file__)
from demolition_config import *
from scene import *
from gui.game_menu import MenuScene
from ui import Path
import random
from random import uniform as rnd
import math
from time import sleep
import dialogs
from freecell.freecell import Freecell
cardsize = (140,190)
X_OFF = 80


class SolitaireGame(Scene):
  """
  The main game code for Tetris
  """
  def __init__(self):
      self.newgame = Freecell()
      self.newgame.print_game()
      Scene.__init__(self)
      self.setup()
      
      
  def setup_ui(self):
    # Root node for UI elements
    self.ui_root = Node(parent=self)
  
    self.score_label = LabelNode('0', font=('Avenir Next', 20),
                                  position=(60, 10),
                                  parent=self)
    self.line_label = LabelNode(str(self.line_timer_current), font=('Avenir Next', 20), position=(120, 10), parent=self)
    LabelNode('Foundation', font=('Avenir Next', 30), position=(900, 970), parent=self)
    LabelNode('Freecells', font=('Avenir Next', 30), position=(300, 970), parent=self)
    self.debug = LabelNode('Demolition', font=('Avenir Next', 20), 
                                    position=(screen_width / 2, 10),
                                    parent=self)
                    
    for col in range(8):
        # column labels    
        LabelNode(str(col+1), font=('Avenir Next', 30), position=(col*(cardsize[0]+10)+X_OFF, 730), parent=self)      
        # foundation labels         
        LabelNode(str(col%4+1), font=('Avenir Next', 20), position=(col*(cardsize[0]+10)+25, 925), parent=self)     
        i =['\u2660', '\u2665', '\u2666','\u2663',  ]                      
        LabelNode(i[col%4], font=('Avenir Next', 80), position=((col%4+4)*(cardsize[0]+10)+85, 850), z_position=10, parent=self)          
    # foundation and freecell positions
    self.foundation_positions = []
    self.foundation_bboxes = []
    self.pile_positions = []
    for i in range(8):
       self.foundation_positions.append((i*(cardsize[0]+10)+X_OFF, 850))
       self.foundation_bboxes.append(Rect(*self.foundation_positions[-1], *cardsize))
       ShapeNode(path=ui.Path.rounded_rect(0,0,cardsize[0], cardsize[1], 10), 
                 position=self.foundation_positions[-1],
                 fill_color='red' if i<4 else 'blue', stroke_color='white',
                 z_position=0,alpha=0.95, 
                 parent=self)
    
    for col in range(8):
        self.pile_positions.append([(col*(cardsize[0]+10)+X_OFF, 680-row*60) for row in range(13)])
    #print(f'{self.foundation_positions=}')
    self.all_cards = []
    for col in self.newgame.pile:
        for card in col:
          card.tileobject = SpriteNode(card.image, position=(0,0),
                                       z_position=1,parent=self)
          self.all_cards.append(card.tileobject)        

                                                                
  def setup(self):
    #self.background_color = COLORS["bg"]
  
    # Root node for all game elements
    
    
    self.line_timer = INITIAL_LINE_SPEED
    self.line_timer_store = INITIAL_LINE_SPEED
    self.line_timer_current = INITIAL_LINE_SPEED
    self.index = 1    
    self.score = 0
    self.level = 1
    # only set up fixed items once
    try:
      a = self.score_label.text
    except AttributeError:
      self.setup_ui()
    self.show_cards()
    self.save_game()
    
  def show_cards(self):
      # clear all positions
      for card in self.all_cards:
          card.position = (0,0)
          
      #redraw piles
      for col, pile in enumerate(self.newgame.pile):
        for row, card in enumerate(reversed(pile)):
          card.tileobject.position =self.pile_positions[col][len(pile)-row]
          card.tileobject.z_position=20-int(2*row+1)
        
      #redraw foundations  
      #print('foundation',self.newgame.foundation)  
      for col, found in enumerate(self.newgame.foundation):
        if found:
            found[-1].tileobject.position = self.foundation_positions[col+4]
          
            for item in found[:-1]:
              item.tileobject.remove_from_parent()
              #item.tileobject = None #position = self.foundation_positions[col+4]
              #card.tileobject.z_position=int(2*row+1)
              
      #redraw freecells 
      #print('freecell', self.newgame.cell)        
      for col, cell in enumerate(self.newgame.cell):
          for item in cell:
              item.tileobject.position = self.foundation_positions[col]
              
  def save_game(self):
  	# save in format for solver to read
    # save game.txt in format
    #xxx xxx xxx xxx   # foundations: S, H, D, C
    #yyy yyy yyy yyy   # freecells: 0, 1, 2, 3
    #cascade[0]
    #cascade[1]
    #...
    #cascade[7]
    #Example:

    #None None A 2
    #6d 5c None None
    #6c 8s Jc 4s 9s 7c Kh
    def convert_foundation(foundation):
    	
    	return s
    for found in self.newgame.foundation:
    	pass
    for cell in self.newgame.cell:
    	pass
    for pile in self.newgame.pile:
    	pass
    g = self.newgame
    s = ''
    for i in range(4):
        if g.foundation[i]:
            rankIndex = g.foundation[i]-1
            rank = all_ranks[rankIndex]
        else:
            rank = None
        s += str(rank) + ' '
    s += '\n'
    for i in range(4):
        s += str(g.cell[i]) + ' '
    s += '\n'
    for i in range(8):
        for j in range(len(g.pile[i])):
                s += str(g.pile[i][j])[:2] + ' '
        s += '\n'
    s = s.replace('T', '10')
    with open('game.txt', 'w') as f:
    	f.write(s)
    return s       
    
  def read_moves(self):
  	  # read moves file to replay solution
  	  pass
  	         
  def show_start_menu(self):
    self.pause_game()
    self.menu = MenuScene('New Game?', '', ['Play', 'Quit'])
    self.present_modal_scene(self.menu)  
         
  
  def update_score(self):
    self.score_label.text = str(self.score)    
    self.line_label.text = str(self.line_timer_current)            
  
  def did_change_size(self):
    pass    
  
  def check_for_finish(self):
    """check if new piece is at start location when collision detected"""
    for t in self.get_tiles():
      if t.row >= ROWS-1:
        return True
    return False 
    
  def pause_game(self):
    self.paused = True
    '''
    self.ball_timer = 100000 # pause next ball move
    # store line timer
    self.line_timer_store = self.line_timer
    self.line_timer = 10000 # pause next line
    '''
  def resume_game(self):
    self.paused = False
    '''
    self.fall_speed = INITIAL_FALL_SPEED 
    self.ball_timer = self.fall_speed
    self.line_timer = self.line_timer_store
    '''
    
  def next_game(self):
    self.pause_game()
    self.show_start_menu()     
              
  def update(self):
    # dt is provided by Scene
    self.line_timer -= self.dt
    
    # Check for intersection and spawn a new piece if needed  
      
    # line creation
    if self.line_timer <= 0:
      self.line_timer = self.line_timer_current
       
  def touch_began(self, touch):
    self.selected = None
    self.sel_card = None
    # start will be c1-8, f1-4, p1-4
    self.start = self.decode_position(touch)
    for pile in self.newgame.pile:
        for card in reversed(pile):
          if card.tileobject.bbox.contains_point(touch.location):
            self.selected = card.tileobject
            self.sel_card = card
            return
    for cell in self.newgame.cell:
        for card in reversed(cell):
          if card.tileobject.bbox.contains_point(touch.location):
            self.selected = card.tileobject
            self.sel_card = card
            return
                 
  def touch_moved(self, touch):
    if self.selected:
      self.selected.position = touch.location
    self.score_label.text = self.decode_position(touch)
  
  def touch_ended(self, touch):
    if self.selected:
      self.end = self.decode_position(touch)
      self.debug.text = f'card {self.start} to {self.end}'
      #print(self.debug.text)
      self.move(self.start, self.end)
      self.show_cards()     
           
  def decode_position(self, touch):
      # find if touch in pile, cell or foundation
      x = int((touch.location.x) / (cardsize[0]+10)) + 1
      # y is True for goundation or freecell
      y = (touch.location.y - 750) > 0      
      if  not y:
          return  f'p{x}'
      elif x < 5:
          return f'c{x}'
      else:
          return f'f{x-4}'
          
  @ui.in_background 
  def move(self, start, end):
        """
        print("\t p2f #P #F -- Pile to Foundation 1: ")
        print("\t e.g. Pile 2 to Foundation: p2f 2 1 ")
        print("\t p2p #P #P -- Pile to Pile: ")
        print("\t e.g. Pile 2 to Pile 1: p2f 2 1 ")
        print("\t p2c #P #C -- Pile to Cell: ")
        print("\t e.g. Pile 2 to Cell 1: p2c 2 1 ")
        print("\t c2p #C #P -- Cell to Pile: ")
        print("\t e.g. Cell 2 to Pile 1: c2p 2 1 ")
        print("\t c2f #C #F -- Cell to Foundation: ")
        print("\t e.g. Cell 2 to Foundation 1: c2f 2 1 ")
        """
        print(start, end)
        x1, x2 = int(start[1]), int(end[1])
        match (start[0], end[0]):
          case ('p','f'):
            error = self.newgame.p2f(x1,x2)
          case ('p', 'p'):
            error = self.newgame.p2p(x1,x2)
          case ('p', 'c'):
            error = self.newgame.p2c(x1,x2)
          case ('c','p'):
            error = self.newgame.c2p(x1,x2)
          case ('c', 'f'):
            error = self.newgame.c2f(x1,x2)
        
        self.newgame.print_game()
        self.show_cards()
        self.save_game()
        self.debug.text = str(error)
        if self.newgame.win_game():
          dialogs.hud_alert('Win game')
                    
  def menu_button_selected(self, title):
    """ choose to play again or quit """
    if title.startswith('Play'):
      # start again
      self.dismiss_modal_scene()
      self.menu = None
      self.resume_game()
      self.clear_tiles()
      self.ball.remove_from_parent()  
      self.setup()
      self.score_label.text = '0'
    else:
      # quit
      self.view.close()

            


if __name__ == '__main__':
  run(SolitaireGame(), PORTRAIT, show_fps=False)
















