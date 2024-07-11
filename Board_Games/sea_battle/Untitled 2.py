# Kyle Gerner
# Started 9.5.2021
# Sea Battle AI (Battleship clone)
# TODO turn. this into a player vs aAI game
# create 2 boards with random ships at the moment it seems to be 2 player
from datetime import datetime
import math
import os
import sys
from queue import Queue
import console

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
import util.gui.gui_scene as gscene
from util.gui.gui_interface import Gui

# Board characters
DESTROY = "D"
EMPTY = "-"
HIT = "H"
MISS = "^"
POSSIBLE = "?"

class Player():
  def __init__(self):
    self.PLAYER_1 = 'o'
    self.PLAYER_2 = '@'
    self.EMPTY = '-'
    self.PLAYERS =[self.PLAYER_1, self.PLAYER_2]
    self.PIECES = ['emj:Fire','emj:Explosion','emj:Droplet','emj:Question_Mark_1']
    self.PIECE_NAMES ={DESTROY: 'D', HIT: 'H', MISS: '^', POSSIBLE: '?'}
    
# Globals that can be changed throughout execution
SAVE_FILENAME = "sea_battle_save.txt"


class BattleShip():
  
  def __init__(self):
 
    self.DENSITY_PYRAMID = []  # created later; level 'i' has i integers that represent the score for a location if there are i spaces open in a row/column
    self.SIZE = self.get_size()     
    # load the gui interface
    self.q = Queue(maxsize=10)
    self.gui = Gui(self.game_board, Player())
    #self.gui.set_prompt(f"Invalid input. The board will be 10x10!")
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.SIZE]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.setup_gui()
    self.gui.gs.q = self.q
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.gs.pause_menu = {'Continue': self.gui.gs.dismiss_modal_scene, 
                              'Show Densities': self.print_space_densities, 
                              'Quit': self.quit}
    self.gui.gs.start_menu = {'New Game': self.run, 'Quit': self.quit}
    
    self.all = [[j,i] for i in range(self.SIZE) for j in range(self.SIZE) if self.game_board[j][i] == EMPTY]
    #self.gui.valid_moves(self.all, message=None)
    
  def process_ai_move(self, row, col):
    self.gui.set_prompt(f"The selected move {self.gui.ident((row, col))} has been highlighted.")
      
    outcome = self.gui.input_message(f"Was that shot a miss (M), a partial-hit (H), or a sink (S)?\t").strip().upper()
    while outcome not in ['Q', 'H', 'S', 'M']:
      outcome = self.gui.inpur_message(f"Invalid input. Try again:\t").strip().upper()
      if outcome == 'M':
        self.game_board[row][col] = MISS
      elif outcome == "H":
        self.game_board[row][col] = HIT
      elif outcome == "S":
        self.sink_ship(row, col)
      else: # outcome = Q
        print("\nThanks for playing!\n")
        exit(0)
          
  def run(self):
    """
    Main method that prompts the user for input
    """       
    self.create_density_pyramid()
    best_move_coordinates_list = self.get_optimal_moves()
    self.print_board(optimal_locations=best_move_coordinates_list)
    
    while True:
      self.gui.set_message2(f"The spot  most likely to contain \na ship colored blue.")
      
      most_recent_move = self.get_player_move()
      row, col = most_recent_move
      self.print_board([row, col], best_move_coordinates_list)
      self.process_ai_move(row, col)
  
      if game_over():
        break
      best_move_coordinates_list = get_optimal_moves()
      self.print_board([row, col], best_move_coordinates_list)
    self.print_board(most_recent_move)
    print("\nGood job, you won!\n")
  
  def get_size(self):

    selection = console.input_alert("What is the dimension of the board (8, 9, or 10)? (Default is 10x10)\nEnter a single number:\t")
    try:
      selection = selection.strip()
    except:
      pass
    if selection.isdigit() and int(selection) in [8, 9, 10]:
      board_dimension = int(selection)      
    else:
       board_dimension = 10
       print(f"Invalid input. The board will be 10x10!")
    self.create_game_board(int(board_dimension))
    return board_dimension
      
  def create_game_board(self, dimension):
    """Creates the gameBoard with the specified number of rows and columns"""   
    self.game_board = [[EMPTY] * dimension for row_num in range(dimension)]
    if dimension == 10:
      return
    elif dimension == 9:
      self.REMAINING_SHIPS = {3: 5,4: 3}
    elif dimension == 8:
      self.REMAINING_SHIPS = {2: 3,3: 3,4: 1}
    else:
      # ship_length: num_remaining
      self.REMAINING_SHIPS = {1: 4, 2: 3, 3: 2, 4: 1}

  
  def print_board(self, most_recent_move=None, optimal_locations=None):
    """
    Display the  players game board 
    """
    if optimal_locations is None:
      optimal_locations = []
      self.gui.valid_moves(self.all, message=None)
    else:
      self.gui.valid_moves(optimal_locations, message=None)
      
    if most_recent_move:
      self,game_board[most_recent_move[0]][most_recent_move[1]] = POSSIBLE
      
    self.gui.update(self.game_board)  
        
    sh =[[l, self.REMAINING_SHIPS[l]] for l in list(reversed(self.REMAINING_SHIPS))]
      
    self.gui.set_moves("".join(("Remaining ships:\n", 
    "\t%dx  %s\n" % (sh[0][1], "S"*sh[0][0]),
    "\t%dx  %s\n" % (sh[1][1], "S"*sh[1][0]),
    "\t%dx  %s\n" % (sh[2][1], "S"*sh[2][0]) if len(sh) > 2 else '\n' 
    "\t%dx  %s" % (sh[3][1], "S"*sh[3][0]) if len(sh) > 3  else '\n')))



  def print_space_densities(self, color_mode=True):
    """
    Prints out the space densities chart on gui
    """
    def get_color(value, max_val, min_val):
      """
      Get the color that corresponds to the given value
      """
      if value == max_val:
        return 'cyan'
      elif value == 0:
        return 'red'
      total_range = max(max_val - min_val, 1)
      percentage = 100 * ((value - min_val) / total_range)
      if percentage > 75:
        return 'lightgreen'
      elif percentage > 40:
        return 'yellow'
      else:
        return 'orange'
        
    density_dict =[]
    space_densities = self.generate_space_densities()
    max_score, min_score = -1, 100000
    max_score = max(max_score, max(max(x) for x in space_densities))
    min_score = min(min_score, min(min(x) for x in space_densities))
        
    for row_index, row in enumerate(space_densities):   
      for col_index, value in enumerate(row):
        color = get_color(value, max_score, min_score)
        density_dict.append({'position': (row_index, col_index), 'text':str(int(value)), 'color': color})
    self.gui.add_numbers(density_dict)
      

  def game_over(self):
    """
    Checks if the game is over
    """
    if not any(EMPTY in row for row in self.game_board):
      return True
    for ship_size in self.REMAINING_SHIPS:
      if self.REMAINING_SHIPS[ship_size] > 0:
        return False
    return True


  def save_game(self):
    """Saves the given board state to a save file"""
    if not allow_save(SAVE_FILENAME):
      return
    with open(SAVE_FILENAME, 'w') as saveFile:
      saveFile.write("This file contains the save state of a previously played game.\n")
      saveFile.write("Modifying this file may cause issues with loading the save state.\n\n")
      timeOfSave = datetime.now().strftime("%m/%d/%Y at %I:%M:%S %p")
      saveFile.write(timeOfSave + "\n\n")
      saveFile.write("SAVE STATE:\n")
      for row in self.game_board:
        saveFile.write(" ".join(row) + "\n")
      saveFile.write("Ships remaining:\n")
      for shipSize, numShips in REMAINING_SHIPS.items():
        saveFile.write(f"{shipSize}: {numShips}\n")
      saveFile.write("END")
    print(f"The game has been saved!")


  def validateLoadedSaveState(self, board):
    """Make sure the state loaded from the save file is valid. Returns a boolean"""
    board_dimension = len(board)
    if board_dimension not in [8, 9, 10]:
      print(f"Invalid board size!")
      return False
    for row in board:
      if len(row) != board_dimension:
        print(f"Board is not square!")
        return False
      for spot in row:
        if spot not in [DESTROY, HIT, MISS, EMPTY]:
          print(f"Board contains invalid pieces!")
          return False
    for ship_size, num_ships in self.REMAINING_SHIPS.items():
      if not 1 <= ship_size <= 4:
        print(f"Invalid ship size: {ship_size}")
        return False
      if not num_ships >= 0:
        print(f"pInvalid number of ships remaining for size {ship_size}: {num_ships}")
        return False
    if sum(self.REMAINING_SHIPS.values()) == 0:
      print(f"Every ship size has 0 remaining ships!")
      return False
    return True


  def loadSavedGame(self):
    """Try to load the saved game data. Returns boolean for if the save was successful."""

    with open(SAVE_FILENAME, 'r') as saveFile:
      try:
        linesFromSaveFile = saveFile.readlines()
        timeOfPreviousSave = linesFromSaveFile[3].strip()
        useExistingSave = input(f"Would you like to load the saved game from {timeOfPreviousSave}? (y/n)\t").strip().lower()
        erasePreviousLines(1)
        if useExistingSave != 'y':
          print(f"Starting a new game...")
          return
        lineNum = 0
        currentLine = linesFromSaveFile[lineNum].strip()
        while currentLine != "SAVE STATE:":
          lineNum += 1
          currentLine = linesFromSaveFile[lineNum].strip()
        lineNum += 1
  
        currentLine = linesFromSaveFile[lineNum].strip()
        board_from_save_file = []
        while not currentLine.startswith("Ships remaining:"):
          board_from_save_file.append(currentLine.split())
          lineNum += 1
          currentLine = linesFromSaveFile[lineNum].strip()
        lineNum += 1
  
        currentLine = linesFromSaveFile[lineNum].strip()
        while not currentLine.startswith("END"):
          ship_size, num_ships = currentLine.split(":")[:2]
          self.REMAINING_SHIPS[int(ship_size.strip())] = int(num_ships.strip())
          lineNum += 1
          currentLine = linesFromSaveFile[lineNum].strip()
  
        if not self.validateLoadedSaveState(board_from_save_file):
          raise ValueError
        self.game_board = board_from_save_file
              
        print(f"Resuming saved game...")
        return True
      except:
        print(f"There was an issue reading from the save file. Starting a new game...")
        return False
  

  def create_density_pyramid(self):
    """
    Create a pyramid-shaped 2D list that contains the scores for each index given an open sequence of n spaces.
    This will make the generate_space_densities function faster
    """
    remaining_ships = []
    for key in self.REMAINING_SHIPS:
      num_remaining = self.REMAINING_SHIPS[key]
      if num_remaining > 0:
        remaining_ships.append([key, num_remaining])
    self.DENSITY_PYRAMID.clear()
    for level in range(1, self.SIZE+1):
      row = [0] * level
      for ship_data in remaining_ships:
        ship_size, num_remaining = ship_data
        for index in range(level + 1 - ship_size):
          right_index = index + ship_size - 1
          for space in range(index, right_index + 1):
            row[space] += num_remaining
      self.DENSITY_PYRAMID.append(row)


  def generate_space_densities(self, board=None):
    """
    Generate a board where each space has densities that relate to the number of ways ships could be placed there
    NOTE: The implementation is ugly, but it works. I was trying to get this done as quick as possible.
    """
    if board is None:
      gb = self.game_board # a shortcut
    else:
      gb = board
      
    def fill_list_with_density_pyramid_data(arr, start_index, sequence_length):
      """
      Take data from the density pyramid and populate a portion of the given list with that data
      """
      data = self.DENSITY_PYRAMID[sequence_length - 1]
      for i in range(sequence_length):
        arr[i + start_index] += data[i]
        
    def get_num_open_neighbors_in_direction(arr, start_index, ship_size):
        """
        Find the number of open spaces in each direction from the starting index
        Returns a tuple of the # spaces in the positive direction, and negative direction respectively
        """
        pos, neg = 0, 0
        hits_in_pos_dir = 1
        hits_in_neg_dir = 1
    
        index = start_index + 1
        while index < len(arr) and arr[index] == HIT and hits_in_pos_dir < ship_size - 1:
          hits_in_pos_dir += 1
          index += 1
        index = start_index - 1
        while index >= 0 and arr[index] == HIT and hits_in_neg_dir < ship_size - 1:
          hits_in_neg_dir += 1
          index -= 1
    
        index = start_index + 1
        while index < len(arr) and arr[index] == EMPTY and pos < ship_size - hits_in_neg_dir:
          pos += 1
          index += 1
        index = start_index - 1
        while index >= 0 and arr[index] == EMPTY and neg < ship_size - hits_in_pos_dir:
          neg += 1
          index -= 1
        return pos, neg
        
    def get_num_immediate_neighbors(row, col, board=None):
      """
      Find the number of open spaces that are immediately next to the specified coordinate.
      0 < num_open < 8
      """
      if board is None:
        board = self.game_board
        
      num_open = 0
      for row_add in [-1, 0, 1]:
        for col_add in [-1, 0, 1]:
          if row_add == col_add == 0:
            continue
            if 0 <= row + row_add < self.SIZE and 0 <= col + col_add < self.SIZE and board[row+row_add][col+col_add] == EMPTY:
              num_open += 1
      return num_open
 

  
    space_densities = [[0]*self.SIZE for _ in range(self.SIZE)] # initialise to all zero
    
    # Look at horizontal open space and fill space_densities accordingly
    for r in range(self.SIZE):
      row = gb[r]
      next_unavailable_index = 0
      next_open_spot = 0
      evaluating_row = True
      while evaluating_row:
        while next_open_spot < self.SIZE and row[next_open_spot] in [MISS, DESTROY]:
          next_open_spot += 1
        if next_open_spot == self.SIZE:
          break
        while next_unavailable_index < self.SIZE and row[next_unavailable_index] in [EMPTY, HIT]:
          next_unavailable_index += 1
        fill_list_with_density_pyramid_data(space_densities[ro], next_open_spot, next_unavailable_index - next_open_spot)
        if next_unavailable_index == self.SIZE:
          evaluating_row = False
        next_open_spot = next_unavailable_index + 1
        next_unavailable_index += 1
  
    # Look at vertical open space and fill space_densities accordingly
    for c in range(self.SIZE):
      cols = [row[c] for row in gb]
      next_unavailable_index = 0
      next_open_spot = 0
      evaluating_col = True
      while evaluating_col:
        while next_open_spot < self.SIZE and cols[next_open_spot] in [MISS, DESTROY]:
          next_open_spot += 1
        if next_open_spot == self.SIZE:
          break
        while next_unavailable_index < self.SIZE and cols[next_unavailable_index] in [EMPTY, HIT]:
          next_unavailable_index += 1
        density_col = [0]* self.SIZE
        fill_list_with_density_pyramid_data(density_col, next_open_spot, next_unavailable_index - next_open_spot)
        for r in range(self.SIZE):
          space_densities[r][c] += density_col[r]
        if next_unavailable_index == self.SIZE:
          evaluating_col = False
        next_open_spot = next_unavailable_index + 1
        next_unavailable_index += 1
  
    # Give preference to spots where a hit/sink would clear the most space on the board (spaces with more open immediate neighbors)
    for r in range(self.SIZE):
      for c in range(self.SIZE):
        space_densities[r][c] *= (1 + 0.05 * get_num_immediate_neighbors(r, c))
  
    # high scores for partially-sunken ships; also change hits to 0 scores
    largest_remaining_ship_size = max(ship_size for ship_size, num_left in self.REMAINING_SHIPS.items() if num_left > 0)
    max_density = max(max(val) for val in space_densities)
    for r in range(self.SIZE):
      for c in range(self.SIZE):
        spot = gb[r][c]
        if spot == HIT:
          space_densities[r][c] = 0
          # TODO check this
          if (0 <= r - 1 and gb[r - 1][c] == HIT) or (r + 1 < self.SIZE and gb[r + 1][c] == HIT):
            # ship aligned vertically
            cols = [row[c] for row in gb]
            downward_space, upward_space = get_num_open_neighbors_in_direction(
              cols, r, largest_remaining_ship_size
            )
            if 0 <= r-1 and gb[r-1][c] == EMPTY:
              space_densities[r-1][c] = (max_density + upward_space) * (1 + 0.02 * get_num_immediate_neighbors(r-1, c))
              # space_densities[row_index - 1][col_index] *= (upward_space + 1)
            if r + 1 < self.SIZE and gb[r+1][c] == EMPTY:
              space_densities[r+1][c] = (max_density + downward_space) * (1 + 0.02 * get_num_immediate_neighbors(r+1, c))
              # space_densities[row_index + 1][col_index] *= (downward_space + 1)
          elif (0 <= c-1 and gb[r][c-1] == HIT) or (c+1 < self.SIZE and gb[r][c + 1] == HIT):
            # ship aligned horizontally
            rightward_space, leftward_space = get_num_open_neighbors_in_direction(
              gb[r], c, largest_remaining_ship_size
            )
            if 0 <= c - 1 and gb[r][c - 1] == EMPTY:
              space_densities[r][c - 1] = (max_density + leftward_space) * (1 + 0.02 * get_num_immediate_neighbors(row_index, col_index-1))
              # space_densities[r][c - 1] *= (leftward_space + 1)
            if col_index + 1 < self.SIZE and gb[r][c + 1] == EMPTY:
              space_densities[r][c + 1] = (max_density + rightward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c+1))
              # space_densities[r][c + 1] *= (rightward_space + 1)
          else:
            # no neighboring spaces have been hit, so we don't know the alignment of the ship
            cols = [row[c] for row in self.gb]
            downward_space, upward_space = get_num_open_neighbors_in_direction(
              cols, r, largest_remaining_ship_size
            )
            rightward_space, leftward_space = get_num_open_neighbors_in_direction(
              gb[r], c, largest_remaining_ship_size
            )
            if 0 <= r - 1 and gb[r-1][c] == EMPTY:
              space_densities[r - 1][c] = (max_density + upward_space) * (1 + 0.02 * get_num_immediate_neighbors(r-1, c))
              # space_densities[r - 1][c] *= (upward_space + 1)
            if r + 1 < SIZE and gb[r+1][col] == EMPTY:
              space_densities[r + 1][c] = (max_density + downward_space) * (1 + 0.02 * get_num_immediate_neighbors(r+1, c))
              # space_densities[row_index + 1][col_index] *= (downward_space + 1)
            if 0 <= c - 1 and gb[r][c - 1] == EMPTY:
              space_densities[row][c - 1] = (max_density + leftward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c-1))
              # space_densities[row_index][col_index - 1] *= (leftward_space + 1)
            if c + 1 < self.SIZE and gb[r][c + 1] == EMPTY:
              space_densities[r][c + 1] = (max_density + rightward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c+1))
              # space_densities[r][c + 1] *= (rightward_space + 1)
  
    return space_densities
  
  
  def get_optimal_moves(self,board=None):
    """
    Get a list of the coordinates of the best moves
    """
    if board is None:
      board = self.game_board
    space_densities = self.generate_space_densities(board)
    max_score = -1
    best_move_coordinates = []
    for r in range(self.SIZE):
      for c in range(self.SIZE):
        density_score = space_densities[r][c]
        if density_score == max_score:
          best_move_coordinates.append([r,c])
        elif density_score > max_score:
          max_score = density_score
          best_move_coordinates = [[r, c]]
    return best_move_coordinates
  
  
  def sink_ship(self, row, col, board=None):
    """
      Changes the game board to display that a ship has sunk
      Updates the density pyramid
      Updates the ships remaining totals
    """
    if board is None:
      board = self.game_board
      
    board[row][col] = DESTROY
    dir_increments = [
      [0, -1], # left
      [0, 1],  # right
      [-1, 0], # down
      [1, 0]   # up
    ]
    sunken_coordinates = [[row, col]]
    for direction_pair in dir_increments:
      vert_add, horiz_add = direction_pair
      row_incremented, col_incremented = row, col
      while 0 <= (row_incremented + vert_add) < self.SIZE and 0 <= col_incremented + horiz_add < self.SIZE:
        # while in range of board
        spot = board[row_incremented + vert_add][col_incremented + horiz_add]
        if spot == HIT:
          board[row_incremented + vert_add][col_incremented + horiz_add] = DESTROY
          sunken_coordinates.append([row_incremented + vert_add, col_incremented + horiz_add])
          row_incremented += vert_add
          col_incremented += horiz_add
        else:
          break
    try:
      sunken_ship_size = len(sunken_coordinates)
      REMAINING_SHIPS[sunken_ship_size] -= 1
      self.create_density_pyramid()
    except KeyError:
      possible_lengths = str(list(REMAINING_SHIPS.keys()))[1:-1]
      print(f"Looks like there was some confusion. Ships can only be one of the following lengths: {possible_lengths}")
      print("Terminating session.")
      exit(0)
  
    sunken_neighbor_distances = [
      [0, -1],  # left
      [0, 1],   # right
      [-1, 0],  # down
      [1, 0],   # up
      [-1, -1], # lower left
      [-1, 1],  # lower right
      [1, -1],  # upper left
      [1, 1]    # upper right
    ]
    for coord in sunken_coordinates:
      for increment in sunken_neighbor_distances:
        new_row, new_col = coord[0] + increment[0], coord[1] + increment[1]
        if 0 <= new_row < self.SIZE and 0 <= new_col < self.SIZE and board[new_row][new_col] == EMPTY:
          board[new_row][new_col] = MISS
  
  
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move"""
    if board is None:
        board = self.game_board
    prompt = "Which spot would you like to play? (A1 - %s%d):" % (self.COLUMN_LABELS[-1], self.SIZE)
    # sit here until piece place on board   
    while True:
      self.gui.set_prompt(prompt)
      spot = self.gui.wait_for_gui(board) 
      spot = spot.strip().upper()
      row = int(spot[1:]) - 1
      col = self.COLUMN_LABELS.index(spot[0])
      if board[row][col] != EMPTY:
        prompt = f"That spot is already taken, please choose another:"
      else:
        break
    return [row, col]  
  
  def printAsciiTitleArt(self):
    """Prints the fancy text when you start the program"""
    print("""
     _____              ____        _   _   _      
    / ____|            |  _ \\      | | | | | |     
   | (___   ___  __ _  | |_) | __ _| |_| |_| | ___ 
    \\___ \\ / _ \\/ _` | |  _ < / _` | __| __| |/ _ \\
    ____) |  __/ (_| | | |_) | (_| | |_| |_| |  __/
   |_____/ \\___|\\__,_| |____/ \\__,_|\\__|\\__|_|\\___|
   """)

  def quit(self):
    self.gui.gs.close()
    sys.exit() 
  
    
if __name__ == '__main__':
  g = BattleShip()
  g.run()
  #g.wait()


