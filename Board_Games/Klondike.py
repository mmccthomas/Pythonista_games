""" Klondike Solitaire

"""
import base_path
from scene import *
from time import sleep
import traceback
import dialogs
from random import choice
from copy import deepcopy
from types import SimpleNamespace
base_path.add_paths(__file__)
from gui.game_menu import MenuScene
from freecell.klondike_solver import Game, get_solvable, Move, State
# constants 
TOP_GAP = 80
MID_GAP = 10
X_OFF = 10
MOVE_SPEED = 0.001
INITIAL_LINE_SPEED = 1
STOCK = 0
WASTE = 1
FOUNDATION = 2
TABLEAU = 6
TABLEAU_END = 12
A = Action
CARD_INDEXES = 'A23456789TJQK'

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


def set_waiting(message='Processing'):
      a = ui.ActivityIndicator()
      a.style = ui.ACTIVITY_INDICATOR_STYLE_WHITE_LARGE      
      a.hides_when_stopped = True
      a.frame =(100,100,200,200)
      a.name = message
      a.background_color ='red'
      a.start_animating()        
      a.present('sheet', hide_close_button=True)
      return a
        
def reset_waiting(object):
      object.stop()
      object.close() 

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

def get_winning_hand(deal=1):
   with open(f'freecell/klondike_winning_{deal}.txt') as f:
     lines = f.read()
   lines = lines.split('\n')
   return choice(lines)
        
class KlondikeGame(Scene):
  """
  The main game code for Klondike
  """
  def __init__(self):
      """ define newgame with random deck """
      self.debug_print = True
      self.inbuilt_cards = False
      self.deal = 3
      self.game_history = []
      self.face_index = {'A': 1, '2': 2, '3': 3, '4': 4,
                         '5': 5, '6': 6, '7': 7, '8': 8,
                         '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13}
      self.rev_index = {v: k for k, v in self.face_index.items()}
      self.suit_range = ['s', 'h', 'c', 'd']
      self.suit_name = {'c': 'Clubs', 'h': 'Hearts', 's': 'Spades', 'd': 'Diamonds'}
      self.game = Game() #get_solvable(initial_seed=None)
      new_hand = get_winning_hand(self.deal)
      self.game.state = self.game.state.decode(new_hand)
      self.start_state = new_hand  
      # flat list of all cards
      self.all_cards = sum(self.game.state.game, []) 
      self.define_cards()   
      self.game.debug = False
      
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
    for col in range(7):
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
              position=(self.fpos[6].x, self.fpos[0].y+cy+10),
              anchor_point=(0.5, 0), parent=self)
    self.stock_no =LabelNode('0', font=('Avenir Next', 30),
              position=(self.fpos[0].x+cx, self.fpos[0].y+cy),
              anchor_point=(1, 0), parent=self)
    LabelNode('', font=('Avenir Next', 30),
              position=(self.fpos[1].x, self.fpos[0].y+cy+20),
              anchor_point=(0.5, 0), parent=self)
    SpriteNode('iow:pause_32', position=(32, h - 36),
               parent=self)
    SpriteNode('iow:arrow_return_left_32', position=(w-36,  h - 72),
               parent=self)
               
    self.debug = LabelNode('FreeCell', font=('Avenir Next', 20),
                           position=(w / 2, 20),
                           anchor_point=(1, 0),
                           parent=self)
                    
    for col in range(7):
        # column labels
        LabelNode(str(col), font=('Avenir Next', 20),
                  position=(self.pile_positions[col][0].x + cx/2, foundation_start_y-2*MID_GAP),
                  anchor_point=(0.5, 0.5),
                  parent=self)
        # foundation labels
        #LabelNode(str(col % 4 + 1), font=('Avenir Next', 20),
        #          position=(self.fpos[col].x + cx/2, self.fpos[col].y + cy + 5),
        #          anchor_point=(0, 0), parent=self)
    
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
  
  def card_image(self, card, position=None):
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
      if position:       
         # existing image, just change texture       
         card.tileobject.texture = Texture(ui.Image.named(image))
         card.tileobject.size = cardsize                       
      else:       
         card.tileobject = Tile(image, 0,0,
                                 z_position=10,
                                 parent=self)                             
                              
  def change_card_images(self, state):
    # call this on iteration to change card image
    # decode state long_string and change image if any face_up has changed
    for i, char_ in enumerate(state):
       if char_ in 'shcd':
          card_str = state[i-1:i+1]
          faceup = int(state[i+1])   
          card = self.str_to_card(card_str)
          assert card is not None, 'error in  card string'
          # card.face_up has already changed, so cant detect changed
          if True: # card.face_up is not bool(faceup):
            
            card.set_face_up(faceup)
            position = card.tileobject.position
            self.card_image(card, position)
            
       
  def define_cards(self):
      """ create card images and store in card objects """
      try:
        for card in self.all_cards:
            card.tileobject.remove_from_parent()
      except (AttributeError):
          pass      
      for card in self.all_cards:
          self.card_image(card)
                                                                        
  def setup(self):
    """ initialise game """
    global MOVE_SPEED
    self.line_timer = INITIAL_LINE_SPEED
    self.timer = 0
    self.score = 0
    self.game.state.print_game()
    self.game.moves_history = []
    self.game.game_history = []
    
    self.game.no_turn_cards = self.deal
    MOVE_SPEED = 0.001
    # only set up gui items once
    try:
        _ = self.score_label.text
    except AttributeError:
        self.setup_ui()
    self.game_history.append(self.game.state.encode())
    
    self.show_cards()
    self.resume_game()
    self.debug.text = f'Klondike game: {self.game.state.crc_encode()}'  
  
  def show_cards(self, state=None):
      """Draw cards in positions determined by game state
      # For solved games, foundation is only top card.
      # we need to delete lower cards
      """
      # check all cards have tileobject
      for card in self.all_cards:
         assert hasattr(card, 'tileobject'), f'{card} missing tile'
      if state is None:
          state = self.game.state
      else:
         state = self.game.state.decode(state)
      # redraw piles
      for col, pile in enumerate(state.tableau):
        for row, card in enumerate(reversed(pile)):
          card.tileobject.set_pos(self.pile_positions[col][len(pile) - row])
          card.tileobject.z_position = 20 - int(2*row + 1)
        
      # redraw foundations
      for col, found in enumerate(state.foundation):
          for row, card in enumerate(found):
              card.tileobject.set_pos(self.fpos[col+4])
              card.tileobject.z_position = int(2*row + 1)
              
      # redraw stock
      for cell in state.stock:
         if cell:
              cell.tileobject.set_pos(self.fpos[0])
      # redraw waste
      # top card at location 3, next at 2, all others at 1
      waste_length = len(state.waste)
      for index, cell in enumerate(reversed(state.waste)):
          match index:
            case 0:
              pos = 3
            case 1:
              pos = 2
            case _:
              pos = 1            
          cell.tileobject.set_pos(self.fpos[pos])  
          cell.tileobject.z_position = pos
       
  def str_to_card(self, card_str):
      for card in self.all_cards:
          if card.strep() == card_str:
             return card
      return None
      
  # @ui.in_background
  def decode_state(self, index, state):
      """convert from solver state to freecell properties
      state is longstring
      print game and move cards
      """
      if self.debug_print:
          print('index', index)          
      self.game.state = self.game.state.decode(state)
      self.game.state.print_game()
      if self.game.isOver():
          dialogs.hud_alert('Game Complete')
          self.show_start_menu()       
      self.change_card_images(state)
      self.show_cards(state)
      # wait for card movement to finish
      sleep(MOVE_SPEED)
      return self.game.state
      
  
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
      self.game.state.print_game()
             
  @ui.in_background
  def solve(self, fast=False):
    """call solver """
    try:
        self.game.game_history = []
        wait = set_waiting('Getting solution')
        result= self.game.search(depth=4)      
        reset_waiting(wait)
        if result:      
            self.debug.text = f'Solved in {self.game.iteration_counter} moves'
            [print(game) for game in self.game.game_history]
            self.read_moves(fast)
        else:
            self.debug.text = f'Cannot be solved in {self.game.iteration_counter} moves'
            self.show_start_menu('Deck could not be solved')
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
    self.score_label.text = f'Moves:{self.score}   Cards Uncovered:{self.game.state.uncovered} for {self.game.state.counts} turns'
    self.line_label.text = f'Time {self.timer}'       
    self.stock_no.text = str(len(self.game.state.stock))
  
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
    self.start = None
    if touch.location.x < 48 and touch.location.y > self.size.h - 48:
      self.show_start_menu()
    if touch.location.x > self.size.w - 48 and touch.location.y > self.size.h - 96: 
       self.undo()
       return
    # start will be c1-8, f1-4, p1-4
    self.start = self.decode_position(touch)
    for pile in self.game.state.tableau:
        for card in reversed(pile):
          try:
              if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card
                return
          except AttributeError:
            pass
    
    try:
        card = self.game.state.stock[-1]
        if card.tileobject.bbox.contains_point(touch.location):
                self.selected = card
                return
    except (AttributeError, IndexError):
            pass
    
    try:
        card = self.game.state.waste[-1]
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
    if self.start:
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
          return f't{x}_{y_index}'
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
  def undo(self):
      try:
          self.game.state = self.game.state.decode(self.game.game_history.pop())    
          self.score -= 1
          if self.debug_print: self.game.state.print_game()
          self.change_card_images(self.game.state.encode())
          self.show_cards()
          print(self.game.game_history)
      except IndexError:
        dialogs.hud_alert('No more moves')
      
  @ui.in_background
  def move(self, start, end, card):
      """ respond to p|f|c #  for start and end """
      if self.debug_print: print(start, end)
        
      x1, x2 = int(start[1]), int(end[1])
      move = None
      #self.game.state.print_game()
      self.game.available_moves.clear()
      valid_moves = self.game.availableMoves()
      best_moves = self.game.evaluate_moves(valid_moves)
      # Move(priority,src_stack, src_index, dest_stack, dest_index, card)
      # ignore index_to
      match (start[0], end[0]):
          case ('t', 'f'):
              index = int(start[3:])
              move = Move(0, x1+TABLEAU, index, x2+FOUNDATION, -1, card)
          case ('t', 't'):
              # deal with single touch, make best move with same src_stack
              if x1 == x2:
                 if self.debug_print: [print(m) for m in best_moves]
                 for move in reversed(valid_moves):
                     
                     print('available', move.src_stack, x1+TABLEAU)
                     if move.src_stack == x1+TABLEAU:
                        print('make move', move)
                        break
              else:   
                  index_from = int(start[3:])
                  move = Move(0, x1+TABLEAU, index_from, x2+TABLEAU, -1, card)
          case ('w', 'w'):
              # deal with single touch
              for move in reversed(valid_moves):
                if move.src_stack == WASTE:
                  break
          case ('w', 'f'):
              move = Move(0, 1, -1, x2+FOUNDATION, -1, card)
          case (('s', 'w')| ('s', 's')):
              if self.debug_print: print('deal')
              self.game.dealstock()
              move = None
          case ('w', 't'):
              move = Move(0, 1, -1, x2+TABLEAU, -1, card)
          case ('f', 't'):
              move = Move(0, x1+FOUNDATION, -1, x2+TABLEAU, -1, card)
      if move:
            if self.debug_print: print(f'from {x1} to {x2} {move=}')
      
      if self.debug_print: print('move=', move)   
      if self.debug_print: print(best_moves)
      if move:
         for poss_move in best_moves:
            #only check card and from to stacks, use poss_move to match
            if (move.src_stack == poss_move.src_stack
              and move.dest_stack == poss_move.dest_stack
              and move.card.strep() == poss_move.card.strep()):
                self.game.make_move(poss_move)
                self.game.moves_history.append(poss_move)
      if self.debug_print: self.game.state.print_game(move)
      longstring = self.game.state.encode()
      self.change_card_images(longstring)
      self.show_cards()
      self.game.game_history.append(longstring)
      self.score += 1
      #self.game_str = self.save_game()
      if self.game.defeat():
         dialogs.hud_alert('Game cannot finish')
         self.show_start_menu()
      if self.game.isOver():
         dialogs.hud_alert('Game Complete')
         self.show_start_menu()
         
  @ui.in_background              
  def menu_button_selected(self, title):
    """ choose to play again or quit """
    match title:
        case 'Continue':
          self.dismiss_modal_scene()
          self.menu = None
          self.resume_game()
        case 'Restart':
           self.dismiss_modal_scene()
           self.game.state = self.decode_state(0, self.start_state)
           self.setup()
        case 'New Game':
          self.dismiss_modal_scene()
          while True: 
            new_hand = get_winning_hand()
            if new_hand: break
          self.game.state = self.decode_state(0, new_hand)
          self.start_state = new_hand  
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










