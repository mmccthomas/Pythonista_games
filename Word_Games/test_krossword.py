# test solve of all puzzles in krossword
# test user interaction of one puzzle
import Krossword
from copy import deepcopy
import numpy as np

obj = Krossword.KrossWord()
obj.gui.clear_numbers()
obj.gui.clear_messages()

agg = Counter(all)
agg = sorted(dict(agg).items())
pass
xs = [k[0][1] for k in agg]
ys = [-k[0][0] for k in agg]
s = [k[1] for k in agg]

plt.scatter(xs, ys, s=[15*s1 for s1 in s])
[plt.text(x, y, str(i), color="red", fontsize=12) for x, y, i in zip(xs, ys, s)]
plt.show()
wordlist = sorted(list(set(sum([sum(a.values(), []) for a in all_words], []))))

#with open('wordlists/krosswords.txt', 'w') as f:
#  f.write('\n'.join(wordlist[:-1]))
