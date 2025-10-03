
# this module is an interface layer to the lower level graphics below
# moved panel code (scroll_view, input_text_list etc) to new module
# to reduce complexity of this class
from scene import *
import ui
import sys
import time
import console
from queue import Queue
import numpy as np
try:
    from change_screensize import get_screen_size
except ImportError:
    from scene import get_screen_size
sys.path.append('../')

import gui.gui_scene as gscene
from gui.gui_scene import BoxedLabel
from gui.gui_panels import GuiPanel
import os

class Gui():
    # allow for non square board
    # use DIMENSION_X and DIMENSION_Y

    def __init__(self, board, player):

        self.v = SceneView()
        self.v.scene = gscene.GameBoard()
        self.wh = get_screen_size()
        self.v.present('sheet')
        self.gs = self.v.scene
        self.gs.board = [list(row) for row in board] # board.copy()
        self.gs.Player = player
        self.player = player
        self.gs.DIMENSION_Y = len(self.gs.board)
        self.gs.DIMENSION_X = len(self.gs.board[0])
        self.use_alpha = True
        self.q = None
        #self.selection = ''
        #self.selection_row = 0
        self.button_index = 2
        self.dismiss_menu = self.gs.dismiss_modal_scene
        self.device = self.gs.device
        #self.long_touch = self.gs.long_touch
        #try:
        #    self.number_panel = ui.load_view('Number_panel.pyui')
        #except FileNotFoundError:
        #    self.number_panel = None

        # menus can be controlled by dictionary of labels
        # and functions without parameters
        self.gs.pause_menu = {
            'Continue': self.gs.dismiss_modal_scene,
            'Quit': self.gs.close
        }
        self.gs.start_menu = {
            'New Game': self.gs.dismiss_modal_scene,
            'Quit': self.gs.close
        }
        # moved popup panels to gui_panels module
        # define functions to allow unchanged interface
        self.gui_panel = GuiPanel(self)
       
        self.scrollview_h = self.gui_panel.scrollview_h        
        self.scroll_text_box = self.gui_panel.scroll_text_box
        self.input_text_list = self.gui_panel.input_text_list
        self.input_numbers = self.gui_panel.input_numbers
        self.input_letters = self.gui_panel.input_letters
     
    @property   
    def selection(self):
        # get selection from gui_panel
        return self.gui_panel.selection
        
    @selection.setter    
    def selection(self, value):
        self.gui_panel.selection = value
        
    @property   
    def selection_row(self):
        # get selection row from gui_panel
        return self.gui_panel.selection_row
        
    @property   
    def text_box(self):
        # get text box from gui_panel
        return self.gui_panel.text_box                        
        
    @property   
    def letter_panel(self):
        # get letter_panel from gui_panel
        return self.gui_panel.letter_panel
        
    @property   
    def DIMENSION_X(self):
       return self.gs.DIMENSION_X
       
    @DIMENSION_X.setter
    def DIMENSION_X(self, value):
        self.gs.DIMENSION_X = value
        
    @property   
    def DIMENSION_Y(self):
       return self.gs.DIMENSION_Y
       
    @DIMENSION_Y.setter
    def DIMENSION_Y(self, value):
        self.gs.DIMENSION_Y = value

    @property   
    def q(self):
       return self.gs.q
       
    @q.setter
    def q(self, value):
        self.gs.q = value
        
    @property   
    def long_touch(self):
       return self.gs.long_touch
    
    def set_grid_colors(self,
                        grid=None,
                        highlight=None,
                        z_position=10,
                        grid_stroke_color=None):
        if grid is not None:
            # try:
            #    image = ui.Image.from_data(grid)
            #    self.gs.grid_fill = 'clear'
            #    self.gs.background_image = image
            # except (Exception) as e:
            try:
                image = ui.Image.named(grid)
                self.gs.grid_fill = 'clear'
                self.gs.background_image = image
            except (Exception) as e:
                print('error in set_grid_colors', e)
                if grid.startswith('#') or ui.parse_color(grid) != (0.0, 0.0,
                                                                    0.0, 0.0):
                    self.gs.grid_fill = grid
        self.gs.grid_stroke_color = grid_stroke_color
        self.gs.grid_z_position = z_position
        if highlight is not None:
            self.gs.highlight_fill = highlight

    def get_device(self):
        # returns string ipad_landscape, ipad_portrait,
        #                iphone_landscape, iphone_portrait
        return self.gs.device_size()
        
    def get_device_screen_size(self):
        return get_screen_size()
           
    def get_fontsize(self):
        return self.gs.get_fontsize()
        
    def setup_gui(self, **kwargs):
        self.gs.setup_gui(**kwargs)
        self.game_field = self.gs.game_field
        self.grid = self.gs.grid
        
    def orientation(self, fn):
        """ Passes a funtion to be called when device is rotated """ 
        self.gs.orientation = fn
        
    def replace_grid(self, dimx, dimy):
        """remove and replace grid with different of squares"""
        self.gs.DIMENSION_X, self.gs.DIMENSION_Y = dimx, dimy
        self.remove_labels()
        GRID_POS, self.gs.SQ_SIZE, self.gs.font_size = self.gs.grid_sizes(self.gs.device, dimx, dimy)
        self.grid.remove_from_parent()                        
        self.gs.grid = self.gs.build_background_grid()
        self.gs.game_field.add_child(self.gs.grid)
        self.game_field = self.gs.game_field
        self.grid = self.gs.grid
        
    def require_touch_move(self, require=True):
        self.gs.require_touch_move = require

    def allow_any_move(self, allow=False):
        self.gs.allow_any_square = allow

    def set_player(self, current_player, Player):
        self.gs.Player = Player()
        self.gs.current_player = current_player

    def set_alpha(self, mode=True):
        # allows for column numbers to be letters or numbers
        self.use_alpha = mode
        self.gs.use_alpha = mode

    def set_prompt(self, msg, **kwargs):
        # lowest level at bottom
        for k, v in kwargs.items():
            setattr(self.gs.msg_label_prompt, k, v)
        self.gs.msg_label_prompt.text = msg

    def set_message(self, msg, **kwargs):
        # message below box
        for k, v in kwargs.items():
            setattr(self.gs.msg_label_b, k, v)
        self.gs.msg_label_b.text = msg

    def get_message(self):
        return self.gs.msg_label_b.text

    def set_message2(self, msg, **kwargs):
        # message below box
        for k, v in kwargs.items():
            setattr(self.gs.msg_label_b2, k, v)
        self.gs.msg_label_b2.text = msg

    def get_message2(self):
        return self.gs.msg_label_b2.text

    def set_top(self, msg, **kwargs):
        # message above box
        for k, v in kwargs.items():
            setattr(self.gs.msg_label_t, k, v)
        self.gs.msg_label_t.text = msg
        
    def get_top(self):
        return self.gs.msg_label_t.text

    def set_moves(self, msg, **kwargs):
        # right box
        for k, v in kwargs.items():
            setattr(self.gs.msg_label_r, k, v)
        self.gs.msg_label_r.text = msg
        
    def get_moves(self):
        return self.gs.msg_label_r.text

    def set_enter(self, msg, **kwargs):
        # modify existing enter button BoxedLabel object
        self.gs.enter_button.set_props(**kwargs)
        self.gs.enter_button.set_text(msg)
        return self.gs.enter_button

    def set_props(self, button_str, **kwargs):
        # modify existing button BoxedLabel object
        b = getattr(self.gs, button_str)
        if 'anchor_point' in kwargs:
            print(f'anchor_point not supported for {button_str}')
            kwargs.pop('anchor_point')
        b.set_props(**kwargs)

    def set_text(self, button_str, msg, **kwargs):
        # modify existing enter button BoxedLabel object
        b = getattr(self.gs, button_str)
        b.set_props(**kwargs)
        b.set_text(msg)

    def get_text(self, button_str):
        # get  existing text  from BoxedLabel object
        b = getattr(self.gs, button_str)
        msg = b.get_text()
        return msg

    def add_button(self,
                   text='button',
                   title='title',
                   position=(100, 100),
                   min_size=(100, 50),
                   reg_touch=False,
                   **kwargs):
        # create a gui button that can invoke action if reg_touch is true
        box = BoxedLabel(text=text,
                         title=title,
                         position=position,
                         min_size=min_size,
                         parent=self.gs.game_field)
        box.set_index(self.button_index)
        button_name = f'button_{self.button_index}'
        setattr(self.gs, button_name, box)
        button = getattr(self.gs, button_name)
        if reg_touch:
            self.gs.buttons[self.button_index] = box
        if 'anchor_point' in kwargs:
            print(f'anchor_point not supported for {button_name}')
            kwargs.pop('anchor_point')
        button.set_props(**kwargs)
        self.button_index += 1
        return button_name

    def update(self, board=None, fn_piece=None):
        ''' if board, it is a single [row,col] '''
        self.gs.board =  [list(row) for row in board] # board.copy()
        self.gs.redraw_board(fn_piece=fn_piece)
        
    def subset(self, board, loc, N=3):
        # get a subset of board of max NxN, centred on loc
        # subset is computed with numpy slicing
        # to make it as fast as possible
        # max and min are used to clip subset close to edges
        r, c = loc
        subset = board[max(r - (N-2), 0):min(r + N-1, board.shape[0]),
                              max(c - 1, 0):min(c + 2, board.shape[1])] 
        return subset
    
    def number_locs(self, board):
        # return a list of numeric characters in np board
        locs = np.argwhere(np.char.isnumeric(board))
        return list(locs)
        
    def alpha_locs(self, board):
        # return a list of alpha characters in np board
        locs = np.argwhere(np.char.alpha(board))
        return list(locs)
      
    def add_numbers(self, items, clear_previous=True, **kwargs):
        # items are each an instance of Swuares object
        self.gs.add_numbers(items, clear_previous, **kwargs)

    def replace_numbers(self, items, **kwargs):
        # items are each an instance of Swuares object
        self.gs.replace_numbers(items, **kwargs)

    def get_numbers(self, coords):
        return self.gs.get_numbers(coords)

    def put_numbers(self, items, **kwargs):
        self.gs.put_numbers(items, **kwargs)

    def clear_numbers(self, number_list=None):
        # allow for clearing some highlighted squares
        try:
            self.gs.clear_numbers(number_list)
        except (AttributeError):
            pass

    def valid_moves(self, validmoves, message=True, alpha=1.0):
        """ add highlights to show valid moves """
        msg = [self.ident(move) for move in validmoves]
        if message:
            self.set_message2('valid:  ' + ', '.join(msg))
        self.gs.clear_highlights()
        self.gs.highlight_squares(validmoves, alpha=alpha)

    def get_board(self):
        return self.gs.board

    def changed(self, board):
        """ get gui copy of board
    iterate until a difference is seen
    return row, column of different cell
    """
        gui_board = self.get_board()
        for j, row in enumerate(board):
            for i, col in enumerate(row):
                if gui_board[j][i] != col:
                    return j, i
        return None

    def ident(self, changed):
        # change rc to ident A1 or 11
        if self.use_alpha:
            c = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z AAABACADAEAFAGAHAIAJAKALAMANAO'
        else:
            c = '1 2 3 4 5 6 7 8 9 10111213141516171819202122232425262728293031323334353637383940'
        r = '1 2 3 4 5 6 7 8 9 10111213141516171819202122232425262728293031323334353637383940'

        y = changed[0]
        x = changed[1]

        msg = c[2 * x:2 * x + 2] + r[2 * y:2 * y + 2]
        # msg = msg.replace(' ', '')
        return msg

    def wait_for_gui(self, board, return_rc=False):
        # loop until gui board is not same as local version
        while True:
            # if view gets closed, quit the program
            # self.dump_board(self.get_board(), 'gui')
            # self.dump_board(board, '')
            if not self.v.on_screen:
                print('View closed, exiting')
                sys.exit()
                break
            if self.get_board() != board:
                break
            time.sleep(0.5)

        coord = self.ident(self.changed(board))
        if return_rc:
            return self.changed(board)
        else:
            # print('changed' , self.changed(board), coord)
            return coord
            
    def get_move(self):
        # loop until dat received over queue
        while True:
          # if view gets closed, quit the program
          if not self.v.on_screen:
            print('View closed, exiting')
            sys.exit()
            break
          #  wait on queue data, either rc selected or function to call
          time.sleep(0.01)
          if not self.gs.q.empty():
            data = self.gs.q.get(block=False)
            
            # self.delta_t('get')
            # self.q.task_done()
            if isinstance(data, (tuple, list, int)):
              coord = data  # self.gui.ident(data)
              break
            else:
              try:
                # print(f' trying to run {data}')
                data()
              except (Exception) as e:
                print(traceback.format_exc())
                print(f'Error in received data {data}  is {e}')
        return coord
        
    def dump(self):
        tiles = [t.name for t in self.gs.get_tiles()]
        print('gui:', tiles)

    def dump_board(self, board, which=None):
        items = []
        for j, row in enumerate(board):
            for i, col in enumerate(row):
                cell = board[j][i]
                if cell != self.player.EMPTY:
                    items.append(f"{cell}{j}{i}")
        print('board:', which, items)

    def print_board(self, board, which=None, highlight=None):
        # optionally make chars underlined
        # unicode 0333 adds underline to any character
        # highlight is a list of r,c coordinates
        print('board:', which)
        for j, row in enumerate(board):
            for i, col in enumerate(row):
                if highlight and (j, i) in highlight:
                  print(str(board[j][i]) + '\u0333', end=' ')  
                else:
                   print(str(board[j][i]), end=' ')
            print()

    def input_message(self, message):
        response = console.input_alert(message)
        return response

    def clear_squares(self, squares_list=None):
        self.gs.clear_squares(squares_list)
        
    def clear_highlights(self):
        self.gs.clear_highlights()
        
    def clear_messages(self):
        self.set_message2('')
        self.set_message('')
        self.set_top('')
        self.set_prompt('')
        self.set_enter('')
        self.set_moves('')
        
    def close(self):
        self.gs.close()
        
    def show_start_menu(self, **kwargs):
        # pass start_menu call to gs_scene
        self.gs.show_start_menu(**kwargs)

    def set_pause_menu(self, menu_dict):
        self.gs.pause_menu = menu_dict

    def set_start_menu(self, menu_dict):
        self.gs.start_menu = menu_dict
        
    def build_extra_grid(self, *args, **kwargs):                         
        self.gs.build_extra_grid(*args, **kwargs)

    def draw_line(self, coords, **kwargs):
        self.gs.draw_line(coords, **kwargs)

    def remove_lines(self, z_position=1000):
        '''delete all lines based on z_position'''
        lines = [
            item for item in self.game_field.children
            if isinstance(item, ShapeNode) and item.z_position == z_position
        ]
        for line in lines:
            line.remove_from_parent()

    def rc_to_pos(self, coord):
        return self.gs.rc_to_pos(coord[0], coord[1])

    def remove_labels(self):
        """remove all labels
        TODO This is done by position, can we do better?"""
        labels = [
            label for label in self.game_field.children
            if isinstance(label, LabelNode)
        ]
        x, y, w, h = self.grid.bbox
        labels_ = [
                label for label in labels if x - 25 < label.position[0] < x
            ]
        labels_.extend([
                label for label in labels if h < label.position[1] < (h + 25) and label.position[0] < w
            ])

        for label in labels_:
            label.remove_from_parent()
            # label.text = ''
            
    def replace_labels(self,
                       which='row',
                       label_list=None,
                       colors=None,
                       **kwargs):
        """ replace row or column labels with custom set and colors
        TODO This is done by position, can we do better?"""
        labels = [
            label for label in self.game_field.children
            if isinstance(label, LabelNode)
        ]
        x, y, w, h = self.grid.bbox
        if which == 'row':
            labels = [
                label for label in labels if x - 25 < label.position[0] < x
            ]
        else:
            labels = [
                label for label in labels if h < label.position[1] < (h + 25)
            ]

        for label, listitem in zip(labels, label_list):
            label.text = str(listitem)
        if colors is not None:
            if isinstance(colors, (np.ndarray, list)):
                for label, color in zip(labels, colors):
                    label.color = color
            else:
                for label in labels:
                    label.color = colors
        for k, v in kwargs.items():
            for label in labels:
                setattr(label, k, v)

    def add_image(self, img, **kwargs):
        """ display an image on the grid. This is included so that the image
      can be diplayed after the gui and grid are initiated """

        background = SpriteNode(Texture(ui.Image.named(img)))
        background.size = (self.gs.SQ_SIZE * self.gs.DIMENSION_X,
                           self.gs.SQ_SIZE * self.gs.DIMENSION_Y)
        background.position = (0, 0)
        background.anchor_point = (0, 0)
        for k, v in kwargs.items():
            setattr(background, k, v)
        self.grid.add_child(background)

    def set_waiting(self, message='Processing'):
        a = ui.ActivityIndicator()
        a.style = ui.ACTIVITY_INDICATOR_STYLE_WHITE_LARGE
        a.hides_when_stopped = True
        a.frame = (100, 100, 200, 200)
        a.name = message
        a.background_color = 'red'
        a.start_animating()
        a.present('sheet', hide_close_button=True)
        return a

    def reset_waiting(self, object):
        object.stop()
        object.close()


class Board():
    """ class to hold numpy 2d array representation of board
    initial can be single element value or 2d array """

    def __init__(self, sizex=None, sizey=None, dtype='U1', initial=None):                    
            if initial:
                if isinstance(initial, list):
                    self.b = np.array(initial)
                    self.sizey, self.sizex = self.b.shape
                    self.dtype = self.b.dtype
                else:
                    self.b = np.full((sizey, sizex), initial)
            else:
                self.b = np.zeros((sizey, sizex), dtype=dtype)
                self.sizex = sizex
                self.sizey = sizey
                self.dtype = dtype

    def valid_entry(self, value):
        if self.dtype == int and type(value) == int:
            return True
        if self.b.dtype.kind == 'U':
            return len(value) == self.b.dtype.itemsize
        return False

    def get_rc(self, rc):
        return self.b[tuple(rc)]

    def set_rc(self, rc, value):
        if self.valid_entry(value):
            self.b[tuple(rc)] = value

    def copyboard(self):
        return self.b.copy()

    def inside(self, rc):
        """test if rc is within bounds of board """
        r, c = rc
        try:
            return (0 <= r < self.sizey) and (0 <= c < self.sizex)
        except (AttributeError):
            return (0 <= r < len(self.b)) and (0 <= c < len(self.b[0]))

    def getsize(self):
        return (self.sizey, self.sizex)
        
    def replace_board_section(self, coord, replacement):
          """replace a section of ndarray board with replacement ndarray
          """
          r, c = coord
          tile_y, tile_x = replacement.shape
          self.b[r * tile_y:r * tile_y + tile_y,
                 c * tile_x:c * tile_x + tile_x] = replacement


class Coord(tuple):
    """ a simple class to allow addition and slicing
    example: coord = Coord(rc)
             neighbours = coord.all_neighbours()
             scaled = coord * 3
    """

    def __init__(self, val=(0,0)):
        self.val = val
        self.r = self.val[0]
        self.c = self.val[1]
        self.row = self.r
        self.col = self.c
        self.all_dirs = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1),
                         (0, -1), (-1, -1)]
        self.compass_points = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        self.nsew_dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    def __repr__(self):
        return f'Coord({self.row}, {self.col})'

    def __add__(self, other):
        ''' implement + '''
        return Coord(tuple(p + q for p, q in zip(self.val, other)))

    def __sub__(self, other):
        ''' implement  - '''
        return Coord(tuple(p - q for p, q in zip(self.val, other)))

    def __mul__(self, scalar_int):
        ''' implement * '''
        return Coord(tuple(p * scalar_int for p in self.val))

    def __floordiv__(self, scalar_int):
        ''' implement // '''
        return Coord(tuple(p // scalar_int for p in self.val))

    def __truediv__(self, scalar):
        ''' implement // '''
        return Coord(tuple(p / scalar for p in self.val))

    def all_neighbours(self, sizex=None, sizey=None):
        """all directions if in board"""
        if sizex is None:
            return [Coord(self.__add__(d)) for d in self.all_dirs]
        else:
            return [
                Coord(self.__add__(d)) for d in self.all_dirs
                if self.in_board(Coord(self.__add__(d)), sizex, sizey)
            ]

    def nsew(self, sizex=None, sizey=None):
        """ up, down, left, right """
        if sizex is None:
            return [Coord(self.__add__(d)) for d in self.nsew_dirs]
        else:
            return [
                Coord(self.__add__(d)) for d in self.nsew_dirs
                if self.in_board(Coord(self.__add__(d)), sizex, sizey)
            ]

    def distance(self, other):
        """ x y distance of self from target """
        d = self - other
        return abs(d[0] + d[1])

    def in_board(self, coord, sizex, sizey):
        r, c = coord
        return (0 <= r < sizey) and (0 <= c < sizex)
        
    def clamp(self, sizex, sizey):
      col  = min(sizex-1, max(0, self.col)) # clamp c
      row  = min(sizey-1, max(0, self.row)) # clamp r
      return Coord(row, col)
      


class Squares():
    ''' holds parameters for coloured squares'''

    def __init__(self, position, text=' ', color='clear', **kwargs):

        self.position = position
        self.text = text
        self.color = color
        self.radius = 1
        self.z_position = 20
        self.alpha = .5
        self.text_anchor_point = (0.5, 0.5)

        self.offset = (0, 0)
        self.stroke_color = 'black'
        self.text_color = 'black'
        self.font_size = 24
        self.font = ('Avenir Next', self.font_size)

        for k, v in kwargs.items():
            setattr(self, k, v)


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__



