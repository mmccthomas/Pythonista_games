###################################
# Test Module for Class Card and Deck
###################################

'''
The test module build based on the course content of
Michigan State University CSE231 2013 Fall project #8
introduction materials.
'''
from card import Card
from deck import Deck

'''
1. Test Print function on Deck
'''

my_deck = Deck(1, 13, 4)
print("======Basic Sring Representation=====")
print(my_deck)

print("======In Column Format=====")
my_deck.column_print()

my_deck.shuffle()
print("======Shuffled Deck=====")
my_deck.column_print()

'''
2. Test Methods on Card in a poker game context
'''
a_card = my_deck.draw_card()
print("The top card to throw is:",a_card)

print('How many cards left:', len(my_deck))

print("Is this an empty deck?",my_deck.is_empty())

# Simulate a playing context
Dealer_list=[]
Player_list=[]

for i in range(5):
    Dealer_list.append(my_deck.draw_card())
    Player_list.append(my_deck.draw_card())

print("\nDealer:", Dealer_list)
print("Player:", Player_list)
print()

# take the last card dealt out of each hand
last_card_Dealer = Dealer_list.pop()
last_card_Player = Player_list.pop()
print("Dealer threw down",last_card_Dealer, ", Player threw down", last_card_Player)
print("Hands are now:",Dealer_list, Player_list)

# check the compare functions
if last_card_Dealer.equal_face(last_card_Player):
    print(last_card_Dealer, last_card_Player, "of equal rank")
elif last_card_Dealer.get_face_index() > last_card_Player.get_face_index():
    print(last_card_Dealer, "of higher rank than",last_card_Player)
else:
    print(last_card_Player, "of higher rank than",last_card_Dealer)


if last_card_Dealer.equal_suit(last_card_Player):
    print(last_card_Dealer,'of equal suit with',last_card_Player)
else:
    print(last_card_Dealer,'of different suit than',last_card_Player)
