from freecell.card import Card
from freecell.deck import Deck


class Freecell:
    def __init__(self):
        self.pile = [[], [], [], [], [], [], [], []]
    
        self.freecell_deck = Deck(1, 13, 4)
        self.freecell_deck.shuffle()
        column = 0
        while not self.freecell_deck.is_empty():
            self.pile[column].append(self.freecell_deck.draw_card())
            column += 1
            if column % 8 == 0:
                column = 0
    
        self.foundation = [[], [], [], []]
        self.cell = [[], [], [], []]

    def __int__(self, foundation, pile, cell):
        """
        Build a deck containing 52 cards
        Deal the cards into 8 cascades
        Build 4 foundations and 4 cells
        """
        self.foundation = foundation
        self.pile = pile
        self.cell = cell


    def print_game(self):
        print()
        print("      Cells:                   Foundation:")
        #cell and foundation
        for i in range(4):
            print('%8d' % (i + 1), end='')
        print('    ', end='')
        for i in range(4):
            print('%8d' % (i + 1), end='')
        print()

        for c in self.cell:
            try:
                print("%8s" % (c[0]), end='')
            except IndexError:
                print("%8s" % (''), end='')

        print('    ', end='')
        for stack in self.foundation:
            try:
                print("%8s" % (stack[-1]), end='')
            except IndexError:
                print("%8s" % (''), end='')

        print()
        print('------------------------------------------------------------------------')

        print("      pile")
        for i in range(len(self.pile)):
            print("%8d" % (i + 1), end='')
        print()

        max_length = max([len(stack) for stack in self.pile])

        for i in range(max_length):
            print(' ', end='')
            for stack in self.pile:

                try:
                    print("%8s" % (stack[i]), end='')
                except IndexError:
                    print("%8s" % (''), end='')
            print()
        print('------------------------------------------------------------------------')

    ########################################
    #  Check the move whether valid or not

    def move_to_foundation(self, p_col, f_col):
        '''
        moves a card at the end of a column of pile to a foundation
        True if the move is valid, False otherwise
        '''
        the_pile = self.pile[p_col - 1]
        the_foundation = self.foundation[f_col - 1]

        if the_pile == []:
            return False
        else:
            if the_foundation == []:
                if the_pile[-1].face == "A":
                    return True
                else:
                    return False
            else:
                if the_foundation[-1].suit == the_pile[-1].suit and the_foundation[
                    -1].get_face_index() == the_pile[-1].get_face_index() - 1:
                    return True
                else:
                    return False

    def move_to_cell(self, p_col, c_col):
        '''
        moves a card at the end of a column of pile to a cell
        True if the move is valid, False otherwise
        '''

        the_card = self.pile[p_col - 1]
        the_cell = self.cell[c_col - 1]
        if the_cell == []:
            return True
        else:
            return False

    def move_to_pile(self, c_col, p_col):
        '''
        moves a card in the cell to a column of pile
        True if the move is valid, False otherwise
        '''
        the_cell = self.cell[c_col - 1]
        the_pile = self.pile[p_col - 1]
        if the_cell == []:
            return False
        else:
            if the_pile == []:
                return True
            else:
                cell_card = self.cell[c_col - 1][-1]
                the_card = self.pile[p_col - 1][-1]
                if cell_card.get_face_index() == the_card.get_face_index() - 1 and cell_card.get_color() != the_card.get_color():
                    return True
                else:
                    return False

    def move_in_pile(self, p_col_source, p_col_dest):
        '''
        move card from one pile column to another
        True if the move is valid, False otherwise
        '''
        the_source = self.pile[p_col_source - 1]
        the_dest = self.pile[p_col_dest - 1]
        if the_source == []:
            return False
        else:
            if the_dest == []:
                return True
            else:
                the_card = the_source[-1]
                dest_card = the_dest[-1]
                if the_card.get_face_index() == dest_card.get_face_index() - 1 and dest_card.get_color() != the_card.get_color():
                    return True
                else:
                    return False

    def cell_to_foundation(self, c_col, f_col):
        '''
        moves a card of cell to a foundation
        returns: Boolean (True if the move is valid, False otherwise)
        '''

        the_cell = self.cell[c_col - 1]
        the_foundation = self.foundation[f_col - 1]
        if the_cell == []:
            return False
        else:
            if the_foundation == []:
                if the_cell[-1].face == "A":
                    return True
                else:
                    return False
            else:
                if the_foundation[-1].suit == the_cell[-1].suit and the_foundation[
                    -1].get_face_index() == the_cell[-1].get_face_index() - 1:
                    return True
                else:
                    return False

    ########################################
    #  Move Card
    
    def p2f(self, p_col, f_col):
        if self.move_to_foundation(p_col, f_col) == True:
                        the_card = self.pile[p_col - 1].pop()
                        self.foundation[f_col - 1].append(the_card)
        else:
            return 'Invalid move to foundation'
            
    def p2p(self, p_col_source, p_col_dest):
        if self.move_in_pile(p_col_source, p_col_dest) == True:
            the_card = self.pile[p_col_source - 1].pop()
            self.pile[p_col_dest - 1].append(the_card)
        else:
            return 'Invalid move to pile'
    
        
    def p2c(self, p_col, c_col):
        if self.move_to_cell(p_col, c_col) == True:
            the_card = self.pile[p_col - 1].pop()
            self.cell[c_col - 1].append(the_card)
        else:
            return 'Invalid move to cell'
    
    def c2p(self, c_col, p_col):
        if self.move_to_pile(c_col, p_col) == True:
            the_card = self.cell[c_col - 1].pop()
            self.pile[p_col - 1].append(the_card)
        else:
            return 'Invalid move to pile'
            
    def c2f(self, c_col, f_col):
        if self.cell_to_foundation(c_col, f_col) == True:
            the_card = self.cell[c_col - 1].pop()
            self.foundation[f_col - 1].append(the_card)
        else:
            return 'Invalid move to pile'     

    def win_game(self):
        '''
        Check whether the player wins
        '''
        for i in range(0, 4):
            if len(self.foundation[i]) == 13:
                print('''
                
 .----------------.  .----------------.  .-----------------.
| .--------------. || .--------------. || .--------------. |
| | _____  _____ | || |     _____    | || | ____  _____  | |
| ||_   _||_   _|| || |    |_   _|   | || ||_   \|_   _| | |
| |  | | /\ | |  | || |      | |     | || |  |   \ | |   | |
| |  | |/  \| |  | || |      | |     | || |  | |\ \| |   | |
| |  |   /\   |  | || |     _| |_    | || | _| |_\   |_  | |
| |  |__/  \__|  | || |    |_____|   | || ||_____|\____| | |
| |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '---------------
                ''')
                return True
            else:
                return False

    def welcome_game(self):
        '''
        print freecell banner
        state the rules of freecell
        '''
        print('''       
 o__ __o__/_                                                             o    o  
 <|    v                                                                 <|>  <|> 
 < >                                                                     / \  / \ 
  |         \o__ __o     o__  __o     o__  __o       __o__    o__  __o   \o/  \o/ 
  o__/_      |     |>   /v      |>   /v      |>     />  \    /v      |>   |    |  
  |         / \   < >  />      //   />      //    o/        />      //   / \  / \ 
 <o>        \o/        \o    o/     \o    o/     <|         \o    o/     \o/  \o/ 
  |          |          v\  /v __o   v\  /v __o   \\         v\  /v __o   |    |  
 / \        / \          <\/> __/>    <\/> __/>    _\o__</    <\/> __/>  / \  / \ 
                                                                                  
            ''')

        print("To Win")
        print("\tMove all the cards to the Foundations")

        print("Foundation")
        print("\tSorted Cards in a suit from Ace to King")

        print("pile")
        print("\tShuffled 8 piles of cards")

        print("Cell")
        print("\tEmpty 4 slots to put 1 card each")

        print("Rules")
        print("\tOnly 1 card be moved a time")
        print("\tCard placed in pile should be different color")
        print("\tand one less rank e.g. red 3 be placed on black 4")
        print("\tAn empty pile can put any card ")

    def game_help(self):
        '''
        parameters: none
        returns: nothing
        prints the supported commands
        '''
        print("Input should be")
        print("\t p2f #P #F -- Pile to Foundation 1: ")
        print("\t e.g. Pile 2 to Foundation: p2f 2 1 ")
        print("\t p2p #P #P -- Pile to Pile: ")
        print("\t e.g. Pile 2 to Pile 1: p2f 2 1 ")
        print("\t p2c #P #C -- Pile to Cell: ")
        print("\t e.g. Pile 2 to Cell 1: p2c 2 1 ")
        print("\t c2p #C #P -- Cell to Pile: ")
        print("\t e.g. Cell 2 to Pile 1: c2p 2 1 ")
        print("\t c2f #C #F -- Cell to Foundation: ")
        print("\t e.g. Cell 2 to Foundation 1: c2f 2 1 ")
        print("\t 'h' for help")
        print("\t 'q' to quit")
        

def main():
    import time
    print('''   
    ┬ ┬┌─┐┬  ┌─┐┌─┐┌┬┐┌─┐
    │││├┤ │  │  │ ││││├┤ 
    └┴┘└─┘┴─┘└─┘└─┘┴ ┴└─┘   ......
    ''')
    time.sleep(2)
    newgame = Freecell()
    newgame.welcome_game()
    time.sleep(2)
    newgame.game_help()
    time.sleep(2)
    while newgame.win_game() == False:
        newgame.print_game()
        user_input = input("Please type in your move: ")
        user_input = user_input.strip()
        user_input_list = user_input.split()
        if len(user_input_list) > 0:
            mode = user_input_list[0]
            if mode == 'p2f':
                if user_input_list[1] in "1 2 3 4 5 6 7 8".split() and user_input_list[
                    2] in "1 2 3 4".split():
                    p_col = int(user_input_list[1])
                    f_col = int(user_input_list[2])
                    newgame.p2f(p_col, f_col)
                else:
                    print("Invalid column range")

            elif mode == 'p2p':
                if user_input_list[1] in "1 2 3 4 5 6 7 8".split() and user_input_list[
                    2] in "1 2 3 4 5 6 7 8".split():
                    p_col_source = int(user_input_list[1])
                    p_col_dest = int(user_input_list[2])
                    newgame.p2p(p_col_source, p_col_dest)
                else:
                    print("Invalid column range")

            elif mode == 'p2c':
                if user_input_list[1] in "1 2 3 4 5 6 7 8".split() and user_input_list[
                    2] in "1 2 3 4".split():
                    p_col = int(user_input_list[1])
                    c_col = int(user_input_list[2])
                    newgame.p2c(p_col, c_col)
                else:
                    print("Invalid column range")

            elif mode == 'c2p':
                if user_input_list[1] in "1 2 3 4".split() and \
                    user_input_list[2] in "1 2 3 4 5 6 7 8".split():
                    c_col = int(user_input_list[1])
                    p_col = int(user_input_list[2])
                    newgame.c2p(c_col,p_col)
                else:
                    print("Invalid column range")

            elif mode == 'c2f':
                if user_input_list[1] in "1 2 3 4".split() and user_input_list[2] in "1 2 3 4".split():
                    c_col = int(user_input_list[1])
                    f_col = int(user_input_list[2])
                    newgame.c2f(c_col,f_col)
                else:
                    print("Invalid column range")

            elif mode == 'q':
                break
            elif mode == 'h':
                newgame.game_help()
            else:
                print('Unknown command:', mode)
        else:
            print("Unknown Command:", user_input)
    print('''
         ________                __      __  __               __
        /_  __/ /_  ____ _____  / /__    \ \/ /___  __  __   / /
         / / / __ \/ __ `/ __ \/ //_/     \  / __ \/ / / /  / / 
        / / / / / / /_/ / / / / ,<        / / /_/ / /_/ /  /_/  
       /_/ /_/ /_/\__,_/_/ /_/_/|_|      /_/\____/\__,_/  (_)   
                                                         
                                                
            ''')


if __name__ == '__main__':
    main()

    
    













