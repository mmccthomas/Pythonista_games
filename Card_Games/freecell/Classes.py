# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

'''
This module has functions and classes representing playing cards 
and decks of cards.
'''

import random

all_ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
all_suits = ['S', 'H', 'C', 'D',]


class Card:
    '''
    Instances of this class represent a single card in a deck of 52.
    '''

    def __init__(self, value, sVal):
        '''
        Create a card given a valid rank and suit.
        
        Arguments:
          value   -- card's value from 1-13
          sVal    -- card's suit (from 0-3, same as corresponding all_suits val)
        '''
        self.rank = all_ranks[value-1]
        self.suit = all_suits[sVal]
        self.cVal = sVal % 2
        # 0 is black, 1 is red
        self.sVal = sVal
        self.value = value
    
    def __str__(self):
        '''
        Return the string representation of the card.
        '''

        return f'{self.rank}{self.suit.lower()}'


class FreeCell:
    '''
    A FreeCell game is represented by the following data structures:
      -- the foundation: a list of four ints representing the top card
      -- the freecells: a list four cards (or None if no card)
      -- the "cascades": a list of eight lists of cards
    '''

    def __init__(self, filled=True):
        # if initialized with nothing, will deal out deck. If initialized with
        # False, will not deal out deck and will be an 'unfilled' object
        
        self.foundation = [None] * 4   # Not a dictionary, just a list of ints.
        self.freecell   = [None] * 4
        self.cascade    = [None] * 8

        if filled:
            # Deal cards from a full deck to the cascades.
            i = 0   # current cascade #
            deck = [Card(value, sVal) for value in range(1,14)\
                                           for sVal in range(4)]
            random.shuffle(deck)
            for card in deck:
                if self.cascade[i] == None:
                    self.cascade[i] = []
                self.cascade[i].append(card)
                i = (i + 1) % 8




