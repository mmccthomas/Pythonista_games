class Piece:
    # Initialize the piece
    def __init__(self, name, row_number, col_number, player):
        self.name = name
        self.row_number = row_number
        self.col_number = col_number
        self.coord = (row_number, col_number)
        self.player = player
        
    def __repr__(self):
      return f'{self.player}_{self.name} @ {self.coord}'

    # Get the x value
    def get_row_number(self):
        return self.row_number

    # Get the y value
    def get_col_number(self):
        return self.col_number
        
     # get y and x as tuple    
    def get_coord(self):
        return self.coord
        
    # Get the name
    def get_name(self):
        return self.name

    def get_player(self):
        return self.player

    def is_player(self, player_checked):
        return self.get_player() == player_checked

    def change_row_number(self, new_row_number):
        self.row_number = new_row_number
        self.coord = (new_row_number, self.col_number)

    def change_col_number(self, new_col_number):
        self.col_number = new_col_number
        self.coord = (self.row_number, new_col_number)

    def change_position(self, new_position):
        self.row_number, self.col_number = new_position
        self.coord = new_position
        
    # Get moves
    def get_valid_piece_moves(self, game_state):
        pass
