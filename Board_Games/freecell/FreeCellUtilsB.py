'''
FreeCellUtils.py
    Some utility functions on FreeCell instances.
'''

from CardB import *
import FreeCellB as F
import FreeCellFullB as FF


def findValidMoves(game):
    movesLst = []
    nc = 0
    nf = 0
    emptyCascades = []
    
    # Go through freecells, find moves where card goes from freecell to cascade
    # or foundation, find number of empty freecells
    for slot, card in enumerate(game.freecell):
        if card:
            if F.can_add_to_foundation(card, game.foundation, game.canvas):
                movesLst.append(f'xf {slot}')
            for i in range(8):
                if game.can_add_to_cascade(card, i):
                    movesLst.append(f'xc {slot} {i}')
        else:
            nf += 1

    # Go through cascades, find moves where card goes from bottom of cascade
    # to freecell or foundation, find number of empty foundation
    for i, cascade in enumerate(game.cascade):
        if cascade:
            card = cascade[-1]
            if F.can_add_to_foundation(card, game.foundation, game.canvas):
                movesLst.append(f'cf {i}')
            if nf:
                movesLst.append(f'cx {i}')
        else:
            nc += 1
            emptyCascades.append(i)

    # find maxCards in moving to a non-empty cascade, and an empty cascade (B)
    maxCards = FF.max_cards_to_move(nc, nf)
    maxCardsB = maxCards - nc

    # Go through each cascade, compare to every other cascade, if
    for m, cascade in enumerate(game.cascade):
        if not cascade:
            continue
        maxSeq = FF.longest_movable_sequence(cascade)
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
            topCard = game.cascade[n][-1]
            bottomCard = cascade[-1]
            if bottomCard.goes_below(topCard):
                movesLst.append(f'cc {m} {n}')
                continue
            for p in range(2, pmax + 1):
                bottomCard = cascade[-p]
                if bottomCard.goes_below(topCard):
                    movesLst.append(f'cc {m} {n} {p}')
                    break

    return movesLst

def save(game):
    '''
    Return a string representation of the state of the game.
    '''
    g = game
    s = ''
    for suit in all_suits:
        s += str(g.foundation.get(suit, 'None')) + ' '
    s += '\n'
    for i in range(4):
        s += str(g.freecell[i]) + ' '
    s += '\n'
    for i in range(8):
        for j in range(len(g.cascade[i])):
            s += str(g.cascade[i][j]) + ' '
        s += '\n'
    return s

def findCard(game, rank, suit):
    '''
    Given a game of FreeCell, a rank, and a suit,
    finds a card object
    '''
    for card in game.cards:
        if card.rank == rank and card.suit == suit:
            return card


def load(game, s, canvas):
    '''
    Overwrite a game's state given the string representation of
    another FreeCell object.  Returns the new game.  The game is
    passed so that this will work with both FreeCell and FreeCellFull
    objects.

    Format of input string:

    xxx xxx xxx xxx   # foundations: S, H, C, D,
    yyy yyy yyy yyy   # freecells: 0, 1, 2, 3
    cascade[0]
    cascade[1]
    ...
    cascade[7]

    Example:

None None A 2
6d 5c None None
6c 8s Jc 4s 9s 7c Kh
Qc Jd 10c 9d 8c 7d 6s
Qd As Qh 8d Jh 3h
4c Js Kd 3c Ah 4h
4d 9h Qs 3s 3d 10h
Kc 10s 8h 7s 6h
9c 5h 7h 5s 2h 2s
5d 10d Ks 2d

    This encodes a foundations dictionary {'A': 'D', 2: 'C'},
    a freecell list [Card(6, 'D'), Card(5, 'C'), None, None]
    cascade[0] ==> 6c 8s Jc 4s 9s 7c Kh
    cascade[1] ==> Qc Jd 10c 9d 8c 7d 6s
    etc.

    An empty cascade ==> a blank line

    '''

    def load_card(c):
        '''
        Create a card from its string representation.
        '''
        assert len(c) in [2, 3]
        suit = c[-1].upper()
        rank = c[:-1]
        nranks = map(str, range(2, 11))
        if rank in nranks:
            rank = int(rank)
        return Card(rank, suit, canvas)
 
    g = game
    
    # get rid of all old cards
    for card in game.cards:
            card.canvas.delete(card.handle)
    
    # Strip leading and trailing newlines from s.
    lines = s.split('\n')
    while len(lines) > 0 and lines[0] == '':
        lines.pop(0)
    while len(lines) > 0 and lines[-1] == '':
        lines.pop()

    # assert len(lines) == 10  # 1 line for foundation, 1 for freecells, 8 for cascades
    foundations = lines[0].split()
    assert len(foundations) == 4
    freecells = lines[1].split()
    assert len(freecells) == 4
    cascades = list(map(lambda s: s.split(), lines[2:]))

    str_ranks = \
      ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    randoCard = load_card('As')
    randoCard.flip()
    game.cards.clear()

    # Load foundations.
    backImage = PhotoImage(file='pics/back111.gif')
    fnd = {}
    for i in range(4):
        suit = all_suits[i]
        rank = foundations[i]
        if rank == 'None':
            continue
        assert rank in str_ranks
        try:
            rank = int(rank)
        except ValueError:
            pass
        fnd[suit] = rank
        lastIndex = all_ranks.index(rank)
        for rank in all_ranks[:lastIndex+1]:
            card = load_card(f'{rank}{suit.lower()}')
            card.flip()
            game.cards.append(card)
            game.foundationCards.append(card)
            card.glide(f'f{i}')
            card.flip(True)
    game.foundation = fnd


    # Load freecells.
    fc = []
    for i in range(4):
        card = freecells[i]
        if card == 'None':
            fc.append(None)
        else:
            card = load_card(card)
            game.cards.append(card)
            fc.append(card)
            card.flip()
            card.glide(f'x{i}')
            card.flip(True)
    game.freecell = fc

    # Load cascades.
    cc = []
    for i in range(8):
        cc1 = []
        if i < len(cascades):
            for index, card in enumerate(cascades[i]):
                card = load_card(card)
                game.cards.append(card)
                cc1.append(card)
                card.flip()
                if i == len(cascades) - 1:
                    if index == len(cascades[i]) - 1:
                        del randoCard
                card.glide((f'c{i}', index))
                card.flip(True)
        cc.append(cc1)
    game.cascade = cc
    game.history = []
    
    
    return game

def dump(game):
    '''
    Print the state of the board to the terminal.
    '''

    g = game

    print('---- FOUNDATIONS ----')
    print('Spades:   {}'.format(g.foundation.get('S', '')))
    print('Hearts:   {}'.format(g.foundation.get('H', '')))
    print('Diamonds: {}'.format(g.foundation.get('D', '')))
    print('Clubs:    {}'.format(g.foundation.get('C', '')))
    print('---- FREECELLS ----')
    for i in range(4):
        card = g.freecell[i]
        if card == None:
            card = ''
        print(f'{i+1}: {card}')
    print('---- CASCADES ----')
    for i in range(8):
        print(f'{i + 1}: ', end='')
        cascade = g.cascade[i]
        print(list(map(str, cascade)))

def display(game):
    '''
    Print the state of the board to the terminal in a form
    which is pleasant to read.
    '''

    def freecellsToString(fc):
        if fc == None:
            return '  '
        else:
            return str(fc)

    g   = game
    f   = g.foundation
    cs  = g.cascade
    fs  = [str(f.get(s, '  ')) for s in 'SHDC']
    fcs = list(map(freecellsToString, g.freecell))

    print()
    print('---- FOUNDATIONS ----- ----- FREECELLS ------')
    print('   S    H    D    C       0    1    2    3   ')
    print()
    print(f"  {fs[0]:>2}   {fs[1]:>2}   {fs[2]:>2}   {fs[3]:>2}", end='    ')
    print(f"  {fcs[0]:>2}   {fcs[1]:>2}   {fcs[2]:>2}   {fcs[3]:>2}")
    print()
    print('----------------- CASCADES ------------------')
    print('     0    1    2    3    4    5    6    7')
    print()
    maxlen = max(map(len, cs))
    for i in range(maxlen):
        print('   ', end='')
        for j in range(8):
            if i < len(cs[j]):
                print(f'{str(cs[j][i]):>3}  ', end='')
            else:
                print('     ', end='')
        print()
    print()

