# two algorithms to develop number based puzzles
# first is latin rectangle where each row and column contains number once only
# second is puzzle that contains each number only once, with arithmetic
# operators and totals displayed

import random
import math
import itertools
from time import time
import numpy as np

# this only works for Iterable[Iterable]
def is_latin_rectangle(rows):
    rows = list(rows)
    valid = True
    for row in rows:
        if len(set(row)) < len(row):
            valid = False
    if valid and rows:
        for i, val in enumerate(rows[0]):
            col = [row[i] for row in rows]
            if len(set(col)) < len(col):
                valid = False
                break
    return valid

def is_latin_square(rows):
    return is_latin_rectangle(rows) and len(rows) == len(rows[0])

def latin_square1(items, shuffle=True):
    result = []
    for elems in itertools.permutations(items):
        valid = True
        for i, elem in enumerate(elems):
            orthogonals = [x[i] for x in result] + [elem]
            if len(set(orthogonals)) < len(orthogonals):
                valid = False
                break
        if valid:
            result.append(elems)
    if shuffle:
        random.shuffle(result)
    return result
    
def evaluate(expression):
   str1 = ''.join(expression[0:3])
   tmp = eval(str1)
   expr2 = str(tmp)+ ''.join(expression[3:])
   return eval(expr2)

def apply_operators(square):  
    valid= True
    operators = ['+', '-', '*', '/']
    sq = square.copy()
    locs = np.argwhere(sq=='0')
    while True:       
        for loc in  locs:
            if loc[0]<3 or loc[1]<3:
              square[tuple(loc)]= random.choice(operators[:2])
            else:
              square[tuple(loc)]= random.choice(operators)
        print(square)
        expressions = []
        for i in range(0,5, 2):
           expressions.append(square[:,i])
           expressions.append(square[i,:])
        for expression in expressions:
          val = evaluate(expression)
          #print(val, end=' ')
          if val != int(val) or val <= 0:
            valid = False         
            break  
        print()   
        if valid:
          break   
    return square
    
def values(square, direction=0):
    expressions = []
    for i in range(0,2*N-1, 2):
      if direction == 0:
        expressions.append(square[i,:])
      else:
        expressions.append(square[:,i])
    return expressions
    
def operators(N, square, add_only=True):
   # compute possibble operators between values
   # place 0 as placeholder for operators
   op_dict = {'+': '__add__', '-': '__sub__', '*': '__mul__', '/': '__floordiv__'}
   
   def _left():
        return int(square[j, i-1])
   def _right():
       return int(square[j, i+1])
        
   for axis in [0,1]:
        square = np.insert(square, list(range(1,N)), '0', axis=axis)
   # place # as blocking value
   square[1::2,1::2] = '#' 
   
   locs = np.argwhere(square=='0')      
   
   if add_only:
      # use only pluses
      for loc in  locs:
          square[tuple(loc)] = '+'
   else:       
       totals = np.zeros((2, 2*N), dtype='U3')
       # deal with rows, columns
       for dirn in [0, 1]:
           # transposing is easiest way to flip rows, columns
           if dirn: 
               square=np.transpose(square)
           for j in range(0,2*N-1,2):
               for i in range(1, 2*N-1,2):
                   if i == 1:
                       value = _left()
                   # only allow subtract if result is positive
                   if value > _right():
                       op = random.choice(['+', '-'])
                   else:
                       op = '+'
                   # last operator
                   if i >= square.shape[0]-2:
                    #last one +,-,*,/
                     if value > _right():
                         op = random.choice(['+', '-', '*'])                        
                         if value % _right() == 0: # result is integer
                             # prefer divide and mult
                             op = random.choices(['+', '-', '*', '/'], weights=[1,1,2,3], k=1)[0]
                     else:
                         op = random.choice(['+', '*'])
                   # a.fn(b) where fn is __add__, etc
                   value = getattr(value, op_dict[op])(_right())
                   square[(j, i)] = op         
                   totals[(dirn, j)] = value
       # restore original orientation            
       square=np.transpose(square)
   # string array, 2d array of totals for rows, then columns
   return square, totals
   
def add_result(N,square, results):    
    # create larger array for disply thay include equals signs
    # and totals 
    display = np.zeros((2*N+1, 2*N+1), dtype='U3')
    display[:2*N-1, :2*N-1]=square
    for j, res_line in enumerate(results):
        if j > 0: 
            display=np.transpose(display)
        for i, val in enumerate(res_line):
            display[i, -1] = val
            display[i,-2] = '=' if i % 2 == 0 else ' '
        display[1::2,-1] = '#' 
    display=np.transpose(display)    
    return display

def create_empty(display):
    # remove numbers, leaving operators and totals
    blank = np.char.isnumeric(display)
    blank[:,-1]=False
    blank[-1,:] = False
    empty = np.copy(display)
    empty[blank] = ' '
    return empty

def main():
	  
	  # Latin squares
		n = 9
		items = list(range(1, n + 1))
		# shuffle items
		random.shuffle(items)              
		t=time()
		print('Latin square')
		rows1 = np.array(latin_square1(items, True))
		#for row in rows1:
		print(rows1)
		# print(is_latin_square(rows1))
		print(time()-t)
		
		# Generate grid using operators and totals
		N = 3
		print()
		t=time()
		print('Arithmetic puzzle')
		for _ in range(1):
		    items = list(range(1, N*N + 1))
		    # shuffle items
		    random.shuffle(items)
		    square = np.array(items).reshape(N,N).astype('U2')
		    square, val = operators(N, square, add_only=False)
		    display = add_result(N, square, val)
		    print(display)    
		    print('numbers removed')
		    print(create_empty(display))
		    
		print(time()-t)
		
if __name__ == '__main__':
	  main()






