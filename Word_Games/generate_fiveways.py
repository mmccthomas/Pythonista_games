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
"""
import random
import numpy as np
from collections import defaultdict, Counter
from operator import attrgetter
import re
import string
from copy import deepcopy
from time import time
import console
from Letter_game import Word
from gui.gui_interface import Coord 
import word_square_gen
from Krossword import KrossWord
sys.path.append(os.path.expanduser('~/Documents/site-packages/pyconstraint'))
from constraint import Problem, Domain, Constraint, AllDifferentConstraint
from constraint import FunctionConstraint, SomeInSetConstraint
from constraint import MinConflictsSolver

WORDLIST = "wordlists/words_10000.txt"
# avoid 3 letter words till near the end
# WORDLIST = "wordlists/5000-more-common_sorted.txt"
LETTERS3 = "wordlists/letters3_common.txt"
# number or words in ineavh length to choose
# percentages
STATS = {4: 5, 5: 31, 6: 26, 7: 18, 8: 13, 9: 5, 10: 5}


def add(a, b):
  """ helper function to add 2 tuples """
  return tuple(p+q for p, q in zip(a, b))
  

def sub(a, b):
  """ helper function to add 2 tuples """
  return tuple(p-q for p, q in zip(a, b))

def set_board(board, loc, val):
    board[loc] = val

class Cross(KrossWord):
  
  def __init__(self):
    self.debug = False
    self.debug2 = False
    self.debug3 = False
    self.min_word_length = 3
    self.max_word_length = 11
    self.compute_start = ['CSD', 'Random', 'Selected'][2]
    self.dir_str = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
    self.start_letters = 'abcdefghilmnoprst'
    self.word_locations = []
    self.direction_lookup = {'s': np.array([1, 0]), 'e': np.array([0, 1]),
                             'w': np.array([0, -1]), 'n': np.array([-1, 0]),
                             'se': np.array([1, 1]), 'sw': np.array([1, -1]),
                             'nw': np.array([-1, -1]), 'ne': np.array([-1, 1])}
    self.compass = {(-1, 0): 'N', (-1, 1): 'NE', (0, 1): 'E',
                   (1, 1): 'SE', (1, 0): 'S', (1, -1): 'SW',
                   (0, -1): 'W', (-1, -1): 'NW'}
          
  def dirs(self, board, y, x, length=None):
      # fast finding of all directions from starting location
      # optional masking of length
      # TODO change to finding coordinates, then use those to slice
      a = np.array(board)
      # a = np.indices(a.shape).transpose()
      e = a[y, x:]
      w = np.flip(a[y, :x+1])
      s = a[y:, x]
      n = np.flip(a[:y+1, x])
      se = np.diag(a[y:, x:])
      sw = np.diag(np.fliplr(a[y:, :x+1]))
      ne = np.diag(np.flipud(a[:y+1, x:]))
      nw = np.flip(np.diag(a[:y+1, :x+1]))
      all_dirs = [n, ne, e, se, s, sw, w, nw]
      if length:
          for dirn in all_dirs:
              dirn = dirn[:length]
              if len(dirn) < length:
                  dirn = []
      return all_dirs

  def read_board(self, board):
      if isinstance(board, str):
        board = board.split('\n')
      grid = [row.replace("'", "") for row in board if row]
      grid = np.array([row.split('/') for row in grid])
      return grid
                                     
  def find_matches(self, word, words, pos=None):
      """ iterate thru all positions matching to all words"""
      if pos is None:        
        try:
            length = len(word)
            test_words = [word_ for word_  in words[length] if word_[0] in self.start_letters]
            if not test_words:
              raise AttributeError
        except (KeyError, IndexError, AttributeError):
           return []
      else:
          test_words = words
      word = np.char.replace(word, ' ', '.')
      match_pattern = ''.join(word)
      if pos and not '.' in match_pattern:
         return None
      possibles = []
      m = re.compile(match_pattern)
      possible_words = [w for w in test_words
                        if m.search(w)]
      for possible in possible_words:
          if possible == match_pattern:
              return [possible]
          possibles.append(possible)
      return possibles
  
  def create_word_search(self, words, size=15):
      """ attempt to place a set of words onto the board """
      board = np.full((size, size), ' ')
      words_placed = []
      coords = {}
      for word in words:
        w = word.replace(' ', '')
        # bias the word placements for horizontal > vertical > diagonal
        success, coord = word_square_gen.place_word(
          board, w, coords, max_iteration=300, space=' ', bias=[0.8, 1., 0.5])
        if success:
          words_placed.append(word)
      return board, words_placed, coords
      
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
                 
  def wordsearch(self, size=13, no_start=38, iterations=10):
      """  attempt to place no_start words """
      compass = {(-1, 0): 'N', (-1, 1): 'NE', (0, 1): 'E',
                 (1, 1): 'SE', (1, 0): 'S', (1, -1): 'SW',
                 (0, -1): 'W', (-1, -1): 'NW'}
      
      self.board = np.full((size, size), ' ')
      self.word_dict, self.len_dict = self.load_words()
      # need  to get existing puzzle names
      self.existing_puzzles()
      
      # loop until get a filled puzzle
      iteration = 1
      while self.locs_unfilled():
          print(f'{iteration=}')
          iteration += 1
          self.word_locations = []
          wordlist = self.initial_words(no_start)
          # Monte Carlo search word_search to find best
          no_words_placed = 0
          for i in range(iterations):
              t=time()
              self.board, words_placed, self.word_coords = self.create_word_search(wordlist, size)
              #print('elapsed', time()-t)
              #self.print_board(self.board, which=(i, no_words_placed))
              # print(f'{i =}, {len(words_placed)}/{len(self.wordlist)}')
              if len(words_placed) > no_words_placed:
                  best = self.board, words_placed, self.word_coords
                  no_words_placed = len(words_placed)
                  
                  if len(words_placed) == len(wordlist):
                      break
          print()
          self.board, words_placed, self.word_coords = best
          index = 0
          for word, coords in self.word_coords.items():
              if coords:
                  if ''.join([self.board[c] for c in coords]) != word:
                      coords.reverse()
                  dirn = sub(coords[1], coords[0])
                  self.word_locations.append(Word(coords[0], compass[dirn].lower(), len(word), word=word, index=index))
                  index += 1
          if self.debug:
              self.print_board(self.board, highlight=[w.start for w in self.word_locations])
              print(f'{len(words_placed)=}, sorted by length {sorted(self.word_locations, key=attrgetter("length"))}')
              print()
              print(f'{len(words_placed)=}, sorted by position {sorted(self.word_locations, key=attrgetter("start"))}')
          self.fill_remaining()
          
      if self.debug:
          self.print_board(self.board, highlight=[w.start for w in self.word_locations])
          # print(len(words_placed), sorted(self.word_locations, key=attrgetter('index')))
          [print(word) for word in sorted(self.word_locations, key=attrgetter('index'))]
      self.empty_board = np.full_like(self.board, ' ')
      for word in self.word_locations:
          self.empty_board[word.start] = self.board[word.start]
                
  def locs_unfilled(self, board=None):
      if board is None:
          board = self.board
      latest = [tuple(loc) for loc in np.argwhere(board == ' ')]
      random.shuffle(latest)
      return latest   
                     
  def fill_remaining(self):
      """ attempt to fill remaing by placing a new start location
      in unfilled area, then see if adjoining squares can be filled"""                
      unfilled_locs = self.locs_unfilled()
      self.start_locs = unfilled_locs
      # add in additional 3 letter word dictionary
      # _, extra_dict = self.load_words(LETTERS3)
      # for key_number in extra_dict:
      #    self.len_dict[key_number].extend(extra_dict[key_number])
      # self.wordlist =sum(self.len_dict.values(), [])
      
      for i in range(4, 2, -1):
        self.min_word_length = i
        if self.debug:
            print('MIN LENGTH', self.min_word_length)
        index = 20
        random.shuffle(unfilled_locs)
        while unfilled_locs:
            if index == 0:
                break
            loc = unfilled_locs[-1]
            placed = self.find_possibles(loc=loc)
            unfilled_locs = self.locs_unfilled()
            if self.debug:
                print('unfilled', len(unfilled_locs), unfilled_locs)
            if placed:
                if self.debug:
                    self.print_board(self.board, highlight=[w.start for w in self.word_locations])
                index = 20
            if not unfilled_locs:
                break
            index -= 1
        if not unfilled_locs:
            break
            
  def fill_remaining_krossword(self, word_group):
      """ attempt to fill remaing by revisiting start locations
      words must start with same letter
      in unfilled area, then see if adjoining squares can be filled"""                
      
      # add in additional 3 letter word dictionary
      # _, extra_dict = self.load_words(LETTERS3)
      # for key_number in extra_dict:
      #    self.len_dict[key_number].extend(extra_dict[key_number])
      # self.wordlist =sum(self.len_dict.values(), [])
      unfilled_locs = self.locs_unfilled()
      self.debug3 = True
      for i in range(4, 2, -1):
        self.min_word_length = i
        if self.debug:
            print('MIN LENGTH', self.min_word_length)
        index = 20
        random.shuffle(self.start_locs)
        while unfilled_locs:
            if index == 0:
                break
            loc = self.start_locs[-1]
            words = word_group[self.board[loc]]
            self.len_dict = {len(i): [x for x in words if len(x) == len(i)] for i in words}
            # exclude and directions with filled letters
            placed = self.find_possibles(loc=loc, pos=True)
            unfilled_locs = self.locs_unfilled()
            if self.debug:
                print('unfilled', len(unfilled_locs), unfilled_locs)
            if placed:
                if self.debug:
                    self.print_board(self.board, highlight=[w.start for w in self.word_locations])
                index = 20
            if not unfilled_locs:
                break
            index -= 1
        if not unfilled_locs:
            break
                   
  def find_possibles(self, loc=None, multiple=False, pos=None):
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
      self.placed = False
      for start_loc in start_locs:
        
        all_dirs = self.dirs(self.board, *start_loc)
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
              placed = self.place(start_loc, ix, possibles.pop())
              if placed:
                 self.placed = True
                 if not multiple:
                    break
              if loc:
                if not multiple:  # single site
                   return self.placed
      return self.placed
          
  def in_placed(self, word):
     placed_words = [w.word for w in self.word_locations if w.word]
     return word in placed_words
       
  def place(self, start_loc, dirn, possibles):
      # -place word if not already in word_locations
      placed_words = [word.word for word in self.word_locations]
      word_to_place = ''.join(possibles)
      if word_to_place in placed_words:
          if self.debug:
              print(f'{word_to_place} already placed')
          return False
      coords = [tuple(start_loc + self.direction_lookup[self.dir_str[dirn]] * x)
                for x, _ in enumerate(possibles)]
      word = Word(start_loc,
                  self.dir_str[dirn].upper(),
                  len(possibles), word=''.join(possibles),
                  index=len(self.word_locations))
      self.word_locations.append(word)
      
      for coord, p in zip(coords, list(possibles)):
          self.board[coord] = p
      if self.debug3:
          print()
          print(f'placed  {word.word.capitalize()}@{word.start}')
      return True
      
  def place_word(self, start_loc, coords, word):
      # -place word if not already in word_locations
      placed_words = [word.word for word in self.word_locations]
      
      if word in placed_words:
          if self.debug:
              print(f'{word} already placed')
          return False
      direction = self.compass[sub(coords[1], coords[0])]  # N, S etc
      word_ = Word(start_loc,
                  direction.upper(),
                  len(word), word=word,
                  index=len(self.word_locations))
      self.word_locations.append(word_)
      
      for coord, p in zip(coords, list(word)):
          self.board[coord] = p
      if self.debug3:
          print()
          print(f'placed  {word.word.capitalize()}@{word.start}')
      return True
             
  def check_in_board(self, coord):
    r, c = coord
    return (0 <= r < self.board.shape[0]) and (0 <= c < self.board.shape[1])
     
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
            for d, d_name in zip(self.dirs(self.board, r, c), self.dir_str):
                try:
                   length = np.where(np.char.isalpha(d))[0][1]  # first non space
                except IndexError:
                    length = len(d)
                if length >= self.min_word_length:
                   # match pattern is max possible length, which can be more than length
                   match_pattern = ''.join(np.char.replace(d, ' ', '.'))
                   t = Word(rc, d_name, length, match_pattern=match_pattern, index=index)
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
      print('    ' + ''.join([f'{str(i):<2}' for i in range(board.shape[0])]))
      print('    ' + '--' * board.shape[0])
      for j, row in enumerate(board):
          print(f'{str(j):>2}| ', end='')
          for i, col in enumerate(row):
              if highlight and (j, i) in highlight:
                print(str(board[j][i]).upper(), end=' ')
              else:
                 print(str(board[j][i]), end=' ')
          print()
  
  def load_words(self, filename=WORDLIST):
      """dictionary start_let
      word_dict = {'start letter': {2: [], 3: []}} etc
      """
      with open(filename, 'r') as f:
          self.wordset = f.read().split('\n')
      # dictionary of start_letter: {length:[words]}
      word_dict = defaultdict(list)
      for word in self.wordset:
         if word:
            word_dict[word[0]].append(word)
  
      for letter in word_dict:
          len_dict = defaultdict(list)
          for word in word_dict[letter]:
              len_dict[len(word)].append(word)
          word_dict[letter] = len_dict
      # dictionary of length: [words]
      len_dict = defaultdict(list)
      for word in self.wordset:
         if word:
            len_dict[len(word)].append(word)
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
     word_dict = {w: v for w, v in w_dict.items() if not w.endswith('_frame:')}
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
     self.frame_dict = {w: v for w, v in w_dict.items()
                        if w.endswith('_frame:')}
     for puzzle, frame in self.frame_dict.items():
         self.board = self.read_board(frame)
         locs = np.argwhere(self.board != ' ')
         self.start_locs = [tuple(loc) for loc in locs]
         self.length_matrix()
         for word in self.word_locations:
            self.board[word.start] = '#'
            for coord in word.coords[1:]:
              self.board[coord] = '.'
         # self.print_board(self.board,which=puzzle)
         # print(puzzle, self.wordlengths)
         # print(self.word_locations)
     
     print('elapsed', time()-t)
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
     print('word lengths in words list',
           dict(sorted(Counter([len(words) for words in self.wordset if words]).items())))
     print('letter density in words list',
           dict(sorted(Counter([words[0] for words in self.wordset if words]).items())))
                     
  def is_complete(self, board):
      return (board.size - np.count_nonzero(np.char.isalpha(board))) == 0
        
  def compute_puzzle_text(self, name='puzzle', add_coords=True):
      """produce all text """
      if add_coords:
          words = sorted([word.word.upper() + str(word.start)+word.direction.upper()
                          for word in self.word_locations])
      else:
          words = sorted([word.word.upper() for word in self.word_locations])
      all_text = '\n'.join([
          '',
          f'{name}:',
          '\n'.join(words),
          '',
          f'{name}_frame:',
          self.to_frame()
      ])
      return all_text
      
  def grade_positions(self,start_dict ):
      """ given start dict, find the intersections to allow shortening of  words
      dictionary of board location:  """
      pass
      
 
  def create_krossword(self, word_group, size, start_locs, start_dict, iterations=10):
      """ attempt to place a set of words onto the board
      several words start at same location
      13 groups using start letters in 
      abcdefghilmnoprs
      # start positions are imported
      # these are the possible start positions for each row
      # start dict is a dictionary of start locations and coordinates radiating  """
            
      self.debug3 = False
      best_score = 0
      t1 = time()
      for i in range(iterations):
          self.word_locations = []
          letters = list('abcdefghilmnoprst')
          random.shuffle(letters)
          start_letters = letters[:len(start_locs)]
          self.board = np.full((size, size), ' ')
          words_placed = []
          coords = {}
          
          self.start_locs = start_locs
          for start_loc, word_locs in start_dict.items():
            letter = start_letters.pop()
            #may need to try each start letter
            # attempt to place word groups
            #for letter  in start_letters:
            for word_loc in word_locs:                   
                   words = word_group[letter]
                   #self.len_dict = words[len(word_loc)]
                   self.board[start_loc] = letter
                   word = [self.board[loc] for loc in word_loc]       
                   while len(word) >= self.min_word_length:        
                        possibles = self.find_matches(word, words[len(word)], pos=True)
                        if not possibles:
                           word = word[:-1]
                        else:
                           break
                   if possibles:
                      random.shuffle(possibles)
                      # check if word already logged
                      if self.in_placed(possibles[0]):
                          continue
                      placed = self.place_word(start_loc, word_loc, possibles.pop())
                      if placed:
                         self.placed = True
                         #self.print_board(self.board, highlight=start_locs)                           
          #self.fill_remaining_krossword(word_group)
          score = self.board.size - len(self.locs_unfilled())    
          #self.print_board(self.board, highlight=locs)        
          if score > best_score:
              best = (self.board.copy(), deepcopy(self.word_locations))
              best_score = score
              if score == self.board.size:
                  break
              
      self.print_board(best[0],
                       which =f'Filled {best_score} in {(time()-t1):.2f}s',
                       highlight = start_locs)  
      print(best[1])
      return best

  def get_wordset(self, filename):
    # choose 10 words at random for each letter in sorted file
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
       
       self.len_dict = {len(i): [x for x in words if len(x) == len(i)] for i in words}
     
    return wordset
  
  def get_lengths_from_place(self, board, rc):
      # return a dictionary of directions with minimum length
      r, c = rc
      lengths = {}
      for all_chars, d_name in zip(self.dirs(board, r, c) , self.dir_str):            
          try:                             
             alpha_chars =  np.where(np.char.isalpha(all_chars))[0]    
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
                   lambda row1, row2, col1=col1,
                   col2=col2: abs(row1 - row2) !=
                   abs(col1 - col2) and row1 != row2,
                   (col1, col2),
               )                
      return problem.getSolutionIter()
    
  def test_filled(self, r, c, board ):
      # from start point r,c. get coordinates of all locations
      # > 2 and less than 11
      all_dirs = self.dirs(board, r, c)
      neighbours = [[tuple((r, c) + self.direction_lookup[self.dir_str[ix]] * x)
                         for x, _ in enumerate(dirn)]
                        for ix, dirn in enumerate(all_dirs)]     
      neighbours = [n for n in neighbours if self.max_word_length > len(n) >= self.min_word_length]                      
      [set_board(board, rc, 'x')
           for direction in neighbours
           for rc in direction
      ]
      return neighbours
      
  def compute_start_positions(self, size, iterations=10):
      """ Use 'N queens'  CSD algorithm to get best start positions
      using Monte Carlo search """
      
      best_score = 0
      t1 = time()
      # create an iterator with one piece on each row and column
      pieces =  cx.place_pieces(size)
      
      # iterate through possible solutions to see which best allows board to fill
      for i in range(iterations):
          self.board = np.full((size, size), ' ')
          # next attempt
          try:
              start_locs = sorted([(r, c) for r, c in next(pieces).items()])
          except StopIteration:
              best = (self.board.copy(), start_locs, start_dict, score)
              break        
          if self.debug:
              print(start_locs)
          start_dict = defaultdict(list)
          for i, (r, c) in enumerate(start_locs):
              neighbours = cx.test_filled(r, c, self.board)        
              start_dict[(r,c)] = sorted(neighbours, key=len, reverse=True)
              neighbours = set(sum(neighbours, []))
              [set_board(self.board, (r, c), string.ascii_lowercase[i]) for r,c in neighbours]
              if self.debug:
                  self.print_board(self.board,
                                   which=(i,round(time()-t, 3)),
                                   highlight=start_locs)  
          score = self.board.size - len(self.locs_unfilled())
          start_dict = dict(sorted(start_dict.items()))
          # return if full
          if score == self.board.size:
             best = (self.board.copy(), start_locs, start_dict, score)  
             break       
          if score > best_score:
              best_score = score
              best = (self.board.copy(), start_locs, start_dict, score)
              
      self.print_board(best[0],
                 which=f'Best {best[3]} in {(time()-t1):.2f}s',
                 highlight=start_locs)                     
      return best
         
if __name__ == '__main__':
  save = False
  console.clear()
  cx = Cross()
  # cx.stats()
  size=13
  word_dict, len_dict = cx.load_words(filename=WORDLIST)  
  
  # find the best start positions
  board, start_locs, start_dict, score = cx.compute_start_positions(size, iterations=1000)           
  # print('Best starts', start_locs)
  print() 
  # now try to fit words to start positions
  board, word_locs = cx.create_krossword(word_dict, size, start_locs, start_dict, iterations=2000)


  #print(cx.word_locations)

  
  #cx.wordsearch(size=13, no_start=38, iterations=20)
  #text = cx.compute_puzzle_text(name=f'{cx.base}{cx.next_number}',
  #                              add_coords=False)
  
  #print(best.word_locations)
  #print(text)
  if save:
      with open('fiveways.txt', 'a', encoding='utf-8') as f:
          f.write(text)
