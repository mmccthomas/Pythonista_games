# Kyle Gerner 
# Started 3.18.21
# Connect 4 Solver, client facing
import os
import sys
import time
from queue import Queue
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)

from util.aiduel.dueling import get_dueling_ai_class
from datetime import datetime
from connect4.connect4_player import Connect4Player
from connect4.connect4_strategy import Connect4Strategy, opponentOf, performMove, checkIfGameOver, isValidMove, \
    copyOfBoard
    
from gui.game_base import Game
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares

EMPTY, RED, YELLOW = '.', 'o', '@'
gameBoard_init = [[EMPTY for _ in range(7)] for _ in range(6)]

def get_board_rc(coord, board):
  return board[coord[0]][coord[1]]

class Player():
  def __init__(self):
    self.PLAYER_1 = 'o'
    self.PLAYER_2 = '@'
    self.EMPTY = '.'
    self.PLAYERS =[self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:Red_Circle', 'emj:Moon_5']
    self.PIECE_NAMES ={RED: 'Red', YELLOW: 'Yellow'}
    
# class for the Human player
class HumanPlayer(Connect4Player):

    def __init__(self, color):
        super().__init__(color, isAI=False)

    def getMove(self, board, gui):
        """Takes in the user's input and returns the move"""
        gui.set_prompt(
          f"It's your turn, which column to play? (1 - 7")
        # sit here until piece place on board
        coord = gui.wait_for_gui(board) 
        col = coord[0]
        
        while True:
            gui.set_prompt('')    
            if not col.isdigit() or int(col) not in range(1, 8):
                gui.set_prompt(f"Invalid input. Please enter a number 1 through 7:")
                col = gui.wait_for_gui(board)[0]
            elif not isValidMove(board, int(col) - 1):
                gui.set_prompt(f"That column is full, please choose another:")
                col = gui.wait_for_gui(board)[0]
            else:
                break        
        return int(col) - 1

class Connect4(Game):
  
  def __init__(self):
    
    print("\nWelcome to Kyle's Connect 4 AI!")
    self.printAsciiTitleArt()      
    self.gameBoard = copyOfBoard(gameBoard_init)   
    # load the gui interface
    self.q = Queue(maxsize=10)
    self.gui = Gui(self.gameBoard, Player())
    self.gui.set_alpha(False) 
    self.gui.set_grid_colors(grid='othello.jpg', highlight='clear')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui()
    self.gui.gs.q = self.q
    
    self.turn = None
    self.userPiece = YELLOW
    self.board_history = [] # [board, highlightCoordinates]
    self.time_taken_per_player = {}
    self.loaded_file = False # used to skip player selection
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.gs.pause_menu = {'Continue': self.gui.gs.dismiss_modal_scene, 
                              'Show Game': self.getBoardHistory,
                              'Quit': self.quit}
    self.gui.gs.start_menu = {'New Game': self.run, 
                              'Replay': self.getBoardHistory,  
                              'Quit': self.quit}
     
    if "-d" in sys.argv or "-aiDuel" in sys.argv:
          self.UserPlayerClass = get_dueling_ai_class(Connect4Player, "Connect4Strategy")
          print(f"\n You are in AI Duel Mode!")
          AI_DUEL_MODE = True
    else:
          self.UserPlayerClass = HumanPlayer
          AI_DUEL_MODE = False           
      
    self.userPlayerName = "Your AI" if AI_DUEL_MODE else "You"
    self.aiPlayerName = "My AI" if AI_DUEL_MODE else "AI"                         
    self.gui.clear_messages()
    
  def printBoard(self, recentMove=None):
      """Prints the given game board"""
      self.gui.update(self.gameBoard)
  
  def getBoardHistory(self):
      """
      Slowly shows the game 
      """
      for game, col in self.board_history:
        self.gui.update(game)
        time.sleep(1) 
      self.gui.gs.show_start_menu()
           
  def highlight_winning(self):
        NUM_COLS = len(self.gameBoard[0])
        NUM_ROWS = len(self.gameBoard)
        board = self.gameBoard
   
      	# Check horizontal
        for c in range(NUM_COLS - 3):
          for r in range(NUM_ROWS):
            seq = [(r, c + i) for i in range(4)]
            if all([get_board_rc(seq[0], board) == get_board_rc(coord, board) 
                    if get_board_rc(coord, board) != EMPTY else False for coord in seq]):
                return seq                      
      
        # Check vertical
        for c in range(NUM_COLS):
          for r in range(NUM_ROWS - 3):
            seq = [(r + i, c) for i in range(4)]
            if all([get_board_rc(seq[0], board) == get_board_rc(coord, board) 
                    if get_board_rc(coord, board) != EMPTY else False for coord in seq]):
                return seq
      
        # Check diagonal from bottom left to top right
        for c in range(NUM_COLS - 3):
          for r in range(NUM_ROWS - 3):
            seq = [(r + i, c + i) for i in range(4)]
            if all([get_board_rc(seq[0], board) == get_board_rc(coord, board) 
                    if get_board_rc(coord, board) != EMPTY else False for coord in seq]):
                return seq
      
        # Check diagonal from bottom right to top left
        for c in range(NUM_COLS - 3):
          for r in range(3, NUM_ROWS):
            seq = [(r - i, c + i) for i in range(4)]
            if all([get_board_rc(seq[0], board) == get_board_rc(coord, board) 
                    if get_board_rc(coord, board) != EMPTY else False for coord in seq]):
                return seq
        return None
        
  def endGame(self):
      """Ends the game"""
      
      opponentPiece = opponentOf(self.userPiece)
      userTimeTaken = round(self.time_taken_per_player[self.userPiece][1]/max(1, self.time_taken_per_player[self.userPiece][2]), 2)
      aiTimeTaken = round(self.time_taken_per_player[opponentPiece][1]/max(1, self.time_taken_per_player[opponentPiece][2]), 2)
      self.gui.set_moves("Average time:\n" + f"{self.time_taken_per_player[self.userPiece][0]}: {userTimeTaken}s" + "\n" + f"{self.time_taken_per_player[opponentPiece][0]}: {aiTimeTaken}s")
      self.gui.set_prompt("Thanks for playing!")
      self.gui.set_grid_colors(None, "orange")
      self.gui.valid_moves(self.highlight_winning(), False)        
      time.sleep(3)
      self.gui.gs.clear_highlights()     
  
  def printAsciiTitleArt(self):
      """Prints the fancy text when you start the program"""
      print("""
     _____                            _     _  _   
    / ____|                          | |   | || |  
   | |     ___  _ __  _ __   ___  ___| |_  | || |_ 
   | |    / _ \| '_ \| '_ \ / _ \/ __| __| |__   _|
   | |___| (_) | | | | | | |  __/ (__| |_     | |  
    \_____\___/|_| |_|_| |_|\___|\___|\__|    |_|      
      """)
      
  def select_player(self):
      selection = self.gui.input_message("Would you like to be RED ('r') or YELLOW ('y')?\n (yellow goes first!):")
      x, y, w, h = self.gui.grid.bbox
      try:
        selection = selection.strip().lower()
      except:
        pass
            
      if selection == 'y':
        self.userPiece = YELLOW
        self.opponentPiece = RED
        self.gui.set_top(f"{self.userPlayerName} are YELLOW", position=(x, h+50))
      else:
        self.userPiece = RED
        self.opponentPiece = YELLOW
        self.gui.set_top(f"{self.userPlayerName} are RED", position=(x, h+50))
        
  def win(self, winner):
    
      if winner is None:
          self.gui.set_message2("The game ended in a tie!")
      elif winner == RED:
          self.gui.set_message2(f"RED wins!")
      else:
          self.gui.set_message2(f"YELLOW wins!")
      
      self.endGame()   
  
  def run(self):
      """main method that prompts the user for input"""
      
      if not self.loaded_file:                                    
        self.turn = YELLOW
        self.gameBoard = copyOfBoard(gameBoard_init)
          
        self.select_player()        
      
      self.time_taken_per_player = {
          self.userPiece: [self.userPlayerName, 0, 0],    # [player name, total time, num moves]
          self.opponentPiece: [self.aiPlayerName, 0, 0]
      }
      
      # self.gui.set_moves(f"{self.userPlayerName}: {self.userPiece}\t{self.aiPlayerName}: {self.opponentPiece}")
      playerNames = {self.opponentPiece: self.aiPlayerName, self.userPiece: self.userPlayerName}
      players = {self.opponentPiece: Connect4Strategy(self.opponentPiece), self.userPiece: self.UserPlayerClass(self.userPiece)}
      
      gameOver = False
      winningPiece = None      
      
      self.printBoard()
      
      while not gameOver:         
                
          nameOfCurrentPlayer = playerNames[self.turn]
          currentPlayer = players[self.turn]
          
          startTime = time.time()       
             
          self.gui.set_player(self.turn, Player)  
               
          #  ai move                    
          try:
            column = currentPlayer.getMove(self.gameBoard) #AI            
          except (TypeError): # human
            column = currentPlayer.getMove(self.gameBoard, self.gui)
                            
          endTime = time.time()
          totalTimeTakenForMove = endTime - startTime
          self.time_taken_per_player[self.turn][1] += totalTimeTakenForMove
          self.time_taken_per_player[self.turn][2] += 1
          # makes piece drop and updates gameBoard
          performMove(self.gameBoard, column, self.turn)
          
          self.board_history.append([copyOfBoard(self.gameBoard), column])
          self.printBoard()
          
          self.gui.set_message(f"{nameOfCurrentPlayer} played in spot {column + 1}")
          
          self.turn = opponentOf(self.turn)  # switch the turn
          
          gameOver, winningPiece = checkIfGameOver(self.gameBoard)        
  
      self.win(winningPiece)
      self.loaded_file = False
      time.sleep(3)
      self.gui.gs.show_start_menu()
      
  def quit(self):
    self.gui.gs.close()
    sys.exit() 
       
  def wait(self):
    #wait until closed by gui or new game
    while True:
      if not self.gui.v.on_screen:
        print('View closed, exiting')
        break
      try:
        if not self.q.empty():
          item = self.q.get(block=False)
          print('item', item)
          item()
      except (Exception) as e:
        print(e)
        break
      
      time.sleep(0.5)    
      
if __name__ == '__main__':
  g = Connect4()
  g.run()
  g.wait()
