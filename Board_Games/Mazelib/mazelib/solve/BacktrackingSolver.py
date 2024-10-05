from random import choice
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
try:
    from cython import compiled
except (ModuleNotFoundError):
    from  solve.MazeSolveAlgo import MazeSolveAlgo


class BacktrackingSolver(MazeSolveAlgo):
    """
    1. Pick a random direction and follow it
    2. Backtrack if and only if you hit a dead end.
    """

    def _solve(self):
        solution = []

        # a first move has to be made
        current = self.start
        if self._on_edge(self.start):
            current = self._push_edge(self.start)
        solution.append(current)

        # pick a random neighbor and travel to it, until you're at the end
        while not self._within_one(solution[-1], self.end):
            ns = self._find_unblocked_neighbors(solution[-1])

            # do no go where you've just been
            if len(ns) > 1 and len(solution) > 2:
                if solution[-3] in ns:
                    ns.remove(solution[-3])

            nxt = choice(ns)
            solution.append(self._midpoint(solution[-1], nxt))
            solution.append(nxt)

        return [solution]
