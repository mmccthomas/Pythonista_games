import random
import string

def place_word(board, word, coords, max_iteration=500, space='-'):
    # Randomly choose orientation: 0=horizontal, 1=vertical, 2=diagonal
    orientation = random.randint(0, 3)
    # helper to improve readability
    def start(offset):
      ''' random number'''
      x = len(board)- offset
      return  random.randint(0, x)
      
    def _range(x, dirn=1):
      if isinstance(x, tuple):
        return enumerate(zip(range(x[0], x[0]+len(word)),     
                             range(x[1], x[1]+len(word))))
      else:        
       return enumerate(range(x, x+len(word)))
       
    placed = False
    original_word = ''.join(word)
    coords[original_word] = []
    iteration = 0
    while not placed:
        iteration += 1
        if iteration >= max_iteration:
          break
        if len(original_word) + 1 >= len(board) -1:
          break # too long
        if orientation == 0:  # Horizontal
            row = start(1)
            col = start(len(word))
            reverse = random.choice([True, False])
            if reverse:
                word = word[::-1]
            space_available = all(board[row][c] == space or 
              board[row][c] == word[i] 
                for i, c in _range(col))
            if space_available:
                for i, c in _range(col):
                    board[row][c] = word[i]
                    coords[original_word].append((row,c))
                placed = True

        elif orientation == 1:  # Vertical
            row = start(len(word))
            col = start(1)
            reverse = random.choice([True, False])
            if reverse:
                word = word[::-1]
            space_available = all(board[r][col] == space or 
                board[r][col] == word[i] 
                  for i, r in _range(row))
            if space_available:
                for i, r in _range(row):
                    board[r][col] = word[i]
                    coords[original_word].append((r,col))
                placed = True

        elif orientation == 2:  # Diagonal top-left to bottom right
            row = start(len(word))
            col = start(len(word))
            reverse = random.choice([True, False])
            if reverse:
                word = word[::-1]
            space_available = all(board[r][c] == space or 
                board[r][c] == word[i] 
                  for i, (r, c) in _range((row, col)))
            if space_available:
                for i, (r, c) in  _range((row, col)):
                    board[r][c] = word[i]
                    coords[original_word].append((r,c))
                placed = True
                
        elif orientation == 3:  # Diagonal bottom-left to top-right
            row = random.randint(len(word) +1, len(board)-1)
            col = start(len(word))
            reverse = random.choice([True, False])
            if reverse:
                word = word[::-1]
            space_available = all(board[r][c] == space or 
                board[r][c] == word[i] 
                  for i, (r, c) in enumerate(zip(range(row, row-len(word), -1),
                                                 range(col, col+len(word)))))
            if space_available:
                for i, (r, c) in enumerate(zip(range(row, row-len(word), -1), 
                                               range(col, col+len(word)))):
                    board[r][c] = word[i]
                    coords[original_word].append((r,c))
                placed = True
    return placed, coords

def fill_empty(board):
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] == '-':
                board[row][col] = random.choice(string.ascii_lowercase)

def create_word_search(words, size=15):
    board = [['-' for _ in range(size)] for _ in range(size)]  
    words_placed = []
    coords ={} 
    for word in words:
      w= word.replace(' ','')
      success, coord = place_word(board,w,coords,max_iteration=500)
      if success:
        words_placed.append(word)

    fill_empty(board)

    return board, words_placed, coords

def display_board(board):
    for row in board:
        print(' '.join(row))



import random
  #for key in all_words:
  # words = all_words[key]
  #board = create_word_search(words)
  #display_board(board)
  # print(words)
