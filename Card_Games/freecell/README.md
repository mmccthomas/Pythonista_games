# freeCell
This is both a GUI and engine for the game freeCell, and a solver for the game that uses a modified version of A*.
I just have a few things I’d like to point out about this.
First I’ll talk about the really cool things I tried to implement that I hope you don’t 
miss, and then toward the bottom, I try and explain the more confusing things in my code.

Running programs:
1) To Run the GUI, just type in $ python3 player.py — all the fancy features like loading 
files and stuff can be called from the widgets as well
2) To Run the solver, again you can do $ python3 FreeCellSolver.py, but there’s also an 
option for some command line arguments (see the cool stuff section for solver)

GUI Cool Stuff:
1) The Option Panel — The help, hint, quit, and undo buttons all work, and all make for 
	a better experience for sure. However, the really cool feature is the entry widget
	. First, you can manually enter moves (like in the terminal version of the game) 
	. However, with the drag and drop, this seems kind of redundant. However,
	entering the keywords load, save, or execute will also pull up a file dialogue,
	where you can choose a file to load a game from, a file to save the current game
	to, or a file to execute (where every move in the file is carried out). In 
	addition, load, save, and execute can be entered followed by a desired filename, 
	to load, save, or execute that file. The load and execute features make it 
	possible to integrate the solutions from problem 2 into the GUI. Basically, when 
	you use the Solver, it outputs a game file and a move list file. Simply loading 	
	the game file and then executing the move list file will make the solutions really 	
	come alive!

2) The backs of the cards — Not sure if you noticed, but when either initializing a game
	or loading a new game, the cards are back up as they’re dealt out.

3) Change the glide speed — if the cards are moving too fast or too slow, it’s really easy
	to fix. Under the Card class in CardB.py, under the glide method, just change the
	variable step amount to a different integer. The larger the int, the slower the
	cards will move.

4) A really cool workflow -- You start up the player, and see a game. Enter save to save
the game as a file, and pass that filename as a command line argument preceded
by the '-s' flag to the solver to
generate a move list to beat the game. Then, go back to the player, and enter execute,
select this move file to watch yourself win the game!

Solver Cool Stuff:
1) Output files — Again, as the solver runs, it typically outputs two files — a game file 
	and a move list file. by loading the first and executing the second, you can see
	the solution work on the GUI (it’s a lot prettier)

2) Command Line arguments — You can further specify the names for the output files by 	
	using command line args. Simply saying $ python3 FreeCellSolver.py will solve a
	game, but by saying $ python3 FreeCellSolver.py -g game37 -m moveLst37 -s game37.txt , you 
	would load game37.txt (which is hopefully a file in the right form (see save in 
	GameFunctions for details), save another copy as game37, try and solve it, and 
	print the moves to a file called moveLst37.

3) Changing Options — in the if__name__ == ‘__main__’ block of FreeCellSolver, there’s a 
	variable changeSettings set to false. If this is set to True, it gives you the 
	option to change the cap for a search, and the algorithm used to do the searching.
	The cap is the max number of states that will be evaluated before the program 
	gives up, and there are 6 options for how to search.

4) Printing counter — In every search function, there’s a print(counter) statement. I like 	
	it because it tells me the program is thinking, but if the constant stream of 
	numbers is annoying, you could just comment it out.

5) Keyboard interrupt — if the program thinking gets annoying, the keyboard interrupt 	
	actually doesn’t kill the program — it just pauses it, tells you what time and state 
	evaluated you’re at, and asks if you want to keep going. Use keyboard interrupt if 
	the program ever gets annoying. Just remember that each time the keyboard interrupt 
	is used, there are a few states that might have been created that were just 	
	essentially discarded. Also the time still increases when its paused with that 
	keyboard interrupt.

NOTES:
None for GUI, well documented, mostly self-explanatory

Solver:
1) Please note that I had a cool picture for the win screen, but I was exceeding the byte limit for uploading so I had to get rid of it :( …

2) Representing Cards as Tuples and FreeCell Objects as States:
	In making the solver, I started representing cards, instead of objects, as just 
	tuples of two numbers, a value and an sVal (suit value). The value ranged from 1-13 
	(traditionally), and the sVal went from 0-3, with 0 being S, 1=H, 2=C, 3=D (same 
	order as in all_suits.
	States are a little more involved. They had to be immutable, to use in dictionaries
	and sets, so I envisioned states as essentially snapshots of a FreeCell object at a
	moment in time. 
	A state is a 3-tuple, consisting of:
    foundation -- a tuple of four integers, or None if there is no card in the
                  said foundation. The index of each value in the foundation
                  is the same index as the suit in all_suits
    freecell   -- a tuple of four values also, which can be None if that
                  particular freecell is empty. Otherwise, the value will be a
                  card tuple (a 2-tuple of (value, sVal) representing a card
    cascades   -- a tuple of 8 values, which can be None if a cascade is empty.
                  Otherwise, the value will itself be a tuple of card tuples,
                  so if there are 7 caards in a particular column of the
                  cascades, that column will be a tuple of 7 2-tuples
	States are immutable everywhere, but in the executeCommand function, a state is 	
	unpacked into it’s 3 components, which are all mapped to lists (and all the cascades 
	in cascades are likewise made into lists). A move is then made on these new 
	non-immutable data structures, and they are converted back to tuples, repacked, and 
	returned as a new State. Thus states can be updated with a move.

3) Different algorithms: I included 6 algorithms, which are as follows:
	1 -- Greedy Best First Search (fast, not always optimal, recommended)
        2 -- A* (slower, but optimal)
        3 -- Basic Greedy Best First Search (simpler heuristic, less effective)
        4 -- Basic A* (again a simpler heuristic, might be faster)
       	5 -- Breadth First Search (probably not gonna work)
        6 -- Depth First Search (also not gonna work)
	
	I know it’s bad practice to copy-past a lot, but I really liked having all these 
	different versions right there at my fingertips. It was also very interesting how 	
	similar the code for each algorithms was, and having each search function in its 	
	entirety was very interesting, particularly for the compare and contrast.

	With respect to the ideal algorithm again, I think 1 is hands down the best. It’s 	
	typically pretty fast, and solves about 85-90% in the first 100,000 states. That 	
	said, it’s not perfect, and I’ve had to kill it multiple times because it just 		
	couldn’t find an answer. Also, it’s not optimal at all. In this sense, the A* 
	searches are slightly better. However, they also take muuccchh longer. And DFS and 	
	BFS just don’t work. I tried iterative deepening DFS, but it didn’t seem any more 	
	effective, and I wasn’t sure I did it right, so I didn’t include it

4) Note on cycles: In finding a better heuristic function that considered more than just 
	cards in the foundations, I envisioned cycles — sequences of cards that blocked each 
	other. The simplest example of a cycle is a one-suit cycle, where two cards of the 
	same suit are in one cascade, but the lower ranked one is higher up in the cascade. 
	The game can’t be won until this situation is remedied, and thus it’s clear that the 
	more cycles there are, the more moves it would take to win the game, and from there 
	the heuristic function came.

	If it seems like some steps I take are overcomplicated, that’s because at first, I 
	tried also counting 2 suit cycles — for example, a 3 of diamonds is above a K of 
	spades in one cascade, and the A of spades is above a 6 of diamonds in another. The 
	King can’t go onto the foundations until the A does, the Ace can’t go on until the 6 
	is moved, the 6 can’t go on until the 3 does, and the 3 is blocked by the K, making 
	it a full circle (which is where the cycle idea comes from). I originally tried 
	identifying two-suit cycles as well, which is why
	there are remnants like frozen sets with only one tuple in them, and so on.

	Going back to the frozen sets, cycles are essentially represented as a collection of 
	edges — a link between two adjacent cards that, if broken, would end the cycle. 
	Thus, the set of cycles for a state is really a set of all edges, which are 4-tuples 
	that are just 2 card tuples put together. 
	
	One last comment about the cycles. I realized it would be very inefficient to 
	recalculate cycles for each new state introduced, especially since there’s little 	
	variance from the cycles set of a parent state to it’s child. Instead, I calculated 	
	the cycles once initially, and update with each move.


Ok that’s all, thank you so much for reading through this,

Yours truly,
Akshay



