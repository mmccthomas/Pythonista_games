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

def convert_to_png(asset):
    
    img = Image.open(asset.get_image_data())    
    img.save('temp.png', format="png")   
    # Write PIL Image to in-memory PNG
    #membuf = BytesIO()
    #img.save(membuf, format="png")  
    #return membuf.getvalue()
    

def rectangles(asset):
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
      req.minimumSize = 0.015
      req.quadratureTolerance = 45.0
      req.minimumConfidence = 0
      
      handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
      success = handler.performRequests_error_([req], None)    
      if success:
          boxes = []
          boxes2 = []
          print(f'no boxes {len(req.results())}')
          
          for result in req.results():
            rect_box = result #result.VNRectangleObservation()
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
            boxes2.append(((x,y), (x+w,y), (x+w, y+h), (x, y+h), (x,y)))
            boxes.append((bl, br, tr, tl, bl))
            
          return boxes , boxes2    
    
def text_ocr(asset, aoi=None):
  """Image recognition of text
  works best with full words or numbers
  individual letters not so great
  VNDetectTextRectanglesRequest.regionOfInterest
  """
  
  img_data = objc_util.ns(asset.get_image_data().getvalue()) 
  with objc_util.autoreleasepool():
    req = VNRecognizeTextRequest.alloc().init().autorelease()
    req.setRecognitionLanguages_(['zh-Hant', 'en-US'])
    req.setRecognitionLevel_(0) # accurate
    if aoi:
      bl, br, tr, tl, _ = aoi
      req.regionOfInterest = (bl, tr)
    req.setCustomWords_([x for x in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')]) # individual letters
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
        
def sort_by_position(all_text_dict):
    # use the box data to reorder text
    # attempts to reconstruct crossword letters
    
    if not all_text_dict:
      return None, None
    try:  
        #attempt to put dictionary into regular grid
        # all_text_dict has form (x, y, w, h): text
        #x, y, w, h are scaled 0-1.0        
        df = pd.DataFrame(np.array(list(all_text_dict.keys())), columns=('x', 'y', 'w', 'h'))
        # scale 0-1000 and round to nearest 5
        df = df.multiply(1000).astype(int)    
        df = df.divide(5.0).round().multiply(5).astype(int)
        # find  spacing of rows
        df_diff = df.diff()
        df_med = df_diff.median()['y']
        # scale to spacing
        df = df.divide(-df_med).round().astype(int)
        
        #stitch text as new column
        text_df = pd.DataFrame(np.array(list(all_text_dict.values())), columns =['text'])
        df = df.join(text_df) 
          
        #sort by y then x
        sorted_df = df.sort_values(by=['y', 'x'], ascending=[False, True])
        if DEBUG:
            # print all of the dataframe
            print(sorted_df.to_string())
        
        # prepare board
        board = np.empty((df['y'].max()+1, df['x'].max()+1), dtype='U1')
        board[:, :] = ' '
    
        #attempt to fill board given by row and col
    
        for _, row in sorted_df.iterrows():
            board[row['y'], row['x']: row['x']+len(row['text'])] = list(row['text'])
    
        # turn upside down
        board = np.flipud(board)
        if DEBUG:
            # print it
            [print(''.join(row)) for row in board]
        return board, board.shape
    except (Exception) as e:
        print(traceback.format_exc())
        return None, None

