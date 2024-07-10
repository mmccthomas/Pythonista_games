#
# The Chess AI class
# Will utilize minimax and alpha beta pruning
#
# Author: Boo Sung Kim
# Note: Code inspired from the pseudocode by Sebastian Lague
# TODO: switch undo moves to stack data structure
import chess_engine
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from gui.gui_interface import Coord

COORDS = [Coord((r,c)) for r in range(8) for c in range(8)]


class chess_ai:
    '''
    call minimax with alpha beta pruning
    evaluate board
    get the value of each piece
    '''
    def __init__(self, Player):
      self.Player= Player
      self.piece_values ={ "k": 1000, "q": 100, "r": 50, "b": 30, "n": 30, "p": 10}
      #self.minmax_control =[(self.Player.PLAYER_1,"black", "white" ,"white", "black")]
    
    
    def minimax(self, game_state, depth, alpha, beta, maximizing_player, player_color):
    
        # 0 if white lost, 1 if black lost, 2 if stalemate, 3 if not game over
        csc_lookup = {
            (True, 0): 5000000,
            (True, 1): -5000000,
            (True, 2): 100,
            (False, 1): 5000000,
            (False, 0): -5000000,
            (False, 2): 100
        }
        opposite = 'black' if player_color == 'white' else 'white'
        
        csc = game_state.checkmate_stalemate_checker()
        if (maximizing_player, csc) in csc_lookup:
            return csc_lookup[(maximizing_player, csc)]
        if depth <= 0 or csc != 3:
            return self.evaluate_board(game_state, player_color)
            
        if maximizing_player:
            max_evaluation = -10000000
            all_possible_moves = game_state.get_all_legal_moves(opposite)
            for start, end in all_possible_moves:
                game_state.move_piece(start, end, is_ai=True)
                evaluation = self.minimax(game_state, depth - 1, alpha, beta, False, player_color)
                game_state.undo_move()

                if max_evaluation < evaluation:
                    max_evaluation = evaluation
                    best_possible_move = (start, end)
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            if depth == 3:
                return best_possible_move
            else:
                return max_evaluation
        else:
            min_evaluation = 10000000
            all_possible_moves = game_state.get_all_legal_moves(player_color)
            for start, end in all_possible_moves:
                game_state.move_piece(start, end, is_ai=True)
                evaluation = self.minimax(game_state, depth - 1, alpha, beta, True, opposite)
                game_state.undo_move()

                if min_evaluation > evaluation:
                    min_evaluation = evaluation
                    best_possible_move = (start, end)
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            if depth == 3:
                return best_possible_move
            else:
                return min_evaluation    
                

    def evaluate_board(self, game_state, player):
        evaluation_score = 0
        for coord in COORDS:
            if game_state.is_valid_piece(coord):
                  evaluated_piece = game_state.get_piece(coord)
                  evaluation_score += self.get_piece_value(evaluated_piece, player)
        return evaluation_score

    def get_piece_value(self, piece, player):
      
      if player is self.Player.PLAYER_1 and piece.is_player("black") or \
         player is self.Player.PLAYER_2 and piece.is_player("white")  :
         return  self.piece_values[piece.get_name()]  
      else:
          return  -1 * self.piece_values[piece.get_name()]

