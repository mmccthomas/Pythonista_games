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
     button will turn green
  4. press each pink button and try to enter a suitable clue - be creative!
  5. pressing green button again allows editing of clue
  6. press Randomise to shuffle tiles. this can be repeated as necessary.
  7. press Copy and puzzle name or number, e.g. puzzle18
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
import base_path

base_path.add_paths(__file__)
from Letter_game import LetterGame
import gui.gui_scene as gscene
from gui.gui_interface import Coord, BoxedLabel
from crossword_create import CrossWord


PUZZLELIST = "pieceword_templates.txt"
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
        with open('piecestate.pkl', 'wb') as f:
            pickle.dump([
                self.empty_board, self.board, self.solution_board,
                self.word_defs, self.word_locations, self.selection
            ], f)

    def recall_state(self):
        with open('piecestate.pkl', 'rb') as f:
            self.empty_board, self.board, self.solution_board, self.word_defs, self.word_locations, selection = pickle.load(
                f)
        if selection != self.selection:
            console.hud_alert(
                f'Template does not match, select {selection} first')
            return
        # now update gui elements
        self.gui.update(self.board)
        self.update_buttons()
        self.gui.set_text(self.wordsbox, self.update_clue_text())
        for i, word in enumerate(self.get_words().values()):
            button = 'button_' + str(i + 2)
            color = 'lightblue' if 'def' in self.word_defs[word] else 'pink'
            if 'clue' in self.word_defs[word]:
                color = 'lightgreen'
            self.gui.set_props(button, fill_color=color)
        self.check_all_clues()

    def get_words(self):
        word_dict = {}
        for loc in self.word_locations:
            if loc.direction == 'across':
                word_dict[loc.start] = loc.word
        return word_dict

    def lookup_all(self):
        wait = self.gui.set_waiting('Looking up words')
        missing_words = []
        for i, word in enumerate(self.wordset):
            # self.gui.set_prompt(f'looking up {word}')
            wait.name = f'Finding {word}'
            # lookup using free dictionary,merriam_webster if fail
            self.word_defs[word] = {'def': [], 'synonyms': []}
            self.lookup(word, self.lookup_free)
            no_defs = len(self.word_defs[word]['def'])
            self.lookup(word, not self.lookup_free)       
            if self.word_defs[word]['def'] and no_defs == 0:
                  missing_words.append(word)
               
            # change button colour to show if definition found
            button = 'button_' + str(i + 2)
            self.gui.set_props(
                button,
                fill_color='lightblue' if self.word_defs[word]['def'] else 'pink')
            self.word_defs[word]['line_no'] = list(
                self.get_words().keys())[i][0] + 1
        self.gui.reset_waiting(wait)
        if missing_words:
           dialogs.hud_alert(f'Found {missing_words} in 2nd dictionary', duration=4)

        if self.debug:
            for word in self.wordset:
                print()
                print(word, self.word_defs[word])
                
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
        self.wordset = self.get_words().values()
        self.set_buttons()
        while True:
            move = self.get_player_move(self.board)
            move = self.process_turn(move, self.board)
            #if self.game_over():
            #  break
        self.gui.set_message2('')
        self.complete()

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
        # Make x position be relative to previous box on same line
        # need bbox of previous box
        bbox = [0, 0, 0, 0]
        for k, v in self.get_words().items():
            pos = int(w + 20), int(h - (k[0] + 1) * h / 21)
            if pos[1] == bbox[1]:
                pos = bbox[0] + bbox[2] + 10, bbox[1]
            button = self.gui.add_button(text=v,
                                         position=pos,
                                         fill_color='yellow',
                                         **{
                                             **params, 'min_size': (65, h/21 - 2)
                                         })
            # get bbox of just placed button as integers to allow comparison
            bbox = [
                int(x) for x in getattr(self.gui.gs, button).l_box_name.bbox
            ]
        self.gui.set_enter('Fill',
                           position=(w + off + 135, h),
                           fill_color='orange',
                           **params)
        self.gui.add_button(text='Lookup',
                            position=(w + off + 275, h),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })
        self.gui.add_button(text='Copy',
                            position=(w + off + 365, h),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })

        self.randomise_button = self.gui.add_button(text='Randomise',
                                                    position=(w + off + 275,
                                                              h - 80),
                                                    fill_color='red',
                                                    **{
                                                        **params, 'min_size':
                                                        (80, 32)
                                                    })
        self.gui.add_button(text='Reload',
                            position=(w + off + 135, h - 80),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })

        self.wordsbox = self.gui.add_button(
            text='',
            title='Clues',
            position=(w + off + 150, y+50),
            min_size=(250, 300),
            font=('Courier New', 14),
            fill_color='black',
        )

    def update_buttons(self):
        """ change button text and reset colours """
        
        for i, word in enumerate(self.wordset):
            button = 'button_' + str(i + 2)
            self.gui.set_text(button, word)
            self.gui.set_props(button, fill_color='yellow')

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
            self.board = cx.populate_words_graph(max_iterations=100,
                                                 length_first=False,
                                                 max_possibles=100,
                                                 swordsmith_strategy='dfs')
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
        # find button
        for k, button in self.gui.gs.buttons.items():
            if button.text == word:
                button_str = 'button_' + str(k)
                break
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
            if self.debug: print(self.word_defs[word]['clue'])
            try:
               self.gui.set_props(button_str, fill_color='lightgreen')
            except Exception as e:
               pass
        else:
            self.word_defs[word].pop('clue', None)
            try:
               self.gui.set_props(
                button_str,
                fill_color='lightblue' if self.word_defs[word] else 'pink')
            except Exception as e:
               pass
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
        @on_main_thread
        def clipboard_set(msg):
            '''clipboard seems to need @on_main_thread '''
            clipboard.set(msg) 
             
        @on_main_thread
        def clipboard_get():
            return  clipboard.get()              
            
        def check_clipboard():
            data = clipboard_get()
            if data == '':
                print('clipboard fail')
            else:
                print('clipboard', data)        
        
        if move:
            coord, letter, origin = move

            if letter == 'Fill':
                # new solution and buttons
                self.fill_board()
                self.solution_board = self.board.copy()
                self.gui.update(self.board)
                self.update_buttons()
            elif letter == 'Lookup':
                self.word_defs = {}
                t = time()
                self.lookup_all()
                self.gui.set_prompt(
                    f'lookup complete in {(time()-t):.3f} secs')
            elif letter == 'Copy':
                name = dialogs.text_dialog('Enter name for puzzle',
                                           text='puzzle')
                msg = self.compute_puzzle_text(name)
                clipboard_set(msg)
                check_clipboard()
                self.gui.set_message('Data copied')
            elif letter == 'Randomise':
                if self.all_clues_done:
                    self.randomise_grid()
            elif letter == 'Reload':
                self.recall_state()
            elif letter in list(self.wordset) and hasattr(self, 'word_defs'):
                self.select_definition(letter)
                msg = self.update_clue_text()
                self.gui.set_text(self.wordsbox, msg)
        return 0

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








