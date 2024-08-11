import numpy as np
from PIL import Image
from matplotlib import pyplot as plt   
from statistics import mode
""" scan a crossword image to detect squares and blocks (black squares) to produce a 
text representation in the for ' / /#/ / '
"""
    
def rle(inarray):
  """ run length encoding. Partial credit to R rle function. 
  Multi datatype arrays catered for including non Numpy
  returns: tuple (runlengths, startpositions, values) """
  ia = np.asarray(inarray)                # force numpy
  n = len(ia)
  if n == 0: 
    return (None, None, None)
  else:
    y = ia[1:] != ia[:-1]               # pairwise unequal (string safe)
    i = np.append(np.where(y), n - 1)   # must include last element posi
    z = np.diff(np.append(-1, i))       # run lengths
    p = np.cumsum(np.append(0, z))[:-1] # positions
    return(z, p, ia[i])

def scan_xword(image_name, crossword_file):                
    im = np.array(Image.open(image_name).convert('L'),dtype=np.uint8)
    im = im /255
    dec = 3
    im_small = im[:-dec:dec,:-dec:dec]
    sizex, sizey = im_small.shape
    # do rle encoding on array to find size of squares
    lens = []
    for i in range(sizey):
      z,_,_ = rle(im_small[i,:])
      z= z[z>1]
      z=z[z<sizey - 1]
      lens.extend(z)
    mode_ = mode(lens)
    no_squares = int(sizey / mode_)  
    
    board = np.zeros((no_squares+1, no_squares+1), dtype=np.uint8)
    
    for i in range(sizey):
       z, p, ia = rle(im_small[i,:])
       for index, x in enumerate(p):
         l = round(z[index] / mode_)
         xpos = round(x / mode_)
         ypos = round(i / mode_)
         val = round(ia[index])     
         try:
           if l > 0:
             board[ypos][xpos: xpos + l] = val
             print(f'y={ypos},x={xpos},val={val}, length={l}')
         except (IndexError):
           pass
    
    char_board = np.copy(board).astype(dtype=np.dtype('U1'))
    char_board[char_board=='1']=' ' 
    char_board[char_board=='0']='#' 
    
    a = [np.apply_along_axis('/'.join, 0, char_board[i]) for i in range(char_board.shape[0])]
    for b in a:
      print(b)
     
    #plt.imshow(board,cmap='gray',vmin=0,vmax=1)    
    plt.imshow(im_small,cmap='gray',vmin=0,vmax=1)
    plt.show()   
    
    # add to file
    with open(crossword_file, 'a') as f:
      f.seek(2)
      f.write("\n")
      f.write(f"{image_name.split('.')[0]}_frame:\n")
      for line in a:
        f.write("'" + str(line))
        f.write("'\n")
if __name__ == "__main__":
  scan_xword('Cross2 2.jpg','test.txt')
