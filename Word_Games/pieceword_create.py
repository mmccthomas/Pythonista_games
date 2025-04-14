"""
This is a new program to generate Pieceword games.
The most interesting part is to create clues for a word
Set up a series (6) of crossword templates, all 15 x 21
All templates need word or words on each horizontal line 
Use existing Pieceword solutions as templates
Fill crossword, using random Words. 
Visually inspect  grid and regenerate of and words in appropriate or acronyms
For each complete across word, find an online definition or synonym
Need this to be automatic
May be https://www.merriam-webster.com/dictionary/word
or https://www.thefreedictionary.com

Pick the best.
Random shuffle the grid split into 3x3 blocks
Create text version of this shuffled grid using spaces for blanks
Create puzzle data, name, name_text, name_frame

add save state

To operate:
  1. select template
  2. if filled grid is not okay, or contains too many 
     odd words, press Fill again
  3. Press Lookup to get definitions of words. this will only work
     if you have 2 keys in file keys.pkl for https://dictionaryapi.com
     as strings thes_key and dict_key.
     Successful lookups will turn button blue, unsuccessful ones
     will turn pink. if all buttons are pink, key was invalid
  3. press each blue button to select appropriate definition or synonym
     button wil turn green
  4. press each pink button and try to enter a suitable clue - be creative!
  5. pressing green button again allows editing of clue
  6. press Randomise to shuffle tiles. this can be repeated as necessary.
  7. press Copy and puzzle nane or number, e.g. puzzle18
  8. open pieceword.txt and paste text to end of file
  
  
"""
# Pieceword game
# tiles are 3x3 squares, to fit into 15 x 35 grid
# file for each puzzle has 3 sections , puzzleno, puzzleno_text, and puzzleno_frame

from time import sleep, time
import sys
import traceback
import pickle
import numpy as np
from urllib.request import urlopen
import requests
import json
import math
import console
import dialogs
import clipboard
from objc_util import on_main_thread
from textwrap import wrap
from random import shuffle, choice
import matplotlib.colors as mcolors
from types import SimpleNamespace
from Letter_game import LetterGame
import gui.gui_scene as gscene
from gui.gui_interface import Coord, BoxedLabel, Squares
from crossword_create import CrossWord


PUZZLELIST = "pieceword_templates.txt"
OUTPUTFILE = "pieceword.txt"
TILESIZE = 3
CR = '\n'

WordList = [
    'wordlists/letters3_common.txt',
    #'wordlists/words_alpha.txt',
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


class PieceWord(LetterGame):

    def __init__(self):
        LetterGame.__init__(self, column_labels_one_based=True)
        self.first_letter = False
        self.tiles = None
        self.debug = False
        self.lookup_free = False
        self.across_only = True
        self.INIT_COLOR = 'yellow'
        self.outputfile = "pieceword.txt"
        self.savefile = 'piecestate.pkl'
        self.image_dims = [7, 5]
        self.all_clues_done = False
        self.soln_str = '123'
        self.load_words_from_file(PUZZLELIST, no_strip=True)
        self.selection = self.select_list()
        if self.selection is False:
            self.gui.gs.show_start_menu()
            return
        self.gui.build_extra_grid(5,
                                  7,
                                  grid_width_x=3,
                                  grid_width_y=3,
                                  color='red',
                                  line_width=5)
        x, y, w, h = self.gui.grid.bbox

        self.gui.set_pause_menu({
            'Continue': self.gui.dismiss_menu,
            'New ....': self.restart,
            'Reveal': self.reveal,
            'Quit': self.quit
        })
        self.span = self.sizex // TILESIZE
        self.gui.clear_messages()
        self.gui.set_enter('', stroke_color='black')  # hide box
        self.gui.set_top(f'Pieceword frame {self.selection.capitalize()}')
        self.finished = False

    def save_state(self):
        """ save the state of play in pickle file """
        sys.setrecursionlimit(1000)
        with open(self.savefile, 'wb') as f:
            pickle.dump([
                self.empty_board, self.board, self.solution_board,
                self.word_defs, self.word_locations, self.selection
            ], f)

    def recall_state(self):
        with open(self.savefile, 'rb') as f:
            self.empty_board, self.board, self.solution_board, self.word_defs, self.word_locations, selection = pickle.load(
                f)
        self.gui.replace_grid(self.sizex, self.sizey)
        # now update gui elements
        self.gui.update(self.board)
        self.wordset = self.get_words(self.across_only)
        self.update_buttons(self.INIT_COLOR)        
        self.gui.set_text(self.wordsbox, self.update_clue_text())
        self.update_clue_colours()            
        self.check_all_clues()

    def get_words(self, across_only=True):
        """ link word to Word object """
        if across_only:
            return {word.word: word for word in self.word_locations if word.direction=='across'}
        else:
            return {word.word: word for word in self.word_locations}
        
    def lookup_all(self):
        wait = self.gui.set_waiting('Looking up words')
        missing_words = []
        for word in self.wordset:
            word_obj = self.wordset[word]
            # self.gui.set_prompt(f'looking up {word}')
            wait.name = f'Finding {word}'
            # lookup using free dictionary,merriam_webster if fail
            self.word_defs[word] = {'def': [], 'synonyms': [], 'line_no': word_obj.start[0] + 1}
            self.lookup(word, self.lookup_free)
            no_defs = len(self.word_defs[word]['def'])
            self.lookup(word, not self.lookup_free)       
            if self.word_defs[word]['def'] and no_defs == 0:
                  missing_words.append(word)
            self.update_clue_colours(word)
        self.gui.reset_waiting(wait)
        if missing_words:
           dialogs.hud_alert(f'Found {missing_words} in 2nd dictionary', duration=4)

        if self.debug:
            for word in self.wordset:
                print()
                print(word, self.word_defs[word])
                
    def change_color(self, coord, color):
        """ change the colour of a Square """
        try:
            item = self.gui.get_numbers(coord)
            item[coord]['color'] = mcolors.to_rgba(color)
            self.gui.put_numbers(item)  
        except KeyError:
            print(traceback.format_exc()) 
               
    def lookup(self, word, method):         
        if method:
            self.lookup_free_dictionary(word)
        else:
            self.lookup_merriam_webster(word)  
            
    def lookup_free_dictionary(self, word):
        """ free dictionary lookup """
        try:
            data = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}').json()
        except json.JSONDecodeError:
            return
        if isinstance(data, list):
            data = data[0]
            try:                        
                self.word_defs[word]['def'].extend([c['definition'] for c in data['meanings'][0]['definitions']])                                  
                self.word_defs[word]['synonyms'].extend([c['synonyms'] for c in data['meanings']])    
            except KeyError as e:
              print(e)  
        
            
    def lookup_merriam_webster(self, word):
        """ lookup word on merriam-webster dictionary
        cab be modified for any other dictionary lookup
        requires api-key in variable thes_key """
        try:
            with urlopen(
                    f'https://www.dictionaryapi.com/api/v3/references/thesaurus/json/{word}?key={thes_key}'
            ) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return
        try:
            if isinstance(data, list):
                data = data[0]
            self.word_defs[word]['def'].extend(data.get('shortdef', 'Not found'))
            self.word_defs[word]['synonyms'].extend(data['meta'].get('syns', 'Not found'))
        except (IndexError, AttributeError):
            return

    def run(self):
        """
    Main method that prompts the user for input
    """
        LetterGame.load_words(self, file_list=WordList)
        self.min_length = 3
        self.max_length = 15
        self.length_matrix()
        self.partition_word_list()
        self.compute_intersections()
        self.fill_board()
        self.solution_board = self.board.copy()
        self.box_positions()
        self.set_buttons()
        self.update_buttons(self.INIT_COLOR )
        while True:
            move = self.get_player_move(self.board)
            move = self.process_turn(move, self.board)
            #if self.game_over():
            #  break
        self.gui.set_message2('')
        self.complete()
        
    def box_positions(self):
        # positions of all objects for all devices
        x, y, w, h = self.gui.grid.bbox
        off = 100
        position_dict = {'ipad13_landscape': {
        'button1': (w + off + 135, h), 'button2': (w + off + 275, h), 'button3': (w + off + 365, h),
        'button4': (w + off + 275, h - 80), 'button5': (w + off + 135, h - 80),
        'box1': (w + off , y), 'boxsize': (500, 600), 'font': ('Avenir Next', 12)},

        'ipad_landscape': {
        'button1': (w + off + 70, h), 'button2': (w + off + 210, h), 'button3': (w + off + 300, h),
        'button4': (w + off + 210, h - 50), 'button5': (w + off + 70, h - 50),
        'box1': (w + 10 , y), 'boxsize': (500, 600), 'font': ('Avenir Next', 12)},
        
        'ipad_mini_landscape': {
        'button1': (w + off + 70, h), 'button2': (w + off + 210, h), 'button3': (w + off + 300, h),
        'button4': (w + off + 210, h - 50), 'button5': (w + off + 70, h - 50),
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
        x, y, w, h = self.gui.grid.bbox
        off = 100
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

        self.randomise_button = self.gui.add_button(text='Randomise',
                                                    position=self.posn.button4,
                                                    fill_color='red',
                                                    **{
                                                        **params, 'min_size':
                                                        (80, 32)
                                                    })
        self.gui.add_button(text='Reload',
                            position=self.posn.button5,
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })

        self.wordsbox = self.gui.add_button(
            text='',
            title='Clues',
            position=self.posn.box1,
            min_size=self.posn.boxsize,
            font=('Courier New', 14),
            fill_color='black',
        )
        
    def update_buttons(self, color='white'):
        """ change button text and reset colours """
        coords = [coord for word in self.wordset.values() for coord in word.coords]
        #coords = np.argwhere(np.char.isalpha(self.board))
        # fill all squares
        self.gui.add_numbers([
            Squares(coord,
                    '',
                    color,
                    z_position=30,
                    alpha=.2,
                    stroke_color='black',
                    font=('Marker Felt', 15),
                    text_anchor_point=(-0.9, 0.95))
            for coord in coords],
            clear_previous=True)

    def fill_board(self):
        """use  swordsmith to fill crossword
      if it fails, then it can be run ahain from control 
      """

        def transfer_props(props):
            return {k: getattr(self, k) for k in props}

        cx = CrossWord(self.gui, self.word_locations, self.all_words)
        cx.set_props(**transfer_props(
            ['board', 'empty_board', 'all_word_dict', 'max_depth', 'debug']))
        cx.max_cycles = 5000
        try:
            wait = self.gui.set_waiting('Generating')
            for i in range(10):
                self.board = cx.populate_words_graph(max_iterations=100,
                                                     length_first=False,
                                                     max_possibles=100,
                                                     swordsmith_strategy='dfs')
                if not '.' in self.board:
                   self.wordset = self.get_words(self.across_only)      
                   break                        
        except (Exception):
            print(traceback.format_exc())
        finally:
            self.gui.reset_waiting(wait)

    def select_list(self):
        '''Choose which category'''
        items = [s.capitalize() for s in self.word_dict.keys()]
        items = [
            item.split('_')[0] for item in items if item.endswith('_frame')
        ]
        # return selection
        self.gui.selection = ''
        selection = ''
        prompt = 'Select grid'
        while self.gui.selection == '':
            self.gui.input_text_list(prompt=prompt,
                                     items=items,
                                     position=(800, 0))
            while self.gui.text_box.on_screen:
                try:
                    selection = self.gui.selection.lower()
                except (Exception) as e:
                    print(e)
            if selection == 'cancelled_':
                selection = choice(items).lower()
            if len(selection):
                if self.debug:
                    print(f'{selection=}')
                # self.wordlist = self.word_dict[selection]

                if selection + '_text' in self.word_dict:
                    self.table = self.word_dict[selection + '_text']
                    self.image = self.wordlist[0]
                    self.image_dims = [
                        int(st) for st in self.wordlist[1].split(',')
                    ]
                    self.solution = self.wordlist[2]
                    if len(self.solution) < 70:
                        self.debug = True

                if selection.capitalize() + '_frame' in self.word_dict:
                    # rearrange frame text into N 3x3 tiles
                    frame = self.word_dict[selection.capitalize() + '_frame']
                    if self.debug:
                        [print(row, len(row)) for row in frame]  # for debug
                    assert all([len(row) == len(frame[0])
                                for row in frame]), 'Error in string lengths'
                    # convert to numpy
                    frame = np.array(
                        [np.array(row.lower(), dtype=str) for row in frame])
                    frame = np.char.replace(frame, "'", '')
                    frame = np.char.replace(frame, '/', '')
                    frame = frame.view('U1').reshape(
                        (-1, self.image_dims[1] * TILESIZE))
                    # replace spaces and dot by hash for display
                    #frame[frame == ' '] = '#'
                    #frame[frame == '.'] = '#'
                    # divide into rows of 3
                    rowsplit = np.split(frame, self.image_dims[0], axis=0)
                    # divide each row into blocks of 3x3
                    colsplit = [
                        np.split(rowsplit[i], self.image_dims[1], axis=1)
                        for i in range(len(rowsplit))
                    ]
                    # add all together to get N 3x3 blocks
                    self.tiles = np.concatenate(colsplit)
                    self.board = frame
                    self.empty_board = frame.copy()

                #self.wordlist = [word for word in self.table if word]
                self.gui.selection = ''
                return selection
            elif selection == "Cancelled_":
                return False
            else:
                return False
                
    def update_clue_colours(self, word=None):
        # update colour of all words, else just one
        if word is None:
            wordlist = self.wordset
        else:
            wordlist = [word]
        for word in wordlist:
            word_obj = self.wordset[word]
            # change button colour to show if definition found
            color = 'blue' if self.word_defs[word]['def'] else 'red'
            if 'clue' in self.word_defs[word]:
                color = 'green'
            [self.change_color(coord, color) for coord in word_obj.coords]
        
        
    def get_size(self):
        LetterGame.get_size(self, '15, 21')

    def load_words(self, word_length, file_list=PUZZLELIST):
        return

    def initialise_board(self):
        pass

    def get_player_move(self, board=None):
        """Takes in the user's input which is only interacting with buttons,
    """
        move = LetterGame.get_player_move(self, self.board)[0]
        if self.debug:
            print(move)
        # deal with buttons. each returns the button text
        if move[0] < 0 and move[1] < 0:
            if self.debug:
                print(self.gui.gs.buttons[-move[0]].text)
            return (None, None), self.gui.gs.buttons[-move[0]].text, None
        # Coord is a tuple that can support arithmetic
        point = self.gui.gs.start_touch - gscene.GRID_POS
        try:
            rc_start = Coord(self.gui.gs.grid_to_rc(point))
            if self.check_in_board(rc_start):
                rc = Coord(move)
                return rc_start, None, rc
        except (KeyError):
             pass
        return (None, None), None, None

    def place_tile(self, coord, tile_index):
        r, c = coord
        self.board[r * TILESIZE:r * TILESIZE + TILESIZE, c *
                   TILESIZE:c * TILESIZE + TILESIZE] = self.tiles[tile_index]

    def update_clue_text(self):
        """ prepare block of clue text """
        # get unique line_no
        lines = sorted(set([word.start[0] + 1
                            for word in self.word_locations]))

        clues = []
        for line in lines:
            clue_text = f'{str(line):>2} '
            for word in self.word_defs.values():
                if word['line_no'] == line:
                    clue_text += f'{word.get("clue", "")} • '
            # remove last dotand
            clue_text = clue_text[:-3]
            clue_list = wrap(clue_text,
                             width=40,
                             initial_indent='',
                             subsequent_indent='   ',
                             replace_whitespace=False)
            clues.extend(clue_list)

        clue_text = CR.join(clues)
        return clue_text

    #@ui.in_background
    def select_definition(self, word):
        """ word button pressed.
      if word has definitions, open a list_dialog to select
      if not, open a text dialog to enter clue
      """
        clue = None
        self.gui.selection = ''
        selection = ''
        
        if self.word_defs[word]['def'] and 'clue' not in self.word_defs[word]:
            try:
                if self.debug:
                    print(word, self.word_defs[word])
                # flatten and append contents of word_defs
                flat_list = ['DEFINITIONS']
                flat_list.extend(self.word_defs[word]['def'])
                
                #for i, item in enumerate(flat_list):
                #  flat_list[i] = fill(item, width = 20)
                flat_list.extend(['SYNONYMS'])
                flat_list.extend(
                    [x for xs in self.word_defs[word]['synonyms'] for x in xs])
                if self.debug: print(flat_list)
                while self.gui.selection == '':
                    self.gui.input_text_list(
                        prompt=f'Select definition for {word}',
                        items=flat_list,
                        width=600,
                        position=(800, 0))
                    while self.gui.text_box.on_screen:
                        try:
                            selection = self.gui.selection.lower()
                        except (Exception) as e:
                            print(e)
                        if selection == 'cancelled_':
                            return False
                        if selection in ['definitions', 'synonyms']:
                            return False
                        if len(selection):
                            if self.debug:
                                print(f'{selection=}')
                        sleep(0.2)

                clue = selection

            except Exception as e:
                print(e)
        else:
            clue = dialogs.text_dialog(f'Enter clue for {word}',
                                       text=self.word_defs[word].get(
                                           'clue', ''))
        if clue is not None and clue != '':
            self.word_defs[word]['clue'] = clue
        # colour squares green                                  
        if 'clue' in self.word_defs[word]:
            [self.change_color(coord, 'green')
                for coord in self.wordset[word].coords
            ]
        
        self.check_all_clues()
        self.save_state()

    def check_all_clues(self):
        # check if all clues complete
        self.all_clues_done = all(
            [v.get('clue', '') != '' for v in self.word_defs.values()])
        if self.all_clues_done:
            self.gui.set_props(self.randomise_button, fill_color='orange')

    def randomise_grid(self):
        """ shuffle the tiles """
        rowsplit = np.split(self.solution_board, self.image_dims[0], axis=0)
        # divide each row into blocks of 3x3
        colsplit = [
            np.split(rowsplit[i], self.image_dims[1], axis=1)
            for i in range(len(rowsplit))
        ]
        # add all together to get N 3x3 blocks
        self.tiles = np.concatenate(colsplit)
        # shuffle the indexes 0-34
        indexes = list(range(0, math.prod(self.image_dims)))
        origin = indexes.copy()
        shuffle(indexes)

        index_dict = dict(zip(origin, indexes))
        inv_dict = {v: k for k, v in index_dict.items()}
        sol_list = [inv_dict[i] for i in origin]
        self.soln_str = ''.join([str(index).zfill(2) for index in indexes])
        self.soln_str1 = ''.join([str(index).zfill(2) for index in sol_list])

        # now place shuffled tiles
        for i, index in enumerate(sol_list):
            coord = divmod(i, self.image_dims[1])
            self.place_tile(coord, index)
        self.gui.update(self.board)

    def compute_puzzle_text(self, name='puzzle'):
        """produce all text """
        all_text = CR.join([
            f'{name}:',
            '""',
            '7, 5',
            self.soln_str,
            '',
            f'{name}_text:',
            self.update_clue_text(),
            '',
            f'{name}_frame:',
            CR.join([''.join(row) for row in self.board]).replace('#',
                                                                  ' ').upper(),
        ])
        return all_text
        
    def process_turn(self, move, board):
        """ process the turn
    move is coord, new letter, selection_row
    """
        if move:
            coord, letter, origin = move

            if letter == 'Fill':
                # new solution and buttons
                self.fill_board()
                self.solution_board = self.board.copy()
                self.gui.update(self.board)
                self.update_buttons(self.INIT_COLOR)
            elif letter == 'Lookup':
                self.word_defs = {}
                t = time()
                self.lookup_all()
                self.gui.set_prompt(
                    f'lookup complete in {(time()-t):.3f} secs')
            elif letter == 'Copy':
                self.copy_()
                self.gui.set_message('Data copied')
            elif letter == 'Randomise':
                if self.all_clues_done:
                    self.randomise_grid()
            elif letter == 'Reload':
                self.recall_state()

            elif move and hasattr(self, 'word_defs'):
                coord, letter, origin = move
                for word_obj in self.wordset.values():
                    if coord in word_obj.coords:
                        self.select_definition(word_obj.word)
                        msg = self.update_clue_text()
                        try:
                            self.gui.set_text(self.wordsbox, msg)
                        except AttributeError:
                            self.gui.set_moves(msg)
                        return
        return 0
        
    def copy_(self, out=None, final_cr=True):
        if out is None:
            out = self.outputfile
        base, next_number = self.last_puzzle_name(out)        
        name = dialogs.text_dialog('Enter name for puzzle',
                                           text=f'{base}{next_number}')
        msg = self.compute_puzzle_text(name)
        self.clipboard_set(msg)
        if final_cr:
           msg = '\n' + msg + '\n' 
        else:
            msg = '\n' + msg
        with open(out, 'a', encoding='utf-8') as f:
            f.write(msg)
        self.check_clipboard()
        
                
    def reveal(self):
        """ place all tiles in their correct location """
        for n in range(self.span * self.sizey // TILESIZE):
            val = int(self.solution[n * 2:n * 2 + 2])
            coord = Coord(divmod(n, self.span))
            self.place_tile(coord, val)
            self.rack[coord] = val
            self.gui.update(self.board)

        sleep(2)
        self.game_over()
        self.gui.gs.show_start_menu()

    def game_over(self):
        # compare placement with solution
        state = ''
        for r in range(self.sizey // TILESIZE):
            for c in range(self.span):
                if self.tiles is None:
                    no = f'{self.rack[(r, c)].number:02d}'
                else:
                    no = f'{self.rack[(r, c)]:02d}'
                state += no
        if self.debug:
            print(state)
        if state == self.solution:
            self.gui.set_message('Game over')
            return True
        return False

    def restart(self):
        self.gui.gs.close()
        PieceWord().run()


if __name__ == '__main__':
    g = PieceWord()
    g.run()
    while (True):
        quit = g.wait()
        if quit:
            break









