import os
import sys
from queue import Queue

import Dots_Boxes.DotAndBoxGame as dg
from Dots_Boxes.DotAndBoxGame import game
try:
    from change_screensize import get_screen_size
except ImportError:
    from scene import get_screen_size
from scene import Point
from collections import Counter
from time import sleep
import numpy as np
sys.path.append('../')
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
"""
This file is the GUI on top of the game backend.
modified for ios using Pythonista by CMT using my gui framework
"""
BOARDSIZE = 15


class Player():

    def __init__(self):
        self.PLAYER_1 = WHITE = 'O'
        self.PLAYER_2 = BLACK = '0'
        self.EMPTY = ' '
        self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
        self.PIECES = ['emj:White_Circle', 'emj:Black_Circle']
        self.PIECE_NAMES = {'0': 'Black', 'O': 'White'}


class DotAndBox():

    def __init__(self):
        """Create, initialize and draw an empty board."""
        self.display_board = [[' ' for c in range(BOARDSIZE)]
                              for r in range(BOARDSIZE)]
        self.empty_board = self.display_board.copy()
        self.board = None
        self.gui = Gui(self.display_board, Player())
        self.gui.q = Queue()
        self.gui.set_alpha(False)
        self.gui.set_grid_colors(grid='lightgrey',
                                 highlight='lightblue',
                                 z_position=5,
                                 grid_stroke_color='lightgrey')
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)

        self.gui.setup_gui(log_moves=False, grid_fill='lightgrey')
        # menus can be controlled by dictionary of labels and functions without parameters
        #self.gui.pause_menu = {'Continue': self.gui.dismiss_menu,  'Save': save,
        #                 'Load': load,  'Quit': self.gui.close}
        self.gui.start_menu = {
            'New Game': self.restart,
            'Quit': self.gui.close
        }
        self.size = (BOARDSIZE + 1) // 2
        self.gameplay = game('Human', "alphabeta", self.size, self.size)
        self.db = dg.dotsboxes(self.size, self.size)
        self.initialize()

    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # Apply marker dots to board
        self.gui.clear_messages()
        self.square_list = []
        # place dots
        ix = 0
        for i in range(0, BOARDSIZE, 2):
            for j in range(0, BOARDSIZE, 2):
                self.square_list.append(
                    Squares((i, j),
                            ix,
                            'black',
                            text_color='white',
                            z_position=5,
                            stroke_color='clear',
                            alpha=1,
                            radius=5,
                            sqsize=15,
                            offset=(0.5, -0.5),
                            font=('Avenir', 15),
                            anchor_point=(0.5, 0.5)))
                ix += 1
        self.gui.add_numbers(self.square_list)

        self.sq = self.gui.SQ_SIZE // 2
        self.boxes = []

    def wait_for_gui(self):
        # loop until dat received over queue
        while True:
            # if view gets closed, quit the program
            if not self.gui.v.on_screen:
                print('View closed, exiting')
                sys.exit()
                break
            #  wait on queue data, either rc selected or function to call
            sleep(0.01)
            if not self.gui.q.empty():
                data = self.gui.q.get(block=False)
                if isinstance(data, (tuple, list, int)):
                    coord = data
                    break
                else:
                    try:
                        #print(f' trying to run {data}')
                        data()
                    except (Exception) as e:
                        print(traceback.format_exc())
                        print(f'Error in received data {data}  is {e}')
        return coord

    def human_move(self):
        while True:
            coord = self.wait_for_gui()
            return coord

    def computer_move(self):
        nos = self.gameplay.player_b.make_play(self.db)
        return nos

    def convert_move(self, move):
        row, col = move
        if col % 2 == 0 and row % 2 == 1:
            #vertical
            start_number = (row - 1) // 2 * self.size + col // 2
            end_number = (row + 1) // 2 * self.size + col // 2
        elif row % 2 == 0:
            #horizontal
            start_number = row // 2 * self.size + (col - 1) // 2
            end_number = row // 2 * self.size + (col + 1) // 2
        else:
            start_number, end_number = None, None
        return [start_number, end_number]

    def convert_numbers(self, numbers):
        # convert tuple of numbers back to row, col
        start, end = numbers
        c1, r1 = start % self.size, int(start // self.size)
        c2, r2 = end % self.size, int(end // self.size)
        r = r2 + r1
        c = c2 + c1
        return r, c

    def draw_lines(self, move, color):
        # draw line and count lines around each box
        row, col = move
        xy = self.gui.rc_to_pos(move)
        # if col is even, it is a vertical line
        if col % 2 == 0 and row % 2 == 1:
            # vertical
            self.gui.draw_line(
                [xy - (-self.sq, self.sq), xy + (self.sq, 3 * self.sq)],
                stroke_color=color,
                line_width=5)
        elif row % 2 == 0 and col % 2 == 1:
            # horizontal
            self.gui.draw_line(
                [xy - (self.sq, -self.sq), xy + (3 * self.sq, self.sq)],
                stroke_color=color,
                line_width=5)
        else:
            pass  # dont draw the line

    def validate(self, move):
        # check that location is between lines
        start_point, end_point = self.convert_move(move)
        if start_point is None:
            return False
        if self.db.play_dict[(start_point, end_point)] == 1:
            return False
        else:
            return True
        row, col = move
        # if col is even, it is a vertical line
        if col % 2 == 0 and row % 2 == 1:
            # vertical
            return True
        elif row % 2 == 0 and col % 2 == 1:
            # horizontal
            return True
        else:
            return False

    def fill_box(self, color):
        boxes = {k: v for k, v in self.db.score_dict.items() if v != 0}
        for k, v in boxes.items():
            moves = [self.convert_numbers(loc) for loc in k]
            # find centre of lines
            box_loc = tuple(np.mean(np.array(moves), axis=0, dtype=int))
            if box_loc in self.boxes:
                continue
            else:
                # fill box
                self.gui.add_numbers([
                    Squares(box_loc,
                            '',
                            color,
                            z_position=30,
                            sqsize=4 * self.sq,
                            anchor_point=(0.5, 0.5),
                            offset=(0.5, -0.5),
                            alpha=.5)
                ],
                                     clear_previous=False)
                self.boxes.append(box_loc)
                return True
        return False

    def process_move(self, move, color='red'):
        # process human  selection
        self.draw_lines(move, color)
        move_nos = self.convert_move(move)
        if move_nos[0] is not None:
            valid = self.gameplay.player_a.make_play(self.db, move_nos)
            if not valid:
                self.gui.set_prompt(f'{move_nos} = {move} is not valid')
        return self.fill_box(color)

    def game_over(self):
        self.gui.set_message('')
        self.gui.set_message2('')
        self.gui.set_prompt('')
        if self.db.a_score == self.db.b_score:
            self.gui.set_message("It's a tie!")
        elif self.db.a_score >= self.db.b_score:
            self.gui.set_message("A wins!")
        else:
            self.gui.set_message("B wins!")
        self.gui.show_start_menu()

    def restart(self):
        self.gui.close()
        self.__init__()
        self.run()

    def show_score(self):
        self.gui.set_moves(
            f'Player: {self.db.a_score}\nComputer: {self.db.b_score}')

    def run(self):
        while True:
            self.gui.set_top('Human move')
            additional_move = True
            while additional_move:
                move = self.human_move()
                if self.validate(move):
                    additional_move = self.process_move(move, 'red')
                    self.show_score()
                    if self.db.isover():
                        self.game_over()
                        break
                    self.gui.set_message(
                        f'You played {self.convert_move(move)} = {move} ')

            self.gui.set_top('Computer move')
            additional_move = True
            while additional_move:
                nos = self.computer_move()
                if self.db.isover():
                    self.game_over()
                    break
                else:
                    move = self.convert_numbers(nos)
                    self.draw_lines(move, 'blue')
                    additional_move = self.fill_box('blue')
                    self.show_score()
                    self.gui.set_message2(f'ai plays {nos} = {move}')


def main():
    game = DotAndBox()
    game.run()


if __name__ == '__main__':
    main()

