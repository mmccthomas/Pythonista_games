# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

#
# CS 1 Final exam, 2017
#

'''
This module has functions and classes representing playing cards 
and decks of cards.
'''

import random
from tkinter import *
from tkinter import messagebox # used in player.py
from tkinter import filedialog # used in player.py

class InvalidRank(Exception):
    pass

class InvalidSuit(Exception):
    pass

all_ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
all_suits = ['S', 'H', 'C', 'D']
firstRow, secondRow = 150, 275 # y position for foundations/freecells,
# y position for first card of cascades
cardOffset = 25
# How many pixels apart cards in cascades are
all_locs = { 'f0': (133, firstRow),
             'f1': (266, firstRow),
             'f2': (400, firstRow),
             'f3': (533, firstRow),
             'x0': (666, firstRow),
             'x1': (800, firstRow),
             'x2': (933, firstRow),
             'x3': (1066, firstRow),
             'deck': (1000, 700),
             'c0': (133, secondRow),
             'c1': (266, secondRow),
             'c2': (400, secondRow),
             'c3': (533, secondRow),
             'c4': (666, secondRow),
             'c5': (800, secondRow),
             'c6': (933, secondRow),
             'c7': (1066, secondRow) }
# A position is (x,y) pixel coords, a location is like f0, x3, etc. This dict
# will get a position from a location (Note cascades are more complicated.
# CardOffset is pixel separation between cards in a cascade. locations for cards
# in a cascade are tuples, with the first value something from c0 to c7 as
# seen in this dictionary. The second value is the index of the card in the
# cascade, which combined with cardOffset will get a position.


class Card:
    '''
    Instances of this class represent a single card in a deck of 52.
    '''

    def __init__(self, rank, suit, canvas, isFake=False):
        '''
        Create a card given a valid rank, suit, and canvas
        
        Arguments:
          rank: the card rank (an integer between 2 and 10, or 'A', 'J', 'Q',
                or 'K')
          suit: either 'S' (spades), 'H' (hearts), 'C' (clubs), 'D' (diamonds),
          canvas: which canvas to use
          isFake: a bool saying if the card is real, or just a 'test card'
              being made to check if another card can go on a foundation,
              for example
        '''
        
        if rank not in all_ranks:
            raise InvalidRank(f'{rank} not a valid rank.')
        if suit not in all_suits:
            raise InvalidSuit(f'{suit} not a valid suit.')
        self.rank = rank
        self.suit = suit
        self.canvas = canvas
        self.value = all_ranks.index(self.rank) + 1
        self.handle = None
        if suit == 'S' or suit == 'C':
            self.color = 'black'
        else:
            self.color = 'red'

        # Now to make the card appear on a tkinter canvas
        if not isFake:
            # if not a test card being made to see if a move to foundation works
            if self.value < 10:
                imageName = f'pics/0{self.value}{self.suit.lower()}.gif'
            else:
                imageName = f'pics/{self.value}{self.suit.lower()}.gif'
            self.image = PhotoImage(file=imageName)
            self.backImage = PhotoImage(file='pics/back111.gif')
            self.loc = 'deck'
            self.pos = all_locs[self.loc]
            self.handle = self.canvas.create_image(*self.pos,image=self.image)

    def flip(self, isUpsideDown=False):
        '''
        Will 'flip' a card object. Each card has a front and backimage saved.
        If the card is not upsideDown, the card will flip back and the back
        image will show. If isUpsideDown is True (flip is called with an
        argument), then an upside down card will show the front image again).
        '''
        
        self.canvas.delete(self.handle)
        if isUpsideDown:
            self.handle = self.canvas.create_image(self.pos, image=self.image)
        else:
            self.handle = self.canvas.create_image(self.pos, image=self.backImage)
    
    def glide(self, newLoc):
        '''
        Given a location, will move a card to that location and update the
        card's location and position.
        '''
        
        # A position is (x,y) pixel coords, a location is like f0, x3, etc.
        # Note that for cascades, a location would be a tuple, where first
        # term of tuple gets the location of the first card in the tuple,
        # second part increments the y value of the card's position.
        self.loc = newLoc
        if type(newLoc) == tuple:
            x, y0 = all_locs[newLoc[0]]
            y = y0 + newLoc[1] * cardOffset
            newPos = x,y
        else:
            newPos = all_locs[newLoc]
        stepAmount = 10
        # How many stages a card moves in. Increasing this makes glides
        # smoother but longer.
        xDisp = newPos[0] - self.pos[0]
        yDisp = newPos[1] - self.pos[1]
        deltaX, deltaY = xDisp / stepAmount, yDisp / stepAmount
        self.canvas.lift(self.handle)
        for i in range(stepAmount):
            self.canvas.move(self.handle, deltaX, deltaY)
            self.canvas.update()
        self.pos = newPos
        
    
    def fixPos(self):
        '''
        Will move a card to the position given by it's location, if the card
        is not already there. Useful when many moves/undoes are made in quick
        succession, as it ensures all cards go to the right place.
        
        Returns:
            True if card's position changed (position was wrong initially)
            False if not
        '''
        
        if type(self.loc) == tuple:
            x, y0 = all_locs[self.loc[0]]
            y = y0 + self.loc[1] * cardOffset
            idealPos = x,y
        else:
            idealPos = all_locs[self.loc]
        if self.pos is not idealPos:
            self.canvas.coords(self.handle, *idealPos)
            self.pos = idealPos
            return True
        return False

    def __str__(self):
        '''
        Return the string representation of the card.
        '''

        return f'{self.rank}{self.suit.lower()}'

    def goes_above(self, card):
        '''
        Return True if this card can go above 'card' on the foundations.

        Arguments:
          card -- another Card object

        Return value:
          True if this card can go above 'card' on the foundations i.e.
          if it has the same suit as 'card' and is one rank higher,
          otherwise False
        '''

        assert isinstance(card, Card), f'{card} is not a card object.'
        if self.suit is not card.suit:
            return False
        topCardValue = self.value
        bottomCardValue = card.value
        if topCardValue is not bottomCardValue + 1:
            return False
        return True

    def goes_below(self, card):
        '''
        Return True if this card can go below 'card' on a cascade.

        Arguments:
          card -- another Card object

        Return value:
          True if this card can go below 'card' on a cascade i.e.
          if it has the opposite color than 'card' and is one rank lower,
          otherwise False
        '''
        
        assert isinstance(card, Card), f'{card} is not a card object.'
        if self.color == card.color:
            return False
        bottomCardValue = all_ranks.index(self.rank) + 1
        topCardValue = all_ranks.index(card.rank) + 1
        if bottomCardValue is not topCardValue - 1:
            return False
        return True


class Deck:
    '''
    Instances of this class represent a deck of 52 cards, 13 in each
    of four suits (spades (S), hearts (H), clubs (C), and diamonds (D).
    Ranks are 'A', 2 .. 10, 'J', 'Q', 'K'.
    '''
   
    def __init__(self, canvas):
        '''
        Initialize the Deck object and flips the cards in the deck.
        '''
        self.canvas = canvas
        self.cards = [Card(rank, suit, self.canvas) for rank in all_ranks \
                                       for suit in all_suits]
        self.backImage = PhotoImage(file='pics/back111.gif')
        
        # Show the back of a card
        for card in self.cards:
            card.flip()
                                       
        random.shuffle(self.cards)
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        '''
        Return the next card in the Deck, if there is one.
        '''
        if self.current == 52:
            raise StopIteration
        newCard = self.cards[self.current]
        self.current += 1
        return newCard



