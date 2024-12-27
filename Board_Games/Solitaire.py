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
import traceback
import dialogs
from types import SimpleNamespace
from freecell.freecell import Freecell, Card
import freeCellSolver.FreeCellSolver as solver
# import freeCellSolver.Functions as fn

cardsize = (140,190)
X_OFF = 80
MOVE_SPEED = 0.01
INITIAL_LINE_SPEED = 1
A=Action
card_indexes = 'A23456789TJQK'

class Tile(SpriteNode):
  """
  A single tile on the grid.
  """
  def __init__(self, tile, x=0, y=0, **args):
    SpriteNode.__init__(self, tile, **args)   
    self.size = cardsize
    self.anchor_point = 0.5, 0.5 
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
      sleep(MOVE_SPEED)
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
    self.line_label = LabelNode('0', font=('Avenir Next', 20), position=(120, 10), parent=self)
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
    
    for i in range(8):
       self.foundation_positions.append((i*(cardsize[0]+10)+X_OFF, 850))
       self.foundation_bboxes.append(Rect(*self.foundation_positions[-1], *cardsize))
       ShapeNode(path=ui.Path.rounded_rect(0,0,cardsize[0], cardsize[1], 10), 
                 position=self.foundation_positions[-1],
                 fill_color='red' if i<4 else 'blue', stroke_color='white',
                 z_position=0,alpha=0.95, 
                 parent=self)
    self.all_boxes = self.foundation_bboxes

    self.pile_positions = []
    for col in range(8):
        self.pile_positions.append([(col*(cardsize[0]+10)+X_OFF, 680-row*60) for row in range(18)])
        #pile_boxes.append([Rect(col*(cardsize[0]+10)+X_OFF, 680-row*60, *cardsize) for row in range(18)])
        
    self.all_boxes.extend([Rect(*p, *cardsize) for pile in self.pile_positions for p in pile])

    
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
            top_card.tileobject.set_pos(self.foundation_positions[col+4], moveslow=moveslow)
            
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
         if cell != [] and cell != [None]:
            for item in cell:
              item.tileobject.set_pos(self.foundation_positions[col], moveslow=moveslow)
              
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
         f_order[order.index(card.suit)] = card.face
      return ' '.join(f_order)
    
    g = self.newgame
    cstr = []
    for c in g.cell:
      if c == [] or c ==[None]:
        str = 'None'
      else:
        str = c[-1].face + c[-1].suit
      cstr.append(str)
    s = '\n'.join([convert_foundation(g.foundation),
                   ' '.join(cstr),
                   '\n'.join([' '.join([p.face + p.suit for p in pile]) for pile in g.pile])])    
    s = s.replace('T', '10')
    return s   
        
  def tuple_to_card(self, t):
    # convert tuple t (face_no, suit_no) to card object
    try:    
        face, suit = t        
        face_index = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
                       'J': 11, 'Q': 12, 'K': 13}
        rev_index = {v:k for k, v in face_index.items()}
        suit_range = ['s', 'h', 'c', 'd']
        for card in self.all_cards:
           if card.face == rev_index[face] and card.suit == suit_range[suit]:
                return card
    except (IndexError, AttributeError, TypeError, KeyError):
       return None

  def gen_automove_to_foundation(self, foundation, freecell, cascades):
      def goes_above(cardA, cardB):
          # Cards are given by tuples where the first value is their rank(1-13), the
          # second represents their suit (0-3, index corresponds to suit in all_suits)
          '''
          Return True if cardA can go above cardB (in a foundation list).
      
          Arguments:
            cardA -- a card Tuple
            cardB -- a card Tuple in a foundation list
          
          Return value:
            True if cardA can go above cardB, otherwise False
          '''
          valA, sValA = cardA
          valB, sValB = cardB
          if sValA is not sValB:
              return False
          if valA is not valB + 1:
              return False
          return True
      def can_add_to_foundation(card, foundation):
        '''
        Return True if a card can be added to a foundation.
    
        Arguments:
            card       -- a Card tuple
            foundation -- a foundation list (list of values in foundation,
                          index of each value is the same as index of that suit
                          in all_suits)
                
        Return value: True if the card can be moved, else False
        '''
        value, sVal = card
        bottomCardVal = foundation[sVal]
        if not bottomCardVal:
            if value != 1:
                return False
        else:
            bottomCard = (bottomCardVal, sVal)
            if not goes_above(card, bottomCard):
                return False
        return True
        
      def move_cascade_to_foundation(cascades, foundation, n):
        '''
        Move the bottom card of cascade 'n' to a foundation list.
        '''
        topCard = cascades[n].pop()
        foundation[topCard[1]] = topCard[0]
        
      def move_freecell_to_foundation(freecell, foundation, n):
        '''
        Move the card at index 'n' of a freecell list to a foundation list.
        '''
        topCard = freecell[n]
        foundation[topCard[1]] = topCard[0]
        freecell[n] = None
      def ok_to_automove(card, foundation, pr=False):
        '''
        Return True if a card can be automoved to a foundation list.
    
        Arguments:
          card       -- a Card tuple
          foundation -- a foundation list
    
        Return value:
          True if the card can be automoved, else False
        '''
        if pr:
           print(card, foundation, can_add_to_foundation(card, foundation))
        if not can_add_to_foundation(card, foundation):
            return False
        value, sVal = card
        if value > 2:
            if sVal % 2: # S and C are odd, D and H even
                rankValA = foundation[0]
                rankValB = foundation[2]
            else:
                rankValA = foundation[1]
                rankValB = foundation[3]
            if not rankValA or not rankValB:
                return False
            if value > rankValA + 1 or value > rankValB + 1:
                return False
        return True
    
      '''
      Make as many moves as possible from the cascades/freecells to the
      foundations.
      This is generator version to allow moves to be logged
      Argument:
        foundation -- a foundation list to move cards to
        freecell -- a freecell list to move cards from
        cascades -- a list of cascade lists to move cards from
  
      Return value: none
      '''
      print('automove', foundation, freecell, cascades)
      while True:
          mustCheckAgain = False
          for i, cascade in enumerate(cascades):
              print(i, cascade)
              if cascade:
                  print('ok', ok_to_automove(cascade[-1], foundation, pr=True))
                  if ok_to_automove(cascade[-1], foundation):
                      mustCheckAgain = True
                      move_cascade_to_foundation(cascades, foundation, i)
                      print('moved cascf')
                      yield (foundation, freecell, cascades)
          for slot, card in enumerate(freecell):
              print(slot, card)
              if card:
                  print('ok', ok_to_automove(card, foundation))
                  if ok_to_automove(card, foundation):
                      mustCheckAgain = True
                      move_freecell_to_foundation(freecell, foundation, slot)
                      print('moved cellf')
                      yield (foundation, freecell, cascades)
          
          if not mustCheckAgain:
              raise(ValueError)
              break
                   
  @ui.in_background  
  def endgame(self, index, state):
        # deal with a series of automatic moves at end of game
        def move_cascade_to_freecell(cascades, freecell, n):
            '''
            Move card from bottom of cascade 'n' to freecell list.
            '''
            for slot, card in enumerate(freecell):
                if not card:
                    freecell[slot] = cascades[n].pop()
                    return
        foundation, freecells, cascades = state
        foundation = list(foundation)
        freecells = list(freecells)
        cascades =  [[c for c in pile] for pile in cascades] 
        print('end game automoves')
        self.newgame.print_game()
        # try to move cascade to freecell, then automove
        cascades_copy = cascades.copy()
        freecells_copy = freecells.copy()
        foundation_copy = foundation.copy()
        
        for n, _ in enumerate(cascades):
            move_cascade_to_freecell(cascades, freecells, n)
            try:
               for state in self.gen_automove_to_foundation(foundation,  freecells, cascades):
                  print(index, state)
                  self.decode_state(index, state)
                  index += 1
               break
            except Exception as e:
              print(traceback.format_exc())
              print('endgame error', e)
              foundation = foundation_copy
              cascades = cascades_copy
              freecells = freecells_copy
          
  @ui.in_background             
  def decode_state(self, index, state):
      # convert from solver state to freecell properties
      # print game and move cards
      g = self.newgame  
      foundation, freecells, cascade = state
      g.foundation = [[self.tuple_to_card((f, i))] for i, f in enumerate(foundation)]
      g.cell = [[self.tuple_to_card(t)] for t in freecells]
      g.pile =  [[self.tuple_to_card(t) for t in pile]  for pile in cascade]
      print('index', index)
      g.print_game()
      self.show_cards()
      sleep(MOVE_SPEED)
      
  @ui.in_background         
  def read_moves(self):
      # read moves file which is a pickled list of tuples for each move
      # moves file is zero based index
      g = self.newgame  
      import pickle
      if self.read_pickle:
        with open('statefile.pkl', 'rb') as f:         
         moves, states = pickle.load(f)
        print(f'statefile.pkl has {len(moves)} states')
        for index, state in enumerate(states):
            self.decode_state( index, state)
        # finish by showing completed hand
        #self.endgame(index, state)
        #always show 4 Kings
        #state = ([13, 13, 13, 13], [None, None, None, None], [[],[],[],[],[],[],[],[]])        
        #self.decode_state(index,state)
        
  @ui.in_background
  def solve(self):
    # call solver using game.txt  
    print('solve this\n', self.game_str)
    solver.main(SimpleNamespace(**{'gameFile': 'None', 
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
      
  def show_start_menu(self):
    self.pause_game()
    self.menu = MenuScene('Main Menu', '', ['Continue', 'New Game', 'Complete', 'Quit'])
    self.present_modal_scene(self.menu)  
         
  
  def update_score(self):
    self.score_label.text = str(self.score)    
    self.line_label.text = str(self.timer)            
  
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
      self.selected.position = touch.location
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
        self.newgame.print_game()
        self.show_cards()
        self.game_str = self.save_game()
        # self.debug.text = str(error)
        all_kings = all([card[-1].face=='K' for card in self.newgame.foundation])
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





