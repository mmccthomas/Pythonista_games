"""This is an attempt to generate a Fiveways puzzle
The listed words can fit into the grid in one of five ways - up, down, left, right or diagonally.
the letters provided in the grid is the initial letter of one of the words.
On completion, every square in the grid will contain a letter. Letters,
including the starter letters, can appear in more than one
However, don't forget that a starter letter is the initial letter of just one of the listed words.
When solving, it will help you to strike through the starter letters of the words as you fill them in the grid.

Words are not themed.

routine needs to be super fast as lots of words will be searched

The algorithm uses a wordsearch filler for a set of N words,
words are drawn from 10k wordset with lengths defined in dictionary
After this, gaps are filled with a simple search algorithm with min word length of 4,
with final gaps min length 3 letters. the search algorithm tries to start a word at each 
blank position, accepting the first word it tinds.

# Generate N random start locations and letters
# most lengths 5,6,7

Also added Krossways generator
Krossways has a number of start locations.
all words start at these locations


new try. 
place longest words first along diagonals where they will not clash
check each possible does not block child words in n,s,e,w directions
having exhausted diagonals, then deal with vertical anf horizontal. 
aiming to fill as many as possible.
"""
import random
import numpy as np
from collections import defaultdict, Counter, namedtuple
import inspect
import cProfile
from operator import attrgetter, itemgetter
from itertools import groupby
import re
from math import prod
import os
import sys
import string
from copy import deepcopy, copy
from time import time
import console
from queue import Queue
import base_path

base_path.add_paths(__file__)
from Letter_game import Word
from gui.gui_interface import Gui
import word_square_gen
import crossword_create
#from Krossword import KrossWord
sys.path.append(os.path.expanduser('~/Documents/site-packages/pyconstraint'))
from constraint import Problem, Domain, Constraint, AllDifferentConstraint
from constraint import FunctionConstraint

WORDLIST = "wordlists/words_20000.txt"
# avoid 3 letter words till near the end
# WORDLIST = "wordlists/5000-more-common_sorted.txt"
LETTERS3 = "wordlists/letters3_common.txt"
# number or words in ineavh length to choose
# percentages
STATS = {4: 5, 5: 31, 6: 26, 7: 18, 8: 13, 9: 5, 10: 5}
UNFILLED = '.'


def add(a, b):
    """ helper function to add 2 tuples """
    return tuple(p + q for p, q in zip(a, b))


def sub(a, b):
    """ helper function to add 2 tuples """
    return tuple(p - q for p, q in zip(a, b))


def set_board(board, loc, val):
    board[loc] = val


class Cross():

    def __init__(self):
        self.debug = False
        self.debug2 = False
        self.debug3 = False
        self.min_word_length = 3
        self.max_word_length = 11
        self.max_dfs_iteration = 200
        self.placed = set()
        self.compute_start = ['CSD', 'Random', 'Selected'][2]
        self.dir_str = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
        self.start_letters = 'abcdefghilmnoprst'
        self.word_locations = []
        self.direction_lookup = {
            's': np.array([1, 0]),
            'e': np.array([0, 1]),
            'w': np.array([0, -1]),
            'n': np.array([-1, 0]),
            'se': np.array([1, 1]),
            'sw': np.array([1, -1]),
            'nw': np.array([-1, -1]),
            'ne': np.array([-1, 1])
        }
        self.compass = {
            (-1, 0): 'N',
            (-1, 1): 'NE',
            (0, 1): 'E',
            (1, 1): 'SE',
            (1, 0): 'S',
            (1, -1): 'SW',
            (0, -1): 'W',
            (-1, -1): 'NW'
        }
        self.q = Queue()

    def dirs(self, board, y, x, length=None):
        # fast finding of all directions from starting location
        # optional masking of length
        a = np.array(board)
        # a = np.indices(a.shape).transpose()
        e = a[y, x:]
        w = np.flip(a[y, :x + 1])
        s = a[y:, x]
        n = np.flip(a[:y + 1, x])
        se = np.diag(a[y:, x:])
        sw = np.diag(np.fliplr(a[y:, :x + 1]))
        ne = np.diag(np.flipud(a[:y + 1, x:]))
        nw = np.flip(np.diag(a[:y + 1, :x + 1]))
        all_dirs = [n, ne, e, se, s, sw, w, nw]
        if length:
            for dirn in all_dirs:
                dirn = dirn[:length]
                if len(dirn) < length:
                    dirn = []
        return all_dirs

    def ix(self, tuple_list):
        """ create a numpy index that can be used directly on 2d array """
        return tuple(np.array(tuple_list).T)

    def board_is_full(self):
        """board is full
    """
        return np.all(np.char.isalpha(self.board))

    def word_is_known(self, possibles):
        """ check if possible already contains filled word"""
        for possible in possibles:
            if self.in_placed(possible):
                return True
        return False

    def read_board(self, board):
        if isinstance(board, str):
            board = board.split('\n')
        grid = [row.replace("'", "") for row in board if row]
        grid = np.array([row.split('/') for row in grid])
        return grid

    def find_matches(self, try_word, wordset, pos=None):
        """ iterate thru all positions matching to all words
      wordsets are sets"""
        if pos and not UNFILLED in try_word:
            return []
        match_pattern = ''.join(list(try_word))
        if isinstance(wordset, set):
            test_words = wordset
        else:
            try:
                test_words = wordset[len(try_word)]
                if not test_words:
                    raise AttributeError
            except (KeyError, IndexError, AttributeError):
                return []

        m = re.compile(match_pattern)
        possibles = [w for w in test_words if m.search(w)]
        if match_pattern in possibles:
            return [match_pattern]
        return possibles

    def create_word_search(self, words, size=15):
        """ attempt to place a set of words onto the board """
        board = np.full((size, size), ' ')
        words_placed = []
        coords = {}
        for word in words:
            w = word.replace(' ', '')
            # bias the word placements for horizontal > vertical > diagonal
            success, coord = word_square_gen.place_word(board,
                                                        w,
                                                        coords,
                                                        max_iteration=300,
                                                        space=' ',
                                                        bias=[0.8, 1., 0.5])
            if success:
                words_placed.append(word)
        return board, words_placed, coords

    def load_words_from_file(self, file_list, no_strip=False):
        # read the entire wordfile as text
        with open(f'{file_list}', "r", encoding='utf-8') as f:
            data = f.read()
        # yaml read not working, so parse file,
        # removing hyphens and spaces
        data = data.replace('-', ' ')
        data_list = data.split('\n')
        w_dict = {}
        w_list = []

        key = None
        for word in data_list:
            if no_strip is False:
                word = word.strip()

            if ':' in word:
                if key:
                    w_dict[key] = w_list[:-1]  # remove empty string
                    w_list = []
                key = word.split(':')[0]
            else:
                w_list.append(word)
        w_dict[key] = w_list[:-1]  # remove empty string
        # print(w_dict)
        # self.all_words = self.wordlist
        self.word_dict = w_dict

    def initial_words(self, no_start):
        # get no_start words at random from word_dict which start
        # with start_letters
        # use stats to get word lengths
        word_numbers = {k: round(no_start * v / 100) for k, v in STATS.items()}

        if self.debug:
            print(f'Initial words lengths {word_numbers}')
        wordlist = []
        for length, number in word_numbers.items():
            selected = 0
            while selected < number:
                item = random.choice(self.len_dict[length])
                if item[0] in self.start_letters:
                    wordlist.append(item)
                    selected += 1

        # longest words first
        wordlist = sorted(wordlist, key=len, reverse=True)
        # random.shuffle(wordlist)
        return wordlist

    def locs_unfilled(self, board=None):
        if board is None:
            board = self.board
        latest = [tuple(loc) for loc in np.argwhere(board == UNFILLED)]
        random.shuffle(latest)
        return latest

    def no_locs_filled(self):
        latest = self.board.size - len(np.argwhere(self.board == UNFILLED))
        return latest

    def fill_remaining_krossword(self, word_group, start_locs):
        """ attempt to fill remaing by revisiting start locations
      words must start with same letter
      in unfilled area, then see if adjoining squares can be filled
      simply accept first word that fits, igboring other directions"""
        # for efficiency, only revisit start_locs with . in match_pattern

        # add in additional 3 letter word dictionary
        # _, extra_dict = self.load_words(LETTERS3)
        # for key_number in extra_dict:
        #    self.len_dict[key_number].extend(extra_dict[key_number])
        # self.wordlist =sum(self.len_dict.values(), [])
        unfilled_locs = self.locs_unfilled()
        # find words each are part of       
        words_to_visit = [word_ for coord in unfilled_locs
                          for word_ in self.word_locations
                          if word_.intersects(coord)]

        index = 20

        word_locs_list = words_to_visit.copy()
        while unfilled_locs:
            if index == 0:
                break
            try:
                word_ = word_locs_list.pop()
                loc = word_.start
            except IndexError:
                word_locs_list = words_to_visit.copy()
                
            words = word_group[self.board[loc]]
             
            self.len_dict = words
            # exclude and directions with filled letters
            possibles = self.find_max_length_matches(word_.match_pattern)
            if possibles:
               if self.debug:
                  print(f'possibles for {word_} are {possibles}')
               placed = self.place_word(word_.start, word_.coords,
                                                 possibles[0])     
               if self.debug: print(f'Placed {word_}')                                
            else:
              placed = False
  
                                     
            unfilled_locs = self.locs_unfilled()
            if self.debug:
                pass
                # print('unfilled', len(unfilled_locs), unfilled_locs)
            if placed:
                if self.debug:
                    self.print_board(
                        self.board,
                        highlight=[w.start for w in self.word_locations])
                index = 20
            if not unfilled_locs:
                break
            index -= 1

    def find_possibles(self,
                       loc=None,
                       multiple=False,
                       pos=None,
                       word_locs=None):
        # for now, start at each known letter and identify valid directions and its length
        # find matches for each possible. if no matches, reduce length until find match
        # if only one match, place it.
        # REPEAT
        # start_locs = np.argwhere(self.board != ' ')
        # if overlap is False, limit word length to stop at another initial point
        # if single_only is True only allow single option

        if loc is None:
            start_locs = self.start_locs
        else:
            start_locs = [loc]
        placed = False
        for start_loc in start_locs:
            if word_locs is None:
                all_dirs = self.dirs(self.board, *start_loc)
            else:
                all_dirs = [self.board[self.ix(word_locs)]]
            for ix, dir in enumerate(all_dirs):
                possibles = None
                while dir.size >= self.min_word_length:
                    possibles = self.find_matches(dir, self.len_dict, pos=pos)
                    if possibles is None:
                        break
                    if not possibles:
                        dir = dir[:-1]
                    else:
                        break
                if self.debug2:
                    print(f'{start_loc}, {self.dir_str[ix]}, {possibles}')

                if possibles:
                    random.shuffle(possibles)
                    # check if word already logged
                    if self.in_placed(possibles[0]):
                        continue
                    for word_ in self.word_locations:
                        if word_.start == start_loc and word_.direction == self.dir_str[ix].upper():
                           break                
                    placed_ = self.place_word(start_loc, word_.coords, possibles.pop())
                    if placed_:
                        placed = True
                        if not multiple:
                            break
                    if loc:
                        if not multiple:  # single site
                            return placed
        return placed

    def in_placed(self, word):
        return word in self.placed

    def place(self, start_loc, dirn, possibles):
        # -place word if not already in word_locations
        #placed_words = [word.word for word in self.word_locations]
        word_to_place = ''.join(possibles)
        if word_to_place in self.placed:
            if self.debug:
                print(f'{word_to_place} already placed')
            return False
        coords = [
            tuple(start_loc + self.direction_lookup[self.dir_str[dirn]] * x)
            for x, _ in enumerate(possibles)
        ]
        word = Word(start_loc,
                    self.dir_str[dirn].upper(),
                    len(possibles),
                    word=word_to_place,
                    index=len(self.word_locations))
        self.word_locations.append(word)
        self.placed.add(word_to_place)

        for coord, p in zip(coords, list(possibles)):
            self.board[coord] = p
        if self.debug3:
            print()
            print(f'placed  {word}')
        return True

    def get_word(self, coords):
        # get word object from coords
        # use start coordinate and direction
        direction = self.compass[sub(coords[1], coords[0])]  # N, S etc
        for word_ in self.word_locations:
            if word_.start == coords[0] and word_.direction == direction:
                return word_
        #somethings gone wrong
        raise IndexError(f'Word {coords[0]} {direction} not found')

    def place_word(self, start_loc, coords, word, previous=False):
        # -place word if not already in word_locations
        # if previous is True, remove the word
        if not previous:
            if word in self.placed:
                if self.debug:
                    print(f'{word} already placed')
                return False
            word_ = self.get_word(coords)
            #update word object
            word_.word = word
            # if word_ has been shortened, change coords and children
            if word_.length > len(word):
                extra_coords = word_.coords[len(word):]
                word_.coords = word_.coords[:len(word)]
                word_.match_pattern = word_.match_pattern[:len(word)]
                word_.length = len(word)
                # remove any orphaned children
                # [item.children.pop(coord, None)
                #    for coord in extra_coords
                #    for item in word_.children[coord]]
                [word_.children.pop(coord, None) for coord in extra_coords]

            self.placed.add(word)
            word_.update_grid(None, self.board, word)
            if self.debug3:
                print()
                print(f'placed  {word_}')
            return True
        else:
            # board has reverted, remove word and reset matches of children
            word_ = self.get_word(coords)
            try:
                word_.word = ''
                #self.cc.update_children_matches(word_, clear=True)

                self.placed.remove(word)
            except (UnboundLocalError, KeyError):
                pass
            return True

    def check_in_board(self, coord):
        r, c = coord
        return (0 <= r < self.board.shape[0]) and (0 <= c <
                                                   self.board.shape[1])

    def length_matrix(self):
        # process the board to establish starting points of words,
        # its direction, and length
        # word starts on a letter, and proceeds until it hits another letter.
        # note not always true
        self.word_locations = []
        # self.start_time= time()
        index = 0
        for r, row in enumerate(self.board):
            for c, character in enumerate(row):
                rc = r, c
                if character == ' ':
                    continue
                else:
                    for d, d_name in zip(self.dirs(self.board, r, c),
                                         self.dir_str):
                        try:
                            length = np.where(
                                np.char.isalpha(d))[0][1]  # first non space
                        except IndexError:
                            length = len(d)
                        if length >= self.min_word_length:
                            # match pattern is max possible length, which can be more than length
                            match_pattern = ''.join(
                                np.char.replace(d, ' ', UNFILLED))
                            t = Word(rc,
                                     d_name,
                                     length,
                                     match_pattern=match_pattern,
                                     index=index)
                            self.word_locations.append(t)
                            index += 1

        if self.word_locations:
            # find length of all words
            lengths = Counter([word.length for word in self.word_locations])
            self.wordlengths = dict(sorted(lengths.items()))
            self.min_length = min(self.wordlengths)
            self.max_length = max(self.wordlengths)
            # self.delta_t('len matrix')
        return self.min_length, self.max_length

    def print_board(self, board, which='', highlight=None):
        # optionally make chars Uppercase
        # highlight is a list of r,c coordinates
        print(f'board: {which}')
        print('    ' + ''.join(
            [f'{hex(i).upper()[2:]:<2}' for i in range(board.shape[0])]))
        print('    ' + '--' * board.shape[0])
        for j, row in enumerate(board):
            print(f'{hex(j).upper()[2:]:>2}| ', end='')
            for i, col in enumerate(row):
                if highlight and (j, i) in highlight:
                    print(str(board[j][i]).upper(), end=' ')
                else:
                    print(str(board[j][i]), end=' ')
            print()

    def load_words(self, filename=WORDLIST):
        """dictionary start_let
      word_dict = {'start letter': {2: [], 3: []}} etc
      convert word lists to sets
      """

        with open(filename, 'r') as f:
            self.wordset = f.read().split('\n')
        # dictionary of start_letter: {length:[words]}
        word_dict = defaultdict(list)
        for word in self.wordset:
            if word:
                word_dict[word[0]].append(word)
        # now create length dict for each letter
        for letter in word_dict:
            word_dict[letter] = sorted(word_dict[letter], key=len)
            word_dict[letter] = {
                k: set(g)
                for k, g in groupby(word_dict[letter], key=len)
            }

        # Another dictionary of just length: [words]
        self.wordset = sorted(self.wordset, key=len)
        len_dict = {k: set(g) for k, g in groupby(self.wordset, key=len)}
        return word_dict, len_dict

    def create_wordlist_dictionary(self):
        # split the words and numbers into dictionary
        key = None
        w_dict = {}
        w_list = []
        for word in self.wordlist:
            # skip comment
            if word.startswith('#'):
                continue
            if word.startswith('Puzzle'):  # key for krossword
                if key:
                    w_dict[key] = w_list  # remove empty string
                    w_list = []
                key = word
            else:
                w_list.append(word)
        w_dict[key] = w_list  # remove empty string

        return w_dict

    def to_frame(self):
        # convert start board to list of strings
        frame = np.full_like(self.board, ' ')
        for word in self.word_locations:
            loc = word.start
            frame[loc] = self.board[loc]
        self.empty_board = frame
        board_str = ''
        for r, row in enumerate(frame):
            board_str += "'"
            for c, char_ in enumerate(row):
                board_str += char_
                board_str += '/'
            board_str = board_str[:-1] + "'" + '\n'
        return board_str

    def existing_puzzles(self):
        # get existing puzzles
        with open('fiveways.txt') as f:
            self.wordlist = f.read().split('\n')
        w_dict = self.create_wordlist_dictionary()
        word_dict = {
            w: v
            for w, v in w_dict.items() if not w.endswith('_frame:')
        }
        w_list = [puzzle[:-1] for puzzle in word_dict]
        last_name = w_list[-1]
        numbers = re.findall(r'\d+', last_name)
        last_number = numbers[-1]
        self.base = last_name[:last_name.index(last_number)]
        self.next_number = int(last_number) + 1
        return w_dict, word_dict

    def stats(self):
        self.load_words()
        w_dict, word_dict = self.existing_puzzles()
        t = time()
        self.frame_dict = {
            w: v
            for w, v in w_dict.items() if w.endswith('_frame:')
        }
        for puzzle, frame in self.frame_dict.items():
            self.board = self.read_board(frame)
            locs = np.argwhere(self.board != ' ')
            self.start_locs = [tuple(loc) for loc in locs]
            self.length_matrix()
            for word in self.word_locations:
                self.board[word.start] = '#'
                for coord in word.coords[1:]:
                    self.board[coord] = UNFILLED
            # self.print_board(self.board,which=puzzle)
            # print(puzzle, self.wordlengths)
            # print(self.word_locations)

        print('elapsed', time() - t)
        # count words in each puzzle,
        # length of words and number in starting letters
        puzzles = []
        for puzzle, contents in word_dict.items():
            try:
                contents.remove('New:')
            except ValueError:
                pass
            contents = list(set(contents))
            contents.remove('')

            no_words = len(contents)
            Freq = Counter([len(words) for words in contents])
            Start = Counter([words[0] for words in contents])
            puzzles.append((no_words, Freq, Start))
            print(f'{no_words=} {Freq=} {Start=}')
        # aggregate all puzzles
        all_puzzles = list(puzzles[0])
        all_puzzles[0] = int(np.mean([puzzle[0] for puzzle in puzzles]))
        for i in range(1, 3):
            [all_puzzles[i].update(puzzle[i]) for puzzle in puzzles[i:]]
            all_puzzles[i] = dict(sorted(all_puzzles[i].items()))

        # print results
        print('number of puzzles', len(word_dict))
        print('mean no of words in puzzles', all_puzzles[0])
        print('word lengths in puzzles', all_puzzles[1])
        print('start_letters in puzzles', all_puzzles[2])
        print()
        print(
            'word lengths in words list',
            dict(
                sorted(
                    Counter([len(words) for words in self.wordset
                             if words]).items())))
        print(
            'letter density in words list',
            dict(
                sorted(
                    Counter([words[0] for words in self.wordset
                             if words]).items())))

    def is_complete(self, board):
        return (board.size - np.count_nonzero(np.char.isalpha(board))) == 0

    def compute_puzzle_text(self, name='puzzle', add_coords=True):
        """produce all text """
        if add_coords:
            words = sorted([
                word.word.upper() + str(word.start) + word.direction.upper()
                for word in self.word_locations
            ])
        else:
            words = sorted([word.word.upper() for word in self.word_locations])
        all_text = '\n'.join([
            '', f'{name}:', '\n'.join(words), '', f'{name}_frame:',
            self.to_frame()
        ])
        return all_text
        
    def set_all_matches(self, board):
        for word_ in self.word_locations:
            word_.update_match(board)
      
    def fewest_matches(self):
        """Finds the slot that has the fewest possible matches, this is probably the best next place to look.
      Start_dict is a dictionary of start locations and coordinates of words from that start"""
        fewest = self.Fewest([], 100, None, [])
        for position, word_locs in self.start_dict.items():
            letter = self.board[position]
            words = self.word_group[letter]
            for word_loc in word_locs:
                word = self.board[self.ix(word_loc)]
                while len(word) >= self.min_word_length:
                    possibles = self.find_matches(try_word=word,
                                                  wordset=words[len(word)],
                                                  pos=True)
                    if not possibles:
                        word = word[:-1]
                    else:
                        break
                if possibles and len(possibles) > 0:
                    # known existing word
                    if self.word_is_known(possibles):
                        continue
                        return self.Fewest([possibles.pop()], 1, position,
                                           word_loc)
                    if len(possibles) < fewest.matches:
                        fewest = self.Fewest(possibles, len(possibles),
                                             position, word_loc)

        if len(fewest.possibles) == 0:
            fewest = self.Fewest([], 0, position, word_loc)
        return fewest

    def fill(self):
        """recursive fill routine"""
        self.iteration_counter += 1
        if self.iteration_counter >= self.max_dfs_iteration:
            return True
        # if the grid is filled, succeed if every word is valid and otherwise fail
        if self.board_is_full():
            return True

        # choose position with fewest matches
        # this is expensive for time
        # is it best to just get next random location?
        #fewest = self.fewest_matches()

        # get next random word location
        try:
            word_coords = self.all_words.pop()
        except IndexError:  # empty
            return True

        word = self.board[self.ix(word_coords)]
        wordset = self.word_group[word[0]][len(word)]

        possibles = self.find_matches(word, wordset, pos=True)
        if not possibles:  #fewest.matches == 0:
            if self.debug:
                print('no matches, backing up')
            return False

        # iterate through all possible matches in the current slot

        previous_board = self.board.copy()
        # store best filled board for later debug
        if self.no_locs_filled() > self.best_filled:
            self.best_filled = self.no_locs_filled()
            self.best_filled_board = self.board.copy()

        for i, possible in enumerate(possibles[:10]):  #fewest.possibles):
            if self.debug:
                print('iteration', i)
            self.place_word(word_coords[0], word_coords, possible)
            #self.place_word(fewest.start, fewest.coords, possible)
            #print()
            #self.print_board(self.board, which=f'{self.iteration_counter}, {possible.capitalize()} {self.no_locs_filled()}/169 depth= {len(inspect.stack(0))}', highlight=self.start_locs)
            # now proceed to next fewest match
            if self.fill():
                return True
            # back here if match failed
            # if no match works, restore previous word and board
            self.board = previous_board
            # cancel the placement
            # print('Removed', possible)
            self.place_word(word_coords[0],
                            word_coords,
                            possible,
                            previous=True)
            self.all_words.insert(1, word_coords)
            # self.place_word(fewest.start, fewest.coords, possible, previous=True)

        return False

    def create_krossword_dfs(self,
                             word_group,
                             size,
                             start_locs,
                             start_dict,
                             iterations=10):
        """ attempt to place a set of words onto the board
      several words start at same location
      13 groups using start letters in 
      abcdefghilmnoprs
      # start positions are imported
      # these are the possible start positions for each row
      # start dict is a dictionary of start locations and coordinates radiating 
      This function uses DFS instead if Monte Carlo """

        def mediumcopy(value):
            return [copy(word) for word in value]

        Best = namedtuple("Best", "board word_locs start_locs")
        self.Fewest = namedtuple("Fewest", "possibles matches start coords")
        self.start_dict = start_dict
        self.start_locs = start_locs
        self.word_group = word_group
        letters = list('abcdefghilmnoprst')
        # Each iteration shuffles the start letters
        best_score = 0

        for i in range(iterations):
            t1 = time()
            if self.use_random:
                start_locs = random.choice(self.all_start_coords)
                start_dict = self.compute_start_dict(start_locs)
            self.start_dict = start_dict
            self.start_locs = start_locs
            self.iteration_counter = 0
            # self.word_locations = []
            self.best_filled = 0

            self.board = np.full((size, size), UNFILLED)

            random.shuffle(letters)
            start_letters = letters[:len(start_locs)]
            [
                set_board(self.board, loc, val)
                for loc, val in zip(start_locs, start_letters)
            ]
            self.cc.board = self.board
            self.cc.empty_board = self.board
            self.cc.debug = 1
            self.cc.update_all_matches()
            self.print_board(self.board)
            self.cc.all_word_dict = self.len_dict
            #self.cc.populate_words_graph(
            #                   length_first=True,
            #                   max_iterations=600,
            #                   max_possibles=20,
            #                   swordsmith_strategy=None,
            #                   type='American')

            # flat list of word coordinates
            self.all_words = [
                word for words in start_dict.values() for word in words
            ]

            random.shuffle(self.all_words)
            self.all_words.sort(key=len)
            self.fill()
            #self.print_board(self.board, which=f'{i}, {self.no_locs_filled()}/{size*size}', highlight=start_locs)
            self.fill_remaining_krossword(word_group, start_locs)

            self.print_board(self.board,
                             which=f'{i}, {self.no_locs_filled()}/{size*size}',
                             highlight=start_locs)
            score = self.no_locs_filled()
            #self.print_board(self.board, highlight=locs)
            if score > best_score:
                best = Best(self.board.copy(), mediumcopy(self.word_locations),
                            start_locs)
                best_score = score
                if score == self.board.size:
                    break

        self.print_board(best.board,
                         which=f'Best {best_score} in {(time()-t1):.2f}s',
                         highlight=best.start_locs)
        self.board = best.board
        self.word_locations = best.word_locs

        print('Word Objects:')
        word_locs = [word for word in best.word_locs if word.word]
        for i, w in enumerate(sorted(word_locs, key=attrgetter('start'))):
            print(f'{str(w):<35}', end='')
            if i != 0 and i % 3 == 2:
                print()
        return best

    def create_krossword_monte(self,
                               word_group,
                               size,
                               start_locs,
                               start_dict,
                               iterations=30):
        """ attempt to place a set of words onto the board
      several words start at same location
      13 groups using start letters in 
      abcdefghilmnoprs
      # start positions are imported
      # these are the possible start positions for each row
      # start dict is a dictionary of start locations and coordinates radiating  """

        def mediumcopy(value):
            # one level copy
            return [copy(word) for word in value]
            
        Best = namedtuple("Best", "board word_locs")
        word_locations_original = mediumcopy(self.word_locations)
        self.debug = False
        best_score = 0
        t1 = time()
        for i in range(iterations):
            # different set of start letters
            print('\nIteration', i, '>'*32)
            # self.word_locations = mediumcopy(word_locations_original)
            letters = list('abcdefghilmnoprst')
            random.shuffle(letters)
            start_locs = self.compute_start_positions(size, iterations=50)[1]
            self.compute_start_dict(start_locs)
            start_letters = letters[:len(start_locs)]
            self.board = np.full((size, size), UNFILLED)
            [set_board(self.board, loc, letter)
              for loc, letter in zip(start_locs, start_letters)]

            # process words in length order, then diagonals
            # if we come across any single possible words, the push them onto the queue for priority processing
            words_to_process = sorted(self.word_locations,
                                      key=attrgetter('length'))
            words_to_process = sorted(words_to_process,
                                      key=lambda x: len(x.direction))
            if self.debug:
                print(words_to_process)
            counter = 0
            placed = False
            while words_to_process:
                if not placed:
                    counter += 1
                    if counter > 30:
                        print('\n\n')
                        print('Too many tries .....................')                        
                        words_to_process = []
                        break
                else:
                    counter = 0
                if self.q.empty():
                    word_ = words_to_process.pop()
                else:
                    word_ = self.q.get(block=False)

                if word_.word:
                    continue
                self.set_all_matches(self.board)
                
                start_loc = word_.start
                letter = word_.match_pattern[0]
                placed = False
                words = word_group[letter]
                self.len_dict = words
                possibles = self.find_max_length_matches(word_.match_pattern)

                if possibles:
                    random.shuffle(possibles)

                    # for each possible, check if it would block children
                    # place the word on a board copy
                    # update all match patterns
                    # check all children for possibles
                    # if any are none, go to next possible
                    # if multiple, choose best total possibles

                    best_list = []
                    for i, poss in enumerate(possibles[:-1]):
                        poss_dict = self.check_around(
                            word_,
                            poss,
                            dirs=['N', 'S', 'E', 'W'],
                            start_locs=start_locs)
                        # need best metric
                        poss_dict = dict(
                            sorted(poss_dict.items(),
                                   key=itemgetter(1),
                                   reverse=True))
                        if poss_dict:
                           x = min(poss_dict.values())
                        else:
                          x = 0
                        #x = prod(poss_dict.values())
                        if x > 0:
                            best_list.append((poss, x, poss_dict))
                        else:
                            fails = [
                                (word, word.match_pattern.capitalize())
                                for word, len_possibles in poss_dict.items()
                                if len_possibles == 0
                            ]
                            if self.debug:
                               print(
                                f'no options for {poss.capitalize()} as {word_}, due to {fails=}'
                                )
                            # print(poss_dict)
                    
                    best_list = sorted(best_list,
                                       key=itemgetter(1),
                                       reverse=True)
                    if best_list:
                        best_word = best_list[0][0]
                        placed = self.place_word(start_loc, word_.coords,
                                                 best_word)
                        self.set_all_matches(self.board)
                        
                        # place any single possibles onto queue
                        #[self.q.put(k) for k, v in best_list[0][2].items() if v == 1]
                    if placed:
                        if self.debug:
                            self.print_board(self.board,
                                             which=word_,
                                             highlight=start_locs)
                            try:
                                words_to_process.remove(word_)
                            except ValueError:
                                pass
                    #else:
                    #    words_to_process.insert(1, word_)
            # self.print_board(self.board, which='Before Fill', highlight=start_locs)   
            self.fill_remaining_krossword(word_group, start_locs)
            score = self.board.size - len(self.locs_unfilled())
            self.print_board(self.board,which=score, highlight=start_locs)
            if score > best_score:
                best = Best(self.board.copy(), mediumcopy(self.word_locations))
                best_score = score
                if score == self.board.size:
                    break
        # finished searching, report best
        self.print_board(best.board,
                         which=f'Filled {best_score} in {(time()-t1):.2f}s',
                         highlight=start_locs)
        print()
        print('Word Objects:')
        valid_words = sorted([word_ for word_ in best.word_locs if word_.word],
                             key=attrgetter('start'))
        for i, w in enumerate(valid_words):
            print(f'{str(w):<35}', end='')
            if i != 0 and i % 3 == 2:
                print()
        return best

    def find_max_length_matches(self, match_pattern):
        """ find match for match_pattern or shorter """
        possibles = None
        while len(match_pattern) >= self.min_word_length:
            possibles = self.find_matches(match_pattern,
                                          self.len_dict,
                                          pos=False)
            #try shorter lengths
            if possibles is None:
                break
            if not possibles:
                match_pattern = match_pattern[:-1]
            else:
                break
        return possibles

    def check_around(self, word_obj, word, dirs=None, start_locs=None):
        # for word, check if it would block children of wird_obj
        # place the word on a board copy
        # update all match patterns
        # check all children for possibles
        # if any are none, go to nect possible
        # if multiple, choose best total possibles
        board = self.board.copy()
        word_obj.update_grid(None, board, word)

        self.set_all_matches(board)
  
        poss_dict = defaultdict(list)
        children = sum(word_obj.children.values(), [])

        # filter directions
        if dirs is None:
            dirs = self.compass.values()
        children = [child for child in children if child.direction in dirs]
        # self.print_board(board, which=f'trying {word}', highlight=start_locs)
        for child in children:
            p = self.find_max_length_matches(child.match_pattern)
            if p:
                poss_dict[child] = len(p)
            else:
                poss_dict[child] = 0
        #print(poss_dict)
        return poss_dict

    def get_wordset(self, filename):
        # get words at random for each letter in sorted file
        with open(filename) as f:
            all_words = f.read().split('\n')
        word_dict = defaultdict(list)
        # divide into letter keys
        for word in all_words:
            if word:
                word_dict[word[0]].append(word)
        # 4-10 letters from stats
        wordset = defaultdict(list)
        for letter, words in word_dict.items():
            # filter words of correct length
            selection = [word for word in words if 3 <= len(word) < 9]
            # choose 10 at random
            #subset = random.choices(selection, k=200)
            # sort them longest -> smallest
            wordset[letter] = sorted(selection, key=len, reverse=True)
            self.len_dict = {
                len(i): [x for x in words if len(x) == len(i)]
                for i in words
            }
        return wordset

    def get_lengths_from_place(self, board, rc):
        # return a dictionary of directions with minimum length
        r, c = rc
        lengths = {}
        for all_chars, d_name in zip(self.dirs(board, r, c), self.dir_str):
            try:
                alpha_chars = np.where(np.char.isalpha(all_chars))[0]
                #either 1st or 2nd occurence of alpha character
                length = alpha_chars[int(all_chars[0].isalpha())]
            except IndexError:
                length = len(all_chars)
            if length >= 3:
                lengths[d_name] = length
        return lengths

    def place_pieces(self, size):
        """place pieces such that all squares covered
      """
        problem = Problem()
        cols = list(range(size))
        rows = list(range(size))
        random.shuffle(rows)
        random.shuffle(cols)
        problem.addVariables(cols, rows)
        problem.addConstraint(AllDifferentConstraint())
        for col1 in cols:
            for col2 in cols:
                if col1 < col2:
                    problem.addConstraint(
                        lambda row1, row2, col1=col1, col2=col2: abs(
                            row1 - row2) != abs(col1 - col2) and row1 != row2,
                        (col1, col2),
                    )
        return problem.getSolutionIter()

    def test_filled(self, r, c, board, start_locs):
        # from start point r,c. get coordinates of all locations
        # > 2 and less than 11
        # stop before another start location
        starts = start_locs.copy()
        all_dirs = self.dirs(board, r, c)
        neighbours = [[
            tuple((r, c) + self.direction_lookup[self.dir_str[ix]] * x)
            for x, _ in enumerate(dirn)
        ] for ix, dirn in enumerate(all_dirs)]
        neighbours = [
            n for n in neighbours
            if self.max_word_length > len(n) >= self.min_word_length
        ]
        #limit length of any neighbour if it includes another start_loc
        starts.remove((r, c))
        ntemp = neighbours.copy()
        neighbours = []
        for word in ntemp:
            for s in starts:
                try:
                    i = word.index(s)
                except ValueError:
                    i = len(word)
            word = word[:i]
            neighbours.append(word)
        [
            set_board(board, rc, '.') for direction in neighbours
            for rc in direction
        ]
        return neighbours

    def compute_start_dict(self, start_locs):
        """ calculate coordinates for words beginning at start_locs """
        start_dict = defaultdict(list)
        self.word_locations = []
        for i, loc in enumerate(start_locs):
            neighbours = self.test_filled(*loc, self.board, start_locs)
            start_dict[loc] = sorted(neighbours, reverse=False)
        # now fill word_locations
        for k, words in start_dict.items():
            for coords in words:
                direction = self.compass[sub(coords[1], coords[0])]  # N, S etc
                word_ = Word(k,
                             direction.upper(),
                             len(coords),
                             word='',
                             match_pattern='.' * len(coords),
                             index=len(self.word_locations))
                self.word_locations.append(word_)
        # link crossing words as children
        for w in self.word_locations:
            for coord in sorted(w.coords[1:]):
                for word_ in self.word_locations:
                    if w != word_:
                        if word_.intersects(coord):
                            # append if present then remove duplicates
                            w.children.setdefault(coord, []).append(word_)
                            word_.children.setdefault(coord, []).append(w)
                            w.children[coord] = list(set(w.children[coord]))
                            word_.children[coord] = list(
                                set(word_.children[coord]))
        return dict(sorted(start_dict.items()))

    def compute_start_positions(self, size, iterations=10):
        """ Use 'N queens'  CSD algorithm to get best start positions
      using Monte Carlo search """
        Best = namedtuple("Best", "board start_locs start_dict score")
        best_score = 0
        score = 0
        t1 = time()
        # create an iterator with one piece on each row and column
        pieces = self.place_pieces(size)

        # iterate through possible solutions to see which best allows board to fill
        for i in range(iterations):
            t = time()
            self.board = np.full((size, size), ' ')
            # next attempt
            try:
                start_locs = sorted([(r, c) for r, c in next(pieces).items()])
            except StopIteration:
                best = Best(self.board.copy(), start_locs, start_dict, score)
                break
            if self.debug:
                print(start_locs)
            start_dict = self.compute_start_dict(start_locs)
            for i, v in enumerate(start_dict.values()):
                neighbours = set(sum(v, []))
                [
                    set_board(self.board, (r, c), string.ascii_lowercase[i])
                    for r, c in neighbours
                ]
            if self.debug:
                self.print_board(self.board,
                                 which=(i, round(time() - t, 3)),
                                 highlight=start_locs)
            score = self.board.size - len(self.locs_unfilled())
            # return if full
            if score == self.board.size:
                best = Best(self.board.copy(), start_locs, start_dict, score)
                break
            if score > best_score:
                best_score = score
                best = Best(self.board.copy(), start_locs, start_dict, score)

        self.print_board(best.board,
                         which=f'Best {best.score} in {(time()-t1):.2f}s',
                         highlight=start_locs)

        return best

    def decode_krossword(self, word_locs):
        """parse word_locations list
    to seperate groups under letter """
        kross = {}
        word_locs = [word for word in word_locs if word.word]
        word_locs = sorted(word_locs, key=attrgetter('start'))

        word1 = word_locs[0]
        index = 1
        kross[index] = []
        for word in word_locs:
            if word.start == word1.start:
                kross[index].append(word.word.upper())
            else:
                word1 = word
                index += 1
                kross[index] = [word.word.upper()]
        print('\n\n', kross)
        return kross

    def get_starts(self, filename):
        self.load_words_from_file(filename)
        items = [s.capitalize() for s in self.word_dict.keys()]
        items = [item for item in items if not item.endswith('_frame')]
        start_coords = []
        all_words = []
        for selection in reversed(items):
            if selection + '_frame' in self.word_dict:
                table = self.word_dict[selection + '_frame']
            board = [row.replace("'", "") for row in table]
            board = [row.split('/') for row in board]
            board = np.array(board)
            # get alpha numric, then remove alpha
            c = set(
                [tuple(loc) for loc in np.argwhere(np.char.isalnum(board))])
            d = set(
                [tuple(loc) for loc in np.argwhere(np.char.isalpha(board))])
            numbers = c.difference(d)
            start_coords.append(sorted(numbers))
        return start_coords


def main():
    save = False
    console.clear()
    cx = Cross()
    size = 13
    cx.use_random = False
    Best = namedtuple("Best", "board start_locs start_dict score")
    cx.all_start_coords = cx.get_starts('krossword.txt')
    word_dict, cx.len_dict = cx.load_words(filename=WORDLIST)

    # find the best start positions
    best = cx.compute_start_positions(size, iterations=500)
    # print('Best starts', best.start_locs)
    print()
    #start_locs = random.choice(cx.all_start_coords)
    start_locs = best.start_locs
    cx.board = np.full((size, size), ' ')
    best = Best(cx.board, start_locs, cx.compute_start_dict(start_locs), 0)
    cx.cc = crossword_create.CrossWord(Gui(cx.board, None), cx.word_locations,
                                       cx.wordset)
    cx.cc.gui.gs.close()
    cx.cc.board = cx.board
    # now try to fit words to start positions
    best = cx.create_krossword_monte(word_dict,
                                     size,
                                     best.start_locs,
                                     best.start_dict,
                                     iterations=20)
    cx.decode_krossword(best.word_locs)
    #print(best.start_locs)

    #print(best.word_locations)
    #print(text)
    if save:
        with open('fiveways.txt', 'a', encoding='utf-8') as f:
            f.write(text)


if __name__ == '__main__':
    main()
    #cProfile.run('main()')

# what about look forward?
# in deciding a word to place, lookat interconnected words to see if
# they can be satisfied, else we get a block
# preload all word_locations to get children
# dont use uexistence of Word, but content of match
# could i then use crossword code?

