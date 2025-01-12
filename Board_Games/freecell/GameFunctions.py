# Name: Akshay Yeluri
# Csman login: ayeluri

'''
Module includes utility functions, as well as functions that primarily act
on games (full free cell objects).
'''

from freecell.Classes import *
from time import time

def testTime(func, object, bound):
    '''
    Testing function, used to find how efficient time-wise functions are
    '''
    timeA = time()
    for i in range(bound):
        func(object)
    timeB = time()
    print(timeB - timeA)

def makeImmutableState(game):
    '''
    Given a freecell game object, packages the game into immutable tuples and
    returns a state.
    '''
    # 0.3 seconds for 20,000
    freecell = []
    for card in game.freecell:
        if card:
            freecell.append((card.value, card.sVal))
        else:
            freecell.append(None)
    freecell = tuple(freecell)
    # Tuple of 4 values, which are either None (no cards in cell) or
    # themselves a 2-tuple representing a card
    foundation = tuple([game.foundation[i] for i in range(4)])
    # Tuple of 4 int values (0 is none)
    cascades = []
    for cascade in game.cascade:
        if cascade:
            cascades.append(tuple([(card.value, card.sVal) for card in cascade]))
        else:
            cascades.append(None)
    cascades = tuple(cascades)
    # Tuple of 8 values, which are either None (no cards in cascade) or
    # themselves a tuple of 2-tuples representing cards.
    return (foundation, freecell, cascades)

def save(game):
    '''
    Return a string representation of the state of the game.
    '''
    g = game
    s = ''
    for i in range(4):
        if g.foundation[i]:
            rankIndex = g.foundation[i]-1
            rank = all_ranks[rankIndex]
        else:
            rank = None
        s += str(rank) + ' '
    s += '\n'
    for i in range(4):
        s += str(g.freecell[i]) + ' '
    s += '\n'
    for i in range(8):
        for j in range(len(g.cascade[i])):
                s += str(g.cascade[i][j]) + ' '
        s += '\n'
    return s

def saveGameToFile(game, filename):
    '''
    Will save game 'game' to file <filename>
    '''
    with open(filename, 'w') as file:
        str = save(game)
        lineLst = str.split(sep='\n')
        for line in lineLst:
            print(line, file=file)

def load(game, s):
    '''
    Overwrite a game's state given the string representation of
    another FreeCell object.  Returns the new game.  The game is
    passed so that this will work with both FreeCell and FreeCellFull
    objects.

    Format of input string:

    xxx xxx xxx xxx   # foundations: S, H, D, C
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
        return Card(all_ranks.index(rank)+1, all_suits.index(suit))
 
    g = game

    # Strip leading and trailing newlines from s.
    lines = s.split('\n')
    while len(lines) > 0 and lines[0] == '':
        lines.pop(0)
    while len(lines) > 0 and lines[-1] == '':
        lines.pop()

    foundations = lines[0].split()
    assert len(foundations) == 4
    freecells = lines[1].split()
    assert len(freecells) == 4
    cascades = list(map(lambda s: s.split(), lines[2:]))

    str_ranks = \
      ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

    # Load foundations.
    fnd = []
    for i in range(4):
        suit = all_suits[i]
        rank = foundations[i]
        if rank == 'None':
            fnd.append(None)
            continue
        assert rank in str_ranks
        try:
            rank = int(rank)
        except ValueError:
            pass
        fnd.append(all_ranks.index(rank)+1)
    game.foundation = fnd

    # Load freecells.
    fc = []
    for i in range(4):
        card = freecells[i]
        if card == 'None':
            fc.append(None)
        else:
            fc.append(load_card(card))
    game.freecell = fc

    # Load cascades.
    cc = []
    for i in range(8):
        cc1 = []
        if i < len(cascades):
            for card in cascades[i]:
                cc1.append(load_card(card))
        cc.append(cc1)
    game.cascade = cc

    return game

def loadFile(filename, game=FreeCell(False)):
    '''
    Will load a full freecell game from a filename
    '''
    with open(filename, 'r') as file:
        str = ''.join([line for line in file if line[0] != '#'])
    load(game, str)
    return game

def dump(game):
    '''
    Print the state of the board to the terminal.
    '''

    g = game

    print('---- FOUNDATIONS ----')
    print('Spades:   {}'.format(g.foundation[0]))
    print('Hearts:   {}'.format(g.foundation[1]))
    print('Clubs:    {}'.format(g.foundation[2]))
    print('Diamonds: {}'.format(g.foundation[3]))
    
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
    fs  = []
    for i in range(4):
        if f[i]:
            fs.append(str(all_ranks[f[i]-1]))
        else:
            fs.append(' ')
    fcs = list(map(freecellsToString, g.freecell))

    print()
    print('---- FOUNDATIONS ----- ----- FREECELLS ------')
    print('   S    H    C    D       0    1    2    3   ')
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


