#
# CS 1 Final exam, 2017
# Freecell game.
#

import sys

from CardB import * # Has a few global variables, and tkinter/messagebox/
# filedialogue import statements. All global variables are in either CardB or
# in the if __name__ == '__main__' block.
import FreeCellB as F
import FreeCellFullB as FF
import FreeCellUtilsB as U


def setState(stateOfBoard):
    '''
    Given a tuple representing the state of the game, as made by make.State()
    from FreeCellFullB.py, will set the state of the board to be that state.
    '''
    foundation, foundCards, freecell, cascades = stateOfBoard
    (currFoundation, currFoundCards, currFreecell, currCascades) = \
                                            game.makeState()
    game.foundation = foundation.copy()
    game.freecell = freecell[:]
    game.cascade = [cascade[:] for cascade in cascades[:]]
    cardsToRelocate = []
    #print()
    #for i in range(8):
        #print([str(card) for card in cascade[i]])
    game.foundationCards = foundCards[:]
    for slot, card in enumerate(freecell):
        if card:
            if card not in currFreecell:
                card.loc = f'x{slot}'
                # If card was in old freecells, but not anymore, need to
                # relocate the card (change its location and glide). Same true
                # for cards in the cascades
                cardsToRelocate.append(card)
    for i, cascade in enumerate(cascades):
        for j, card in enumerate(cascade):
            if card:
                if card not in currCascades[i]:
                    card.loc = (f'c{i}', j)
                    cardsToRelocate.append(card)
    for card in cardsToRelocate:
        card.glide(card.loc)

def undo():
    '''
    Callback function that will use the history field of a game to return
    it to a previous state.
    '''
    
    if not game.history:
        messagebox.showwarning('Failed undo', 'Cannot undo further!')
    else:
        stateOfBoard = game.history.pop()
        setState(stateOfBoard)

def hint():
    '''
    Callback function that will generate all possible moves at a given point
    in a freecell game, and will offer users the option to execute a move from
    these options, one move at a time. Moves are suggested in the following
    order: moves to foundations first, moves to cascades next, moves to
    freecells last.
    '''
    moveLst = U.findValidMoves(game)
    moveLst = [move.strip().split() for move in moveLst]
    priorityList = ['xf', 'cf', 'xc', 'cc', 'cx']
    moveLst = sorted(moveLst, key=lambda x: priorityList.index(x[0]))
    for i, move in enumerate(moveLst):
        move = ' '.join(move)
        makeMove = messagebox.askyesno('Move suggestion', \
                               f'Would you like to make move: {move}?')
        if makeMove or i == len(moveLst) - 1:
            break
        suggestNewMove = messagebox.askyesno('Suggest again', \
                               f'Want another hint?')
        if not suggestNewMove:
            break
    if makeMove:
        cmd = move.strip().split()
        executeCommand(cmd)


def quit():
    ''' By changing a global variable, this function will instruct the program
    that the gameIsOver, allowing the game to finish and reach an exit page.
    '''
    
    global gameIsOver
    gameIsOver = True

def help():
    '''
    Will print out a string detailing game instructions.
    '''
    usagestr = '''
Welcome to FreeCell by Akshay!
Press the quit button to leave :(, undo
to undo (shocking, I know), hint to see a
move suggested, or help to see...well,
this. To actually play, drag and drop cards
into place, or type a move at the prompt,
and hit the enter button. To save, load, or
execute a game, you can also enter a command at the prompt
    
Legal commands that you can enter at the prompt:

cf n -- move bottom card of cascade n to foundation
xf n -- move freecell card n to foundation
cx m n -- move bottom card of cascade m to freecell n
xc m n -- move freecell card m to cascade n
xx m n -- move freecell card m to freecell n
cc m n -- move bottom card of cascade m to cascade n
cc m n p -- move p bottom cards of cascade m to cascade n

save -- enter or select a file (must be .txt) to save the game to
save <filename> -- saves game as <filename> (will add .txt extension)
load -- enter a file (.txt) to load and play
load <filename> -- loads the file <filename>
execute -- enter a file (.txt) that should have one of the above moves on each
line, to execute those moves in order
execute <filename> -- will execute (make all the moves) the file <filename>
    '''
    messagebox.showinfo("Akshay's Freecell instructions", usagestr)


def executeCommand(cmd):
    '''
    Given a list as a command, will use that list to make a move if possible
    (try and execute the command)
    '''
    prev = game.makeState()
    # save the previous game state before making a move. If a move occurs,
    # append this previous state to game.hisotry
    if cmd == []:
        raise F.NoMove("No Move Entered")
    elif cmd[0] == 'cf' and len(cmd) == 2:
        n = int(cmd[1])
        check_cascade(n)
        game.move_cascade_to_foundation(n)
    elif cmd[0] == 'xf' and len(cmd) == 2:
        n = int(cmd[1])
        check_freecell(n)
        game.move_freecell_to_foundation(n)
    elif cmd[0] == 'cx' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        check_cascade(m)
        check_freecell(n)
        game.move_cascade_to_freecell(m, n)
    elif cmd[0] == 'cx' and len(cmd) == 2:
        m = int(cmd[1])
        check_cascade(m)
        n = -1
        for i, slot in enumerate(game.freecell):
            if not slot:
                n = i
                break
        if n == -1:
            raise F.IllegalMove('No empty Freecells')
        game.move_cascade_to_freecell(m, n)
    elif cmd[0] == 'xx' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        check_freecell(m)
        check_freecell(n)
        game.move_freecell_to_freecell(m, n)
    elif cmd[0] == 'xc' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        check_freecell(m)
        check_cascade(n)
        game.move_freecell_to_cascade(m, n)
    elif cmd[0] == 'cc' and len(cmd) == 3:
        m = int(cmd[1])
        n = int(cmd[2])
        check_cascade(m)
        check_cascade(n)
        game.move_cascade_to_cascade(m, n)
    elif cmd[0] == 'cc' and len(cmd) == 4:
        m = int(cmd[1])
        n = int(cmd[2])
        p = int(cmd[3])
        check_cascade(m)
        check_cascade(n)
        game.multi_move_cascade_to_cascade(m, n, p)
    else:
        raise ValueError(' '.join(cmd))
    game.updateAfterMove(prev)
    # if no errors happen, a move occurred, so save old state of board

def check_cascade(n):
    '''Checks if the cascade number entered as part of a command is valid.'''
    if n < 0 or n >= 8:
        raise F.IllegalMove('Invalid cascade')

def check_freecell(n):
    '''Checks if the freecell number entered as part of a command is valid.'''
    if n < 0 or n >= 4:
        raise F.IllegalMove('Invalid freecell')

def enter():
    '''
    Callback function for when something is entered into the prompt
    '''
    move = cv_entry.get() # From the global variable cv_entry
    cmd = move.strip().split()
    
    try:
    
        # If user trying to save the game as something
        if cmd[0] == 'save':
            if len(cmd) == 1:
                # Choose a file to save to with a filedialog box
                filename = filedialog.asksaveasfilename(title = \
                            "Save as", filetypes = [("text files","*.txt")], \
                            defaultextension='*.txt')
            elif len(cmd) == 2:
                # Will attempt to save the file to the second word in command
                filename = cmd[1]
                if '.' not in filename:
                    # If the file extension is not '.txt', make it '.txt'.
                    filename += '.txt'
            else:
                raise ValueError(' '.join(cmd))
            with open(filename, 'w') as file:
                str = U.save(game) # From FreeCellUtilsB
                print(str, file=file)
            return
            
        # If user trying to load or execute a game
        elif cmd[0] == 'load' or cmd[0] == 'execute':
            if len(cmd) == 1:
                # Choose a file to load with a filedialog box
                filename = filedialog.askopenfilename(title = "Select file")
                # No filetypes so people can load files without extensions,
                # helps integrate it with the solver
                if '.' in filename and '.txt' not in filename:
                    raise IOError(f'{filename} not a valid text file')
                file = open(filename, 'r')
            elif len(cmd) == 2:
                filename = cmd[1]
                try:
                    file = open(filename, 'r')
                    # try to open a file of exactly the entered name
                except IOError:
                    if '.txt' in filename:
                        # try to open a file of the same name without extension
                        file = open(filename[:-4],'r')
                    elif '.' not in filename:
                        # try to open a file of the same name with extension,
                        # b/c didn't have one before
                        file = open(filename+'.txt','r')
                    else:
                        # If neither option works, go back to original error.
                        file = open(filename, 'r')
            else:
                raise ValueError(' '.join(cmd))
            if cmd[0] == 'load':
                str = ''.join(file.readlines())
                U.load(game, str, game.canvas)
                # game.automove_to_foundation()
                # solver does not automove, don't want to mess up the syncing
            else:
                for line in file:
                    if line.strip()[0] == '#':
                        continue
                    # execute a game (make every move in a list of moves, seq
                    # uentially
                    command = line.strip().split()
                    executeCommand(command)
            file.close()
            return
        
        # Code for testing, helps understand what cards are where
        elif cmd[0] == 'cascade':
            n = int(cmd[1])
            for card in game.cascade[n]:
                print(card)

        elif cmd[0] == 'freecell':
            n = int(cmd[1])
            print(freecell[n])

        elif cmd[0] == 'card':
            cardId = cmd[1]
            suit = cardId[-1]
            rank = cardId[:-1]
            if rank in '23456789' or rank == '10':
                rank = int(rank)
            suit = suit.upper()
            card = U.findCard(game, rank, suit)
            print(card.loc)
            print(card.pos)
        # Code for testing done

        else:
            # If not loading, saving, or executing, try to use command to
            # make a move
            executeCommand(cmd)
            
    except F.IllegalMove as e:
        messagebox.showwarning('Illegal Move', e)
    except ValueError as e:
        messagebox.showwarning('Bad Command',f"Command '{e}' invalid."\
                                           ' Please enter new command!')
    except IOError as e:
        messagebox.showwarning('Bad Filename entered',f'{e}. Please try again!')


def playGame():
    '''
    Will play exactly one game of freecell completely.
    '''
    global gameIsOver
    game.automove_to_foundation()
    # Displays placeholder text for where the moves made counter will go
    textHandle = game.canvas.create_text(1000, 700, text='', \
                                  font=('Helvetica', 40), fill='#D4AF37')
    while True:
        if game.game_is_won():
            return True
        if gameIsOver:
            return False
        # If the game_is_won method returns True, game ended with a win, so
        # return True. If global variable gameIsOver is True, most likely
        # quit button was pressed, so leave the loop still, but game is not won
        # so return False.
    
        def updateText(textHandle):
            ''' Updates the number of moves made, displayed in game. '''
            game.canvas.delete(textHandle)
            toDisplay = ''
            if game.history:
                toDisplay = f'Moves Made: {len(game.history)}'
            return game.canvas.create_text(1000, 700, text=toDisplay, \
                                  font=('Helvetica', 40), fill='#D4AF37')
        textHandle = updateText(textHandle)
        
        root.update()
        # If there are moving cards, don't worry about glitches
        if game.cardsToDrag:
            continue
        # try to fix glitches
        fixGlitches()


def fixGlitches():
    '''
    Makes sure all cards in the game are in the right positions based on their
    locations. Fixes glitches resulting from spamming undo or multi_move. Uses
    the fixPos method for cards defined in CardB.py
    '''
    for card in game.foundationCards:
        card.fixPos()
    for index, card in enumerate(game.freecell):
        if card:
            card.fixPos()
    for i, cascade in enumerate(game.cascade):
        if cascade:
            for j, card in enumerate(cascade):
                card.fixPos()
                card.canvas.lift(card.handle)



if __name__ == '__main__':
    # Make a root/canvas
    root = Tk()
    root.geometry('1200x800')
    canvas = Canvas(root, width=1200, height=800)
    canvas.pack()
    
    # Option Panel
    frame = LabelFrame(root, relief=RIDGE, bd=7, padx=5, pady=10)
    cv_entry = StringVar() # Global Variable
    frameTitle = Label(frame, text='Option Panel', font='Verdana')
    frameTitle.grid(row=1, columnspan=4)
    undoButton = Button(frame, text='Undo', command=undo)
    undoButton.grid(row=2, column=0)
    quitButton = Button(frame, text='Quit', command=quit)
    quitButton.grid(row=2, column=1)
    hintButton = Button(frame, text='Hint', command=hint)
    hintButton.grid(row=2, column=2)
    helpButton = Button(frame, text='Help', command=help)
    helpButton.grid(row=2, column=3)
    entryLabel = Label(frame, text='Drag Cards or Enter Move: ')
    entryLabel.grid(row=3, columnspan=4)
    entryLine = Entry(frame, textvariable=cv_entry)
    entryLine.grid(row=4, columnspan=4)
    enterButton = Button(frame, text='Enter', command=enter)
    enterButton.grid(row=5, columnspan=4)
    frameHandle = canvas.create_window(200, 700, \
                                                  window=frame)
    
    # Make a freecell full game,
    game = FF.FreeCellFull(canvas) # Global variable
    
    # Code for testing, immediately loads a different game
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        file = open(filename, 'r')
        str = ''.join(file.readlines())
        U.load(game, str, game.canvas)
    # Code for testing done
    
    gameIsOver = False # Global Variable
    gameIsWon = playGame()
    canvas.lift(game.bgrndHandle)
    canvas.delete(frameHandle)
    def exit(event):
        sys.exit(0)
    root.bind('<Button-1>', exit)
    if gameIsWon:
        wText = canvas.create_text(600,450, font=('Helvetica', 100),\
                           fill='#800000', text='You Win!!!')
        while True:
            canvas.after(300, canvas.itemconfig(wText, fill='#00ffff'))
            canvas.update()
            canvas.after(700, canvas.itemconfig(wText, fill='#800000'))
            canvas.update()
    else:
        canvas.create_text(600,450,font=('Helvetica', 100),\
                           fill='#D4AF37', text='Goodbye :(')
        root.mainloop()



    # Whether on winscreen or goodbyes screen, keep up the image till the user
    # clicks somewhere.


# To Do
# hint button?
# Zip File creation/Documentation













