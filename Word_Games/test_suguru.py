# test solve of all puzzles in zipword
# test user interaction of one puzzle

import Suguru as suguru
from copy import deepcopy
from time import sleep, time
import numpy as np
import gc
obj = None
names = ['Easy', 'Guardian', 'Medium']

obj = suguru.Suguru()   
obj.debug = False
for name in names: 
    for _ in range(3):    
        obj.test = name
        #obj.initialise_board()
        #obj.sizey, obj.sizex = len(obj.board), len(obj.board[0])    
        #obj.gui.replace_grid(obj.sizey, obj.sizex)
        t = time()
        obj.run() 
        elapsed = time() - t
        
        print(obj.solution_board)
        sleep(1)
    


