Pythonista Games
----------------

This is a series of python word and board games to operate on the iPad using the excellent Pythonista app.

The games all use the Scene module, which is a thin wrapper around the Apple UiKit framework.

A generic gui framework has been developed to place a grid at maximum size, along with buttons and messages


Games are:

Kye
---
My personal favourite from 1992
Full credit to Colin Garbutt for the original program, and Colin Phipps for the Python version.
I have adapted GUI to use Pythonista for IOS rather than pygtk.

Sudoko
-------
Both classic, Killer and KenKen are supported.
The Sudoko solve engine is provided by 
http://norvig.com/sudoku.html

Wordsearch
----------
 Another classic game.
 Multiple word categories included
 
 place engine word_square_gen.py from ?
 
Scrabble
--------
Classic game, based on ai engine from Murat Sahin scrabble_ai_main
Plays a mean game.
Option for AI-AI game

ZipWords
--------
Crossword grid filled with a selection of words.
Find the words to fit
Idea taken from Puzzler magazine

NumberWords
-----------
Crossword grid filled with a selection of words.
Find the letter linked to each number.
Idea taken from Puzzler magazine

Anagram words
-------------
Crossword grid filled with a selection of words.
Find the words to fit

Pieceword
---------
2x2 tiles jumbled on a grid. Use the clues to rearrange them.

Wordle clone
------------
Possibly too simple, as only valid words are presented for selection

Tetris
------
Simple implemation of a classic game. 
An early attempt by me, could be prettier!

Demolition (my own from 1983!)
-----------
VERY simple ball drop program in the style of breakout

SeaBattle
---------
Modified from Game-Pigeon-Solvers by Kyle Gerner
https://github.com/k-gerner/Game-Pigeon-Solvers

Othello
-------
Modified from Game-Pigeon-Solvers by Kyle Gerner
https://github.com/k-gerner/Game-Pigeon-Solvers

Connect4
--------
Modified from Game-Pigeon-Solvers by Kyle Gerner
https://github.com/k-gerner/Game-Pigeon-Solvers

Minesweeper
-----------
Another classic game.

Chess (WIP)
-----------
A gui front end bolted on to https://github.com/niklasf/python/chess
Proof of concept, not complete

Dots
-----
Dots and Boxes 
modified from DotsAndBoxes M Sokhail Zakir/ Ammara Riaz 

Tiles
-----
Sliding puzzle game
can select numbers or any image from the photo library
requires installation of slidingpuzzle from pypi

Caterpillar
-----------
a version of Snake modelled on The Very Hungry Caterpillar for my grandchildren



Much of the  working engines of these games were provided by other developers.
I have added the gui front end for use on ios using Pythonista, along with any changes I saw fit.


