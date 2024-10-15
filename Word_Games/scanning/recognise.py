# text and rectangles recognition
# contains Vision class rectanges and text, and CoreML function
import objc_util
from objc_util import ObjCClass, nsurl, ns, autoreleasepool
import numpy as np
from PIL import Image
import traceback
import os
import io
from time import time
import pandas as pd
from matplotlib import pyplot as plt
import straighten_image
import appex
import math
import requests
from PIL.ExifTags import TAGS
import dialogs
import photos
import resource

DEBUG = False

VNImageRequestHandler = ObjCClass('VNImageRequestHandler')
VNRecognizeTextRequest = ObjCClass('VNRecognizeTextRequest')
VNDetectRectanglesRequest = ObjCClass('VNDetectRectanglesRequest')
VNRectangleObservation = ObjCClass('VNRectangleObservation')
MLModel = ObjCClass('MLModel')
VNCoreMLModel = ObjCClass('VNCoreMLModel')
VNCoreMLRequest = ObjCClass('VNCoreMLRequest')


# Configuration (change URL and filename if you want to use a different model):
MODEL_URL = 'https://docs-assets.developer.apple.com/coreml/models/MobileNet.mlmodel'

MODEL_FILENAME = 'Alphanum_28x28.mlmodel'
# Use a local path for caching the model file (no need to sync this with iCloud):
MODEL_PATH = './' + MODEL_FILENAME

exif_rotations = {
1: '0 degrees: the correct orientation, no adjustment is required.',
2: '0 degrees, mirrored: image has been flipped back-to-front.',
3: '180 degrees: image is upside down.',
4: '180 degrees, mirrored: image has been flipped back-to-front and is upside down.',
5: '90 degrees: image has been flipped back-to-front and is on its side.',
6: '90 degrees, mirrored: image is on its side.',
7: '270 degrees: image has been flipped back-to-front and is on its far side.'
}

  
class Recognise():
    def __init__(self, gui):
      self.w =0
      self.h = 0
      self.asset = None
      self.gui = gui
      
    @staticmethod 
    def memused():
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss// (2**20) 
        
    def get_exif(self, i):
      ret = {}
      # i = Image.open(fn)
      info = i._getexif()
      for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        ret[decoded] = value
      return ret
        
    def convert_to_png(self, asset):
        """ convert and  make smaller
        get rotation from exif data """
        filename = 'temp.png'
        img = Image.open(asset.get_image_data()) 
        exif = self.get_exif(img)
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
        
    def scan_xword(self, image_name, crossword_file):                
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
        
    def rectangles(self, asset, aoi=None):
        """Image recognition of rectangles
        to use as subframes
        """
        img_data = ns(asset.get_image_data().getvalue()) 
        #img_data = straighten_image.straighten(convert_to_png(asset))
        width = asset.pixel_width
        height = asset.pixel_height
        # print(width, height)
        with autoreleasepool():
          req = VNDetectRectanglesRequest.alloc().init().autorelease()
          req.minimumSize = 0.08 
          req.maximumObservations = 0
          req.minimumAspectRatio = 0
          req.maximumAspectRatio = 1
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
              #print(f'no boxes {len(req.results())}')
              
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
                    print(f'{x:.3f}, {y:.3f}')
                    print('w,h=', w,h)

                bounding_boxes.append((x, y, w, h))
                rect_boxes.append((bl.x, bl.y, tr.x - bl.x, tr.y-bl.y))
              return rect_boxes , bounding_boxes
        
    def text_ocr(self, asset, aoi=None):
      """Image recognition of text
      works best with full words or numbers
      individual letters not so great
      VNDetectTextRectanglesRequest.regionOfInterest
      """      
      img_data = objc_util.ns(asset.get_image_data().getvalue()) 
      with autoreleasepool():
        req = VNRecognizeTextRequest.alloc().init().autorelease()
        req.setRecognitionLanguages_(['en-US'])
        req.setRecognitionLevel_(0) # accurate
        if aoi:
          x, y, w, h = aoi
          req.regionOfInterest = ((x, y), (w, h))        
        req.reportCharacterBoxes = True
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
            return all_text         
    
    def load_model(self, modelname):
      '''Helper method for downloading/caching the mlmodel file'''
      if not os.path.exists(MODEL_PATH):
        print(f'Downloading model: {MODEL_FILENAME}...')
        r = requests.get(MODEL_URL, stream=True)
        file_size = int(r.headers['content-length'])
        with open(MODEL_PATH, 'wb') as f:
          bytes_written = 0
          for chunk in r.iter_content(1024*100):
            f.write(chunk)
            print(f'{bytes_written/file_size*100:.2f}% downloaded')
            bytes_written += len(chunk)
        print('Download finished')
      ml_model_url = nsurl(MODEL_PATH)
      # Compile the model:
      c_model_url = MLModel.compileModelAtURL_error_(ml_model_url, None)
      # Load model from the compiled model file:
      ml_model = MLModel.modelWithContentsOfURL_error_(c_model_url, None)
      # Create a VNCoreMLModel from the MLModel for use with the Vision framework:
      vn_model = VNCoreMLModel.modelForMLModel_error_(ml_model, None)
      return vn_model
    
    
    def _classify_img_data(self, modelname, img_data, aoi):
      '''The main image classification method, used by `classify_image` (for camera images) and `classify_asset` (for photo library assets).'''
      if not hasattr(self, 'vnmodel'):
          self.vn_model = self.load_model(modelname)
      
      # Create and perform the recognition request:
      with autoreleasepool():
          req = VNCoreMLRequest.alloc().initWithModel_(self.vn_model).autorelease()
          if aoi:
              x, y, w, h = aoi
              req.regionOfInterest = ((x, y), (w, h))
          handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
          success = handler.performRequests_error_([req], None)
          
          if success:
            best_result = req.results()[0]
            label = str(best_result.identifier())
            confidence = best_result.confidence()
            return {'label': label, 'confidence': confidence, 'cg_box': aoi}
          else:
            return None    
    
    def classify_image(self, img, aoi):
      buffer = io.BytesIO()
      img.save(buffer, 'JPEG')
      img_data = ns(buffer.getvalue())
      return self._classify_img_data(img_data, aoi)
    
    def character_ocr(self, asset, aoi):
      """ read a single 28 x 28 pixel character
      scale the image so that aoi size is 28 x 28 pixels
      """
      if aoi is None:
          x, y, w, h = 0.0, 0.0, 1.0, 1.0 
      else:
          x, y, w, h = aoi   
      if asset is not self.asset or not math.isclose(w, self.w, abs_tol=0.005) or not math.isclose(h, self.h, abs_tol=0.005):
        MAX_SIZE = 28
        img = asset.get_image().convert('1')
        width = asset.pixel_width
        height = asset.pixel_height                 
        sq_x, sq_y = (w * width, h * height)
        ratio_x, ratio_y = MAX_SIZE / sq_x, MAX_SIZE / sq_y
        img.resize((int(width * ratio_x), int(width * ratio_y)), Image.ANTIALIAS)
        buffer = io.BytesIO()
        img.save(buffer, 'JPEG')      
        img_data = ns(buffer.getvalue()) 
        self.w, self.h, self.asset = w, h, asset
        self.img_data = img_data     
      
      return self._classify_img_data('Alphanum_28x28.mlmodel', self.img_data, aoi)    
    
    def scale_image(self, img, max_dim):
      '''Helper function to downscale an image for showing in the console'''
      scale = max_dim / max(img.size)
      w = int(img.size[0] * scale)
      h = int(img.size[1] * scale)
      return img.resize((w, h), Image.ANTIALIAS)
    
    def draw_box(self,rect_, **kwargs):
          W, H = self.gui.gs.DIMENSION_X, self.gui.gs.DIMENSION_Y
          x, y, w, h = rect_
          x1, y1 = x+w, y+h                 
          box = [self.gui.gs.rc_to_pos(H-y*H-1, x*W), 
                 self.gui.gs.rc_to_pos(H-y1*H-1, x*W), 
                 self.gui.gs.rc_to_pos(H-y1*H-1, x1*W), 
                 self.gui.gs.rc_to_pos(H-y*H-1, x1*W), 
                 self.gui.gs.rc_to_pos(H-y*H-1, x*W)]                                                  
          self.gui.draw_line(box, **kwargs)      
        
    def pieceword_sort(self, asset, page_text_dict, rectangles):
        """ from a series of rectangles, perform a text recognition inside each"""
     
        def get_chars(rectangles):
            params = {'line_width': 5, 'stroke_color': 'red', 'z_position':1000}
            all_dict = []   
            self.gui.remove_lines()    
            for index, text_rect in rectangles.iterrows():      
                try:     
                    box  = tuple(text_rect)                  
                    char_ =  self.character_ocr(asset, aoi=box)                    
                    
                    self.draw_box(box, **{**params,'stroke_color': 'green'})
                    self.gui.set_message(f'{index} {box[0]:.2f}, {box[1]:.2f}, {char_["label"]}  {char_["confidence"]:.2f}')
                    all_dict.append(char_)
                    if DEBUG:
                        print(f'{index} {box[0]:.2f}, {box[1]:.2f}, {char_["label"]}  {char_["confidence"]:.2f}')                    
                except (Exception) as e:
                   print(e)
            self.gui.remove_lines()    
            return all_dict             
             
        all_dict = get_chars(rectangles)  
        return all_dict
        
    def sort_by_position(self, all_text_dict, max_y=None):
        # use the box data to reorder text
        # attempts to reconstruct crossword letters
        
        if not all_text_dict:
          return None, None
        try:  
            #attempt to put dictionary into regular grid
            # all_text_dict has form (x, y, w, h): text
            #x, y, w, h are scaled 0-1.0        
            df = pd.DataFrame([t['cg_box'] for t in all_text_dict], columns=('x', 'y', 'w', 'h'))
            df = np.round(df, 2)
            df['text'] = [t['label'] for t in all_text_dict]
            df['conf'] = [round(t['confidence'], 2) for t in all_text_dict]
            df['area']= df.w * df.h * 1000
            df.sort_values(by=['x','y','area'], inplace=True, ignore_index=True)
            df.drop_duplicates(['x', 'y'], keep='last', inplace=True, ignore_index=True)
            df = self.convert_to_rc(df)
            data = np.array(df[['x','y']])
            x, y = data.T
            #plt.scatter(x,y, color='red' )          
            #plt.show()
            board = np.full((self.Ny, self.Nx), ' ', dtype='U1')
            for index, selection in df.iterrows():
                 if selection['conf']> 0.3:
                      board[int(selection["r"]), int(selection["c"])] = selection['text']
                 else:
                      board[int(selection["r"]), int(selection["c"])] = '#'
            return board, board.shape
            
        except (Exception) as e:
            print(traceback.format_exc())
            return None, None            
            
    def convert_to_rc(self, df):
       '''add r, c columns to  a dataframe with x y values'''
       def process(column, ratio=None):
           """calculate size of axis, then values and hence delta           
           ratio = 0.5 # fraction of counts to accept
           """           
           values = np.array(df[column])
           u, count = np.unique(values, return_counts=True)
           
           avg_ = np.mean(count)
           
           if ratio is None:
              stdev_ = np.std(count)
              ratio = 1 - stdev_ / avg_
              
           #plt.stem(u, count, linefmt='red') 
           if ratio < 1.0:  
               filtered = u[count >= avg_ * ratio]
               filt_count = count[count >= avg_ * ratio]               
               #plt.stem(filtered, filt_count, linefmt='blue')    
           else:
              filtered = u
                           
           #plt.show()
           N = len(filtered)            
           diff_ = np.mean(np.diff(filtered))
           return N, diff_, filtered
         
       print('x red=original, blue = filtered') 
       self.Nx, diffx, self.xs = process('x', ratio=None)
       print('y red=original, blue = filtered') 
       self.Ny, diffy, self.ys = process('y', ratio=None)
       print(f'{self.Nx=}, {diffx=:.3f}, {self.xs=}')
       print(f'{self.Ny=}, {diffy=}:.3f, {self.ys=}')
       # TODO does not account for non uniform spacing
       # better to index u values?
       c = np.digitize(df.x, self.xs, right=True)
       r = np.digitize(df.y, self.ys, right=True)
       df['c'] = c #np.rint((df.x - min(self.xs)) / diffx).astype(int)
       df['r'] = r #np.rint((df.y - min(self.ys)) / diffy).astype(int)
       
       return df
           
    def hough_line(self,img, angle_step=1, lines_are_white=True, value_threshold=5):
            """
            Hough transform for lines
        
            Input:
            img - 2D binary image with nonzeros representing edges
            angle_step - Spacing between angles to use every n-th angle
                         between -90 and 90 degrees. Default step is 1.
            lines_are_white - boolean indicating whether lines to be detected are white
            value_threshold - Pixel values above or below the value_threshold are edges
        
            Returns:
            accumulator - 2D array of the hough transform accumulator
            theta - array of angles used in computation, in radians.
            rhos - array of rho values. Max size is 2 times the diagonal
                   distance of the input image.
            """
            # Rho and Theta ranges
            thetas = np.deg2rad(np.arange(-90.0, 90.0, angle_step))
            width, height = img.shape
            diag_len = int(round(math.sqrt(width * width + height * height)))
            rhos = np.linspace(-diag_len, diag_len, diag_len * 2)
        
            # Cache some reusable values
            cos_t = np.cos(thetas)
            sin_t = np.sin(thetas)
            num_thetas = len(thetas)
        
            # Hough accumulator array of theta vs rho
            accumulator = np.zeros((2 * diag_len, num_thetas), dtype=np.uint8)
        
            # indices of none zero (row, col)
            are_edges = img > value_threshold if lines_are_white else img < value_threshold
            y_idxs, x_idxs = np.nonzero(are_edges)
        
            # Vote in the hough accumulator
            for i in range(len(x_idxs)):
                x = x_idxs[i]
                y = y_idxs[i]
        
                for t_idx in range(num_thetas):
                    # Calculate rho. diag_len is added for a positive index
                    rho = diag_len + int(round(x * cos_t[t_idx] + y * sin_t[t_idx]))
                    accumulator[rho, t_idx] += 1
        
            return accumulator, thetas, rhos        
        
    def show_hough_line(self,img, accumulator, thetas, rhos, save_path=None):
            import matplotlib.pyplot as plt
        
            fig, ax = plt.subplots(1, 2, figsize=(10, 10))
        
            ax[0].imshow(img, cmap=plt.cm.gray)
            ax[0].set_title('Input image')
            ax[0].axis('image')
        
            ax[1].imshow(
                accumulator, cmap='jet',
                extent=[np.rad2deg(thetas[-1]), np.rad2deg(thetas[0]), rhos[-1], rhos[0]])
            ax[1].set_aspect('equal', adjustable='box')
            ax[1].set_title('Hough transform')
            ax[1].set_xlabel('Angles (degrees)')
            ax[1].set_ylabel('Distance (pixels)')
            ax[1].axis('image')
        
            # plt.axis('off')
            if save_path is not None:
                plt.savefig(save_path, bbox_inches='tight')
            plt.show()                      
            
            accumulator, thetas, rhos = self.hough_line(img)
            self. gshow_hough_line(img, accumulator, thetas, rhos, save_path='imgs/output.png')
    
    def threshold_otsu(self, x, *args, **kwargs):
          """Find the threshold value for a bimodal histogram using the Otsu method.
      
          If you have a distribution that is bimodal (AKA with two peaks, with a valley
          between them), then you can use this to find the location of that valley, that
          splits the distribution into two.
      
          From the SciKit Image threshold_otsu implementation:
          https://github.com/scikit-image/scikit-image/blob/70fa904eee9ef370c824427798302551df57afa1/skimage/filters/thresholding.py#L312
          """
          counts, bin_edges = np.histogram(x, *args, **kwargs)
          bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2
          # class probabilities for all possible thresholds
          weight1 = np.cumsum(counts)
          weight2 = np.cumsum(counts[::-1])[::-1]
          # class means for all possible thresholds
          mean1 = np.cumsum(counts * bin_centers) / weight1
          mean2 = (np.cumsum((counts * bin_centers)[::-1]) / weight2[::-1])[::-1]
      
          # Clip ends to align class 1 and class 2 variables:
          # The last value of ``weight1``/``mean1`` should pair with zero values in
          # ``weight2``/``mean2``, which do not exist.
          variance12 = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
      
          idx = np.argmax(variance12)
          threshold = bin_centers[idx]
          return threshold
              
def main():
  g = Recognise(None)
  r = dialogs.alert('Classify Image', '', 'Camera', 'Photo Library')
  if r == 1:
    img = photos.capture_image()
    if img is None:
      return
    g.scale_image(img, 224).show()
    result = classify_image(img)
  else:
    asset = photos.pick_asset()
    if asset is None:
      return
    result = g.corel_ml_text_recognition(asset, aoi=None)
    asset.get_ui_image((255, 255)).show()
  if result:
    print(result)
  else:
    print('Image classification failed')
                            
if __name__ == '__main__':
  main()
