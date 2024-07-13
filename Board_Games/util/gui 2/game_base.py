# common routines
from util.save.saving import path_to_save_file, allow_save
from connect4.connect4_strategy import  opponentOf
from datetime import datetime

class Game():
  
  def saveGame(self, turn, SAVE_FILENAME):
      """Saves the given board state to a save file"""
      #if not allow_save(SAVE_FILENAME):
      #    return
      with open(SAVE_FILENAME, 'w') as saveFile:
          saveFile.write("This file contains the save state of a previously played game.\n")
          saveFile.write("Modifying this file may cause issues with loading the save state.\n\n")
          timeOfSave = datetime.now().strftime("%m/%d/%Y at %I:%M:%S %p")
          saveFile.write(timeOfSave + "\n\n")
          saveFile.write("SAVE STATE:\n")
          for row in self.gameBoard:
              saveFile.write(" ".join(row) + "\n")
          saveFile.write("User piece: " + str(self.userPiece)  +"\n")
          saveFile.write("Opponent piece: " + opponentOf(self.userPiece)  +"\n")
          saveFile.write("Turn: " + turn)
      self.gui.set_prompt(f"The game has been saved!")
      
  def loadSavedGame(self, SAVE_FILENAME):
      """Try to load the saved game data"""
      with open(SAVE_FILENAME, 'r') as saveFile:
          try:
              linesFromSaveFile = saveFile.readlines()
              timeOfPreviousSave = linesFromSaveFile[3].strip()
              self.gui.set_prompt(f"Loading saved game from {timeOfPreviousSave}")           
              
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
              user_piece = currentLine.split(": ")[1].strip()
              lineNum += 2
              currentLine = linesFromSaveFile[lineNum].strip()
              turn = currentLine.split(": ")[1].strip()
              
              board = boardFromSaveFile
              
              return turn,board, user_piece
          except (Exception) as e:
              print(e)
              self.gui.set_prompt(f"Error reading from the save file. Starting a new game..")
              return None, None, None
  
  def printMoveHistory(self, numMovesPrevious):
      """Prints the move history of the current game"""
      while True:
          self.printBoard(self.board_history[-(numMovesPrevious + 1)][0], self.board_history[-(numMovesPrevious + 1)][1])
          if numMovesPrevious == 0:
              return
          print("(%d move%s before current board state)\n" % (numMovesPrevious, "s" if numMovesPrevious != 1 else ""))
          numMovesPrevious -= 1
          userInput = input("Press enter for next move, or 'e' to return to game.  ").strip().lower()      
      
  
