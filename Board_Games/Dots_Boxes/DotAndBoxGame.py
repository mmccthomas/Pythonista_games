import random
import copy
import math
import time


class dotsboxes(object):
    
    def __init__(self, rows, columns):
        self.play_dict = {}
        for i in range((rows)):
            for j in range(columns-1):
                self.play_dict[((j+(i*columns)), j+(i*columns)+1)] = 0
        
        #creates the possible vertical plays
        for i in range(rows-1):
            for j in range (columns):
                self.play_dict[(j+(i*columns), j+columns+(i*columns))] = 0
        self.score_dict = {}
        
        for i in range((rows-1)): 
            for j in range(columns-1): 
                box = [(j + i*columns, j+i*columns +1)]
                box.append((box[0][0], box[0][1] + columns - 1))
                box.append((box[0][0] + 1, box[0][1] + columns))
                box.append((box[0][0] + columns, box[2][1]))
                self.score_dict[tuple(box)] = 0
        
      
        self.row_count = rows
        self.column_count = columns
        
        #scorekeeping
        self.a_score = 0
        self.b_score = 0
        
    def render_row(self, i):
       
        left = (i * self.column_count)
        right = left + 1
        for j in range(self.column_count - 1):
            if self.play_dict[(left, right)] == 0:
                print("{:^3d}".format(left), end = "   ") 
            else: 
                print("{:^3d} -".format(left), end = " ")
            left = right
            right = left + 1
        print("{:^3d}".format(left))
        
    def render_vertical(self, upper_left, upper_right):
        if self.play_dict[(upper_left, upper_right)] == 0:
            print("  ", end = " ")
        else:
            print(" |", end = " ")
    
    def render_middle_row(self, i):
        upper_left = (i * self.column_count)
        upper_right = upper_left + 1
        bottom_left = upper_left + self.column_count
        bottom_right = bottom_left + 1
        
        for j in range(self.column_count - 1):
           
            self.render_vertical(upper_left, bottom_left)
       
            top = (upper_left, upper_right)
            left = (upper_left, bottom_left)
            right = (upper_right, bottom_right)
            bottom = (bottom_left, bottom_right)
            score = self.score_dict[(top, left, right, bottom)]
            
            if score == 0:
                print("  ", end = " ")
            else: 
                print(" " + score, end = " ")
            
          
            upper_left, bottom_left = upper_right, bottom_right
            upper_right += 1
            bottom_right += 1
        self.render_vertical(upper_left, bottom_left)
        print()
        
    
    def render(self):
        
        for i in range(self.row_count - 1):
       
            self.render_row(i)
            self.render_middle_row(i)
            
        self.render_row(self.row_count - 1)
        print("\nPlayer A: {} Player B: {}".format(self.a_score, self.b_score))
        
    def check_for_scores(self, player_a):
        
        player = "A" if player_a else "B"
        
       
        taken_set = {k for k, v in self.play_dict.items() if v == 1}
        open_scores = [k for k, v in self.score_dict.items() if v == 0]
        
        score_counter = 0
        
        
        for box in open_scores:
            #if a new score is found:
            if set(box).issubset(taken_set):
                score_counter += 1
                #keeps track of the score in the dict:
                self.score_dict[box] = player
        return(score_counter) #returns the score
                
    
    def make_play(self, start_point, end_point, player_a):
       
        try:
          
            if self.play_dict[(start_point, end_point)] == 1:
                return(False)
        except KeyError:
            return(False)
        
        self.play_dict[(start_point, end_point)] = 1
      
        score = self.check_for_scores(player_a)
        if player_a:
            self.a_score += score
        else:
            self.b_score += score
        return(True)
            
    def get_open_plays(self):
        #return([i for i in self.play_dict if self.play_dict[i] == 0])
        return([k for k, v  in self.play_dict.items() if v == 0])
        
    def isover(self):
    
        return(self.a_score + self.b_score == len(self.score_dict))
        
class random_player(object):
   
    def __init__(self, player_a):
      
        self.player = player_a
        
    def make_play(self, game):
      
        list_of_plays = game.get_open_plays()
        play = random.choice(list_of_plays)
        game.make_play(*play, self.player)
        player = "A" if self.player else "B"
        print("Player {}'s move: {} {}".format(player, *play))
        return play

class human_player(object):
   
    def __init__(self, player_a):
       
        self.player_a = player_a
        self.playername = "A" if player_a else "B"
    
    def make_play(self, game, move=None):
      
            #while True:
            if move is None:
                move = input("Player {}, make your move (start point end point):"\
                             .format(self.playername))
                move = move.split()
            try:
                move[0], move[1] = int(move[0]), int(move[1])
                if len(move) != 2: 
                    print("Error. Input must be of form start point, endpoint")
            
            except NameError: 
                print("Error. Input must be of form start point, endpoint")
                #continue
            except IndexError: 
                print("Error. Input must be of form start point, endpoint")
                #continue
            except ValueError:
                print("Error. Input must be of form start point, endpoint")
                #continue
            move.sort() 
            valid_move = game.make_play(*move, self.player_a)
            if valid_move:
                return valid_move
            print("Error. That move does not exist. Try again")
            return valid_move
        
        
class alphabeta_player(object):
    
    def __init__(self, player_a):
        self.player = player_a
        
    def alphabeta(self, game, play, depth, alpha, beta, player_a):
       
        if (game.isover()) or depth == 0:
          
            return((game.a_score - game.b_score, play))
        if player_a:
            value = -math.inf 
            for move in game.get_open_plays():
               
                new_game = copy.deepcopy(game)
                old_score = new_game.a_score
                new_game.make_play(*move, True)
                new_score = new_game.a_score
                
                
                if new_score == old_score:
                    new_play_results = self.alphabeta(new_game, move, \
                                            depth - 1, alpha, beta, False)
                else:
                    new_play_results = self.alphabeta(new_game, move, \
                                            depth - 1, alpha, beta, True)
                    
            
                if value >= new_play_results[0]:
                    play = move
                    value = new_play_results[0]
                
              
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return(value, play)
        
        else:
      
            value = math.inf
            for move in game.get_open_plays():
                
                new_game = copy.deepcopy(game)
                old_score = new_game.b_score
                new_game.make_play(*move, False)
                new_score = new_game.b_score
                
                if new_score == old_score:
                    move_results = self.alphabeta(new_game, move, depth-1, \
                                                  alpha, beta, True)
                else:
                    move_results = self.alphabeta(new_game, move, depth-1, \
                                                  alpha, beta, False)
                
                if value <= move_results[0]:
                    play = move
                    value = move_results[0]
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return(value, play)
    
    def make_play(self, game):
 
        start_time = time.time()

        play_space_size = len(game.get_open_plays())
        total_plays = len(game.play_dict)
        values = range(total_plays// 2, total_plays)
        
        match play_space_size:
          case 0:
              return None # finished  
          case 1:
              play = random.choice(game.get_open_plays())
              game.make_play(*play, self.player)
              return play
          # random until half way through
          case val if  play_space_size in values:
              play = random.choice(game.get_open_plays())             
              game.make_play(*play, self.player)
          case _:
              depth = math.floor(math.log(19000, play_space_size))                       
              play = self.alphabeta(game, (0, 0), depth, -math.inf, math.inf, \
                                    self.player)[1]             
              print('play =', play)
              if play == (0, 0):                 
                  play = random.choice(game.get_open_plays())
              game.make_play(*play, self.player)
        
        elapsed = time.time() - start_time
        player = "A" if self.player else "B"
        print("Player {}'s move: {} {}".format(player, *play))
        print(f"Time elapsed to make move: {elapsed:,.2f}")
        return play
        

class game(object):
      
    def __init__(self, player_a_type = "random" , player_b_type = "random", \
                 rows = 5, columns = 5):
     
        self.show_render = True
        self.rows = rows
        self.columns = columns
        
     
        if player_a_type == "random":
            self.player_a = random_player(True)
        elif player_a_type == "alphabeta":
            self.player_a = alphabeta_player(True)
        else:
            self.player_a = human_player(True)
            
      
        if player_b_type == "random":
            self.player_b = random_player(False)
        elif player_b_type == "alphabeta":
            self.player_b = alphabeta_player(False)
        else:
            self.player_b = human_player(False)
        
    def play_game(self):      
  
        game = dotsboxes(self.rows, self.columns)
        
        print()
        if self.show_render:
            game.render()
        print()
      
        coin_toss = random.randint(1, 2)
        print("The coin landed on {}".\
              format("heads" if coin_toss == 1 else "tails"))
        print("Player {} goes first".format("A" if coin_toss == 1 else "B"))
        print()
            
        while not(game.isover()):
            
           
            while not(game.isover()):
             
                if coin_toss == 2:
                    coin_toss = 3
                    break
                old_score = game.a_score
                self.player_a.make_play(game)
                if self.show_render:
                    game.render()
                if old_score == game.a_score:
                    break
    
            while not(game.isover()):
                old_score = game.b_score
                self.player_b.make_play(game)
                if self.show_render:
                    game.render()
                if old_score == game.b_score:
                    break
      
        if game.a_score == game.b_score:
            print("It's a tie!")
        elif game.a_score >= game.b_score:
            print("A wins!")
        else:
            print("B wins!")
                
def main():
    print("Welcome to dots and boxes!")
    print("Rules about the game can be found here:"\
          "https://en.wikipedia.org/wiki/Dots_and_Boxes")
    
   
    loop = "y"
    while loop == "y":
        
      
        playtype = input("Press r to play against a random player. "\
                         "Press i for a more intelligent one.(Intelligent "\
                         "takes player ~5-10 seconds to think): ").lower()
        
 
        if (playtype != "r") and (playtype != "i"):
            print("Invalid game type. Please try again")
            continue
        
     
        player_b = "alphabeta" if playtype == "i" else "random"
        
 
        while True:
         
            rows = input("How many rows should the grid have? "\
                         "(limit 500): ")
         
            try:
                rows = int(rows)
                if rows > 500:
                    print("Too many rows! Please try again (limit 500)")
                    continue
            except ValueError:
                print("Not an integer. Please try again.")
                continue
            break
        while True:
     
            limit = math.floor(min(16, 9999/rows))
            columns = input("How many columns should the grid have?" \
                            "(limit {}): ".format(limit))
            try:
                columns = int(columns)
                if columns > limit:
                    print("Too many columns! Try again (limit {})"\
                          .format(limit))
                    continue
            except ValueError:
                print("That is not an integer value! try again")
                continue
            break
        
        gameplay = game("Human", player_b, rows, columns)
        gameplay.play_game()
        
        loop = input("Play again?(y/n): ")
        
    print("Thank you for playing! c:")
    

if __name__ == "__main__":
    main()
