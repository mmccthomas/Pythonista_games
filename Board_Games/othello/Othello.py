# Kyle Gerner
# Started 7.15.22
# Othello AI, client facing
# CMT
# added gui and converted print statements to
# gui message calls
# inputs are mostly replaced by waiting for touch finishes.
# detect by mismatch in board contents

import os
import sys
import time
from datetime import datetime
sys.path.append('../')
sys.path.append('../../')
import gui.gui_scene as gscene
from gui.gui_interface import Gui

from util.save.saving import path_to_save_file, allow_save
from util.aiduel.dueling import get_dueling_ai_class

from othello.othello_strategy import OthelloStrategy, copyOfBoard, BOARD_DIMENSION, getValidMoves, opponentOf, \
    playMove, currentScore, checkGameOver, numberOfPieceOnBoard, pieceAt, hasValidMoves, isMoveValid, isMoveInRange
from othello.othello_player import OthelloPlayer

BLACK = "0"
WHITE = "O"
EMPTY = "."


# Miscellaneous

SAVE_FILENAME = "othello_save.txt"
TIME_TAKEN_PER_PLAYER = {}
INFO_SYMBOL = ERROR_SYMBOL = "<!>"
COLUMN_LABELS = list(map(chr, range(65, 65 + BOARD_DIMENSION)))

# Relevant to game state
BOARD = []
RESPONSE = None
BOARD_HISTORY = []
USER_PIECE = BLACK      # may be changed in game setup
OPPONENT_PIECE = WHITE  # may be changed in game setup

class Player():
  def __init__(self):
    self.PLAYER_1 = 'O'
    self.PLAYER_2 = '0'
    self.EMPTY = '.'
    self.PLAYERS =[self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:White_Circle', 'emj:Black_Circle']
    self.PIECE_NAMES ={BLACK: 'Black', WHITE: 'White'}

# class for the Human player
class HumanPlayer(OthelloPlayer):

    def __init__(self, color):
        super().__init__(color, isAI=False)

    def getMove(self, board, gui):
        """Takes in the user's input and returns the move"""
        
        gui.set_prompt(
          f"It's your turn, which spot would you like to play? (A1 - H8)")
        # sit here until piece place on board
        coord = gui.wait_for_gui(board)    
          
        linesWrittenToConsole = BOARD_DIMENSION + 6
        
        index = 0
        while True:
            index += 1
            gui.set_prompt('')          
            if len(coord) in ([2] if BOARD_DIMENSION < 10 else [2, 3]) and coord[0] in COLUMN_LABELS and \
                    coord[1:].isdigit() and int(coord[1:]) in range(1, BOARD_DIMENSION + 1):
                row, col = int(coord[1]) - 1, COLUMN_LABELS.index(coord[0])
                if isMoveValid(self.color, row, col, board):                    
                    return row, col
                elif isMoveInRange(row, col) and pieceAt(row, col, board) != EMPTY:
                    gui.set_prompt(f"{ERROR_SYMBOL} That spot is already taken! Please choose a different spot:   ")
                    coord = gui.wait_for_gui(board)                      
                else:
                    gui.set_prompt(f"{ERROR_SYMBOL} Please choose one of the highlighted spaces:")
                    coord = gui.wait_for_gui(board)
        


                
   
def printBoard(gui, highlightedCoordinates=None, board=None):
    """Transfers  gameBoard to gui
    if board is a single list just update that item"""
    if highlightedCoordinates is None:
        highlightedCoordinates = []
    if board is None:
        board = BOARD
    gui.update(board)
    gui.valid_moves(highlightedCoordinates)
            
    movesRemaining = numberOfPieceOnBoard(EMPTY, board)
    userScore, aiScore = currentScore(USER_PIECE, board)
    gui.set_moves(f"{movesRemaining} turns remain\n1: {userScore} to 2: {aiScore}")     
    


def printMoveHistory(gs, numMovesPrevious):
    """Prints the move history of the current game"""
    while True:
        printBoard(gs, board=[BOARD_HISTORY[-(numMovesPrevious + 1)][0], BOARD_HISTORY[-(numMovesPrevious + 1)][1]])
        if numMovesPrevious == 0:
            return
        gui.set_message("(%d move%s before current board state)" % (numMovesPrevious, "s" if numMovesPrevious != 1 else ""))
        numMovesPrevious -= 1
        

def getBoardHistoryInputFromUser(gui, board, turn, isAi, linesWrittenToConsole):
    """
    Prompts the user for input for how far the board history function.
    Returns the user's input for the next move, and the new value for linesWrittenToConsole
    """
    nextMovePrompt = "Press enter to continue." if isAi else "Enter a valid move to play:"
    if len(BOARD_HISTORY) < 2:
        userInput = input(f"No previous moves to see. {nextMovePrompt}   ").strip().upper()
        
    else:
        numMovesPrevious = input(f"How many moves ago do you want to see? (1 to {len(BOARD_HISTORY) - 1})  ").strip()
        if numMovesPrevious.isdigit() and 1 <= int(numMovesPrevious) <= len(BOARD_HISTORY) - 1:
            linesWrittenToConsole += 1
            erasePreviousLines(linesWrittenToConsole)
            printMoveHistory(gs, int(numMovesPrevious))
            
            printBoard(getValidMoves(turn, board))
            userInput = input(f"{INFO_SYMBOL} You're back in play mode. {nextMovePrompt}   ").strip().upper()
            
            linesWrittenToConsole = BOARD_DIMENSION + 4
        else:
            userInput = input(f"{ERROR_SYMBOL} Invalid input. {nextMovePrompt}   ").strip().upper()
            
    return userInput, linesWrittenToConsole

def textColorOf(piece):
    """Gets the text color of the given piece, or an empty string if no piece given"""
    if piece == USER_PIECE:
        return USER_COLOR
    elif piece == OPPONENT_PIECE:
        return AI_COLOR
    else:
        return None


def nameOfPieceColor(piece):
    """Gets the name of the color of the given piece"""
    if piece == BLACK:
        return "BLACK"
    elif piece == WHITE:
        return "WHITE"
    else:
        return "EMPTY"


def endGame(gui, winner=None):
    """Ends the game"""
    if winner:
        colorName = nameOfPieceColor(winner)
        gui.set_message(f"\n{colorName} wins!")
        gui.set_prompt('')
        gui.set_message2('')
    else:
        gui.set_message("The game ended in a draw!")
    userTimeTaken = round(TIME_TAKEN_PER_PLAYER[USER_PIECE][1]/max(1, TIME_TAKEN_PER_PLAYER[USER_PIECE][2]), 2)
    aiTimeTaken = round(TIME_TAKEN_PER_PLAYER[OPPONENT_PIECE][1]/max(1, TIME_TAKEN_PER_PLAYER[OPPONENT_PIECE][2]), 2)
    gui.set_moves(f"Average time / move:\n{TIME_TAKEN_PER_PLAYER[USER_PIECE][0]}: {userTimeTaken}s \   {TIME_TAKEN_PER_PLAYER[OPPONENT_PIECE][0]}: {aiTimeTaken}s")
    gui.set_prompt("Thanks for playing!")
    time.sleep(3)
    sys.exit()
    

def save():
  global gui, turn
  saveGame(BOARD,turn, gui)
  
def saveGame(board, turn, gui):
    """Saves the given board state to a save file"""
    #if not allow_save(SAVE_FILENAME):
    #    return
    with open(SAVE_FILENAME, 'w') as saveFile:
        saveFile.write("This file contains the save state of a previously played game.\n")
        saveFile.write("Modifying this file may cause issues with loading the save state.\n\n")
        timeOfSave = datetime.now().strftime("%m/%d/%Y at %I:%M:%S %p")
        saveFile.write(timeOfSave + "\n\n")
        saveFile.write("SAVE STATE:\n")
        for row in board:
            saveFile.write(" ".join(row) + "\n")
        saveFile.write(f"User piece: " + USER_PIECE  +"\n")
        saveFile.write("Opponent piece: " + OPPONENT_PIECE  +"\n")
        saveFile.write("Turn: " + turn)
    gui.set_prompt(f"The game has been saved!")


def printGameRules():
    """Gives the user the option to view the rules of the game"""
    print("\nType 'q' at any move prompt to quit the game.")
    print("Type 's' save the game.")
    print("Type 'h' to see previous moves.")
    print("AI constants are modifiable in the othello_strategy.py file.")
    showRules = input("Would you like to see the rules? (y/n)   ").strip().lower()

    if showRules == 'q':
        print("\nThanks for playing!")
        exit(0)
    elif showRules == 'y':
        print("""
    - OBJECTIVE: Have more pieces on the board than the opponent when all spaces are full
    - TURNS: Black will go first. Each player will take turns placing one piece each turn
    - GAMEPLAY: Trap enemy pieces between two friendly pieces to convert them to friendly pieces
        """)


def printAsciiTitleArt():
    """Prints the fancy text when you start the program"""
    print("""
             _  __     _      _
            | |/ /    | |    ( )
            | ' /_   _| | ___|/ ___
            |  <| | | | |/ _ \ / __|
            | . \ |_| | |  __/ \__ \\
            |_|\_\__, |_|\___| |___/
 _____  _   _     __/ |_ _                  _____
/  __ \\| | | |   |___/| | |           /\\   |_   _|
| |  | | |_| |__   ___| | | ___      /  \\    | |
| |  | | __| '_ \\ / _ \\ | |/ _ \\    / /\\ \\   | |
| |__| | |_| | | |  __/ | | (_) |  / ____ \\ _| |_
\\_____/ \\__|_| |_|\\___|_|_|\\___/  /_/    \\_\\_____|
    """)
def load(): # from gui
  global BOARD, USER_PIECE, turn
  if os.path.exists(SAVE_FILENAME):
        BOARD, USER_PIECE, turn = loadSavedGame()
        print(turn, USER_PIECE, BOARD)
        gui.set_message('')
        gui.set_message2('')
        printBoard(gui)

def loadSavedGame():
    global gui
    """Try to load the saved game data"""
    with open(SAVE_FILENAME, 'r') as saveFile:
        try:
            linesFromSaveFile = saveFile.readlines()
            timeOfPreviousSave = linesFromSaveFile[3].strip()       
            gui.set_prompt(f'Loading saved game from {timeOfPreviousSave}')
            
            lineNum = 0
            currentLine = linesFromSaveFile[lineNum].strip()
            while currentLine != "SAVE STATE:":
                lineNum += 1
                currentLine = linesFromSaveFile[lineNum].strip()
            lineNum += 1
            currentLine = linesFromSaveFile[lineNum].strip()
            board = []
            while not currentLine.startswith("User piece"):
                board.append(currentLine.split())
                lineNum += 1
                currentLine = linesFromSaveFile[lineNum].strip()
            userPiece = currentLine.split(": ")[1].strip()
            lineNum += 2
            currentLine = linesFromSaveFile[lineNum].strip()
            turn = currentLine.split(": ")[1].strip()
            if not validateLoadedSaveState(board, userPiece, turn):
                raise ValueError
            
            gui.set_prompt(f"{INFO_SYMBOL} Resuming saved game...")
            return board, userPiece, turn
        except Exception:
            gui.set_prompt(f"{ERROR_SYMBOL} Error reading from the save file. Starting a new game...")
            return None, None, None


def validateLoadedSaveState(board, piece, turn):
    """Make sure the state loaded from the save file is valid. Returns a boolean"""
    if len(board) != BOARD_DIMENSION:
        print(f"{ERROR_SYMBOL} Board dimension does not match!")
        return False
    if piece not in [BLACK, WHITE]:
        print(f"{ERROR_SYMBOL} Invalid user piece!")
        return False
    if turn not in [BLACK, WHITE]:
        print(f"{ERROR_SYMBOL} Invalid player turn!")
        return False
    boardDimension = len(board)
    for row in board:
        if len(row) != boardDimension:
            print(f"{ERROR_SYMBOL} Board is not square!")
            return False
        if row.count(EMPTY) + row.count(BLACK) + row.count(WHITE) != boardDimension:
            print(f"{ERROR_SYMBOL} Board contains invalid pieces!")
            return False
    return True


def getUserPieceColorInput(gui):
    """Gets input from the user to determine which color they will be"""
    color_input = gui.input_message("Would you like to be  BLACK ('b') or WHITE ('w')?\n (black goes first!):")
    try:
      color_input = colorinput.strip().lower()
    except:
      pass
    color = BLACK if color_input == 'b' else WHITE
    if color == BLACK:
        gui.set_top("You are BLACK")
    else:
        gui.set_top("You will be WHITE")   
    return color


def createNewBoard():
    """Creates the initial game board state"""
    board = [[EMPTY for _ in range(BOARD_DIMENSION)] for __ in range(BOARD_DIMENSION)]
    board[BOARD_DIMENSION // 2][BOARD_DIMENSION // 2 - 1] = WHITE
    board[BOARD_DIMENSION // 2 - 1][BOARD_DIMENSION // 2] = WHITE
    board[BOARD_DIMENSION // 2][BOARD_DIMENSION // 2] = BLACK
    board[BOARD_DIMENSION // 2 - 1][BOARD_DIMENSION // 2 - 1] = BLACK
    return board
    


def run():
    global BOARD, USER_PIECE, OPPONENT_PIECE, TIME_TAKEN_PER_PLAYER, gui, turn
    
    
    if "-d" in sys.argv or "-aiDuel" in sys.argv:
        UserPlayerClass = get_dueling_ai_class(OthelloPlayer, "OthelloStrategy")
        print(f"\n{INFO_SYMBOL} You are in AI Duel Mode!")
        AI_DUEL_MODE = True
    else:
        UserPlayerClass = HumanPlayer
        AI_DUEL_MODE = False
        
    BOARD = createNewBoard()  
    #printAsciiTitleArt()
    #printGameRules()
    # load the gui interface
    gui = Gui(BOARD, Player())  
    gui.setup_gui()  
    # menus can be controlled by dictionary of labels and functions without parameters
    gui.gs.pause_menu = {'Continue': gui.gs.dismiss_modal_scene,  'Save': save, 
                         'Load': load,  'Quit': gui.gs.close}
    gui.gs.start_menu = {'New Game': run, 'Quit': gui.gs.close} 
    USER_PIECE = getUserPieceColorInput(gui)
    
    turn = BLACK
    BOARD_HISTORY.append([[], copyOfBoard(BOARD)])
    OPPONENT_PIECE = opponentOf(USER_PIECE)
    userPlayerName = "Your AI" if AI_DUEL_MODE else "You"
    aiPlayerName = "My AI" if AI_DUEL_MODE else "AI"
    
                       
                         
    playerNames = {USER_PIECE: userPlayerName, OPPONENT_PIECE: aiPlayerName}
    players = {
        USER_PIECE: UserPlayerClass(USER_PIECE),
        OPPONENT_PIECE: OthelloStrategy(OPPONENT_PIECE)
    }
    TIME_TAKEN_PER_PLAYER = {
        USER_PIECE: [userPlayerName, 0, 0],    # [player name, total time, num moves]
        OPPONENT_PIECE: [aiPlayerName, 0, 0]
    }
    
    
    printBoard(gui, getValidMoves(turn, BOARD))
    gui.set_top(f'You are {"BLACK" if USER_PIECE==BLACK else "WHITE"}')
    
    numValidMovesInARow = 0
    gameOver, winner = False, None
    # Game Loop
    while not gameOver:
        movesRemaining = numberOfPieceOnBoard(EMPTY, BOARD)
        userScore, aiScore = currentScore(USER_PIECE, BOARD)
        
        gui.set_moves(f"{movesRemaining} turns remain\n" +
         f"{playerNames[USER_PIECE]}: {userScore} to  {playerNames[OPPONENT_PIECE]}: {aiScore}")   
        linesWrittenToConsole = BOARD_DIMENSION + 6
        if hasValidMoves(turn, BOARD):
            numValidMovesInARow = 0
            nameOfCurrentPlayer = playerNames[turn]
            currentPlayer = players[turn]
            if currentPlayer.isAI:
              time.sleep(1) 
              
            startTime = time.time()
            # human move or ai move
            # human move needs gui instance
            try:
              # gui.start_activity()
              row, col = currentPlayer.getMove(BOARD)
              # gui.stop_activity()
            except (TypeError):
              row, col = currentPlayer.getMove(BOARD, gui)
            endTime = time.time()
            timeToPlayMove = (endTime - startTime)
            TIME_TAKEN_PER_PLAYER[turn][1] += timeToPlayMove
            TIME_TAKEN_PER_PLAYER[turn][2] += 1
            timeToPlayMove = round(timeToPlayMove, 2)
            playMove(turn, row, col, BOARD)
            BOARD_HISTORY.append([[[row, col]], copyOfBoard(BOARD)])
            gui.gs.clear_highlights()
            gui.valid_moves(getValidMoves(opponentOf(turn), BOARD))
            #printBoard([[row, col]] + getValidMoves(opponentOf(turn), BOARD))
            if currentPlayer.isAI:
                additionalOutput = "  (%0.2f sec" % timeToPlayMove
                if hasattr(currentPlayer, 'numBoardsEvaluated'):
                    additionalOutput += ", %d possible futures)" % currentPlayer.numBoardsEvaluated
                else:
                    additionalOutput += ")"
            else:
                additionalOutput = ""
            moveOutputFormatted = COLUMN_LABELS[col] + str(row + 1)
            gui.update(BOARD)
            gui.set_message(f"{nameOfCurrentPlayer} played in spot {moveOutputFormatted}{additionalOutput}")
            
        else:
            numValidMovesInARow += 1
            if numValidMovesInARow == 2:
                gui.set_prompt("Neither player has any valid moves left!")
                userScore, aiScore = currentScore(USER_PIECE, BOARD)
                if userScore > aiScore:
                    endGame(gui, USER_PIECE)
                elif aiScore > userScore:
                    endGame(gui, OPPONENT_PIECE)
                else:
                    endGame(gui)
            gui.set_prompt(f"<!> {nameOfPieceColor(turn)} has no valid moves this turn! \{nameOfPieceColor(opponentOf(turn))} will play again." )
        gameOver, winner = checkGameOver(BOARD)
        turn = opponentOf(turn)
    endGame(gui, winner)

if __name__ == '__main__':
  run()
