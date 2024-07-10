import random
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)

alphabet = list()

class Board:
    def __init__(self, multiplier_file) -> None:
        multipliers = self.read_multipliers(multiplier_file)
        self.board = [[Cell((i, j), multipliers[i][j]) for j in range(15)] for i in range(15)]

    def read_multipliers(self, filename):
        with open(filename, 'r') as f:
            return [[num for num in line.split(',')] for line in f.read().split('\n')]

    def all_positions(self):
        positions = []
        for i in range(15):
            for j in range(15):
                positions.append((i, j))
        return positions

    def left(self, pos):
        i, j = pos
        return i, j - 1
    
    def right(self, pos):
        i, j = pos
        return i, j + 1

    def up(self, pos):
        i, j = pos
        return i - 1, j
    
    def down(self, pos):
        i, j = pos
        return i + 1, j
    
    def before(self, pos, is_horizontal):
        if is_horizontal:
            return self.left(pos)
        else:
            return self.up(pos)
        
    def after(self, pos, is_horizontal):
        if is_horizontal:
            return self.right(pos)
        else:
            return self.down(pos)
        
    def has_left(self, pos):
        i, j = pos
        return not((j - 1) < 0 or self.is_empty((i, j - 1)))
    
    def has_right(self, pos):
        i, j = pos
        return not((j + 1) > 14 or self.is_empty((i, j + 1)))
    
    def has_up(self, pos):
        i, j = pos
        return not((i - 1) < 0 or self.is_empty((i - 1, j)))
    
    def has_down(self, pos):
        i, j = pos
        return not((i + 1) > 14 or self.is_empty((i + 1, j)))
    
    def has_before(self, pos, is_horizontal):
        if is_horizontal:
            return self.has_left(pos)
        else:
            return self.has_up(pos)
        
    def has_after(self, pos, is_horizontal):
        if is_horizontal:
            return self.has_right(pos)
        else:
            return self.has_down(pos)

    def is_inbounds(self, pos):
        i, j = pos
        return i >= 0 and i <= 14 and j >= 0 and j <= 14 

    def is_empty(self, pos, allow_draft = True):
        i, j = pos
        tile = self.board[i][j].tile
        return (tile is None) if allow_draft else (tile is None or tile.draft)
    
    def get_pos(self, pos):
        return self.board[pos[0]][pos[1]]
          
class Cell:
    def __init__(self, position, multiplier) -> None:
        self.position = position
        self.multiplier = multiplier
        self.tile = None
    
    def is_empty(self):
        return self.tile == None
    
class Tile:
    def __init__(self, letter, point) -> None:
        self.letter = letter
        self.point = point
        self.draft = False

class Pouch: 
    def __init__(self, tile_file) -> None:
        self.tiles = list()
        self.init_tiles(tile_file)

    def init_tiles(self, filename):
        global alphabet
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line_info = line.split(',')
                alphabet.append(line_info[0])
                for i in range(int(line_info[2])):
                    self.add_tile(Tile(line_info[0], int(line_info[1])))

    def add_tile(self, tile):
        self.tiles.append(tile)

    def draw_tile(self):
        if len(self.tiles) == 0:
            return None
        index = random.randint(0, len(self.tiles) - 1)
        tile = self.tiles[index]
        self.tiles.pop(index)
        return tile
    
    def tiles_amount(self):
        return len(self.tiles)

class Player:
    def __init__(self) -> None:
        self.rack = Rack()
        self.score = 0
        self.name = ''
        
    def draw_tile(self, pouch):
        self.rack.add_tile(pouch.draw_tile())
        
    def __repr__(self):
        return self.name

class Rack:
    def __init__(self) -> None:
        self.tiles = [None] * 7

    def remove_played_tiles(self):
        for i, tile in enumerate(self.tiles):
            if tile != None and tile.draft:
                self.tiles[i] = None

    def fill_empty_tiles(self, pouch):
        for i, tile in enumerate(self.tiles):
            if tile == None:
                drawed_tile = pouch.draw_tile()
                if drawed_tile != None:
                    self.tiles[i] = drawed_tile
                else:
                    return False
        return True

    def add_tile(self, tile, pos = -1):
        if pos == -1:
            for i in range(7):
                if self.tiles[i] == None:
                    pos = i
                    break
        self.tiles[pos] = tile

    def tiles_amount(self):
        amount = 0
        for tile in self.tiles:
            if tile is not None:
                amount += 1
        return amount
    
