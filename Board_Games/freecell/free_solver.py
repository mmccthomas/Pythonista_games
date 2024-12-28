# Name: Akshay Yeluri
# CMS cluster login name: ayeluri

'''
This module solves FreeCell games using a variety of algorithms.
'''
# converted to class to remove duplicated gameOver Chris Thomas Dec 2024
import sys
import base_path
base_path.add_paths(__file__)
import freeCellSolver.GameFunctions as G
# GameFunctions also includes utilities, mostly functions that act on games
# (FreeCell objects), as opposed to states
import freeCellSolver.Classes as C
# Classes is just the Card and FreeCell classes, very basic objects
import freeCellSolver.StateFunctions as S
# StateFunctions has a lot of important functions, primarily acting on states
# which are immutable tuples that package all the information in a freecell
# game into a single snapshot
from time import time
import argparse

class Solver():
  
  def gameOver(self, parentState=None):
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
              # raise exception rather that msnual input
              raise RuntimeError('Game could not be solved :(')
              toContinue = input('See the best the program could do? (y or n): ')
              if toContinue != 'y':
                  return None
              isWon = False
              parentState = S.findLowestState(statesToCheck.union\
                                                (statesChecked), S.hFunctionBasic)
              # search through set of states for one that produces lowest value
              # for a given function. Reduce is much more expensive for time.
              # Using hFunctionBasic will find state with most foundation cards
              
          # answerLst is now tuple of moves and states CMT
          answerLst = S.constructPath(parentState, self.parentAndPathDict)
          # take a state and a dictionary linking states to ancestors, produce a
          # list of all moves till parentState.
          totalTime = time() - self.timeA
          numOfMoves = len(answerLst[0])
          statesEval = self.counter
          S.remakeGame(self.firstState, answerLst[0], noprint=self.no_print)
          # plays a whole game given list of moves and initial state
          print(f'Number of moves in solution: {numOfMoves}')
          print(f'Total time: {totalTime} seconds')
          print(f'States evaluated: {self.counter}')        
          return answerLst
  
  def initialise(self):
      #initialise common class variables
      # counts number of states visited
      self.counter = 0
      self.timeA = time()
      # set of all visited nodes, prevents looping
      self.parentAndPathDict = {}
      
      # common initialising functions
      self.firstState = G.makeImmutableState(self.game)
      S.printState(self.firstState)
      self.parentAndPathDict[self.firstState] = None 
         
  def greedySearch(self):
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
      self.initialise()                        
      buckets = [set() for i in range(200)]
      # buckets is priority queue necessary for both Greedy BestFirstSearch
      # and A*. Since fixed number of integer values for either
      # the hFunctions (Greedy BFS) or f functions(A*), buckets is a list of sets
      # indexed by these values.
      statesToCheck = set()
      # has same states as buckets, but easier to use the in operator with
      statesChecked = set()
      
      # states --> (predecessor state, move to go from predecessor to state)
      cyclesDict = {}
      # states --> set of cycles in that state (see Note on cycles)
      hScores = {}
      # states --> score according to a heuristic function (distance to goal)      
      
      firstCycles = S.makeCycles(self.firstState)
      # makeCycles only used here. Too long to calculate cycles from a
      # given state, adds too much time complexity. Instead, take parent's cycles,
      # modify based on move to get to child to find child's cycles
      cyclesDict[self.firstState] = firstCycles
      hVal = S.hFunction(self.firstState, firstCycles)
      hScores[self.firstState] = hVal
      buckets[hVal].add(self.firstState)
      statesToCheck.add(self.firstState)
      
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
              self.counter += 1
              if self.counter % 1000 == 0:
                 print(self.counter)
              
              # 3/4 conditions to end a game. Last one is KeyboardInterrupt
              if not isStateToCheck: # impossible
                  return self.gameOver()
              if S.game_is_won(parentState):
                  return self.gameOver(parentState)
              if self.counter == self.cap:
                  return self.gameOver()
  
              # To conserve memory, progressively wipe all nonessential
              # states from the data structures
              i = self.counter % 500000 + 70
              if i < 200 and self.counter > 200:
                  for state in buckets[i]:
                      del cyclesDict[state]
                      del hScores[state]
                      del self.parentAndPathDict[state]
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
                      self.parentAndPathDict[child] = (parentState, move)
                      statesToCheck.add(child)
                      cyclesDict[child] = cycles
                      hVal = S.hFunction(child, cycles)
                      hScores[child] = hVal
                      buckets[hVal].add(child)
          except KeyboardInterrupt:
              # Allows user to stop the loop anytime. Stopping kills a few states
              # though, because most likely the parentState already added to
              # statesChecked, but no kids produced.(See note on KeyboardInterrupts)
              print(f'States Evaluated: {self.counter}')
              print(f'Time: {time()-self.timeA} seconds')
              toQuit = input('Would you like to quit? (y or n): ')
              if toQuit != 'y':
                  continue
              return self.gameOver()
    
  def AStarSearch(self):
      '''
      Uses the A* algorithm, with the same heuristic function as greedySearch.
      '''
      # For more detailed docstrings, comments, see greedySearch
      self.initialise()      
           
      buckets = [set() for i in range(300)]
      # Bigger range than buckets in greedySearch since A* has fScores >
      # hScores in greedy BFS
      statesToCheck = set()
      statesChecked = set()      
      cyclesDict = {}
      fScores = {}
      # states --> fScores = gScores + hScores
      # hScores are same as those calculated in greedySearch
      gScores = {}
      # states --> gScores (number of moves to reach that state)       
      
      firstCycles = S.makeCycles(self.firstState)
      cyclesDict[self.firstState] = firstCycles
      gScores[self.firstState] = 0 # since 0 moves to reach first state
      hVal = S.hFunction(self.firstState, firstCycles)
      fScores[self.firstState] = hVal # since fScore = gScore + hScore = 0 + hVal
      buckets[hVal].add(self.firstState)
      statesToCheck.add(self.firstState)
      
      while True:
          try:
              isStateToCheck = False
              for i in range(300):
                  if buckets[i]:
                      parentState = buckets[i].pop()
                      isStateToCheck = True
                      break
              self.counter += 1
              if self.counter % 1000 == 0:
                 print(self.counter)\
                            
              if not isStateToCheck: # almost impossible
                  return self.gameOver()
              if S.game_is_won(parentState):
                  return self.gameOver(parentState)
              if self.counter == self.cap:
                  return self.gameOver()
    
              i = self.counter % 500000 + 160
              if i < 300 and self.counter > 300:
                  for state in buckets[i]:
                      del cyclesDict[state]
                      del fScores[state]
                      del gScores[state]
                      del self.parentAndPathDict[state]
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
                      self.parentAndPathDict[child] = (parentState, move)
                      statesToCheck.add(child)
                      cyclesDict[child] = cycles
                      gVal = gScores[parentState] + 1 # Since only 1 extra move
                      gScores[child] = gVal
                      hVal = S.hFunction(child, cycles)
                      fScores[child] = gVal + hVal
                      buckets[gVal + hVal].add(child)
          except KeyboardInterrupt:
              print(f'States Evaluated: {self.counter}')
              print(f'Time: {time()-self.timeA} seconds')
              toQuit = input('Would you like to quit? (y or n): ')
              if toQuit != 'y':
                  continue
              return self.gameOver()  
  
  def greedySearchBasic(self):
      '''
      Another greedySearch algorith using a simpler heuristic function. Only
      calculates how many cards are in the foundation for a given state, ignoring
      cycles.
      '''
      # For more detailed docstrings, comments, see greedySearch
      self.initialise()        
      buckets = [set() for i in range(200)]
      statesToCheck = set()
      statesChecked = set()    
      # Notice the lack of a cycles dictionary
      hScores = {}     
           
      hVal = S.hFunctionBasic(self.firstState)
      # hFunctionBasic only counts # of cards in foundation for a state,
      # it is much simpler than hFunction used in other algorithms, which has
      # an additional argument of the set of cycles for a given state.
      hScores[self.firstState] = hVal
      buckets[hVal].add(self.firstState)
      statesToCheck.add(self.firstState)
      
      while True:
          try:
              isStateToCheck = False
              for i in range(53):
                  if buckets[i]:
                      parentState = buckets[i].pop()
                      isStateToCheck = True
                      break
              self.counter += 1
              if self.counter % 1000 == 0:
                 print(self.counter)
              
              
              if not isStateToCheck:
                  return self.gameOver()
              if S.game_is_won(parentState):
                  return self.gameOver(parentState)
              elif self.counter == self.cap:
                  return self.gameOver()
  
              i = self.counter % 500000 + 70
              if i < 200 and self.counter > 200:
                  for state in buckets[i]:
                      del hScores[state]
                      del self.parentAndPathDict[state]
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
                      self.parentAndPathDict[child] = (parentState, move)
                      statesToCheck.add(child)
                      hVal = S.hFunctionBasic(child)
                      hScores[child] = hVal
                      buckets[hVal].add(child)
          except KeyboardInterrupt:
              print(f'States Evaluated: {self.counter}')
              print(f'Time: {time()-self.timeA} seconds')
              toQuit = input('Would you like to quit? (y or n): ')
              if toQuit != 'y':
                  continue
              return self.gameOver()  
  
  def AStarSearchBasic(self):
      '''
      Uses the A* algorithm, with the same heuristic function as greedySearchBasic.
      '''
      # For more detailed docstrings, comments, see greedySearch
      self.initialise()    
      buckets = [set() for i in range(300)]
      statesToCheck = set()
      statesChecked = set()
      fScores = {}
      # states --> fScores = gScores + hScores
      # hScores are same as those calculated in greedySearch
      gScores = {}
      # states --> gScores (number of moves to reach that state)      
      
      gScores[self.firstState] = 0 # since 0 moves to reach first state
      hVal = S.hFunctionBasic(self.firstState)
      fScores[self.firstState] = hVal # since fScore = gScore + hScore = 0 + hVal
      buckets[hVal].add(self.firstState)
      statesToCheck.add(self.firstState)
      
      while True:
          try:
              isStateToCheck = False
              for i in range(300):
                  if buckets[i]:
                      parentState = buckets[i].pop()
                      isStateToCheck = True
                      break
              self.counter += 1
              if self.counter % 1000 == 0:
                 print(self.counter)
              
              
              if not isStateToCheck: # almost impossible
                  return self.gameOver()
              if S.game_is_won(parentState):
                  return self.gameOver(parentState)
              if self.counter == self.cap:
                  return self.gameOver()
  
  
              i = self.counter % 500000 + 160
              if i < 300 and self.counter > 300:
                  for state in buckets[i]:
                      del fScores[state]
                      del gScores[state]
                      del self.parentAndPathDict[state]
                      statesToCheck.remove(state)
                  buckets[i].clear()
          
  
              statesToCheck.remove(parentState)
              statesChecked.add(parentState)
              nodesGenerated = S.findSuccessorsBasic(parentState)
              for (child, move) in nodesGenerated:
                  if child in statesChecked:
                      continue
                  if child not in statesToCheck:
                      self.parentAndPathDict[child] = (parentState, move)
                      statesToCheck.add(child)
                      gVal = gScores[parentState] + 1 # Since only 1 extra move
                      gScores[child] = gVal
                      hVal = S.hFunctionBasic(child)
                      fScores[child] = gVal + hVal
                      buckets[gVal + hVal].add(child)
          except KeyboardInterrupt:
              print(f'States Evaluated: {self.counter}')
              print(f'Time: {time()-self.timeA} seconds')
              toQuit = input('Would you like to quit? (y or n): ')
              if toQuit != 'y':
                  continue
              return self.gameOver()
    
  def BorDFirstSearch(self, useDFS=False):
      '''
      Runs either a breadth or depth first search to solve a game.
      '''
      # For more detailed docstrings, comments, see greedySearch
      self.initialise()            
      statesToCheck = []
      # Just a list now, not a priority queue. If BFS is used, the list will be
      # used as a queue (items inserted at beginning, popped from end), while
      # DFS would be a stack (inserted at end, popped from end)
      statesChecked = set()      
      insertPoint = 0
      if useDFS:
          insertPoint = -1
      # If BFS, add to 0th position, so back of the queue. If DFS, add to -1
      # position, so top of the stack         
      
      statesToCheck.append(self.firstState)     
  
      while statesToCheck:
          try:
              parentState = statesToCheck.pop()
              self.counter += 1
              if self.counter % 1000 == 0:
                 print(self.counter)
      
              if S.game_is_won(parentState):
                  return self.gameOver(parentState)
              if self.counter == self.cap:
                  return self.gameOver()
  
              statesChecked.add(parentState)
              nodesGenerated = S.findSuccessorsBasic(parentState)
              for (child, move) in nodesGenerated:
                  if child in statesChecked:
                      continue
                  if child not in statesToCheck:
                      self.parentAndPathDict[child] = (parentState, move)
                      statesToCheck.insert(insertPoint, child)
      
          except KeyboardInterrupt:
              print(f'States Evaluated: {self.counter}')
              print(f'Time: {time()-self.timeA} seconds')
              toQuit = input('Would you like to quit? (y or n): ')
              if toQuit != 'y':
                  continue
              return self.gameOver()
  
  def solve(self, args):
      # external entry point, calls selected solver  
      # args istype SimpleNameSpace  
      gameFile = args.gameFile
      moveFile = args.moveFile
      searchType = args.searchType
      self.no_print = args.noprint
      if searchType not in range(1, 7):
          raise ValueError("Search Type must be an integer from 1-6")
      self.cap = args.cap
      if self.cap not in range(2000001):
          raise ValueError("Cap must be <= 2000000")
      startFile = args.startFile
      self.game = C.FreeCell()
      if startFile:
          try:            
              self.game = G.load(self.game, startFile)
          except AssertionError:
              try:
                  self.game = G.loadFile(startFile)
              except IOError as e:
                  print(e)
                  print('Bad startFile, reverting to randomly generating a game')
      G.saveGameToFile(self.game, gameFile)
  
      # Select which search to run
      searches = [self.greedySearch, self.AStarSearch, self.greedySearchBasic, self.AStarSearchBasic]
      searchType -= 1 # Get 0 indexed

      if searchType >= 4:
          useDFS = (searchType > 4)
          answerLst = self.BorDFirstSearch(useDFS)
      else:
          answerLst = searches[searchType]()
      
      print(f'Game printed to file <{gameFile}>')
      if not answerLst:
          print(f'No move list printed')
          return
      # output changed  to pickled answerList 
      # contains moves and states
      import pickle
      with open('statefile.pkl', 'wb') as f:
          pickle.dump(answerLst, f)
      #with open(moveFile, 'w') as file:
      #    for move in answerLst[0]:
      #        print(move, file=file)
      #print(f'Move list printed to file <{moveFile}>')

if __name__ == '__main__':
    from types import SimpleNamespace
    args = SimpleNamespace(**{'gameFile': 'None', 
                                   'moveFile': 'moves.txt', 
                                   'searchType': 3, 
                                   'startFile': 'game.txt',
                                   'cap': 1000000,
                                   'noprint': False})
    """                             
    parser = argparse.ArgumentParser(\
                description="This is a solver for the game FreeCell, using a" +\
                            " variety of search algorithms to find a solution"+\
                            " for an entered game")
    parser.add_argument('--gameFile', '-g', default='game1.txt', \
                        help='name of file to save game to')
    parser.add_argument('--moveFile', '-m', default='moves.txt', \
                        help='name of file to save movelist (game solution) to')
    parser.add_argument('--startFile', '-s', default='game.txt', \
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
    """
    s = Solver()
    s.solve(args)    
    #sys.exit(0)
