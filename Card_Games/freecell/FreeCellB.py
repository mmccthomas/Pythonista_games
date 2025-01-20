# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

#
# CS 1 Final exam, 2017
#

'''
This module has classes that implement a FreeCell game.
'''

import random
from CardB import *


class IllegalMove(Exception):
    '''
    Exception class representing illegal moves in a FreeCell game.
    '''
    pass

class NoMove(IllegalMove):
    '''
    Exception class representing non moves in a FreeCell game.
    '''
    pass


def can_add_to_foundation(card, foundation, canvas):
        # Helper Function used both here and FreeCellFullB.py (in ok_to_automove)
        '''
        Return True if a card can be added to a foundation.

        Arguments:
            card       -- a Card object
            foundation -- a foundation dictionary (mapping suits to ranks)
            canvas     -- what canvas to use
            
        Return value: True if the card can be moved, else False
        '''
        
        suit = card.suit
        bottomCardRank = foundation.get(suit, None)
        if not bottomCardRank:
            if card.rank != 'A':
                return False
        else:
            bottomCard = Card(bottomCardRank, suit, canvas, True)
            if not card.goes_above(bottomCard):
                return False
        return True


class FreeCell:
    '''
    A FreeCell game is represented by the following data structures:
      -- the foundation: a dictionary mapping suits to ranks
         e.g. { 'S' : 'A', 'D': 2 }  # other two suits (H, C) empty
      -- the freecells: a list four cards (or None if no card)
      -- the "cascades": a list of eight lists of cards
      -- the bgrnd and bgrndHandle: the fancy background picture :)
      -- the base handles:
          a dictionary where the keys represent the freecells ('x'), the
          cascades ('c'), and the foundations ('f'). Each associated value is
          a list that gets filled with handles to the base images for each.
      -- the foundation images: a list that literally exists because if the
          images for the foundations aren't saved somewhere, they vanish
      
    '''

    def __init__(self, canvas):
    
        # Note that a few more fields are specified in the constructor for
        # a FreeCellFull object
        self.canvas = canvas
        self.bgrnd = PhotoImage(file='pics/bgrnd.gif')
        self.bgrndHandle = self.canvas.create_image(0, 0, image=self.bgrnd, \
                                                                    anchor=NW)
                                                                    
        self.foundation = {}   # suit -> number map
        self.foundationImages = [] # Cuz garbage collectors, have to save image.
        self.foundationCards = [] # To use with undo
        self.cards = []
        self.freecell   = [None] * 4
        self.cascade    = [None] * 8
        self.baseHandles = { 'x': [],
                             'f': [],
                             'c': [] }
        
        
        # Foundation, freecell, and cascade backgrounds
        self.xPic = PhotoImage(file='pics/shade.gif')
        self.cPic = PhotoImage(file='pics/bottomC.gif')
        for i in range(4):
            xHandle = self.canvas.create_image(*all_locs[f'x{i}'], \
                                                       image=self.xPic)
            self.baseHandles['x'].append(xHandle)
            # make a freecell base in each free cell location, 2 cascade bases,
            # and a foundation base. Append all to the baseHandles dict.
            # All_locs is the dictionary that connects location (ex, cascade 2
            # card 0 = ('c2', 0) to position -- (x,y) pixel coordinates.
            cHandleA = self.canvas.create_image(*all_locs[f'c{2*i}'], \
                                                        image=self.cPic)
            cHandleB = self.canvas.create_image(*all_locs[f'c{2*i+1}'], \
                                                        image=self.cPic)
            self.baseHandles['c'].append(cHandleA)
            self.baseHandles['c'].append(cHandleB)
            base = PhotoImage(file=f'pics/bottom{i}.gif')
            suit = PhotoImage(file=f'pics/{all_suits[i]}.gif')
            self.foundationImages.append(base)
            self.foundationImages.append(suit)
            # make new images using the fact that all foundation pic
            # filepaths are similar, and add images to list of foundation pics
            self.canvas.create_image(all_locs[f'f{i}'][0], 60, image=suit)
            fHandle = self.canvas.create_image(*all_locs[f'f{i}'], \
                                           image=base)
            self.baseHandles['f'].append(fHandle)
       
       
        # Deal cards from a full deck to the cascades.
        i = 0   # current cascade #
        for card in Deck(self.canvas):
            self.cards.append(card)
            if self.cascade[i] == None:
                self.cascade[i] = []
            self.cascade[i].append(card)
            cardLoc = (f'c{i}', len(self.cascade[i])-1)
            # First value of tuple is a valid key in all_locs, second is index
            # of card in cascade
            card.glide(cardLoc)
            card.flip(True)
            i = (i + 1) % 8


    def game_is_won(self):
        '''
        Return True if the game is won.
        '''
        
        for cascade in self.cascade:
            if cascade:
                return False
        for potentialCard in self.freecell:
            if potentialCard:
                return False
        for suit in all_suits:
            if self.foundation.get(suit) is not 'K':
                return False
        return True


    #
    # Movement-related functions.
    #

    def move_cascade_to_freecell(self, m, n):
        '''
        Move the bottom card of cascade 'm' to freecells 'n'.
        Raise an IllegalMove exception if the move can't be made.
        '''

        if m not in range(8):
            raise IllegalMove(f'Invalid cascade index: {m}.')
        if not self.cascade[m]:
            raise IllegalMove(f'Empty cascade at index: {m}.')
        slot = self.freecell[n]
        if slot:
            raise IllegalMove(f'Freecell not empty')
        cardToMove = self.cascade[m].pop()
        self.freecell[n] = cardToMove
        cardToMove.glide(f'x{n}')
    
    def move_freecell_to_freecell(self, m, n):
        '''
        Move card in freecell 'm' to freecell 'n'.
        Raise an IllegalMove exception if the move can't be made.
        '''

        if m not in range(4):
            raise IllegalMove(f'Invalid freecell index: {m}.')
        if not self.freecell[m]:
            raise IllegalMove(f'Empty freecell at index: {m}.')
        slot = self.freecell[n]
        if slot:
            raise IllegalMove(f'Freecell not empty')
        cardToMove = self.freecell[m]
        self.freecell[n] = cardToMove
        self.freecell[m] = None
        cardToMove.glide(f'x{n}')



    def move_freecell_to_cascade(self, m, n):
        '''
        Move freecell card 'm' to bottom of cascade 'n'.
        Raise an IllegalMove exception if the move can't be made.
        '''

        if m not in range(4):
            raise IllegalMove(f'Invalid freecell index: {m}.')
        if n not in range(8):
            raise IllegalMove(f'Invalid cascade index: {n}.')
        if not self.freecell[m]:
            raise IllegalMove(f'no card in freecell {m}')
        bottomCard = self.freecell[m]
        if not self.can_add_to_cascade(bottomCard, n):
            raise IllegalMove(f"card {str(bottomCard)} can't move \
                                                      to cascade {n}")
        self.cascade[n].append(bottomCard)
        self.freecell[m] = None
        bottomCard.glide((f'c{n}', len(self.cascade[n])-1))
        
        
    def move_cascade_to_cascade(self, m, n):
        '''
        Move a single card from bottom of one cascade to another.
        Raise an IllegalMove exception if the move can't be made.
        '''

        if m not in range(8):
            raise IllegalMove(f'Invalid first cascade index: {m}.')
        if n not in range(8):
            raise IllegalMove(f'Invalid second cascade index: {n}.')
        if not self.cascade[m]:
            raise IllegalMove(f'no cards in cascade {m}')
        bottomCard = self.cascade[m][-1]
        if not self.can_add_to_cascade(bottomCard, n):
            raise IllegalMove(f"card {str(bottomCard)} can't move \
                                                      to cascade {n}")
        self.cascade[n].append(self.cascade[m].pop())
        bottomCard.glide((f'c{n}', len(self.cascade[n])-1))


    def can_add_to_cascade(self, card, cascadeNum):
        # Used both here and FreeCellFull.py (in multi_move_cascade_to_cascade)
        '''
        Return True if a card can be added to a cascade.

        Arguments:
            card       -- a Card object
            cascadeNum -- which cascade to add to (an int from 0 to 7)
            
        Return value: True if the card can be moved, else False
        '''
        
        if self.cascade[cascadeNum]:
            topCard = self.cascade[cascadeNum][-1]
            if not card.goes_below(topCard):
                return False
        return True


    def move_cascade_to_foundation(self, n):
        '''
        Move the bottom card of cascade 'n' to the foundation.
        If there is no card, or if the bottom card can't go to the foundation,
        raise an IllegalMove exception.
        '''
    
        if n not in range(8):
            raise IllegalMove(f'Invalid cascade index: {n}.')
        if not self.cascade[n]:
            raise IllegalMove(f'no cards in cascade {n}')
        topCard = self.cascade[n][-1]
        if not can_add_to_foundation(topCard, self.foundation, self.canvas):
            raise IllegalMove(f"card {str(topCard)} can't go on foundation")
        self.foundation[topCard.suit] = topCard.rank
        self.foundationCards.append(topCard)
        fIndex = all_suits.index(topCard.suit)
        self.cascade[n].pop()
        topCard.glide(f'f{fIndex}')
        
        
    def move_freecell_to_foundation(self, n):
        '''
        Move the card at index 'n' of the freecells to the foundation.
        If there is no card there, or if the card can't go to the foundation,
        raise an IllegalMove exception.
        '''

        if n not in range(4):
            raise IllegalMove(f'Invalid freecell index: {n}.')
        if not self.freecell[n]:
            raise IllegalMove(f'no card in freecell {n}')
        topCard = self.freecell[n]
        if not can_add_to_foundation(topCard, self.foundation, self.canvas):
            raise IllegalMove(f"card {str(topCard)} can't go on foundation")
        self.foundation[topCard.suit] = topCard.rank
        self.foundationCards.append(topCard)
        fIndex = all_suits.index(topCard.suit)
        self.freecell[n] = None
        topCard.glide(f'f{fIndex}')





