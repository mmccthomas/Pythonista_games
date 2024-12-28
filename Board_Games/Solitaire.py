# TODO fix post completion code
# allow resolve after solve
# still stops before end

""" Solitaire
"""
import base_path
base_path.add_paths(__file__)
from scene import *
from gui.game_menu import MenuScene
from time import sleep
import traceback
import dialogs
from types import SimpleNamespace
from freecell.freecell import Freecell
from  freeCellSolver.free_solver import Solver

w,h = get_screen_size()
# w, h = 1112, 834
# w, h = 852, 393
if w == 1366:
   #ipad13
   cardsize = Size(140,190)
elif w == 1112:
    #ipad
    cardsize = Size(114, 155)
elif w == 852:
    # iphone landscape
    cardsize = Size(43, 59)
TOP_GAP = 80
MID_GAP = 20
X_OFF = 10
MOVE_SPEED = 0.001
INITIAL_LINE_SPEED = 1
A = Action
card_indexes = 'A23456789TJQK'

class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, tile, x=0, y=0, **args):
    SpriteNode.__init__(self, tile, **args)   
    self.size = cardsize
    self.anchor_point = 0,0 
    self.number = 1
    self.set_pos((x, y))
    
  def set_pos(self, xy, moveslow=True):
    """
    Sets the position of the tile in the grid.
    """      
    pos = Vector2()
    pos.x, pos.y  = xy
    if self.position != xy and pos != (-200, 0) and moveslow:
      fast = f'{pos} slow move'
      self.run_action(A.sequence(
        A.move_to(pos.x,pos.y, MOVE_SPEED), 
        A.wait(MOVE_SPEED), 
        A.remove)) 
      #sleep(MOVE_SPEED)
    else:
        fast = None
    self.position = pos
    return fast

        
class SolitaireGame(Scene):
  """
  The main game code for Tetris
  """
  def __init__(self):
      self.read_pickle = True
      self.debug_print = True
      self.newgame = Freecell()
      self.newgame.print_game()
      Scene.__init__(self)
      self.setup()
           
  def setup_ui(self):
    # place all gui elements
    # scale to device
    w,h = get_screen_size()
    #w, h = 1112, 834
    #w, h = 852, 393
    
    # define all card locations
    cx, cy = cardsize
    
    foundation_start_y = h - cy - TOP_GAP
    pile_start_y = foundation_start_y - cy - MID_GAP
    # foundation and freecell positions, centre of card
    self.fpos = []
    self.foundation_bboxes = []
    self.pile_positions = []
    
    for i in range(8):
       self.fpos.append(Point(i*(cx+10)+X_OFF, foundation_start_y))
       self.foundation_bboxes.append(Rect(*self.fpos[-1], *cardsize))
       
    self.all_boxes = self.foundation_bboxes
    
    for col in range(8):
        self.pile_positions.append([Point(self.fpos[col].x, pile_start_y - row * cy / 3) for row in range(18)])
        
    self.all_boxes.extend([Rect(*p, *cardsize) for pile in self.pile_positions for p in pile])
    
    # now build gui
    # Root node for UI elements
    self.ui_root = Node(parent=self)
  
    self.score_label = LabelNode('0', font=('Avenir Next', 20),
                                  position=(60, 10),
                                  parent=self)
    self.line_label = LabelNode('Time 0', font=('Avenir Next', 30), 
                                position=(w/2,h), 
                                anchor_point=(1,1),parent=self)
    LabelNode('Foundation', font=('Avenir Next', 30), 
              position=(self.fpos[6].x, self.fpos[0].y+cy+20), 
              anchor_point=(0.5, 0), parent=self)
    LabelNode('Freecells', font=('Avenir Next', 30), 
              position=(self.fpos[2].x, self.fpos[0].y+cy+20),
              anchor_point=(0.5, 0), parent=self)
    
    SpriteNode('iow:pause_32', position=(32, h - 36),
                              parent=self)
    self.debug = LabelNode('FreeCell', font=('Avenir Next', 20), 
                                    position=(w / 2, 20),
                                    anchor_point=(1, 0),
                                    parent=self)
                    
    for col in range(8):
        # column labels    
        LabelNode(str(col+1), font=('Avenir Next', 20), 
                  position=(self.fpos[col].x + cx/2, foundation_start_y-MID_GAP), 
                  anchor_point=(0.5, 0.5),
                  parent=self)      
        # foundation labels         
        LabelNode(str(col%4+1), font=('Avenir Next', 20), 
                  position=(self.fpos[col].x + cx/2, self.fpos[col].y + cy+5), 
                  anchor_point=(0,0), parent=self)     
                         
    
    # freecell and foundation outlines
    icons = ['\u2660', '\u2665', '\u2663',  '\u2666']      # S, H, C, D        
    for i, f in enumerate(self.fpos):
        ShapeNode(path=ui.Path.rounded_rect(0,0,cx+8, cy+8, 10), 
                  position=f-(4,4),
                  fill_color='red' if i<4 else 'blue', stroke_color='white',
                  z_position=0, alpha=0.95, 
                  anchor_point = (0, 0),
                  parent=self)
        LabelNode(icons[i%4], font=('Avenir Next', cx/2), 
                  position=(self.fpos[i%4+4].x +cx/2, foundation_start_y+cy/2), 
                  anchor_point = (0.5, 0.5),
                  z_position=10, parent=self)          
    
    
  def define_cards(self):
      try:
        for card in self.all_cards:
          card.tileobject.remove_from_parent()
      except (AttributeError):
          pass
      # flat list
      self.all_cards = sum(self.newgame.pile, [])
        
      [card.set_tileobject(Tile(card.image, 0, 0,
                                z_position=1,
                                parent=self))
       for col in self.newgame.pile
       for card in col]
       
                                                          
  def setup(self):
    #       
    self.line_timer = INITIAL_LINE_SPEED
    self.timer = 0    
    self.score = 0
    # only set up fixed items once
    try:
      a = self.score_label.text
    except AttributeError:
      self.setup_ui()
    self.define_cards()
    self.show_cards(moveslow=False)
    self.game_str = self.save_game()
    self.resume_game()
    self.debug.text = 'FreeCell'
  
  def show_cards(self, moveslow=True):
      # for solved games, foundation is only top card.
      # we need to delete lower cards
      #for card in self.all_cards:
      #   card.tileobject.set_pos((-200,0))
      #redraw piles
      for col, pile in enumerate(self.newgame.pile):
        for row, card in enumerate(reversed(pile)):
          card.tileobject.set_pos(self.pile_positions[col][len(pile)-row], moveslow=moveslow)
          card.tileobject.z_position=20-int(2*row+1)
          
        
      #redraw foundations
      # only show top one in each pile  
      for col, found in enumerate(self.newgame.foundation):
        if found != [] and found != [None]:
            top_card = found[-1]
            top_card_face, top_card_suit = (card_indexes.index(top_card.face)+1, 'shcd'.index(top_card.suit))
            top_card.tileobject.set_pos(self.fpos[col+4], moveslow=moveslow)
            
            # delete cards below top found
            sleep(MOVE_SPEED)
            for face_no in range(top_card_face,1,-1):
              try:
                lower_card = self.tuple_to_card((face_no-1, top_card_suit))                
                lower_card.tileobject.z_position = -1
                lower_card.tileobject.remove_from_parent()
                self.all_cards.remove(lower_card)
                lower_card.tileobject = None 
              except (AttributeError):
                pass
              
      #redraw freecells       
      for col, cell in enumerate(self.newgame.cell):
         if cell:
            for item in cell:
              item.tileobject.set_pos(self.fpos[col], moveslow=moveslow)
              
  def save_game(self):
    # save in format for solver to read
    
    def convert_foundation(foundation):
      # find highest card in each pile
      # assumes last card is highest
      # in order S, H, C, D
      order = 'shcd'
      f_order = ['None', 'None', 'None', 'None']
      for f in foundation:
        if f:
         card = f[-1]
         if card:
           f_order[order.index(card.suit)] = card.face
      return ' '.join(f_order)
    
    g = self.newgame
    cstr = []
    for c in g.cell:
      if not c:
        str = 'None'
      else:
        str = c[-1].face + c[-1].suit
      cstr.append(str)
    s = '\n'.join([convert_foundation(g.foundation),
                   ' '.join([c[-1].face + c[-1].suit if c else 'None' for c in g.cell]),
                   '\n'.join([' '.join([p.face + p.suit for p in pile]) for pile in g.pile])])    
    s = s.replace('T', '10')
    return s   
        
  def tuple_to_card(self, t):
    # convert tuple t (face_no, suit_no) to card object
    try:    
        face, suit = t        
        face_index = {'A': 1, '2': 2, '3': 3, '4': 4, 
                      '5': 5, '6': 6, '7': 7, '8': 8, 
                      '9': 9, 'T': 10,'J': 11, 'Q': 12, 'K': 13}
        rev_index = {v:k for k, v in face_index.items()}
        suit_range = ['s', 'h', 'c', 'd']
        for card in self.all_cards:
           if card.face == rev_index[face] and card.suit == suit_range[suit]:
                return card
    except (IndexError, AttributeError, TypeError, KeyError):
       return None
          
  # @ui.in_background             
  def decode_state(self, index, state):
      # convert from solver state to freecell properties
      # print game and move cards
      g = self.newgame  
      foundation, freecells, cascade = state
      g.foundation = [[self.tuple_to_card((f, i))] if f else [] for i, f in enumerate(foundation)]
      # need empty g.cell to be [], not [None]
      g.cell = [[self.tuple_to_card(t)] if t else [] for t in freecells]
      g.pile =  [[self.tuple_to_card(t) for t in pile] if pile else [] for pile in cascade]
      if self.debug_print:
          print('index', index)
          g.print_game()
      self.show_cards()
      sleep(MOVE_SPEED)
      
  @ui.in_background         
  def read_moves(self):
      # read moves file which is a pickled list of tuples for each move
      # moves file is zero based index
      global MOVE_SPEED
      MOVE_SPEED = 0.2
      g = self.newgame  
      import pickle
      if self.read_pickle:
        with open('statefile.pkl', 'rb') as f:         
         moves, states = pickle.load(f)
        print(f'statefile.pkl has {len(moves)} states')
        for index, state in enumerate(states):
            self.decode_state( index, state)
        # finish is accomplished by hand
        g.print_game()               
        self.debug.text = 'Solve Complete - finish manually'
        
  def solve(self):
    # call solver using game.txt  
    print('solve this\n', self.game_str)
    try:
        Solver().solve(SimpleNamespace(**{'gameFile': 'None', 
                                       'moveFile': 'moves.txt', 
                                       'searchType': 1,
                                       'startFile': self.game_str,
                                       'cap': 1000000,
                                       'noprint': True}))
        self.read_moves()  
        all_kings = all([card[-1].face=='K' for card in self.newgame.foundation])
        if self.newgame.win_game() or all_kings:
              dialogs.hud_alert('Win game')
              self.show_start_menu()
        
        
    except RuntimeError:         
        self.show_start_menu('Deck could not be solved')
    except Exception:
       print(traceback.format_exc())    
     
  def show_start_menu(self, title=''):
    self.pause_game()
    self.menu = MenuScene('Main Menu', title,  ['Continue', 'New Game', 'Complete', 'Quit'])
    self.present_modal_scene(self.menu)  
          
  def update_score(self):
    self.score_label.text = str(self.score)    
    self.line_label.text = f'Time {self.timer}'     
  
  def did_change_size(self):
    pass    
    
  def pause_game(self):
    self.paused = True
    
  def resume_game(self):
    self.paused = False    
    
  def next_game(self):
    self.pause_game()
    self.show_start_menu()     
             
  def update(self):
    # dt is provided by Scene
    self.line_timer -= self.dt    
    # 
    if self.line_timer <= 0:
      self.line_timer = INITIAL_LINE_SPEED
      self.timer += 1
      self.update_score()
      
  def touch_began(self, touch):
    self.selected = None
    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.show_start_menu()
      
    # start will be c1-8, f1-4, p1-4
    self.start = self.decode_position(touch)
    for pile in self.newgame.pile:
        for card in reversed(pile):
          try:
              if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card.tileobject
                return
          except AttributeError:
            pass
    for cell in self.newgame.cell:
        for card in reversed(cell):
          try:
              if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card.tileobject
                return
          except AttributeError:
            pass
            
  def touch_moved(self, touch):
    if self.selected:
      self.selected.position = touch.location - (cardsize/2)
      self.score_label.text = self.decode_position(touch)
  
  def touch_ended(self, touch):
    if self.selected:
      self.end = self.decode_position(touch)
      #self.selected.position = touch.location
      for pos in self.all_boxes:
        if pos.contains_point(touch.location):
          self.selected.position = (pos[0], pos[1])
          break
      # self.debug.text = f'card {self.start} to {self.end}'
      #print(self.debug.text)
      self.move(self.start, self.end)
      self.show_cards()     
           
  def decode_position(self, touch):
      # find if touch in pile, cell or foundation
      x = max(1, min(8, int((touch.location.x) / (cardsize[0]+10)) + 1))
      # y is True for goundation or freecell
      y = (touch.location.y - self.fpos[0].y-50) > 0      
      if  not y:
          return  f'p{x}'
      elif x < 5:
          return f'c{x}'
      else:
          return f'f{x-4}'
          
  @ui.in_background 
  def move(self, start, end):
        global MOVE_SPEED 
        print(start, end)
        MOVE_SPEED = 0.001
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
        if error:
            print(f'from {x1} to {x2} {error=} cells={self.newgame.cell}, found={self.newgame.foundation}')
        self.newgame.print_game()
        self.show_cards()
        self.game_str = self.save_game()
        # self.debug.text = str(error)
        kings = []
        for card in self.newgame.foundation:
          if card and card != [None]:
             kings.append(card[-1].face=='K')
          else:
              kings.append(False)
        all_kings = all(kings)
        if all_kings:
          dialogs.hud_alert('Win game')
          self.show_start_menu()
                    
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
        self.setup()       
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











