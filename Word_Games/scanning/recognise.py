# text and rectangles recognition
import objc_util
import numpy as np
from PIL import Image
from io import BytesIO
import traceback
import pandas as pd
from matplotlib import pyplot
import straighten_image
DEBUG=False

VNImageRequestHandler = objc_util.ObjCClass('VNImageRequestHandler')
VNRecognizeTextRequest = objc_util.ObjCClass('VNRecognizeTextRequest')
VNDetectRectanglesRequest = objc_util.ObjCClass('VNDetectRectanglesRequest')
VNRectangleObservation = objc_util.ObjCClass('VNRectangleObservation')

import appex
from PIL import Image
from PIL.ExifTags import TAGS
import clipboard
exif_rotations = {
1: '0 degrees: the correct orientation, no adjustment is required.',
2: '0 degrees, mirrored: image has been flipped back-to-front.',
3: '180 degrees: image is upside down.',
4: '180 degrees, mirrored: image has been flipped back-to-front and is upside down.',
5: '90 degrees: image has been flipped back-to-front and is on its side.',
6: '90 degrees, mirrored: image is on its side.',
7: '270 degrees: image has been flipped back-to-front and is on its far side.'
}
def get_exif(i):
  ret = {}
  # i = Image.open(fn)
  info = i._getexif()
  for tag, value in info.items():
    decoded = TAGS.get(tag, tag)
    ret[decoded] = value
  return ret


def convert_to_png(asset):
    """ convert and  make smaller
    get rotation from exif data """
    filename = 'temp.png'
    img = Image.open(asset.get_image_data()) 
    exif = get_exif(img)
    w = h = r = None
    try:
       w = exif['ExifImageWidth']
       h = exif['ExifImageHeight']
       r = exif['Orientation']
    except (KeyError):
        pass
    props = (w, h, r, exif_rotations.get(r, None))
    scale = h/w
    img = img.resize((1000,1000)) 
    match r:
      case 6:
        img = img.transpose(Image.ROTATE_270) 
      case _:
        pass

    img.save(filename, format="png")   
    # Write PIL Image to in-memory PNG
    #membuf = BytesIO()
    #img.save(membuf, format="png")  
    #return membuf.getvalue()
    return filename, scale, props
    
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
    
def rectangles(asset, aoi=None):
    """Image recognition of rectangles
    to use as subframes
    """
    img_data = objc_util.ns(asset.get_image_data().getvalue()) 
    #img_data = straighten_image.straighten(convert_to_png(asset))
    width = asset.pixel_width
    height = asset.pixel_height
    print(width, height)
    with objc_util.autoreleasepool():
      req = VNDetectRectanglesRequest.alloc().init().autorelease()
      req.maximumObservations = 0
      req.minimumAspectRatio = 0
      req.maximumAspectRatio = 1
      req.minimumSize = 0.08
      req.quadratureTolerance = 45.0
      req.minimumConfidence = 0
      if aoi:
        x, y, w, h = aoi
        req.regionOfInterest = ((x, y), (w, h))
      handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
      success = handler.performRequests_error_([req], None)    
      if success:
          rect_boxes = []
          bounding_boxes = []
          print(f'no boxes {len(req.results())}')
          
          for result in req.results():
            # bounding box is bigger than rectangle box
            rect_box = result #.VNRectangleObservation()
            bl = rect_box.bottomLeft()
            br = rect_box.bottomRight()
            tl = rect_box.topLeft()
            tr = rect_box.topRight()  
                      
            cg_box = result.boundingBox()
            x, y = cg_box.origin.x, cg_box.origin.y
            w, h = cg_box.size.width, cg_box.size.height
            if DEBUG:
                print([f'{p.x:.3f}, {p.y:.3f}' for p in [bl, br, tr, tl]])
                print('w,h=', w,h)
            #bounding_boxes.append(((x,y), (x+w,y), (x+w, y+h), (x, y+h), (x,y)))
            #rect_boxes.append(((bl.x, bl.y), (br.x, br.y), (tr.x, tr.y), (tl.x, tl.y), (bl.x, bl.y)))
            bounding_boxes.append((x, y, w, h))
            rect_boxes.append((bl.x, bl.y, tr.x - bl.x, tr.y-bl.y))
          return rect_boxes , bounding_boxes
    
def text_ocr(asset, aoi=None):
  """Image recognition of text
  works best with full words or numbers
  individual letters not so great
  VNDetectTextRectanglesRequest.regionOfInterest
  """
  
  img_data = objc_util.ns(asset.get_image_data().getvalue()) 
  with objc_util.autoreleasepool():
    req = VNRecognizeTextRequest.alloc().init().autorelease()
    req.setRecognitionLanguages_(['en-US'])
    req.setRecognitionLevel_(0) # accurate
    if aoi:
      x, y, w, h = aoi
      req.regionOfInterest = ((x, y), (w, h))
    
    # req.reportCharacterBoxes = True
    # req.setCustomWords_([x for x in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ01')]) # individual letters
    handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
    success = handler.performRequests_error_([req], None)    
    if success:
        all_text = {}
        for result in req.results():
          cg_box = result.boundingBox()
          x, y = cg_box.origin.x, cg_box.origin.y
          w, h = cg_box.size.width, cg_box.size.height
          all_text[x, y, w, h] = str(result.text())
        
        results =  [result.text() for result in req.results()]
         
        return all_text #[str(result.text()) for result in req.results()]       

def pieceword_sort(asset, page_text_dict, rectangles):
    """ from a series of rectangles, perform a text recognition inside each"""
    def r2(x):
        """ round"""
        return round(x, 3)
    all_dict ={}   
    for index, text_rect in enumerate(rectangles):
       
       #try to split rectangles into 9
       w = (text_rect[2][0] - text_rect[0][0])
       h = (text_rect[2][1] - text_rect[0][1])
       x, y = text_rect[0]
       #for i in range(9):
          #box = ((x + (i % 3) * w, y + 2*h - (i//3) * h), (w,h))
       aoi = ((x, y), (w, h))
       all_text_dict = text_ocr(asset, aoi=aoi)
       if DEBUG:
             print(f'{index} {x:.2f}, {y:.2f}, {list(all_text_dict.values())}')
       b, bs = sort_by_position(all_text_dict, max_y=3)
       all_dict.update({(r2(x),r2(y),r2(w),r2(h)): b})
       
    board, shape = sort_by_position(all_dict, max_y=-3)
    return   '\n'.join([''.join(row) for row in board])
    
def sort_by_position(all_text_dict, max_y=None):
    # use the box data to reorder text
    # attempts to reconstruct crossword letters
    
    if not all_text_dict:
      return None, None
    try:  
        #attempt to put dictionary into regular grid
        # all_text_dict has form (x, y, w, h): text
        #x, y, w, h are scaled 0-1.0        
        df = pd.DataFrame(np.array(list(all_text_dict.keys())), columns=('x', 'y', 'w', 'h'))
        
        if max_y is None:
            # scale 0-1000 and round to nearest 5
            df = df.multiply(1000).astype(int)    
            df = df.divide(5.0).round().multiply(5).astype(int)
            # TODO convert x and y to row and col
            p = np.polyfit(np.arange(df.shape[0]), np.sort(df['y']),1)
            ys = np.sort(df['y'])
            #spacing = np.sort(np.abs(np.diff(ys)))
            unique = np.unique(df['y'])
            #spacing_mean = np.mean(spacing)
            # scale to spacing
            if DEBUG:
                print(df.to_string(), p)
            df = df.subtract(p[1]).divide(p[0]).astype(int)
        elif max_y>0:           
           df = np.rint(df.multiply(max_y)).astype(int)
        elif max_y < 0:
           df = np.rint(df.divide(np.max(df['h']))).astype(int)
           if DEBUG:
                print(df.to_string())
           
        #stitch text as new column
        text_df = pd.DataFrame(np.array(list(all_text_dict.values())), columns =['text'])
        df = df.join(text_df) 
          
        #sort by y then x
        sorted_df = df.sort_values(by=['y', 'x'], ascending=[False, True])
        if DEBUG:
            # print all of the dataframe
            print(sorted_df.to_string())
        if max_y is not None and max_y < 0:
            board = np.empty((-max_y*(df['y'].max()+1), -max_y*(df['x'].max()+1)), dtype='U1')
            board[:, :] = '#'
            
            for _, row in sorted_df.iterrows():
              if row['text'] is not None:
                board[-max_y*row['y']: -max_y*row['y']+row['text'].shape[0], -max_y*row['x']: -max_y*row['x']+row['text'].shape[1]] = np.flipud(row['text'])
        else: 
            # prepare board
            board = np.empty((df['y'].max()+1, df['x'].max()+1), dtype='U1')
            board[:, :] = '#'
    
            #attempt to fill board given by row and col
        
            for _, row in sorted_df.iterrows():
                board[row['y'], row['x']: row['x']+len(row['text'])] = list(row['text'])
    
        # turn upside down
        board = np.flipud(board)
        if True:
            print()
            # print it
            [print(''.join(row)) for row in board]
           
        return board, board.shape
    except (Exception) as e:
        print(traceback.format_exc())
        return None, None













