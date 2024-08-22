# module to fill crossword template
# this involves finding words from a selected dictionary to
# fill a selected template.
# entry point is populate_words_graph

from time import sleep, time
import traceback
import random
import re
import traceback
from  collections import Counter
import matplotlib.colors as mcolors
from collections import defaultdict
BLOCK = '#'
SPACE = ' '

def lprint(seq, n):
  if len(seq) > 2 * n:
      return f'{seq[:n]}...........{seq[-n:]}'
  else:
      return(seq)
      
class CrossWord():
  
  def __init__(self, gui, word_locations, all_words):
    self.max_depth = 1
    self.debug = False
    self.word_counter = None
    self.gui = gui
    self.word_locations = word_locations
    self.all_words = all_words
    self.board = []
    self.empty_board = []
    self.all_word_dict = {}
    
  def set_props(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)
       
  def copy_board(self, board):
    return list(map(list, board)) 
     
  def  board_rc(self, rc, board, value):
    """ set character on board """
    try:
      board[rc[0]][rc[1]] = value
    except(IndexError):
      return None 
  
  def  get_board_rc(self, rc, board):
    try:
      return board[rc[0]][rc[1]]
    except(IndexError):
      return None
      
  def delta_t(self, msg=None, do_print=True):
    try:
        t =  time() - self.start_time 
        if do_print:
          print(f'{msg} {t:.3f}') 
        return f'{msg} {t:.3f}'
    except(AttributeError):
      print('self.start_time not defined')
      print(traceback.format_exc())
            
  def get_next_cross_word(self, iteration, max_possibles=None,length_first=True):
      """ computes the next word to be attempted """
      
      def log_return(word):
          """ count the occurence of a word
          allows detection of unplaceable word
          """
          self.word_counter[word] += 1
          if self.word_counter[word] > 50:
            #word.fixed = True # dont try it again?
            if self.debug:
              print(f'Word {word} tried more than 50 times')
            #return word
            raise ValueError(f'Word {word} tried more than 50 times')
          else:
            return word
          
      if iteration == 0:  
        def longest():
          #def req(n): return n.length
          return sorted(self.word_locations, key= lambda x: x.length, reverse=False)   
        self.word_counter = Counter()
        if len(self.all_words) > 1000:
          max_possibles = max_possibles
        else:
          max_possibles = None 
        known = self.known() # populates word objects with match_pattern
        self.hints = list(set([word for word in self.word_locations for k in known if word.intersects(k)]))
        try:
          #self.gui.set_moves('hints')
          return  log_return(self.hints.pop())     
        except(ValueError, IndexError):
          pass        
        try: 
          #self.gui.set_moves('longest')
          return  log_return(longest()[-1])
        except (ValueError, IndexError):
          pass
        try:
          #self.gui.set_moves('fixed')
          return  log_return([word for word in self.word_locations if word.fixed][0]) 
        except (ValueError):
          print('returned here')
          return None
               
        #wordlist = longest()      
        
      else:
          fixed =  [word for word in self.word_locations if word.fixed]
          if self.debug:
              self.gui.set_message(f' placed {len(fixed)} {iteration} iterations')
          
          fixed_weights = [5 for word in fixed]
          # create weight for all unplaced words based on word length
          #def req(n): return n.length
          unplaced = sorted([word for word in self.word_locations if not word.fixed], key=lambda x: x.length, reverse=True)
          unplaced_weights = [word.length for word in unplaced]
          
          unplaced_long_words = sorted( [word for word in unplaced if word.length > 6], key=lambda x: x.length)
           
          def match_size(n):
              return sum([i.isalnum() for i in n if '.' in n])
          # all match patterns except for full words
          patterned =  [word for word in self.word_locations if word.match_pattern and '.' in word.match_pattern]
          patterned_weights = [4 * match_size(match.match_pattern) for match in patterned]
          # so pick a random choice of words with patterns, followed by all unplaced words, with
          # reference for longest word
          try:
            # self.gui.set_moves('hints')
            return log_return( self.hints.pop())
          except(ValueError, IndexError):
            pass
          if length_first:
            try:
                # self.gui.set_moves('unplaced long')
                return log_return(unplaced_long_words.pop())
                #print(' unplaced long words', unplaced_long_words)
            except(ValueError, IndexError):  # no more long words
              pass
            try:
                # self.gui.set_moves('random patterned')
                return log_return(random.choices(patterned, weights=patterned_weights,k=1)[0])
                #return random.choices(patterned + unplaced, weights=patterned_weights + unplaced_weights,k=1).pop()
            except(ValueError, IndexError):
              pass
            try:
                # self.gui.set_moves('random')
                return log_return(random.choice(self.word_locations))
            except(ValueError):
                print('returned here')
                return None
                
          else: 
             try:
                # self.gui.set_moves('patterned and unplaced')
                #return random.choices(patterned, weights=patterned_weights,k=1)[0]
                return log_return(random.choices(patterned + unplaced, weights=patterned_weights + unplaced_weights,k=1).pop())
                #print(' unplaced long words', unplaced_long_words)
             except(ValueError, IndexError):  # no more long words
                pass
             try:
                 # self.gui.set_moves('long words')
                 return log_return(unplaced_long_words.pop())               
             except(ValueError, IndexError):
                 pass
             try:
                # self.gui.set_moves('random')
                return log_return(random.choice(self.word_locations))
             except(ValueError):
                return None
 
         
  def populate_words_graph(self, length_first=True, max_iterations=2000, max_possibles=None):
    # for all words attempt to fit in the grid, allowing for intersections
    # some spaces may be known on empty board
    self.start_time = time()
    index = 0 
    self.populate_order = []
    while any([not word.fixed for word in self.word_locations]):
        fixed =  [word for word in self.word_locations if word.fixed]
        if self.debug:
            self.gui.set_message(f' placed {len(fixed)} {index} iterations')
        word = self.get_next_cross_word(index, max_possibles,length_first)   
        
        if word is None:
          if self.debug:
              try:
                print(f'options for word at {word.start} are {options}')
                print('possibles for stuck word', self.possibles)
              except(AttributeError):
                pass
          continue
            
        if self.debug:
          try:
            #self.gui.gs.highlight_squares(word.coords)            
            self.gui.update(self.board)
            sleep(.25)  
          except(AttributeError) as e:
            pass
        if index == max_iterations:
          break
        
        options = self.look_ahead_3(word, max_possibles=max_possibles) # child, coord)   
        if options is None:
          break                   
        index += 1
        
    fixed = [word for word in self.word_locations if word.fixed]   
    
    #self.update_board(filter_placed=False)
    if self.debug:
        self.gui.print_board(self.board)
        print('Population order ', self.populate_order)
    ptime = self.delta_t('time', do_print=False)
    msg = f'Filled {len(fixed)}/ {len(self.word_locations)} words in {index} iterations, {ptime}secs'
    words=len([w for w in self.word_locations if w.word])
    print('no words', words)
    # print(msg)   
    self.gui.set_prompt(msg)
    self.gui.update(self.board) 
    
  
  def get_word(self, wordlist, req_letters, wordlength):
    ''' get a word matching req_letters (letter, position) '''
    match =['.'] * wordlength
    for req in req_letters:
      match[req[1]] = req[0] if req[0] != ' ' else '.'
    match = ''.join(match)
    #self.gui.set_moves(match)
    m = re.compile(match)
    possible_words = [word for word in wordlist if  m.search(word)]
    # remove already placed words
    
    if possible_words:
      try_word = random.choice(possible_words)
      self.score += 1
      return try_word, possible_words
    else:
      # print(f'could find {match} for req_letters')
      return match, None 
      
  def known(self):
    """ Find all known words and letters """
    known = []
    # get characters from empty board
    #written this wa to allow single step during debugging
    [known.append((r,c)) if self.get_board_rc((r,c), self.empty_board) != SPACE and self.get_board_rc((r,c), self.empty_board) != BLOCK  else None for r, rows in enumerate(self.empty_board) for c, char_ in enumerate(rows) ]
    #board = np.array(self.empty_board)
    #known = np.where(board!=BLOCK || board!#==SPACE)
    # now fill known items into word(s)
    if known:
      for word in self.word_locations:
        for k in known:
          if word.intersects(k) : # found one
            if all([wc in known for wc in word.coords]): # full word known
              word.set_word(''.join([self.get_board_rc(pos, self.empty_board) for pos in word.coords]))
              if self.debug:
                  print(f'>>>>>>>>>Set word from known {word}')
              word.match_pattern = word.word
              word.fixed = True
              break
      # now deal with indivdual letters
      # check each coordinate
      for coord in known:
        for word in self.word_locations:
          if word.intersects(coord) : # found one
            letter = self.get_board_rc(coord, self.empty_board)
            match = ''.join([letter if coord == c else '.' for c in word.coords])
            if word.match_pattern:
              word.match_pattern = self.merge_matches(word.match_pattern, match)
            else:
              word.match_pattern = match
            if self.debug:
                print('set word match  from known ', word.start, word.index, word.match_pattern)
    return known
        
  def get_possibles(self, match_pattern, max_possibles=None):
    ''' get a list of words matching match_pattern, if any
    from self.word_dict '''     
    
    known_words = [word.word for word in self.word_locations if word.fixed]
    m = re.compile(match_pattern)
    try:
        possibles = [word for word in self.all_word_dict[len(match_pattern)] 
          if  m.search(word) and word not in known_words]
        l= len(possibles)
        if max_possibles and l > max_possibles:
          possibles= possibles[0:max_possibles]
        if possibles:
            return len(possibles), possibles
        else:
            # print(f'could find {match_pattern} for req_letters')
            return None, match_pattern
    except(KeyError):
         print(match_pattern)
         print(traceback.format_exc())
         return None, match_pattern
                                
  def fix_word(self, word_obj, text):   
     """ place a known word """ 
     if not word_obj.fixed:
       word_obj.set_word(text)
       word_obj.fixed = True
       self.populate_order.append(text)
       word_obj.match_pattern = text
       word_obj.update_grid('', self.board, text)
       if self.debug:
           print(f'Placed word {word_obj}')
       self.update_children_matches(word_obj)      
       for coord, child in word_obj.children.items(): 
         #print(child.match_pattern, type(child.match_pattern))
         child.update_grid('', self.board, child.match_pattern)
         
  def merge_matches(self, a, b):
    ''' take two matches and combine them'''
    if a == '': return b
    elif b == '': return a
    else:
      return ''.join([y if x=='.' else x for x,y in zip(a,b)])    
     
  def update_children_matches(self, word_obj, clear=False):
    """ update the match patterns for children of current wordl
    eg if word = abacus and child1 intersects at pos 1 match for child is 'a.....' """
    parent_word = word_obj.word
    children_dict = word_obj.children
    intersections = word_obj.get_inter()
    coords = word_obj.coords
    for key, child in children_dict.items():
      if clear:
        child.match_pattern = ''
      else:        
        match = []
        for ichild in child.coords:
            l = '.'
            for p, letter in zip(word_obj.coords,parent_word):
                if ichild == p:
                    l=letter 
            match.append(l )
        match = ''.join(match)
        child.match_pattern = self.merge_matches(child.match_pattern, match)
        #if not child.fixed:
           #child.set_word(match)  # for testing
           #child.update_grid('', self.board, match)
            
  def calc_matches(self, word_obj, try_word=None):
    """ calculate the match patterns for children of current word
    eg if word = abacus and child1 intersects at pos 1 match for child is 'a.....' """
    if try_word is None:
        parent_word = word_obj.word
    else:
        parent_word = try_word 
    children_dict = word_obj.children
    intersections = word_obj.get_inter()
    coords = word_obj.coords
    c_dict ={}
    for key, child in children_dict.items():
        match = []
        for ichild in child.coords:
            l = '.'
            for p, letter in zip(word_obj.coords,parent_word):
                if ichild == p:
                    l=letter 
            match.append(l)
        match = ''.join(match)
        c_dict[key]= self.merge_matches(child.match_pattern, match)
    return c_dict
        
  def compute_depths(self):
    """ find how many nodes to traverse before arriving  back at same word"""
    for node in self.word_locations:
        [w.set_visited(False) for w in self.word_locations if w is not node]
        visited = [item for item in self.word_locations if item.get_visited()]
        component = self.bfs(node, visited, stop=self.max_depth)  # Traverse to each node of a graph
        #path = [f'Node={node.index} item={item.index}, {item.start}' for item in component]  
    return component 
    
  def dfs(self, node, graph, visited, component, stop=None):
    component.append(node)  # Store answer
    node.visited = True  # Mark visited
    # Traverse to each adjacent node of a node
    for coord, child in node.children.items():
        if child is stop:
          return
        if not child.get_visited():  # Check whether the node is visited or not
            self.dfs(child, graph, visited, component, stop)  # Call the dfs recursively  
              
  def bfs(self, node, visited, stop=None): #function for BFS
    """ This will return all child node of starting node
    return is a list of dictianaries {'word_obj', 'depth' 'parent'} """
    queue = []
    component=[]
    component.append({'word_obj': node, 'depth':0, 'parent':None})
    node.visited = True
    queue.append((0,None,node))
    
    while queue:          # Creating loop to visit each node      
      depth, coord, item = queue.pop(0)      
      if depth >= stop:
        break   
      #print(f'Depth={depth} Item={item.index} item={item.start}')   
      for coord, child in item.children.items():
        if not child.get_visited():
          component.append({'word_obj': child, 'depth':depth + 1, 'parent':item})
          child.visited = True
          queue.append((depth + 1, coord, child))
    return component
            
  def search(self):
    graph = self.word_locations
    known = self.known()
    if known:
      for word in self.word_locations:
        if word.intersects(known[0]) : # found one
          node = word
          break
    else:
      node = self.word_locations[0]  # Starting node
    [w.set_visited(False) for w in self.word_locations]
    visited = [item for item in graph if item.get_visited()]
    component = []
    self.dfs(node, graph, visited, component)  # Traverse to each node of a graph
    path = [f'{item.index}, {item.start}' for item in component]
    if self.debug:
      print(f"Following is the Depth-first search:")  # Print the answer
      for p in path:
        print(p)
    for i, c in enumerate(component[1:]):
      self.word_locations[i-1].parent_node = c
    return component
    
  def _best_score(self, options):
      """place best choice from options
      the aim is place best word that allows other words to follow
      highest score wins, since this means greatest options for next level
      1000 means only one word fits at some level, so not a good choice
      need to avoid choosing  word that blocks an intersecting word
      options is dictionary of try_word, list of dictionary for intersections , score
      """
      scores =[(key, [v_[0][1] for _, v_ in v.items()]) for key, v in options]
      if self.debug:
          print(f'Scores________{len(scores)} words__________')
          [print(score) for score in scores]
      #def mx(n): return sum(n[1])
      # filter subwords not possible 
      scores1 =[score for score in scores if 0 not in score[1]]
      # filter only one option for subword
      scores2 =[score for score in scores1 if 1000 not in score[1]] # remove unique word
      # if result is empty, reinstate unique word
      if not scores2:
          scores2= scores1
      # still no good, reinstate not possible subword, since we' re probably at end of board fill
      if not scores2:
          scores2 = scores                                      
      s = sorted(scores2, key= lambda x: sum(x[1]), reverse=True)
      if self.debug:
          print(f'Scores filtered_____{len(s)} words__________')
          [print(score) for score in s]
      
      # choose shortest that is not zero
      try:
          # find all best that have same score
          first = sum(s[0][1])
          best = [word for word, score in s if sum(score) >= first - 5]
          if self.debug:
            print('best',best)
          select = random.choice(best)
      except(IndexError):
          return None
      return select
                     
  def _search_down(self, word, dict_parents,try_word=None, max_possibles=None):
        """ recursive function to establish  viabilty of options """
        # sets matches for all children of word using try_word
        #component.append({'try_word': try_word, 'word_obj': word, 'depth':0, 'parent':None})
        
        matches = self.calc_matches(word, try_word)
        found = defaultdict(list)
        for child, depth in dict_parents[word]:
            if child.fixed:
              continue
            coord = word.get_child_coord(child)
            match = matches[coord]        
            length, possibles  = self.get_possibles(match, max_possibles)
            #print(length, 'possible words for ', child.start, child.direction )
            if not length and not child.fixed:
                found[child].append((match, 0))
                
            elif length == 1:
                if not child.fixed:
                   found[child].append((possibles.pop(), 1000))
                   
            else:
              try:
                found[child].append((lprint(possibles,3), length)) # must be atleast 1
                #found[child].append((possibles,100 * depth + length)) # must be atleast 1
                for index, try_word in enumerate(possibles): 
                    #self.gui.set_message2(f'{index}/{length} possibles  at {child.start} trying {try_word}')
                    result = self._search_down(child, dict_parents, try_word, max_possibles)
                    found[child].extend(result)
              except(KeyboardInterrupt):
                  return None
                    
        return found # list of True, False for this top,level option
          
  def look_ahead_3(self, word, max_possibles=100):
    """ This uses breadth first search  to look ahead
       use max_possibles with a full word 
       list comprehensions are extensively used to allow simple stepove during debug
       for defined word puzzles. there is no guessing. there can be only one solution, so if a decision cannot be made in this iteration, it must be der
       deferred  to later.
       Use varaible max_possibles to switch between unconstrained and constrained puzzles """
    #self.update_board(filter_placed=True)
    #sleep(1) 
    
    [w.set_visited(False) for w in self.word_locations]
    [word.set_visited(True) for w in self.word_locations if w.fixed]
    visited = [item for item in self.word_locations if item.get_visited()]
    components = self.bfs(word, visited, stop=self.max_depth)
    if False: #self.debug:
      for c in components:
        try:
          print(f"{c['word_obj'].start}{c['word_obj'].direction}  depth={c['depth']} parent={c['parent'].start}{c['parent'].direction}")
        except:
          pass
    # now have  list of dictionaries {'word_obj', 'depth' 'parent'}
    # create dictionary of children of each parent
    
    # create a new dictionary using parent word as key
    dict_parents = defaultdict(list) 
    {dict_parents[c['parent']].append((c['word_obj'], c['depth'])) for c in components if c['parent'] is not None}    
    # {dict_parents[c['parent']].append(c['word_obj']) for c in components if c['parent'] is not None}   
    if self.debug:
        print('>Start', word) 
    #[print('parent ', k.start,k.direction,[str(f.start)+f.direction for f in v]) for k,v in dict_parents.items()]
    match = word.match_pattern    
    length, possibles  = self.get_possibles(match, max_possibles)
    if self.debug:
        print(length, 'possible words')
    options = []
    try:
        # simple solutions 
        if word.fixed:
          result = True
        # no word fits here
        elif length is None and not word.fixed:          
            result = False #print(f'wrong parent word {word.word} shouldnt be here')
        # only one word fits
        elif  length == 1:
            # only word. use it
            self.fix_word(word, possibles.pop()) 
            if self.debug:
                print('>>>>>>>>fix word line 701', word)
            result = True
        # ok now need to look ahead
        else: 
            options = []          
            max_component = []
            for index, try_word in enumerate(possibles):
              if self.debug:
                  self.gui.set_message(f'{index}/{length} possibles  at {word.start} trying {try_word}')
              result = self._search_down(word, dict_parents, try_word=try_word, max_possibles=max_possibles)   
              # need result to be greatest number of hits in order to best choose options    
              #if self.debug:
              #    print('Try Word ', try_word)
              #     [print('Key', k, v)  for k, v in result.items()]                             
              if result is None:
                if self.debug:
                    print('result is NoneXXXXXXXXXXXXXXXXXXXXXXXX')                
                return None
              if max_possibles:
                 if all(result):
                    options.append((try_word, result))
              else:                
                #if all(result):
                valid = True
                for i in result.values():
                  if len(i) == 1 and i.pop()[1] == 0:
                    valid = False
                    break # not valid
                if valid:
                   options.append((try_word, result))  
            #if self.debug:    
            #    print('result OPTIONS ',word, options)
            if len(options) == 1 and not word.fixed :
                self.fix_word(word, options.pop()[0])
                if self.debug:
                    print('>>>>>>>>>>fix word line 703 ', word)
                
                result = True 
                #print(f'try_word at {word.start} {try_word} {result}')
            elif options: #and max_possibles:
                # dealwith only one option is not zero              
                _options =[option for option in options if option[1] != 0]
                if len(_options) == 1:
                     self.fix_word(word, _options.pop()[0]) # already random
                     if self.debug:
                         print('>>>>>>>>>fix word line 773 from max options ', word)
                     return
                # deal with one option being large and all others = 100
                _options =[option for option in options if option[1] != 1000]
                if len(_options) == 1:
                     self.fix_word(word, _options.pop()[0]) # already random
                     if self.debug:
                         print('>>>>>>>>>fix word line 773 from max options ', word)
                     return
                     
                if max_possibles:
                    select = self._best_score(_options)
                    if select:
                       self.fix_word(word, select) # already random
                       if self.debug:
                          print('selectxxxxxxxxxxxxx', select)
                          print('>>>>>>>>>fix word line 773 from max options ', word)
  
    except(Exception, IndexError):
        print(locals())
        print(traceback.format_exc()) 
            
    finally:       
        return options # unplaced option   
