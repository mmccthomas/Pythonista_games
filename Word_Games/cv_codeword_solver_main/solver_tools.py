# from https://github.com/rg1990/
# added some debug code to allow diagnosis when solver fails
# due to missing word or incorrect numbers
# allow detection of missing word in dictionary
# allow debug of incorrect number at location
# CMT JAN 2025
import time
import string
import numpy as np
import re
import inspect

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        
        
class WordDictionary:
    def __init__(self):
        self.root = TrieNode()      

    def add_word(self, word):
        current_node = self.root
        for character in word:
            current_node = current_node.children.setdefault(character, TrieNode())
        # Node for final char in word. Set flag is_word to True
        current_node.is_word = True
        
    def search(self, word):
        def dfs(node, index):
            if index == len(word):
                return node.is_word
               
            if word[index] == ".":
                for child in node.children.values():
                    if dfs(child, index+1):
                        return True
                    
            if word[index] in node.children:
                return dfs(node.children[word[index]], index+1)
            
            return False
        return dfs(self.root, 0)
                

class CodewordSolverDFS():
    
    def __init__(self, encoded_words, code_dict, word_trie, use_heuristics=True):
        """
        Args:
            encoded_words (list[list[int]]): List with one sub-list per encoded word.
                Sub-lists contain integers representing encoded letters.
            code_dict (dict): A dictionary containing the initial number-letter
                pairs provided as a starting point for the puzzle.
            word_trie (WordDictionary): Trie data structure containing all
                valid words.
            use_heuristics (bool): If True, apply sorting to lists of available
                numbers and letters to reduce the time taken to solve.

        """
        # TODO - Determine which methods and attributes should be public/private
        
        self.encoded_words = encoded_words
        self.code_dict = code_dict
        self._word_trie = word_trie
        self.debug = False
        self.best = 0
        self.word_missing_dict = {}
        self.best_wordset = []
        # find initial level for recursion depth reporting
        self.initial_depth = len(inspect.stack())
        
        # Create a list of letters sorted by most frequently occurring
        self._letter_frequency = [str(char) for char in "etaonihsrlducmwyfgpbvkjxqz"]
        # Get lists of letters and numbers which are not yet paired
        self.available_letters, self.unknown_numbers = self._initialise_letter_and_number_lists(code_dict, encoded_words, use_heuristics)
    
    
    def update_puzzle(self, new_encoded_words, new_code_dict, use_heuristics=True):
        '''
        Update the details of the puzzle without having to create a new instance
        of the class.
        
        Args:
            new_encoded_words (list[list[int]]): List with one sub-list per encoded word.
                Sub-lists contain integers representing encoded letters.
            new_code_dict (dict): A dictionary containing the initial number-letter
                pairs provided as a starting point for the puzzle.
            use_heuristics (bool): If True, apply sorting to lists of available
                numbers and letters to reduce the time taken to solve.
        '''
        self.encoded_words = new_encoded_words
        self.code_dict = new_code_dict
        
        # Get lists of letters and numbers which are not yet paired
        self.available_letters, self.unknown_numbers = self._initialise_letter_and_number_lists(new_code_dict, new_encoded_words, use_heuristics)
    
    
    def _initialise_letter_and_number_lists(self, code_dict, encoded_words, use_heuristics):
        '''
        Generate lists of letters and numbers that are not included in the
        number-letter pairings provided in the puzzle's initial state.
        Optionally sort the resulting lists using heuristics to enable faster
        solving.
    
        Args:
            code_dict (dict): A dictionary containing the initial number-letter
                pairs provided as a starting point for the puzzle.
            encoded_words (list[list[int]]): List with one sub-list per encoded word.
                Sub-lists contain integers representing encoded letters.
            use_heuristics (bool): If True, sort available_letters by the letter
                frequency in English, and sort empty_numbers by their frequency
                in the puzzle, most common first.
    
        Returns:
            available_letters (list): List of letters that are not part of a
                number-letter pair in code_dict.
            empty_numbers (list): List of numbers that are not part of a
                number-letter pair in code_dict.
        
        '''
        if use_heuristics:
            # Count how many times each coded number is found in the puzzle
            encoded_words_flat = np.hstack(encoded_words)
            # Find out how many instances of each coded number the puzzle contains
            numbers, counts = np.unique(encoded_words_flat, return_counts=True)
            number_counts = np.array(list(zip(numbers, counts)))
            # Sort by number of occurrences, most frequent first
            number_counts = number_counts[number_counts[:, 1].argsort()[::-1]]
            # Get the unknown numbers, sorted by frequency in puzzle
            empty_numbers = [num for num in number_counts[:,0] if code_dict[num] == "."]
            # Get the available letters, sorted by their frequency in English
            available_letters = [l for l in self._letter_frequency if l not in code_dict.values()]
        else:
            # Simplified default case with no heuristics, for testing backtracking
            available_letters = [l for l in string.ascii_lowercase if l not in code_dict.values()]
            empty_numbers = [num for num, letter in code_dict.items() if letter == "."]
        
        return available_letters, empty_numbers
    
    
    def solve(self, encoded_words=None, available_letters=None, empty_numbers=None):
        """
        Recursively solve for the letter assignments in a list of encoded words.
    
        This method attempts to solve for the missing letter assignments in the encoded words,
        given a list of available letters and a list of numbers without assigned letters.
    
        Args:
            encoded_words (list): List of lists. One sub-list per encoded word,
                containing integers representing encoded letters.
            available_letters (list): A list of available letters to choose from for
                assigning to the missing numbers.
            empty_numbers (list): A list of numbers without letters assigned to them.
    
        Returns:
            bool: True if valid letter assignments are successfully found for
                all numbers, False otherwise.
                
        CMT added some debug to allow diagnosis when solver fails
        Helps to  Highlight missing word in wordlist, or incorrect numbers
        """
        def score(decoded_words):
            """ count the number of alpha characters as percentage of total"""
            total_len = len(''.join(decoded_words))
            alpha = sum([c.isalpha() for c in ''.join(decoded_words)])
            return int(100 * alpha / total_len)
                    
        # Assignments for initial call to solve
        if encoded_words is None:
            encoded_words = self.encoded_words.copy()
        if available_letters is None:
            available_letters = self.available_letters.copy()
        if empty_numbers is None:
            empty_numbers = self.unknown_numbers.copy()
        
        
        # Base case - no more numbers without letters, so we are finished
        if not empty_numbers:
            return True
        else:
            num = empty_numbers[0]
          
        # Try every available letter in place of the current empty number
        if self.debug: print(f'Recursion depth >>>>>>>>>>>>>>>>>>>>>> {len(inspect.stack())- self.initial_depth}')
        for letter in available_letters:
            # Check if this letter is valid for this number
            self.code_dict[num] = letter
            decoded_words = self.decode_words_in_list(encoded_words)
            if self.debug:
                print(f'Number {num}: Trying {letter}')
                # capitalise the letter being tested                
                words = [''.join([_letter.upper() if no == num else _letter
                                  for no, _letter in zip(number, word)])
                         for number, word in  zip(encoded_words, decoded_words)]
                print('Decoded words would be', words)
            
            if self.all_words_are_valid(decoded_words):
                if self.debug: print(f'VALID. Completion {score(decoded_words)}%\n')
                # Create letter/number lists to pass to next call to solve()
                next_available_letters = [l for l in available_letters if l != letter]
                next_empty_numbers = [number for number in empty_numbers if number != num]
                if self.solve(encoded_words, next_available_letters, next_empty_numbers):
                    # This means there are no more empty numbers, so we are finished
                    return True      
            else:
                if self.debug:
                   # show trial and invalid word
                   print(f'NOT valid. Completion {score(decoded_words)}%\n')
                   ok_words = [self._word_trie.search(search_string) for search_string in decoded_words]
                   list_invalid = [word for word, ok in zip(decoded_words, ok_words) if not ok]
                   print('invalid ', list_invalid)                                
                   # calculate a score of number of alpha characters in words
                   best = score(decoded_words)                                        
                   if best  > self.best:
                       self.best_wordset = decoded_words.copy()
                       self.best = best      
                   if len(list_invalid) == 1: 
                       print('above word may not be in wordlist')
                       self.word_missing_dict[best] = (list_invalid[0], ok_words.index(False))                             
                   print()
                   print(f'No more letters so previous guess is incorrect, backing up to depth {len(inspect.stack())- self.initial_depth -1}\n')
                # We have run out of letters to try. Undo assignment, then backtrack.
                self.code_dict[num] = "."
        return False

    def decode_words_in_list(self, encoded_word_list):        
        '''
        Given a list of encoded words, each represented by a list of integers,
        generate a list of decoded strings, each comprising letters and possibly
        wildcard characters (".").

        Args:
            encoded_word_list (list): List of lists. One sub-list per encoded word,
                containing integers representing encoded letters.
        
        Returns:
            (list): List of decoded strings, where each contains letters or the
                placeholder "." for unknown letters.
        '''
        return ["".join([self.code_dict[num] for num in encoded_word]) for encoded_word in encoded_word_list]


    def all_words_are_valid(self, word_list):
        '''
        For each word in word_list, including words containing wildcard characters ("."),
        search the trie to find a match. Unless there is a match for every word in
        word_list, return False.
        
        Args:
            word_list (list): List of decoded words, possibly containing
                wildcard characters.
                
        Returns:
            bool: True if there exists a match in the trie for every word in
                word_list, else False.
        '''
        return all([self._word_trie.search(search_string) for search_string in word_list])
            
    def print_decoded_letters(self):
        '''
        Print the letters assigned to the numbers in self.code_dict, displaying
        13 letters per row, to match the format of the example puzzles.
        '''
        print("\nDecoded letters:")
        for i, letter in enumerate(self.code_dict.values()):
            # Split the decoded letters into 2 rows like in the puzzle key        
            end_str = "\n" if (i+1) % 13 == 0 else " "
            print(f"{letter.upper()}", end=end_str)
            






