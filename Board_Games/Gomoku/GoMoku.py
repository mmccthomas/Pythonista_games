# Kyle Gerner
# Started 3.22.2021
# Gomoku solver, client facing
# CMT
# added gui and converted print statements to
# gui message calls
# inputs are mostly replaced by waiting for touch finishes.
# detect by mismatch in board contents
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from datetime import datetime
import time
from time import sleep
from queue import Queue
import console
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares
from gomoku_strategy import GomokuStrategy, opponentOf, performMove, copyOfBoard
from gomoku_player import GomokuPlayer

EMPTY, BLACK, WHITE = '.', 'X', 'O'

"""
This file is the GUI on top of the game backend.
modified for ios using Pythonista by CMT using my gui framework
"""
BACKGROUND = 'ramin.jpg'

def point_to_rc(point):
  #point is 1 based
  r, c = point[1] - 1, point[0] - 1
  return  r, c

def rc_to_point(rc):
  x, y = rc[0], rc[1]
  return x, y

def get_rbg(color):
    if color == 'WHITE':
        return 255, 255, 255
    elif color == 'BLACK':
        return 0, 0, 0
    else:
        return 0, 133, 211
            
class Player():
  def __init__(self):
    self.PLAYER_1 = WHITE = 'O'
    self.PLAYER_2 = BLACK = 'X'
    self.EMPTY = ' '
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:Black_Circle', 'emj:White_Circle']
    self.PIECE_NAMES = {'X': 'Black', 'O': 'White'}
    
class UI:
    def __init__(self):
        """Create, initialize and draw an empty board."""
        size = console.input_alert('Board size 11, 13, 15, 17, 19')
        if size is None:
          size = 19
        else:
          try:
            size = int(size)
          except:
            size = 19
        SIZE = size
        BOARD_DIMENSION = size + 1
        self.board_size = BOARD_DIMENSION
        self.display_board = [[' ' for c in range(SIZE)] for r in range(SIZE)]
        self.board = None        
        self.gui = Gui(self.display_board, Player())
        self.q = Queue()  
        self.gui.gs.q = self.q
        self.gui.set_alpha(True) 
        self.gui.set_grid_colors(grid=BACKGROUND, highlight='#ffc9b6', z_position=5, grid_stroke_color='clear')
        self.gui.require_touch_move(False)
        self.gui.gs.column_labels = '1 2 3 4 5 6 7 8 9 101112131415161718192021222324252627282930'
        self.gui.allow_any_move(True)
        self.gui.setup_gui(log_moves=False)
        self.gui.build_extra_grid(grids_x=SIZE-1, grids_y=SIZE-1, 
                                  grid_width_x=1, grid_width_y=1, color='black', 
                                  line_width=2, offset=(self.gui.gs.SQ_SIZE/2, self.gui.gs.SQ_SIZE/2), 
                                  z_position=5) 
        # menus can be controlled by dictionary of labels and functions without parameters
        # menus can be controlled by dictionary of labels and functions without parameters
        self.gui.gs.pause_menu = {'Continue': self.gui.gs.dismiss_modal_scene,
                                  'Complete': self.complete,
                                  'Quit': self.gui.gs.close}
        #self.gui.gs.start_menu = {'New Game': run, 'Quit': self.gui.gs.close} 
        self.game = None
      
                     
    def initialize(self):
        """This method should only be called once, when initializing the board."""
        # Apply marker dots to board
        self.gui.clear_messages()
        self.square_list =[]
        # 12 - 20
        match self.board_size:
          case 12:
              start, spacing = 1, 3
          case 14:
              start, spacing = 1, 4
          case 16:
              start, spacing = 2, 4
          case 18:
              start, spacing = 2, 5
          case 20:
              start, spacing = 2, 6
        for i in range(3):
            for j in range(3):
                self.square_list.append(Squares((start + (i*spacing), start+1 + (j*spacing)), '', 'black', 
                                                z_position=5, stroke_color='clear',alpha =1, 
                                                radius=5, sqsize=10, offset=(0.5,0.5), anchor_point=(0.5, 0.5)))     
        self.gui.add_numbers(self.square_list )   
        
    def complete(self):
        """ switch human player to computer play and complete game """
        opponentPiece = opponentOf(self.game.userPiece)
        self.game.players = {opponentPiece: GomokuStrategy(opponentPiece, self.game.board_dimension, self), 
                             self.game.userPiece: GomokuStrategy(self.game.userPiece, self.game.board_dimension, self)}  
        self.q.put((-1, -1))
      
    def draw(self, point, color, size=None):
        """ place color at point, need to convert to rc 
        """
        if size is None:
            # place tile
            r,c = point_to_rc(point)
            self.display_board[r][c] = '0' if color == 'BLACK' else 'O'
            self.gui.update(self.display_board)
        else:          
            color = get_rbg(color)
            if isinstance(point, list):
                points = [(point_to_rc(p)[0]-1, point_to_rc(p)[1]) for p in point]
                squares = [Squares((r, c), '', color, z_position=8, alpha=1,
                                   stroke_color='clear',  radius=5, sqsize=size, 
                                   offset = (0.5, 0.5), anchor_point=(0.5, 0.5)) 
                                   for r,c in points]
                self.gui.replace_numbers(squares)
            else:
                 r,c = point_to_rc(point)      
                 self.gui.replace_numbers([Squares((r, c), '', color, z_position=8, alpha=1,
                                           stroke_color='clear',  radius=5, sqsize=size, 
                                           offset = (0.5, 0.5), anchor_point=(0.5, 0.5))])    
            self.gui.set_moves(str(len(self.gui.gs.numbers)))     

    def remove(self, point):
        """ remove liberties at point """
        if isinstance(point, list):
            points = [(point_to_rc(p)[0]-1, point_to_rc(p)[1]) for p in point]
            self.gui.clear_numbers(points)
        else:
            r,c = point_to_rc(point)
            self.gui.clear_numbers([(r, c)])
        self.gui.set_moves(str(len(self.gui.gs.numbers)))
        
    def human_move(self):
        while True:
           coord = self.wait_for_gui()
           #rc  = (coord[:2], coord[2:]) 
           if coord == (-1, -1):
             return None, None
           return  coord
           
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
        if not self.q.empty():
          data = self.q.get(block=False)
          
          #self.delta_t('get')
          #self.q.task_done()
          if isinstance(data, (tuple, list, int)):
            coord = data # self.gui.ident(data)
            break
          else:
            try:
              #print(f' trying to run {data}')
              data()
            except (Exception) as e:
              print(traceback.format_exc())
              print(f'Error in received data {data}  is {e}')
      return coord
  
    def get_player_move(self, board=None):
      """Takes in the user's input and performs that move on the board, returns the coordinates of the move
      Allows for movement over board"""
      #self.delta_t('start get move')
      if board is None:
          board = self.game_board
      coord_list = []
      
      # sit here until piece place on board   
      items = 0
      
      while items < 1000: # stop lockup
        #self.gui.set_prompt(prompt, font=('Avenir Next', 25))
        
        move = self.wait_for_gui()
        if items == 0: st = time()
        #print('items',items, move)
        try:
          # spot = spot.strip().upper()
          # row = int(spot[1:]) - 1
          # col = self.COLUMN_LABELS.index(spot[0])
          if self.log_moves:
            coord_list.append(move)
            items += 1
            if move == -1:
              #self.delta_t('end get move')
              return coord_list       
          else:
            break
        except (Exception) as e:
          print(traceback.format_exc())
          print('except,', move, e)
          coord_list.append(move)
          return coord_list
      return move

        
# class for the Human player
class HumanPlayer(GomokuPlayer):

  def __init__(self, color, ui=None):
    super().__init__(color, isAI=False, ui=ui)
    self.gui=ui   

  def getMove(self, board):
    """Takes in the user's input and returns the move"""   
    # sit here until piece place on board        
    while True:
      spot = self.gui.human_move()
      if spot == (None, None):
        return spot      
      if board[spot[0]][spot[1]] != EMPTY:
        self.gui.gui.set_prompt(f"That spot is already taken, please choose another:\t")      
      else:
        break
    row, col = spot
    return row, col

class GomukuGame():
  
  def __init__(self, ui):
    self.ui = ui
    self.gameBoard = None
    self.userPiece = BLACK
    self.board_dimension = self.ui.board_size-1
    self.COLUMN_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    opponentPiece = opponentOf(self.userPiece)
    self.players = {opponentPiece: GomokuStrategy(opponentPiece, self.board_dimension, self.ui), 
                    self.userPiece: HumanPlayer(self.userPiece, self.ui)}   
  
  def createEmptyGameBoard(self, dimension):
    """Creates the gameBoard with the specified number of rows and columns"""
    return [[EMPTY for i in range(dimension)] for j in range(dimension)]
    
  def printGameBoard(self, highlightCoordinates=None):
      """Prints the gameBoard in a human-readable format"""
      """Transfers  gameBoard to gui
      if board is a single list just update that item"""
      self.ui.gui.update(self.gameBoard)
      if highlightCoordinates:
        self.ui.gui.gs.clear_highlights()
        self.ui.gui.valid_moves(highlightCoordinates)  
        
  def player_time(self, turn, start=True):
      if start:
          self.startTime = time.time()
      else:
          endTime = time.time()
          totalTimeTakenForMove = endTime - self.startTime
          self.time_player[turn][1] += totalTimeTakenForMove
          self.time_player[turn][2] += 1
          minutes = int(totalTimeTakenForMove) // 60
          seconds = totalTimeTakenForMove % 60
          timeTaken = ("  (%dm " % minutes if minutes > 0 else "  (") + ("%.2fs)" % seconds) if self.currentPlayer.isAI else ""
          return timeTaken              
  
  def printAverageTimeTakenByPlayers(self):
    """Prints out the average time taken per move for each player"""
    opponentPiece = opponentOf(self.userPiece)
    userTimeTaken = round(self.time_player[self.userPiece][1]/max(1, self.time_player[self.userPiece][2]), 3)
    aiTimeTaken = round(self.time_player[opponentPiece][1]/max(1, self.time_player[opponentPiece][2]), 3)
    self.ui.gui.set_moves('\n'.join(["Average time taken per move:",
                                f"{self.time_player[self.userPiece][0]}: {userTimeTaken}s",
                                f"{self.time_player[opponentPiece][0]}: {aiTimeTaken}s"]))
      
  def run(self):
      """main method that prompts the user for input"""
      
      UserPlayerClass = HumanPlayer
      AI_DUEL_MODE = False 
      
      turn = BLACK
      useSavedGame = False
    
      userPlayerName = "You"
      aiPlayerName = "AI"
      self.gameBoard = self.createEmptyGameBoard(int(self.board_dimension))
  
      playerColorInput = console.input_alert("Would you like to be BLACK ('b') or WHITE ('w')? (black goes first!):")
      if playerColorInput == 'b':
        self.userPiece = BLACK
        opponentPiece = WHITE
        self.ui.gui.set_top(f"{userPlayerName} will be BLACK!")
      else:
        self.userPiece = WHITE
        opponentPiece = BLACK
        self.ui.gui.set_top(f"{userPlayerName} will be WHITE!")
  
      self.time_player = {
        self.userPiece: [userPlayerName, 0, 0],    # [player name, total time, num moves]
        opponentPiece: [aiPlayerName, 0, 0]
      }           
      playerNames = {self.userPiece: userPlayerName, opponentPiece: aiPlayerName}      
      self.players = {opponentPiece: GomokuStrategy(opponentPiece, self.board_dimension, self.ui), 
                    self.userPiece: HumanPlayer(self.userPiece, self.ui)}  
      self.printGameBoard()   
      gameOver, winner = False, None
    
      while not gameOver:
        nameOfCurrentPlayer = playerNames[turn]
        self.currentPlayer = self.players[turn]
        self.player_time(turn, start=True)
        self.ui.gui.set_prompt(f"Select  position (A1 - {self.COLUMN_LABELS[self.board_dimension-1]}{self.board_dimension})")
        rowPlayed, colPlayed = self.currentPlayer.getMove(self.gameBoard)
        if rowPlayed == None:
           # switched to AI vs AI
           rowPlayed, colPlayed = self.currentPlayer.getMove(self.gameBoard) 
        timeTakenOutputStr = self.player_time(turn, start=False)    
      
        performMove(self.gameBoard, rowPlayed, colPlayed, turn)
        
        self.printGameBoard( [[rowPlayed, colPlayed]])
        moveFormatted = self.COLUMN_LABELS[colPlayed] + str(rowPlayed + 1)
        self.ui.gui.set_message2("%s played in spot %s%s\n" % (nameOfCurrentPlayer, moveFormatted, timeTakenOutputStr))
        turn = opponentOf(turn)
        gameOver, winner = self.players[opponentPiece].isTerminal(self.gameBoard)
    
      if winner is None:
          self.ui.gui.set_messge("Nobody wins, it's a tie!")
      else:        
          winnerColorName = "BLACK" if winner == BLACK else "WHITE"
          self.ui.gui.set_message(f"{winnerColorName} wins!\n", color='black')
      self.printAverageTimeTakenByPlayers()
      
def main():
    ui = UI()
    ui.initialize()
    game = GomukuGame(ui)
    ui.game = game
    game.run()
  
if __name__ == '__main__':
  main()

