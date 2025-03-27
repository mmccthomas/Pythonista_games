# test solve of all puzzles in numberword
import NumberWord
from time import time
import numpy as np

obj = None
with open('crossword_templates.txt') as f:
    words = f.readlines()
names = [word.split('_')[0] for word in words if word.endswith(':\n')]

obj = NumberWord.CrossNumbers(names[-1])

for name in reversed(names):
    obj.test = name
    obj.debug = False
    obj.initialise_board()
    obj.sizey, obj.sizex = len(obj.board), len(obj.board[0])
    obj.gui.replace_grid(obj.sizey, obj.sizex)
    t = time()
    obj.run()
    elapsed = time() - t
    full_squares = ~np.any(obj.solution_board == ' ')
    print(
        f'{name}, complete={full_squares}, no_squares={np.sum(np.char.isalpha(obj.solution_board))} in {elapsed:.2f}secs'
    )

