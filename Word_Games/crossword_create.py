# module to fill crossword template
# this involves finding words from a selected dictionary to
# fill a selected template.
# entry point is populate_words_graph

from time import sleep, time
import traceback
import random
import re
from math import ceil
import numpy as np
import itertools
from collections import Counter
# import matplotlib.colors as mcolors
from collections import defaultdict
from types import SimpleNamespace as sname
from Letter_game import Word, rle
import console

BLOCK = '#'
SPACE = ' '


def lprint(seq, n):
    if len(seq) > 2 * n:
        return f'{seq[:n]}...........{seq[-n:]}'
    else:
        return (seq)


class CrossWord():

    def __init__(self, gui, word_locations, all_words):
        self.max_depth = 1
        self.debug = False
        self.word_counter = None
        self.gui = gui
        self.word_locations = word_locations
        self.all_words = all_words
        self.board = []
        self.empty_board = []
        self.all_word_dict = {}
        self.max_cycles = 5000

    def set_props(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            
    def add(self, a, b):
        """ helper function to add 2 tuples """
        return tuple(p+q for p, q in zip(a, b))
        
    def copy_board(self, board):
        return list(map(list, board))

    def board_rc(self, rc, board, value):
        """ set character on board """
        try:
            board[rc[0]][rc[1]] = value
        except (IndexError):
            return None

    def get_board_rc(self, rc, board):
        try:
            return board[rc[0]][rc[1]]
        except (IndexError):
            return None
            
    def check_in_board(self, coord):
        r,c = coord
        try:
          return  (0 <= r < self.sizey) and (0 <= c <  self.sizex)
        except (AttributeError):
          return  (0 <= r < len(self.board)) and  (0 <= c <  len(self.board[0]))
      
    def delta_t(self, msg=None, do_print=True):
        try:
            t = time() - self.start_time
            if do_print:
                print(f'{msg} {t:.3f}')
            return f'{msg} {t:.3f}'
        except (AttributeError):
            print('self.start_time not defined')
            print(traceback.format_exc())

    def get_next_cross_word(self,
                            iteration,
                            max_possibles=None,
                            length_first=True):
        """ computes the next word to be attempted """

        def log_return(word):
            """ count the occurence of a word
          allows detection of unplaceable word
          """
            self.word_counter[word] += 1
            if self.word_counter[word] > 50:
                # word.fixed = True # dont try it again?
                if self.debug:
                    print(f'Word {word} tried more than 50 times')
                # return word
                raise ValueError(f'Word {word} tried more than 50 times')
            else:
                return word

        if iteration == 0:

            def longest():
                # def req(n): return n.length
                return sorted(self.word_locations,
                              key=lambda x: x.length,
                              reverse=False)

            self.word_counter = Counter()
            if len(self.all_words) > 1000:
                max_possibles = max_possibles
            else:
                max_possibles = None
            known = self.known()  # populates word objects with match_pattern
            self.hints = list(
                set([
                    word for word in self.word_locations for k in known
                    if word.intersects(k)
                ]))
            try:
                # self.gui.set_moves('hints')
                return log_return(self.hints.pop())
            except (ValueError, IndexError):
                pass
            try:
                # self.gui.set_moves('longest')
                return log_return(longest()[-1])
            except (ValueError, IndexError):
                pass
            try:
                # self.gui.set_moves('fixed')
                return log_return(
                    [word for word in self.word_locations if word.fixed][0])
            except (ValueError):
                print('returned here')
                return None

            # wordlist = longest()

        else:
            fixed = [word for word in self.word_locations if word.fixed]
            if self.debug:
                self.gui.set_message(
                    f' placed {len(fixed)} {iteration} iterations')

            # fixed_weights = [5 for word in fixed]
            # create weight for all unplaced words based on word length
            # def req(n): return n.length
            unplaced = sorted(
                [word for word in self.word_locations if not word.fixed],
                key=lambda x: x.length,
                reverse=True)
            unplaced_weights = [word.length for word in unplaced]

            unplaced_long_words = sorted(
                [word for word in unplaced if word.length > 6],
                key=lambda x: x.length)

            def match_size(n):
                return sum([i.isalnum() for i in n if '.' in n])

            # all match patterns except for full words
            patterned = [
                word for word in self.word_locations
                if word.match_pattern and '.' in word.match_pattern
            ]
            patterned_weights = [
                4 * match_size(match.match_pattern) for match in patterned
            ]

            # so pick a random choice of words with patterns, followed by all unplaced words, with
            # reference for longest word
            try:
                # self.gui.set_moves('hints')
                return log_return(self.hints.pop())
            except (ValueError, IndexError):
                pass
            if length_first:
                try:
                    # self.gui.set_moves('unplaced long')
                    return log_return(unplaced_long_words.pop())
                    # print(' unplaced long words', unplaced_long_words)
                except (ValueError, IndexError):  # no more long words
                    pass
                try:
                    # self.gui.set_moves('random patterned')
                    return log_return(
                        random.choices(patterned,
                                       weights=patterned_weights,
                                       k=1)[0])
                    # return random.choices(patterned + unplaced, weights=patterned_weights + unplaced_weights,k=1).pop()
                except (ValueError, IndexError):
                    pass
                try:
                    # self.gui.set_moves('random')
                    return log_return(random.choice(self.word_locations))
                except (ValueError):
                    print('returned here')
                    return None

            else:
                try:
                    # self.gui.set_moves('patterned and unplaced')
                    # return random.choices(patterned, weights=patterned_weights,k=1)[0]
                    return log_return(
                        random.choices(patterned + unplaced,
                                       weights=patterned_weights +
                                       unplaced_weights,
                                       k=1).pop())
                    # print(' unplaced long words', unplaced_long_words)
                except (ValueError, IndexError):  # no more long words
                    pass
                try:
                    # self.gui.set_moves('long words')
                    return log_return(unplaced_long_words.pop())
                except (ValueError, IndexError):
                    pass
                try:
                    # self.gui.set_moves('random')
                    return log_return(random.choice(self.word_locations))
                except (ValueError):
                    return None

    def update_all_matches(self):
        # need to update match for contained word
        for word in self.word_locations:
            try:
                match = [
                    self.board[coord] if self.board[coord].isalpha() else '.'
                    for coord in word.coords
                ]
                match = ''.join(match)
                word.match_pattern = self.merge_matches(
                    word.match_pattern, match)
            except (IndexError):
                print(traceback.format_exc())
                print(word.coords)
                print(self.board.shape)

    def update_board_and_soln(self):
        # update all occurences of letters on board in solution_dict
        # if a letter is not in solution_dict, then add it in
        letter_pos = np.argwhere(np.char.isalpha(self.board))
        for pos in letter_pos:
            letter = self.board[tuple(pos)]
            no = self.number_board[tuple(pos)]
            # need to check if letter already in solution_dict
            if letter not in self.solution_dict.values():
                self.solution_dict[no] = letter

        # now fill the rest of board from solution_dict
        for r in range(len(self.board)):
            for c in range(len(self.board[0])):
                no = self.number_board[(r, c)]
                letter = self.solution_dict.get(no, None)
                if letter:
                    self.board[(r, c)] = letter

    def number_words_solve(self, max_iterations=2000, max_possibles=None):
        """ This is used to solve number words or cryptograms
      Words are only fixed when they match completely
      Every time a word is fixed, the solution dict is updated
      and the board is updated with letters. Hence known is updated each time
      """
        index = 0
        self.populate_order = []
        while any([not word.fixed for word in self.word_locations]):
            index += 1
            if self.debug:
                print('Next Iteration >>>>>>>')
            if index == max_iterations:
                break
            known = self.known(
                self.board)  # populates word objects with match_pattern
            self.hints = list(
                set([
                    word for word in self.word_locations for k in known
                    if word.intersects(k)
                ]))

            if self.debug:
                print('number hints', len(self.hints))
                try:
                    # self.gui.gs.highlight_squares(word.coords)
                    self.gui.update(self.board)
                    sleep(0.25)
                except (AttributeError):
                    pass
            while True:
                try:  # exits when used all hints
                    word = self.hints.pop()
                    length, possibles = self.get_possibles(
                        word.match_pattern, max_possibles)
                    if length:
                        if self.debug:
                            print(f'{word=}, {word.match_pattern=}, {length=}')
                        # simple solutions
                        if word.fixed:
                            continue
                        if length < 10:
                            for possible in possibles[::-1]:
                                # test if all letters in solution dict
                                # if so, drop this possibility
                                res = set(possible).difference(
                                    set(self.solution_dict.values()))
                                if not res:
                                    possibles.remove(possible)
                                    length -= 1
                        if self.debug:
                            if length > 5:
                                print(possibles[:5])
                            else:
                                print(possibles)
                        # only one word fits
                        if length == 1:
                            # only word. use it
                            self.fix_word(word, possibles.pop())
                            if self.debug:
                                print('>>>>>>>>fix word', word)

                except (ValueError, IndexError):
                    # arrive here when all existing hints exhausted
                    self.update_board_and_soln()
                    self.update_all_matches()
                    if self.debug:
                        print(index, self.populate_order, self.solution_dict)
                        self.gui.print_board(self.board)
                    # now continue outer loop
                    break
        if self.debug:
            print(self.populate_order)

    def solve_swordsmith(self, strategy='dfs'):
        """ solve using swordsmith implementation"""
        import swordsmith.swordsmith as sword
        # convert board to grid, replace space with dot, and hash with space
        self.board = np.array(self.empty_board)
        grid = np.char.replace(np.char.replace(self.board, ' ', '.'), '#', ' ')
        crossword = sword.BritishCrossword.from_grid(grid)
        crossword.max_cycles = self.max_cycles
        filler = sword.get_filler(sname(**{'strategy': strategy, 'k': 5}))
        wordlist = sword.Wordlist(self.all_words)
        filler.fill(crossword=crossword, wordlist=wordlist, animate=self.debug)
        for slot in crossword.slots:
            for i, idx in enumerate(slot):
                self.board[idx] = crossword.words[slot][i]

        self.board[self.board == ' '] = '#'
        self.populate_order = crossword.words.values()
        for word in self.word_locations:
            word.word = crossword.words[tuple(word.coords)]
            word.fixed = crossword.is_word_filled(word.word)
        if self.debug:
            print(crossword)
        return crossword.index

    def populate_words_graph(self,
                             length_first=True,
                             max_iterations=2000,
                             max_possibles=None,
                             swordsmith_strategy=False):
        # for all words attempt to fit in the grid, allowing for intersections
        # some spaces may be known on empty board
        self.start_time = time()
        index = 0
        if swordsmith_strategy:
            index = self.solve_swordsmith(strategy=swordsmith_strategy)
        else:
            self.populate_order = []
            while any([not word.fixed for word in self.word_locations]):
                fixed = [word for word in self.word_locations if word.fixed]
                if self.debug:
                    self.gui.set_message(
                        f' placed {len(fixed)} {index} iterations')
                word = self.get_next_cross_word(index, max_possibles,
                                                length_first)

                if word is None:
                    #if self.debug:
                    #     try:
                
                                        #print(
                            #    f'options for word at {word.start} are {options}'
                            #)
                    #         print('possibles for stuck word', self.possibles)
                    #     except (AttributeError):
                    #         pass
                    continue

                if self.debug:
                    try:
                        # self.gui.gs.highlight_squares(word.coords)
                        self.gui.update(self.board)
                        sleep(0.25)
                    except AttributeError:
                        pass
                if index == max_iterations:
                    break

                options = self.look_ahead_3(
                    word, max_possibles=max_possibles)  # child, coord)
                if options is None:
                    break
                index += 1

        fixed = [word for word in self.word_locations if word.fixed]

        # self.update_board(filter_placed=False)
        if self.debug:
            self.gui.print_board(self.board)
            print('Population order ', self.populate_order)
        ptime = self.delta_t('time', do_print=False)
        method = '' if not swordsmith_strategy else swordsmith_strategy
        msg = f'Filled {len(fixed)}/ {len(self.word_locations)} words in {index} iterations,  {ptime}secs, {method}'
        words = len([w for w in self.word_locations if w.word])
        print('no words', words)
        # print(msg)
        self.gui.set_prompt(msg)
        self.gui.update(self.board)
        return self.board

    def get_word(self, wordlist, req_letters, wordlength):
        ''' get a word matching req_letters (letter, position) '''
        match = ['.'] * wordlength
        for req in req_letters:
            match[req[1]] = req[0] if req[0] != ' ' else '.'
        match = ''.join(match)
        # self.gui.set_moves(match)
        m = re.compile(match)
        possible_words = [word for word in wordlist if m.search(word)]
        # remove already placed words

        if possible_words:
            try_word = random.choice(possible_words)
            self.score += 1
            return try_word, possible_words
        else:
            # print(f'could find {match} for req_letters')
            return match, None

    def known(self, board=None):
        """ Find all known words and letters """
        if board is None:
            board = self.empty_board
        known = []
        # get characters from empty board
        # written this wa to allow single step during debugging
        [
            known.append((r, c)) if self.get_board_rc(
                (r, c), board) != SPACE and self.get_board_rc(
                    (r, c), board) != BLOCK and self.get_board_rc(
                        (r, c), board) != '.' else None
            for r, rows in enumerate(board) for c, char_ in enumerate(rows)
        ]
        # board = np.array(self.empty_board)
        # known = np.where(board!=BLOCK || board!#==SPACE)
        # now fill known items into word(s)
        if known:
            for word in self.word_locations:
                for k in known:
                    if word.intersects(k):  # found one
                        if all([wc in known
                                for wc in word.coords]):  # full word known
                            word.set_word(''.join([
                                self.get_board_rc(pos, board)
                                for pos in word.coords
                            ]))
                            if self.debug:
                                print(f'>>>>>>>>>Set word from known {word}')
                            word.match_pattern = word.word
                            word.fixed = True
                            break
            # now deal with indivdual letters
            # check each coordinate
            for coord in known:
                for word in self.word_locations:
                    if word.intersects(coord):  # found one
                        letter = self.get_board_rc(coord, self.board)
                        match = ''.join([
                            letter if coord == c else '.' for c in word.coords
                        ])
                        if word.match_pattern:
                            word.match_pattern = self.merge_matches(
                                word.match_pattern, match)
                        else:
                            word.match_pattern = match
                        if self.debug:
                            print('set word match  from known ', word.start,
                                  word.index, word.match_pattern)
        return known

    def get_possibles(self, match_pattern, max_possibles=None):
        ''' get a list of words matching match_pattern, if any
    from self.word_dict '''

        known_words = [word.word for word in self.word_locations if word.fixed]
        m = re.compile(match_pattern)
        try:
            possibles = [
                word for word in self.all_word_dict[len(match_pattern)]
                if m.search(word) and word not in known_words
            ]
            l = len(possibles)
            if max_possibles and l > max_possibles:
                possibles = possibles[0:max_possibles]
            if possibles:
                return len(possibles), possibles
            else:
                # print(f'could find {match_pattern} for req_letters')
                return None, match_pattern
        except (KeyError):

            print(match_pattern)
            print(traceback.format_exc())
            return None, match_pattern

    def fix_word(self, word_obj, text):
        """ place a known word """
        if not word_obj.fixed:
            word_obj.set_word(text)
            word_obj.fixed = True
            self.populate_order.append(text)
            word_obj.match_pattern = text
            word_obj.update_grid('', self.board, text)
            if self.debug:
                print(f'Placed word {word_obj}')
            self.update_children_matches(word_obj)
            for coord, child in word_obj.children.items():
                # print(child.match_pattern, type(child.match_pattern))
                child.update_grid('', self.board, child.match_pattern)

    def merge_matches(self, a, b):
        ''' take two matches and combine them'''
        if a == '': return b
        elif b == '': return a
        else:
            return ''.join([y if x == '.' else x for x, y in zip(a, b)])

    def update_children_matches(self, word_obj, clear=False):
        """ update the match patterns for children of current wordl
    eg if word = abacus and child1 intersects at pos 1 match for child is 'a.....' """
        parent_word = word_obj.word
        children_dict = word_obj.children
        # intersections = word_obj.get_inter()
        # coords = word_obj.coords
        for key, child in children_dict.items():
            if clear:
                child.match_pattern = ''
            else:
                match = []
                for ichild in child.coords:
                    l = '.'
                    for p, letter in zip(word_obj.coords, parent_word):
                        if ichild == p:
                            l = letter
                    match.append(l)
                match = ''.join(match)
                child.match_pattern = self.merge_matches(
                    child.match_pattern, match)
                # if not child.fixed:
                # child.set_word(match)  # for testing
                # child.update_grid('', self.board, match)

    def calc_matches(self, word_obj, try_word=None):
        """ calculate the match patterns for children of current word
    eg if word = abacus and child1 intersects at pos 1 match for child is 'a.....' """
        if try_word is None:
            parent_word = word_obj.word
        else:
            parent_word = try_word
        children_dict = word_obj.children
        # intersections = word_obj.get_inter()
        # coords = word_obj.coords
        c_dict = {}
        for key, child in children_dict.items():
            match = []
            for ichild in child.coords:
                l = '.'
                for p, letter in zip(word_obj.coords, parent_word):
                    if ichild == p:
                        l = letter
                match.append(l)
            match = ''.join(match)
            c_dict[key] = self.merge_matches(child.match_pattern, match)
        return c_dict

    def compute_depths(self):
        """ find how many nodes to traverse before arriving  back at same word"""
        for node in self.word_locations:
            [
                w.set_visited(False) for w in self.word_locations
                if w is not node
            ]
            visited = [
                item for item in self.word_locations if item.get_visited()
            ]
            component = self.bfs(
                node, visited,
                stop=self.max_depth)  # Traverse to each node of a graph
            #path = [f'Node={node.index} item={item.index}, {item.start}' for item in component]
        return component

    def dfs(self, node, graph, visited, component, stop=None):
        component.append(node)  # Store answer
        node.visited = True  # Mark visited
        # Traverse to each adjacent node of a node
        for coord, child in node.children.items():
            if child is stop:
                return
            if not child.get_visited(
            ):  # Check whether the node is visited or not
                self.dfs(child, graph, visited, component,
                         stop)  # Call the dfs recursively

    def bfs(self, node, visited, stop=None):  # function for BFS
        """ This will return all child node of starting node
    return is a list of dictianaries {'word_obj', 'depth' 'parent'} """
        queue = []
        component = []
        component.append({'word_obj': node, 'depth': 0, 'parent': None})
        node.visited = True
        queue.append((0, None, node))

        while queue:  # Creating loop to visit each node
            depth, coord, item = queue.pop(0)
            if depth >= stop:
                break
            # print(f'Depth={depth} Item={item.index} item={item.start}')
            for coord, child in item.children.items():
                if not child.get_visited():
                    component.append({
                        'word_obj': child,
                        'depth': depth + 1,
                        'parent': item
                    })
                    child.visited = True
                    queue.append((depth + 1, coord, child))
        return component

    def search(self):
        graph = self.word_locations
        known = self.known()
        if known:
            for word in self.word_locations:
                if word.intersects(known[0]):  # found one
                    node = word
                    break
        else:
            node = self.word_locations[0]  # Starting node
        [w.set_visited(False) for w in self.word_locations]
        visited = [item for item in graph if item.get_visited()]
        component = []
        self.dfs(node, graph, visited,
                 component)  # Traverse to each node of a graph
        path = [f'{item.index}, {item.start}' for item in component]
        if self.debug:
            print("Following is the Depth-first search:")  # Print the answer
            for p in path:
                print(p)
        for i, c in enumerate(component[1:]):
            self.word_locations[i - 1].parent_node = c
        return component

    def _best_score(self, options):
        """place best choice from options
      the aim is place best word that allows other words to follow
      highest score wins, since this means greatest options for next level
      1000 means only one word fits at some level, so not a good choice
      need to avoid choosing  word that blocks an intersecting word
      options is dictionary of try_word, list of dictionary for intersections , score
      """
        scores = [(key, [v_[0][1] for _, v_ in v.items()])
                  for key, v in options]
        if self.debug:
            print(f'Scores________{len(scores)} words__________')
            [print(score) for score in scores]
        # def mx(n): return sum(n[1])
        # filter subwords not possible
        scores1 = [score for score in scores if 0 not in score[1]]
        # filter only one option for subword
        scores2 = [score for score in scores1
                   if 1000 not in score[1]]  # remove unique word
        # if result is empty, reinstate unique word
        if not scores2:
            scores2 = scores1
        # still no good, reinstate not possible subword, since we' re probably at end of board fill
        if not scores2:
            scores2 = scores
        s = sorted(scores2, key=lambda x: sum(x[1]), reverse=True)
        if self.debug:
            print(f'Scores filtered_____{len(s)} words__________')
            [print(score) for score in s]

        # choose shortest that is not zero
        try:
            # find all best that have same score
            first = sum(s[0][1])
            best = [word for word, score in s if sum(score) >= first - 5]
            if self.debug:
                print('best', best)
            select = random.choice(best)
        except (IndexError):
            return None
        return select

    def _search_down(self,
                     word,
                     dict_parents,
                     try_word=None,
                     max_possibles=None):
        """ recursive function to establish  viabilty of options """
        # sets matches for all children of word using try_word
        #component.append({'try_word': try_word, 'word_obj': word, 'depth':0, 'parent':None})

        matches = self.calc_matches(word, try_word)
        found = defaultdict(list)
        for child, depth in dict_parents[word]:
            if child.fixed:
                continue
            coord = word.get_child_coord(child)
            match = matches[coord]
            length, possibles = self.get_possibles(match, max_possibles)
            #print(length, 'possible words for ', child.start, child.direction )
            if not length and not child.fixed:
                found[child].append((match, 0))

            elif length == 1:
                if not child.fixed:
                    found[child].append((possibles.pop(), 1000))

            else:
                try:
                    found[child].append(
                        (lprint(possibles, 3), length))  # must be atleast 1
                    #found[child].append((possibles,100 * depth + length)) # must be atleast 1
                    for index, try_word in enumerate(possibles):
                        #self.gui.set_message2(f'{index}/{length} possibles  at {child.start} trying {try_word}')
                        result = self._search_down(child, dict_parents,
                                                   try_word, max_possibles)
                        found[child].extend(result)
                except (KeyboardInterrupt):
                    return None

        return found  # list of True, False for this top,level option

    def look_ahead_3(self, word, max_possibles=100):
        """ This uses breadth first search  to look ahead
       use max_possibles with a full word
       list comprehensions are extensively used to allow simple stepove during debug
       for defined word puzzles. there is no guessing. there can be only one solution, so if a decision cannot be made in this iteration, it must be der
       deferred  to later.
       Use varaible max_possibles to switch between unconstrained and constrained puzzles """
        # self.update_board(filter_placed=True)
        # sleep(1)

        [w.set_visited(False) for w in self.word_locations]
        [word.set_visited(True) for w in self.word_locations if w.fixed]
        visited = [item for item in self.word_locations if item.get_visited()]
        components = self.bfs(word, visited, stop=self.max_depth)
        if False:  # self.debug:
            for c in components:
                try:
                    print(
                        f"{c['word_obj'].start}{c['word_obj'].direction}  depth={c['depth']} parent={c['parent'].start}{c['parent'].direction}"
                    )
                except Exception:
                    pass
        # now have  list of dictionaries {'word_obj', 'depth' 'parent'}
        # create dictionary of children of each parent

        # create a new dictionary using parent word as key
        dict_parents = defaultdict(list)
        {
            dict_parents[c['parent']].append((c['word_obj'], c['depth']))
            for c in components if c['parent'] is not None
        }
        # {dict_parents[c['parent']].append(c['word_obj']) for c in components if c['parent'] is not None}
        if self.debug:
            print('>Start', word)
        #[print('parent ', k.start,k.direction,[str(f.start)+f.direction for f in v]) for k,v in dict_parents.items()]
        match = word.match_pattern
        length, possibles = self.get_possibles(match, max_possibles)
        if self.debug:
            print(length, 'possible words')
        options = []
        try:
            # simple solutions
            if word.fixed:
                result = True
            # no word fits here
            elif length is None and not word.fixed:
                result = False  #print(f'wrong parent word {word.word} shouldnt be here')
            # only one word fits
            elif length == 1:
                # only word. use it
                self.fix_word(word, possibles.pop())
                if self.debug:
                    print('>>>>>>>>fix word line 701', word)
                result = True
            # ok now need to look ahead
            else:
                options = []
                max_component = []
                for index, try_word in enumerate(possibles):
                    if self.debug:
                        self.gui.set_message(
                            f'{index}/{length} possibles  at {word.start} trying {try_word}'
                        )
                    result = self._search_down(word,
                                               dict_parents,
                                               try_word=try_word,
                                               max_possibles=max_possibles)
                    # need result to be greatest number of hits in order to best choose options
                    # if self.debug:
                    #    print('Try Word ', try_word)
                    #     [print('Key', k, v)  for k, v in result.items()]
                    if result is None:
                        if self.debug:
                            print('result is NoneXXXXXXXXXXXXXXXXXXXXXXXX')
                        return None
                    if max_possibles:
                        if all(result):
                            options.append((try_word, result))
                    else:
                        # if all(result):
                        valid = True
                        for i in result.values():
                            if len(i) == 1 and i.pop()[1] == 0:
                                valid = False
                                break  # not valid
                        if valid:
                            options.append((try_word, result))
                # if self.debug:
                #    print('result OPTIONS ',word, options)
                if len(options) == 1 and not word.fixed:
                    self.fix_word(word, options.pop()[0])
                    if self.debug:
                        print('>>>>>>>>>>fix word line 703 ', word)

                    result = True
                    # print(f'try_word at {word.start} {try_word} {result}')
                elif options:  # and max_possibles:
                    # dealwith only one option is not zero
                    _options = [option for option in options if option[1] != 0]
                    if len(_options) == 1:
                        self.fix_word(word,
                                      _options.pop()[0])  # already random
                        if self.debug:
                            print(
                                '>>>>>>>>>fix word line 773 from max options ',
                                word)
                        return
                    # deal with one option being large and all others = 100
                    _options = [
                        option for option in options if option[1] != 1000
                    ]
                    if len(_options) == 1:
                        self.fix_word(word,
                                      _options.pop()[0])  # already random
                        if self.debug:
                            print(
                                '>>>>>>>>>fix word line 773 from max options ',
                                word)
                        return

                    if max_possibles:
                        select = self._best_score(_options)
                        if select:
                            self.fix_word(word, select)  # already random
                            if self.debug:
                                print('selectxxxxxxxxxxxxx', select)
                                print(
                                    '>>>>>>>>>fix word line 773 from max options ',
                                    word)

        except (Exception, IndexError):
            print(locals())
            print(traceback.format_exc())

        finally:
            return options  # unplaced option
            
    def get_words(self, file_list):
        """ get words, copied from lettergame"""
        all_word_list = []
        for word_file in file_list:
          with open(f'{word_file}', 'r') as f:
            words = [line.strip() for line in f]
          all_word_list.extend(words)
        self.all_words = set(all_word_list)  # fast seach for checking
    
    def length_matrix(self, search_directions=['down', 'across']):
        # process the board to establish starting points of words, its direction, and length
        self.word_locations = []
        # self.start_time= time()
        direction_lookup = {'down': (1, 0), 'across': (0, 1), 'left': (0, -1),
                             'up': (-1, 0),  'diag_lr': (1, 1), 'diag_rl': (1, -1),
                             'diag_ul': (-1, -1), 'diag_ur': (-1, 1)}
        directions = [direction_lookup[d] for d in search_directions]
                  
        for r, row in enumerate(self.board):
          for c, character in enumerate(row):
            rc = r, c
            if character == BLOCK:
              continue
            else:
              for d, d_name in zip(directions, search_directions):
                delta = (0, 0)
                length = 1
                while self.check_in_board(self.add(rc, delta)) and self.get_board_rc(self.add(rc, delta), self.board) != BLOCK :
                    length += 1
                    delta = self.add(delta, d)
                length -= 1
                t = Word(rc, d_name, length)
                
                if length > 1 and not any([w.intersects(rc, d_name) for w in self.word_locations]):
                  self.word_locations.append(t)
                  
        if self.word_locations:
          for word in self.word_locations:
            word.match_pattern = '.' * word.length
          lengths = Counter([word.length for word in self.word_locations])
          self.wordlengths = dict(sorted(lengths.items()))
                    
          self.min_length = min(self.wordlengths)
          self.max_length = max(self.wordlengths)
          # self.delta_t('len matrix')
        return self.min_length, self.max_length
        
    def initial_grid(self, type, size):
        """ This is EXPERIMENTAL
        
        create initial grid with blocks changing in a row
        type has form [(no_x1, no_y1, type1), (no_x2, no_y2, type2)]
        where no_x1, no_y1 will form a sub grid of type 1
        no_x2, no_y2 will form a subgrid adjacent to the first
        """
        types = {0: np.array([['#', ' '], [' ', ' ']]), 
                 1: np.array([[' ', '#'], [' ', ' ']]),
                 2: np.array([[' ', ' '], ['#', ' ']]),
                 3: np.array([[' ', ' '], [' ', '#']]),
                 4: np.array([[' ', ' '], [' ', ' ']])
                 }
        if isinstance(size, tuple):
          self.sizey, self.sizex = size
        else:
           self.sizey = self.sizex = size
        # widerby one space to permit filling with 2x2 patterns
        self.board = np.full((self.sizey, self.sizex+1), SPACE)
        
        # type can be fixed for regular grid
        #  ([no_x, no_y, type1],[no_x, no_y, type2] etc))
        if isinstance(type, int):            
            self.type = ([(self.sizex//2, self.sizey//2, type)])
        else:
            self.type = type
            
        # fill board with types
        for typeset in self.type:          
            # typeset is (no_x, no_y, type)
            # subs is list of subblocks          
            subs = [np.tile(types[typeset[2]], (typeset[1], typeset[0]))      
                    for typeset in self.type]    
        # now place subblocks into self.board
        offx = 0
        for sub in subs:         
            self.board[0: sub.shape[0], 
                       offx: offx+sub.shape[1]] = sub
            offx = sub.shape[1]
        # clip board to defined size   
        self.board = self.board[:self.sizey, :self.sizex]
        # efficient mirroring of spaces and blocks
        # fill spaces with element from rotated board
        self.board = np.where(np.char.isspace(self.board), np.rot90(self.board, 2), self.board)    
        if self.debug:    
            self.print_board(msg=str(self.board.shape))
        return self.board      
        
    def create_grid_alt(self, type=3, size=15, min_length=3, max_length=9):
        # EXPERIMENTAL
        
        # deals with non uniform types
        # iterate over every row
        self.max_length = max_length
        self.min_length = min_length
        self.initial_grid(type, size)              
         # split rows
        if self.debug: 
            print('FILLING ROWS')
        try:
            for r in range(0, ceil(self.sizey / 2)):
                self.split_row_alt(r, row=True)
            # print('filled rows')
            if self.debug: 
                self.print_board(None, 'FINAL ROWS')
            
            for c in range(0, ceil(self.sizex / 2)):
                self.split_row_alt(c, row=False)
                
        except ValueError as e:
            print(e)
            return None
        return self.board
         
    def create_grid(self, type=3, size=15, min_length= 3, max_length=9):
        """ create a british style crossword grid of defined odd numbered size
        1.starts with alternating black white squares
          black starts in  1 of 4 start positions 0:(0,0), 1:(0,1), 2:(1,0) or 3:(1,1)
        2. word lengths will be minimum 3, maximum to be defined (11 absolute max)
        3. starting at first empty row (0,or 1 depending on type), split the row by
           placing a block to make words on 1st row min3, max max_length
        4. move to next empty row and repeat, also ensuring that
           min length of all empty vertical rows are greater than 3.
           and position is not same as last one
        5. repeat 4 to halfway.
        6. fill lower half with mirror image
        7. start with first empty column
           split the row by
           placing a block to make words on 1st row min3, max max_length, ensuring that all horizontal rows are between
           3 and max_length
        7. repeat to middle
        8. fill right half with mirror image
        9. verify spread of word lengths
        10. print grid
        note: X shape are desirable. if given choice of disturbing
        X or not, dont't
        
        TODO could this be modified to switch types mid grid?
        it would need to select every line and avoid word lengths of 1
        """
        types = {k:divmod(k,2) for k in range(4)}  # for position of starting block
        self.max_length = max_length
        self.min_length = min_length
        if isinstance(size, tuple):
          self.sizey, self.sizex = size
        else:
           self.sizey = self.sizex = size           
        self.type = type            
        self.start = types[type]
        self.board = np.full((self.sizey, self.sizex), SPACE)
        # fill alternating square
        self.board[self.start[0]:self.sizey:2, self.start[1]:self.sizex:2] = BLOCK
        
        # split empty rows
        if self.debug: 
            print('FILLING ROWS')
        try:
            for r in range(self.start[0] ^ 1, ceil(self.sizey / 2), 2):
                self.split_row(r, row=True)
            # print('filled rows')
            if self.debug: 
                self.print_board(None, 'FINAL ROWS')
            
            for c in range(self.start[1] ^ 1, ceil(self.sizex / 2), 2):
                self.split_row(c, row=False)
                
        except ValueError:
            # print(traceback.format_exc())
            return None
        return self.board
        

    def lengths(self, index, row):
        """return array of lengths and indices  of words in selected axis
        usinf run length encding is very efficient but complex
        get row or column
        """
        # get row or column as array
        a = np.take(self.board, index, axis=int(not row))
        lengths, start_locations, characters = rle(a)
        lengths = list(lengths[characters == ' '])
        indices = list(start_locations[characters == ' '])  
        if self.debug:
            print(a, lengths, indices)
        return lengths, indices
        
    def is_x_design(self, loc):
        """ loc is at centre of x shape """
        r, c = loc
        return self.board[r-1: r+1][c-1: c+1] == np.array(
          [['#', ' ', '#'], [' ' ' ', ' '], ['#', ' ', '#']])
                                                        
    def next_to_x(self, loc):
        """ loc is next to x shape """
        x = np.array([['#', ' ', '#'], [' ', '#', ' '], ['#', ' ', '#']])
        r, c = loc
        locs = [(r+1, c+2), (r-1, c+2),
                (r+1, c-2), (r-1, c-2),
                (r+2, c+1), (r+2, c-1),
                (r-2, c+1), (r-2, c-1)]
        for location in locs:
            R, C = location
            if self.board[R-1: R+1][C-1: C+1] == x:
                return True
        return False
      
    def check_lengths(self, index, row):
          """ check lengths in selected row or column
              and length of all columns or rows
              return True if all ok
          index is row or column number
          row is True if we are dealing with rows
          """
          # check current row/col
          lengths, indices = self.lengths(index, row)
          if self.debug: 
              print(f'Index {index}, {"Row" if row else "Column"}, lengths {lengths}')
          
          if any([(l>self.max_length or l<3) for l in lengths]):
              return False
          # check other cols/rows
          start = self.start[row] ^ 1  # invert 0-1, 1-0
          if self.debug: 
              print(f'dealing with {"Rows" if not row else "Columns"}')
          size = self.sizex if row else self.sizey
          lengths = [self.lengths(index, not row)[0] for index in range(start, size, 2)]
          if self.debug: 
              print(f'Lengths are {lengths}')
          # if any column lengths < 3 in flattened set of lengths
          a = set(list(range(1,self.min_length)))
          b = set(sum(lengths, []))
          #print('b=', b)
          if a.intersection(b):
              return False
          return True
    
    def final_lengths(self):
        """report the number of words in each row and column """
        all_lengths = {}
        for row in [True, False]:
          rowstr = 'row' if row else 'col'
          all_lengths[rowstr] = {}
          size = self.sizey if row else self.sizex
          for i in range(size):
            lengths_ = self.lengths(i, row)
            if all([x == 1 for x in lengths_]):
              continue
            all_lengths[rowstr][i] = lengths_
        return all_lengths
          
    def print_board(self, board=None, msg=None, show_lengths=False):
        if board is None:
          board = self.board
        if msg:
            print(msg)
        if show_lengths:
            # print no words against each row/col
            lengths_ = self.final_lengths()
            str_= '  '
            for i, _ in enumerate(board[0]):
               ix = len(lengths_['col'].get(i, []))
               s = str(ix) if ix else ' '
               str_ += s
            print(str_)
            for i, row in enumerate(board):
              ix = len(lengths_['row'].get(i, []))
              print(str(ix) if ix else ' ', ''.join(row))
            
        else:
            print('\n'.join([''.join(row) for row in board]))
        
    def mirror(self, rc):
        # copy the element at loc to its mirror image (x &y)
        r, c = rc
        self.board[(self.sizey-1-r, self.sizex-1-c)] = self.board[rc]
        
    def permutate(self,n, size):
       """ split an line of length size into n pieces 
       returns list of list of block locations"""       
       possible_numbers = range(self.min_length, self.max_length+1)
       # list of n lists of possible_numbers
       group = [possible_numbers] *  n         
       # list of all combinations of lengths allowing for positions
       # occupied by blocks
       possibles = [x for x in itertools.product(*group) if sum(x) == (size-n+1)]  
       
       # now find locations of blocks
       indices = [[x+i for i, x in enumerate(itertools.accumulate(poss)) if i<n-1] for poss in possibles]
       if self.debug:
           print()
           print(f'possibles for {n} splits of {size} min {self.min_length}, max {self.max_length} {possibles}')
           print(f'indices for {n} splits of {size} min {self.min_length}, max {self.max_length}  {indices}')       
       return indices
    
    def mix_possibles(self, row, size=None):
        """ mix possible splits from 2 or 3 splits """
        # split slice into minimum 2 parts, randomly 3 parts
        # no 3 parts is same as 2parts(if any)
        # giving 50% chance
        if size is None:
           size = self.sizex if row else self.sizey
           
        possibles = []
        poss2 = self.permutate(2, size)
        poss3 = self.permutate(3, size)
        poss4 = self.permutate(4, size)
        random.shuffle(poss3)
        # produce all possibilities
        possibles.extend(poss2)
        if poss2:
            possibles.extend(poss3[:len(poss2)])
        else:
            possibles.extend(poss3)        
            possibles.extend(poss4[:len(poss3)])
        if not possibles:
          # allow for shortening or no split
          possibles.extend([[0], [None], [size-1]])
        random.shuffle(possibles) 
        
        return possibles
        
    def split_row_alt(self, index, row=True):
        """EXPERIMENTAL
        placing a block to make words on row min3, max max_length
        allow for alternating space and blocks
        """    
        lengths, indices = self.lengths(index, row)           
        lens_ = [l for l, i in zip(lengths, indices) if l>self.min_length]
        ind_ = [i for l, i in zip(lengths, indices) if l>self.min_length]
        for size, start in zip(lens_, ind_):
            possibles = self.mix_possibles(row, size)
            # try each possible 
            for i, possible in enumerate(possibles):
                placed = []
                # print('selected split', len(possible))
                # place each block
                for location in possible:
                    if location:
                        loc = (index, location+start) if row else (location+start, index)
                        placed.append((loc, self.board[loc]))
                        self.board[loc] = BLOCK
                        self.mirror(loc)
                        if self.debug: 
                            print(f'trying row {index} positions {possible}')
                        if self.check_lengths(index, row):
                           if self.debug:
                               print(f'row {index} positions {possible} is valid')
                               self.print_board(None, index)
                           return
                        # reset blocks   
                        for item in placed:
                            loc, value = item                   
                            self.board[loc] = value
                            self.mirror(loc)
            
        #raise ValueError('Grid is not possible')
            
    def split_row(self, index, row=True):
        '''placing a block to make words on row min3, max max_length'''                
        possibles = self.mix_possibles(row)
        # try each possible 
        for i, possible in enumerate(possibles):
            placed = []
            # print('selected split', len(possible))
            # place each block
            for location in possible:
                loc = (index, location) if row else (location, index)
                placed.append((loc, self.board[loc]))
                self.board[loc] = BLOCK
                self.mirror(loc)
            if self.debug: 
                print(f'trying row {index} positions {possible}')
            if self.check_lengths(index, row):
                if self.debug:
                    print(f'row {index} positions {possible} is valid')
                    self.print_board(None, index)
                return
            # reset blocks   
            for item in placed:
                loc, value = item                   
                self.board[loc] = value
                self.mirror(loc)
            
        raise ValueError('Grid is not possible')


WordList = ['wordlists/letters3_common.txt',
            'wordlists/5000-more-common.txt',
            'wordlists/words_10000.txt']

                    
if __name__ == '__main__':
   # test of grid creation and fill
   console.clear()
   # random.seed(1)
   g = CrossWord(None, None, None)
   g.debug = False
   g.max_cycles=10000
   g.get_words(WordList)
   type = random.randint(0,3)
   wordlengths = Counter()
   for i in range(10):
        print(f'\nType {type} Iteration {i} ')
        #board = g.create_grid_alt(type=(([4,4,0],[3,3, 2])), size=(15, 13), min_length=4, max_length=13)
        # board = g.create_grid_alt(type=type, size=(15, 13), min_length=4, max_length=13)
        board = g.create_grid(type=type, size=(21,21), min_length=4, max_length=13)
        if board is not None:
          # g.print_board(board, 'Final')
          g.length_matrix()
          for i, word in enumerate(g.word_locations):
          	word.index = i+1
          print(f'Type={type} {g.wordlengths}')
          wordlengths = wordlengths + Counter(g.wordlengths)
          g.empty_board = g.board.copy()
          # print(g.final_lengths())
          g.solve_swordsmith('dfs')
          g.print_board(np.char.upper(g.board), 'Filled', show_lengths=True)
          # break
   wordlengths = dict(sorted(wordlengths.items()))
   tot = sum(wordlengths.values())
   print('Overall Percentages ', {k: int(v * 100 / tot) for k, v in wordlengths.items()})
   print('Overall Actual wordlengths ', wordlengths)





