# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

'''
This module has functions that act on States. A state is very similar to a
freecell object, and can be thought of as a snapshot of a freecell object in
time. States are immutable, and thus fit well in dictionaries and sets.
A state is a 3-tuple, consisting of:
    foundation -- a tuple of four integers, or None if there is no card in the
                  said foundation. The index of each value in the foundation
                  is the same index as the suit in all_suits
    freecell   -- a tuple of four values also, which can be None if that
                  particular freecell is empty. Otherwise, the value will be a
                  card tuple (a 2-tuple of (value, sVal) representing a card
    cascades   -- a tuple of 8 values, which can be None if a cascade is empty.
                  Otherwise, the value will itself be a tuple of card tuples,
                  so if there are 7 caards in a particular column of the
                  cascades, that column will be a tuple of 7 2-tuples
'''

from freecell.Functions import *
from freecell.Classes import *
from freecell.GameFunctions import *

def remakeGame(firstState, movesLst, waitForInput=False, noprint=False):
    '''
    Given an initial state and a list of moves, will recreate the game, printing
    out each subsequent state and the move preceding it.
    '''
    totalMoves = len(movesLst)
    state = firstState
    if not noprint: 
		    for i, move in enumerate(movesLst):
		        if waitForInput:
		            input('Hit <Enter> to see the next move!')
		        print(f'Move {i+1} of {totalMoves}: {move}')
		        state = executeCommand(state, move)
		        printState(state)

def findLowestState(Set, func):
    '''
    Given a set of states, finds the highest priority state according to the
    value returned by passing that state to a function. Can be used to
    find a state with the lowest value according to an evaluation function in a
    priority queue. Does the same thing as:
            return reduce(lambda x, y: min(x, y, key=func), Set)
    but is significantly faster.
    '''
    
    initParentState = False
    for state in Set:
        if not initParentState:
            parentState = state
            initParentState = True
            oldMin = func(parentState)
            continue
        newMin = func(state)
        if newMin < oldMin:
            parentState = state
            oldMin = newMin
    return parentState

def game_is_won(state):
    '''
    Return True if a state represents the solved, winning state.
    '''
    foundation, freecell, cascades = state
    for cascade in cascades:
        if cascade:
            return False
    for potentialCard in freecell:
        if potentialCard:
            return False
    for val in foundation:
        if val != 13:
            return False
    return True

def findValidMoves(state):
    '''
    Return a list of valid moves that can be made from a certain state in
    a freecell game
    '''
    # for 20,000 runs takes 1.67 seconds
    foundation, freecell, cascades = state
    movesLst = []
    nc = 0
    nf = 0
    emptyCascades = set()
    
    # Go through freecells, find moves where card goes from freecell to cascade
    # or foundation, find number of empty freecells
    for slot, card in enumerate(freecell):
        if card:
            if can_add_to_foundation(card, foundation):
                movesLst.append(f'xf {slot}')
            for i in range(8):
                if can_add_to_cascade(card, cascades, i):
                    movesLst.append(f'xc {slot} {i}')
        else:
            nf += 1

    # Go through cascades, find moves where card goes from bottom of cascade
    # to freecell or foundation, find number of empty foundation
    for i, cascade in enumerate(cascades):
        if cascade:
            card = cascade[-1]
            if can_add_to_foundation(card, foundation):
                movesLst.append(f'cf {i}')
            if nf:
                movesLst.append(f'cx {i}')
        else:
            nc += 1
            emptyCascades.add(i)

    # find maxCards in moving to a non-empty cascade, and an empty cascade (B)
    maxCards = max_cards_to_move(nc, nf)
    maxCardsB = maxCards - nc

    # Go through each cascade, compare to every other cascade
    for m, cascade in enumerate(cascades):
        if not cascade:
            continue
        maxSeq = longest_movable_sequence(cascade)
        for n in range(8):
            if m == n:
                continue
            if n in emptyCascades:
                pmax = min(maxCardsB, maxSeq)
                movesLst.append(f'cc {m} {n}')
                for p in range(2, pmax + 1):
                    movesLst.append(f'cc {m} {n} {p}')
                continue
            pmax = min(maxCards, maxSeq)
            topCard = cascades[n][-1]
            bottomCard = cascade[-1]
            if goes_below(bottomCard, topCard):
                movesLst.append(f'cc {m} {n}')
                continue
            for p in range(2, pmax + 1):
                bottomCard = cascade[-p]
                if goes_below(bottomCard, topCard):
                    movesLst.append(f'cc {m} {n} {p}')
                    break

    return movesLst

def makeGameFromState(state):
    '''
    Given an immutable state, will return a game object currently at the same
    values as the state.
    '''
    # 1.26 s
    foundation, freecell, cascades = state
    game = FreeCell(False)
    for i, value in enumerate(foundation):
        game.foundation[i] = value
    for i, card in enumerate(freecell):
        if not card:
            game.freecell[i] = None
        else:
            game.freecell[i] = Card(card[0], card[1])
    for i, cascade in enumerate(cascades):
        game.cascade[i] = []
        if cascade:
            for card in cascade:
                game.cascade[i].append(Card(card[0], card[1]))
    return game

def printState(state):
    '''
    Nicely displays a state -- makes use of the display function in
    GameFunctions.
    '''
    display(makeGameFromState(state))

def constructPath(state, parentAndPathDict):
    '''
    Given a state and a dictionary mapping states to the previous state
    and the move to get between the two, will work backwards and assemble a list
    of all moves made to get from the initial state in the dictionary to the
    state passed as an argument.
    '''
    states = []
    actionsLst = []
    while True:
        row = parentAndPathDict.get(state)
        if not row:
            break
        actionsLst.append(row[1])        
        state = row[0]
        states.append(state)
    actionsLst.reverse()
    states.reverse()
    return actionsLst, states

def hFunction(state, cycles):
    '''
    A heuristic function used by the non-basic A* and Greedy Search algorithms
    that evaluates approximately how many moves are between a freecell state
    and solution based on two things: number of cycles and number of cards
    already in foundations.
    
    Arguments:
        state -- an immutable 3-tuple representing a snapshot of a freecell game
        cycles -- a set of frozensets, where each frozenset represents a cycle
    
    Return:
        an integer approximate of moves till completiong
    '''
    foundation = state[0]
    m_f = 0
    for val in foundation:
        if val:
            m_f += val
    m_e = len(cycles)
    return 52 - m_f + m_e

def oneSuitCyle(cardA, cardB):
    '''
    Given two cards (each a 2-tuple), returns a frozenset with a 4-tuple
    representing the edge that defines a cycle (if the edge, the connection
    between two cards) is broken, the cycle ceases to exist
    '''
    return frozenset({(*cardA, *cardB)})

def makeCycles(state):
    '''
    Given a state, makes a set of cycles for the state, where a cycle is a
    frozenset of the relevant edges (all edges that must be destroyed for the
    cycle to not exist). An edge is a 4-tuple (2 adjacent cards put together)
    '''
    cascades = state[2]
    cycles = set()
    
    
    for col1, cascade1 in enumerate(cascades):
        if not cascade1:
            continue
        for row1, cardX1 in enumerate(cascade1):
            # For each card in the cascades...
            x1rank, x1suit = cardX1
            
            for cardY1 in cascade1[:row1]:
                # If another card above it in the same cascade...
                if (cardY1[1] is not x1suit) or (cardY1[0] > x1rank):
                    continue
                # is of the same suit and a lower rank...
                cycle = oneSuitCyle(cascade1[row1-1], cardX1)
                # then the first card (cardX1) and the card directly above it
                # make the edge of a cycle including both cardX1 and cardY1
                cycles.add(cycle)
                break
    return cycles

def findSuccessors(state, cycles):
    '''
    Given a state and its set of cycles, will find out what moves can be made
    on a state, execute all those moves, figure out what the cycles set would
    be for each new state, and return a list of 3-tuples, where each 3-tuple
    is a new childState, the move made to get to that child state, and the
    set of cycles associated with the new state
    '''
    #5.0 seconds for 20,000 runs
    childAndPathLst = []
    movesLst = findValidMoves(state)
    for move in movesLst:
        child = state # works cuz all tuples/immutables
        newCycles = updateCycles(child, move, cycles.copy())
        # figure out what the new cycles set would be even before finding the
        # new state.
        child = executeCommand(child, move)
        toAdd = (child, move, newCycles)
        childAndPathLst.append(toAdd)
    return childAndPathLst


def executeCommand(state, str):
    '''
    Given a command that is a legal move that could be entered in a freecell
    game, will execute the move on a state and automove cards to foundations.
    Essentially unpackages a state into non-immutable parts (tuples becomes
    lists), makes a move, automoves cards to the foundations, repackages the
    modified parts into an immutable tuple, and returns a new game state, a
    result of the previous move.
    '''
    foundation, freecell, cascades = tuple(map(list, state))
    # deal with empty pile
    cascades = [list(p) if p else [] for p in cascades]
    #cascades = list(map(list, cascades))
    # All mutable things now
    cmd = str.strip().split()
    if cmd[0] == 'cf' and len(cmd) == 2:
        n = int(cmd[1])
        move_cascade_to_foundation(cascades,foundation,n)
    elif cmd[0] == 'xf' and len(cmd) == 2:
        n = int(cmd[1])
        move_freecell_to_foundation(freecell, foundation, n)
    elif cmd[0] == 'cx' and len(cmd) == 2:
        n = int(cmd[1])
        move_cascade_to_freecell(cascades, freecell, n)
    elif cmd[0] == 'xc' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        move_freecell_to_cascade(freecell, cascades, m, n)
    elif cmd[0] == 'cc' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        move_cascade_to_cascade(cascades, m, n)
    elif cmd[0] == 'cc' and len(cmd) == 4:
        m = int(cmd[1])
        n = int(cmd[2])
        p = int(cmd[3])
        multi_move_cascade_to_cascade(cascades, m, n, p)
    #automove_to_foundation(foundation, freecell, cascades)
    cascades = tuple(map(tuple, cascades))
    newState = tuple(map(tuple, (foundation, freecell, cascades)))
    # repackage everything
    return newState

def updateCycles(child, move, cycles):
    '''
    Given a state, a move to make on that state, and the associated set of
    cycles with a state, will return the new set of cycles for the new state
    that would be produced by applying the move to the child state. Allows
    the avoidance of repeatedly calling the makeCycles function, which is very
    inefficient.
    '''

    foundation, freecell, cascades = child
    cmd = move.strip().split()
    
    def cycleRemover(i, n):
        '''
        Given a cascade index n, and a card's index in that cascade i, finds
        what edges would be broken if that card left the cascade, and
        since breaking edges destroys cycles, also edits the cycles set.
        '''
        
        cyclesToRemove = set()
        cascade = cascades[n]
        if len(cascade) < 2:
            return cycles
        edgeBroken = (*cascade[i-1], *cascade[i])
        for cycle in cycles:
            if edgeBroken in cycle:
                cyclesToRemove.add(cycle)
        return cycles - cyclesToRemove
    
    def cycleAdder(bottomCard, col1, extraCards=None):
        '''
        Given a card to add to a cascade, a cascade index col1, and some extra
        cards list to append to the cascade before adding the card, finds what
        new cycles would be created as a result of adding that card.
        '''
        if cascades[col1]:
            cascade1 = list(cascades[col1])
        else:
        	cascade1 = []
        if extraCards:
             cascade1 += extraCards
        if not cascade1:
            return None
        cardX1 = bottomCard
        x1rank, x1suit = cardX1
        topCard = cascade1[-1]
    
        for cardY1 in cascade1[:]:
            if (cardY1[1] is not x1suit) or (cardY1[0] > x1rank):
                continue
            cycle = oneSuitCyle(topCard, cardX1)
            cycles.add(cycle)
            break

    if cmd[0] == 'xf':
        return cycles
    elif cmd[0] == 'xc' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        bottomCard = freecell[m]
        cycleAdder(bottomCard, n)
    elif cmd[0] == 'cx' and len(cmd) == 2:
        n = int(cmd[1])
        cycles = cycleRemover(-1, n)
    elif cmd[0] == 'cc' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        cycles = cycleRemover(-1, m)
        bottomCard = cascades[m][-1]
        cycleAdder(bottomCard, n)
    elif cmd[0] == 'cc' and len(cmd) == 4:
        m = int(cmd[1])
        n = int(cmd[2])
        p = int(cmd[3])
        max = len(cascades[m])
        extraCards = []
        for i in range(max-p, max):
            if not i == 0:
                cycles = cycleRemover(i, m)
            bottomCard = cascades[m][i]
            cycleAdder(bottomCard, n, extraCards)
            extraCards.append(bottomCard)
            # As more cards are moved to another cascade, increased chance of
            # making more cycles there.

    return cycles

def hFunctionBasic(state):
    '''
    A more basic heuristic function used by A* and greedy (basic) algorithms,
    does not consider cycles at all. Only subtracts number of cards in the
    foundations from 52
    '''
    # For 20,000 runs takes 0.0103759765625
    foundation = state[0]
    m_f = 0
    for val in foundation:
        if val:
            m_f += val
    return 52 - m_f

def findSuccessorsBasic(state):
    '''
    A more basic finding successor function, does not involve cycles.
    '''
    #5.0 seconds for 20,000 runs
    childAndPathLst = []
    movesLst = findValidMoves(state)
    for move in movesLst:
        child = state
        child = executeCommand(child, move)
        toAdd = (child, move)
        childAndPathLst.append(toAdd)
    return childAndPathLst








