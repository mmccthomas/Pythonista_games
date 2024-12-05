# test solve of all puzzles in zipword
# test user interaction of one puzzle
import zip_word
from copy import deepcopy
from time import sleep, time
import numpy as np
import gc
obj = None

with open('wordpuzzles.txt') as f:
    words = f.readlines()
names = [word.split('_')[0].replace('-',' ') 
         for word in words 
         if word.endswith('_frame:\n')]

names = names[:10]
for name in reversed(names):    
    
    obj = zip_word.ZipWord(name)   
    t = time()
    obj.run() 
    elapsed = time() - t
    full_squares =  ~np.any(obj.solution_board == ' ')
    print(f'{name}, complete={full_squares}, no_squares={np.sum(np.char.isalpha(obj.solution_board))} in {elapsed:.2f}secs')
    
    if obj is not None:
       obj.gui.gs.view.close()
       sleep(1)
       #obj.gui.v = None
       del obj
       gc.collect()
       

#test placing move 'sandpiper' in puzzle 1
move = [(r,r) for r in range(4,14)]
#obj.process_turn(move, obj.board, test=('sandpiper', 0))


