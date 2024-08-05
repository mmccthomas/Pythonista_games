# The super class that player objects will inherit from

from typing import List, Tuple

class GomokuPlayer:

    def __init__(self, color:str, boardDimension:int=13, isAI:bool=True, ui=None):
        """Sets the color for this player, and indicates whether it is an AI"""
        self.color = color
        self.BOARD_DIMENSION = boardDimension
        self.isAI = isAI
        self.ui = ui

    def getMove(self, board:List[List[str]]) -> Tuple[int, int]:
        """Returns the chosen move for a given board, in [rowIndex, columnIndex] format"""
        print("\n<!> Function 'getMove' has not been implemented.\n"+
              "The program has been terminated.\n" +
              "Please make sure that you have implemented 'getMove' from the Player super class.\n")
        exit(0)
        return -1, -1 # to satisfy the return type hint warning
        
    def print_output(self, msg, **kwargs):
      if self.ui:
        self.ui.gui.set_prompt(msg)
      else:
        print(msg)
