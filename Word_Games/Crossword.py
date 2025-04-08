# Crossword game
#
# file for each puzzle has 2sections , puzzleno_text, and puzzleno_frame

from time import sleep
import dialogs
import numpy as np
import random
from itertools import groupby
from scene import get_screen_size
from Letter_game import LetterGame
import gui.gui_scene as gscene
from gui.gui_interface import Coord, Squares

PUZZLELIST = "crossword_puzzles.txt"


class CrossWord(LetterGame):

    def __init__(self, test=None):
        LetterGame.__init__(self, column_labels_one_based=True)
        self.first_letter = False
        self.tiles = None
        self.debug = False
        self.test = test
        self.load_words_from_file(PUZZLELIST, no_strip=True)
        self.selection = self.select_list(self.test)
        if self.selection is False:
            self.gui.gs.show_start_menu()
            return

        self.images = None

        x, y, w, h = self.gui.grid.bbox

        self.gui.set_pause_menu({
            'Continue': self.gui.dismiss_menu,
            'New ....': self.restart,
            'Reveal': self.reveal,
            'Quit': self.quit
        })
        self.gui.clear_messages()
        self.gui.set_top(
            f'Crossword no {self.selection.capitalize()} {self.sizex}x{self.sizey}'
        )
        self.set_buttons()
        self.finished = False

    def set_buttons(self):
        """ install set of active buttons
        Note: **{**params,'min_size': (80, 32)} overrides parameter
         """
        W, H = get_screen_size()
        x, y, w, h = self.gui.grid.bbox
        off = 50
        params = {
            'title': '',
            'stroke_color': 'black',
            'font': ('Avenir Next', 18),
            'reg_touch': True,
            'color': 'black',
            'min_size': (80, 32)
        }
        self.gui.set_enter('Check',
                           position=(w + 20, h),
                           fill_color='orange',
                           **params)

        self.gui.add_button(text='Hint',
                            position=(w + off + 120, h),
                            fill_color='orange',
                            **{
                                **params, 'min_size': (80, 32)
                            })

        # adjust text size to screen
        fontsize = (W - w) // 28
        self.gui.set_moves('\n'.join(self.table),
                           font=('Ubuntu Mono', fontsize),
                           position=(w + 10, y),
                           anchor_point=(0, 0))

    def run(self):
        """
    Main method that prompts the user for input
    """
        while True:
            move = self.get_player_move(self.board)
            move = self.process_turn(move, self.board)
            if self.game_over():
                break
        self.gui.set_message2('')
        self.complete()

    def decode_filled_board(self):
        """ take a number filled board, and display it"""
        self.decode_and_display_filled_board()
        self.solution_board = self.board.copy()
        self.board[np.char.isalpha(self.board)] = ' '
        self.empty_board = self.board.copy()
        return

    def decode_and_display_filled_board(self):
        """ take a number filled board, display
        format is '#/#/3/4/5b/' etc"""

        def split_text(s):
            for k, g in groupby(s, str.isalpha):
                yield ''.join(g)

        self.board = np.array(self.board)
        self.board[self.board == '-'] = ' '
        # deal with number/alpha combo
        # selects 1a, not b or #
        number_letters = np.argwhere(
            np.char.isalnum(self.board) & ~np.char.isalpha(self.board))
        self.number_board = np.zeros(self.board.shape, dtype=int)

        for number in number_letters:
            try:
                no, letter = list(split_text(self.board[tuple(number)]))
                self.board[tuple(number)] = letter
            except (ValueError):
                no = self.board[tuple(number)]
            self.number_board[tuple(number)] = int(no)
        self.board[np.char.isnumeric(self.board)] = ' '

        return self.board, self.number_board

    def print_squares(self):
        numbers = np.argwhere(self.number_board != 0)
        square_list = [
            Squares(tuple(rc),
                    str(self.number_board[tuple(rc)]),
                    'white',
                    z_position=30,
                    alpha=0.1,
                    stroke_color='black',
                    font=('Marker Felt', 15),
                    text_color='red',
                    text_anchor_point=(-0.9, 0.95)) for rc in numbers
        ]
        self.gui.add_numbers(square_list, clear_previous=True)

    def select_list(self, test, select=None):
        '''Choose which category'''
        items = [s.capitalize() for s in self.word_dict]
        items = [item.removesuffix('_text') for item in items if (item.endswith('_text'))]
        # get board size for items 
        boards = {name: board for name, board in self.word_dict.items() if name.endswith('_frame')}       
        items = [item + ' ' + item_size for item, item_size in zip(items, self.get_frame_sizes(boards))]
        # return selection
        self.gui.selection = ''
        selection = ''
        prompt = ' Select puzzle'
        if not test:
            while self.gui.selection == '':
                self.gui.input_text_list(prompt=prompt,
                                         items=items,
                                         position=(800, 0))
                while self.gui.text_box.on_screen:
                    try:
                        # remove frame size string
                        selection = self.gui.selection.lower().split(' ')[0]
                    except (Exception) as e:
                        print(e)
                if selection == 'cancelled_':
                    return False
                if len(selection):
                    if self.debug:
                        print(f'{selection=}')
        else:
            selection = select if select else items[0]

        if selection + '_text' in self.word_dict:
            self.table = self.word_dict[selection + '_text']

        if selection + '_frame' in self.word_dict:
            
            frame = self.word_dict[selection + '_frame']
            if self.debug:
                [print(row, len(row)) for row in frame]  # for debug

            # convert to numpy
            board = [row.replace("'", "") for row in frame]
            board = [row.split('/') for row in board]
            self.board = np.array(board)
            self.decode_filled_board()
            self.gui.remove_labels()
            self.gui.replace_grid(*self.board.shape)
            self.gui.remove_labels()
            self.sizey, self.sizex = self.board.shape
            self.gui.build_extra_grid(*self.board.shape,
                                      grid_width_x=1,
                                      grid_width_y=1,
                                      color='black',
                                      line_width=1)
            self.gui.build_extra_grid(1,
                                      1,
                                      grid_width_x=self.board.shape[0],
                                      grid_width_y=self.board.shape[1],
                                      color='red',
                                      line_width=4)
            self.print_squares()
            self.length_matrix()
            self.gui.update(self.board)
            self.gui.selection = ''
            return selection
        elif selection == "Cancelled_":
            return False
        else:
            return False

    def get_size(self):
        LetterGame.get_size(self, '15, 15')

    def load_words(self, word_length, file_list=PUZZLELIST):
        return

    def initialise_board(self):
        pass

    def get_player_move(self, board=None):
        """Takes in the user's input and performs that move on the board,
    returns the coordinates of the move
    Allows for movement over board"""

        move = LetterGame.get_player_move(self, self.board)

        if move[0] == (-1, -1):
            return (None, None), 'Enter', None  # pressed enter button
        # deal with buttons. each returns the button text
        if move[0][0] < 0 and move[0][1] < 0:
            return (None, None), self.gui.gs.buttons[-move[0][0]].text, None
        point = self.gui.gs.start_touch - gscene.GRID_POS
        # touch on board
        # Coord is a tuple that can support arithmetic
        try:
            rc_start = Coord(self.gui.gs.grid_to_rc(point))

            if self.check_in_board(rc_start):
                rc = Coord(move[-2])
                return rc, None, rc_start
        except (KeyError):
            pass

        return (None, None), None, None

    def process_turn(self, move, board):
        """ process the turn
    move is coord, new letter, selection_row
    """
        if move:
            coord, letter, origin = move

            # self.gui.set_message(f'{origin}>{coord}={letter}')

            if letter == 'Enter':
                # show all incorrect squares
                self.gui.set_prompt('Incorrect squares marked orange')
                self.update_board(hint=True)
                # now turn off marked squares
                sleep(2)
                self.update_board(hint=False)
                self.gui.update(self.board)
                self.print_squares()

                return False
            elif letter == 'Finish':
                return 0
            elif letter == 'Hint':
                # show a random unplaced word
                while True:
                    index = random.randint(0, len(self.word_locations) - 1)
                    word = self.word_locations[index]
                    if not word.fixed:
                        [
                            self.board_rc(coord, self.board,
                                          self.solution_board[coord])
                            for coord in word.coords
                        ]
                        word.fixed = True
                        self.gui.update(self.board)
                        break

            elif letter is None:
                # guess word
                for word_obj in self.word_locations:
                    if coord in word_obj.coords:
                        word_guess = dialogs.input_alert(
                            f'Enter word ({word_obj.length} letters)')
                        if len(word_guess) == word_obj.length:
                            word_obj.word = word_guess

                            [self.board_rc(coord, self.board, val)
                             for coord, val in zip(
                                word_obj.coords, word_guess)
                            ]
                            # mark word as fixed if correct
                            word_obj.fixed = all([
                                self.board[tuple(coord)] == self.solution_board[tuple(coord)]
                                for coord in word_obj.coords
                            ])

                        else:
                            dialogs.hud_alert('Wrong length')
                        self.gui.update(self.board)
                        return

    def update_board(self, hint=False):
        incorrect = np.argwhere(
            np.char.isalpha(self.board) & (self.board != self.solution_board))
        self.gui.clear_numbers()
        if hint:
            self.gui.add_numbers([
                Squares(coord,
                        '',
                        'orange',
                        z_position=30,
                        alpha=0.5,
                        stroke_color='white') for coord in incorrect
            ])
        else:
            [self.board_rc(coord, self.board, ' ') for coord in incorrect]

    def get_tile_no(self, n):
        for t in self.gui.gs.get_tiles():
            if t.number == n:
                return t

    def reveal(self):
        """ place all tiles in their correct location """
        self.board = self.solution_board
        self.gui.update(self.board)
        self.complete()

    def game_over(self):
        if np.array_equal(self.board, self.solution_board):
            return True

    def restart(self):
        self.gui.gs.close()
        CrossWord().run()


if __name__ == '__main__':
    g = CrossWord()
    g.run()
    while (True):
        quit = g.wait()
        if quit:
            break

