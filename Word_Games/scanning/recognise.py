# text and rectangles recognition
import objc_util
from objc_util import ObjCClass, nsurl, ns, autoreleasepool
import numpy as np
from PIL import Image
from io import BytesIO
import traceback
import os
import pandas as pd
from matplotlib import pyplot
import straighten_image
import clipboard
import appex
from PIL.ExifTags import TAGS

DEBUG=False

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
		                print([f'{p.x:.3f}, {p.y:.3f}' for p in [bl, br, tr, tl]])
		                print('w,h=', w,h)
		            #bounding_boxes.append(((x,y), (x+w,y), (x+w, y+h), (x, y+h), (x,y)))
		            #rect_boxes.append(((bl.x, bl.y), (br.x, br.y), (tr.x, tr.y), (tl.x, tl.y), (bl.x, bl.y)))
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
		
		
		def load_model(self):
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
		
		
		def _classify_img_data(self, img_data):
			'''The main image classification method, used by `classify_image` (for camera images) and `classify_asset` (for photo library assets).'''
			vn_model = load_model()
			# Create and perform the recognition request:
			req = VNCoreMLRequest.alloc().initWithModel_(vn_model).autorelease()
			handler = VNImageRequestHandler.alloc().initWithData_options_(img_data, None).autorelease()
			success = handler.performRequests_error_([req], None)
			if success:
				best_result = req.results()[0]
				label = str(best_result.identifier())
				confidence = best_result.confidence()
				return {'label': label, 'confidence': confidence}
			else:
				return None
		
		
		def classify_image(self, img):
			buffer = io.BytesIO()
			img.save(buffer, 'JPEG')
			img_data = ns(buffer.getvalue())
			return self._classify_img_data(img_data)
		
		
		def classify_asset(self, asset):
			img_data = ns(asset.get_image_data().getvalue())
			return self._classify_img_data(img_data)
		
		
		def scale_image(self, img, max_dim):
			'''Helper function to downscale an image for showing in the console'''
			scale = max_dim / max(img.size)
			w = int(img.size[0] * scale)
			h = int(img.size[1] * scale)
			return img.resize((w, h), Image.ANTIALIAS)
		
		def corel_ml_text_recognition(self, asset, roi):	
				result = self.classify_asset(asset, roi)
				asset.get_ui_image((255, 255)).show()
				if result:
					print(result)
				else:
					print('Image classification failed')
				
		def pieceword_sort(self, asset, page_text_dict, rectangles):
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
		       b, bs = self.sort_by_position(all_text_dict, max_y=3)
		       all_dict.update({(r2(x),r2(y),r2(w),r2(h)): b})
		       
		    board, shape = self.sort_by_position(all_dict, max_y=-3)
		    return   '\n'.join([''.join(row) for row in board])
		    
		def sort_by_position(self, all_text_dict, max_y=None):
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
		
		
		import math
		    
		    
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
		          








