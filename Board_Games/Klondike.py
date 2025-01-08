""" Klondike Solitaire

"""
import base_path
from scene import *
from time import sleep
import traceback
import dialogs
from copy import deepcopy
from types import SimpleNamespace
base_path.add_paths(__file__)
from gui.game_menu import MenuScene
from freecell.klondike_solver import Game, get_solvable, Move, State

w, h = get_screen_size()
# w, h = 1112, 834
# w, h = 852, 393
if w == 1366:
   # ipad13
   cardsize = Size(114, 155)
elif w == 1112:
    # ipad
    cardsize = Size(114, 155)
elif w == 852:
    # iphone landscape
    cardsize = Size(43, 59)
TOP_GAP = 80
MID_GAP = 20
X_OFF = 10
MOVE_SPEED = 0.001
INITIAL_LINE_SPEED = 1

STOCK = 0
WASTE = 1
FOUNDATION = 2
TABLEAU = 6
TABLEAU_END = 12

A = Action
card_indexes = 'A23456789TJQK'


class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, tile, x=0, y=0, **args):
    SpriteNode.__init__(self, tile, **args)
    self.size = cardsize
    self.anchor_point = 0, 0
    self.number = 1
    self.set_pos((x, y))
    
  def set_pos(self, xy):
    """
    Sets the position of the tile in the grid.
    """
    pos = Vector2()
    pos.x, pos.y = xy
    if self.position != xy:
      self.run_action(A.sequence(
        A.move_to(pos.x, pos.y, MOVE_SPEED),
        A.wait(MOVE_SPEED),
        A.remove))
      # sleep(MOVE_SPEED
    self.position = pos

        
class KlondikeGame(Scene):
  """
  The main game code for Klondike
  """
  def __init__(self):
      """ define newgame with random deck """
      self.debug_print = False
      self.inbuilt_cards = False
      self.face_index = {'A': 1, '2': 2, '3': 3, '4': 4,
                         '5': 5, '6': 6, '7': 7, '8': 8,
                         '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13}
      self.rev_index = {v: k for k, v in self.face_index.items()}
      self.suit_range = ['s', 'h', 'c', 'd']
      self.suit_name = {'c': 'Clubs', 'h': 'Hearts', 's': 'Spades', 'd': 'Diamonds'}
      self.game = get_solvable(initial_seed=None)
      self.start_state = deepcopy(self.game)
      self. game.no_turn_cards = 1
      self.state = self.game.state
      self.game.debug = False
      self.state.print_game()
      Scene.__init__(self)
      self.setup()
           
  def setup_ui(self):
    """place all gui elements"""
    # scale to device
    w, h = get_screen_size()
    # w, h = 1112, 834
    # w, h = 852, 393
    
    # define all card locations
    cx, cy = cardsize
    
    foundation_start_y = h - cy - TOP_GAP
    pile_start_y = foundation_start_y - cy - MID_GAP
    # foundation and freecell positions, bottom left of card
    self.fpos = []
    self.foundation_bboxes = []
    self.pile_positions = []
    # stock, waste and foundation
    for i in range(8):
       if i == 2:
           self.fpos.append(Point(i*(cx+10)+X_OFF - cx*0.9, foundation_start_y))
       elif i == 3:
           self.fpos.append(Point(i*(cx+10)+X_OFF - cx*1.8, foundation_start_y))   
       else:
           self.fpos.append(Point(i*(cx+10)+X_OFF, foundation_start_y))
       self.foundation_bboxes.append(Rect(*self.fpos[-1], *cardsize))
       
    self.all_boxes = self.foundation_bboxes
    #tableau
    for col in range(8):
        self.pile_positions.append([Point(col*(cx+10)+X_OFF, pile_start_y - row*cy/3)
                                    for row in range(30)])
        
    self.all_boxes.extend([Rect(*p, *cardsize)
                           for pile in self.pile_positions for p in pile])
    
    # now build gui
    # Root node for UI elements
    self.ui_root = Node(parent=self)
  
    self.score_label = LabelNode('0', font=('Avenir Next', 20),
                                 position=(60, 20),
                                 anchor_point=(0, 0),
                                 parent=self)
    self.line_label = LabelNode('Time 0', font=('Avenir Next', 30),
                                position=(w / 2, h),
                                anchor_point=(1, 1), parent=self)
    LabelNode('Foundation', font=('Avenir Next', 30),
              position=(self.fpos[6].x, self.fpos[0].y+cy+20),
              anchor_point=(0.5, 0), parent=self)
    LabelNode('Stock', font=('Avenir Next', 30),
              position=(self.fpos[0].x, self.fpos[0].y+cy+20),
              anchor_point=(0.5, 0), parent=self)
    LabelNode('Waste', font=('Avenir Next', 30),
              position=(self.fpos[1].x, self.fpos[0].y+cy+20),
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
        LabelNode(str(col % 4 + 1), font=('Avenir Next', 20),
                  position=(self.fpos[col].x + cx/2, self.fpos[col].y + cy + 5),
                  anchor_point=(0, 0), parent=self)
    
    # freecell and foundation outlines
    icons = ['\u2660', '\u2665', '\u2663',  '\u2666']      # S, H, C, D
    for i, f in enumerate(self.fpos):
        if i  in [2,3]:
           continue
        ShapeNode(path=ui.Path.rounded_rect(0, 0, cx + 8, cy + 8, 10),
                  position=f-(4, 4),
                  fill_color='red' if i < 4 else 'blue', stroke_color='white',
                  z_position=0, alpha=0.95,
                  anchor_point=(0, 0),
                  parent=self)
        LabelNode(icons[i % 4], font=('Avenir Next', cx/2),
                  position=(self.fpos[i%4 + 4].x + cx/2, foundation_start_y + cy/2),
                  anchor_point=(0.5, 0.5),
                  z_position=1, parent=self)
    
  def define_cards(self, state=None):
      """ create card images and store in card objects """
      if state is None:
         state = self.state
      try:
        for card in self.all_cards:
          card.tileobject.remove_from_parent()
      except (AttributeError):
          pass
      # flat list
      self.all_cards = sum(state.game, [])
      for card in self.all_cards:
              if self.inbuilt_cards:
                  face = '10' if card.face == 'T' else card.face
                  if card.get_face_up():
                      image = f'card:{self.suit_name[card.suit]}{face}' 
                  else:
                      image = 'card:BackGreen1'
              else:
                  if card.get_face_up():
                       image = f'./freeCellSolver/pics/{self.face_index[card.face]:02d}{card.suit}.gif'
                  else:
                       image = f'./freeCellSolver/pics/back111.gif'
              card.tileobject = (Tile(image, 0, 0,
                                z_position=10,
                                parent=self))

                                                          
  def setup(self):
    """ initialise game """
    global MOVE_SPEED
    self.line_timer = INITIAL_LINE_SPEED
    self.timer = 0
    self.score = 0
    MOVE_SPEED = 0.001
    # only set up fixed items once
    try:
      a = self.score_label.text
    except AttributeError:
      self.setup_ui()
    self.define_cards()
    self.show_cards()
    #self.game_str = self.save_game()
    self.resume_game()
    self.debug.text = 'Klondike'
  
  def show_cards(self, state=None):
      """Draw cards in positions determined by game state
      For solved games, foundation is only top card.
      we need to delete lower cards
      """
      if state is None:
          state = self.state
      # redraw piles
      for col, pile in enumerate(state.tableau):
        for row, card in enumerate(reversed(pile)):
          card.tileobject.set_pos(self.pile_positions[col][len(pile) - row])
          card.tileobject.z_position = 20 - int(2*row + 1)
        
      # redraw foundations
      # only show top one in each pile
      for col, found in enumerate(state.foundation):
        if found != []:
            top_card = found[-1]
            top_card_face, top_card_suit = (card_indexes.index(top_card.face) + 1,
                                            'shcd'.index(top_card.suit))
            top_card.tileobject.set_pos(self.fpos[col + 4])
            
            # delete cards below top found
            # wait for card movement to finish
            sleep(MOVE_SPEED)
            for face_no in range(top_card_face, 1, -1):
              try:
                lower_card = self.tuple_to_card((face_no - 1, top_card_suit))
                lower_card.tileobject.z_position = -1
                lower_card.tileobject.remove_from_parent()
                self.all_cards.remove(lower_card)
                lower_card.tileobject = None
              except (AttributeError):
                pass
              
      # redraw stock
      for cell in state.stock:
         if cell:
              cell.tileobject.set_pos(self.fpos[0])
      # redraw waste
      # top card at location 3, next at 2, all others at 1
      waste_length = len(state.waste)
      for index, cell in enumerate(state.waste):
          if index == waste_length-1:
            pos = self.fpos[3]
          elif index == waste_length-2:
            pos = self.fpos[2]
          else:
            pos = self.fpos[1]
          cell.tileobject.set_pos(pos)
  """          
  def save_game(self):
    # save in format for solver to read
    
    def convert_foundation(foundation):
      
      find highest card in each pile
      assumes last card is highest
      in order S, H, C, D
      
      order = 'shcd'
      f_order = ['None', 'None', 'None', 'None']
      for f in foundation:
        if f:
         card = f[-1]
         if card:
           f_order[order.index(card.suit)] = card.face
      return ' '.join(f_order)
    
    g = self.state
    cstr = []
    for c in g.stock:
      if not c:
        str_ = 'None'
      else:
        str_ = c[-1].face + c[-1].suit
      cstr.append(str_)
    s = '\n'.join([convert_foundation(g.foundation),
                   ' '.join([c[-1].face + c[-1].suit if c else 'None' for c in g.cell]),
                   '\n'.join([' '.join([p.face + p.suit for p in pile]) for pile in g.tableau])])
    s = s.replace('T', '10')  # 10 is T in freecell, 10 in solver
    return s
    """
        
  def tuple_to_card(self, t):
    """convert tuple t (face_no, suit_no) to card object"""
    try:
        face, suit = t
        for card in self.all_cards:
           if card.face == self.rev_index[face] and card.suit == self.suit_range[suit]:
               return card
    except (IndexError, AttributeError, TypeError, KeyError):
       return None
          
  # @ui.in_background
  def decode_state(self, index, state):
      """convert from solver state to freecell properties
      print game and move cards
      """
      #g = self.state
      #foundation, freecells, cascade = state
      #g.foundation = [[self.tuple_to_card((f, i))] if f else [] for i, f in enumerate(foundation)]
      # need empty g.cell to be [], not [None]
      #g.cell = [[self.tuple_to_card(t)] if t else [] for t in freecells]
      #g.tableau =  [[self.tuple_to_card(t) for t in pile] if pile else [] for pile in cascade]
      if self.debug_print:
          print('index', index)
          state.print_game()
      self.define_cards(state)
      self.show_cards(state)
      # wait for card movement to finish
      sleep(MOVE_SPEED)
      
  def place_last(self):
      """solve leaves one card left.
      place this card
      place last card in cascade
      """
      print('pile', self.state.tableau)
      if len(sum(self.state.tableau, [])) == 1:
        
         for index, pile in enumerate(self.state.tableau):
             if pile:
                # only 1
                card = pile[-1]
                print(card)
                # call move with p# f#
                self.move(f'p{index+1}',f'f{self.suit_range.index(card.suit)+1}')
      # try to move freecell to foundation
      print('cells', self.state.cell)
      for index, card in enumerate(self.state.cell):
          if card:
            # call move with c# f#
            self.move(f'c{index+1}',f'f{self.suit_range.index(card[-1].suit)+1}')
                
  @ui.in_background
  def read_moves(self, fast=False):
      """read state file which is a pickled tuple of lists for each move
      moves file is zero based index
      """
      global MOVE_SPEED
      if not fast:
         MOVE_SPEED = 0.3
      states = self.game.game_history
      print(f'Solution has {len(states)} states')
      for index, state in enumerate(states):
            self.decode_state(index, state)
            self.score += 1
      # finish is accomplished by hand
      # self.place_last()
      self.state.print_game()
        
  @ui.in_background
  def solve(self, fast=False):
    """call solver using game_str """
    #print('solve this\n', self.game_str)
    for card in self.all_cards:
          card.tileobject.remove_from_parent()
          card.tileobject=None
    try:
        self.game.game_history = []
        self.game.search(depth=2)              
        self.debug.text = f'Solved in {self.game.iteration_counter} moves'
        self.read_moves(fast)
                
    except RuntimeError:
        self.show_start_menu('Deck could not be solved')
    except Exception:
       # something else went wrong
       print(traceback.format_exc())
     
  def show_start_menu(self, title=''):
    self.pause_game()
    self.menu = MenuScene('Main Menu', title,
                          ['Continue', 'Restart', 'New Game', 'Complete',
                           'Complete Fast', 'Quit'])
    self.present_modal_scene(self.menu)
          
  def update_score(self):
    self.score_label.text = f'Moves {self.score}'
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
    for pile in self.state.tableau:
        for card in reversed(pile):
          try:
              if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card
                return
          except AttributeError:
            pass
    
    try:
        card = self.state.stock[-1]
        if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card
                return
    except (AttributeError, IndexError):
            pass
    
    try:
        card = self.state.waste[-1]
        if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card
                return
    except (AttributeError, IndexError):
            pass  
                 
  def touch_moved(self, touch):
    if self.selected:
      # position = bottom left of card
      self.selected.tileobject.position = touch.location - (cardsize/2)
      self.score_label.text = self.decode_position(touch)
  
  def touch_ended(self, touch):
    """ snap end location to all_boxes """    
    self.end = self.decode_position(touch)
    if self.selected:
      for pos in self.all_boxes:
        if pos.contains_point(touch.location):
          self.selected.tileobject.position = (pos[0], pos[1])
          break
    self.move(self.start, self.end, self.selected)
           
  def decode_position(self, touch):
      """ find if touch in tableau, stock, waste or foundation 
      need to identify index for tableau as can move from any position"""
      x = max(0, min(7, int((touch.location.x) / (cardsize[0] + 10))))
      # y is True for goundation or freecell
      y = (touch.location.y - self.fpos[0].y - 50) > 0
      y_index = 0
      for index, box in enumerate(self.all_boxes[8:]):
          # 8*30 positions
          if box.contains_point(touch.location):
            y_index = index % 30
            break
      
      if not y:
          return f'p{x}_{y_index}'
      elif x < 1:
          return f's{x}_{y_index}'
      elif x < 4:
          return f'w{x}_{y_index}'
      elif x >= 4:
          return f'f{x-4}_{y_index}'
      else:
          print(x, y)
          return 'None'
          
  @ui.in_background
  def move(self, start, end, card):
      """ respond to p|f|c #  for start and end """
      print(start, end)
        
      x1, x2 = int(start[1]), int(end[1])
      move = None
      # Move(priority,src_stack, src_index, dest_stack, dest_index, card)
      # ignore index_to
      match (start[0], end[0]):
          case ('p', 'f'):
            index = int(start[3:])
            move = Move(0, x1+TABLEAU, index, x2+FOUNDATION, -1, card)
          case ('p', 'p'):
            index_from = int(start[3:])
            # 
            move = Move(0, x1+TABLEAU, index_from, x2+TABLEAU, -1, card)
          case ('w', 'f'):
            index_from = len(self.state.waste)-1
            # index_to = len(self.state.foundation[x2])-1
            move = Move(0, 1, index_from, x2+FOUNDATION, -1, card)
          case (('s', 'w')| ('s', 's')):
            print('deal')
            self.game.dealstock()
            move = None
          case ('w', 'p'):
            #index_to = len(self.state.tableau[x2])-1
            move = Move(0, 1, -1, x2+TABLEAU, -1, card)
      if move:
            print(f'from {x1} to {x2} {move=}')
      self.game.availableMoves() 
      print('move=', move)   
      print(self.game.available_moves)
      if move:
        for poss_move in self.game.available_moves:
        	  #only check card and from to stacks
            if (move.src_stack == poss_move.src_stack
              and move.dest_stack == poss_move.dest_stack
              and move.card == poss_move.card):
                self.game.make_move(poss_move)
      self.state.print_game()
      self.define_cards()
      self.show_cards()
      self.score += 1
      #self.game_str = self.save_game()
        
      kings = []
      for card in self.state.foundation:
          if card:
             kings.append(card[-1].face == 'K')
          else:
              kings.append(False)
      all_kings = all(kings)
      if all_kings:
          dialogs.hud_alert('Game Complete')
          self.show_start_menu()
                    
  def menu_button_selected(self, title):
    """ choose to play again or quit """
    match title:
        case 'Continue':
          self.dismiss_modal_scene()
          self.menu = None
          self.resume_game()
        case 'Restart':
           self.dismiss_modal_scene()
           self.game = self.start_state
           self.state = self.game.state
           self.setup()
        case 'New Game':
          self.dismiss_modal_scene()
          self.game = get_solvable()
          self.state = self.game.state
          self.setup()
        case 'Complete':
          self.dismiss_modal_scene()
          self.solve()
          self.menu = None
          self.resume_game()
        case 'Complete Fast':
          self.dismiss_modal_scene()
          self.solve(fast=True)
          self.menu = None
          self.resume_game()
        case _:
          # quit
          self.view.close()

           
if __name__ == '__main__':
  run(KlondikeGame(), PORTRAIT, show_fps=False)





















