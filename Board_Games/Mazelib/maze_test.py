import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
grandparent = os.path.dirname(parent)
sys.path.append(grandparent)
from time import time
from mazelib import Maze
from mazelib.generate.AldousBroder import AldousBroder
from mazelib.generate.BacktrackingGenerator import BacktrackingGenerator
from mazelib.generate.BinaryTree import BinaryTree
from mazelib.generate.CellularAutomaton import CellularAutomaton
from mazelib.generate.Division import Division
from mazelib.generate.DungeonRooms import DungeonRooms
from mazelib.generate.Ellers import Ellers
from mazelib.generate.GrowingTree import GrowingTree
from mazelib.generate.HuntAndKill import HuntAndKill
from mazelib.generate.Kruskal import Kruskal
from mazelib.generate.Prims import Prims
from mazelib.generate.Sidewinder import Sidewinder
from mazelib.generate.TrivialMaze import TrivialMaze
from mazelib.generate.Wilsons import Wilsons


from mazelib.solve import BacktrackingSolver
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.pyplot as plt

def plotXKCD(grid):
    """ Generate an XKCD-styled line-drawn image of the maze. """
    H = len(grid)
    W = len(grid[0])
    h = (H - 1) // 2
    w = (W - 1) // 2

    with plt.xkcd(0,0,0):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        vertices = []
        codes = []

        # loop over horizontals
        for r,rr in enumerate(range(1, H, 2)):
            run = []
            for c,cc in enumerate(range(1, W, 2)):
                if grid[rr-1,cc]:
                    if not run:
                        run = [(r,c)]
                    run += [(r,c+1)]
                else:
                    use_run(codes, vertices, run)
                    run = []
            use_run(codes, vertices, run)

        # grab bottom side of last row
        run = []
        for c,cc in enumerate(range(1, W, 2)):
            if grid[H-1,cc]:
                if not run:
                    run = [(H//2,c)]
                run += [(H//2,c+1)]
            else:
                use_run(codes, vertices, run)
                run = []
            use_run(codes, vertices, run)

        # loop over verticles
        for c,cc in enumerate(range(1, W, 2)):
            run = []
            for r,rr in enumerate(range(1, H, 2)):
                if grid[rr,cc-1]:
                    if not run:
                        run = [(r,c)]
                    run += [(r+1,c)]
                else:
                    use_run(codes, vertices, run)
                    run = []
            use_run(codes, vertices, run)

        # grab far right column
        run = []
        for r,rr in enumerate(range(1, H, 2)):
            if grid[rr,W-1]:
                if not run:
                    run = [(r,W//2)]
                run += [(r+1,W//2)]
            else:
                use_run(codes, vertices, run)
                run = []
            use_run(codes, vertices, run)

        vertices = np.array(vertices, float)
        path = Path(vertices, codes)

        # for a line maze
        pathpatch = PathPatch(path, facecolor='None', edgecolor='black', lw=2)
        ax.add_patch(pathpatch)

        # hide axis and labels
        ax.axis('off')
        #ax.set_title('XKCD Maze')
        ax.dataLim.update_from_data_xy([(-0.1,-0.1), (h + 0.1, w + 0.1)])
        ax.autoscale_view()

        plt.show()

def use_run(codes, vertices, run):
    """Helper method for plotXKCD. Updates path with newest run."""
    if run:
        codes += [Path.MOVETO] + [Path.LINETO] * (len(run) - 1)
        vertices += run




m = Maze()
for fn in [AldousBroder, BacktrackingGenerator, 
           GrowingTree, HuntAndKill, 
           Wilsons]:
    m.generator = fn(30, 31)
    m.solver = BacktrackingSolver   
    t= time()
    m.generate()
    m.generate_entrances()
    #m.solve()
    print(str(fn), time() -t)
    plotXKCD(m.grid)
    showPNG(m.grid)


    

