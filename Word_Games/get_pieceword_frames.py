''' extract all pieceword frames
remove the letters leaving only blocks
determine unique grids and statistics for each
to find best template grids
minimise 3 letter words
'''
import test_pieceword
import Letter_game
import numpy as np

def inList(array, list):
    for element in list:
        if np.array_equal(element, array):
            return True
    return False
    
puzzles, all_frames, lengths = test_pieceword.main()
frames = []
for fr in all_frames:
   fr[np.char.isalpha(fr)] = ' '
   frames.append(fr.copy())


unique_frames = []
all_lengths = []
all_names = []
print(len(puzzles), len(frames), len(lengths))
for puzzle, frame, word_loc in zip(puzzles, frames, lengths):  
  if inList(frame, unique_frames):
      print('duplicate', puzzle)
      continue
  
  unique_frames.append(frame.copy())

  print()
  lengths = {}
  for word in word_loc:
      if word.direction == 'across':
          lengths[word.length] = lengths.get(word.length, 0) + 1
  all_lengths.append(dict(sorted(lengths.items())).copy())
  all_names.append(puzzle)
  
# now have unique boards, word lengths and names
# sort them by word lengths
result = [{'puzzle': puzzle, 'frame':	'\n'.join(['/'.join(row) for row in frame]), 'lengths': length} for puzzle, frame, length in zip(all_names, unique_frames, all_lengths)]
print(f'In {len(all_frames)}, {len(unique_frames)} were unique')

print('sorted')
result = sorted(result, key=lambda d: min(d['lengths'].keys()))
for d in result:
	print(d['puzzle'], d['lengths'])
	# print(d['frame'])
# select ones with fewest 3 letter words	
for i, d in enumerate(result[-12:]):
	print(f'Puzzle{i+1}_frame:')
	print(d['frame'])
	print()
	


