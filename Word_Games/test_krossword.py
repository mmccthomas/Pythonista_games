# test solve of all puzzles in krossword
# test user interaction of one puzzle
import Krossword
from copy import deepcopy

obj = Krossword.KrossWord()
obj.gui.clear_numbers()
obj.gui.clear_messages()
obj.load_words_from_file(obj.wordfile)
items = [s.capitalize() for s in obj.word_dict.keys()]
items = [item for item in items if not item.endswith('_frame')]
      
for selection in reversed(items):
    obj.iteration_counter = 0
    obj.placed = 0    
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

#test placing move 'sandpiper' in puzzle 1
move = [(r,r) for r in range(4,14)]
obj.process_turn(move, obj.board, test=('sandpiper', 0))

