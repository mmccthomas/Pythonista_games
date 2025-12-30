# A set of utilities to read a puzzle image from the photo library
#  Read blocks of text
#  create crossword grid manually
#  Read a crossword gridwith letters only
#  Read Pieceword grid with groups of 3x3 squares
#  Read numerical crossword grid

# Use VisionKit text recognition to read an image
# containing text.
# Provide a grid to generate crossword frame as text
#cthomas
# Oct 2024
import photos
import objc_util
import os
import sys
import clipboard
from objc_util import on_main_thread
import dialogs
import console
import traceback
from time import time
from queue import Queue
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import resource
from scene import Rect

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from types import SimpleNamespace
from gui.gui_interface import Gui, Coord, Squares
from Word_Games.Letter_game import LetterGame
from ui import LINE_CAP_ROUND
from scene import *
import gui.gui_scene as gs
import numpy as np
from PIL import Image
from io import BytesIO
from  recognise import Recognise
# import testgrid
from time import sleep
from setup_logging import logger, is_debug_level
savefile= 'Ocr_save'
tmp_directory = '///private/var/mobile/Containers/Data/Application/BF0000C4-73CE-4920-B411-8C8662899F1B/tmp'
MSG = ('','')


class Player():
    def __init__(self):
        self.PLAYER_1 = ' '
        self.PLAYER_2 = '@'
        self.EMPTY = ' '
        self.PIECE_NAMES  ='abcdefghijklmnopqrstuvwxyz0123456789. '
        self.PIECES = [f'../../gui/tileblocks/{k}.png' for k in self.PIECE_NAMES[:-2]]
        self.PIECES.append(f'../../gui/tileblocks/@.png')
        self.PIECES.append(f'../../gui/tileblocks/_.png')

        self.PLAYERS = None


class OcrCrossword(LetterGame):
    def __init__(self, all_text, board=None, board_size=None, asset=None, autoload=False):
        self.board = board
        self.load(autoload=autoload) # attempt to load temp file
        self.SIZE = self.get_size(board=self.board, board_size=board_size)
        self.asset = asset
        self.log_moves = False
        self.gui = Gui(self.board, Player())
        self.gui.set_grid_colors(grid='black') # background is classic board
        self.gui.q = Queue()
        self.words = []
        self.letters_mode = False
        self.direction_mode = False
        self.index_mode = False
        self.image_mode = False
        self.defined_area = None
        self.gui.require_touch_move(False)
        self.gui.allow_any_move(True)
        self.gui.setup_gui()
        self.board = np.array(self.board)
        self.board[self.board == '-'] = ' ' # replace '-' by ' '
        self.gui.build_extra_grid(self.sizex, self.sizey,
                                  grid_width_x=1, grid_width_y=1,
                                  color='black', line_width=1)
        self.all_text = all_text
        self.x, self.y, self.w, self.h = self.gui.grid.bbox
        self.gui.update(self.board)
        self.gui.clear_messages()
        self.box_positions()
        self.set_buttons()
        self.add_boxes()
        self.add_indexes()
        self.create_grid(self.board)
        self.recognise = Recognise(self.gui)


    def get_size(self, board, board_size):
        """ get board size
        if loaded board, board is an np array
        board_size is a default 25x25
        for Lettergame.set_size()
          if board_size is specified use it
          else if self.board is specified, use that
          else prompt for size
        """
        if board is not None:
            response = dialogs.alert('Use previously decoded board?', '', 'YES', 'NO', hide_cancel_button=True)
            if response == 1:
                try:
                    self.board = np.char.lower(board)
                    super().get_size()
                    return
                except (Exception) as e:
                    print(e)
            else:
                self.board = None

        super().get_size(board_size)

    def draw_rectangles(self, rectangles, **kwargs):
        W, H = self.sizex, self.sizey

        if isinstance(rectangles, pd.DataFrame):
            rectangles = list(rectangles[['x','y','w','h']].itertuples(index=False, name=None))
        elif rectangles is None:
            return
        for rect in rectangles:
            x, y, w, h = rect
            x1, y1 = x+w, y+h
            box = [self.gui.rc_to_pos((H-y*H-1, x*W)),
                   self.gui.rc_to_pos((H-y1*H-1, x*W)),
                   self.gui.rc_to_pos((H-y1*H-1, x1*W)),
                   self.gui.rc_to_pos((H-y*H-1, x1*W)),
                   self.gui.rc_to_pos((H-y*H-1, x*W))]
            self.gui.draw_line(box, **kwargs)

    def add_indexes(self):
        if hasattr(self, 'indexes'):
            indexes = np.argwhere(self.indexes !=0)
            squares_list = []
            for index in indexes:
                i = self.indexes[tuple(index)]
                squares_list.append(Squares(index, str(i), 'yellow', z_position=30,
                                                alpha=0.5, font=('Avenir Next', 18),
                                                text_anchor_point=(-1.0, 1.0)))
            self.gui.add_numbers(squares_list)
        else:
            self.indexes = np.zeros(self.board.shape, dtype=int)

    def box_positions(self):
        # positions of all objects for all devices
        x, y, w, h = self.gui.grid.bbox
        W, H = self.gui.get_device_screen_size()
        spc = self.gui.gs.spacing
        if H > W:
            raise KeyError('Portrait mode  or iphone not supported')
        else:
            position_dict = {'rackscale': 0.9, 
                             'gridbox': (6*spc*w, 5*spc*h),
                             'wordsbox': (18*spc*w, 10*spc*h),
                             'button1': (w+spc*w, 0),
                             'button2': (w+spc*w, h/21), 
                             'button3': (w+6*spc*w, h/21),
                             'button4': (w+spc*w, 3 *h/21), 
                             'button5': (w+6*spc*w, 3*h/21),
                             'button6': (w+spc*w, 4 *h/21), 
                             'button7': (w+6*spc*w, 0), 
                             'button8': (w+spc*w, 5*h/21),
                             'button9': (w+6*spc*w, 5*h/21),   
                             'button10': (w+10*spc*w, 5*h/21), 
                             'button11': (w+10*spc*w, 4*h/21),
                             'button12': (w+10*spc*w, 3*h/21),   
                             'button13': (w+10*spc*w, 2*h/21),  
                             'button14': (w+10*spc*w, 1*h/21),
                             'button15': (w+10*spc*w, 0),
                      
                             'box2': (w+spc*w, 6*h/21),  
                             'box3': (w+3*spc*w, 0), # top
                             'font': ('Avenir Next', 0.75*self.gui.get_fontsize())}        
        
        self.posn = SimpleNamespace(**position_dict)
        
    def add_boxes(self):
        global MSG
        """ add non responsive decoration boxes"""
        x, y, w, h = self.gui.grid.bbox
        tsize = self.posn.rackscale * self.gui.SQ_SIZE
        fontsize = self.gui.get_fontsize() /2
        #self.wordsbox = self.gui.add_button(text='', title='Words',
        #                    position=self.posn.box1,
        #                    min_size=(5 * tsize+10, tsize+10),
        #                    fill_color='black')
        #self.gui.set_props(self.wordsbox, font=('Courier New', 12))
        self.gridbox = self.gui.add_button(text='', title='Grid',
                            position=self.posn.box2,
                            min_size=self.posn.gridbox, #min_size=(2* tsize+10, tsize+10),
                            fill_color='black')
        self.gui.set_props(self.gridbox, font=('Courier New', fontsize))
        self.wordsbox = self.gui.scroll_text_box(x=self.posn.box3[0],
                                                 y=self.posn.box3[1],
                                                 width=self.posn.wordsbox[0], height=self.posn.wordsbox[1],
                                                 font=('Courier New', fontsize))
         
        msg = self.format_cols(MSG[0], columns=4, width=12)
        self.wordsbox.text=msg

    def set_buttons(self):
        """ install set of active buttons
        Note: **{**params,'min_size': (80, 32)} overrides parameter
         """
        x, y, w, h = self.gui.grid.bbox
        fontsize = self.gui.get_fontsize()
        params = {'title': '', 'stroke_color': 'black', 'font': self.posn.font, 'reg_touch': True, 'color': 'black', 'min_size': (2*fontsize, fontsize)}
        self.gui.set_enter('Quit', position=self.posn.button7,
                           fill_color='pink', **params)
        self.gui.add_button(text='Fill bottom', position=self.posn.button2,
                            fill_color='yellow', **{**params})
        self.gui.add_button(text='Fill right', position=self.posn.button3,
                            fill_color='yellow', **params)
        self.gui.add_button(text='Copy Text', position=self.posn.button4,
                            fill_color='orange', **{**params})
        self.gui.add_button(text='Copy grid', position=self.posn.button5,
                            fill_color='orange', **{**params})
        self.gui.add_button(text='Copy both', position=self.posn.button6,
                            fill_color='orange', **{**params,'min_size': (4*fontsize, fontsize)})
        self.gui.add_button(text='Clear', position=self.posn.button1,
                            fill_color='pink', **params)
        self.letters = self.gui.add_button(text='Add letters', position=self.posn.button8,
                                           fill_color='cyan', **params)
        self.direction = self.gui.add_button(text='Across', position=self.posn.button9,
                                             fill_color='cyan', **params)
        self.multi_character = self.gui.add_button(text='Indexes', position=self.posn.button10,
                                                   fill_color='cyan', **params)
        self.images = self.gui.add_button(text='Image Mode', position=self.posn.button11,
                                          fill_color='cyan', **params)
        self.gui.add_button(text='Recognise Text', position=self.posn.button12,
                            fill_color='cyan', **params)
        self.gui.add_button(text='Recognise Pieceword', position=self.posn.button13,
                            fill_color='cyan', **params)
        self.gui.add_button(text='Recognise Crossword', position=self.posn.button14,
                            fill_color='cyan', **params)
        self.gui.add_button(text='Recognise NumberGrid', position=self.posn.button15,
                            fill_color='cyan', **params)

    def create_grid(self, board):
        """ create string representation of board
            slashes separate each character
            check shape if board and indexes as board can resize
        """
        r_board_shape, c_board_shape = board.shape
        r_index_shape, c_index_shape = self.indexes.shape
        if r_index_shape < r_board_shape or c_index_shape < c_board_shape :
            new_indexes = np.zeros((board.shape), dtype=int)
            new_indexes[:r_index_shape, :c_index_shape] = self.indexes
            self.indexes = new_indexes

        self.lines = []
        use_indexes =  np.any(self.indexes)
        for r in range(board.shape[0]):
            line = "'"
            for c in range(board.shape[1]):
                if use_indexes:

                    i = self.indexes[r, c]
                char = board[r][c]
                if use_indexes:
                    if i != 0 and char != ' ':
                        item = str(i) + char
                    elif i != 0:
                        item = str(i)
                    else:
                        item = char
                else:
                    item = char
                line = line + item + '/'

            line = line[:-1] + "'\n"
            self.lines.append(line)

        # remove last \n
        self.lines[-1] = self.lines[-1].rstrip()
        fontsize = 24 if self.gui.device == 'ipad13_landscape' else 18
        grid_font = fontsize * 13/len(self.lines)
        self.gui.set_props(self.gridbox, font=('Courier New', grid_font))
        self.gui.set_text(self.gridbox, ''.join(self.lines))

    def select_defined_area(self, origin, coord):
        """select defined area"""
        def r2(x):
            """ round and scale"""
            return round(x, 2)/self.sizex

        st_y, st_x = origin # / self.sizex
        #st_y = 1.0 - st_y
        end_y, end_x = coord # / self.sizex
        # find which way we drew the box
        x, y = min(st_x, end_x), max(st_y, end_y)
        x1, y1 = max(st_x, end_x), min(st_y, end_y)

        box = [self.gui.rc_to_pos(y, x),
               self.gui.rc_to_pos(y1-1, x),
               self.gui.rc_to_pos(y1-1, x1+1),
               self.gui.rc_to_pos(y, x1+1),
               self.gui.rc_to_pos(y, x)]
        params = {'line_width': 4, 'line_cap_style': LINE_CAP_ROUND,
                  'stroke_color': 'blue', 'z_position':1000}
        self.gui.remove_lines(z_position=1000)
        self.gui.draw_line(box, **params)
        # calculate region of interest
        # need x, y relative to original asset
        # 0,0 is lower left, 1,1 is upper right
        x, y = r2(x), r2(self.sizey - 1 - y)
        x1, y1 = r2(x1+1), r2(self.sizey - y1)
        w = abs(x1-x)
        h = abs(y-y1)
        self.defined_area = (x, y, w, h)

    def get_player_move(self, board=None):
        """Takes in the user's input and performs that move on the board,
        returns the coordinates of the move
        Allows for movement over board"""

        move = LetterGame.get_player_move(self, self.board)

        # deal with buttons. each returns the button text
        if move[0] < 0 and move[1] < 0:
            return (None, None), self.gui.buttons[-move[0]].text, None

        point = self.gui.start_touch - self.gui.grid_pos
        # touch on board
        # Coord is a tuple that can support arithmetic
        rc_start = Coord(self.gui.grid_to_rc(point))

        if self.check_in_board(rc_start):
            rc = Coord(move)
            return rc, self.get_board_rc(rc, self.board), rc_start

        return (None, None), None, None

    def change_letters(self, coord, origin):
            # letters mode
        try:
            letter = dialogs.input_alert('Enter 1 or more letters')
        except (KeyboardInterrupt):
            return
        if letter:
            if self.index_mode and letter.isnumeric():
                self.indexes[origin] = int(letter)
                if letter == '0':
                    self.gui.clear_numbers(origin)
                else:
                    self.gui.replace_numbers([Squares(origin, str(letter), 'yellow', z_position=30,
                                                       alpha=0.5, font=('Avenir Next', 18),
                                                       text_anchor_point=(-1.0, 1.0))])
            else:
                for index, l in enumerate(letter):
                    #.       down.                                 across
                    delta = (index, 0) if self.direction_mode else (0, index)
                    self.board_rc(origin + delta, self.board, l.lower())


    def process_turn(self, move, board):
        """ process the turn
        move is coord, new letter, selection_row
        """
        @on_main_thread
        def clipboard_set(msg):
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
            match letter:
                case 'Quit':
                    self.gui.close()
                    #sys.exit()
                    return 0

                case 'Clear':
                    self.board = np.full((self.sizey, self.sizex), ' ')
                    self.create_grid(self.board)
                    self.gui.update(self.board)

                case 'Copy Text':
                    clipboard_set('Puzzle:\n' + '\n'.join(self.words))
                    check_clipboard()
                    self.gui.set_message('Data copied')

                case 'Fill bottom':
                    self.board[np.fliplr(np.flipud(self.board.copy()))=='#'] = '#'
                    self.gui.update(self.board)
                    self.create_grid(self.board)

                case 'Fill right':
                    self.board[np.fliplr(self.board.copy())=='#'] = '#'
                    self.gui.update(self.board)
                    self.create_grid(self.board)

                case 'Copy grid':
                    if self.image_mode:
                        dialogs.hud_alert('Exit image mode first')
                        return
                    text = self.gui.get_text(self.gridbox)
                    #text = None

                    if text:
                        clipboard_set('Puzzle_frame:\n' + text)
                    else:
                        self.create_grid(self.board)
                        clipboard_set('Puzzle_frame:\n' + ''.join(self.lines))

                    check_clipboard()
                    self.gui.set_message('Data copied')

                case 'Copy both':
                    if self.image_mode:
                        dialogs.hud_alert('Exit image mode first')
                        return
                    text = self.gui.get_text(self.gridbox)
                    if text:
                        clipboard_set( 'Puzzle:\n' + '\n'.join(self.words) + '\nPuzzle_frame:\n' + text)
                    else:
                        self.create_grid(self.board)
                        msg = 'Puzzle:\n' + '\n'.join(self.words) + '\nPuzzle_frame:\n' + ''.join(self.lines)
                        clipboard_set(msg)
                    check_clipboard()
                    self.gui.set_message('Data copied')

                case 'Across' | 'Down':
                    self.direction_mode = not self.direction_mode
                    self.gui.set_text(self.direction, 'Down' if self.direction_mode else 'Across')
                    self.gui.set_props(self.direction, fill_color='lightblue' if self.direction_mode else 'cyan')

                case 'Indexes':
                    self.index_mode = not self.index_mode
                    self.gui.set_props(self.multi_character, fill_color='lightblue' if self.index_mode else 'cyan')

                case 'Add letters':
                    self.letters_mode = not self.letters_mode
                    self.gui.set_props(self.letters, fill_color = 'red' if self.letters_mode else 'cyan')
                    if self.image_mode:
                        self.enter_image_mode()

                case 'Image Mode':
                    self.image_mode = not self.image_mode
                    self.gui.set_props(self.images, fill_color = 'red' if self.image_mode else 'cyan')
                    self.enter_image_mode()

                case 'Recognise Text':
                    if self.image_mode:
                        text_sort = console.alert('Text format', 'Select text format',
                                     'No format (pieceword)', 'Sorted length and alpha', 
                                     'Sorted alpha', hide_cancel_button=True)
                        self.recognise_area(rc=False, text_sort=text_sort)

                case 'Recognise Pieceword':
                    if self.image_mode:
                        self.recognise_crossword(pieceword=True)

                case  'Recognise Crossword':
                    if self.image_mode:
                        self.recognise_crossword(pieceword=False, allow_numbers=False)

                case 'Recognise NumberGrid':
                    if self.image_mode:
                        df = self.recognise_area()
                        self.board, shape, conf_board, self.indexes =  self.recognise.fill_board(df, min_confidence=0.5)
                        self.create_grid(self.board)
                        # make blocks black
                        self.board[self.indexes==0] = '#'
                        #self.recognise_crossword(pieceword=False, allow_numbers=True)

                case '':
                    pass

                case _:  # valid selection
                    # if single touch (origin=coord) then overrides image mode
                    # to allow boxes to be updated while image on screen
                    try:
                        if self.image_mode and (origin != coord):
                            self.select_defined_area(origin, coord)
                            return

                        cell = self.get_board_rc(origin, self.board)
                        if not self.letters_mode:
                            # toggle square colour
                            self.board_rc(origin, self.board, '#' if cell == ' ' else ' ')
                        else:
                            self.change_letters(coord, origin)

                        self.create_grid(self.board)
                        self.gui.update(np.char.lower(self.board))
                    except (IndexError):
                        pass

    def save(self):

        np.savez(savefile, board=self.board, indexes=self.indexes, words=self.words)

    def load(self, autoload=False):
        if autoload:
            response = 1
        else:
            response = dialogs.alert('Load temporary file?', '', 'YES', 'NO', hide_cancel_button=True)

        if response == 1:
            try:
                data = np.load(savefile + '.npz')
                self.board = data['board']
                self.indexes = data['indexes']
                self.words = data['words']

            except (Exception) as e:
                print(e)

    def run(self):
        self.create_grid(self.board)
        if MSG[0] != '':
            self.words = MSG[0]
        if hasattr(self, 'rectangles'):
            self.draw_rectangles()
        #if not self.image_mode:
        self.gui.update(np.char.lower(self.board))
        while True:
            move = self.get_player_move()
            end = self.process_turn(move, self.board)
            self.save()
            if end == 0:
                break

    def filter(self, sort_alpha=True, max_length=None, min_length=None, sort_length=True, remove_numbers=False, reverse=True):
        """ filter all detected text and sort according to length
        """

        words = self.all_text
        if max_length:
            words = [word for word in words if len(word) < max_length]
        if min_length:
            words = [word for word in words if len(word) > min_length]
        if remove_numbers:
            self.all_text = [word for word in words if word.isalpha()]

        # sort by length then by alphabet
        if sort_alpha:
            words.sort() # sorts normally by alphabetical order
        if sort_length:
            words.sort(key=len)
        if reverse:
            words.reverse()
        try:
            msg = self.format_cols(words, columns=4, width=12)
            #self.gui.set_text(self.wordsbox, msg)
            self.wordsbox.text=msg
        except:
            print(traceback.format_exc())
        self.words = words

    def enter_image_mode(self):
        global MSG
        if self.asset is not None:
            if self.image_mode:
                filename, self.scale, props = self.recognise.convert_to_png(self.asset)
                self.gui.set_message(f'{props}')
                self.gui.add_image(filename)
                self.rects, self.bboxes  = self.recognise.rectangles(self.asset)
                self.draw_rectangles(self.bboxes)
                self.board[self.board == ' '] = '-' # this ensures transparent grid
                self.gui.update(np.char.lower(self.board))
                all_text_dict = self.recognise.text_ocr(self.asset)
                try:
                        #board, board_size = recognise.sort_by_position(all_text_dict)
                    all_text = list(all_text_dict.values())
                except (AttributeError):
                    all_text = []
            else:
                # clear image and rectangles

                MSG = (self.words, self.lines, self.indexes)
                # force quit
                self.gui.q.put([-1,-1])

    def convert_text_to_dataframe(self, text_dict, existing_df=None):
        """ take text_dict with form [{label, confidence, cg_box}]
        to form Dataframe x, y, w, h, areax1000, c, r, confidence, label
        if existing_df then merge the dataframes
        need confidence and label from text_dict
        """
        df = pd.DataFrame(text_dict)
        df = np.round(df, 3)

        if existing_df is not None:
            #need to merge df into existing df
            # if multiple boxes in df with same aoi xy join them to
            # sort by y then x
            df.sort_values(by=['y', 'x'], ascending=True, inplace=True, ignore_index=True)
            # group same x,y values together.
            # concatenate label strings, average confidence
            df2 = df.groupby(['y', 'x'])[['label', 'confidence']].agg({'label':lambda x: ''.join(x), 'confidence': lambda x: np.mean(x)}).reset_index()
            # now merge this dataframe with rectangle dataframe to align x,y and r,c
            df3 = pd.merge(existing_df, df2,
                           how='outer', on=['y', 'x'],left_on=None, right_on=None,
                           left_index=False, right_index=False, sort=False)
            logger.debug(df3.to_string())
            # change NaN values to space for label, and 0 for confidence
            df3['confidence'] = df3['confidence'].fillna(0.0)
            df3['label'] = df3['label'].fillna(' ')
            return df3
        return df


    def recognise_area(self, defined_area=(0,0,1,1), rc=True, text_sort=None):
        '''recognise text in defined area'''
        if self.asset is None:
            return
        if self.defined_area is not None:
            defined_area =  self.defined_area
        all_text_dict = self.recognise.text_ocr(self.asset, defined_area)
        df = self.convert_text_to_dataframe(all_text_dict)
        df.sort_values(by=['y','x'], ascending=False, inplace=True, ignore_index=True)
        points = list(df[['x','y']].itertuples(index=False, name=None))

        # Group areas together to better order text
        #how to get best threshold?
        # This algorithm is empirical to group large and smaller areas
        threshold = 0.05 / min(defined_area[2], defined_area[3])
        cluster_count, labels = self.recognise.partition(points, threshold=threshold)

        df['group'] = np.array(labels)
        data = np.array(df[['x','y']])
        if is_debug_level():
            plt.close()
            x, y = data.T
            colorset = plt.cm.rainbow(np.linspace(0, 1, cluster_count))
            c = [colorset[col] for col in labels]
            plt.scatter(x,y, color=c )
            plt.show()
        df.sort_values(by=['group','y','x'], ascending=[True,False,True], inplace=True, ignore_index=True)
        if rc:
            # for number grids we need to obtain row and column for numbers
            # not needed for text
            df = self.recognise.normalise(df)
            #df = self.recognise.convert_to_rc(df)

            # These 2 lines work very well to fill number grid, but overwrites part of display
            #self.board, shape, conf_board, self.indexes =  self.recognise.fill_board(df, min_confidence=0.5)
            #self.create_grid(self.board)
            df = np.round(df, 2)
            df.sort_values(by=['r','c'], ascending=[True,True], inplace=True, ignore_index=True)
        logger.debug(df.to_string())
        try:
            self.all_text = list(df.label)
            self.draw_rectangles(df)
            if not rc:              
              match text_sort:
                case 1:
                  sort_alpha = False
                  sort_length = False
                case 2:
                  sort_alpha = True
                  sort_length = True
                case 3:
                  sort_alpha = True
                  sort_length = False
                case _:
                  sort_alpha = False
                  sort_length = False
            else:
            	  sort_alpha = False     
            	  sort_length = False  
            self.filter(sort_alpha=sort_alpha, max_length=None, min_length=None, sort_length=sort_length, remove_numbers=False, reverse=rc)
        except (AttributeError):
            self.gui.set_message(f'No text found in {self.defined_area}')
        return df

    def recognise_crossword(self, pieceword=False, allow_numbers=False):
        """ process crossword grid,
        either regular grid or pieceword
        pieceword is displayed as groups of 9 tiles
        if allow_numbers is True, use text_ocr instead of char_ocr """

        if self.defined_area:
            total_rects = pd.DataFrame(columns=('x', 'y', 'w', 'h'))
            #subdivide selected area and find rectangles
            if not pieceword:
                for subrect in self.split_defined_area(N=5):
                    df = self.find_rects_in_area(subrect)
                    if df is not None:
                        total_rects = pd.concat([total_rects, df], ignore_index=False)
            else:
                # find groups of pieces
                boxes = self.find_pieceword()
                if boxes is not None:
                    self.draw_rectangles(boxes)
                    print('no boxes', len(boxes))
                    sleep(.5)
                print(f'found {len(boxes)} boxes')
                total_rects = boxes

            self.draw_rectangles(total_rects)
            total_rects = self.filter_total(total_rects)
            self.gui.remove_lines()
            self.draw_rectangles(total_rects)
            print(f' Total rectangles {len(total_rects)}')
            total_rects =self.recognise.convert_to_rc(total_rects)
            df = self.add_missing(total_rects)
            total_rects = pd.concat([total_rects, df], ignore_index=False)
            total_rects.sort_values(by=['r','c','areax1000'], inplace=True, ignore_index=True)
            params = {'line_width': 5, 'stroke_color': 'green', 'z_position':1000}
            self.draw_rectangles(df, **params)
            self.gui.set_message2(f'Grid x={self.recognise.Nx}, y={self.recognise.Ny}, {len(total_rects)} squares found')
            logger.debug(total_rects.to_string())

            # at this point we have all the valid rectangles
            try:
                if is_debug_level():
                    data = np.array(total_rects[['x','y']])
                    #plt.close()
                    x, y = data.T
                    plt.scatter(x,y, color='green' )
                    plt.show()
                if allow_numbers:
                # text ocr allows numbers
                    all_text_dict = self.recognise.text_ocr(self.asset, total_rects)
                    total_rects = self.convert_text_to_dataframe(all_text_dict, total_rects)

                else:
                    total_rects = self.recognise.read_characters(self.asset, total_rects)
                self.board, shape, conf_board, self.indexes =  self.recognise.fill_board(total_rects, min_confidence=0.5)

                #board = '\n'.join(['/'.join(row) for row in np.flipud(self.board)])
                self.create_grid(self.board)
                #self.gui.set_text(self.gridbox, board)
                #self.lines = board
                self.wordsbox.text =  f'{np.flipud(conf_board)}'
                self.gui.set_message(f'OCR complete {len(np.where(conf_board>=5)[0])} items recognised')
                return self.board

            except ((ValueError,AttributeError))as e:
                self.gui.set_message(f'Text reading error  in {self.defined_area} {e}')

    def split_defined_area(self, N=5):
        # split defined area into N x N overlapping areas
        # d defines amount of overlap

        x, y, w, h = self.defined_area
        d = w / (N + 4) # overlap
        subrects = []
        for i in range(N * N):
            div, mod = divmod(i, N)
            subrects.append((x + mod * (w / N) - d * (mod != 0),
                             y + div * (h / N) - d * (div != 0),
                             w / N + d,
                             h / N + d))
        return subrects

    def find_pieceword(self):
        """ pieceword grids are arranged as 9x4 or 7x5  rectangles of 3x3 squares
        this gives grid size of 27, 12 or 21, 15
        try both arrangements to see which is used.
        First find the bounding rectangle to divide more accurately
        """
        if self.defined_area:
            aoi = self.defined_area
            rects, bboxes  = self.recognise.rectangles(self.asset, aoi, min_size=0.1)
            areas = np.array(rects)
            xmin, ymin = np.min(areas[:,0]), np.min(areas[:,1])
            xmax, ymax = np.max(areas[:,0] + areas[:,2]), np.max(areas[:,1] + areas[:,3])
            bounding_rect = (xmin, ymin, xmax-xmin, ymax-ymin)
            #self.draw_rectangles(bboxes)
            self.draw_rectangles([bounding_rect], line_width=10, stroke_color='cyan')
            #try to divide into rectangles
            # if most found boxes are same size, then use that arrangement
            bx, by, bw, bh = bounding_rect
            bound_area = bw * bh
            # these are printed grids
            for Y, X in [(9,4), (7,5)]:
                print(f'Trying {Y},{X}')
                subrects = [(bx + x * bw/X, by + y * bh/Y, bw/X, bh/Y) for x in range(X) for y in range(Y)]
                self.gui.remove_lines()
                df_all = pd.DataFrame(columns=('x', 'y', 'w', 'h', 'index', 'areax1000'))

                for index, aoi in enumerate(subrects):
                    rects, bboxes  = self.recognise.rectangles(self.asset, aoi, min_size=0.3, min_aspect=0.3)
                    #find biggest box. is it close to aoi?
                    if rects:
                        df = pd.DataFrame(np.array(rects), columns=('x', 'y', 'w', 'h'))
                        df['index']= index
                        df['areax1000'] = df.w * df.h * 1000
                        df_all = pd.concat([df_all, df], ignore_index=False)

                # find max of each column grouped by index
                df2 = df_all.groupby(['index']).max()
                max_area = np.array(df2.areax1000)
                print('Max area {max_area}')
                box_area = 1000 * bound_area / X / Y
                area_close_to_aoi = abs(max_area - box_area) < box_area / 4
                most_close = sum(area_close_to_aoi)/ X /Y
                if most_close > 0.8:  # allow some latitude
                    break
            print(f'Shape selected {Y},{X} score={most_close}')
            df_all = np.round(df_all, 4).reset_index(drop=True)
            # remove the large boxes
            df_all.drop(df_all[df_all.areax1000 > box_area/8].index, inplace=True)
            logger.debug(df_all.to_string())
            # now we know X and Y
            # we have subrects
            return df_all

    def find_rects_in_area(self, subrect , use_bboxes=False, min_size=0.08):
        """ find all rectangles in smaller area
        then filter those rectangles to remove outsize or undersize items
        returns pandas dataframe
        #TODO. this deletes some rectangles that it shouldn't. investigate
        """
        full = Rect(0.0, 0.0, 1.0, 1.0)
        if isinstance(subrect, pd.Series):
            aoi = tuple(subrect[['x','y','w','h']])
        else:
            aoi = subrect
        if not full.contains_rect(Rect(*aoi)):
            aoi = (0,0,1.0,1.0)
        rects, bboxes  = self.recognise.rectangles(self.asset, aoi, min_size=min_size)
        select = bboxes if use_bboxes else rects
        if select:
            df = pd.DataFrame(np.array(select), columns=('x', 'y', 'w', 'h'))
            df = np.round(df, decimals=3)
            df['areax1000']= np.round(df.w * df.h * 1000, 3)
            #print(len(df))
            df.sort_values(by=['y','x','areax1000'], inplace=True, ignore_index=True)
            df.drop_duplicates(['x', 'y'], keep='last', inplace=True, ignore_index=True)

            #get areas and aspect of each rectangle
            areas = np.round(df.areax1000, 1)
            aspects = np.round(df.h / df.w, 2)

            hist_area = np.histogram(areas, bins=10)
            #hist_aspect = np.histogram(aspects, bins=10)

            area_span = np.linspace(min(areas), max(areas), num=10)
            #area_span = np.unique(areas)
            d_area= np.digitize(areas, area_span, right=True)

            aspect_span = np.linspace(min(aspects), max(aspects), num=10)
            d_aspect = np.digitize(aspects, aspect_span, right=True)

            #find greatest number of items  in area
            if is_debug_level():
                    # TODO should we also use aspect?
                print('digitized', d_area)
                print('areas', areas)
                print('digitized', d_aspect)
                print('aspects', aspects)
            unique, counts = np.unique(d_area, return_counts=True)

            most = unique[np.argmax(counts)]
            self.draw_rectangles(df)
            filtered = df
            filtered = df[d_area[df.index] == most]
            logger.debug(f'unique, counts, {unique}, {counts}')
            logger.debug(f'filtered, {len(filtered)}')
            return filtered
        return None

    def filter_total(self, total_rects):
        """ total rects is pandas Dataframe
        add reduced resolution column for sorting and filtering
        remove them at the end
        TODO this does not filter very well"""
        total_rects[['xr', 'yr', 'wr', 'hr']] = np.round(total_rects[['x', 'y', 'w', 'h']], 2)

        total_rects['areax1000']= round(total_rects.wr * total_rects.hr * 1000, 3)
        print(len(total_rects))
        total_rects.sort_values(by=['yr','xr','areax1000'], inplace=True, ignore_index=True)
        total_rects.drop_duplicates(['xr', 'yr'], keep='last', inplace=True, ignore_index=True)
        area_span = np.linspace(total_rects.min(axis=0)['areax1000'], total_rects.max(axis=0)['areax1000'], num=10)
        d_area= np.digitize(np.array(total_rects.areax1000), area_span, right=True)
        unique, counts = np.unique(d_area, return_counts=True)
        most = unique[np.argmax(counts)]
        idx = d_area[np.array(total_rects.index)] == most
        #total_rects = total_rects[idx]
        total_rects = total_rects.drop(['xr', 'yr', 'wr', 'hr'], axis='columns')
        total_rects.reset_index(drop=True, inplace=True)
        return total_rects


    def add_missing(self, total_rects):
        """ find which rc coordinates are not in total_rects, add them in"""
        #fill a board of computed size with logic True
        Ny, Nx = self.recognise.Ny, self.recognise.Nx
        board = np.full((Ny, Nx), True)
        #fill board with logic False if r,c in totsl_rects
        locs = np.array(total_rects[['r', 'c']])
        #print(total_rects.to_string())
        [self.board_rc(tuple(loc), board, False) for loc in locs]
        # missing is  what's left
        missing = np.argwhere(board==True)
        # make a new datafram from missing r,c
        missing_df = pd.DataFrame(missing, columns=['r', 'c'])
        w, h = tuple(total_rects.mean(axis=0)[['w', 'h']])
        assert ( np.max(missing_df.c) < Nx)
        assert ( np.max(missing_df.r) < Ny)
        # fill x, y, w, h and size columns

        missing_df['x'] = np.array([self.recognise.xs[c] for c in missing_df.c])
        missing_df['y'] = np.array([self.recognise.ys[r] for r in missing_df.r])
        missing_df['w'] = np.round(w, 3)
        missing_df['h'] = np.round(h, 3)
        missing_df['areax1000'] = np.round(w * h * 1000, 3)
        print(f'added {len(missing_df)} missing items')
        return missing_df


def main():

    all_assets = photos.get_assets()
    asset = photos.pick_asset(assets=all_assets)
    ocr = OcrCrossword([], asset=asset, board_size='25 25')
    ocr.defined_area =[0,0,1,1]
    df = ocr.recognise_area(rc=False)
    if df is not None:
        ocr.image_mode = not ocr.image_mode
        ocr.gui.set_props(ocr.images, fill_color = 'red' if ocr.image_mode else 'cyan')
        ocr.enter_image_mode()
    ocr.run()

    # if closed with MSG set then restart with new grid
    # if autoload then used previous data
    while MSG:
        ocr = OcrCrossword([], asset=asset, autoload=True)
        ocr.words = MSG[0]
        ocr.lines = MSG[1]
        ocr.indexes = MSG[2]
        ocr.run()

if __name__ == '__main__':
    main()



