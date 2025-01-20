from freecell.card import Card
import random

class Deck:
    def __init__(self, value_start = None, value_end = None, number_of_suits = None):
        self.deck = []
        if (value_start == None) and (value_end == None) and (number_of_suits == None):
            self.deck = self.deck
        else:
            for s in Card.suit_range[0:number_of_suits]:
                for f in Card.face_range[value_start-1:value_end]:
                    self.deck.append(Card(f, s))
                    

    def __str__(self):
        if self.deck == []:
            return '[_]'
        else:
            return ','.join([item.get_face() + item.get_suit() + ":" + item.get_color()
                               for item in self.deck])

    def __len__(self):
        return len(self.deck)

    def __getitem__(self, index):
        return self.deck[index]

    def __repr__(self):
        return self.__str__()

    def column_print(self, column_len = 8):
        for index, card in enumerate(self.deck):
            if index % column_len == 0:  # at final column so print a carriage return
                print()
            print('{:}'.format(card), end='')
        print()
        print()


    def get_top_card(self):
        if len(self.deck) != 0:
            return self.deck[-1]
        else:
            return None

    def is_empty(self):
        if self.deck == []:
            return True
        else:
            return False

    def shuffle(self):
        random.shuffle(self.deck)

    def add_card(self, card):
        self.deck.append(card)

    def draw_card(self):
        if len(self.deck) != 0:
            return self.deck.pop()
        else:
            return None




def main():
    test_deck = Deck(1,13,4)
    test_deck.column_print()



if __name__ == "__main__":
    main()
