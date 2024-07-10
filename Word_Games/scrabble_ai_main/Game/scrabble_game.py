import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from Game.scrabble_objects import *
from AI.scrabble_wordfinder import *
#import pygame as p
import time

# TODO Improve by adding sim ?

class GameState:
    def __init__(self, multiplier_file, tile_file):
        self.board = Board(multiplier_file)
        self.pouch = Pouch(tile_file)
        self.player_1 = Player()
        self.player_1.name= 'Human'
        self.player_2 = Player()
        self.player_2.name= 'AI'
        self.p1_to_play = True
        self.game_ended = False
        for _ in range(7):
            self.player_1.draw_tile(self.pouch)
            self.player_2.draw_tile(self.pouch)
        #self.player_1.rack.tiles[0] = Tile('A', 2)
        
    def current_player(self):
        current_player = self.player_1 if self.p1_to_play else self.player_2
        return current_player

class GameEngine:
    def __init__(self, gamestate, word_list_file):
        self.gamestate = gamestate
        self.word_finder = WordFinder(word_list_file, gamestate.board)
        self.exchanges = 0
        self.autoplay = False
        self.ai_possible_moves = list()
        self.ai_possible_move_ids = list()
        self.logs = list()
        
    
        
    def play_draft(self):   

        # Find the coordinates of the tiles played by the player
        played_cells = self.get_draft()
        board_obj = self.gamestate.board

        # Check if it is the first ever word and if it is check if it is played on the center
        first_play = board_obj.is_empty((7, 7), False)
        if first_play:
            for cell in played_cells:
                if cell.position == (7, 7):
                    break
            else:
                self.logs.append("First play is not in the center")
                return

        # Check if played tiles are in the same direction
        is_horizontal = all(cell.position[0] == played_cells[0].position[0] for cell in played_cells)
        is_vertical = all(cell.position[1] == played_cells[0].position[1] for cell in played_cells)
        if not(is_horizontal or is_vertical):
            self.logs.append("Tiles played are not in the same direction")
            return
        
        # Check if played tiles are connected
        prev_pos = -1
        for cell in played_cells:
            cur_pos = cell.position[1] if is_horizontal else cell.position[0]
            if prev_pos != -1:
                for diff in range(cur_pos - prev_pos):
                    if is_horizontal and board_obj.is_empty((cell.position[0], prev_pos + diff + 1)):
                        self.logs.append("Horizontal played tiles are not connected.")
                        return
                    if is_vertical and board_obj.is_empty((prev_pos + diff + 1, cell.position[1])):
                        self.logs.append("Vertical played tiles are not connected.")
                        return
            prev_pos = cur_pos
        
        # Check if played word is anchored to some existing word
        for cell in played_cells:
            i = cell.position[0]
            j = cell.position[1]
            if (i > 0 and not board_obj.is_empty((i - 1, j), False)) or (i < 14 and not board_obj.is_empty((i + 1, j), False)) or \
               (j > 0 and not board_obj.is_empty((i, j - 1), False)) or (j < 14 and not board_obj.is_empty((i, j + 1), False)):
               break
        else:
            if not first_play:
                self.logs.append("Word played is not anchored to an existing tile")
                return
            
        # Get all new words the player created
        main_word_cells = self.find_word_in_direction(*played_cells[0].position, is_horizontal)
        side_words_cells = list()

        for cell in played_cells:
            cur_side_word = self.find_word_in_direction(*cell.position, not is_horizontal)
            if len(cur_side_word) > 1:
                side_words_cells.append(cur_side_word)

        main_word_str = self.get_word_str_from_cells(main_word_cells)
        side_words_str = [self.get_word_str_from_cells(word_cells) for word_cells in side_words_cells]

        all_words = list()
        if not(len(main_word_str) == 1 and len(side_words_str) > 0):
            all_words.append(main_word_str)
        all_words.extend(side_words_str)

        # Check if newly formed words exist in the dictionary
        bad_word = []
        for word in all_words:
          #print('word', word, word in self.word_finder.trie.word_list, len(self.word_finder.trie.word_list))
          test = not self.is_valid_word(word)
          bad_word.append(test)
        if any(bad_word):
            self.logs.append(f'Not all formed words {all_words} are valid')
            #clear word
            for cell in played_cells:
              r,c = cell.position
              self.gamestate.board.board[r][c].tile = None
            # set rack
            current_player = self.gamestate.current_player()
            for tile in current_player.rack.tiles:
               tile.draft = False
            return False

        # Calculate the score for each word

        main_word_score = self.calculate_score_of_word(main_word_cells)
        side_word_scores = [self.calculate_score_of_word(side_word_cells) for side_word_cells in side_words_cells]

        # Calculate the play score
        
        play_score = main_word_score + sum(side_word_scores)
        if len(played_cells) == 7:
          play_score += 50

        # Update and swap the player letters if there are enough tiles 

        current_player = self.gamestate.current_player()
        current_player.rack.remove_played_tiles()
        current_player.rack.fill_empty_tiles(self.gamestate.pouch)

        # Add the score to the player and save the draft

        current_player.score += play_score

        for cell in played_cells:
            cell.tile.draft = False
            
        self.logs.append(f'{current_player.name} played {main_word_str} for {play_score}')

        self.gamestate.p1_to_play = not self.gamestate.p1_to_play

        #self.exchanges = 0
        self.check_game_end()

        # Make AI move if AI turn & autoplay enabled
        #if not self.gamestate.p1_to_play:
        #    self.ai_handle_turn()
        return True

    def ai_handle_turn(self):
        if self.autoplay:
            time.sleep(0.1) # delay for observability
            self.ai_make_move()
            return
        
        all_options = self.word_finder.find_all_plays(self.gamestate.player_1.rack if self.gamestate.p1_to_play else self.gamestate.player_2.rack)
        points = list()
        sim_points = list()
        all_words = list()
        
        for option in all_options:
            point, option_words = self.calculate_option_point(option, True)
            #sim_point = self.simulate_option_point(option)
            points.append(point)
            #sim_points.append(sim_point)
            all_words.append(option_words)

        option_ids = []
        for i in range(len(all_options)):
            option_ids.append(f'{points[i]} - {all_words[i]}')
            # option_ids.append((str(points[i]) + " - " + "{:.2f}".format(sim_points[i]) + " - " + str(all_words[i]),))

        sorted_option_idx = [x for x,y in sorted(enumerate(points), key = lambda x: (points[x[0]], all_words[x[0]]))]
        sorted_option_idx.reverse()

        self.ai_possible_moves = [all_options[i] for i in sorted_option_idx]
        self.ai_possible_move_ids = [option_ids[i] for i in sorted_option_idx]
        
    def ai_make_move(self, gui=None):
        player = self.gamestate.current_player() #self.gamestate.player_1 if self.gamestate.p1_to_play else self.gamestate.player_2
        all_options = self.word_finder.find_all_plays(player.rack)
        
        points = list()
        
        for i, option in enumerate(all_options):
            points.append(self.calculate_option_point(option))
            if gui:
               gui.set_prompt(f'{player} considering  {i}/{len(all_options)} options')
          
        if len(all_options) > 0:
            option = all_options[max(enumerate(points), key=lambda x: x[1])[0]]
            for cell, tile in option.items():
                cell.tile = tile
                tile.draft = True
            if False: #gui:
               letters = ''.join([t.letter for t in option.values()])
               gui.set_prompt(f'{player} playing  {letters}')
            self.play_draft()
        else:
            swapped = self.swap_draft(True)
            if not swapped:
                self.pass_turn()
                self.check_game_end()

    def play_option(self, option_idx):
        for cell, tile in self.ai_possible_moves[option_idx].items():
            cell.tile = tile
            tile.draft = True
        self.play_draft()

    def clear_draft(self):
        for pos in self.gamestate.board.all_positions():
            cell = self.gamestate.board.board[pos[0]][pos[1]]
            if cell.tile is not None and cell.tile.draft:
                cell.tile.draft = False
                cell.tile = None

    def simulate_option_point(self, option, sim_times = 1, half_depth = 1):

        self.clear_draft()

        # snapshot before changes

        save_board_tiles = [[cell.tile for cell in self.gamestate.board.board[i]] for i in range(15)]
        save_rack_tiles_1 = self.gamestate.player_1.rack.tiles
        save_rack_tiles_2 = self.gamestate.player_2.rack.tiles
        save_score_1 = self.gamestate.player_1.score
        save_score_2 = self.gamestate.player_2.score
        save_pouch_tiles = self.gamestate.pouch.tiles
        save_p1_to_play = self.gamestate.p1_to_play
        save_game_ended = self.gamestate.game_ended
        save_exchanges = self.exchanges
        save_logs = self.logs

        #

        total_point_gain = 0
        for _ in range(sim_times):

            # prepare for sim
            self.gamestate.player_1.rack.tiles = save_rack_tiles_1.copy()
            self.gamestate.player_2.rack.tiles = save_rack_tiles_2.copy()
            self.gamestate.pouch.tiles = save_pouch_tiles.copy()
            self.gamestate.player_1.score = save_score_1
            self.gamestate.player_2.score = save_score_2
            self.gamestate.p1_to_play = save_p1_to_play
            self.gamestate.game_ended = save_game_ended
            self.exchanges = save_exchanges
            self.logs = save_logs.copy()
            #

            # randomize opponent rack
            is_p1_to_play = self.gamestate.p1_to_play
            opponent = self.gamestate.player_2 if self.gamestate.p1_to_play else self.gamestate.player_1
            opponent_rack = opponent.rack
            self.gamestate.pouch.tiles += opponent_rack.tiles
            opponent_rack.tiles.clear()
            opponent_rack.fill_empty_tiles(self.gamestate.pouch)

            # make first option a draft and play that draft
            for cell, tile in option.items():
                cell.tile = tile
                tile.draft = True

            self.play_draft()

            # make tree moves as much as depth
            for _ in range(half_depth * 2):
                if self.gamestate.game_ended:
                    break
                self.ai_make_move()

            # point gain
            total_point_gain += ((self.gamestate.player_1.score - self.gamestate.player_2.score) - (save_score_1 - save_score_2)) if is_p1_to_play\
            else ((self.gamestate.player_2.score - self.gamestate.player_1.score) - (save_score_2 - save_score_1))

            # roll back board snapshot
            for i in range(15):
                for j in range(15):
                    self.gamestate.board.board[i][j].tile = save_board_tiles[i][j]

        # roll back the snapshot
        self.gamestate.player_1.rack.tiles = save_rack_tiles_1
        self.gamestate.player_2.rack.tiles = save_rack_tiles_2
        self.gamestate.pouch.tiles = save_pouch_tiles
        self.gamestate.player_1.score = save_score_1
        self.gamestate.player_2.score = save_score_2
        self.gamestate.p1_to_play = save_p1_to_play
        self.gamestate.game_ended = save_game_ended
        self.exchanges = save_exchanges
        self.logs = save_logs
        #

        # return avg point gain
        return total_point_gain / sim_times

    def calculate_option_point(self, option, return_words =  False):
        cells = list(option.keys())
        for cell, tile in option.items():
            cell.tile = tile
            tile.draft = True
            
        is_horizontal = True
        if len(cells) > 1:
            if cells[0].position[1] == cells[1].position[1]:
                is_horizontal = False
        main_word = self.find_word_in_direction(*cells[0].position, is_horizontal)
        side_words = list()
        for cell in cells:
            found_word = self.find_word_in_direction(*cell.position, not is_horizontal)
            if len(found_word) > 1:
                side_words.append(found_word)

        all_words = list()
        if not(len(main_word) == 1 and len(side_words) > 0):
            all_words.append(main_word)
        all_words.extend(side_words)
        
        point = 0
        for word in all_words:
            point += self.calculate_score_of_word(word)
        if len(cells) == 7:
            point += 50 # add bingo point

        if return_words:
            words = list()
            for word in all_words:
                words.append(self.cells_to_word(word))
            for cell, tile in option.items():
                cell.tile = None
                tile.draft = False
            return point, words

        for cell, tile in option.items():
            cell.tile = None
            tile.draft = False

        return point

    def swap_draft(self, swap_all = False):

        player = self.gamestate.current_player()
        player_rack = player.rack
        is_swap_allowed = self.gamestate.pouch.tiles_amount() >= 7

        
        if is_swap_allowed and swap_all:
            for tile in player_rack.tiles:
                if tile is not None:
                    tile.draft = True

        tiles_to_swap = 0
        for tile in player_rack.tiles:
            if tile is not None and tile.draft:
                tiles_to_swap += 1

        if is_swap_allowed:
            old_tiles = list()
            for i, tile in enumerate(player_rack.tiles):
                if tile.draft:
                    player_rack.tiles[i] = None
                    tile.draft = False
                    old_tiles.append(tile)
            
            for _ in range(tiles_to_swap):
                player.draw_tile(self.gamestate.pouch)
            
            for tile in old_tiles: 
                self.gamestate.pouch.add_tile(tile)
            
            self.clear_draft()             
            self.pass_turn()
            
           
            #if tiles_to_swap == 0:
            self.logs.append(f'{player.name} passed turn ({self.exchanges})')
            self.check_game_end()
            return True
        else:
            if tiles_to_swap > 0:
                self.logs.append(f'{player.name} swap failed, not enough tiles ({tiles_to_swap})')
                self.clear_draft()   
                return False
            else:
                self.clear_draft()   
                self.pass_turn()
                self.logs.append(f'{player.name} passed turn ({self.exchanges})') 
                self.check_game_end()
                return True

    def get_draft(self):
        # Find the coordinates of the tiles played by the player
        played_cells = []
        board_obj = self.gamestate.board
        board = board_obj.board
        for pos in board_obj.all_positions():
            i, j = pos
            cell = board[i][j]
            if cell.tile is not None and cell.tile.draft:
                played_cells.append(cell)

        return played_cells

    def pass_turn(self):
        self.gamestate.p1_to_play = not self.gamestate.p1_to_play
        self.exchanges += 1

    def check_game_end(self):
        if self.exchanges == 4 or (self.gamestate.pouch.tiles_amount() == 0 and (self.gamestate.player_1.rack.tiles_amount() == 0 or self.gamestate.player_2.rack.tiles_amount() == 0)):
            self.logs.append(" --- GAME ENDED --- ")
            self.gamestate.game_ended = True

    def calculate_score_of_word(self, word_cells):
        word_score = 0
        word_multiplier = 1
        for cell in word_cells:
            point = cell.tile.point
            if cell.tile.draft:
                letter_multiplier = cell.multiplier
                if letter_multiplier == "DL":
                    point *= 2
                elif letter_multiplier == "TL":
                    point *= 3
                elif letter_multiplier == "DW":
                    word_multiplier *= 2
                elif letter_multiplier == "TW":
                    word_multiplier *= 3

            word_score += point

        word_score *= word_multiplier

        return word_score

    def cells_to_word(self, cells):
        word = ""
        for cell in cells:
            word += cell.tile.letter
        return word

    def find_word_in_direction(self, i, j, is_horizontal):
        cur_i = i
        cur_j = j
        cells = list()
        board_obj = self.gamestate.board
        board = board_obj.board
        if is_horizontal:
            while board_obj.has_left((cur_i, cur_j)):
                cur_j -= 1
            while board_obj.has_right((cur_i, cur_j)):
                cells.append(board[cur_i][cur_j])
                cur_j += 1
            cells.append(board[cur_i][cur_j])
        else:
            while board_obj.has_up((cur_i, cur_j)):
                cur_i -= 1
            while board_obj.has_down((cur_i, cur_j)):
                cells.append(board[cur_i][cur_j])
                cur_i += 1
            cells.append(board[cur_i][cur_j])

        return cells

    def get_word_str_from_cells(self, cells):
        word = ""
        for cell in cells:
            word += cell.tile.letter
        return word

    def is_valid_word(self, word):
        
        return self.word_finder.trie.is_word(word)
