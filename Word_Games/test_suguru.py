# test solve of all puzzles in zipword
# test user interaction of one puzzle

import Suguru as suguru
from copy import deepcopy
from time import sleep, time
import numpy as np
import gc
obj = None
names = ['Easy', 'Regular', 'Medium', 'Hard', 'Hardest']

obj = suguru.Suguru()   
obj.debug = False
for name in reversed(names): 
    for i in range(3):    
        obj.test = name
        print(f'{name=}, #{i}')
        #obj.initialise_board()
        #obj.sizey, obj.sizex = len(obj.board), len(obj.board[0])    
        #obj.gui.replace_grid(obj.sizey, obj.sizex)
        t = time()
        obj.run() 
        elapsed = time() - t
        print(f'{elapsed=:.1f}sec')
        print(obj.solution_board)
        sleep(1)
    


