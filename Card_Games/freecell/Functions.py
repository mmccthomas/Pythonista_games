# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

'''
This module has simple functions that do small tasks. One set checks
Boolean conditions, one set takes game states that are 'unmuted' (converted from
tuples to lists) and changes the states, and one set does simple calculations
'''


#
#  Bool functions -- functions that check one thing, return true or false
#

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

def goes_below(cardA, cardB):
    '''
    Return True if cardA can go below cardB (in a cascade).

    Arguments:
      cardA -- a card Tuple
      cardB -- a card Tuple in a cascade
    
    Return value:
      True if cardA can go below cardB, otherwise False
    '''
    valA, sValA = cardA
    valB, sValB = cardB
    if (sValA + sValB) % 2 == 0:
        return False
    if valA is not valB - 1:
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

def can_add_to_cascade(card, cascades, i):
    '''
    Return True if a card can be added to a cascade.
    
    Arguments:
        card       -- a Card tuple
        i -- which cascade to add to (an int from 0 to 7)
        
    Return value: True if the card can be moved, else False
    '''
    if cascades[i]:
        topCard = cascades[i][-1]
        if not goes_below(card, topCard):
            return False
    return True
        
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

#
#  Basic movement functions modifying lists (used by ExecuteCommand). These
#  act on the list versions of the tuples packaged in states. The idea is
#  states are immutable, except when a command is executed. Then, a state is
#  'unmuted' and its lists are modified by these functions, before a new state
#  is made that is again unmutable.
#

def move_cascade_to_freecell(cascades, freecell, n):
    '''
    Move card from bottom of cascade 'n' to freecell list.
    '''
    for slot, card in enumerate(freecell):
        if not card:
            freecell[slot] = cascades[n].pop()
            return

def move_freecell_to_cascade(freecell, cascades, m, n):
    '''
    Move freecell card 'm' to cascade 'n'.
    '''
    bottomCard = freecell[m]
    cascades[n].append(bottomCard)
    freecell[m] = None

def move_cascade_to_cascade(cascades, m, n):
    '''
    Move a single card from one cascade to another.
    '''
    bottomCard = cascades[m][-1]
    cascades[n].append(cascades[m].pop())

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

#
#  Complex movement functions modifying lists (used by ExecuteCommand). 
#

def multi_move_cascade_to_cascade(cascades, m, n, p):
    '''
    Move a sequence of 'p' cards from cascade 'm' to cascade 'n'.
    Cascade 'm' must have at least 'p' cards.  The last 'p'
    cards of cascade 'm' must be in descending rank order and
    alternating colors.
    
    Arguments:
      cascades -- list of cascades
      m, n -- cascade indices (integers between 0 and 7)
      p    -- an integer >= 0
      
    Return value: none
    '''
    cardsToMove = [cascades[m].pop() for i in range(p)]
    cardsToMove.reverse()
    cascades[n].extend(cardsToMove)

def automove_to_foundation(foundation, freecell, cascades):
    '''
    Make as many moves as possible from the cascades/freecells to the
    foundations.
    
    Argument:
      foundation -- a foundation list to move cards to
      freecell -- a freecell list to move cards from
      cascades -- a list of cascade lists to move cards from

    Return value: none
    '''
    while True:
        mustCheckAgain = False
        for i, cascade in enumerate(cascades):
            if cascade:
                if ok_to_automove(cascade[-1], foundation):
                    mustCheckAgain = True
                    move_cascade_to_foundation(cascades, foundation, i)
        for slot, card in enumerate(freecell):
            if card:
                if ok_to_automove(card, foundation):
                    mustCheckAgain = True
                    move_freecell_to_foundation(freecell, foundation, slot)
        
        if not mustCheckAgain:
            break
#
#  Calculation functions. Find a single int (for making the moves list)
#

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
    tuple of cards that can be moved in a single move.  Cards in the sequence
    must be in strict descending order and alternate colors.

    Arguments:
      cards -- a tuple of cards (a cascade in its usual state)

    Return value:
      the number of cards at the end of the tuple forming the longest
      sequence
    '''

    sizeOfSeq = 0
    if cards:
        sizeOfSeq = 1
    for i in range(-1, -len(cards), -1):
        topCard = cards[i-1]
        bottomCard = cards[i]
        if not goes_below(bottomCard, topCard):
            break
        sizeOfSeq += 1
    return sizeOfSeq
