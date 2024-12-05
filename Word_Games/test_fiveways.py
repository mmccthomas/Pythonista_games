# test solve of all puzzles in fiveways
# test user interaction of one puzzle
import Fiveways
from copy import deepcopy

obj = Fiveways.FiveWays()
obj.gui.clear_numbers()
obj.gui.clear_messages()
obj.load_words_from_file(obj.wordfile)
items = [s.capitalize() for s in obj.word_dict.keys()]
items = [item for item in items if not item.endswith('_frame')]
      
for selection in reversed(items):
    obj.iteration_counter = 0
    obj.placed = 0    
    obj.strikethru = False
    obj.puzzle = selection
    obj.wordlist = obj.word_dict[selection]
    if selection + '_frame' in obj.word_dict:
         obj.table = obj.word_dict[selection + '_frame']
         obj.wordlist = [word.lower() for word in obj.wordlist]          
         obj.selection = selection
    obj.initialise_board()
    obj.print_board()
    obj.empty_board = obj.board.copy()
    obj.wordlist_original = deepcopy(obj.wordlist)
    msg = obj.solve() 
    print(f'{selection} {msg}')

#test placing move 'matchstick' in puzzle 1 at row 9
move = [(9,r) for r in range(9, -2, -1)]
obj.process_turn(move, obj.board, test=('matchstick', 1))
assert 'matchstick' not in obj.wordlist[None]
