# produced by Gemini AI
# Othello with Minimax AI
# This script implements the game of Othello (also known as Reversi)
# with a human player and an AI opponent. The AI uses the Minimax algorithm
# with Alpha-Beta Pruning for efficient decision-making.
import os
import sys
import copy
import time
import ui
from datetime import datetime
from queue import Queue
import traceback
import random
import numpy as np
import dialogs
import base_path
base_path.add_paths(__file__)
from gui_interface import Gui


class Player():
  def __init__(self):
    self.PLAYER_1 = 1
    self.PLAYER_2 = 2
    self.EMPTY = 0
    self.PLAYERS = [self.PLAYER_1, self.PLAYER_2]
    self.PIECES = {2:'emj:White_Circle', 1:'emj:Black_Circle'}
    self.PIECE_NAMES = {BLACK: 'Black', WHITE: 'White'}



# ################################################################################################
# produced by Gemini AI
# Othello with Minimax AI
# This script implements the game of Othello (also known as Reversi)
# with a human player and an AI opponent. The AI uses the Minimax algorithm
# with Alpha-Beta Pruning for efficient decision-making.

# --- Game Constants ---
BOARD_SIZE = 8  # 8-12
EMPTY = 0
BLACK = 1
WHITE = 2
PLAYER_SYMBOLS = {EMPTY: ' ', BLACK: '*', WHITE: 'o'}

# Directions to check for valid moves (8 directions: horizontal, vertical, diagonal)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1), (1, 0), (1, 1)
    ]

# --- Board and Game State Functions ---

def create_board():
    """Initializes and returns the starting Othello board."""
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    # Set up the initial four pieces
    board[BOARD_SIZE//2-1][BOARD_SIZE//2-1] = WHITE
    board[BOARD_SIZE//2 -1][BOARD_SIZE//2] = BLACK
    board[BOARD_SIZE//2][BOARD_SIZE//2 -1] = BLACK
    board[BOARD_SIZE//2][BOARD_SIZE//2] = WHITE
    return board

def print_board(board):
    """Prints the current state of the board to the console."""
    print("  " + " ".join([str(i) for i in range(BOARD_SIZE)]))
    print("  " + "-" * (BOARD_SIZE * 2 - 1))
    for row_idx, row in enumerate(board):
        row_str = " ".join([PLAYER_SYMBOLS[piece] for piece in row])
        print(f"{row_idx}|{row_str}|")
    print("  " + "-" * (BOARD_SIZE * 2 - 1))
    print()

def get_valid_moves(board, player):
    """
    Finds all valid moves for the given player.
    Returns a list of tuples (row, col).
    """
    valid_moves = []
    opponent = WHITE if player == BLACK else BLACK

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == EMPTY:
                for dr, dc in DIRECTIONS:
                    r, c = row + dr, col + dc
                    # Check if the move is within the board and next to an opponent's piece
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == opponent:
                        # Check for a line of opponent pieces
                        r += dr
                        c += dc
                        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == opponent:
                            r += dr
                            c += dc
                        # If the line ends with the player's piece, it's a valid move
                        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                            if (row, col) not in valid_moves:
                                valid_moves.append((row, col))
    return valid_moves

def make_move(board, player, move):
    """
    Makes a move on the board for the given player.
    Assumes the move is valid and updates the board in place.
    """
    row, col = move
    board[row][col] = player
    opponent = WHITE if player == BLACK else BLACK
    
    # Flip the opponent's pieces
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        pieces_to_flip = []
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == opponent:
            pieces_to_flip.append((r, c))
            r += dr
            c += dc
        
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
            for r_flip, c_flip in pieces_to_flip:
                board[r_flip][c_flip] = player

def is_game_over(board):
    """Checks if the game has ended (no valid moves for either player)."""
    return not get_valid_moves(board, BLACK) and not get_valid_moves(board, WHITE)

def get_score(board):
    """Calculates and returns the score for Black and White."""
    black_score = sum(row.count(BLACK) for row in board)
    white_score = sum(row.count(WHITE) for row in board)
    return black_score, white_score

# --- Minimax AI with Alpha-Beta Pruning ---

# A static board evaluation table. Corner positions are highly valuable.
# This helps the AI make smarter, more strategic moves.
BOARD_WEIGHTS = {8:[
    [20, -3, 11,  8,  8, 11, -3, 20],
    [-3, -7, -4,  1,  1, -4, -7, -3],
    [11, -4,  2,  2,  2,  2, -4, 11],
    [ 8,  1,  2, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3,  2,  1,  8],
    [11, -4,  2,  2,  2,  2, -4, 11],
    [-3, -7, -4,  1,  1, -4, -7, -3],
    [20, -3, 11,  8,  8, 11, -3, 20]],
9: [
    [20, -3, 11,  8,  8,  8, 11, -3, 20],
    [-3, -7, -4,  1,  1,  1, -4, -7, -3],
    [11, -4,  2,  2,  2,  2,  2, -4, 11],
    [ 8,  1,  2, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3,  2,  1,  8],
    [11, -4,  2,  2,  2,  2,  2, -4, 11],
    [-3, -7, -4,  1,  1,  1, -4, -7, -3],
    [20, -3, 11,  8,  8,  8, 11, -3, 20]], 
10 : [
    [20, -3, 11,  8,  8,  8,  8, 11, -3, 20],
    [-3, -7, -4,  1,  1,  1,  1, -4, -7, -3],
    [11, -4,  2,  2,  2,  2,  2,  2, -4, 11],
    [ 8,  1,  2,  2,  2,  2,  2,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2,  2,  2,  2,  2,  2,  1,  8],
    [11, -4,  2,  2,  2,  2,  2,  2, -4, 11],
    [-3, -7, -4,  1,  1,  1,  1, -4, -7, -3],
    [20, -3, 11,  8,  8,  8,  8, 11, -3, 20]],
11: [
    [20, -3, 11,  8,  8,  8,  8,  8, 11, -3, 20],
    [-3, -7, -4,  1,  1,  1,  1,  1, -4, -7, -3],
    [11, -4,  2,  2,  2,  2,  2,  2,  2, -4, 11],
    [ 8,  1,  2,  2,  2,  2,  2,  2,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2,  2,  2,  2,  2,  2,  2,  1,  8],
    [11, -4,  2,  2,  2,  2,  2,  2,  2, -4, 11],
    [-3, -7, -4,  1,  1,  1,  1,  1, -4, -7, -3],
    [20, -3, 11,  8,  8,  8,  8,  8, 11, -3, 20]],
12: [
    [20, -3, 11,  8,  8,  8,  8,  8,  8, 11, -3, 20],
    [-3, -7, -4,  1,  1,  1,  1,  1,  1, -4, -7, -3],
    [11, -4,  2,  2,  2,  2,  2,  2,  2,  2, -4, 11],
    [ 8,  1,  2,  2,  2,  2,  2,  2,  2,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2, -3, -3, -3, -3, -3, -3,  2,  1,  8],
    [ 8,  1,  2,  2,  2,  2,  2,  2,  2,  2,  1,  8],
    [11, -4,  2,  2,  2,  2,  2,  2,  2,  2, -4, 11],
    [-3, -7, -4,  1,  1,  1,  1,  1,  1, -4, -7, -3],
    [20, -3, 11,  8,  8,  8,  8,  8,  8, 11, -3, 20]]}


def evaluate_board(board, player, opponent):
    """
    Evaluates the board's state for the AI player.
    Uses a weighted board heuristic.
    """
    score = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == player:
                score += BOARD_WEIGHTS[BOARD_SIZE][row][col]
            elif board[row][col] == opponent:
                score -= BOARD_WEIGHTS[BOARD_SIZE][row][col]
    return score

def minimax(board, depth, is_maximizing_player, player, opponent, alpha=-sys.maxsize, beta=sys.maxsize):
    """
    The Minimax algorithm with Alpha-Beta Pruning.
    Returns the optimal score for the current state.
    """
    # Base case: if max depth is reached or game is over, evaluate the board
    if depth == 0 or is_game_over(board):
        return evaluate_board(board, player, opponent)

    valid_moves = get_valid_moves(board, player if is_maximizing_player else opponent)

    if is_maximizing_player:
        max_eval = -sys.maxsize
        for move in valid_moves:
            new_board = copy.deepcopy(board)
            make_move(new_board, player, move)
            eval = minimax(new_board, depth - 1, False, player, opponent, alpha, beta)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break # Alpha-Beta Pruning
        return max_eval
    else: # Minimizing player
        min_eval = sys.maxsize
        for move in valid_moves:
            new_board = copy.deepcopy(board)
            make_move(new_board, opponent, move)
            eval = minimax(new_board, depth - 1, True, player, opponent, alpha, beta)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break # Alpha-Beta Pruning
        return min_eval

def get_best_move(board, player, depth):
    """
    Calculates and returns the best move for the AI using Minimax.
    """
    best_move = None
    max_eval = -sys.maxsize
    opponent = WHITE if player == BLACK else BLACK
    
    valid_moves = get_valid_moves(board, player)
    
    if not valid_moves:
        return None

    for move in valid_moves:
        new_board = copy.deepcopy(board)
        make_move(new_board, player, move)
        eval = minimax(new_board, depth - 1, False, player, opponent, -sys.maxsize, sys.maxsize)
        if eval > max_eval:
            max_eval = eval
            best_move = move
    
    return best_move
    
@ui.in_background
def alert(msg):
    dialogs.hud_alert(msg)
    
# --- Main Game Loop ---
def play_game():
    global BOARD_SIZE
    """Main function to run the Othello game."""
    BOARD_SIZE = dialogs.list_dialog('select size(default 8)', list(range(8,13)))
    if BOARD_SIZE is None:
       BOARD_SIZE = 8    
    board = create_board()
    
    # boiler plate to create gui as recipient for board array
    gui = Gui(board, Player())
    gui.setup_gui()
    q = Queue()
    gui.q = gui.gs.q = q  # pass queue into gui
    gui.replace_labels('row', list(range(0,BOARD_SIZE)))
    gui.replace_labels('col', list(range(0,BOARD_SIZE)))
    # menus can be controlled by dictionary of labels and functions without parameters
    gui.gs.pause_menu = {
              'Continue': gui.gs.dismiss_modal_scene,
              'Quit': gui.gs.close}
    gui.gs.start_menu = {'New Game': play_game, 'Quit': gui.gs.close}
    gui.clear_messages()
    
    
    current_player = BLACK
    ai_player = WHITE
    ai_depth = 4 # Adjust this for AI difficulty

    black_score, white_score = get_score(board)
    
    # game loop
    while not is_game_over(board):        
        valid_moves = get_valid_moves(board, current_player)
        black_score, white_score = get_score(board)
        
        gui.update(board)        
        # show score on gui
        gui.set_moves(f"Black: {black_score}\nWhite: {white_score}")    
        gui.valid_moves(valid_moves, message=False)
        if not valid_moves:
            gui.set_prompt(f"Player {PLAYER_SYMBOLS[current_player]} has no valid moves. Passing turn...")
            current_player = BLACK if current_player == WHITE else WHITE
            continue
        
        if current_player == BLACK:
            # Human player's turn
            gui.set_top(f"Your turn (BLACK)")                        
            while True:
                # wait for touch
                rc = gui.get_move()                                
                if rc in valid_moves:
                    make_move(board, current_player, rc)
                    gui.set_prompt('')
                    break                
        else:
            # AI player's turn
            gui.set_top(f"AI's turn (WHITE). Thinking...")
            time.sleep(random.random()) # just for effect
            move = get_best_move(board, ai_player, ai_depth)            
            if move:
                gui.set_prompt(f"AI moves to {move}.")
                make_move(board, ai_player, move)
            else:
                alert("AI has no valid moves. Passing turn...")
        
        # Switch turns
        current_player = BLACK if current_player == WHITE else WHITE

    # --- Game Over ---
    prompt = "--- Game Over! ---\n"
    # print_board(board)
    black_score, white_score = get_score(board)
    gui.set_prompt(f"Final Score: Black: {black_score}, White: {white_score}")

    if black_score > white_score:
        alert(f'{prompt}You win!')
    elif white_score > black_score:
        alert(f'{prompt}The AI wins!')
    else:
        alert(f"{prompt}It's a tie!")

if __name__ == "__main__":
    play_game()
