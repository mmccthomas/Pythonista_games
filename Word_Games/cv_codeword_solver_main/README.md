# Codeword Puzzle Solver

## Introduction

This is a Python project that uses computer vision and deep learning to solve codeword puzzles from natural images. The relevant puzzle elements are extracted and interpreted, the puzzle is solved, and finally the solution is displayed back on the original image. The solver uses a depth-first search to deduce the correct letter-number pairs to decode the words in the puzzle grid. [OpenCV](https://opencv.org/) was used for image processing, and [Keras](https://keras.io/) for the deep learning number/letter classification models. 

A number of sample images of codeword puzzles with varied lighting, angles, and backgrounds, are provided in `data/codeword_images/`.

Check out my [Sudoku solver](https://github.com/rg1990/cv-sudoku-solver) project too!

## Table of Contents

- [Codeword Puzzle Description](#codeword-puzzle-description)
- [Features](#features)
- [Algorithm and Data Structures](#algorithm-and-data-structures)
- [Heuristics](#heuristics)
- [Installation](#installation)
- [Current Limitations](#current-limitations)
- [Future Developments](#future-developments)
- [Contributing](#contributing)
- [Licence](#licence)


## Codeword Puzzle Description
A codeword is a type of word puzzle that looks similar to a crossword. The 2D puzzle grid contains white and black squares. White cells each contain a number between 1 and 26, where each number encodes one letter of the alphabet. A number of decoded number-letter pairs are provided as a starting point. To solve the puzzle, the player must successfully decode the number-letter pairs such that all of the resulting words on the grid are valid English words.

This is an example of a codeword puzzle:<br>
![small_codeword_example](https://github.com/rg1990/cv-codeword-solver/assets/70291897/b75ad6af-2c34-481e-b250-094f2c634441)


## Features
Current:
- Automatically solves codeword puzzles by deducing number-letter pairs.
- Implements a depth-first search to explore various possibilities and find solutions.

Upcoming:
- Locate, extract and interpret the codeword puzzle from an image.
- Solve the puzzle and annotate the original image with the decoded words.

## Algorithm and Data Structures
- A depth-first search is used to (...TODO...)

- A trie data structure is used to store a dictionary of approximately 370,000 English words, sourced from [here](https://github.com/dwyl/english-words/tree/master)<sup>[1]</sup>.
- The use of a trie enables fast searching to check the validity of candidate words. The trie implementation also supports the use of a wildcard character (```.```), which is used in place of encoded letters, allowing us to search the trie for partially-encoded words to assess their validity.

<!--- - A Python dictionary is used to store decoded number-letter pairs. --->


## Heuristics
The following tricks are used to reduce the time taken to solve a puzzle (in some experiments, from 3 **minutes** to 0.05 **seconds**.)
- Count the occurrences of numbers in the grid and search over the numbers in order of most to least frequently occurring.
- Sort the letters of the alphabet according to their frequency of use in English. When subsituting candidate letters for a particular number, start with the most common letters first.

## Installation
Follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/rg1990/cv-codeword-solver.git
   cd cv-codeword-solver
2. Set up a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    venv\Scripts\activate
3. Install the required dependencies:
   ``` bash
   pip install -r requirements.txt
    ```

## Usage
- (...TODO...)


## Current Limitations
- (...TODO...)


## Future Developments
- Create a game where the user can upload an image of a codeword, which is interpreted to generate an on-screen representation of the puzzle in a GUI. The user can then solve the puzzle interactively and have access to hints, or the final solution.





## Contributing
Contributions are always welcome. If you find a bug or have suggestions for improvement, feel free to open an issue or submit a pull request.

## Licence
This project is open-source software licensed under the MIT License. Feel free to modify and distribute the code as per the terms of this license.

---
[1] A note on the word list: I realised that the word list contained some inappropriate words. I have tried to clean it up, but please be aware that some may remain.
