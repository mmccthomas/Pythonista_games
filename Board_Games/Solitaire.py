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
from types import SimpleNamespace
from freecell.freecell import Freecell, Card
import freeCellSolver.FreeCellSolver as solver
cardsize = (140,190)
X_OFF = 80


class SolitaireGame(Scene):
  """
  The main game code for Tetris
  """
  def __init__(self):
      self.read_pickle = True
      self.newgame = Freecell()
      self.newgame.print_game()
      Scene.__init__(self)
      self.setup()
      
      
  def setup_ui(self):
    # Root node for UI elements
    w,h = get_screen_size()
    self.ui_root = Node(parent=self)
  
    self.score_label = LabelNode('0', font=('Avenir Next', 20),
                                  position=(60, 10),
                                  parent=self)
    self.line_label = LabelNode(str(self.line_timer_current), font=('Avenir Next', 20), position=(120, 10), parent=self)
    LabelNode('Foundation', font=('Avenir Next', 30), position=(900, 970), parent=self)
    LabelNode('Freecells', font=('Avenir Next', 30), position=(300, 970), parent=self)
    
    pause_button = SpriteNode('iow:pause_32', position=(32, h - 36),
                              parent=self)
    self.debug = LabelNode('FreeCell', font=('Avenir Next', 20), 
                                    position=(screen_width / 2, 10),
                                    parent=self)
                    
    for col in range(8):
        # column labels    
        LabelNode(str(col+1), font=('Avenir Next', 30), position=(col*(cardsize[0]+10)+X_OFF, 730), parent=self)      
        # foundation labels         
        LabelNode(str(col%4+1), font=('Avenir Next', 20), position=(col*(cardsize[0]+10)+25, 925), parent=self)     
        i =['\u2660', '\u2665', '\u2663',  '\u2666']                      
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
          self.all_cards.append(card)        

                                                                
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
    self.game_str = self.save_game()
    
  def show_cards(self):
      # clear all positions
      for card in self.all_cards:
          card.tileobject.position = (0,0)
          
      #redraw piles
      for col, pile in enumerate(self.newgame.pile):
        for row, card in enumerate(reversed(pile)):
          card.tileobject.position =self.pile_positions[col][len(pile)-row]
          card.tileobject.z_position=20-int(2*row+1)
        
      #redraw foundations  
      #print('foundation',self.newgame.foundation)  
      for col, found in enumerate(self.newgame.foundation):
        if found != [] and found != [None]:
            found[-1].tileobject.position = self.foundation_positions[col+4]
          
            for item in found[:-1]:
              item.tileobject.remove_from_parent()
              #item.tileobject = None #position = self.foundation_positions[col+4]
              #card.tileobject.z_position=int(2*row+1)
              
      #redraw freecells 
      #print('freecell', self.newgame.cell)        
      for col, cell in enumerate(self.newgame.cell):
      	 if cell != [] and cell != [None]:
            for item in cell:
              item.tileobject.position = self.foundation_positions[col]
              
  def save_game(self):
    # save in format for solver to read
    # save game.txt in format
    # xxx xxx xxx xxx   # foundations: S, H, C, D
    # yyy yyy yyy yyy   # freecells: 0, 1, 2, 3
    # cascade[0]
    # cascade[1]
    #
    # cascade[7]
    # Example:

    # None None A 2
    # 6d 5c None None
    # 6c 8s Jc 4s 9s 7c Kh
    def convert_foundation(foundation):
      # find highest card in each pile
      # assumes last card is highest
      # in order S, H, C, D
      order = 'shcd'
      f_order = ['None', 'None', 'None', 'None']
      for f in foundation:
        if f:
         card = f[-1]
         f_order[order.index(card.suit)] = card.face
      return ' '.join(f_order)
    
    g = self.newgame
    s = '\n'.join([convert_foundation(g.foundation),
                   ' '.join([c[-1].face + c[-1].suit if c else 'None' for c in g.cell ]),
                   '\n'.join([' '.join([p.face + p.suit for p in pile]) for pile in g.pile])])
    
    s = s.replace('T', '10')
    #with open('freeCellSolver/game.txt', 'w') as f:
    #  f.write(s)
    return s   
        
  def tuple_to_card(self, t):
    # convert tuple t (face_no, suit_no) to card object
    
    if t is None:
    	return None
    face, suit = t
    if face is None:
    		return None
    face_index = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
                   'J': 11, 'Q': 12, 'K': 13}
    rev_index = {v:k for k, v in face_index.items()}
    suit_range = ['s', 'h', 'c', 'd']
    for card in self.all_cards:
    	 if card.face == rev_index[face] and card.suit == suit_range[suit]:
            return card
    
  @ui.in_background
  def read_moves(self):
      # read moves file to replay solution
      # moves file is zero based index
      g = self.newgame  
      import pickle
      if self.read_pickle:
        with open('statefile.pkl', 'rb') as f:         
         moves, states = pickle.load(f)
        print(len(states))
        for index, state in enumerate(states):
          g.foundation = [[self.tuple_to_card((f, i))] for i, f in enumerate(state[0])]
          g.cell = [[self.tuple_to_card(t)] for t in state[1]]
          g.pile =  [[self.tuple_to_card(t) for t in pile]  for pile in state[2]]
          print('index', index)
          g.print_game()
          self.show_cards()
          sleep(0.5)
        # finish by showing completed hand
        g.foundation = [[self.tuple_to_card((13, i))] for i in range(4)]
        g.cell = [[None] for t in range(4)]
        g.pile =  [[] for i in range(8)]
        g.print_game()
        self.show_cards()
        return
        
      def f_col(card):
         # find column number for foundation string """
         return 'shcd'.index(card.suit)
             
      def empty_cell():
        for i in range(4):
          if len(g.cell[i]) == 0:
            return i
        return 0
        
      def supermove(x1,x2,n):
        # move a sequence onto another pile
        # only possible if free cell and empty column
        # assume coputation is correct
        # x1 = start pile, x2 = end pile
        # n = no to move
        # compute empty piles
        npile = sum([len(p) == 0 for p in g.pile])
        nfree = sum([len(c) == 0 for c in g.cell])
        #if n > (npile + nfree +1):
        #    raise IndexError ('supermove not possible, no free cells')
        x1 -= 1
        x2 -= 1
        move_cards = g.pile[x1][-n:]
        g.pile[x1] = g.pile[x1][:-n]
        g.pile[x2].extend(move_cards)
        
      def automove():
        # automatically move Ace or 2  to foundation if possible
        while True:
            mustCheckAgain = False
            for i, p in enumerate(g.pile):
                if p:                                    
                  x1 = i
                  x2 = f_col(g.pile[x1][-1]) + 1
                  if g.pile[x1][-1].face in ['A2']:
                     error = g.p2f(x1+1,x2)
                     if not error:
                        mustCheckAgain = True        
            if not mustCheckAgain:
                break
        
            
      with open('moves.txt', 'r') as f:
          moves = f.read()
     
      moves = moves.split('\n')
      for index, move in enumerate(moves):
        items = move.split(' ')  
        print(f'{index=}, {move=}') 
        if move:
          x1 = int(items[1]) + 1
          if g.pile[x1-1]:
              print(f'last pile {g.pile[x1-1][-1]}') # freecell {g.cell[x1][-1]}')
        match (items[0], len(items)):
            case ('cx', 2):              
              x2 = empty_cell() +1
              error = g.p2c(x1,x2)
            case ('cf', 2):
              x2 = f_col(g.pile[x1-1][-1]) + 1
              error = g.p2f(x1,x2)
            case ('cc', 3):
              x2 = int(items[2]) + 1
              error = g.p2p(x1,x2)
            case ('cc', 4):
              x2 = int(items[2]) + 1         
              n = int(items[3])
              error = supermove(x1, x2, n)
            case ('xc', 3):
              x2 = int(items[2]) + 1
              error = g.c2p(x1,x2)
            case ('xf', 2):
              x2 = f_col(g.cell[x1-1][-1]) + 1
              error = g.c2f(x1,x2)
        if error:
          print(f'Error, {index}, {error}')
        automove()
        g.print_game()
        self.show_cards()
        sleep(0.25)
      print('finished')
      print(self.newgame.foundation)
      print([len(f) for f in self.newgame.foundation])
      self.show_start_menu()

        
  @ui.in_background
  def solve(self):
    # call solver using game.txt  
    #print(self.newgame)
    print('solve this', self.game_str)
    solver.main(SimpleNamespace(**{'gameFile': 'None', 
                                   'moveFile': 'moves.txt', 
                                   'searchType': 1, 
                                   'startFile': self.game_str,
                                   'cap': 1000000}))
    self.read_moves()  
    print(self.newgame.foundation)
    print([len(f) for f in self.newgame.foundation])
    if self.newgame.win_game():
          dialogs.hud_alert('Win game')
          self.show_start_menu()
      
  def show_start_menu(self):
    self.pause_game()
    self.menu = MenuScene('Main Menu', '', ['Continue', 'New Game', 'Complete', 'Quit'])
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
    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.show_start_menu()
      
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
    # self.score_label.text = self.decode_position(touch)
  
  def touch_ended(self, touch):
    if self.selected:
      self.end = self.decode_position(touch)
      # self.debug.text = f'card {self.start} to {self.end}'
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
        print(self.newgame.foundation)
        print(self.newgame.cell)
        self.newgame.print_game()
        self.show_cards()
        self.game_str = self.save_game()
        # self.debug.text = str(error)
        if self.newgame.win_game():
          dialogs.hud_alert('Win game')
                    
  def menu_button_selected(self, title):
    """ choose to play again or quit """
    #Continue', 'New Game', 'Complete', 'Quit
    if title.startswith('Continue'):
        self.dismiss_modal_scene()
        self.menu = None
        self.resume_game()
    elif title.startswith('New Game'):
        self.dismiss_modal_scene()
        self.newgame = Freecell()
        self.show_cards()
        self.game_str = self.save_game()
    
    elif title.startswith('Complete'):
        self.dismiss_modal_scene()
        self.solve()
        
        self.menu = None
        self.resume_game()
    else:
        # quit
        self.view.close()

           

if __name__ == '__main__':
  run(SolitaireGame(), PORTRAIT, show_fps=False)
























