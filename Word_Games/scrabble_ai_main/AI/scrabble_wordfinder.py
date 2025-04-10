from scrabble_ai_main.AI.trie import *
from scrabble_ai_main.Game.scrabble_objects import alphabet

class WordFinder:
    def __init__(self, word_list_file, board):
        self.trie = Trie(word_list_file)
        self.board_obj = board
        self.board = board.board
        self.rack = None
        self.cross_suitable_letters = None
        self.is_horizontal = True
        self.ai_possible_moves = list()

    def find_anchors(self):
        anchors = []
        for pos in self.board_obj.all_positions():
            is_empty = self.board_obj.is_empty(pos)
            neighbor_filled = self.board_obj.has_left(pos) or self.board_obj.has_right(pos) or self.board_obj.has_up(pos) or self.board_obj.has_down(pos) 

            if is_empty and neighbor_filled:
                anchors.append(pos)
        return anchors
    
    def legal_move(self, move_record):
        self.ai_possible_moves.append(move_record.copy())

    def extend_after(self, partial_word, cur_node, next_pos, move_record, anchor_filled):
        if not(self.board_obj.is_inbounds(next_pos) and not self.board_obj.is_empty(next_pos)) and cur_node.is_word and anchor_filled:
            self.legal_move(move_record)
        if self.board_obj.is_inbounds(next_pos):
            if self.board_obj.is_empty(next_pos):
                for i, tile in enumerate(self.rack.tiles):
                    if tile is not None and tile.letter in cur_node.children.keys() and tile.letter in self.cross_suitable_letters[next_pos]:
                        self.rack.tiles[i] = None
                        move_record[self.board_obj.get_pos(next_pos)] = tile
                        self.extend_after(partial_word + tile.letter, cur_node.children[tile.letter], self.board_obj.after(next_pos, self.is_horizontal), move_record, True)
                        move_record.popitem() # Python version > 3.7 is REQUIRED just for this line
                        self.rack.tiles[i] = tile
            else:
                existing_letter = self.board_obj.get_pos(next_pos).tile.letter
                if existing_letter in cur_node.children.keys():
                    self.extend_after(partial_word + existing_letter, cur_node.children[existing_letter], self.board_obj.after(next_pos, self.is_horizontal), move_record, True)

    def before_part(self, partial_word, cur_node, anchor_pos, move_record, limit):
        self.extend_after(partial_word, cur_node, anchor_pos, move_record, False)
        if limit <= 0:
            return
        for i, tile in enumerate(self.rack.tiles):
            if tile is not None and tile.letter in cur_node.children.keys():
                self.rack.tiles[i] = None
                    
                move_record[self.board_obj.get_pos(anchor_pos)] = tile
                records_before_shift = move_record.copy()
                move_record.clear()
                for cell, cell_tile in records_before_shift.items():
                    move_record[self.board_obj.get_pos(self.board_obj.before(cell.position, self.is_horizontal))] = cell_tile

                self.before_part(partial_word + tile.letter, cur_node.children[tile.letter], anchor_pos, move_record, limit - 1)

                move_record.popitem()
                records_before_shift = move_record.copy()
                move_record.clear()
                for cell, cell_tile in records_before_shift.items():
                    move_record[self.board_obj.get_pos(self.board_obj.after(cell.position, self.is_horizontal))] = cell_tile

                self.rack.tiles[i] = tile
    
    def find_all_plays(self, rack):
        self.rack = rack
        self.ai_possible_moves.clear()
        for self.is_horizontal in [True, False]:
            move_record = dict()
            self.cross_suitable_letters = self.get_cross_suitable_letters()
            anchors = self.find_anchors()
            if self.board_obj.is_empty((7, 7)):
                anchors.append((7, 7))
            for anchor_pos in anchors:
                if self.board_obj.has_before(anchor_pos, self.is_horizontal):
                    seek_pos = self.board_obj.before(anchor_pos, self.is_horizontal)
                    partial_word = self.board_obj.get_pos(seek_pos).tile.letter
                    while self.board_obj.has_before(seek_pos, self.is_horizontal):
                        seek_pos = self.board_obj.before(seek_pos, self.is_horizontal)
                        partial_word = self.board_obj.get_pos(seek_pos).tile.letter + partial_word
                    partial_word_node = self.trie.lookup_string(partial_word)
                    if partial_word_node is not None:
                        self.extend_after(partial_word, partial_word_node, anchor_pos, move_record, False)
                else:
                    before_limit = 0
                    seek_pos = anchor_pos
                    # we can prevent merging while extending to the before since there will be an extension to the after of those anchors anyway
                    while self.board_obj.is_inbounds(self.board_obj.before(seek_pos, self.is_horizontal)) and self.board_obj.is_empty(self.board_obj.before(seek_pos, self.is_horizontal)) and self.board_obj.before(seek_pos, self.is_horizontal) not in anchors: # allow near boundaries but prevent merging with a word
                        before_limit += 1
                        seek_pos = self.board_obj.before(seek_pos, self.is_horizontal)
                    
                    self.before_part("", self.trie.root, anchor_pos, move_record, before_limit)
        return self.ai_possible_moves.copy()

    def get_cross_suitable_letters(self):
        check_results = dict()
        for pos in self.board_obj.all_positions():
            if not self.board_obj.is_empty(pos):
                continue
            letters_before = ""
            seek_pos = pos
            while self.board_obj.has_before(seek_pos, not self.is_horizontal):
                seek_pos = self.board_obj.before(seek_pos, not self.is_horizontal)
                letters_before = self.board_obj.get_pos(seek_pos).tile.letter + letters_before
            letters_after = ""
            seek_pos = pos
            while self.board_obj.has_after(seek_pos, not self.is_horizontal):
                seek_pos = self.board_obj.after(seek_pos, not self.is_horizontal)
                letters_after = letters_after + self.board_obj.get_pos(seek_pos).tile.letter
            if len(letters_before) + len(letters_after) == 0:
                suitable_letters = alphabet.copy()
            else:
                suitable_letters = list()
                for letter in alphabet:
                    word  = letters_before + letter + letters_after
                    if self.trie.is_word(word):
                        suitable_letters.append(letter)
            check_results[pos] = suitable_letters
        return check_results
