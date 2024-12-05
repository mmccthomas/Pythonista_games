# test solve of all puzzles in numberword
# test user interaction of one puzzle
import NumberWord
from copy import deepcopy
from time import sleep, time
import gc

obj = None
with open('crossword_templates.txt') as f:
    words = f.readlines()
names = [word.split('_')[0]for word in words if word.endswith(':\n')]

names = names[:20]
for name in reversed(names):
    
    
    obj = NumberWord.CrossNumbers(name)   
    t = time()
    obj.run() 
    elapsed = time() - t
    full_squares =  ~np.any(obj.solution_board == ' ')
    print(f'{name}, complete={full_squares}, no_squares={np.sum(np.char.isalpha(obj.solution_board))} in {elapsed:.2f}secs')
    
    if obj is not None:
       obj.gui.v.close()
       del obj
       sleep(.5)
       gc.collect()

#test placing move 'sandpiper' in puzzle 1
move = [(r,r) for r in range(4,14)]
#obj.process_turn(move, obj.board, test=('sandpiper', 0))



