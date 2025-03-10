# test solve of all puzzles in pieceword
import Pieceword
from copy import deepcopy

def main():
    obj = Pieceword.PieceWord(test=True)
    obj.debug = False
    
    items = obj.word_dict.keys()
    items = [item for item in items if not item.endswith('_frame')]
    items = [item for item in items
                   if (not item.endswith('_text') and not item.endswith('_frame'))]
    all_boards = [] 
    all_lengths = []  
    all_puzzles = []       
    for index, selection in enumerate(items):
        obj.debug = False
        obj.select_list(test=True, select=selection)   
        obj.puzzle = selection
        if len(obj.solution) == 70:
            [obj.place_tile(divmod(n, obj.span) ,  int(obj.solution[n * 2: n * 2 + 2]) ) for n in range(obj.span * obj.sizey//3)]
            obj.gui.print_board(obj.board, which=f'{index} {selection}')    
            obj.length_matrix()
            all_boards.append(obj.board.copy())
            all_lengths.append(obj.word_locations.copy())
            all_puzzles.append(selection)
    return all_puzzles, all_boards, all_lengths    
    
if __name__ == '__main__':
  main()


