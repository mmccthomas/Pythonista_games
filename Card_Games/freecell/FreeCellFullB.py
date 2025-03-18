# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

#
# CS 1 Final exam, 2017
#

'''
This module has functions and classes that augment the base FreeCell
object to produce a more full-featured FreeCell game.
'''


import random
from CardB import *
from FreeCellB import *

# Supplied to students:
def max_cards_to_move(nc, nf):
    '''
    Return the maximum number of cards that can be moved as a single sequence
    if the game has 'nc' empty cascades and 'nf' empty freecells.
    If the target cascade is empty then subtract 1 from 'nc'.

    Arguments:
      nc -- number of empty non-target cascades
      nf -- number of empty freecells

    Return value:
      the maximum number of cards that can be moved to the target
    '''

    assert type(nc) is int
    assert 0 <= nc <= 8
    assert type(nf) is int
    assert 0 <= nf <= 4

    return 1 + nf + sum(range(1, nc + 1))

def longest_movable_sequence(cards):
    '''
    Compute the length of the longest sequence of cards at the end of a 
    list of cards that can be moved in a single move.  Cards in the sequence 
    must be in strict descending order and alternate colors.

    Arguments:
      cards -- a list of cards

    Return value:
      the number of cards at the end of the list forming the longest
      sequence
    '''

    assert type(cards) is list
    for c in cards:
        assert isinstance(c, Card)
    sizeOfSeq = 0
    if cards:
        sizeOfSeq = 1
    for i in range(-1, -len(cards), -1):
        topCard = cards[i-1]
        bottomCard = cards[i]
        if not bottomCard.goes_below(topCard):
            break
        sizeOfSeq += 1
    return sizeOfSeq



def ok_to_automove(card, foundation, canvas):
    '''
    Return True if a card can be automoved to a foundation.

    Arguments:
      card       -- a Card object
      foundation -- a foundation dictionary (mapping suits to ranks)
      canvas     -- what canvas to use

    Return value:
      True if the card can be automoved, else False
    '''

    assert isinstance(card, Card)
    assert type(foundation) is dict
    if not can_add_to_foundation(card, foundation, canvas): # In FreeCellB.py
        return False
    currRankVal = all_ranks.index(card.rank)
    if currRankVal > 1:
        if card.color == 'black':
            rankToCheckA = foundation.get('D', None)
            rankToCheckB = foundation.get('H', None)
        else:
            rankToCheckA = foundation.get('C', None)
            rankToCheckB = foundation.get('S', None)
        if not rankToCheckA or not rankToCheckB:
            return False
        rankValA = all_ranks.index(rankToCheckA)
        rankValB = all_ranks.index(rankToCheckB)
        if currRankVal > rankValA + 1 or currRankVal > rankValB + 1:
            return False
    return True


class FreeCellFull(FreeCell):
    '''
    FreeCellFull is an enhanced version of FreeCell with extra useful
    features.
    '''
    def __init__(self, canvas):
        # First use the FreeCellB.py constructor
        super(FreeCellFull, self).__init__(canvas)
        self.cardsToDrag = []
        # cardsToDrag is a list of the cards currently being moved as a unit,
        # while the offset field represents the displacement of the initial
        # click from the cards being moved.
        self.clickToCardOffset = (0,0)
        self.history = []
        # Saves the state of the game after every move, for Undo and to find
        # number of moves made
        
        # Bind canvas events
        self.canvas.bind('<Button-1>', self.getCardsToDrag)
        self.canvas.bind('<B1-Motion>', self.moveDraggingCards)
        self.canvas.bind('<ButtonRelease-1>', self.releaseCards)
        
    
    def makeState(self):
        '''
        Will make a tuple of four values representing the state of a game at
        that moment, and will return said tuple. The four values are the
        foundation dictionary, the list of cards in the foundations, the
        cascades, and the freecells.
        '''
        
        foundationCopy = self.foundation.copy()
        foundCardCopy = self.foundationCards[:]
        freecellCopy = self.freecell[:]
        cascadeCopy = [cascade[:] for cascade in self.cascade[:]]
        stateOfGameTuple = (foundationCopy, foundCardCopy, freecellCopy, cascadeCopy)
        return stateOfGameTuple
    
    def updateAfterMove(self, prev):
        '''
        Does all the updating after a move is made (automoves cards to
        foundations, and saves the previous state of the board to self.history)
        '''
        
        self.automove_to_foundation()
        self.history.append(prev)
    

#
# Call-back / Helper functions.
#
    def getWhereTo(self, cx, cy, cascadeToSkip=None):
        '''
        Given a mouseclick location, will try and determine what structure cards
        are being moved to. Will return this as a tuple (first value type of
        structure, second is index of that structure, so freecell 4 would be
        ('x', 4)
        '''
        
        # Check all cascades by finding the bbox of the last card in the
        # cascade, and seeing if mouse click is within that. (Note that origin
        # cascade is skipped in this search).
        for i, cascade in enumerate(self.cascade):
            if i == cascadeToSkip:
                continue
            if cascade:
                card = cascade[-1]
                x0, y0, x1, y1 = self.canvas.bbox(card.handle)
            else:
                cascadeHandle = self.baseHandles['c'][i]
                x0, y0, x1, y1 = self.canvas.bbox(cascadeHandle)
            if x0 <= cx and cx <= x1 and y0 <= cy and cy <= y1:
                whereTo = ('c', i)
                return whereTo
    
        # Check freecells
        for i in range(4):
            cellHandle = self.baseHandles['x'][i]
            x0, y0, x1, y1 = self.canvas.bbox(cellHandle)
            if x0 <= cx and cx <= x1 and y0 <= cy and cy <= y1:
                whereTo = ('x', i)
                return whereTo

        # Check foundations
        for i in range(4):
            fHandle = self.baseHandles['f'][i]
            x0, y0, x1, y1 = self.canvas.bbox(fHandle)
            if x0 <= cx and cx <= x1 and y0 <= cy and cy <= y1:
                whereTo = ('f', i)
                return whereTo

        # If the mouse click is in ambiguous location, no destination specified.
        return None
        
    def releaseCards(self, event):
        '''
        Callback function that gets called when mouse is unclicked. Tries to
        find a move using helper function whereTo, and tries to execute move. If
        an error occurs, all moved cards glide back to original locations.
        '''
        
        # No move occurred, not even worth raising an exception because user
        # can clearly see no cards were being dragged.
        if not self.cardsToDrag:
            return None
        
        # Find which location (not position) the cards came from
        cx, cy = event.x, event.y
        origination = self.cardsToDrag[0].loc
        if type(origination) is tuple:
            origination = origination[0]
        whereFrom = (origination[0], int(origination[1]))
        
        # cascadeToSkip is a variable set equal to the cascade the cards
        # came from (none if cards not from a cascade)
        cascadeToSkip = None
        if whereFrom[0] == 'c':
            cascadeToSkip = whereFrom[1]
        
        # whereFrom and whereTo are both tuples with the first value the type
        # of structure (freecell, foundation, or cascade), and the second the
        # index of that structure (freecell/foundation 0-3, cascade 0-7
        whereTo = self.getWhereTo(cx, cy, cascadeToSkip)
        
        # Once cards origin and intended destination are know, the function
        # tries to make a move based on this info
        try:
            if not whereTo or whereTo == whereFrom:
                raise NoMove(f"No move")
            prev = self.makeState()
            if whereFrom[0] == 'c' and whereTo[0] == 'c':
                m, n, p = whereFrom[1], whereTo[1], len(self.cardsToDrag)
                self.multi_move_cascade_to_cascade(m, n, p)
            elif len(self.cardsToDrag) > 1:
                raise IllegalMove(f"Cannot move {len(self.cardsToDrag)} cards "\
                                  "to non-cascade location")
            if whereFrom[0] == 'c' and whereTo[0] == 'x':
                self.move_cascade_to_freecell(whereFrom[1], whereTo[1])
            elif whereFrom[0] == 'c' and whereTo[0] == 'f':
                self.move_cascade_to_foundation(whereFrom[1])
            elif whereFrom[0] == 'x' and whereTo[0] == 'c':
                self.move_freecell_to_cascade(whereFrom[1], whereTo[1])
            elif whereFrom[0] == 'x' and whereTo[0] == 'x':
                self.move_freecell_to_freecell(whereFrom[1], whereTo[1])
            elif whereFrom[0] == 'x' and whereTo[0] == 'f':
                self.move_freecell_to_foundation(whereFrom[1])
            self.updateAfterMove(prev)
        except NoMove as e:
            for card in self.cardsToDrag:
                card.glide(card.loc)
        except IllegalMove as e:
            messagebox.showwarning('Illegal Move', str(e))
            for card in self.cardsToDrag:
                card.glide(card.loc)

        # No matter what, have to reset for the next move
        self.cardsToDrag = []
        self.clickToCardOffset = (0,0)
        
    def moveDraggingCards(self, event):
        '''
        Callback function that keeps all the cards in self.cardsToDrag moving
        together while updating their position.
        '''
        
        # No move occurred, not even worth raising an exception because user
        # can clearly see no cards were being dragged.
        if not self.cardsToDrag:
            return None
        
        clickedCard = self.cardsToDrag[0]
        oldX, oldY = clickedCard.pos
        deltaX, deltaY = event.x - oldX, event.y - oldY
        offsetX, offsetY = self.clickToCardOffset
        deltaX -= offsetX
        deltaY -= offsetY
        for index, card in enumerate(self.cardsToDrag):
            self.canvas.lift(card.handle)
            self.canvas.move(card.handle, deltaX, deltaY)
            prevX, prevY = card.pos
            card.pos = prevX + deltaX, prevY + deltaY

    
    def getCardsToDrag(self, event):
        '''
        Callback function that determines what cards are attempting to be moved
        based on click location.
        '''
        
        cx, cy = event.x, event.y
        attemptedCardsToDrag = []
        whichCascade = -1
        
        # go through cascades and see what cards in a cascade, if any, are being
        # selected.
        for i, cascade in enumerate(self.cascade):
            for j, card in enumerate(cascade):
                x0, y0, x1, y1 = self.canvas.bbox(card.handle)
                if j < len(cascade)-1:
                    y1 = y0+cardOffset # From CardB.py
                if x0 <= cx and cx <= x1 and y0 <= cy and cy <= y1:
                    attemptedCardsToDrag = cascade[j:]
                    whichCascade = i
                    break
            if whichCascade > -1:
                break
    
        # go through freecells.
        for slot, card in enumerate(self.freecell):
            if card:
                x0, y0, x1, y1 = self.canvas.bbox(card.handle)
                if x0 <= cx and cx <= x1 and y0 <= cy and cy <= y1:
                    attemptedCardsToDrag = [card]
                    break
                
        # establish which cards are being dragged, and also the offset of the
        # click from the cards' positions. If an error occurs, self.cardsToDrag
        # remains an empty list
        try:
            seqSize = len(attemptedCardsToDrag)
            if not seqSize:
                raise NoMove("No Move")
            if seqSize > 1:
                self.check_sequence_movable(whichCascade, seqSize)
            self.cardsToDrag = attemptedCardsToDrag[:]
            oldX, oldY = self.cardsToDrag[0].pos
            self.clickToCardOffset = cx - oldX, cy - oldY
        except IllegalMove as e:
            pass
    

#
# Movement-related functions.
#

    def check_sequence_movable(self, m, p, n=-1):
        '''
        Helper function that will take a given cascade index and a number of
        cards from that cascade to move, and will see if that sequence can be
        moved based on whether or not it's an ordered sequence, and
        whether or not there's enough empty cells and cascades to move it
        '''
        
        maxSizeOfSeq = longest_movable_sequence(self.cascade[m])
        if p > maxSizeOfSeq:
            raise IllegalMove(f'not enough cards in sequence to move {p}')
        numFreeCells = len([slot for slot in self.freecell if not slot])
        numEmptyCascades= len([i for i in range(8) if \
                                   not self.cascade[i] and i is not n])
        # having n default to -1 means that when check_sequence_movable is
        # called in getCardsToDrag, the number of empty cascades is +1 than
        # when check_sequence movable is called in multi_move_cascade_to_cascade
        # . This means that the user is allowed to drag extra cards, but if
        # they try and move the max number of cards to an empty cascade, they
        # would then get an error.
        maxCards = max_cards_to_move(numEmptyCascades, numFreeCells)
        if p > maxCards:
            raise IllegalMove(f'not enough spaces to move {p} cards')

    def multi_move_cascade_to_cascade(self, m, n, p):
        '''
        Move a sequence of 'p' cards from cascade 'm' to cascade 'n'.
        Cascade 'm' must have at least 'p' cards.  The last 'p'
        cards of cascade 'm' must be in descending rank order and
        alternating colors.

        If the move can't be made, raise an IllegalMove exception.

        Arguments:
          m, n -- cascade indices (integers between 0 and 7)
          p    -- an integer >= 0

        Return value: none
        '''
    
        if m not in range(8):
            raise IllegalMove(f'Invalid first cascade index: {m}.')
        if n not in range(8):
            raise IllegalMove(f'Invalid second cascade index: {n}.')
        if type(p) is not int or p < 0:
            raise IllegalMove(f'Invalid number of cards to move: {p}')
        if not p:
            return # Nothing happens if 0 cards are moved
        self.check_sequence_movable(m, p, n)
        firstCardIndex = len(self.cascade[m]) - p
        if firstCardIndex < 0:
            raise IllegalMove(f'not enough cards in cascade {m} to move {p}')
        firstCard = self.cascade[m][firstCardIndex]
        if not self.can_add_to_cascade(firstCard, n): # In FreeCell.py
            raise IllegalMove(f"Sequence can't move to cascade {n}")

        # Actually execute the move after checking all conditions
        cardsToMove = [self.cascade[m].pop() for i in range(p)]
        cardsToMove.reverse()
        self.cascade[n].extend(cardsToMove)
        for card in cardsToMove:
            whichIndexInCascade = self.cascade[n].index(card)
            card.loc = (f'c{n}', whichIndexInCascade)
        for card in cardsToMove:
            card.glide(card.loc)



    def automove_to_foundation(self, verbose=False):
        '''
        Make as many moves as possible from the cascades/freecells to the
        foundations.

        Argument:
          verbose -- if True, print a message when each card is automoved

        Return value: none
        '''
        
        while True:
            mustCheckAgain = False
            for i, cascade in enumerate(self.cascade):
                if cascade:
                    if ok_to_automove(cascade[-1], self.foundation, self.canvas):
                        mustCheckAgain = True
                        self.move_cascade_to_foundation(i)
                        if verbose:
                            print(f'[automove bottom of cascade {i} to \
                                                          foundation]')
            for slot, card in enumerate(self.freecell):
                if card:
                    if ok_to_automove(card, self.foundation, self.canvas):
                        mustCheckAgain = True
                        self.move_freecell_to_foundation(slot)
                        if verbose:
                            print(f'[automove freecell {slot} to foundation]')
            if not mustCheckAgain:
                break





