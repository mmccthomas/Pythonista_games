# taken from https://github.com/AryKno/klondike_solver_AI
# which was based upon https://web.stanford.edu/~bvr/pubs/solitaire.pdf
# original code had many anonymous indexes etc
# changed to Move and state classes
# changed move[1] to move.src_deck etc 
# lots of anonymous indices
import base_path
base_path.add_paths(__file__)
from random import choices, shuffle, seed, randint
from freecell.deck import Deck
from copy import deepcopy, copy
import console
from objc_util import ObjCClass, get_possible_method_names
#import inspect
from time import time
from collections import Counter
RED = (1, 0, 0)
STOCK = 0
WASTE = 1
FOUNDATION = 2
TABLEAU = 6
TABLEAU_END = 12
suit_order = 'shcd'

class Move:
    """ class to encapsulate a card move 
    includes testing and single card simple heuristics
    """
            
    def __init__(self,priority=0,src_stack=0, src_index=0, dest_stack=0, dest_index=0, card=None):
        self.priority = priority
        self.src_stack = src_stack
        self.src_index = src_index
        self.dest_stack = dest_stack
        self.dest_index = dest_index
        self.card = card
        
    def __repr__(self):
       return (f'Move(p={self.priority}) = src:{self.decode(self.src_stack)} > dest:{self.decode(self.dest_stack)}, {self.card}  ({self.src_stack},{self.src_index},{self.dest_stack},{self.dest_index})')
       
    def decode(self, stack):
      match stack:
        case 0:
           return 'Stock'
        case 1:
           return 'Waste'
        case (2|3|4|5):
           return 'Foun'
        case (6|7|8|9|10|11|12):
           return 'Tabl_' + str(stack-TABLEAU)
           
    # define hash and eq to allow set operations 
    def __hash__(self):
        return hash((self.src_stack, self.src_index, self.dest_stack,
                    self.dest_index, self.card.strep))
    
    def __eq__(self, other):
       return (self.src_stack == other.src_stack
              and  self.src_index == other.src_index
              and self.dest_stack == other.dest_stack
              and self.dest_index == other.dest_index
              and self.card.strep == other.card.strep)
              
    @property
    def is_empty(self):
      return all([self.priority==0, self.src_stack==0, 
                  self.src_index==0, self.dest_stack==0, 
                  self.dest_index==0])
                    
    def heuristic(self, original=False):
        #return the heuristic of a move
        #the moves are stored as a tuple (source stack,source card number, destination stack, destination card number)
        #move between build or waste to suit = 5pt
        if original:
            if self.to_foundation:
                return 5
            if self.waste_to_build:
                return 5
            if self.foundation_to_build:
                return -10                 
            #any moves that don't comply with the strategy above = 0       
            return 0
          
        else:
            if self.card.face == 'A':
                return 10
            if self.card.face == 'K' and self.dest_index <= 0:
                return 9
            if self.card.face == 'Q' and self.dest_index <= 2:
                return 9 
            # moving would clear column
            if self.src_index == 0:
                return  8            
            if self.to_foundation:
                return 5
            #move between waste to build = 5 pts
            if self.waste_to_build:
                return 4
            #move between suit stack and build stack
            if self.foundation_to_build:
                return -10                 
            #any moves that don't comply with the strategy above = 0       
            return 0
   
    @property  
    def from_build(self):
        return  self.src_stack >= TABLEAU and self.src_stack<=TABLEAU_END

    @property   
    def to_build(self):
        return self.dest_stack >= TABLEAU and self.dest_stack <= TABLEAU_END

    @property                          
    def build_to_build(self):
        return self.from_build and self.to_build

    @property                
    def waste_to_build(self):
        return self.src_stack   == WASTE and self.to_build
        
    @property    
    def foundation_to_build(self):
        return self.src_stack >= FOUNDATION and self.src_stack < TABLEAU and self.to_build
        
    @property    
    def to_foundation(self):
        return self.dest_stack >= FOUNDATION and self.dest_stack < TABLEAU and (self.from_build or self.src_stack  == WASTE)    

    def set_priority(self, priority):
        self.priority = priority
            
class State():
    """ class to encapsulate game state, lists for different stacks
    self.game joins stacks together into multilevel list """
    
    def __init__(self, stock=None, waste=None, foundation=None, tableau=None, faceup_index=None):
        self.visible = True
        if stock is None:
          self.stock = []
        else:
            self.stock = stock
        if waste is None:
          self.waste = []
        else:
            self.waste = waste
        if foundation is None:
          self.foundation = [[],[],[], []]
        else:
            self.foundation = foundation
        if tableau is None:
          self.tableau = [[], [], [], [], [], [], []]
        else:
            self.tableau = tableau
            
    def __eq__(self, other):
        return (self.foundation == other.foundation and self.tableau == other.tableau)
        
    def ident(self):
        return self.crc_encode()
        
    def encode(self): 
        """ turn state into string """
        
        long_string = '-'.join(
                       [''.join([card.strep + str(int(card.face_up)) for card in self.stock]),
                        ''.join([card.strep + str(int(card.face_up)) for card in self.waste]),
                        '-'.join([''.join([card.strep + str(int(card.face_up)) for card in pile]) for pile in self.foundation]),
                        '-'.join([''.join([card.strep + str(int(card.face_up)) for card in pile]) for pile in self.tableau])
                       ])
        return long_string
        
    def decode(self, long_string):
        """ split long string back to state """
        
        all_cards = sum(self.game, [])
        game = []
        sections = long_string.split('-')
        for section in sections:
          sec_list = []
          for i in range(0, len(section), 3):
            str_ = section[i:i+3]
            for card in all_cards:
              # compare first 2 chars
              if card.strep == str_[:2]:
                sec_list.append(card)
                # set card face_up to 3rd char 
                card.set_face_up(int(str_[2]))
                break
          game.append(sec_list)
        self.game = game
        self.stock = game[0]
        self.waste = game[1]
        self.foundation = game[2:6]
        self.tableau = game[6:]
        return self

    
    def crc_encode(self, longstring=None):
      """ simple representation of game state by 4 character hex code
      may be used simply to distinguish one state from another
      not possible to recover state
      """
      def crc16(data : bytearray, offset , length):
          if data is None or offset < 0 or offset > len(data)- 1 and offset+length > len(data):
              return 0
          crc = 0
          for i in range(0, length):
              crc ^= data[offset + i]
              for j in range(0,8):
                  if (crc & 1) > 0:
                      crc = (crc >> 1) ^ 0x8408
                  else:
                      crc = crc >> 1
          return crc 
      if longstring is None:     
          byte_repr = bytes(self.encode(), 'utf8')
      else:
      	  byte_repr = bytes(longstring, 'utf8')
      crc_code = crc16(byte_repr, 0, len(byte_repr))
      return hex(crc_code)
    
    def number_face_ups(self, longstring):
        # count number of faceup cards in foundation and tableau
        # find remainder of string after location of 2nd separator
        str_ = longstring[longstring.index('-', longstring.index('-') +1)+1:]
        #print(f'{longstring=}, {str_=}') 
        # search string for suit code and get next character 0 or 1       
        return sum([int(str_[i+1]) for i,  char_ in enumerate(str_) if char_ in 'shcd'])
        
    def update_game(self):
        #this flattens lists to allow indexing from base methods
        # produces [[stock], [waste], [found], [found], [found], [found], [stack], ..[stack]]
        self.game = [[] for _ in range(13)]
        self.game[0] = self.stock
        self.game[1] = self.waste
        for i in range(2,6):
            self.game[i] = self.foundation[i-FOUNDATION]
        for i in range(6,13):
            self.game[i] =self.tableau[i-TABLEAU]
      
    def new_game(self):
        deck = Deck(1,13,4)
        deck.shuffle()
        for index, column in enumerate(self.tableau):
            for row in range(index+1):
                card = deck.draw_card()
                card.set_face_up(row >= index)
                self.tableau[index].append(card)
        self.stock = deck[:]
        [c.set_face_up(False) for c in self.stock]
        self.update_game()
    
    def print_game(self, move=None):
        self.update_game()
        #[print(section, state) for section, state in zip(['Stock', 'Waste', 'Foundation', 'Tableau'], [self.stock, self.waste, self.foundation, #self.tableau])]
        console.set_color()
        print("Stock:   Waste:      Foundation:")
        #cell and foundation        
        print(f'  {len(self.stock):2d}       {len(self.waste)}     Spades Hearts Clubs Diamonds')   
        print('####   ', end=' ')
        if self.waste:
            print(f'{self.waste[-1]}', end=' ')    
        else:
            print(' '*4, end=' ')       

        print('    ', end='')
        for i, stack in enumerate(self.foundation):
              try:
                  print(f"{str(stack[-1]): <7}", end='')
              except IndexError:
                  print("       ", end='')  
        print()
        print('-----------------------------------------------')
  
        print("      Tableau")
        for i, _ in enumerate(self.tableau):
              print("%4d" % (i), end='  ')
        print()
  
        max_length = max([len(stack) for stack in self.tableau])
  
        for i in range(max_length):
              print(' ', end='  ')
              for j, stack in enumerate(self.tableau):  
                  try:
                      # show covered cards with block
                      if move:
                        if i == move.dest_index+1 and j == move.dest_stack-TABLEAU:
                            console.set_color(*RED)
                            pass
                      if self.visible:
                          card = str(stack[i]) if stack[i].get_face_up()  else str(stack[i]) + '\u258d'
                      else:
                          card = str(stack[i]) if stack[i].get_face_up()  else '####  '
                      print(f'{card:<6}', end='')
                      console.set_color()
                  except IndexError:
                      print(" "*6, end='')                  
              print()          
        print('------------------------------------------------')

# #########################################################################################################
              
class Game:

    #content of the game. game[0]=stock, game[1]=waste, game[2-5]=suits stacks game[6-12] = build stacks
    # game has stock, waste, foundation, tableau
    #the content of the build stack array is from the most covered card to the uncovered
    #same for the others
    game_history = []
    moves_history = []
    rollout_moves_lists = []

    rolloutCounter = 0
    __color = ["S","H","C","D"]

    available_moves = [] #represent the doable moves, the moves are stored as a Move object

    def __init__(self):
        self.iteration_counter = 0
        self.debug = True
        self.use_original = False
        self.no_turn_cards = 3       
        self.game_history = [] 
        self.state = State()
        self.state.new_game()
        self.dealstock()
        self.game_history.append(self.state.encode())
        self.state.uncovered = 7
        self.state.counts = 1
        if self.debug: print(self.state.print_game())
      
    def isOver(self):
        #the game is over if the 4 suit stacks are full with the same color
        return all([len(f)==13 for f in self.state.foundation])
        
    def diff_heuristic(self,move, original=False):
        #called if several moves have the highest score, decide between the moves, which one is the best
        #move between build to build
        # stack is index 6-13
        game = self.state.game
        card = move.card
        if original:
            if move.build_to_build:
                #if the move empties a stack, priority = 1
                if len(game[move.src_stack][:-1]) == 0:
                    return 1
                #if the move turn a face-down card, over
                if game[move.src_stack][move.src_index-1].face_up == False:
                    #return the number of face down card
                    return sum([~card.face_up for card in game[move.src_stack][:move.src_index]])
            
        else: 
            # these are modified heuristics that i tried
            if move.to_foundation:
               return 10
               
            if move.src_stack  == WASTE:
                card = self.state.waste[-1]
            else:
                card = game[move.src_stack][move.src_index]
            #print('card to move', card)
            if move.build_to_build:
                #if the move empties a stack, priority = 1
                if len(game[move.src_stack][:-1]) == 0:
                    return 3
                #if the move turn a face-down card, over
                if game[move.src_stack][move.src_index-1].face_up == False:
                    return 7 
                    #return len(game[move.src_stack][:-1])+1 #return the number of face down card
                    
        #if the move is between waste and builds
        if move.waste_to_build:
            #if the move is not a king
            if card.face != 'K':
                return 1
            #if the move is a king and the matching queen is known
            queen_known = False
            for stack in self.state.tableau:
                for c in stack:
                    if c.face_up and c.face=='Q' and c.color != card.color:
                        queen_known = True
                        break 
            if card.face == 'K' and queen_known :
                return 1
            if card.face == 'K' and not queen_known:
                return -1
        
        #any other move
        return 0

    def availableMoves(self):        
        #we go on every build stacks,we try every possibilities :
        #   -build ->
        #we go through the build stacks and suits stack
        for i, stock in enumerate(self.state.tableau):
            for j, card in enumerate(stock):
                if card.face_up:
                    # -attempt to place on foundation
                    for k, f in enumerate(self.state.foundation):
                         mv = Move(0, i+TABLEAU,j, k+FOUNDATION, len(f)-1, card)
                         if self.move_is_legal(mv): #if the move is legal we add it at the end
                             self.available_moves.append(mv)
                    # attempt to place on another stack
                    for k, p in enumerate(self.state.tableau):
                        if p != stock: #if the destination build stack is different from the source one
                              mv = Move(0, i+TABLEAU,j, k+TABLEAU, len(p)-1, card) #we can only add at the bottom of a build stack
                              if self.move_is_legal(mv): #if the move is legal we add it at the end
                                  self.available_moves.append(mv)                        
        
        #we test the top card of the waste
        if len(self.state.waste) > 0:
            #if there's at least one card
            card = self.state.waste[-1]
            for k, f in enumerate(self.state.foundation): #we go through the others build and suits stacks
                mv = Move(0, WASTE, suit_order.index(card.suit)+FOUNDATION, k+FOUNDATION, len(f)-1, card)
                if self.move_is_legal(mv): #if the move is legal we add it at the end
                    self.available_moves.append(mv)
            for k, p in enumerate(self.state.tableau):
                mv = Move(0, WASTE, -1, k+TABLEAU, len(p)-1, card) #we can only add at the bottom of a build stack
                if self.move_is_legal(mv): #if the move is legal we add it at the end
                    self.available_moves.append(mv)         
        # rarer case when moving a stack item back breaks deadlock    
        if self.available_moves == 0:        
            for i, f in enumerate(self.state.foundation):
                try:
                    card == f[-1]  
                    if card.face not in ['A', '2']:
                        for k, p in enumerate(self.state.tableau):
                            mv = Move(i+FOUNDATION, -1, i+TABLEAU, len(k)-1, card)
                            if self.move_is_legal(mv): #if the move is legal we add it at the end
                                self.available_moves.append(mv)                                                                                                                                                       
                except IndexError:
                    pass                                                                                    
       
        # remove duplicates
        self.available_moves =  list(set(self.available_moves))
         # if no moves are available, we deal the stock        
        return self.available_moves
           
    def evaluate_moves(self,moves_list):
        """ sort the available moves, best is last """
        #we evaluate the priority for the first time
        for move in moves_list:
            move.priority += move.heuristic(self.use_original)
            #we update the priority
        #we update the sort the moves_list with highest priority last
        best = sorted(moves_list, key = lambda x: x.priority)

        # now sort again using additional heuristic
        if(len(best)>1):
            #there's several moves at the maximum value, we use the other priority calculator
            for move in best:
               move.priority += self.diff_heuristic(move, self.use_original) #we had the previous calculated heuristic to the new one
            best = sorted(best, key = lambda x: x.priority)              
            #best = [move for move in best if move.priority == best[-1].priority]            
        return best
        #return a list that contains the index of the best moves in self.available_moves
            
    def play(self):
        if self.availableMoves():
            #print("Available move at the beginning : ",end="")
            #[print(move) for move in self.available_moves]
            #if there is at least one available move
            #generate the priorities and give back the priority_list
            self.available_moves = self.evaluate_moves(self.available_moves) 
            #print("Available move after evaluate_moves : ",end="")
            #print(self.available_moves)
            print('available moves')
            [print(move) for move in self.available_moves]
            #We check if one of the move is repetitive
            #we execute the only move chosen
            
            self.available_moves = [move for move in self.available_moves if not self.repetitive_move(move)]
            #print("Available move after repetitive check : ",end="")
            #[print(move) for move in self.available_moves]
            if not self.state.waste:
               self.dealstock()

            if self.available_moves:
                #if there's no move after the repetition check
                # random choice or only one
                # use highest priority
                move = choices(self.available_moves, [move.priority+1 for move in self.available_moves])[0]
                # move.card = self.state.game[move.src_stack][move.src_index]
                self.make_move(move)
                
                #we add the move to the history
                self.moves_history.append(move)
                #we add the move to the move_history
                #print("Available move at the end : ",end="")
                #[print(move) for move in self.available_moves]
                #self.defeat(self.available_moves[0])

            else:
                #the move is repetitive or none available
                # we deal the stock
                self.dealstock()
                
                #we add the move to the history, the deal of the stock is represented by a 4-zero tuple
                self.moves_history.append(Move())
                print("deal the stock")
                #self.defeat([0,0,0,0,0])
            #we clean the available_moves to do another play
            self.available_moves.clear()            
        else:
            #if there is no move available
            self.dealstock()
            #if no moves are possible, we deal the stock
            #we add the move to the history, the deal of the stock is represented by a 4-zero tuple
            self.moves_history.append(Move())
            print("deal the stock, no moves")
        
        self.game_history.append(self.state.encode())
           
        
    def evaluate_game(self,moves_list):
        #evaluate the game value, used by the rollout algorithm, by simply making the sum of the moves priority
        return sum([move.priority for move in moves_list])
   

    def move_is_legal(self,move):
        # import card object to make life easier
        #return true if a move  is legal
        #from x stack to builds
        # move is move object
        s = self.state
        card = move.card
        
        #the source is a build
        if move.from_build:         
            # can't move a king from start position into stack or on top of  another stack
            if card.face == 'K' and move.to_build and move.src_index == 0:
                return False

        if move.to_build:
            #the destination is a build stack
            if len(s.tableau[move.dest_stack-TABLEAU]) == 0:
                #the build stack is empty
                return card.face == 'K' 
                #the first card must be a king
            else:
                dest_card = s.tableau[move.dest_stack-TABLEAU][-1]
                #if self.debug: print(f'{card.next_up()=}, {dest_card.face=} , {card.color=},{dest_card.color=}' )
                return (card.next_up() == dest_card.face) and (card.color != dest_card.color)
                #true if the source card's number is lower and if the colors are different
           
        #from x stack to suits # S, H, C, D
        if move.to_foundation:
            top_card = (move.src_index == len(s.tableau[move.src_stack-TABLEAU])-1) or (move.src_stack  == WASTE)
            if top_card: #In any case, a card that is moved to a suit stack is at the end of its stack
                if len(self.state.game[move.dest_stack]) == 0:
                    #if the suit stack is empty
                    return card.face == "A" and card.suit == suit_order[move.dest_stack-FOUNDATION]
                    #the first card must be an Ace
                else:
                    dest_card = s.foundation[move.dest_stack-FOUNDATION][-1]
                    return (card.next_down() == dest_card.get_face()) and (card.suit == dest_card.suit)
                    #true if the source card's number is higher and if the symbol are the same
            else:
                return False      
                        
    def make_faceup(self, move):
        # try to make card below face up
        if move.from_build:
           #if the move come from a build stack
           try:
              card_below = self.state.tableau[move.src_stack-TABLEAU][move.src_index-1]
              card_below.set_face_up(True)               
           except IndexError:
              pass
            
    def make_move(self,move):
        #update the game list
        #move is a Move object
        #print("make_move.move= ", move)
        
        if move.to_foundation:
            #top card only
            self.state.foundation[suit_order.index(move.card.suit)].append(move.card)
            self.state.game[move.src_stack].pop()
        else:         
            self.state.game[move.dest_stack].extend(self.state.game[move.src_stack][move.src_index:])
            del self.state.game[move.src_stack][move.src_index:] #we delete the old position            
        self.make_faceup(move)
        #
        
        # remove any other move using same card
        self.available_moves = [move_ for move_ in self.available_moves if move_.card != move.card]
        self.state.update_game()
        # self.moves_history.append(move)        

    def dealstock(self):
        #deal the stock        
        # transfer N cards to waste
        s = self.state
        if not s.stock:
            if self.debug: print("stock is empty")
            #if the stock is  empty
            s.stock = s.waste[::-1] + s.stock
            [card.set_face_up(False) for card in s.stock]
            #We put the cards of the waste at the bottom of the stock (at the beginning of the list)
            s.waste.clear()
            #We clear the waste
        #we add the last three card of the stock to the waste
        s.waste.extend(s.stock[::-1][:self.no_turn_cards])
        [card.set_face_up(True) for card in s.waste]

        del s.stock[-self.no_turn_cards:]


    def defeat(self):
        #this function checks the game_history for any dead end
        counts = Counter([self.state.number_face_ups(state) for state in self.game_history])                 
        self.state.uncovered = max(counts.keys())
        self.state.counts = counts[self.state.uncovered]
        
        if len(self.moves_history) > 11:
            print('checking history')
            #if the game history contains at least 12 moves
            
            #test if there's an exchange between stacks and if there is dealstock between them
            """
            if t.build_to_build():            
                #if the game is stuck in a juggle between builds
                count = 0
                for i in range(1,len(self.moves_history)+1):
                    prev = self.moves_history[-i]
                    if prev.is_empty(): 
                        count += 1
                    else:
                        if count >=5:
                            if (t.src_stack == prev.src_stack and t.dest_stack == prev.dest_stack) \
                               or (t.src_stack == prev.dest_stack and t.dest_stack == prev.src_stack):
                                #there's a juggle between 
                                return True
            """
            #we check if anynew card has not been discovered for a while
            # detect a run of 20 same value if not at endgame     
            for number, count in counts.items():
                if count > 20 and number != 52:
                    print('finished due to no new cards')
                    return True   
                              
        return False #no defeat       
          
    def filter_repetitive(self, available_moves):
        return [move for move in available_moves if not self.repetitive_move(move)]
        
    def repetitive_move(self, move):
        #return true if the move is repetitive
        #check if the move is only between builds or between suits or between builds and suits        
        if move.build_to_build:
            card = move.card
            moved_cards = [move.card for move in self.moves_history]
            '''
            for moved_card in moved_cards:
               if move.card == moved_card:
                move.priority -= 5
                break
            '''    
            # start checking when enough moves made
            if(len(self.moves_history)>9):                
                # find where card was previously moved 
                for pre in reversed(self.moves_history):
                  if move.card == pre.card:
                    a = move == pre
                indices = [i for i, x in enumerate(self.moves_history) if x.card == card]                   
                for index in indices:
                    prevMove = self.moves_history[index]
                    if prevMove == move:
                        if self.debug: print('eliminated move1', move.card)                            
                        return True
                        
                        #if the move is bouncing between the same two builds stacks
                    #if (move.src_stack == prevMove.dest_stack 
                    #       and move.dest_stack == prevMove.src_stack):
                    #    if self.debug: print('eliminated move2', move.card) 
                    #    return True                                
        return False

    def savegame(self):
    #return a copy of the game state      
        return self.state.encode()
        
    def cycle_stock(self):
        """ transfer from stock until available move or return to start position """  
        if len(self.available_moves) == 0:
            # loop thru stock until available move or
            # back to start position
            len_stock = len(self.state.stock)
            len_waste = len(self.state.waste)
            # no more cards
            if len_stock == len_waste == 0:
                return False
            iteration = 0
            while True:
                self.dealstock()
                if self.debug: print('dealt stock', len(self.state.stock), len_stock, self.state.waste[-1])
                # if self.debug: print(self.state.stock, self.state.waste)
                self.availableMoves()
                self.available_moves = self.filter_repetitive(self.available_moves)
                if len(self.available_moves) > 0:
                     if self.debug: print('After stack deal')
                     if self.debug: self.state.print_game()
                     return True
                if len(self.state.stock) == len_stock:
                   return False
                if iteration > 20:
                  return False
                iteration += 1
            return True 
            
    def get_moves(self):
        # filter and grade available moves
        self.available_moves.clear()
        self.available_moves = self.availableMoves()
        self.available_moves = self.filter_repetitive(self.available_moves)
        self.cycle_stock()  
        # sort and filter moves to return list with best priorities last
        self.available_moves = self.evaluate_moves(self.available_moves)
        return self.available_moves
                             
    def search(self, depth=0):
        # basis of this is https://web.stanford.edu/~bvr/pubs/solitaire.pdf
        # For each step, find best of available moves
        # then look forward for each option to grade the most effective
        # depth 2 seems to give best result
        # typically 1/5 to 1/3 are solvable
        
        self.iteration_counter = 0
        while True:
          self.iteration_counter += 1
          if self.debug: print('\n')
          if self.debug: print(f'iteration {self.iteration_counter}')   
          
          # if the grid is filled, succeed if every word is valid and otherwise fail
          if self.isOver():
              return True

          self.available_moves = self.get_moves()
                                 
          if len(self.available_moves)==0:
              if self.debug:
                  print('no more moves')                
              return False
                    
          # if all moves have same priority
          if len({move.priority for move in self.available_moves}) ==1:
            # randomising choices allows different solve path on each run
            # can solve failures
            # shuffle the moves
            shuffle(self.available_moves)
          if self.debug: print('Number moves', len(self.available_moves))
          
          moves = copy(self.available_moves)
                    
          if len(moves) == 1 or moves[-1].card.face == 'A':
              self.make_move(moves[-1])
              if self.debug: print(moves[-1])
              self.moves_history.append(moves[-1])     
              self.game_history.append(self.state.encode())
              if self.debug: self.state.print_game()         
              continue
          else:
              #more than 1
              # which move is really best?
              # look forward N moves and return evaluation of each choice
              scores = []
              initial_state = self.state.encode()
              for move in moves:
                  # store a copy of the current board
                  previous_state = self.state.encode()
                  score = self.iteration_loop(depth, move)[0] + move.priority
                  scores.append(score)
                  self.state = self.state.decode(previous_state)
                 
              if self.debug: print('scores:', scores)
              if self.debug: [print(move) for move in  moves]
              move_no = scores.index(max(scores))
              self.state = self.state.decode(initial_state)
              self.make_move(moves[move_no])
              if self.debug: print('Moved', moves[move_no])
              self.moves_history.append(moves[move_no])
              self.game_history.append(self.state.encode())
              if self.debug: self.state.print_game()                        
          
    def iteration_loop(self, depth=0, move=None):        
        # recursive routine to assess score lower down
        while True:
          if depth <= 0:
              return self.score, depth                       
          self.available_moves.clear()   
          if move:
              self.score = 0
              self.make_move(move)                                     
          else:
              self.get_moves()
              score = self.evaluate_game(self.available_moves)
              if self.available_moves: self.make_move(self.available_moves[-1])
              self.score += score 
          score, depth = self.iteration_loop(depth-1, move=None) 
             
          return score, depth 
     
def get_solvable(debug=False, initial_seed=1327):
    """ return a solvable game """
    if initial_seed:
        _seed = initial_seed
    else: 
        _seed = randint(1,10000)
        seed(_seed)
    while True:        
        game = Game()
        game.debug = debug
        result = game.search(depth=2)
        print('result', result)
        game.state.print_game()
        if result:
            # solved game
            # reset same game
            seed(_seed)   
            game = Game()
            break
    print(_seed)
    return game
                                         
    
if __name__ == '__main__':
  console.clear()
  #game = get_solvable(False, 1327)
  seed(1)
  game = Game()
  game.search(depth=2)
  game.state.print_game()
  #_code = game.state.crc_encode()
  long_str = game.state.encode()
  game.state.decode(long_str)
  print(game.state.crc_encode())
  game.state.print_game()
  
      
  #print(f'{_code=}')
  # find solvability with varying depth
  count = 0
  N = 500
  D = 1
  card_turns = 3
  counts = []
  times = []
  with open(f'klondike_winning.txt', 'w') as f:
      for d in range(4,5):
        tstart = time()
        for i in range(1,N):
          seed()
          print('\nStart state, ', i, d)
          game = Game()
          game.debug = False
          game.no_turn_cards = card_turns
          t = time()
          # game.playRollout(3)
          result = game.search(depth=D)
          print(f'{"Complete" if result is True else "Defeat"} in time {time()-t:.3f} secs {game.iteration_counter} counts')
          print('\nEnd state')
          game.state.print_game()
          if result :
            f.write(game.game_history[0] + '\n')
            print('winning start state', game.game_history[0])
            count += 1
          # for i in range(0):
          #     game.play()
          #     game.state.print_game()
        print('solved', count, 'in ', N)
        print('total time=', time()-tstart)
        counts.append(count)
        times.append(time()-tstart)
  print('counts', counts)
  print('times', times)
   













