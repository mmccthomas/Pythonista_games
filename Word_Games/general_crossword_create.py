# utility to create crosswword puzzles
# similar to pieceword creator

import numpy as np
import base_path
import random
import pickle
import dialogs
from scene import get_screen_size
from itertools import zip_longest
from textwrap import wrap
import matplotlib.colors as mcolors

base_path.add_paths(__file__)
from pieceword_create import PieceWord
from crossword_create import CrossWord
from Letter_game import LetterGame
from gui.gui_interface import Squares, Coord
#PUZZLELIST = "pieceword_templates.txt"
#TILESIZE = 3
CR = '\n'
WordList = [
    'wordlists/letters3_common.txt',
    # 'wordlists/words_alpha.txt',
    #  'wordlists/extra_words.txt',
    'wordlists/5000-more-common.txt',
    'wordlists/words_10000.txt'
]
try:
    with open('keys.pkl', 'rb') as f:
        thes_key = pickle.load(f)
        dict_key = pickle.load(f)
except IOError:
    print('No such pickle file')
    thes_key = 'ABC'


class Cross(PieceWord):

    def __init__(self):
        self.selection = self.select_list()
        LetterGame.__init__(self, column_labels_one_based=True)
        self.first_letter = False
        self.tiles = None
        self.debug = False
        self.lookup_free = False
        self.image_dims = (self.selection, self.selection)
        self.all_clues_done = False
        self.soln_str = '123'
        # self.load_words_from_file(PUZZLELIST, no_strip=True)

        if self.selection is False:
            self.gui.gs.show_start_menu()
            return

        x, y, w, h = self.gui.grid.bbox

        self.gui.set_pause_menu({
            'Continue': self.gui.dismiss_menu,
            'New ....': self.restart,
            'Reveal': self.reveal,
            'Quit': self.quit
        })
        # self.span = self.sizex // TILESIZE
        self.gui.clear_messages()
        self.gui.set_enter('', stroke_color='black')  # hide box
        self.gui.set_top(f'Crossword frame {self.selection}')
        self.finished = False
        self.gui.remove_labels()                

    def get_size(self):
        LetterGame.get_size(self, f'{self.selection},{self.selection}')

    def select_list(self):
        '''Choose which category'''
        items = [f'{i}x{i}' for i in range(13, 23, 2)]
        selection = dialogs.list_dialog('select grid', items)
        if selection:
            return int(selection[:2])
        else:
            return 15

    def fill_board(self):
        """use  swordsmith to fill crossword
      if it fails, then it can be run ahain from control
      """

        def transfer_props(props):
            return {k: getattr(self, k) for k in props}

        cx = CrossWord(self.gui, None, self.all_words)
        cx.max_cycles = 5000
        cx.debug = self.debug
        type = random.randint(0, 3)
        for i in range(10):
            self.board = cx.create_grid(type=type,
                                        size=self.image_dims,
                                        min_length=self.min_,
                                        max_length=self.max_)
            if self.board is not None:
                cx.length_matrix()
                self.word_locations = cx.word_locations
                self.compute_intersections()
                [
                    word.set_index(i + 1)
                    for i, word in enumerate(cx.word_locations)
                ]
                cx.empty_board = self.board.copy()
                cx.solve_swordsmith('dfs')
                break
        self.board = cx.board
        self.empty_board = cx.board.copy()
        self.wordset = self.get_words()
        self.solution_board = self.board.copy()
        self.gui.update(self.board)

    def set_buttons(self):
        """ install set of active buttons
        Note: **{**params,'min_size': (80, 32)} overrides parameter
         """
        W, H = get_screen_size()
        x, y, w, h = self.gui.grid.bbox
        off = 50
        t = h / self.selection
        params = {
            'title': '',
            'stroke_color': 'black',
            'font': ('Avenir Next', 18),
            'reg_touch': True,
            'color': 'black',
            'min_size': (80, 32)
        }

        self.gui.set_enter('Fill',
                           position=(w + off, h),
                           fill_color='orange',
                           **params)
        self.gui.add_button(text='Lookup',
                            position=(w + off + 140, h),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })
        self.gui.add_button(text='Copy',
                            position=(w + off + 230, h),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })

        self.gui.add_button(text='Reload',
                            position=(w + off, h - 80),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })
        # adjust text size to screen
        size = (W - w) // 28
        self.gui.set_moves('Clues',
                           font=('Ubuntu Mono', size),
                           position=(w + 10, y),
                           anchor_point=(0, 0))
        

    def update_buttons(self):
        """ change button text and reset colours """
        coords = np.argwhere(np.char.isalpha(self.board))
        # fill all squares
        self.gui.add_numbers([
            Squares(coord,
                    '',
                    'white',
                    z_position=30,
                    alpha=.2,
                    stroke_color='black',
                    font=('Marker Felt', 15),
                    text_anchor_point=(-0.9, 0.95))
            for coord in coords],
            clear_previous=True)
        # get unique word starts to avoid duplicated indexes
        # for down and across words starting on same square
        try:
		        unique_words = set([word.start for word in self.word_locations])
		        # add and save indices
		        self.indices = {}
		        for coord in unique_words:
		            item = self.gui.get_numbers(coord)
		            item[coord]['text'] = str(self.get_word_obj(coord).index)
		            item[coord]['text_color'] = mcolors.to_rgba('red')
		            self.indices[coord] = str(self.get_word_obj(coord).index)
		            self.gui.put_numbers(item)
        except KeyError:
         	   pass
         	      
    def update_clue_colours(self):
        for word_obj in self.word_locations:
            word = word_obj.word
            # change button colour to show if definition found
            color = 'blue' if self.word_defs[word]['def'] else 'red'
            if 'clue' in self.word_defs[word]:
                color = 'green'
            [self.change_color(coord, color) for coord in word_obj.coords]
        self.gui.set_moves(self.update_clue_text())
        
    def get_words(self):
        """ link word to Word object """
        return {loc.word: loc for loc in self.word_locations}

    def get_word_obj(self, coord):
        for word_obj in self.word_locations:
            if word_obj.start == coord:
                return word_obj

    def change_color(self, coord, color):
        """ change the colour of a Square """
        item = self.gui.get_numbers(coord)
        item[coord]['color'] = mcolors.to_rgba(color)
        self.gui.put_numbers(item)

    def lookup_all(self):
        wait = self.gui.set_waiting('Looking up words')
        missing_words = []
        for i, word_obj in enumerate(self.word_locations):
            word = word_obj.word

            wait.name = f'Finding {word}'
            # lookup using free dictionary,merriam_webster if fail
            self.word_defs[word] = {'def': [], 'synonyms': [], 'line_no': word_obj.start}
            self.lookup(word, self.lookup_free)
            no_defs = len(self.word_defs[word]['def'])
            self.lookup(word, not self.lookup_free)
            if self.word_defs[word]['def'] and no_defs == 0:
                missing_words.append(word)
            
            # change button colour to show if definition found
            color = 'blue' if self.word_defs[word]['def'] else 'red'
            [self.change_color(coord, color) for coord in word_obj.coords]

        self.gui.reset_waiting(wait)
        if missing_words:
            dialogs.hud_alert(f'Found {missing_words} in 2nd dictionary',
                              duration=4)
        if self.debug:
            for word in self.wordset:
                print(CR, word, self.word_defs[word])

    def select_definition(self, word):
        PieceWord.select_definition(self, word)
        #self.update_clue_colours()
        # colour squares green
        if 'clue' in self.word_defs[word]:
            [self.change_color(coord, 'green')
                for coord in self.wordset[word].coords
            ]

    def check_all_clues(self):
        pass

    def update_clue_text(self):
        """ prepare block of clue text
        for normal crossword. need across and down columns
        this is different from pieceword """
        clue_text = ''
        clues = [['ACROSS'], ['DOWN']]
        for word in self.word_locations:
            index = int(word.direction == 'down')
            # add index
            text = f'{self.gui.get_numbers(word.start)[word.start]["text"]:2} '
            try:
                text += f'{self.word_defs[word.word].get("clue", "")}'
                clue_list = wrap(text,
                                 width=20,
                                 initial_indent='',
                                 subsequent_indent='   ',
                                 replace_whitespace=False)
                clues[index].extend(clue_list)
            except AttributeError:
                pass
        for left, right in zip_longest(*clues, fillvalue=' '):
            line = f'{left:<20}  {right}\n'
            clue_text += line
        return clue_text

    def compute_puzzle_text(self, name='puzzle'):
        """produce all text
        add in indexes and seperate by forward slash
        """
        board_str = ''
        for r, row in enumerate(self.board):
            board_str += "'"
            for c, char_ in enumerate(row):
                board_str += self.indices.get((r, c), '')
                board_str += char_
                board_str += '/'
            board_str = board_str[:-1] + "'" + CR

        all_text = CR.join([
            f'{name}_text:',
            self.update_clue_text(), '', f'{name}_frame:', board_str
        ])
        return all_text

    def run(self):
        """
    Main method that prompts the user for input
    """
        LetterGame.load_words(self, file_list=WordList)
        self.min_ = 4
        self.max_ = 12
        self.fill_board()
        self.set_buttons()
        self.gui.update(self.board)
        self.update_buttons()
        while True:
            move = self.get_player_move(self.board)
            move = self.process_turn(move, self.board)
        self.gui.set_message2('')
        self.complete()

    def process_turn(self, move, board):
        """ add prosessing of board touches to initiate
        select_definition
        """
        PieceWord.process_turn(self, move, board)
        if move and hasattr(self, 'word_defs'):
            coord, letter, origin = move
            for word_obj in self.word_locations:
                if coord in word_obj.coords:
                    self.select_definition(word_obj.word)
                    msg = self.update_clue_text()
                    self.gui.set_moves(msg)
                    return

    def recall_state(self):
        """recall WIP puzzle to complete """
        with open('piecestate.pkl', 'rb') as f:
            (self.empty_board, self.board, self.solution_board,
             self.word_defs, self.word_locations, self.selection) = pickle.load(f)     
        self.sizex = self.sizey = self.selection           
        self.image_dims = (self.selection, self.selection)
        self.gui.replace_grid(self.selection, self.selection)
        self.gui.remove_labels()     
        self.wordset = self.get_words()
        self.gui.set_top(f'Crossword frame {self.selection}')
        # now update gui elements
        self.gui.update(self.board)
        self.update_buttons()
        self.update_clue_colours()
                        
    def initialise_board(self):
        pass
    
    def restart(self):
        self.gui.gs.close()
        self.finished = False
        g = Cross()
        g.run()


if __name__ == '__main__':
    g = Cross()
    g.run()





