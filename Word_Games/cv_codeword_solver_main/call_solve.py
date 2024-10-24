import time
import numpy as np
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
#from codeword_puzzles import get_puzzle
from solver_tools import CodewordSolverDFS, WordDictionary


def check_results(word_trie, decoded_words):
    # Check if the solver failed and notify the user
    if np.any(["." in word for word in decoded_words]):
        print("Solving failed! Incomplete words remain in decoded_words. Check puzzle details are correct.")
    
    # Catch the case where the words don't have wildcards, but are nonsense words
    if not np.all([word_trie.search(word) for word in decoded_words]):
        raise RuntimeError(f"One or more decoded words are not valid:\n{decoded_words}")


def solve():
    '''
    Demonstration using CodewordSolverDFS class to solve two example codeword
    puzzles sourced from codeword_puzzles.py.
    
    
    '''
    
    # Load the list of words and construct the trie
    print("Building trie word dictionary...\n")
    with open("data/words_alpha.txt") as word_file:
        word_list = set(word_file.read().split())
        word_trie = WordDictionary()
        for word in word_list:
            word_trie.add_word(word)
    
    
    # Get an example puzzle (choose from 12, 13, 15 or 19)
    example_code_dict, all_encoded_words, solution = get_puzzle(12)
    # Create a CodewordSolver instance
    solver = CodewordSolverDFS(all_encoded_words, example_code_dict.copy(), word_trie, use_heuristics=True)
    # Solve the codeword
    start_time = time.perf_counter()
    solver.solve()
    end_time = time.perf_counter()
    print(f"Solving the first puzzle took {end_time - start_time:.3f} seconds.\n")
    
    # Check if the solver failed and notify the user
    decoded_words = solver.decode_words_in_list(all_encoded_words)
    check_results(word_trie, decoded_words)
    print(f"Decoded words:\n{decoded_words}")
    solver.print_decoded_letters()
    
if __name__ == "__main__":
    main()
