# utility to create square crossword puzzles
# similar to pieceword creator

import numpy as np
import random
import pickle
import dialogs
from scene import get_screen_size
from itertools import zip_longest
from textwrap import wrap
import matplotlib.colors as mcolor
from types import SimpleNamespace
from time import time
from pieceword_create import PieceWord
from crossword_create import CrossWord
from Letter_game import LetterGame
from gui.gui_interface import Squares, Coord
PUZZLELIST = "crossword_puzzles.txt"
OUTPUTFILE = "crossword_puzzles.txt"

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
        self.across_only = False
        self.INIT_COLOR = 'white'
        self.outputfile = "crossword_puzzles.txt"
        self.savefile = 'piecestate.pkl'
        self.image_dims =  (self.selection[1], self.selection[0])
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
        LetterGame.get_size(self, f'{self.selection[0]},{self.selection[1]}')

    def select_list(self):
        '''Choose which category'''
        items = [f'{i}x{j}' for i,j in zip([13,15,17,19,21,23,15,17],
                                           [13,15,17,19,21,23,21,27])]
        selection = dialogs.list_dialog('select grid', items)
        if selection:
            return int(selection[:2]), int(selection[-2:])
        else:
            return 15, 15

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
        self.wordset = self.get_words(self.across_only)
        self.solution_board = self.board.copy()
        self.gui.update(self.board)
        
    def box_positions(self):
        # positions of all objects for all devices
        x, y, w, h = self.gui.grid.bbox
        off = 0
        position_dict = {'ipad13_landscape': {
        'button1': (w + off + 35, h), 'button2': (w + off + 150, h), 'button3': (w + off + 265, h),
        'button4': (w + off + 35, h - 80),
        'box1': (w + off , y), 'boxsize': (500, 600), 'font': ('Avenir Next', 12)},

        'ipad_landscape': {
        'button1': (w + off + 70, h), 'button2': (w + off + 210, h), 'button3': (w + off + 300, h),
        'button4': (w + off + 210, h - 50),
        'box1': (w + 10 , y), 'boxsize': (500, 600), 'font': ('Avenir Next', 12)},
        
        'ipad_mini_landscape': {
        'button1': (w + off + 40, h), 'button2': (w + off + 180, h), 'button3': (w + off + 270, h),
        'button4': (w + off + 180, h - 50),
        'box1': (w + 10 , y), 'boxsize': (500, 530), 'font': ('Avenir Next', 12)}
        }
        try:
            self.posn = SimpleNamespace(**position_dict[self.gui.device])
        except (KeyError):
            raise KeyError('Portrait mode  or iphone not supported')

    def set_buttons(self):
        """ install set of active buttons
        Note: **{**params,'min_size': (80, 32)} overrides parameter
         """
        W, H = self.gui.wh
        x, y, w, h = self.gui.grid.bbox
        off = 50
        t = h / self.selection[1]
        params = {
            'title': '',
            'stroke_color': 'black',
            'font': ('Avenir Next', 18),
            'reg_touch': True,
            'color': 'black',
            'min_size': (80, 32)
        }

        self.gui.set_enter('Fill',
                           position=self.posn.button1,
                           fill_color='orange',
                           **params)
        self.gui.add_button(text='Lookup',
                            position=self.posn.button2,
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })
        self.gui.add_button(text='Copy',
                            position=self.posn.button3,
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })

        self.gui.add_button(text='Reload',
                            position=self.posn.button4,
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })
        # adjust text size to screen
        fontsize = (W - w) // 28
        self.gui.set_moves('Clues',
                           font=('Ubuntu Mono', fontsize),
                           position=self.posn.box1,
                           anchor_point=(0, 0))
        # trial scrollbox, gives problem with control
        #scroll_, self.wordsbox = self.gui.scrollview_h(w+100,h-600,(W-w), 600, text='Clues', )
        # self.wordsbox.font=('Ubuntu Mono', size)

    def update_buttons(self, color='lightgrey'):
        """ change button text and reset colours """
        PieceWord.update_buttons(self, color=color)
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
                      
        
    def get_word_obj(self, coord):
        for word_obj in self.word_locations:
            if word_obj.start == coord:
                return word_obj       
    
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
                text += f'{self.word_defs[word.word].get("clue", "")}({word.length})'
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
        self.box_positions()
        self.set_buttons()
        self.gui.update(self.board)
        self.update_buttons()
        while True:
            move = self.get_player_move(self.board)
            move = self.process_turn(move, self.board)
        self.gui.set_message2('')
        self.complete()
    
    
    def copy_(self, out=None, final_cr=False):
        super().copy_(out=self.outputfile, final_cr=final_cr)
        
    def recall_state(self):
        """recall WIP puzzle to complete """
        with open(self.savefile, 'rb') as f:
            (self.empty_board, self.board, self.solution_board,
             self.word_defs, self.word_locations, self.selection) = pickle.load(f)     
        self.sizex, self.sizey = self.selection           
        self.image_dims = self.selection
        self.gui.replace_grid(*self.selection)
        self.gui.remove_labels()     
        self.wordset = self.get_words(self.across_only)
        self.gui.set_top(f'Crossword frame {self.selection}')
        # now update gui elements
        self.gui.update(self.board)
        self.update_buttons()
        self.update_clue_colours()
        self.gui.set_moves(self.update_clue_text())
                       
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



