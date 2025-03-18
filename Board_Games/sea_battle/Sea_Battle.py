# ios front end Chris Thomas 12.7.24
# refactored to use classes Ship and Ships
# Kyle Gerner
# Started 9.5.2021
# Sea Battle AI (Battleship clone)
#
# create 2 boards with random ships at the moment it seems to be 2 player
from datetime import datetime
from time import sleep, time
import math
import random
import os
import sys
from queue import Queue
import console
import sound

SOUND = True

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
import gui.gui_scene as gscene
from gui.gui_interface import Gui, Squares

# Board characters
DESTROY = "D"
EMPTY = "-"
HIT = "H"
MISS = "^"
POSSIBLE = "?"

def add(a,b):
  """ helper function to add 2 tuples """
  return tuple(p+q for p, q in zip(a, b))

def  board_rc(rc, board, value):
  board[rc[0]][rc[1]] = value 
      
class Player():
  def __init__(self):
    self.PLAYER_1 = '?'
    self.PLAYER_2 = '@'
    self.EMPTY = '-'
    
    self.PIECES = ['emj:Question_Mark_1','emj:Fire','emj:Explosion','iow:close_32']
    self.PIECE_NAMES ={POSSIBLE: '?',HIT: 'H', DESTROY: 'D',  MISS: '^', }
    self.PLAYERS =['?', 'H', 'D', '^']

class Ship():
  """ class to hold single ship """
  
  
  def __init__(self, length=1, coords=None, direction=None, size=None, player='human'):
    if player == 'ai':
      self.color = 'pink'
    else:
      self.color = 'green'
    self.player = player
    self.length = length
    self.coordinates = coords
    self.update_colors()
    self.direction = direction
    self.size = size
    
    
    self.keepouts = self.update_keepouts()
    
  def update_colors(self):
    self.color_of_sections = [self.color for _ in self.coordinates]
    
  def check_in_board(self, coord):
    r,c = coord 
    return  (0 <= r < self.size) and  (0 <= c <  self.size)
      
  def damage(self, rc):
    self.color_of_sections[self.coordinates.index(rc)] = "red"
    
  def sink(self, rc, board):
    """
      update board locations for sunk ship      
    """    
    for rc in self.keepouts:
      if self.check_in_board(rc):  
        board_rc(rc, board, MISS)   

    for rc  in self.coordinates:
      if self.check_in_board(rc):     
        board_rc(rc, board, DESTROY)
    
  def destroyed(self):
    pass
    
  def keepout(self) :
    return [(r, c) for r in range(-1,2) for c in range(-1, 2)] # all round single coordinate
    
  def update_keepouts(self):
    """ mark all around ship """
    keeps= [add(coord, k) for k in self.keepout() for coord in self.coordinates]
    for item in keeps:
      if not self.check_in_board(item):
        keeps.remove(item)   
    keeps = list(set(keeps)) # remove duplicates 
    keeps = sorted(keeps)
    return keeps
    
  def check_too_close(self, all_keepouts):
    for coord in self.coordinates:        
      if coord in all_keepouts or not self.check_in_board(coord):
        return True
    return False
    
  def place_random_ship(self):
    inside_board = False
    directions = {'up': (-1, 0), 'left': (0, 1), 'down': (1, 0), 'right': (0, 1)}
    # try to make a ship inside the board
    # iterate until ok
    while inside_board == False:
      direction = random.choice(['up', 'left', 'down', 'right'])
      ship_coords = []
      # place bow for ship
      bow_r, bow_c = random.randint(0, self.size - 1), random.randint(0, self.size - 1)
      ship_coords.append((bow_r, bow_c))
      # try to place rest of ship
      for i in range(self.length -1):            
        last_pos = ship_coords[-1]
        incr = directions[direction]
        ship_coords.append(add(last_pos, incr))
      if all([self.check_in_board(rc) for rc in ship_coords]):
          inside_board = True
      
    self.coordinates = ship_coords
    self.direction = direction
    self.update_colors()
    self.keepouts = self.update_keepouts()
    
class Ships(Ship):
   """ class to hold set of ships for each player """
   def __init__(self, size, remaining_ships):
     # initial load with remaining
     self.ships =[] # a list of Ship
     self.remaining_ships = remaining_ships
     self.all = []
     self.size = size
     self.density_pyramid = self.create_density_pyramid()
     
   def add_ship(self, ship):
     self.ships.append(ship)
     self.all = self.all_positions()
     self.player = ship.player

   def update_remaining(self):
     pass
     
   def create_ships(self):
     pass
     
   def find_hit_ship(self, rc, opponent_board):
     """ remove a struck ship
         if all sections of ship are removed, sink ship
     """
     for ship in self.ships:
        # iterate over ships in that length
        if tuple(rc) in ship.coordinates:
          ship.damage(rc)
                
          if ship.length == 1 or all(c=='red' for c in ship.color_of_sections):
                # Changes the game board to display that a ship has sunk
                ship.sink(rc, opponent_board)
                self.ships.remove(ship)
                self.count_remaining_ships()
          break
            
     
   def print_ship(self):
     pass
     
   def all_positions(self):
     all = []
     for ship in self.ships:
       for coord in ship.coordinates:
         all.append(coord)
     return sorted(all)
     
   def all_keepouts(self):
     all_keepouts = []
     for s in self.ships:
       all_keepouts.extend(s.keepouts)
     if len(all_keepouts):
       return sorted(list(set(all_keepouts)))
     else:
       return []
          
   def count_remaining_ships(self):
      
      #self.remaining_ships = {1: 4, 2: 3, 3: 2, 4: 1}
      #  {2: 3, 3: 3, 4: 1}
      #clear the dictionary and rebuild
      for k in self.remaining_ships:
        self.remaining_ships[k] = 0
      for ship in self.ships:
        self.remaining_ships[ship.length] += 1
      total = []
      for l, no in reversed(self.remaining_ships.items()):
        total.append(f'{no}x  {chr(896) * l}\n' if no > 0 else '\t----\n')
      return ''.join(total).strip()
      
      
   def create_density_pyramid(self):
     """level 'i' has i integers that represent the score for a location 
     if there are i spaces open in a row/column
     """
     self.density_pyramid =[]
     for level in range(1, self.size+1):
       row = [0] * level
       for ship_data in self.remaining_ships.items(): # a list of k,v tuples
         ship_size, num_remaining = ship_data
         for index in range(level + 1 - ship_size):
           right_index = index + ship_size - 1
           for space in range(index, right_index + 1):
             row[space] += num_remaining
       self.density_pyramid.append(row)
     return(self.density_pyramid)
         
   def print_keepouts(self):
     """for testing print keepouts"""
     keep = [['-' for j in range(self.size)] for _ in range(self.size)]
     for rc in self.all_keepouts():
       keep[rc[0]][rc[1]] = 'x'
                       
     for (r,c) in self.all_positions():
       keep[r][c] = '0' # print 

     for j, row in enumerate(keep):
       for i, col in enumerate(row):
         print(keep[j][i], end=' ')
       print()                                                         
    
  
# Globals that can be changed throughout execution
SAVE_FILENAME = "sea_battle_save.txt"


class BattleShip():
  
  def __init__(self):
 
     
    self.remaining_ships =[[]]
    # create game_board and ai_board
    self.SIZE = self.get_size() 
     
    # load the gui interface
    self.q = Queue(maxsize=10)
    self.gui = Gui(self.game_board, Player())
    self.gui.gs.q = self.q # pass queue into gui
    self.COLUMN_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:self.SIZE]
    self.gui.set_alpha(True) 
    self.gui.set_grid_colors(grid='lightgrey', highlight='lightblue')
    self.gui.require_touch_move(False)
    self.gui.allow_any_move(True)
    self.gui.setup_gui()
    
    # menus can be controlled by dictionary of labels and functions without parameters
    self.gui.gs.pause_menu = {'Continue': self.gui.gs.dismiss_modal_scene, 
                              'Show Densities': self.print_space_densities, 
                              'Quit': self.quit}
    self.gui.gs.start_menu = {'New Game': self.restart, 'Quit': self.quit}
    
    self.all = [[j,i] for i in range(self.SIZE) for j in range(self.SIZE) if self.game_board[j][i] == EMPTY]
    #self.gui.valid_moves(self.all, message=None)
    self.toggle_density_chart = False # each call to density chart will switch on and off
    x, y, w, h = self.gui.grid.bbox
    if self.gui.get_device().endswith('_portrait'):
      posn1 = (0, h+60)
      posn2 = (w/2, h+60)
    else:
      posn1 = (w+10, h/2)
      posn2 = (w+10, h/6)
    self.human_ships_status = self.gui.add_button(text='', title='Human Ships', position=posn1, 
                                        min_size=(50, 50),
                                        fill_color='clear')
    self.ai_ships_status = self.gui.add_button(text='', title='AI Ships', position=posn2, 
                                        min_size=(50, 50),
                                        fill_color='clear' )
  #.  Main Game loop #######s#  
     
  def run(self):
    """
    Main method that prompts the user for input
    """
    self.gui.clear_messages()
    self.ships = self.position_ships(player='human')
    if self.ships is None:
      print('start again with new size')
      return
    self.ai_ships = self.position_ships(player='ai')
    if self.ai_ships is None:
      return
    self.print_ships(self.ships)
    # self.print_ships(self.ai_ships, color='pink')
    
    self.create_density_pyramid(self.ships) 

    self.gui.set_message2(f"The spot  most likely to contain \na ship colored blue.", font=('Avenir Next', 25))
    self.finished = False
    while True:
      # for debug
      #self.gui.print_board(self.ai_board, 'ai')
      self.gui.gs.clear_highlights()
      
      # human play
      self.gui.set_top('Human turn')
      self.print_ships(self.ships)
      #self.print_ships(self.ai_ships, color='pink')
      self.create_density_pyramid(self.ships)
      best_move_coordinates_list = self.get_optimal_moves(self.game_board, player='human')
      self.print_board(optimal_locations=best_move_coordinates_list)
      move = self.get_player_move(self.game_board)               
      
      hit = self.check_hit(move ,self.ai_ships)
      self.process_strike(hit, move, self.game_board, self.ai_ships)
      self.gui.set_message(f"You played {self.gui.ident(move)}:  {'Hit!' if hit else 'Miss!'}", font=('Avenir Next', 25)) 
      if self.game_over():
        break 
     
      self.print_board(move, best_move_coordinates_list)
      self.gui.gs.clear_highlights()
      
        
      # ai play
      self.gui.set_prompt("", font=('Avenir Next', 25))
      self.gui.set_top('AI turn')
      sleep(1)
      self.create_density_pyramid(self.ai_ships) 
      best_move_coordinates_list = self.get_optimal_moves(board=self.ai_board,player='ai')
      move = tuple(random.choice(best_move_coordinates_list))
      self.print_board(move, best_move_coordinates_list)
      
      hit = self.check_hit(move, self.ships)
      self.gui.set_message2(f"AI played {self.gui.ident(move)}:  {'Hit!' if hit else 'Miss!'}    from {len(best_move_coordinates_list)} possible moves", font=('Avenir Next', 25))

      self.process_strike(hit, move, self.ai_board, self.ships)
      if self.game_over():
        break
      self.gui.gs.clear_highlights()     
       
    self.print_board()
    self.gui.set_message2(f'{self.game_over()} WON!')
    self.gui.set_message('') 
    self.gui.set_prompt('')
    sleep(4)
    self.finished = True
    self.gui.gs.show_start_menu()
    
    
      
  def check_hit(self, rc, ships):
     """ ships is a an instance of Ships, containing several Ship onjects 
     """
     if SOUND:
       sound.play_effect('arcade:Hit_1')
     sleep(1)
     for ship in ships.ships:
       if tuple(rc) in ship.coordinates: 
        return True     
     return  False 
      
  def process_strike(self, hit, rc, board, ships):
    """ process the strike to find which ship 
        to allow finding if ship has sunk
        update appropriate board and remaining ships
    """
    # ships is an object containing ship objects
    if hit:
      board_rc(rc, board, HIT)
      ships.find_hit_ship(rc, board)
    else:
      board_rc(rc, board, MISS)    
        
  def print_ships(self, whose_ships, color=None):
    #
    try: 
      self.gui.gs.clear_numbers()
    except (AttributeError):
      
      pass
      
    ships_list = []
    for ship in whose_ships.ships:
      for i, rc in enumerate(ship.coordinates):
        ships_list.append(Squares(rc, int(ship.length), ship.color_of_sections[i], 
                                  font=('Marker Felt',20), text_anchor_point=(0,1),radius=10, stroke_color='black'))
    self.gui.add_numbers(ships_list)  

    
  def get_size(self):
    selection = console.input_alert("What is the dimension of the board (8, 9, or 10)? (Default is 10x10)\nEnter a single number:")
    try:
      selection = selection.strip()
    except:
      pass
    if selection.isdigit() and int(selection) in [5, 6, 7, 8, 9, 10, 11, 12]:
      board_dimension = int(selection)      
    else:
       board_dimension = 10
       print(f"Invalid input. The board will be 10x10!")
    self.create_game_board(int(board_dimension))
    return board_dimension
      
  def create_game_board(self, dimension):
    """Creates the gameBoard with the specified number of rows and columns"""   
    self.game_board = [[EMPTY] * dimension for row_num in range(dimension)]
    self.ai_board = [[EMPTY] * dimension for row_num in range(dimension)]
    if dimension == 5:
      self.remaining_ships = {1: 2, 2: 2} 
    elif dimension == 6:
      self.remaining_ships = {1: 3, 2: 3} 
    elif dimension == 7:
      self.remaining_ships = {2: 2, 3: 3, 4: 1} 
    elif dimension == 8:
      self.remaining_ships = {2: 3, 3: 3, 4: 1} 
    elif dimension == 9:
      self.remaining_ships = {3: 5, 4: 3}
    elif dimension == 11:
      self.remaining_ships =  {1: 5, 2: 3, 3: 4, 4: 2}
    elif dimension == 12:
      self.remaining_ships = {1: 6, 2: 4, 3: 3,  4: 3}
    else:
      # ship_length: num_remaining
      self.remaining_ships =  {1: 4, 2: 3, 3: 2, 4: 1}
                               
  def check_in_board(self, coord):
    r,c = coord 
    return  (0 <= r < self.SIZE) and  (0 <= c <  self.SIZE)
    
  def position_ships(self, player=None):
    """ place the ships in random locations following the rules
        Ships cannot be within 1 tile of one another
    """
    tstart = time()
    ships = Ships(self.SIZE, self.remaining_ships)
            
    # longest first
    ship_list =list(self.remaining_ships.items())
    for len_ship, no_ship in reversed(ship_list):
      for ship in range(no_ship):
        location_ok = False
        loop = 0
        while not location_ok:
          loop += 1                     
          ship_obj = Ship(len_ship, [], '', self.SIZE, player)   
          ship_obj.place_random_ship()     
          if  not ship_obj.check_too_close(ships.all_keepouts()):
            location_ok = True                                                                           
          # go back and try again 
          if loop > 100:
            print('unable to position ships')
            return None            
        if location_ok:          
          ships.add_ship(ship_obj)
    time_taken = time() - tstart
    #print (f'Time taken for {player} ships = {time_taken} secs')       
    return ships      
      
  def print_board(self, most_recent_move=None, optimal_locations=None):
    """
    Display the  players game board, we neve see ai
    """
    if optimal_locations is None:
      optimal_locations = []
      self.gui.valid_moves(self.all, message=None, alpha=0.1)
    else:
      self.gui.valid_moves(optimal_locations, message=None, alpha=0.5)
      
    #if most_recent_move:
    #  board_rc(most_recent_move, self.game_board, POSSIBLE)
      
    self.gui.update(self.game_board)
    player = ['', 'AI']
    total = [self.ships.count_remaining_ships(),
              self.ai_ships.count_remaining_ships()]       
    totals = "".join(total[0]) + "".join(total[1])       
    self.gui.set_text(self.human_ships_status,''.join(self.ships.count_remaining_ships()))
    self.gui.set_text(self.ai_ships_status, ''.join(self.ai_ships.count_remaining_ships()))      
    #self.gui.set_moves(totals, font=('Avenir Next', 25))


  def print_space_densities(self):
    """
    Prints out the space densities chart on gui
    """
    print('toggle', self.toggle_density_chart)
    if self.toggle_density_chart:
      self.gui.gs.clear_numbers()
      self.print_ships(self.ships)
      self.toggle_density_chart = not self.toggle_density_chart
      return
      
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
        
    density_ =[]
    space_densities = self.generate_space_densities()
    max_score, min_score = -1, 100000
    max_score = max(max_score, max(max(x) for x in space_densities))
    min_score = min(min_score, min(min(x) for x in space_densities))
        
    for row_index, row in enumerate(space_densities):   
      for col_index, value in enumerate(row):
        color = get_color(value, max_score, min_score)
        density_.append(Squares((row_index, col_index), int(value), color))
    self.gui.add_numbers(density_)
    
    self.toggle_density_chart = not self.toggle_density_chart
      

  def game_over(self):
    """
    Checks if the game is over
    """
    for ships in [self.ships, self.ai_ships]:
      if len(ships.ships) <= 0:
        return 'AI' if ships == self.ships else 'You'
    for board in [self.game_board, self.ai_board]:
      if not any(EMPTY in row for row in board):
        return  'AI' if board == self.game_board else 'You'   
    return False


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
      for shipSize, numShips in selfremaining_ships.items():
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
    for ship_size, num_ships in self.remaining_ships.items():
      if not 1 <= ship_size <= 4:
        print(f"Invalid ship size: {ship_size}")
        return False
      if not num_ships >= 0:
        print(f"pInvalid number of ships remaining for size {ship_size}: {num_ships}")
        return False
    if sum(self.remaining_ships.values()) == 0:
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
          self.remaining_ships[int(ship_size.strip())] = int(num_ships.strip())
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
  

  def create_density_pyramid(self, ships=None):
    """
    Create a pyramid-shaped 2D list that contains the scores for each index given an open sequence of n spaces.
    This will make the generate_space_densities function faster
    """
    # allow for two maps, human and ai
        
    ships.create_density_pyramid()
    
  def generate_space_densities(self, board=None, player=None):
    """
    Generate a board where each space has densities that relate to the number of ways ships could be placed there
    NOTE: The implementation is ugly, but it works. I was trying to get this done as quick as possible.
    """
    if player == 'ai': 
      p = 1
      gb = self.ai_board
      ships = self.ships
    else: 
      p = 0
      gb = self.game_board
      ships = self.ai_ships
      
    def fill_list_with_density_pyramid_data(arr, start_index, sequence_length, ships):
      """
      Take data from the density pyramid and populate a portion of the given list with that data
      """
      data = ships.density_pyramid[sequence_length - 1]
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
        fill_list_with_density_pyramid_data(space_densities[r], next_open_spot, next_unavailable_index - next_open_spot, ships)
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
        fill_list_with_density_pyramid_data(density_col, next_open_spot, next_unavailable_index - next_open_spot, ships)
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
    # check for finish
    if sum([num_left  for ship_size, num_left in ships.remaining_ships.items()]) == 0:
      return None
    largest_remaining_ship_size = max(ship_size for ship_size, num_left in ships.remaining_ships.items() if num_left > 0)
    max_density = max(max(val) for val in space_densities)
    for r in range(self.SIZE):
      for c in range(self.SIZE):
        spot = gb[r][c]
        if spot == HIT:
          space_densities[r][c] = 0
          
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
              space_densities[r][c - 1] = (max_density + leftward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c-1))
              # space_densities[r][c - 1] *= (leftward_space + 1)
            if c + 1 < self.SIZE and gb[r][c + 1] == EMPTY:
              space_densities[r][c + 1] = (max_density + rightward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c+1))
              # space_densities[r][c + 1] *= (rightward_space + 1)
          else:
            # no neighboring spaces have been hit, so we don't know the alignment of the ship
            cols = [row[c] for row in gb]
            downward_space, upward_space = get_num_open_neighbors_in_direction(
              cols, r, largest_remaining_ship_size
            )
            rightward_space, leftward_space = get_num_open_neighbors_in_direction(
              gb[r], c, largest_remaining_ship_size
            )
            if 0 <= r - 1 and gb[r-1][c] == EMPTY:
              space_densities[r - 1][c] = (max_density + upward_space) * (1 + 0.02 * get_num_immediate_neighbors(r-1, c))
              # space_densities[r - 1][c] *= (upward_space + 1)
            if r + 1 < self.SIZE and gb[r+1][c] == EMPTY:
              space_densities[r + 1][c] = (max_density + downward_space) * (1 + 0.02 * get_num_immediate_neighbors(r+1, c))
              # space_densities[row_index + 1][col_index] *= (downward_space + 1)
            if 0 <= c - 1 and gb[r][c - 1] == EMPTY:
              space_densities[r][c - 1] = (max_density + leftward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c-1))
              # space_densities[row_index][col_index - 1] *= (leftward_space + 1)
            if c + 1 < self.SIZE and gb[r][c + 1] == EMPTY:
              space_densities[r][c + 1] = (max_density + rightward_space) * (1 + 0.02 * get_num_immediate_neighbors(r, c+1))
              # space_densities[r][c + 1] *= (rightward_space + 1)
  
    return space_densities
  
  
  def get_optimal_moves(self,board=None, player=None):
    """
    Get a list of the coordinates of the best moves
    """
    if board is None:
      board = self.game_board
    space_densities = self.generate_space_densities(board, player)
    if space_densities is None:
      return None
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
  
          
  def wait_for_gui(self):
    # loop until dat received over queue
    while True:
      # if view gets closed, quit the program
      if not self.gui.v.on_screen:
        print('View closed, exiting')
        sys.exit() 
        break   
      #  wait on queue data, either rc selected or function to call
      sleep(0.2)
      if not self.q.empty():
        data = self.q.get(block=False)
        self.q.task_done()
        #print(f'got {data} from queue')
        if isinstance(data, tuple) or isinstance(data, list):
          coord = self.gui.ident(data)
          break
        else:
          try:
            #print(f' trying to run {data}')
            data()
          except (Exception) as e:
            print(f'Error in received data {data}  is {e}')
    return coord
  
  def get_player_move(self, board=None):
    """Takes in the user's input and performs that move on the board, returns the coordinates of the move"""
    if board is None:
        board = self.game_board
    prompt = (f"Select  position (A1 - {self.COLUMN_LABELS[-1]}{self.SIZE})")
    # sit here until piece place on board   
    while True:
      self.gui.set_prompt(prompt, font=('Avenir Next', 25))
      
      spot = self.wait_for_gui() 
      spot = spot.strip().upper()
      row = int(spot[1:]) - 1
      col = self.COLUMN_LABELS.index(spot[0])
      if board[row][col] != EMPTY:
        prompt = f"{spot} is already taken, please choose another:"
      else:
        break
    return (row, col) 
  
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
  
  def restart(self):
    self.gui.gs.close()
    self.finished = False
    self.__init__() 
    self.run()
        
  def wait(self):
    #wait until closed by gui or new game
    while True:
      if not self.gui.v.on_screen:
        print('View closed, exiting')
        return True
        break
      if self.finished: # skip if in game
        try:
          if not self.q.empty():
            item = self.q.get(block=False)
            # print('item', item)
            if item is self.quit:
              return True
            item()
        except (Exception) as e:
          print(e)
      
      sleep(0.5)    
    
if __name__ == '__main__':
  g = BattleShip()
  g.run()
  while(True):
    quit = g.wait()
    if quit:
      break



