# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

'''
This module solves FreeCell games using a variety of algorithms.
'''

import sys
import base_path
base_path.add_paths(__file__)
import freeCellSolver.GameFunctions as G
# GameFunctions also includes utilities, mostly functions that act on games
# (FreeCell objects), as opposed to states
import Classes as C
# Classes is just the Card and FreeCell classes, very basic objects
import StateFunctions as S
# StateFunctions has a lot of important functions, primarily acting on states
# which are immutable tuples that package all the information in a freecell
# game into a single snapshot
from time import time
import argparse

def greedySearch(game, cap=-1):
    '''
    A search algorithm that takes a freecell game and tries to solve it. Uses
    the Greedy Best First Search algorithm. Heuristic function based off
    number of cards in foundations and number of cycles (patterns that make
    it hard to clear the cascades)
    
    Arguments:
        game -- a freecell game object
        cap -- a maximum for the number of states to consider in trying to
               find a solution
    
    Return:
        if successful, will return a list of all moves to solve the game. If
        unsuccessful, users still have the option to see a list of all moves
        to the closest state to the solution. If users decline, returns None.
    '''
    
    
    def gameOver(parentState=None):
        '''
        Handles what to do when a game ends (either if won, cap is reached, all
        states are investigated -- an almost impossibility --, or user quits via
        KeyboardInterrupt). If game is won, will display the game after every
        subsequent move till the end. If game is lost, will ask users if they
        would like to see the closest state to solved.
        '''
        
        isWon = True
        if not parentState:
            # only called with an argument when game is won (parentState=solve)
            print('Game could not be solved :(')
            toContinue = input('See the best the program could do? (y or n): ')
            if toContinue != 'y':
                return None
            isWon = False
            parentState = S.findLowestState(statesToCheck.union\
                                              (statesChecked), S.hFunctionBasic)
            # search through set of states for one that produces lowest value
            # for a given function. Reduce is much more expensive for time.
            # Using hFunctionBasic will find state with most foundation cards
        answerLst = S.constructPath(parentState, parentAndPathDict)
        # take a state and a dictionary linking states to ancestors, produce a
        # list of all moves till parentState.
        totalTime = time() - timeA
        numOfMoves = len(answerLst)
        statesEval = counter
        S.remakeGame(firstState, answerLst)
        # plays a whole game given list of moves and initial state
        print(f'Number of moves in solution: {numOfMoves}')
        print(f'Total time: {totalTime} seconds')
        print(f'States evaluated: {counter}')
        return answerLst
    
    
    timeA = time()
    buckets = [set() for i in range(200)]
    # buckets is priority queue necessary for both Greedy BestFirstSearch
    # and A*. Since fixed number of integer values for either
    # the hFunctions (Greedy BFS) or f functions(A*), buckets is a list of sets
    # indexed by these values.
    statesToCheck = set()
    # has same states as buckets, but easier to use the in operator with
    statesChecked = set()
    # set of all visited nodes, prevents looping
    parentAndPathDict = {}
    # states --> (predecessor state, move to go from predecessor to state)
    cyclesDict = {}
    # states --> set of cycles in that state (see Note on cycles)
    hScores = {}
    # states --> score according to a heuristic function (distance to goal)
    counter = 0
    # counts number of states visited
    
    firstState = G.makeImmutableState(game)
    S.printState(firstState)
    parentAndPathDict[firstState] = None
    firstCycles = S.makeCycles(firstState)
    # makeCycles only used here. Too long to calculate cycles from a
    # given state, adds too much time complexity. Instead, take parent's cycles,
    # modify based on move to get to child to find child's cycles
    cyclesDict[firstState] = firstCycles
    hVal = S.hFunction(firstState, firstCycles)
    hScores[firstState] = hVal
    buckets[hVal].add(firstState)
    statesToCheck.add(firstState)
    
    while True:
        try:
            isStateToCheck = False
            for i in range(200):
            # in the buckets version of a priority que, first nonempty set
            # will have the best heuristic
                if buckets[i]:
                    parentState = buckets[i].pop()
                    isStateToCheck = True
                    break
            counter += 1
            print(counter)
            
            # 3/4 conditions to end a game. Last one is KeyboardInterrupt
            if not isStateToCheck: # impossible
                return gameOver()
            if S.game_is_won(parentState):
                return gameOver(parentState)
            if counter == cap:
                return gameOver()

            # To conserve memory, progressively wipe all nonessential
            # states from the data structures
            i = counter % 500000 + 70
            if i < 200 and counter > 200:
                for state in buckets[i]:
                    del cyclesDict[state]
                    del hScores[state]
                    del parentAndPathDict[state]
                    statesToCheck.remove(state)
                buckets[i].clear()
            # Exceptions is statesChecked, cuz still want to prevent looping

            statesToCheck.remove(parentState)
            statesChecked.add(parentState)
            nodesGenerated = S.findSuccessors(parentState,\
                                              cyclesDict[parentState])
            for (child, move, cycles) in nodesGenerated:
                if child in statesChecked:
                    # already seen, no looping
                    continue
                if child not in statesToCheck: # if state not yet generated
                    parentAndPathDict[child] = (parentState, move)
                    statesToCheck.add(child)
                    cyclesDict[child] = cycles
                    hVal = S.hFunction(child, cycles)
                    hScores[child] = hVal
                    buckets[hVal].add(child)
        except KeyboardInterrupt:
            # Allows user to stop the loop anytime. Stopping kills a few states
            # though, because most likely the parentState already added to
            # statesChecked, but no kids produced.(See note on KeyboardInterrupts)
            print(f'States Evaluated: {counter}')
            print(f'Time: {time()-timeA} seconds')
            toQuit = input('Would you like to quit? (y or n): ')
            if toQuit != 'y':
                continue
            return gameOver()






def AStarSearch(game, cap):
    '''
    Uses the A* algorithm, with the same heuristic function as greedySearch.
    '''
    # For more detailed docstrings, comments, see greedySearch
    
    def gameOver(parentState=None):
        ''' Handles what to do when a game ends. '''
        
        isWon = True
        if not parentState:
            print('Game could not be solved :(')
            toContinue = input('See the best the program could do? (y or n): ')
            if toContinue != 'y':
                return None
            isWon = False
            parentState = S.findLowestState(statesToCheck.union\
                                              (statesChecked), S.hFunctionBasic)
        answerLst = S.constructPath(parentState, parentAndPathDict)
        totalTime = time() - timeA
        numOfMoves = len(answerLst)
        statesEval = counter
        S.remakeGame(firstState, answerLst)
        print(f'Number of moves in solution: {numOfMoves}')
        print(f'Total time: {totalTime} seconds')
        print(f'States evaluated: {counter}')
        return answerLst
    
    
    timeA = time()
    buckets = [set() for i in range(300)]
    # Bigger range than buckets in greedySearch since A* has fScores >
    # hScores in greedy BFS
    statesToCheck = set()
    statesChecked = set()
    parentAndPathDict = {}
    cyclesDict = {}
    fScores = {}
    # states --> fScores = gScores + hScores
    # hScores are same as those calculated in greedySearch
    gScores = {}
    # states --> gScores (number of moves to reach that state)
    counter = 0
    
    firstState = G.makeImmutableState(game)
    S.printState(firstState)
    parentAndPathDict[firstState] = None
    firstCycles = S.makeCycles(firstState)
    cyclesDict[firstState] = firstCycles
    gScores[firstState] = 0 # since 0 moves to reach first state
    hVal = S.hFunction(firstState, firstCycles)
    fScores[firstState] = hVal # since fScore = gScore + hScore = 0 + hVal
    buckets[hVal].add(firstState)
    statesToCheck.add(firstState)
    
    while True:
        try:
            isStateToCheck = False
            for i in range(300):
                if buckets[i]:
                    parentState = buckets[i].pop()
                    isStateToCheck = True
                    break
            counter += 1
            print(counter)
            
            
            if not isStateToCheck: # almost impossible
                return gameOver()
            if S.game_is_won(parentState):
                return gameOver(parentState)
            if counter == cap:
                return gameOver()


            i = counter % 500000 + 160
            if i < 300 and counter > 300:
                for state in buckets[i]:
                    del cyclesDict[state]
                    del fScores[state]
                    del gScores[state]
                    del parentAndPathDict[state]
                    statesToCheck.remove(state)
                buckets[i].clear()
        

            statesToCheck.remove(parentState)
            statesChecked.add(parentState)
            nodesGenerated = S.findSuccessors(parentState,\
                                              cyclesDict[parentState])
            for (child, move, cycles) in nodesGenerated:
                if child in statesChecked:
                    continue
                if child not in statesToCheck:
                    parentAndPathDict[child] = (parentState, move)
                    statesToCheck.add(child)
                    cyclesDict[child] = cycles
                    gVal = gScores[parentState] + 1 # Since only 1 extra move
                    gScores[child] = gVal
                    hVal = S.hFunction(child, cycles)
                    fScores[child] = gVal + hVal
                    buckets[gVal + hVal].add(child)
        except KeyboardInterrupt:
            print(f'States Evaluated: {counter}')
            print(f'Time: {time()-timeA} seconds')
            toQuit = input('Would you like to quit? (y or n): ')
            if toQuit != 'y':
                continue
            return gameOver()





def greedySearchBasic(game, cap):
    '''
    Another greedySearch algorithm using a simpler heuristic function. Only
    calculates how many cards are in the foundation for a given state, ignoring
    cycles.
    '''
    # For more detailed docstrings, comments, see greedySearch
    
    def gameOver(parentState=None):
        isWon = True
        if not parentState:
            print('Game could not be solved :(')
            toContinue = input('See the best the program could do? (y or n): ')
            if toContinue != 'y':
                return None
            isWon = False
            parentState = S.findLowestState(statesToCheck.union\
                                              (statesChecked), S.hFunctionBasic)
        answerLst = S.constructPath(parentState, parentAndPathDict)
        totalTime = time() - timeA
        numOfMoves = len(answerLst)
        statesEval = counter
        S.remakeGame(firstState, answerLst)
        print(f'Number of moves in solution: {numOfMoves}')
        print(f'Total time: {totalTime} seconds')
        print(f'States evaluated: {counter}')
        return answerLst
    
    
    timeA = time()
    buckets = [set() for i in range(200)]
    statesToCheck = set()
    statesChecked = set()
    parentAndPathDict = {}
    # Notice the lack of a cycles dictionary
    hScores = {}
    counter = 0
    
    firstState = G.makeImmutableState(game)
    S.printState(firstState)
    parentAndPathDict[firstState] = None
    
    
    hVal = S.hFunctionBasic(firstState)
    # hFunctionBasic only counts # of cards in foundation for a state,
    # it is much simpler than hFunction used in other algorithms, which has
    # an additional argument of the set of cycles for a given state.
    hScores[firstState] = hVal
    buckets[hVal].add(firstState)
    statesToCheck.add(firstState)
    
    while True:
        try:
            isStateToCheck = False
            for i in range(53):
                if buckets[i]:
                    parentState = buckets[i].pop()
                    isStateToCheck = True
                    break
            counter += 1
            print(counter)
            
            
            if not isStateToCheck:
                return gameOver()
            if S.game_is_won(parentState):
                return gameOver(parentState)
            elif counter == cap:
                return gameOver()

            i = counter % 500000 + 70
            if i < 200 and counter > 200:
                for state in buckets[i]:
                    del hScores[state]
                    del parentAndPathDict[state]
                    statesToCheck.remove(state)
                buckets[i].clear()

            statesToCheck.remove(parentState)
            statesChecked.add(parentState)
            nodesGenerated = S.findSuccessorsBasic(parentState)
            # Again, findSuccessorsBasic is like findSuccessors, but
            # simpler because there is no cycle information, and therefore
            # one less argument. Also notice that it returns a list of 2-tuples,
            # as opposed to 3-tuples.
            for (child, move) in nodesGenerated:
                if child in statesChecked:
                    continue
                if child not in statesToCheck:
                    parentAndPathDict[child] = (parentState, move)
                    statesToCheck.add(child)
                    hVal = S.hFunctionBasic(child)
                    hScores[child] = hVal
                    buckets[hVal].add(child)
        except KeyboardInterrupt:
            print(f'States Evaluated: {counter}')
            print(f'Time: {time()-timeA} seconds')
            toQuit = input('Would you like to quit? (y or n): ')
            if toQuit != 'y':
                continue
            return gameOver()


def AStarSearchBasic(game, cap):
    '''
    Uses the A* algorithm, with the same heuristic function as greedySearchBasic.
    '''
    # For more detailed docstrings, comments, see greedySearch
    
    def gameOver(parentState=None):
        ''' Handles what to do when a game ends. '''
        
        isWon = True
        if not parentState:
            print('Game could not be solved :(')
            toContinue = input('See the best the program could do? (y or n): ')
            if toContinue != 'y':
                return None
            isWon = False
            parentState = S.findLowestState(statesToCheck.union\
                                              (statesChecked), S.hFunctionBasic)
        answerLst = S.constructPath(parentState, parentAndPathDict)
        totalTime = time() - timeA
        numOfMoves = len(answerLst)
        statesEval = counter
        S.remakeGame(firstState, answerLst)
        print(f'Number of moves in solution: {numOfMoves}')
        print(f'Total time: {totalTime} seconds')
        print(f'States evaluated: {counter}')
        return answerLst
    
    
    timeA = time()
    buckets = [set() for i in range(300)]
    statesToCheck = set()
    statesChecked = set()
    parentAndPathDict = {}
    fScores = {}
    # states --> fScores = gScores + hScores
    # hScores are same as those calculated in greedySearch
    gScores = {}
    # states --> gScores (number of moves to reach that state)
    counter = 0
    
    firstState = G.makeImmutableState(game)
    S.printState(firstState)
    parentAndPathDict[firstState] = None
    gScores[firstState] = 0 # since 0 moves to reach first state
    hVal = S.hFunctionBasic(firstState)
    fScores[firstState] = hVal # since fScore = gScore + hScore = 0 + hVal
    buckets[hVal].add(firstState)
    statesToCheck.add(firstState)
    
    while True:
        try:
            isStateToCheck = False
            for i in range(300):
                if buckets[i]:
                    parentState = buckets[i].pop()
                    isStateToCheck = True
                    break
            counter += 1
            print(counter)
            
            
            if not isStateToCheck: # almost impossible
                return gameOver()
            if S.game_is_won(parentState):
                return gameOver(parentState)
            if counter == cap:
                return gameOver()


            i = counter % 500000 + 160
            if i < 300 and counter > 300:
                for state in buckets[i]:
                    del fScores[state]
                    del gScores[state]
                    del parentAndPathDict[state]
                    statesToCheck.remove(state)
                buckets[i].clear()
        

            statesToCheck.remove(parentState)
            statesChecked.add(parentState)
            nodesGenerated = S.findSuccessorsBasic(parentState)
            for (child, move) in nodesGenerated:
                if child in statesChecked:
                    continue
                if child not in statesToCheck:
                    parentAndPathDict[child] = (parentState, move)
                    statesToCheck.add(child)
                    gVal = gScores[parentState] + 1 # Since only 1 extra move
                    gScores[child] = gVal
                    hVal = S.hFunctionBasic(child)
                    fScores[child] = gVal + hVal
                    buckets[gVal + hVal].add(child)
        except KeyboardInterrupt:
            print(f'States Evaluated: {counter}')
            print(f'Time: {time()-timeA} seconds')
            toQuit = input('Would you like to quit? (y or n): ')
            if toQuit != 'y':
                continue
            return gameOver()



def BorDFirstSearch(game, cap, useDFS=False):
    '''
    Runs either a breadth or depth first search to solve a game.
    '''
    # For more detailed docstrings, comments, see greedySearch
    
    def gameOver(parentState=None):
        ''' Handles what to do when a game ends. '''
        
        isWon = True
        if not parentState:
            print('Game could not be solved :(')
            toContinue = input('See the best the program could do? (y or n): ')
            if toContinue != 'y':
                return None
            isWon = False
            parentState = S.findLowestState(set(statesToCheck).union\
                                              (statesChecked), S.hFunctionBasic)
        answerLst = S.constructPath(parentState, parentAndPathDict)
        totalTime = time() - timeA
        numOfMoves = len(answerLst)
        statesEval = counter
        S.remakeGame(firstState, answerLst)
        print(f'Number of moves in solution: {numOfMoves}')
        print(f'Total time: {totalTime} seconds')
        print(f'States evaluated: {counter}')
        return answerLst
    
    
    timeA = time()
    statesToCheck = []
    # Just a list now, not a priority queue. If BFS is used, the list will be
    # used as a queue (items inserted at beginning, popped from end), while
    # DFS would be a stack (inserted at end, popped from end)
    statesChecked = set()
    parentAndPathDict = {}
    
    insertPoint = 0
    if useDFS:
        insertPoint = -1
    # If BFS, add to 0th position, so back of the queue. If DFS, add to -1
    # position, so top of the stack
    
    firstState = G.makeImmutableState(game)
    S.printState(firstState)
    parentAndPathDict[firstState] = None
    statesToCheck.append(firstState)
    counter = 0

    while statesToCheck:
        try:
            parentState = statesToCheck.pop()
            counter += 1
            print(counter)
    
            if S.game_is_won(parentState):
                return gameOver(parentState)
            if counter == cap:
                return gameOver()

            statesChecked.add(parentState)
            nodesGenerated = S.findSuccessorsBasic(parentState)
            for (child, move) in nodesGenerated:
                if child in statesChecked:
                    continue
                if child not in statesToCheck:
                    parentAndPathDict[child] = (parentState, move)
                    statesToCheck.insert(insertPoint, child)
    
        except KeyboardInterrupt:
            print(f'States Evaluated: {counter}')
            print(f'Time: {time()-timeA} seconds')
            toQuit = input('Would you like to quit? (y or n): ')
            if toQuit != 'y':
                continue
            return gameOver()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(\
                description="This is a solver for the game FreeCell, using a" +\
                            " variety of search algorithms to find a solution"+\
                            " for an entered game")
    parser.add_argument('--gameFile', '-g', default='game.txt', \
                        help='name of file to save game to')
    parser.add_argument('--moveFile', '-m', default='moves.txt', \
                        help='name of file to save movelist (game solution) to')
    parser.add_argument('--startFile', '-s', default=None, \
                        help='name of file containing game to solve')
    parser.add_argument('--cap', '-c', default=2000000, type=int, \
                        help='name of file containing game to solve')
    searchTypeStr = '''
        Integer value representing searchtype to use.
        Options are: 
            1 -- Greedy Best First Search (fast, not always optimal, recommended)
            2 -- A* (slower, but optimal)
            3 -- Basic Greedy Best First Search (simpler heuristic, less effective)
            4 -- Basic A* (again a simpler heuristic, might be faster)
            5 -- Breadth First Search (probably not gonna work)
            6 -- Depth First Search (also not gonna work)
    '''
    parser.add_argument('--searchType', '-t', default=1, type=int, help=searchTypeStr)
    args = parser.parse_args()
    
    gameFile = args.gameFile
    moveFile = args.moveFile
    searchType = args.searchType
    if searchType not in range(1, 7):
        raise ValueError("Search Type must be an integer from 1-6")
    cap = args.cap
    if cap not in range(2000001):
        raise ValueError("Cap must be <= 2000000")
    startFile = args.startFile
    game = C.FreeCell()
    if startFile:
        try:
            game = G.loadFile(startFile)
        except IOError as e:
            print(e)
            print('Bad startFile, reverting to randomly generating a game')
    G.saveGameToFile(game, gameFile)

    # Select which search to run
    searches = [greedySearch, AStarSearch, greedySearchBasic, AStarSearchBasic]
    searchType -= 1 # Get 0 indexed
    if searchType >= 4:
        useDFS = (searchType > 4)
        answerLst = BorDFirstSearch(game, cap, useDFS)
    else:
        answerLst = searches[searchType](game, cap)
    
    print(f'Game printed to file <{gameFile}>')
    if not answerLst:
        print(f'No move list printed')
        sys.exit(0)
    with open(moveFile, 'w') as file:
        for move in answerLst:
            print(move, file=file)
    print(f'Move list printed to file <{moveFile}>')
    
    sys.exit(0)


