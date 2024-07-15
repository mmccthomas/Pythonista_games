#
# The Chess Board class
# Will store the state of the chess game, print the chess board, find valid moves, store move logs.
#
# Note: move log class inspired by Eddie Sharick
#

from rook import Rook
from knight import Knight
from bishop import Bishop
from pawn import Pawn
from queen import Queen
from king import King
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from gui.gui_interface import Coord
from types import SimpleNamespace

COORDS = [Coord((r,c)) for r in range(8) for c in range(8)]



'''
r \ c     0           1           2           3           4           5           6           7 
0   [(r=0, c=0), (r=0, c=1), (r=0, c=2), (r=0, c=3), (r=0, c=4), (r=0, c=5), (r=0, c=6), (r=0, c=7)]
1   [(r=1, c=0), (r=1, c=1), (r=1, c=2), (r=1, c=3), (r=1, c=4), (r=1, c=5), (r=1, c=6), (r=1, c=7)]
2   [(r=2, c=0), (r=2, c=1), (r=2, c=2), (r=2, c=3), (r=2, c=4), (r=2, c=5), (r=2, c=6), (r=2, c=7)]
3   [(r=3, c=0), (r=3, c=1), (r=3, c=2), (r=3, c=3), (r=3, c=4), (r=3, c=5), (r=3, c=6), (r=3, c=7)]
4   [(r=4, c=0), (r=4, c=1), (r=4, c=2), (r=4, c=3), (r=4, c=4), (r=4, c=5), (r=4, c=6), (r=4, c=7)]
5   [(r=5, c=0), (r=5, c=1), (r=5, c=2), (r=5, c=3), (r=5, c=4), (r=5, c=5), (r=5, c=6), (r=5, c=7)]
6   [(r=6, c=0), (r=6, c=1), (r=6, c=2), (r=6, c=3), (r=6, c=4), (r=6, c=5), (r=6, c=6), (r=6, c=7)]
7   [(r=7, c=0), (r=7, c=1), (r=7, c=2), (r=7, c=3), (r=7, c=4), (r=7, c=5), (r=7, c=6), (r=7, c=7)]
'''


# TODO: stalemate
# TODO: move logs - fix king castle boolean update
# TODO: change move method argument about is_ai into something more elegant
class game_state:
    # Initialize 2D array to represent the chess board
    def __init__(self, Player):
        # The board is a 2D array
        self.move_log = []
        self.Player = Player
        self.white_turn = True
        self.valid_moves = {}
        self.EMPTY = self.Player.EMPTY
        self.P1 = self.Player.PLAYER_1
        self.P2 = self.Player.PLAYER_2
        self.can_en_passant_bool = False
        self._en_passant_previous = (-1, -1)

        self.checkmate = False
        self.stalemate = False
        self._is_check = False

        # TODO: REMOVE THESE TWO LATER
        self._white_king_location = Coord((0, 3))
        self._black_king_location = Coord((7, 3))

        # Has king not moved, has Rook1(col=0) not moved, has Rook2(col=7) not moved
        self.white_king_can_castle = [True, True, True]  
        self.black_king_can_castle = [True, True, True]

        # Initialize White pieces
        white_rook_1 = Rook('r', 0, 0, self.P1)
        white_rook_2 = Rook('r', 0, 7, self.P1)
        white_knight_1 = Knight('n', 0, 1, self.P1)
        white_knight_2 = Knight('n', 0, 6, self.P1)
        white_bishop_1 = Bishop('b', 0, 2, self.P1)
        white_bishop_2 = Bishop('b', 0, 5, self.P1)
        white_queen = Queen('q', 0, 4, self.P1)
        white_king = King('k', 0, 3, self.P1)
        white_pawn_1 = Pawn('p', 1, 0, self.P1)
        white_pawn_2 = Pawn('p', 1, 1, self.P1)
        white_pawn_3 = Pawn('p', 1, 2, self.P1)
        white_pawn_4 = Pawn('p', 1, 3, self.P1)
        white_pawn_5 = Pawn('p', 1, 4, self.P1)
        white_pawn_6 = Pawn('p', 1, 5, self.P1)
        white_pawn_7 = Pawn('p', 1, 6, self.P1)
        white_pawn_8 = Pawn('p', 1, 7, self.P1)

        # Initialize Black Pieces
        black_rook_1 = Rook('r', 7, 0, self.P2)
        black_rook_2 = Rook('r', 7, 7, self.P2)
        black_knight_1 = Knight('n', 7, 1, self.P2)
        black_knight_2 = Knight('n', 7, 6, self.P2)
        black_bishop_1 = Bishop('b', 7, 2, self.P2)
        black_bishop_2 = Bishop('b', 7, 5, self.P2)
        black_queen = Queen('q', 7, 4, self.P2)
        black_king = King('k', 7, 3, self.P2)
        black_pawn_1 = Pawn('p', 6, 0, self.P2)
        black_pawn_2 = Pawn('p', 6, 1, self.P2)
        black_pawn_3 = Pawn('p', 6, 2, self.P2)
        black_pawn_4 = Pawn('p', 6, 3, self.P2)
        black_pawn_5 = Pawn('p', 6, 4, self.P2)
        black_pawn_6 = Pawn('p', 6, 5, self.P2)
        black_pawn_7 = Pawn('p', 6, 6, self.P2)
        black_pawn_8 = Pawn('p', 6, 7, self.P2)

        self.board = [
            [white_rook_1, white_knight_1, white_bishop_1, white_king, white_queen, white_bishop_2, white_knight_2,
             white_rook_2],
            [white_pawn_1, white_pawn_2, white_pawn_3, white_pawn_4, white_pawn_5, white_pawn_6, white_pawn_7,
             white_pawn_8],
            [self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY,
             self.EMPTY],
            [self.EMPTY, self.EMPTY, Player.EMPTY, self.EMPTY, Player.EMPTY, self.EMPTY, self.EMPTY,
             self.EMPTY],
            [self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY,
             self.EMPTY],
            [self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.Player.EMPTY, self.EMPTY,
             self.EMPTY],
            [black_pawn_1, black_pawn_2, black_pawn_3, black_pawn_4, black_pawn_5, black_pawn_6, black_pawn_7,
             black_pawn_8],
            [black_rook_1, black_knight_1, black_bishop_1, black_king, black_queen, black_bishop_2, black_knight_2,
             black_rook_2]
        ]
        
    def whose_turn(self):
        # true if white, false if black
        return self.white_turn    
             
    def get_board_rc(self, coord, board=None):
        r, c = coord
        if board is None:      
            return self.board[r][c]
        else:
            return board[r][c]
          
    def set_board_rc(self, coord, val, board=None):
        r, c = coord
        if board is None:      
            self.board[r][c] = val
        else:
            board[r][c] = val  
              
    def board_print(self):       
      for r in range(8):
        for c in range(8):
          piece = self.get_piece((r, c))
          if piece is not None and piece != self.EMPTY:
            print(f"{piece.player[0]}{piece.name}", end=" ")
          else:
            print('..', end=" ")
        print()
      print()
      
    def get_piece(self, coord, col=None):
        if isinstance(coord, tuple):         
            row, col = coord
        else:
            row = coord            
        if 0 <= row < 8 and 0 <= col < 8:
            return self.get_board_rc((row, col))
        else:
            return None
            
    def check_in_board(self, coord):
        r, c = coord
        return (0 <= r < 8) and (0 <= c < 8)

    def is_valid_piece(self, coord, col=None):
        if isinstance(coord, tuple):         
            row, col = coord
        elif isinstance(coord, Coord):
            row, col = coord.r, coord.c
        else:
            row = coord
        evaluated_piece = self.get_piece((row, col))
        return evaluated_piece is not None and evaluated_piece != self.EMPTY

    def get_valid_moves(self, starting_square):
        '''
        remove pins from valid moves (unless the pinned piece move can get rid of a check and checks is empty
        remove move from valid moves if the move falls within a check piece's valid move
        if the moving piece is a king, the ending square cannot be in a check
        '''
        if not isinstance( starting_square, Coord):
            current = Coord(starting_square)
        else:
            current = starting_square
        #print('valid', self.is_valid_piece(current))
        if self.is_valid_piece(current):
            #print('valid piece', current)
            valid_moves = []
            moving_piece = self.get_piece(current)
            if self.get_piece(current).is_player(self.P1):
                king_location = self._white_king_location
            else:
                king_location = self._black_king_location 
            checking_pieces, pinned_pieces, pinned_checks = self.check_for_check(king_location, moving_piece.get_player())
            initial_valid_piece_moves = moving_piece.get_valid_piece_moves(self)
            
            # immediate check
            if checking_pieces:
                for move in initial_valid_piece_moves:
                    can_move = True
                    for piece in checking_pieces:
                        if moving_piece.get_name() == "k":
                            temp = self.get_board_rc(current)
                            self.set_board_rc(current, self.EMPTY)
                            temp2 = self.get_board_rc(move)
                            self.set_board_rc(move, temp)
                            if not self.check_for_check(move, moving_piece.get_player())[0]:
                                pass
                            else:
                                can_move = False
                            self.set_board_rc(current, temp)
                            self.set_board_rc(move, temp2)                            
                        elif all((move == piece, len(checking_pieces) == 1, 
                                 moving_piece.get_name() != "k",  current not in pinned_pieces)):
                            pass
                        elif all((move != piece, len(checking_pieces) == 1, 
                                 moving_piece.get_name() != "k",  current not in pinned_pieces)):
                            temp = self.get_board_rc(move)
                            self.set_board_rc(move, moving_piece)
                            self.set_board_rc(current, self.EMPTY)                          
                            if self.check_for_check(king_location, moving_piece.get_player())[0]:
                                can_move = False
                            self.set_board_rc(current, moving_piece)                       
                            self.set_board_rc(move, temp)                  
                        else:
                            can_move = False
                    if can_move:
                        valid_moves.append(move)
                self._is_check = True
            # pinned checks
            elif pinned_pieces and moving_piece.get_name() != "k":
                if starting_square not in pinned_pieces:
                    for move in initial_valid_piece_moves:           
                        valid_moves.append(move)
                elif starting_square in pinned_pieces:
                    for move in initial_valid_piece_moves:
                        temp = self.get_board_rc(move)
                        self.set_board_rc(move, moving_piece)                       
                        self.set_board_rc(current, self.EMPTY)                      
                        if not self.check_for_check(Coord(king_location), moving_piece.get_player())[0]:
                            valid_moves.append(move)
                        self.set_board_rc(current, moving_piece)                      
                        self.set_board_rc(move, temp)                        
            else:
                if moving_piece.get_name() == "k":
                    for move in initial_valid_piece_moves:
                        temp = self.get_board_rc(current)                   
                        temp2 = self.get_board_rc(move)
                        self.set_board_rc(current, self.EMPTY)                       
                        self.set_board_rc(move, temp)                        
                        if not self.check_for_check(Coord(move), moving_piece.get_player())[0]:
                            valid_moves.append(move)
                        self.set_board_rc(current, temp)                        
                        self.set_board_rc(move, temp2)                       
                else:
                    for move in initial_valid_piece_moves:
                        valid_moves.append(move)
            # if not valid_moves:
            #     if self._is_check:
            #         self.checkmate = True
            #     else:
            #         self.stalemate = True
            # else:
            #     self.checkmate = False
            #     self.stalemate = False
            return valid_moves
        else:
            return None

    
    def checkmate_stalemate_checker(self):
        # 0 if white lost, 1 if black lost, 2 if stalemate, 3 if not game over
        all_white_moves = self.get_all_legal_moves(self.P1)
        all_black_moves = self.get_all_legal_moves(self.P2)
        if self._is_check and self.whose_turn() and not all_white_moves:
            print("white lost")
            return 0 # white lost
        elif self._is_check and not self.whose_turn() and not all_black_moves:
            print("black lost")
            return 1 # black lost
        elif not all_white_moves and not all_black_moves:
            return 2 # stalemate
        else:
            return 3 # game continues

    def get_all_legal_moves(self, player):
        _all_valid_moves = []
        for coord in COORDS:
            if self.is_valid_piece(coord) and self.get_piece(coord).is_player(player):
                valid_moves = self.get_valid_moves(coord)
                for move in valid_moves:
                    _all_valid_moves.append((coord, move))
        return _all_valid_moves

    def king_can_castle_left(self, player):
        if player is self.P1:
            return self.white_king_can_castle[0] and self.white_king_can_castle[1] and \
                   self.get_piece((0, 1)) is self.EMPTY and self.get_piece((0, 2) )is self.EMPTY and not self._is_check
        else:
            return self.black_king_can_castle[0] and self.black_king_can_castle[1] and \
                   self.get_piece((7, 1)) is self.EMPTY and self.get_piece((7, 2)) is self.EMPTY and not self._is_check

    def king_can_castle_right(self, player):
        if player is self.P1:
            return self.white_king_can_castle[0] and self.white_king_can_castle[2] and \
                   self.get_piece((0, 6)) is self.EMPTY and self.get_piece((0, 5) )is self.EMPTY and not self._is_check
        else:
            return self.black_king_can_castle[0] and self.black_king_can_castle[2] and \
                   self.get_piece((7, 6) )is self.EMPTY and self.get_piece((7, 5)) is self.EMPTY and not self._is_check

    def promote_pawn(self, starting_square, moved_piece, ending_square):
        while True:
            new_piece_name = input("Change pawn to (r, n, b, q):\n")
            piece_classes = {"r": Rook, "n": Knight, "b": Bishop, "q": Queen}
            if new_piece_name in piece_classes:
                move = chess_move(starting_square, ending_square, self, self._is_check)

                new_piece = piece_classes[new_piece_name](new_piece_name, ending_square[0],
                                                          ending_square[1], moved_piece.get_player())
                self.set_board_rc(ending_square, new_piece)                                           
                self.board[ending_square[0]][ending_square[1]] = new_piece
                self.board[moved_piece.get_row_number()][moved_piece.get_col_number()] = self.EMPTY
                moved_piece.change_row_number(ending_square[0])
                moved_piece.change_col_number(ending_square[1])
                move.pawn_promotion_move(new_piece)
                self.move_log.append(move)
                break
            else:
                print("Please choose from these four: r, n, b, q.\n")

    def promote_pawn_ai(self, starting_square, moved_piece, ending_square):
        move = chess_move(starting_square, ending_square, self, self._is_check)
        # The ai can only promote the pawn to queen
        new_piece = Queen("q", ending_square[0], ending_square[1], moved_piece.get_player())
        self.set_board_rc(ending_square, new_piece)    
        self.board[moved_piece.get_row_number()][moved_piece.get_col_number()] = self.EMPTY
        moved_piece.change_position(ending_square)
        move.pawn_promotion_move(new_piece)
        self.move_log.append(move)

    # have to fix en passant for ai
    def can_en_passant(self, current_square):
        return False
        # if is_ai:
        #     return False
        # else:
        #     return self.can_en_passant_bool and current_square_row == self.previous_piece_en_passant()[0] \
        #            and abs(current_square_col - self.previous_piece_en_passant()[1]) == 1

    def previous_piece_en_passant(self):
        return self._en_passant_previous
     
    def move_king(self, starting_square, next_square, moving_piece):
        ending_square = next_square
        moved_to_piece = self.get_piece(next_square)
        if moving_piece.is_player(self.P1):                        
             if all((moved_to_piece == self.EMPTY, next_square.c == 1, 
                    self.king_can_castle_left(moving_piece.get_player()))):
                  move = chess_move(starting_square, ending_square, self, self._is_check)
                  move.castling_move((0, 0), (0, 2), self)
                  self.move_log.append(move)

                  # move rook
                  self.get_piece(0, 0).change_col_number(2)

                  self.board[0][2] = self.board[0][0]
                  self.board[0][0] = self.EMPTY

                  self.white_king_can_castle[0] = False
                  self.white_king_can_castle[1] = False
             elif all((moved_to_piece == self.EMPTY, next_square.c == 5, 
                     self.king_can_castle_right(moving_piece.get_player()))):
                  move = chess_move(starting_square, ending_square, self, self._is_check)
                  move.castling_move((0, 7), (0, 4), self)
                  self.move_log.append(move)
                  # move rook
                  self.get_piece(0, 7).change_col_number(4)

                  self.board[0][4] = self.board[0][7]
                  self.board[0][7] = self.EMPTY

                  self.white_king_can_castle[0] = False
                  self.white_king_can_castle[2] = False
             else:
                  move = chess_move(starting_square, ending_square, self, self._is_check)
                  self.move_log.append(move)
                  self.white_king_can_castle[0] = False
                  self._white_king_location = next_square
        else:
             if moved_to_piece == self.EMPTY and next_square.c == 1 and self.king_can_castle_left(
                                moving_piece.get_player()):
                  move = chess_move(starting_square, ending_square, self, self._is_check)
                  move.castling_move((7, 0), (7, 2), self)
                  self.move_log.append(move)

                  self.get_piece(7, 0).change_col_number(2)
                  # move rook
                  self.board[7][2] = self.board[7][0]
                  self.board[7][0] = self.EMPTY

                  self.black_king_can_castle[0] = False
                  self.black_king_can_castle[1] = False
             elif moved_to_piece == self.EMPTY and next_square.c == 5 and self.king_can_castle_right(
                                moving_piece.get_player()):
                  move = chess_move(starting_square, ending_square, self, self._is_check)
                  move.castling_move((7, 7), (7, 4), self)
                  self.move_log.append(move)

                  self.get_piece((0, 7)).change_col_number(4)

                  # move rook
                  self.board[7][4] = self.board[7][7]
                  self.board[7][7] = self.EMPTY

                  self.black_king_can_castle[0] = False
                  self.black_king_can_castle[2] = False
             else:
                  move = chess_move(starting_square, ending_square, self, self._is_check)
                  self.move_log.append(move)
                  self.black_king_can_castle[0] = False
                  self._black_king_location = next_square
                  # self.can_en_passant_bool = False  WHAT IS THIS
    
    def move_pawn(self, starting_square, ending_square, moving_piece, is_ai):
        row = 0
        col = 1
        temp = True
        #print('moving pawn')
        next_square = ending_square
        
        if (moving_piece.is_player(self.P1) and next_square.r == 7) or moving_piece.is_player(self.P2) and next_square.r == 0:
            # Promoting pawn
            # print("promoting pawn")
            if is_ai:
                self.promote_pawn_ai(starting_square, moving_piece, ending_square)
            else:
                self.promote_pawn(starting_square, moving_piece, ending_square)
                temp = False       
           
        elif abs(next_square.r - starting_square.r) == 2 and starting_square.c == next_square.c:
           # Moving pawn forward by two
           # Problem with Pawn en passant ai
           # print("move pawn forward")
           self.move_log.append(chess_move(starting_square, ending_square, self, self._is_check))
           # self.can_en_passant_bool = True
           self._en_passant_previous = next_square
           
        elif all((abs(next_square.r - starting_square.r) == 1,  
                abs(starting_square.c - next_square.c) == 1, 
                self.can_en_passant(starting_square))):
            # en passant
            # print("en passant")
            incr = (-1, 0) if moving_piece.is_player(self.P1) else (1, 0)
            move = chess_move(starting_square, ending_square, self, self._is_check)
            move.en_passant_move(self.get_board_rc(next_square + incr), next_square + incr)
            self.move_log.append(move)
            self.set_board_rc(next_square + incr, self.EMPTY)            
            
        else:
            # moving forward by one or taking a piece
            self.move_log.append(chess_move(starting_square, ending_square, self, self._is_check))
            self.can_en_passant_bool = False  
            
        return temp 
        
    def move_rook(self, starting_square, next_square, moving_piece):
      
      if moving_piece.is_player(self.P1) and starting_square.c == 0:
          self.white_king_can_castle[1] = False
      elif moving_piece.is_player(self.P1) and starting_square.c == 7:
          self.white_king_can_castle[2] = False
      elif moving_piece.is_player(self.P2) and starting_square.c == 0:
          self.white_king_can_castle[1] = False
      elif moving_piece.is_player(self.P2) and starting_square.c == 7:
          self.white_king_can_castle[2] = False
          self.move_log.append(chess_move(starting_square, next_square, self, self._is_check))
          self.can_en_passant_bool = False
                                              
                                                                                                                              
    # Move a piece
    def move_piece(self, starting_square, ending_square, is_ai, debug=False):
        # need Coord type to allow addition and r,c subscripting
        if not isinstance(starting_square, Coord):
          starting_square = Coord(starting_square)
        if not isinstance(ending_square, Coord):
          ending_square = Coord(ending_square)  

        if debug:
          print('moving piece', starting_square, ending_square)
        next_square = ending_square
        v = self.is_valid_piece(starting_square)
        if v:
          b = self.whose_turn() and self.get_piece(starting_square).is_player(self.P1)
          c = not self.whose_turn() and self.get_piece(starting_square).is_player(self.P2)
        else:
          b = c = False
        d = self.is_valid_piece(starting_square) and \
                (((self.whose_turn() and self.get_piece(starting_square).is_player(
                    self.P1)) or
                  (not self.whose_turn() and self.get_piece(starting_square).is_player(
                      self.P2))))
        a = v and (b or c)
        if debug:
          print(f'turn={self.whose_turn()}')
        if a:
            # The chess piece at the starting square
            
            moving_piece = self.get_piece(starting_square)
            valid_moves = self.get_valid_moves(starting_square)
            if debug:
              print('valid piece', moving_piece, starting_square, ending_square, valid_moves)
            temp = True
            if debug:
                  print('end square', ending_square, valid_moves)
            if ending_square in valid_moves:
                if debug:
                     print('valid piece', moving_piece, starting_square, ending_square, valid_moves) 
                moved_to_piece = self.get_piece(next_square)
                if moving_piece.get_name() == "k":
                    self.move_king(starting_square, next_square, moving_piece)                    
                elif moving_piece.get_name() == "r":
                    self.move_rook(starting_square, next_square, moving_piece)                   
                # Add move class here
                elif moving_piece.get_name() == "p":
                    temp = self.move_pawn(starting_square, ending_square, moving_piece, is_ai)                    
                else:
                    self.move_log.append(chess_move(starting_square, ending_square, self, self._is_check))
                    self.can_en_passant_bool = False

                if temp:
                    # print('moving', next_square, moving_piece)
                    moving_piece.change_position(next_square)
                    self.set_board_rc(next_square, self.get_board_rc(starting_square))
                    self.set_board_rc(starting_square, self.EMPTY)                    

                self.white_turn = not self.white_turn
            else:
                pass

    def undo_move(self):
        if self.move_log:
            u_move = self.move_log.pop()
            if u_move.castled is True:
                self.set_board_rc(u_move.starting_square, u_move.moving_piece)
                self.set_board_rc(u_move.ending_square, u_move.removed_piece)
                self.get_piece(u_move.starting_square).change_position(u_move.starting_square)
                self.set_board_rc(u_move.rook_starting_square, u_move.moving_rook)
                self.set_board_rc(u_move.rook_ending_square, self.EMPTY)
                u_move.moving_rook.change_position(u_move.rook_starting_square)
                if u_move.moving_piece is self.P1:
                    if u_move.rook_starting_square[1] == 0:
                        self.white_king_can_castle[0] = True
                        self.white_king_can_castle[1] = True
                    elif u_move.rook_starting_square[1] == 7:
                        self.white_king_can_castle[0] = True
                        self.white_king_can_castle[2] = True
                else:
                    if u_move.rook_starting_square[1] == 0:
                        self.black_king_can_castle[0] = True
                        self.black_king_can_castle[1] = True
                    elif u_move.rook_starting_square[1] == 7:
                        self.black_king_can_castle[0] = True
                        self.black_king_can_castle[2] = True
            elif u_move.pawn_promoted is True:
                self.set_board_rc(u_move.starting_square, u_move.moving_piece)
                self.get_piece(u_move.starting_square).change_position(u_move.starting_square)
                self.set_board_rc(u_move.ending_square, u_move.removed_piece)
                if u_move.removed_piece != self.EMPTY:
                    self.get_piece(u_move.ending_square).change_position(u_move.ending_square)
            elif u_move.en_passaned is True:
                self.set_board_rc(u_move.starting_square, u_move.moving_piece)
                self.set_board_rc(u_move.ending_square, u_move.removed_piece)
                self.get_piece(u_move.starting_square).change_position(u_move.starting_square)
                self.set_board_rc(u_move.en_passant_eaten_square,u_move.en_passant_eaten_piece)
                self.can_en_passant_bool = True
            else:
                self.set_board_rc(u_move.starting_square, u_move.moving_piece)
                self.get_piece(u_move.starting_square).change_position(
                    u_move.starting_square)                             
                self.set_board_rc(u_move.ending_square, u_move.removed_piece)
                if u_move.removed_piece != self.EMPTY:
                    self.get_piece(u_move.ending_square).change_position(u_move.ending_square)
                    
            self.white_turn = not self.white_turn
            # if u_move.in_check:
            #     self._is_check = True
            if u_move.moving_piece.get_name() == 'k' and u_move.moving_piece.get_player() is self.P1:
                self._white_king_location = u_move.starting_square
            elif u_move.moving_piece.get_name() == 'k' and u_move.moving_piece.get_player() is self.P2:
                self._black_king_location = u_move.starting_square

            return u_move
        else:
            pass
            # print("Back to the beginning!")
    
    

    def check_for_check(self, king_location, player):
        '''
        check for immediate check
        - check 8 directions and 8 knight squares
        check for pins
        - whatever blocked from above is a pin
    
        - if immediate check, change check value to true
        - list valid moves to prevent check but not remove pin
        - if there are no valid moves to prevent check, checkmate
        '''
        # self._is_check = False
        _checks = []
        _pins = []
        _pins_check = []
        king_location = Coord(king_location)
        all_directions = [Coord((r, c)) for r in range(-1,2) for c in range(-1,2) if (r,c) != (0,0)]
        
        for loc in all_directions:
            _possible_pin = ()
            k_pos = king_location + loc
            while self.check_in_board(k_pos) and self.get_piece(k_pos) is not None:
                k_pos = king_location + loc
                if self.is_valid_piece(k_pos) and \
                   self.get_piece(k_pos).is_player(player) and \
                   self.get_piece(k_pos).get_name() != "k":
                      if not _possible_pin:
                          _possible_pin = k_pos
                      else:
                          break
                elif self.is_valid_piece(k_pos) and not self.get_piece(k_pos).is_player(player):
                      if _possible_pin:
                          temp = self.get_board_rc(_possible_pin)
                          self.set_board_rc(_possible_pin, self.EMPTY)
                          if king_location in self.get_piece(k_pos).get_valid_piece_moves(self):
                              _pins.append(_possible_pin)
                              _pins_check.append(k_pos)
                          self.set_board_rc(_possible_pin, temp)
                      else:
                          if king_location in self.get_piece(k_pos).get_valid_piece_moves(self):
                              # self._is_check = True
                              _checks.append(k_pos)
                      break
                loc = loc + loc # move in same direction
        
        # knights
        changes =[(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, 1), (2, -1)]
        for change in changes:
            if self.is_valid_piece(king_location + change) and \
                    not self.get_piece(king_location + change).is_player(player):
                if king_location in self.get_piece(king_location + change).get_valid_piece_moves(self):
                    # self._is_check = True
                    _checks.append(king_location + change)
        # print([_checks, _pins, _pins_check])
        return _checks, _pins, _pins_check


class chess_move():
    def __init__(self, starting_square, ending_square, game_state, in_check):
        self.starting_square = starting_square
        self.ending_square = ending_square
        self.moving_piece = game_state.get_piece(self.starting_square)
        self.in_check = in_check

        if game_state.is_valid_piece(self.ending_square):
            self.removed_piece = game_state.get_piece(self.ending_square)
        else:
            self.removed_piece = game_state.EMPTY

        self.castled = False
        self.rook_starting_square = None
        self.rook_ending_square = None
        self.moving_rook = None

        self.pawn_promoted = False
        self.replacement_piece = None

        self.en_passaned = False
        self.en_passant_eaten_piece = None
        self.en_passant_eaten_square = None

    def castling_move(self, rook_starting_square, rook_ending_square, game_state):
        self.castled = True
        self.rook_starting_square = rook_starting_square
        self.rook_ending_square = rook_ending_square
        self.moving_rook = game_state.get_piece(rook_starting_square)

    def pawn_promotion_move(self, new_piece):
        self.pawn_promoted = True
        self.replacement_piece = new_piece

    def en_passant_move(self, eaten_piece, eaten_piece_square):
        self.en_passaned = True
        self.en_passant_eaten_piece = eaten_piece
        self.en_passant_eaten_square = eaten_piece_square

    def get_moving_piece(self):
        return self.moving_piece

        
def main():
  # testing all functions
  import ai_engine
  def copy_board(board):
      return list(map(list, board)) 
  p_dict = {'PLAYER_1':  'white', 'PLAYER_2': 'black',
                        'EMPTY': -9, 'PLAYERS': ['white', 'black']}
  Player = SimpleNamespace(**p_dict)  
  pass
  gs = game_state(Player)
  ai = ai_engine.chess_ai(Player)
  board = gs.board
  gs.white_turn = True
  #white pawn
  moves = gs.get_valid_moves(Coord((1, 3)))
  print('valid moves', moves)
  gs.move_piece(starting_square=Coord((1, 3)), ending_square=Coord((2, 3)), is_ai=False)
  gs.board_print()
  
  def black_play():
      # now ai move for black
      copied_board = copy_board(gs.board)
      start, end = ai.minimax(gs, 3, -100000, 100000, True, Player.PLAYER_1)      
      print(f'ai moves from {start} to {end}')      
      gs.white_turn = False
      gs.board = copied_board
      board = gs.board
      gs.move_piece(starting_square=Coord(start), ending_square=Coord(end), is_ai=True, debug=True)
      print('after ai move')
      gs.board_print() 
      
  def white_play():
      # now ai move for white
      copied_board = copy_board(gs.board)
      start, end = ai.minimax(gs, 3, -100000, 100000, True, Player.PLAYER_2)      
      print(f'ai moves from {start} to {end}')  
      gs.white_turn = True    
      gs.board = copied_board
      board = gs.board
      gs.move_piece(starting_square=Coord(start), ending_square=Coord(end), is_ai=True, debug=True)
      print('after player move')
      gs.board_print()
      
  for i in range(20): 
     print('ITERATION ', i)
     white_play() 
     black_play()
     
  #black_play()
  
  # move white queen
  moves = gs.get_valid_moves((0, 4))
  print('valid moves', moves)
  gs.move_piece(starting_square=Coord((0, 4)), ending_square=Coord((2, 2)), is_ai=False)
  gs.board_print()   
      
  
    
  
if __name__ == '__main__':
  main()
        
    
