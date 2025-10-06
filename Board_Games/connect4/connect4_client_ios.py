# Kyle Gerner 
# Started 3.18.21
# Connect 4 Solver, client facing
import os
import sys
import time
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)


from util.save.saving import path_to_save_file, allow_save
from util.aiduel.dueling import get_dueling_ai_class
from datetime import datetime
from connect4.connect4_player import Connect4Player
from connect4.connect4_strategy import Connect4Strategy, opponentOf, performMove, checkIfGameOver, isValidMove, \
    copyOfBoard
    
import util.gui.gui_scene as gscene
from util.gui.gui_interface import Gui



SAVE_FILENAME = path_to_save_file("connect4_save.txt")
BOARD_HISTORY = []  # [board, highlightCoordinates]

EMPTY, RED, YELLOW = '.', 'o', '@'
gameBoard = [[EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],  # bottom row
             [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
             [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
             [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
             [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
             [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]]  # top row
userPiece = YELLOW
TIME_TAKEN_PER_PLAYER = {}

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
            elif not isValidMove(gameBoard, int(col) - 1):
                gui.set_prompt(f"That column is full, please choose another:")
                col = gui.wait_for_gui(board)[0]
            else:
                break
        
        return int(col) - 1


def printBoard(gui, board, recentMove=None):
    """Prints the given game board"""
    highlightedCoordinates = [[j,i] for i in range(7) for j in range(6) if board[j][i] == EMPTY]
    gui.update(board)
    gui.valid_moves(highlightedCoordinates, message=None)


def printMoveHistory(numMovesPrevious):
    """Prints the move history of the current game"""
    while True:
        printBoard(BOARD_HISTORY[-(numMovesPrevious + 1)][0], BOARD_HISTORY[-(numMovesPrevious + 1)][1])
        if numMovesPrevious == 0:
            return
        print("(%d move%s before current board state)\n" % (numMovesPrevious, "s" if numMovesPrevious != 1 else ""))
        numMovesPrevious -= 1
        userInput = input("Press enter for next move, or 'e' to return to game.  ").strip().lower()
        


def getBoardHistory():
    global gui
    """
    Prompts the user for input for how far the board history function.
    Returns the user's input for the next move
    """
    for game, col in BOARD_HISTORY:
      gui.update(game)
      time.sleep(1)    

def endGame(gui):
    """Ends the game"""
    def highlight_winning():
      NUM_COLS = len(gameBoard[0])
      NUM_ROWS = len(gameBoard)
      board = gameBoard
      # TODO this stinks a bit    
    	# Check horizontal
      for c in range(NUM_COLS - 3):
        for r in range(NUM_ROWS):
          #if [board[r][c] == board[r][c + i] for i in range(1,3) if 
          if board[r][c] == board[r][c + 1] == board[r][c + 2] == board[r][c + 3] != EMPTY:
            return [[r, c], [r, c + 1], [r, c + 2], [r, c + 3]]
    
      # Check vertical
      for c in range(NUM_COLS):
        for r in range(NUM_ROWS - 3):
          if board[r][c] == board[r + 1][c] == board[r + 2][c] == board[r + 3][c] != EMPTY:
            return [[r, c], [r + 1, c], [r + 2, c], [r + 3, c]]
    
      # Check diagonal from bottom left to top right
      for c in range(NUM_COLS - 3):
        for r in range(NUM_ROWS - 3):
          if board[r][c] == board[r + 1][c + 1] == board[r + 2][c + 2] == board[r + 3][c + 3] != EMPTY:
            return [[r, c], [r + 1, c + 1], [r + 2, c + 2], [r + 3, c + 3]]
    
      # Check diagonal from bottom right to top left
      for c in range(NUM_COLS - 3):
        for r in range(3, NUM_ROWS):
          if board[r][c] == board[r - 1][c + 1] == board[r - 2][c + 2] == board[r - 3][c + 3] != EMPTY:
            return [[r, c], [r + 1, c + 1], [r + 2, c + 2], [r + 3, c + 3]]

      return None
    opponentPiece = opponentOf(userPiece)
    userTimeTaken = round(TIME_TAKEN_PER_PLAYER[userPiece][1]/max(1, TIME_TAKEN_PER_PLAYER[userPiece][2]), 2)
    aiTimeTaken = round(TIME_TAKEN_PER_PLAYER[opponentPiece][1]/max(1, TIME_TAKEN_PER_PLAYER[opponentPiece][2]), 2)
    gui.set_moves("Average time:\n" + f"{TIME_TAKEN_PER_PLAYER[userPiece][0]}: {userTimeTaken}s" + "\n" + f"{TIME_TAKEN_PER_PLAYER[opponentPiece][0]}: {aiTimeTaken}s")
    gui.set_prompt("Thanks for playing!")
    gui.set_grid_colors(None, "orange")
    gui.valid_moves(highlight_winning(), False)        
      
    time.sleep(3)
    #sys.exit()

def save():
  global gui, turn
  saveGame(turn, gui)
  
def saveGame(turn, gui):
    """Saves the given board state to a save file"""
    if not allow_save(SAVE_FILENAME):
        return
    with open(SAVE_FILENAME, 'w') as saveFile:
        saveFile.write("This file contains the save state of a previously played game.\n")
        saveFile.write("Modifying this file may cause issues with loading the save state.\n\n")
        timeOfSave = datetime.now().strftime("%m/%d/%Y at %I:%M:%S %p")
        saveFile.write(timeOfSave + "\n\n")
        saveFile.write("SAVE STATE:\n")
        for row in gameBoard:
            saveFile.write(" ".join(row) + "\n")
        saveFile.write("User piece: " + str(userPiece)  +"\n")
        saveFile.write("Opponent piece: " + opponentOf(userPiece)  +"\n")
        saveFile.write("Turn: " + turn)
    gui.set_prompt(f"The game has been saved!")


def validateLoadedSaveState(board, piece, turn):
    """Make sure the state loaded from the save file is valid. Returns a boolean"""
    if piece not in [RED, YELLOW]:
        print(f"Invalid user piece!")
        return False
    if turn not in [RED, YELLOW]:
        print(f"Invalid player turn!")
        return False
    for row in board:
        if len(row) != 7:
            print(f"Invalid board!")
            return False
        if row.count(EMPTY) + row.count(RED) + row.count(YELLOW) != 7:
            print(f"Board contains invalid pieces!")
            return False
    return True
    
def load(): # from gui
  global gameBoard, userPiece, turn
  if os.path.exists(SAVE_FILENAME):
        turn = loadSavedGame()
        print(turn, userPiece, gameBoard)
        gui.set_message('')
        gui.set_message2('')
        printBoard(gui)

def loadSavedGame():
    """Try to load the saved game data"""
    global userPiece, gameBoard
    with open(SAVE_FILENAME, 'r') as saveFile:
        try:
            linesFromSaveFile = saveFile.readlines()
            timeOfPreviousSave = linesFromSaveFile[3].strip()
            gui.set_prompt(f"Loading saved game from {timeOfPreviousSave}")           
            
            lineNum = 0
            currentLine = linesFromSaveFile[lineNum].strip()
            while currentLine != "SAVE STATE:":
                lineNum += 1
                currentLine = linesFromSaveFile[lineNum].strip()
            lineNum += 1
            currentLine = linesFromSaveFile[lineNum].strip()
            boardFromSaveFile = []
            while not currentLine.startswith("User piece"):
                boardFromSaveFile.append(currentLine.split())
                lineNum += 1
                currentLine = linesFromSaveFile[lineNum].strip()
            userPiece = currentLine.split(": ")[1].strip()
            lineNum += 2
            currentLine = linesFromSaveFile[lineNum].strip()
            turn = currentLine.split(": ")[1].strip()
            if not validateLoadedSaveState(boardFromSaveFile, userPiece, turn):
                raise ValueError
            gameBoard = boardFromSaveFile
            gui.set_prompt(f"Resuming saved game...")
            return turn
        except Exception:
            gui.set_prompt(f"Error reading from the save file. Starting a new game..")
            return None


def printAsciiTitleArt():
    """Prints the fancy text when you start the program"""
    print("""
   _____                            _     _  _   
  / ____|                          | |   | || |  
 | |     ___  _ __  _ __   ___  ___| |_  | || |_ 
 | |    / _ \| '_ \| '_ \ / _ \/ __| __| |__   _|
 | |___| (_) | | | | | | |  __/ (__| |_     | |  
  \_____\___/|_| |_|_| |_|\___|\___|\__|    |_|      
    """)


def run():
    """main method that prompts the user for input"""
    global userPiece, TIME_TAKEN_PER_PLAYER, gui
    if "-d" in sys.argv or "-aiDuel" in sys.argv:
        UserPlayerClass = get_dueling_ai_class(Connect4Player, "Connect4Strategy")
        print(f"\n You are in AI Duel Mode!")
        AI_DUEL_MODE = True
    else:
        UserPlayerClass = HumanPlayer
        AI_DUEL_MODE = False
    print("\nWelcome to Kyle's Connect 4 AI!")
    printAsciiTitleArt()
    userPlayerName = "Your AI" if AI_DUEL_MODE else "You"
    aiPlayerName = "My AI" if AI_DUEL_MODE else "AI"
    # load the gui interface
    gui = Gui(gameBoard, Player())
    gui.set_alpha(False) 
    gui.set_grid_colors(grid='othello.jpg', highlight='clear')
    gui.require_touch_move(False)
    gui.setup_gui() 
    # menus can be controlled by dictionary of labels and functions without parameters
    gui.set_pause_menu({'Continue': gui.dismiss_modal_scene, 'Save': save, 
                         'Load': load, 'Show Game': getBoardHistory, 'Quit': gui.close})
    gui.set_start_menu({'New Game': run, 'Quit': gui.close})
                         
                        
    turn = YELLOW
    useSavedGame = False
            
    if not useSavedGame:
        userPieceInput = gui.input_message("Would you like to be RED ('r') or YELLOW ('y')?\n (yellow goes first!):")
        try:
          userPieceInput = userPieceInput.strip().lower()
        except:
          pass
          
        if userPieceInput == 'y':
            userPiece = YELLOW
            opponentPiece = RED
            gui.set_top(f"{userPlayerName} are YELLOW")
        else:
            userPiece = RED
            opponentPiece = YELLOW
            gui.set_top(f"{userPlayerName} are RED")

    TIME_TAKEN_PER_PLAYER = {
        userPiece: [userPlayerName, 0, 0],    # [player name, total time, num moves]
        opponentPiece: [aiPlayerName, 0, 0]
    }
    
    print(f"{userPlayerName}: {userPiece}\t{aiPlayerName}: {opponentPiece}")
    playerNames = {opponentPiece: aiPlayerName, userPiece: userPlayerName}
    players = {opponentPiece: Connect4Strategy(opponentPiece), userPiece: UserPlayerClass(userPiece)}
    gameOver = False
    winningPiece = None
    
    
    printBoard(gui, gameBoard)
    
    firstTurn = True
    while not gameOver:
        nameOfCurrentPlayer = playerNames[turn]
        currentPlayer = players[turn]
        
        startTime = time.time()        
        # human move or ai move
        # human move needs gui instance
        gui.set_player(turn, Player)
        try:
          column = currentPlayer.getMove(gameBoard) #AI
          
        except (TypeError): # human
          column = currentPlayer.getMove(gameBoard, gui)                
        endTime = time.time()
        # time.sleep(1) 
        totalTimeTakenForMove = endTime - startTime
        TIME_TAKEN_PER_PLAYER[turn][1] += totalTimeTakenForMove
        TIME_TAKEN_PER_PLAYER[turn][2] += 1
        performMove(gameBoard, column, turn)
        BOARD_HISTORY.append([copyOfBoard(gameBoard), column])
        
        gui.clear_highlights()
        printBoard(gui, gameBoard)
        
        gui.set_message(f"{nameOfCurrentPlayer} played in spot {column + 1}")
        
        turn = opponentOf(turn)  # switch the turn
        firstTurn = False
        gameOver, winningPiece = checkIfGameOver(gameBoard)        

    if winningPiece is None:
        gui.set_message2("The game ended in a tie!")
    elif winningPiece == RED:
        gui.set_message2(f"RED wins!")
    else:
        gui.set_message2(f"YELLOW wins!")
    
    endGame(gui)
    gui.show_start_menu()
    
if __name__ == '__main__':
  run()
