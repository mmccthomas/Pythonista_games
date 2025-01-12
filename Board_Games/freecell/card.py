class Card:
    # A face list to build card
    face_range = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    # A index to refer face easily
    face_index = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
                   'J': 11, 'Q': 12, 'K': 13}

    # A suit list to build card: c = clubs, s = spade, h = heart, d=  diamond
    suit_range = ['c', 'h', 's', 'd']
    suit_name = {'c': 'Clubs', 'h': 'Hearts', 's': 'Spades', 'd': 'Diamonds'}
    # A index to refer suit easily
    suit_index = {'c':1, 'h':2, 's':3, 'd':4}


    def __init__(self, face = None, suit = None, color = None):

        # the face value and the suit
        if face in self.face_range and suit in self.suit_range:
            self.face = face
            self.suit = suit
            if self.face == 'T':
            	  self.image = f'card:{self.suit_name[self.suit]}10'
            else:
                self.image = f'card:{self.suit_name[self.suit]}{self.face}'
            self.tileobject = None
        else:
            self.face = None
            self.suit = None
            print("Not A Poker Card")

        if self.suit_index.get(self.get_suit())%2 == 0:
            self.color = 'R'
        elif self.suit_index.get(self.get_suit())%2 == 1:
            self.color = 'B'
        else:
            self.color = None

    # string representation of class Card
    def __str__(self):
        if (self.face == None) or (self.suit == None) or (self.color == None):
            return "None"
        else:
            return "{:}{:2}{:}".format(self.face, self.suit, self.color)

    # enter a card name in the shell to print the card
    def __repr__(self):
        return self.__str__()


    # set methods to change face and suit of a card;
    # seldom used in game implementation, build to follow class convention.

    def set_face(self, face):
        self.face = face

    def set_suit(self, suit):
        self.suit = suit
        
    def set_tileobject(self, tile):
        self.tileobject = tile

    # get methods to access attributes of Card class;

    def get_face(self):
        return self.face

    def get_suit(self):
        return self.suit

    def get_color(self):
        return self.color

    def get_face_index(self):
        return self.face_index.get(self.face)

    def get_suit_index(self):
        return self.suit_index.get(self.suit)


    # compare methods to facilitate games
    def equal_face(self, other):
        '''Returns True if ranks are equal.'''
        return self.face == other.face

    def equal_suit(self, other):
        return self.suit == other.suit



def main():
    test_card = Card('K', 's')
    print(test_card)
    for k in test_card.face_range:
    	print(Card(k,'s').image)
  


if __name__ == "__main__":
    main()
