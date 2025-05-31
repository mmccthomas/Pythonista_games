import random
from time import time
import numpy as np
import inspect
import json
import console
from operator import itemgetter, attrgetter
from itertools import permutations
""" This is an attempt to solve suguru puzzles to assess difficulty
Does it matter where  the start visible numbers are located?

This uses no Pythonista code
Chris Thomas April 2025
"""
BLOCK = '#'
SPACE = ' '
SIZE = 9  # fixed f
FILENAME = 'suguru.txt'


class Cell():
    """ an individual cell """

    def __init__(self, loc, c, value=0):
        if isinstance(loc, tuple):
            self.r, self.c = loc
        else:
            self.r = loc
            self.c = c
        self.coordinate = (self.r, self.c)
        self.value = value
        self.possibles = []

    def __repr__(self):
        return f'Cell({self.r}, {self.c}) = {self.value}'

    def add_possible(self, value):
        self.possibles.append(value)

    def remove_possible(self, value):
        if value in self.possibles:
            self.possibles.remove(value)

    def update_board(self, board, value):
        board[self.coordinate] = value

    @property
    def solution(self):
        return (self.r, self.c, self.value)

    def parent(self, obj):
        for cage in obj.cages:
            if self in cage.members:
                return cage
        raise AssertionError('cell parent not found')

    def get_neighbour_vals(self, board, N=3):
        # get a subset of board of max NxN, centred on loc
        # subset is computed with numpy slicing
        # to make it as fast as possible
        # max and min are used to clip subset close to edges
        self.neighbour_vals = board[
            max(self.r - (N - 2), 0):min(self.r + N - 1, board.shape[0]),
            max(self.c - 1, 0):min(self.c + 2, board.shape[1])]
        return self.neighbour_vals

    def get_neighbours(self, board, N=3):
        # get a subset of board of max NxN, centred on loc
        # subset is computed with numpy slicing
        # to make it as fast as possible
        # max and min are used to clip subset close to edges
        top = max(self.r - (N - 2), 0)
        left = max(self.c - 1, 0)
        bottom = min(self.r + (N - 1), board.shape[0])
        right = min(self.c + 2, board.shape[1])
        self.neighbours = [(r1, c1) for r1 in range(top, bottom)
                           for c1 in range(left, right)
                           if (r1, c1) != self.coordinate]
        return self.neighbours


class CageItem():
    """ a cage of cells"""

    def __init__(self, index):
        self.index = index
        self.members = []
        self.neigbours = np.zeros((1, 1), dtype=int)
        self.neigbour_vals = np.zeros((1, 1), dtype=int)

    def __repr__(self):
        return f'Cage {self.index}({self.length})'

    def add_member(self, cell):
        self.members.append(cell)

    def get_members(self):
        return self.members

    @property
    def coordinates(self):
        return [member.coordinate for member in self.members]

    @property
    def solution(self):
        return [member.solution for member in self.members]

    @property
    def length(self):
        return len(self.members)

    def get_cell(self, loc):
        """ return Cell of this cage if contains loc """
        for cell in self.members:
            if tuple(loc) == cell.coordinate:
                return cell
        return None

    def prepare_options(self):
        # use only cage locations, not values
        # possibles are all possible numbers in each square
        for cell in self.members:
            cell.possibles = list(range(1, self.length + 1))


class Board():
    """collection of Cages """

    def __init__(self, cageset=None):
        self.cages = []
        self.board = np.zeros((1, 1), dtype=int)
        if cageset:
            self.load_cages(cageset)
        self.update()
        for cage in self.cages:
            cage.prepare_options()

    def update(self):
        self.cage_coords = [cage.coordinates for cage in self.cages]
        # self.compute_board()

    def add_cage(self, cage):
        if isinstance(cage, CageItem):
            self.cages.append(cage)
            self.update()
        else:
            raise AssertionError(f'{cage} is not a Cage')

    def get_cages(self):
        return self.cages

    def get_cage(self, loc):
        pass

    def clear_cages(self):
        for cage in self.cages:
            for cell in cage.members:
                cell.value = 0

    def load_cages(self, cage_set):
        """ puzzle is a list of list of (r,c, val)"""
        cage_set = sorted(cage_set)

        for index, cage in enumerate(cage_set):
            c_ = CageItem(index)
            for cell in cage:
                c_.add_member(Cell(*cell))
            self.add_cage(c_)
        self.board = self.compute_board()

    def compute_board(self):
        # create cage view of board
        # set board very big, then reduce
        board = np.zeros((20, 20), dtype=int)
        for cage in self.cages:
            for item in cage.members:
                board[item.coordinate] = item.value
        # furthest non zero value
        r, c = np.max(np.argwhere(board > 0), axis=0)
        board = board[:r + 1, :c + 1]
        return board

    def __repr__(self):
        return self.print_cage_board(which=None, highlight=None)

    def find_cell(self, loc):
        for cage in self.cages:
            cell = cage.get_cell(loc)
            if cell:
                return cell
        raise AssertionError(loc)

    def parent(self, loc):
        for cage in self.cages:
            cell = cage.get_cell(loc)
            if cell:
                return cage
        raise AssertionError(loc)

    def is_same_cage(self, loc1, loc2):
        """Returns true if two coordinates belong to the same cage.
          """
        try:
            return self.parent(loc1) == self.parent(loc2)
        except AssertionError:
            return False

    def print_cage_board(self, which=None, highlight=None):
        """Print the board with cages to the console.
        :param which: text to identify board
        :param highlight: list of r,c locations to underline content
        """
        msg_list = []
        msg_list.append(f'board: {which}')
        Y, X = self.board.shape
        msg_list.append(f'+{"---+" * X}')

        for y in range(Y):
            line = ''
            sep_line = "|"
            line += sep_line
            for x in range(X):
                if highlight and (y, x) in highlight:
                    value = str(self.board[y][x]) + '\u0333'
                else:
                    value = str(self.board[y][x])
                end_char = "|"
                if x < X and self.is_same_cage((y, x), (y, x + 1)):
                    end_char = " "
                if y < Y and self.is_same_cage((y, x), (y + 1, x)):
                    sep_line += "   +"
                else:
                    sep_line += "---+"
                line += f" {value if  value != '0' else ' '} {end_char}"
            msg_list.append(line)
            msg_list.append(sep_line)
        msg = '\n'.join(msg_list)
        return msg

    def get_possibles(self):
        """get all possibles, formatted for printing """

        return '\n'.join([
            ' '.join([
                f'{member.coordinate}, {member.possibles}'
                for member in cage.members
            ]) for cage in self.cages
        ])

    def flat_list(self):
        return sorted(sum([cage.coordinates for cage in self.cages], []),
                      key=itemgetter(0, 1))


# ###############################################################################


class SuguruSolve():

    def __init__(self, test=None):
        self.debug = False
        self.test = test

    def time_us(self, t0, msg=''):
        print(f'{msg} {int((time()-t0) * 1e6):_}us')

    def cage_board_view(self, cages):
        # create cage view of board
        # set board very big, then reduce
        board = np.zeros((20, 20), dtype=int)
        for cage in cages:
            for item in cage:
                r, c, number_val = item
                board[(r, c)] = number_val
        # furthest non zero value
        r, c = np.max(np.argwhere(board > 0), axis=0)
        board = board[:r + 1, :c + 1]
        return board

    def load_puzzles(self):
        """ return a dictionary of list of puzzles for each size"""
        try:
            with open(FILENAME, 'r') as f:
                data = f.read()
            puzzle_strings = data.split('\n')
            puzzles = {'5x5': [], '6x6': [], '7x7': [], '8x8': [], '9x9': []}
            cage_sets = [json.loads(p) for p in puzzle_strings if p]
            for cage in cage_sets:
                board = self.cage_board_view(cage)
                shape = f'{board.shape[0]}x{board.shape[1]}'
                puzzles[shape].append((board, cage))
            self.msg = '\n'.join(
                [f'{k},  {len(v)} puzzles' for k, v in puzzles.items()])
            if self.test:
                print(self.msg)
            return puzzles
        except FileNotFoundError:
            pass

    def store_valid_puzzle(self, cg):
        """ add valid puzzle to file """
        # store in cages
        cages = [[(cage[0], cage[1], int(self.board[(cage[0], cage[1])]))
                  for cage in cagelist] for cagelist in cg.cages]
        with open('suguru.txt', 'a') as f:
            f.write(json.JSONEncoder().encode(cages) + '\n')

    def prepare_options(self):
        # use only cage locations, not values
        # possibles are all possible numbers in each square
        for cage in self.board_obj.cages:
            for cell in cage.members:
                cell.possibles = list(range(1, cage.length + 1))
                cell.value = 0

    def add_known(self, known=None):
        """ if specified, known is list of Cell objects"""
        replaced = False
        # now fill initial squares
        if known:
            for item in known:
                self.board_obj.board[item.coordinate] = item.value
                cell = self.board_obj.find_cell(item.coordinate)
                cell.possibles = []
                cell.value = item.value
                replaced = True
            # fill single squares
            for cage in self.board_obj.cages:
                if cage.length == 1:
                    cell = cage.members[0]
                    cell.value = 1
                    cell.possibilities = []
                    self.board_obj.board[cell.coordinate] = 1
                    replaced = True
        return replaced

    def filter_adjacent(self):
        """ remove value of known value from adjacent cells """
        number_locs = np.argwhere(self.board_obj.board > 0)
        for loc in number_locs:
            cell = self.board_obj.find_cell(loc)
            neighbours = cell.get_neighbours(self.board_obj.board)
            for neighbour in neighbours:
                c = self.board_obj.find_cell(neighbour)
                c.remove_possible(cell.value)

    def filter_same_cage(self):
        """ remove value of known value all members of cage """
        number_locs = np.argwhere(self.board_obj.board > 0)
        for loc in number_locs:
            cage = self.board_obj.parent(loc)
            base_cell = self.board_obj.find_cell(loc)
            for cell in cage.members:
                cell.remove_possible(base_cell.value)

    def remove_single_poss(self):
        for cage in self.board_obj.cages:
            for cell in cage.members:
                if len(cell.possibles) == 1:
                    cell.value = cell.possibles[0]
                    self.board_obj.board[cell.coordinate] = cell.value
                    cell.possibles = []

    def filter_same_possibilities(self):
        """if 2 cells  has  samepossibilities,
        and more than 1 adjacent cells have
        same possibilities, then adjacent cell cannot have those possibles
        if cell has [A, B, C] and neighbours have [A, B] or [B, A],
        cell cannot have [A, B]"""
        for cage in self.board_obj.cages:
            for cell in cage.members:
                base_poss = cell.possibles
                if len(base_poss) < 2:
                    continue
                neighbours = [
                    self.board_obj.find_cell(loc)
                    for loc in cell.get_neighbours(self.board_obj.board)
                ]
                # get neighbours with only 2 possibles
                unknown_neighbours = [(neighbour, neighbour.possibles)
                                      for neighbour in neighbours
                                      if len(neighbour.possibles) == 2]
                # construct list of neighbours with possibles and parent cages
                neighbour_list = []
                for neighbour, possibles in unknown_neighbours:
                    parent = neighbour.parent(self.board_obj)
                    neighbour_list.append((possibles, parent))
                # print(f'{cell=}, {base_poss=}, {neighbour_set=}')
                # now test for same numbers in same cage
                for (poss, par) in neighbour_list:
                    c = neighbour_list.count((poss, par))
                    if c == 2:
                        [cell.remove_possible(p) for p in poss]
                        # print(f'removed {poss} from {cell}')

    def filter_larger(self):
        """if a cell is adjacent to all cells in a neighbouring group,
           it has to have values higher than length of neighbouring group"""
        for cage in self.board_obj.cages:
            for cell in cage.members:
                neighbours = [
                    self.board_obj.find_cell(loc)
                    for loc in cell.get_neighbours(self.board_obj.board)
                ]
                # find if all neighbours in same cage
                parents = [
                    neighbour.parent(self.board_obj)
                    for neighbour in neighbours
                ]
                if len(set(parents)) == 1 and len(
                        parents) == parents[0].length:
                    if cell.parent(self.board_obj).length > parents[0].length:
                        [
                            cell.remove_possible(p)
                            for p in range(1, parents[0].length + 1)
                        ]
                        print(
                            f'removed {list(range(1, parents[0].length+1))} from {cell}'
                        )

    def choose(self):
        """Typically, the logic is along the lines of
        "if this cell is a 5, then this pair of cells could be 3/7 or 7/3
        with no way of determining which. Since the puzzle has a unique solution,
        the first cell must not be a 5"."""
        pass
        
    def compute_known(self, N, method=1):
        # first try is just random
        if method == 0:  #
            number_loc_list = self.board_obj.flat_list()
            random.shuffle(number_loc_list)
            known_locs = number_loc_list[:N]
            known = [self.sol_obj.find_cell(loc) for loc in known_locs]
        else:
            # try to ensure each known is random position in each cage
            # remainder go into largest cage
            known = []
            cages = sorted(self.board_obj.cages,
                           key=attrgetter('length'),
                           reverse=True)
            to_fill = [cage.index for cage in cages if cage.length > 2]
            indices = []
            i = 0
            while len(indices) < N:
                idx = to_fill[i % len(to_fill)]
                sel = random.randint(0, self.board_obj.cages[idx].length - 1)
                if (idx, sel) not in indices:
                    indices.append((idx, sel))
                    known.append(self.sol_obj.cages[idx].members[sel])
                    i += 1
        # should now have N unique row, col
        return known

    def identify_single(self, cages):
        # identify if number is only one in cage
        for cage in self.board_obj.cages:
            possibles = [cell.possibles for cell in cage.members]
            if any(possibles):
                # if possible not in possibles of other squares
                # iterate thru possible of each cage
                for i, poss in enumerate(possibles):
                    b = [set(x) for x in possibles]
                    # get indexed set
                    c = b.pop(i)
                    # diff from set of  all the rest
                    unique = c.difference(b.pop(0).union(*b))
                    if len(unique) == 1:
                        cage.members[i].possibles = list(unique)
                        # print(i, list(unique))

    def coords(self, cages):
        return [[(r, c) for r, c, _ in cage] for cage in cages]

    def check_valid(self, cell, number):
        # iterate thru number set
        # for cell
        # for each, check if surrounding squares have same number
        # return False if found
        subset = cell.get_neighbour_vals(self.board_obj.board)
        if np.any(np.isin(number, subset)):
            return False
        else:
            cell.update_board(self.board_obj.board, number)
        return True

    def fill(self, cell_no):
        """ use dfs to iterate through permutations of number set
      """
        self.fill_iteration += 1

        # return if the grid is filled
        if ~np.any(self.board_obj.board == 0):
            return True
        if cell_no == len(self.empty_cells):
            return False

        if self.fill_iteration > self.board_obj.board.size * 10:
            if self.debug:
                print('too many iterations')
            return False

        if self.debug:
            print(f'\nCell {cell_no} Recursion depth >>>>>>>>>>>>>>>>>>>>>>'
                  f'{len(inspect.stack())-self.initial_depth}')

        cell = self.empty_cells[cell_no]
        try:
            number = self.empty_possibles[cell].pop()
            for no in number:
                if self.debug:
                    # print(f'{number=}')
                    # print(self.board_obj.print_cage_board(which=f'DFS{cell}',
                    #                                       highlight=cell.coordinate))
                    pass
                if self.check_valid(cell, no):
                    if self.fill(cell_no + 1):
                        return True
                    cell.update_board(self.board_obj.board, 0)
                    if self.debug:
                        print('backing up')
        except (AttributeError, IndexError):
            return False
        return False

    def fill_remaining(self):
        """ starting with partially filled board,
        fill the rest with depth first search """
        self.permutation_dict = {
            k: list(permutations(list(range(1, k + 1))))
            for k in range(1, 7)
        }
        self.fill_iteration = 0
        self.initial_depth = len(inspect.stack())
        self.empty_cells = [
            cell for cage in self.board_obj.cages for cell in cage.members
            if cell.value == 0
        ]
        while not np.array_equal(self.board_obj.board, self.sol_obj.board):
            # print(f'{self.board_obj.board=}\n{self.sol_obj.board=}')
            [
                cell.update_board(self.board_obj.board, 0)
                for cell in self.empty_cells
            ]
            self.empty_possibles = {}
            for cell in self.empty_cells:
                perms = list(permutations(cell.possibles))
                random.shuffle(perms)
                self.empty_possibles[cell] = perms
            # print(self.empty_possibles)
            self.fill(cell_no=0)

    #########################################################################
    # main loop
    def run(self):
        """
      Main method that tries to solve each puzzle without guessing
      """
        random.seed(0)
        console.clear()

        counts = {}
        visible = {'5x5': -1, '6x6': 6, '7x7': 6, '8x8': 20, '9x9': 25}
        self.puzzles_from_file = self.load_puzzles()
        solution_dict = {}
        for group, items in self.puzzles_from_file.items():
            N = visible[group]
            counts[group] = []
            i = 0
            for solution, cages in items:
                # print('Board # ',i)
                t = time()
                self.sol_obj = Board(cages)
                self.board_obj = Board(cages)
                self.board_obj.board = np.zeros(self.sol_obj.board.shape,
                                                dtype=int)
                self.board_obj.clear_cages()
                N = len(self.board_obj.cages) + visible[group]
                i1 = 0
                # try different initial positions
                while not np.array_equal(self.board_obj.board,
                                         self.sol_obj.board):
                    self.board_obj.board = np.zeros(self.sol_obj.board.shape,
                                                    dtype=int)
                    self.board_obj.clear_cages()
                    known = self.compute_known(N=N, method=1)
                    # print(i1, 'known', known)
                    self.prepare_options()
                    index = 0
                    # iterate the board using rules
                    tries = 0
                    while np.any(self.board_obj.board == 0):
                        previous = self.board_obj.board.copy()
                        if index == 0:
                            self.add_known(known)
                            items = [k.coordinate for k in known]
                            # print(self.board_obj.print_cage_board(
                            #     which=f'Board{i}_{group},start {i1} iteration {index}',
                            #      highlight=items))
                        # print(self.board_obj.get_possibles())
                        # rule sets
                        self.filter_same_cage()
                        self.filter_adjacent()
                        self.identify_single(cages)
                        if tries > 0:
                            self.filter_same_possibilities()
                            self.filter_larger()

                        self.remove_single_poss()
                        index += 1
                        # no further progress for 3 tries
                        if np.array_equal(self.board_obj.board, previous):
                            tries += 1
                            if tries > 3:
                                # give up, fill remaining with dfs search
                                # print(self.board_obj.print_cage_board(
                                #     which=f'Board{i}_{group},start {i1} iteration {index}',
                                #      highlight=items))
                                # print(self.sol_obj.print_cage_board(which=f'solution',highlight=items))
                                # self.fill_remaining()
                                break
                        else:
                            tries = 0
                    i1 += 1
                    if i1 > 500:
                        break
                    # print('#'*32)
                board_solved = np.array_equal(self.board_obj.board,
                                              self.sol_obj.board)
                solution_dict[str(cages)] = ([c.coordinate for c in known], board_solved)
                counts[group].append(board_solved)
                print(
                    f'Board {i} in {group} solved {board_solved} in {(time()-t):.1f}s {i1} start points{"*"*1}'
                )
                print(
                    self.board_obj.print_cage_board(which=str(i),
                                                    highlight=items))
                i += 1
        for group in self.puzzles_from_file:
            print(f'{group}, {(sum(counts[group])/ len(counts[group])):.0%}')

        print(len(solution_dict))
        data = json.dumps(solution_dict)
        with open('sug_dict.txt', 'w') as f:
            f.write(data)


if __name__ == '__main__':
    SuguruSolve(test='Medium').run()

