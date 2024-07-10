# place pieces starting at top left
# if placing a piece would leave a single space, first try all the rotations of that tile.
# otherwise move on to next tile
import numpy as np
import random
SIZE = 9


class Cages:
    
    def __init__(self, level=None):
        # types ## ### ### ## ##.  #
        #            #.  ##. ## ###
        if level is None:
          self.piece_types = (
              [[1, 1]], [[2, 2, 2]],
              [[3, 0], [3, 3]], [[4, 0, 0], [4, 4, 4]],
              [[5, 5], [5, 5]], [[6, 6, 0], [0, 6, 6]],
              [[0, 7, 0], [7, 7, 7]])
        elif level == 'Easy':
           self.piece_types = (
              [[1, 1]], [[2, 2, 2]],
              [[3, 0], [3, 3]], [[4, 0, 0], [4, 4, 4]],
              [[5, 5], [5, 5]])
              
        self.color_map = ("⬛", "🟦", "🟥", "🟧", "🟩", "🟪",  "🟫", "⬜")
        self.cage_colors = ["blue", "red", "yellow", "green", "purple", "cyan"]
        self.board = np.zeros((SIZE, SIZE), dtype=int)
        
        self.piece_positions = self.gen_piece_positions(self.piece_types)
        self.delta = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]])
        self.solutions = []
        self.terminate = False
    
    def draw_board(self, board):
        def cm(n):
          return np.array([self.color_map[i] for i in n])
        print(np.apply_along_axis(cm, 0, board))
        
    def get_board_rc(self, rc, board):
        try:
          return board[rc[0]][rc[1]]
        except (IndexError):
          return None
          
    def board_rc(self, rc, board, value):
        """ set character on board """
        try:
          board[rc[0]][rc[1]] = value
        except (IndexError):
          return None
           
    def get_rotations(self, piece):
      
        pieces = [np.rot90(piece, n) for n in range(1, 4)]
        unique_rotations = [pieces[0]]
        for i in pieces[1:]:
            if not any([np.array_equal(j, i) for j in unique_rotations]):
               unique_rotations.append(i)
        return unique_rotations, len(unique_rotations)

    def get_all_positions(self, piece):
        positions, _ = self.get_rotations(piece)
        for pos in positions:
            y_reflect = np.flipud(pos)
            x_reflect = np.fliplr(pos)
            if not any([np.array_equal(p, y_reflect) for p in positions]):
               positions.append(y_reflect)
            if not any([np.array_equal(p, x_reflect) for p in positions]):
               positions.append(x_reflect)
        return positions

    def gen_piece_positions(self, pieces):
        piece_positions = []
        for piece in pieces:
            piece_positions.append(self.get_all_positions(piece))
        return piece_positions
           
    def check_zeroes(self, board):
      """ checks for isolated zero which cannot be filled
      this routine needs to be super quick
      """
      zero_locs = np.argwhere(board == 0)
         
      for loc in zero_locs:
         # get coordinate pairs
         # look in vert and horizontal dirns
         coords = np.transpose(self.delta + loc)
         out_of_bounds = np.argwhere((coords < 0) | (coords > 8))
         if out_of_bounds.shape[0] != 0:
           coords = np.delete(coords, out_of_bounds[:, 1], axis=1)
         # if surrounded by non zero, flag a result
         if np.all(board[coords[0], coords[1]]):
           return False
      return True

    def add_piece(self, board, piece, start_row, start_col):
        """ add a piece to the board, checking if it is legal """
        piece_height, piece_width = piece.shape
        legal_move = True
        
        if ((start_row + piece_height > board.shape[0]) or
            (start_col + piece_width > board.shape[1])):
            return board, False, None

        changed_squares = []
        
        for i, row in enumerate(piece):
            for j, val in enumerate(row):
                # only add filled spaces, never take away
                if val:
                    # don't overwrite existing pieces on the board
                    try:
                       if self.get_board_rc((start_row + i, start_col + j), board):
                          return board, False, None
                       else:
                           changed_squares.append((start_row + i, start_col + j, val))
                    except (IndexError):
                        return board, False, None

        new_board = np.copy(board)
        [self.board_rc((r, c), new_board, val) for r, c, val in changed_squares]

        # check if the move created any illegal squares
        if not self.check_zeroes(new_board):
            return board, False, None

        return new_board, legal_move, changed_squares

    def solve_board(self, board, pieces, display):
        """ place cages on empty board """
        cages = []
        iterations = 0
        if self.terminate:
            return
            
        while True:
          iterations += 1
          if display:
              print('iterations', iterations)
              self.draw_board(board)
          if iterations % 100 == 0:
            # start again
            print('Restarting search')
            iterations = 0
            cages = []
            board = np.zeros((SIZE, SIZE), dtype=int)
            if display:
               print('iterations', iterations)
          # win condition is whole board is covered in pieces
          if np.all(board):
              self.solutions.append(board)
              print(f"Solutions: {len(self.solutions):,}")
              print(f"Iterations: {iterations:,}\n")
              if display:
                  self.draw_board(board)
                  print(cages)
              return board, cages  # comment this to continuously search
              print('Restarting search')
              iterations = 0
              cages = []
              board = np.zeros((SIZE, SIZE), dtype=int)
          else:
            for r, row in enumerate(self.board):
              for c, pos in enumerate(row):
                if self.board[r][c] != 0:  # not empty
                  continue  # next c
                if iterations < 2:
                   piece_positions = pieces[random.randint(0, len(pieces)-1)]
                else:
                   # only 2 or 3 squares to fill in spaces - faster
                   piece_positions = pieces[random.randint(0, 2)]
                for position in piece_positions:
                  new_board, legal_move, squares = self.add_piece(board, position, r, c)
                  if legal_move:
                    board = new_board
                    cages.append(squares)
                    break  # next board position
                    
    def adj_matrix(self, cage_board):
      """ Construct adjacent matrix to allow colour algorithm
         adjacent matrix has size for all nodes (individual cages) on board
         a one in row, column shows adjacency
      """
      max_val = np.max(cage_board)
      self.adj_matrix = np.zeros((max_val+1, max_val+1), dtype=int)
      delta = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]])
      neighbours = []
      for r in range(cage_board.shape[0]):
        for c in range(cage_board.shape[1]):
          loc = np.array([r, c])
          origin = self.get_board_rc(loc, cage_board)
          # get coordinate pairs
          coords = delta + loc
          coords = np.clip(coords, 0, 8)
          # can use clipping to defeat out of bounds
          for coord in coords:
            neighbour = self.get_board_rc(coord, cage_board)
            if origin != neighbour:
                self.adj_matrix[origin][neighbour] = 1
                self.adj_matrix[neighbour][origin] = 1
                neighbours.append([origin, neighbour])
      return self.adj_matrix
   
    def color_4colors(self, G=None, colors=None):
      """ computes adjacent colours in grid using 4 colours only """
      
      if G:
        # Adjacent Matrix
        G= [[0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
           [0,0,0,1,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
           [0,0,1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
           [0,0,0,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,1],
           [1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [1,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,1,1,0,0,0,1,0,0,1,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,1,0,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,0,1,1,0,0,0,0,1,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,1,0,0],
           [0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,1,0,1,0,0,1,0,0,1,1,0,0,0,1,0,0,0,1,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0],
           [0,0,0,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,1,1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1,0,0,1,1,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,1,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
           [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0],
           [0,0,0,0,1,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
           [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0]]

      else:
         G = self.adj_matrix
         
      if colors is None:
        colors = self.cage_colors
        
      # print('len G', len(G))
      # initialise the name of node.
      node = np.arange(len(G), dtype=int)
      t_ = {i: i for i in range(len(G))}
      
      # count degree of all node.
      degree = np.array([sum(G[i]) for i in range(len(G))])
      
      # initialise the posible color
      colorDict = {i: colors.copy() for i in range(len(G))}
      # sort the node depends on the degree
      sortedNode = np.flip(node[degree.argsort()])
      
      # The main process
      theSolution = {}
      for n in sortedNode:
        setTheColor = colorDict[n]
        theSolution[n] = setTheColor[0]
        adjacentNode = G[t_[n]]
        for adj, nd in zip(adjacentNode, node):
          if adj == 1 and (setTheColor[0] in colorDict[nd]):
            # dont remove last one
            if len(colorDict[nd]) > 1:
                colorDict[nd].remove(setTheColor[0])
            else:
                colorDict[nd] = random.choice(['lunar green', 'desert brown', 'cashmere', 'linen'])
                print(f'needed extra color {colorDict[nd]} for n={n}, nd={nd}')
      return theSolution
      # Print the solution
      for t, w in sorted(theSolution.items()):
        print("Node", t, " = ", w)
          
    def cage_board_view(self):
        # create cage view of board
        self.cage_board = np.zeros((SIZE, SIZE), dtype=int)
        for index, item in enumerate(self.cages):
          number_val, coords = item
          for coord in coords:
            self.board_rc(coord, self.cage_board, index)
        return self.cage_board
        
    def check_cage(self, board, display=False):
      # get cage solution and see if it fits
        _, cages = self.run(display=display)
        if cages:
          self.cages = []
          for cage in cages:
            coords = [(r, c) for r, c, _ in cage]
            numbers = [board[r][c] for r, c, _ in cage]
            if len(numbers) == len(set(numbers)):
              # no duplicates
              self.cages.append((sum(numbers), coords))
            else:
              # need another cages set
              return False
        return True
    
    def __best_choice(self, neighbours, edges, prev_one, dirn='left'):
      """ get best choice of move to create dotted lines
          we want to move left if possible otherwise straight on
      """
      options = neighbours[prev_one]  # indexes
      # seeking to turn left
      turn_left_dict = {'left': ('down', [1, 0]), 'right': ('up', [-1, 0]),
                        'up': ('left', [0, -1]), 'down': ('right', [0, 1])}
      straight_dict = {'left': ('left', [0, -1]), 'right': ('right', [0, 1]), 
                       'up': ('up', [-1, 0]), 'down': ('down', [1, 0])}
      straight_inv_dict = {tuple(v[1]): k for k, v in straight_dict.items()}
      coords = edges[options]
      # print(f'options for {prev_one} {edges[prev_one]} are {options} {coords}')
      vector = np.sign(coords - edges[prev_one]).astype(dtype=int)
      vector = vector.tolist()
      if len(options) == 1:
        # return direction for turn
        return neighbours[prev_one].pop(), straight_inv_dict[tuple(vector[0])]
        
      elif options is None:
        raise IndexError
        return None, None
      else:
        # which way?  try to turn left, else straight on
        for seek_dict in (turn_left_dict, straight_dict):
          seek = seek_dict[dirn][1]
          if seek in vector:
              s = vector.index(seek)
              # print(f'choosing {options[s]}')
              return neighbours[prev_one].pop(s), seek_dict[dirn][0]
        # get last item
        return neighbours[prev_one].pop(), dirn
      
    def dotted_lines(self, coords, delta=0.435):
      """draw dotted lines inside each cage"""
      delta = 0.25 if delta < 0.25 else delta
      delta = 0.5 if delta > 0.50 else delta
      tol = 0.01
      offset = 0.5  # fixed to allow for anchor point of coords
      
      nodes = np.array(coords)
      nodes = np.subtract(nodes, [1, 0])
      # produce coordinates around path of nodes
      dxdy = np.array([[-1, -1], [-1, 1], [1, 1], [1, -1]])
      # produce points around each coordinate
      expanded = np.array([dxdy * delta +  nodes[i] for i in range(nodes.shape[0])])
      expanded = np.concatenate(expanded, axis=0)
      edges = np.unique(expanded, axis=0)
      
      # deal with special case  2x2 square
      # remove internal edges otherwise we get a torus
      if nodes.size == 8 and all(np.ptp(nodes, axis=0) == (1, 1)):
           xmin, ymin = min(edges[:, 1]) + tol, min(edges[:, 0]) + tol
           xmax, ymax = max(edges[:, 1]) - tol, max(edges[:, 0]) - tol
           remove = [index for index, edge in enumerate(edges)  if  xmin < edge[1] < xmax and ymin < edge[0] < ymax]
           edges = np.delete(edges, remove, axis=0)
           
      def flatten(xss):
         return [x for xs in xss for x in xs]
         
      # find index of neighbours at each point
      neighbours = {}
      for i, edge in enumerate(edges):
        a = np.abs(edges - edge)
        s = np.sum(a, axis=1)
        nearest = np.argwhere(np.logical_and(s <= (2 * delta + tol), s > tol)) # exclude origin
        if nearest.size == 0:
            nearest = np.argwhere(s <= delta + tol)
            
        nearest = sorted(flatten(nearest.tolist()))[::-1]  # lowest item last
        neighbours[i] = nearest
        
      # start with the first node
      # these are all node numbers that reference edges indices
      seq = [0]
      dirn = 'right'
      for _ in neighbours:
          prev_one = seq[-1]
          try:
            next_one, dirn = self.__best_choice(neighbours, edges, prev_one, dirn)
          except (TypeError, IndexError):
            break
          # delete back-reference to previous neighbor in all locations
          for k in neighbours:
            try:
               neighbours[k].remove(prev_one)
            except (ValueError):
              continue
          seq.append(next_one)
      seq.append(0)
      
      path_coords = edges[seq, :]            
      points = np.add(path_coords, [offset, offset])            
      return points
      
                                   
    def run(self, display=True):
        return self.solve_board(self.board, self.piece_positions, display=display)


if __name__ == "__main__":
    # a=np.random.randint(0,4,(SIZE,SIZE))
    b = Cages('Easy')
    b.check_cage(b.board, display=True)
    b.cage_board = b.cage_board_view()
    print(b.cage_board)
    b.color_4colors(True)
    # b.check_zeroes(a)
