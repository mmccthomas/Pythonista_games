# test solve of all puzzles in krossword
# test user interaction of one puzzle
import Krossword
from copy import deepcopy
import numpy as np

obj = Krossword.KrossWord()
obj.gui.clear_numbers()
obj.gui.clear_messages()
obj.load_words_from_file(obj.wordfile)
items = [s.capitalize() for s in obj.word_dict.keys()]
items = [item for item in items if not item.endswith('_frame')]
start_coords = [] 
all_words = []    
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
    all_words.append(obj.wordlist)
    board = [row.replace("'", "") for row in obj.table]
    board = [row.split('/') for row in board]
    board = np.array(board)    
    numbers = np.argwhere(np.char.isnumeric(board))
    coords = [tuple(loc) for loc in numbers]
    start_coords.append(numbers)
    
    obj.print_board()
    
    obj.empty_board = obj.board.copy()
    obj.wordlist_original = deepcopy(obj.wordlist)
    #msg = obj.solve() 
    #print(f'{selection} {msg}')

#test placing move 'sandpiper' in puzzle 1
move = [(r,r) for r in range(4,14)]
obj.process_turn(move, obj.board, test=('sandpiper', 0))
print(len(start_coords))
import matplotlib.pyplot as plt
from collections import Counter
all = [tuple(rc) for item in start_coords for rc in item]
agg = Counter(all)
agg = sorted(dict(agg).items())
pass
xs = [k[0][1] for k in agg]
ys = [-k[0][0] for k in agg]
s = [k[1] for k in agg]

plt.scatter(xs, ys, s=[15*s1 for s1 in s])
[plt.text(x, y, str(i), color="red", fontsize=12) for x, y, i in zip(xs, ys, s)]
plt.show()
wordlist = sorted(list(set(sum([sum(a.values(), []) for a in all_words], []))))

#with open('wordlists/krosswords.txt', 'w') as f:
#  f.write('\n'.join(wordlist[:-1]))
