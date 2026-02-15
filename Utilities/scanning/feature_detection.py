# detection of circles, lines and arcs in an image
import numpy as np
from PIL import Image, ImageDraw, ImageColor
import os
import math
from operator import attrgetter
# from time import time
import console
import cProfile
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from itertools import cycle
import logging


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s %(message)s',
    datefmt='%H:%M:%S'  # This removes the year, month, and day
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set root logger level to DEBUG


def get_distance(p1, p2):
    """Calculates Euclidean distance: sqrt((x2-x1)^2 + (y2-y1)^2)"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

                
def is_debug_level():
    return logging.getLevelName(logger.getEffectiveLevel()) == 'DEBUG'


def test_plot(coords):
    plt.plot(coords[:, 0], coords[:, 1],
             color='red',
             linewidth=3)
    plt.axis('equal')
    plt.show()

        
class Shape():
    # container for generic shape
    def __init__(self, centroid, circularity, coordinates, perimeter):
         
       self.centroid = (int(centroid[0]), int(centroid[1]))
       self.perimeter = int(perimeter)
       self.circularity = round(circularity, 3)
       self.is_circle = 0.7 < circularity < 1.3  # Threshold for "roundness"
       self.coordinates = coordinates
       self.no_points = len(coordinates)
       self.image = None
       self.description = ''
       self.quadrant = ''
       self.image_size = (0, 0)
       self.color_names = ''
       self.shape = 'shape'
       if self.is_circle:
           self.shape = 'circle'
       if self.circularity == 10:
           self.shape = 'rounded rectangle'
       if self.circularity == -10:
           self.shape = 'rectangle'
                
    def __repr__(self):
        return (f'{self.quadrant.capitalize()} {self.color_names} '
                f'{self.shape.capitalize()}@{self.centroid} ({self.no_points}points)')

                                
class FeatureExtract():
    """ returns self.img_array, self.edges"""
    def __init__(self, image_path, output_dir='output',
                 canny_low=0.05, canny_high=0.15):
                      
        self.image_path = image_path
        self.output_dir = output_dir
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.find_edges()
        
    def find_edges(self):
        self.img_array = self.load_image()
        
        # Convert to grayscale
        logger.debug("Converting to grayscale...")
        gray = self.rgb_to_grayscale(self.img_array)
        
        # Edge detection
        logger.debug("Performing edge detection...")
        self.edges = self.canny_edge_detection(gray, self.canny_low, self.canny_high)
        
    def load_image(self):
        logger.debug(f"Loading image: {self.image_path}")
        
        # Load image
        self.img = Image.open(self.image_path)
        img_array = np.array(self.img)
      
        img_array = img_array[:, :, :3]  # remove alpha
        
        logger.debug(f"Image shape: {img_array.shape}")
        return img_array
        
    def rgb_to_grayscale(self, img):
        """Convert RGB image to grayscale."""
        if len(img.shape) == 2:
            return img
        return np.dot(img[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
    
    def gaussian_kernel(self, size, sigma):
        center = size // 2
        # Generate open grids (1xN and Nx1)
        y, x = np.ogrid[-center: size - center, -center: size - center]
        
        # Compute the 2D Gaussian using broadcasting
        kernel = np.exp(-(x**2 + y**2) / (2 * sigma**2))
        
        return kernel / kernel.sum()

    def convolve2d(self, image, kernel):
        h, w = image.shape
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        
        # Pad the image to handle edges
        padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='edge')
        
        # Create a sliding window view of the image
        # This creates a 4D array of shape (h, w, kh, kw)
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(padded, (kh, kw))
        
        # Element-wise multiply windows by kernel and sum over the last two axes
        # This replaces the nested for-loops entirely
        output = np.sum(windows * kernel, axis=(2, 3))
        
        return output.astype(np.float32)
        
    def gaussian_blur(self, image, kernel_size=5, sigma=1.0):
        """Apply Gaussian blur to image."""
        kernel = self.gaussian_kernel(kernel_size, sigma)
        return self.convolve2d(image, kernel)
        
    def sobel_filters(self, image):
        """Apply Sobel filters to get gradients."""
        # Sobel kernels
        Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
        
        Gx = self.convolve2d(image, Kx)
        Gy = self.convolve2d(image, Ky)
        
        # Gradient magnitude and direction
        G = np.sqrt(Gx**2 + Gy**2)
        theta = np.arctan2(Gy, Gx)
        
        return G, theta
    
    def non_maximum_suppression(self, gradient, theta):
        h, w = gradient.shape
        suppressed = np.zeros_like(gradient)
        
        # Convert angle to degrees and wrap to [0, 180]
        angle = theta * 180.0 / np.pi
        angle[angle < 0] += 180
        
        # Initialize neighbor comparison arrays
        q = np.zeros_like(gradient)
        r = np.zeros_like(gradient)
        
        # Define masks for the four primary directions
        # 0 degrees (Horizontal)
        mask0 = ((0 <= angle) & (angle < 22.5)) | ((157.5 <= angle) & (angle <= 180))
        # 45 degrees (Diagonal /)
        mask45 = (22.5 <= angle) & (angle < 67.5)
        # 90 degrees (Vertical)
        mask90 = (67.5 <= angle) & (angle < 112.5)
        # 135 degrees (Diagonal \)
        mask135 = (112.5 <= angle) & (angle < 157.5)
    
        # Use slicing to shift the image and find neighbors for all pixels at once
        # We ignore the 1-pixel border to match your original loop (1 to h-1)
        
        # Angle 0: Neighbors are Left and Right
        q[1:-1, 1:-1][mask0[1:-1, 1:-1]] = gradient[1:-1, 2:][mask0[1:-1, 1:-1]]
        r[1:-1, 1:-1][mask0[1:-1, 1:-1]] = gradient[1:-1, :-2][mask0[1:-1, 1:-1]]
    
        # Angle 45: Neighbors are Bottom-Left and Top-Right
        q[1:-1, 1:-1][mask45[1:-1, 1:-1]] = gradient[2:, :-2][mask45[1:-1, 1:-1]]
        r[1:-1, 1:-1][mask45[1:-1, 1:-1]] = gradient[:-2, 2:][mask45[1:-1, 1:-1]]
    
        # Angle 90: Neighbors are Top and Bottom
        q[1:-1, 1:-1][mask90[1:-1, 1:-1]] = gradient[2:, 1:-1][mask90[1:-1, 1:-1]]
        r[1:-1, 1:-1][mask90[1:-1, 1:-1]] = gradient[:-2, 1:-1][mask90[1:-1, 1:-1]]
    
        # Angle 135: Neighbors are Top-Left and Bottom-Right
        q[1:-1, 1:-1][mask135[1:-1, 1:-1]] = gradient[:-2, :-2][mask135[1:-1, 1:-1]]
        r[1:-1, 1:-1][mask135[1:-1, 1:-1]] = gradient[2:, 2:][mask135[1:-1, 1:-1]]
    
        # Suppress pixels that are not local maxima
        keep_mask = (gradient >= q) & (gradient >= r)
        suppressed[keep_mask] = gradient[keep_mask]
        return suppressed
    
    def double_threshold(self, image, low_threshold_ratio=0.05, high_threshold_ratio=0.15):
        """Apply double threshold to classify edges."""
        high_threshold = image.max() * high_threshold_ratio
        low_threshold = high_threshold * low_threshold_ratio
        
        strong = 255
        weak = 50
        
        result = np.zeros_like(image)
        
        strong_i, strong_j = np.where(image >= high_threshold)
        weak_i, weak_j = np.where((image <= high_threshold) & (image >= low_threshold))
        
        result[strong_i, strong_j] = strong
        result[weak_i, weak_j] = weak
        
        return result, weak, strong
    
    def edge_tracking(self, image, weak=50, strong=255):
        # Create masks
        strong_mask = (image == strong)
        weak_mask = (image == weak)
        
        # We will "grow" the strong mask into the weak mask
        # Current state of confirmed edges
        confirmed = strong_mask.copy()
        
        while True:
            # 1. Find all neighbors of currently confirmed strong pixels
            # We shift the image in all 8 directions to simulate the 3x3 window
            neighbors = np.zeros_like(confirmed)
            
            # Directions: Up, Down, Left, Right, and 4 Diagonals
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    # Roll performs a cyclic shift (efficient for neighbor lookup)
                    shifted = np.roll(confirmed, shift=(dx, dy), axis=(0, 1))
                    neighbors |= shifted
            
            # 2. A weak pixel becomes confirmed if it touches a confirmed neighbor
            new_confirmations = weak_mask & neighbors & ~confirmed
            
            # 3. If no new pixels were converted, we are done
            if not np.any(new_confirmations):
                break
                
            # 4. Add new pixels to the confirmed set and repeat
            confirmed |= new_confirmations
    
        # Map back to original values
        result = np.zeros_like(image)
        result[confirmed] = strong
        return result
    
    def canny_edge_detection(self, image, low_threshold=0.05, high_threshold=0.15):
        """Perform Canny edge detection."""
        logger.debug("  Applying Gaussian blur...")
        blurred = self.gaussian_blur(image, kernel_size=5, sigma=1.4)
        
        logger.debug("  Computing gradients...")
        gradient, theta = self.sobel_filters(blurred)
        
        logger.debug("  Non-maximum suppression...")
        suppressed = self.non_maximum_suppression(gradient, theta)
        
        logger.debug("  Double threshold...")
        thresholded, weak, strong = self.double_threshold(suppressed, low_threshold, high_threshold)
        
        logger.debug("  Edge tracking...")
        edges = self.edge_tracking(thresholded, weak, strong)
        
        return edges

    def crop_image(self, points):
                        
        # Create a mask for the polygon region
        mask = Image.new('L', self.img.size, 0)
        boundary = [tuple(p) for p in points]
        ImageDraw.Draw(mask).polygon(boundary, outline=255, fill=255)
        
        # Method 2: Crop to bounding box of the polygon
        x_coords = points[:, 0]
        y_coords = points[:, 1]
        bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
        
        # Crop both image and mask
        cropped_img = self.img.crop(bbox)
        cropped_mask = mask.crop(bbox)
        
        # Apply mask to cropped image
        cropped_rgba = cropped_img.convert('RGBA')
        cropped_rgba_array = np.array(cropped_rgba)
        cropped_mask_array = np.array(cropped_mask)
        cropped_rgba_array[:, :, 3] = cropped_mask_array
        
        result_cropped = Image.fromarray(cropped_rgba_array)
        
        # logger.debug(f"Cropped image size: {result_cropped.size}")
        return result_cropped

    def get_dominant_colors(self, image, k=3, iterations=10):
        """ AI generated """
        # Load image and resize for performance
        img = image.resize((100, 100))
        img_array = np.array(img)[:, :, :3]  # remove alpha
        pixels = img_array.reshape(-1, 3).astype(float)
        
        # K-Means Implementation
        # Initialize centroids randomly from the existing pixels
        centroids = pixels[np.random.choice(pixels.shape[0], k, replace=False)]
    
        for _ in range(iterations):
            # Calculate Euclidean distance between pixels and centroids
            # (N, 1, 3) - (1, k, 3) -> (N, k, 3) -> distance (N, k)
            distances = np.linalg.norm(pixels[:, np.newaxis] - centroids, axis=2)
            
            # Assign each pixel to the closest centroid
            labels = np.argmin(distances, axis=1)
            
            # Move centroids to the mean of their assigned pixels
            new_centroids = np.array([pixels[labels == i].mean(axis=0)
                                     if np.any(labels == i) else centroids[i]
                                     for i in range(k)])
            
            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids
    
        # Calculate percentages
        counts = np.bincount(labels, minlength=k)
        percentages = counts / len(pixels)
        
        # Sort by dominance
        indices = np.argsort(percentages)[::-1]
        return centroids[indices], percentages[indices]

    def closest_colors(self, image):
        """ find the closest colour names to the image
        use k-clustering to identify major colour areas
        """
        def hex_to_rgb(value):
            value = value.lstrip('#')
            return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

        def find_closest_colourname(rgb):
            # Find the name with the smallest Euclidean distance to the RGB value
            best_name = min(colordict.keys(),
               key=lambda name: np.linalg.norm(np.array(rgb) - np.array(hex_to_rgb(colordict[name]))))
            return best_name
            
        # colordict = mcolors.TABLEAU_COLORS  # a curated list of colors
        colordict = mcolors.CSS4_COLORS  # a curated list of colors
 
        top_colors, weights = self.get_dominant_colors(image, k=3)
        
        closest_name = []
        for i, (color, weight) in enumerate(zip(top_colors, weights)):
            name = find_closest_colourname(color)
            closest_name.append(name)
            # logger.debug(f"{i+1}. {name}: {weight*100:.1f}% (RGB: {color.astype(int)})")
        # filter black
        closest_name = [name for name in closest_name if name != 'black']
        return '/'.join(closest_name)

    def quadrant(self, coord):
        """returns quadrant of cood in image """
        w, h = self.img.size
        x, y = coord
        if x < 0.45 * w:
            x_quad = 'left'
        elif x > 0.55 * w:
            x_quad = 'right'
        else:
            x_quad = 'centre'
        
        if y < 0.45 * h:
            y_quad = 'top'
        elif y > 0.55 * h:
            y_quad = 'bottom'
        else:
            y_quad = 'centre'
        return y_quad, x_quad

                  
class LineDetector(FeatureExtract):
    """Extends FeatureExtract to add line detection capability."""
    def __init__(self, image_path=None, output_dir='output',
                 canny_low=0.05, canny_high=0.15, image_process=None):
       
       if image_process is None:
           super().__init__(image_path, output_dir,
                            canny_low, canny_high)
       else:
           self.edges = image_process.edges
           self.img_array = image_process.img_array
           self.output_dir = image_process.output_dir
            
    def extract_lines(self, min_line_length=50, max_line_gap=10, threshold=50):
        """
        Extract lines from an image using pure NumPy implementation.
        Parameters:
        -----------
        min_line_length : int
            Minimum line length
        max_line_gap : int
            Maximum gap to bridge between segments
        """
        logger.debug(f"Performing Hough Line Transform (threshold={threshold})...")
        lines = self.hough_line_transform(self.edges, threshold, min_line_length, max_line_gap)
        logger.debug(f"Detected {len(lines)} lines!")
        return lines
                     
    def hough_transform_vectorized(self, edge_points, thetas, rhos, rho_res):
        """
        Vectorized Hough Accumulator.
        edge_points: Nx2 array of (y, x) coordinates
        """
        h, w = self.edges.shape
        # Calculate diagonal length for max rho
        diag_len = int(np.sqrt(h**2 + w**2))
        # Precompute cos and sin values
        cos_thetas = np.cos(thetas)
        sin_thetas = np.sin(thetas)
        # 1. Extract y and x as column vectors (shape: N x 1)
        y = edge_points[:, 0][:, np.newaxis]
        x = edge_points[:, 1][:, np.newaxis]
        
        # 2. Calculate rho for ALL points and ALL thetas at once
        # x * cos_thetas results in (N x 1) * (1 x len(thetas)) -> (N x len(thetas))
        rhos_all = x * cos_thetas + y * sin_thetas
        
        # 3. Convert rho values to indices
        rho_indices = ((rhos_all + diag_len) / rho_res).astype(int)
        
        # 4. Create an empty accumulator
        accumulator = np.zeros((len(rhos), len(cos_thetas)), dtype=np.int32)
        
        # 5. Filter valid indices (those within the accumulator bounds)
        theta_indices = np.arange(len(cos_thetas))
        # Tile theta_indices to match the shape of rho_indices (N x len(thetas))
        theta_indices_grid = np.tile(theta_indices, (len(edge_points), 1))
        
        valid_mask = (rho_indices >= 0) & (rho_indices < len(rhos))
        
        # 6. Use np.add.at for unbuffered "voting"
        # This correctly handles multiple points voting for the same bin
        np.add.at(accumulator, (rho_indices[valid_mask], theta_indices_grid[valid_mask]), 1)
        
        return accumulator
    
    def extract_lines_vectorized(self, accumulator, rhos, thetas, line_indices):
        """
        Extracts line parameters and votes, then sorts them by strength.
        line_indices: tuple of (rho_idxs, theta_idxs) as returned by np.where or np.argwhere
        """
        # 1. Separate the indices
        rho_idxs, theta_idxs = line_indices[:, 0], line_indices[:, 1]
        
        # 2. Map indices to actual values using NumPy indexing
        # This replaces the loop and rhos[rho_idx] / thetas[theta_idx] calls
        rho_values = rhos[rho_idxs]
        theta_values = thetas[theta_idxs]
        votes = accumulator[rho_idxs, theta_idxs]
        
        # 3. Stack into a single Nx3 array: [rho, theta, votes]
        lines = np.column_stack((rho_values, theta_values, votes))
        
        # 4. Sort by votes (the 3rd column, index 2) in descending order
        # argsort returns indices that would sort the array; [::-1] reverses it
        sorted_indices = np.argsort(lines[:, 2])[::-1]
        sorted_lines = lines[sorted_indices]
        
        return sorted_lines
        
    def filter_lines_vectorized(self, lines, rho_threshold=20, theta_threshold=0.1):
        """
        Vectorized suppression of similar lines.
        lines: Nx3 array of [rho, theta, votes], assumed to be sorted by votes.
        """
        if len(lines) == 0:
            return lines
    
        rhos = lines[:, 0]
        thetas = lines[:, 1]
    
        # 1. Compute pairwise absolute differences for all lines
        # Using broadcasting: (N, 1) - (1, N) results in an (N, N) matrix
        rho_diffs = np.abs(rhos[:, np.newaxis] - rhos[np.newaxis, :])
        theta_diffs = np.abs(thetas[:, np.newaxis] - thetas[np.newaxis, :])
    
        # 2. Define "similarity" (True if lines are close)
        is_similar = (rho_diffs < rho_threshold) & (theta_diffs < theta_threshold)
    
        # 3. Greedy elimination
        # Since lines are sorted by votes, we want to keep the lower index (stronger line)
        # and discard any higher index (weaker line) that is similar to it.
        keep = np.ones(len(lines), dtype=bool)
        
        for i in range(len(lines)):
            if keep[i]:
                # Set 'keep' to False for all lines that are similar to line 'i'
                # and come AFTER line 'i' in the sorted list.
                # is_similar[i, i+1:] targets the weaker neighbors.
                keep[i+1:] &= ~is_similar[i, i+1:]
    
        return lines[keep]
    
    def measure_line_segments(self, rho, theta, min_line_length=50, max_line_gap=10):
        """
        Measure actual contiguous line segments along a detected line.
        
        Parameters:
        -----------
        rho : float
            Distance from origin to line
        theta : float
            Angle of line in radians
        min_line_length : int
            Minimum length of line segment in pixels
        max_line_gap : int
            Maximum gap to bridge between segments
        
        Returns:
        --------
        segments : list of tuples
            List of ((x1, y1), (x2, y2), length) for each segment
        """
        h, w = self.edges.shape
        
        # Get all edge points
        edge_points = np.argwhere(self.edges > 0)
        
        if len(edge_points) == 0:
            return []
        
        # Calculate perpendicular distance from each edge point to the line
        y_coords = edge_points[:, 0]
        x_coords = edge_points[:, 1]
        
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        
        # Distance from point (x,y) to line: |x*cos(theta) + y*sin(theta) - rho|
        distances = np.abs(x_coords * cos_theta + y_coords * sin_theta - rho)
        
        # Points within 1.5 pixels of the line are considered "on" the line
        on_line_mask = distances < 1.5
        line_points = edge_points[on_line_mask]
        
        if len(line_points) == 0:
            return []
        
        # Project points onto the line direction to get 1D coordinates along the line
        # The line direction vector is (-sin(theta), cos(theta))
        line_direction_x = -sin_theta
        line_direction_y = cos_theta
        
        # Project each point onto the line direction
        projections = line_points[:, 1] * line_direction_x + line_points[:, 0] * line_direction_y
        
        # Sort points by their projection (position along the line)
        sorted_indices = np.argsort(projections)
        sorted_points = line_points[sorted_indices]
        sorted_projections = projections[sorted_indices]
        
        # Find contiguous segments by detecting gaps
        segments = []
        
        if len(sorted_points) > 0:
            segment_start_idx = 0
            
            for i in range(1, len(sorted_points)):
                # Calculate gap between consecutive points
                gap = sorted_projections[i] - sorted_projections[i-1]
                
                # If gap exceeds threshold, end current segment and start new one
                if gap > max_line_gap:
                    # End current segment
                    segment_end_idx = i - 1
                    segment_length = sorted_projections[segment_end_idx] - sorted_projections[segment_start_idx]
                    
                    if segment_length >= min_line_length:
                        start_point = sorted_points[segment_start_idx]
                        end_point = sorted_points[segment_end_idx]
                        segments.append((
                            (int(start_point[1]), int(start_point[0])),  # (x1, y1)
                            (int(end_point[1]), int(end_point[0])),      # (x2, y2)
                            segment_length
                        ))
                    
                    # Start new segment
                    segment_start_idx = i
            
            # Handle the last segment
            segment_end_idx = len(sorted_points) - 1
            segment_length = sorted_projections[segment_end_idx] - sorted_projections[segment_start_idx]
            
            if segment_length >= min_line_length:
                start_point = sorted_points[segment_start_idx]
                end_point = sorted_points[segment_end_idx]
                segments.append((
                    (int(start_point[1]), int(start_point[0])),
                    (int(end_point[1]), int(end_point[0])),
                    segment_length
                ))
        
        return segments
                
    def hough_line_transform(self, edges, threshold=100, min_line_length=50, max_line_gap=10):
        """
        Perform Hough Line Transform to detect lines.
        
        Parameters:
        -----------
        edges : numpy array
            Binary edge image
        threshold : int
            Accumulator threshold (higher = fewer, stronger lines)
        min_line_length : int
            Minimum length of line in pixels
        max_line_gap : int
            Maximum gap between line segments to treat as single line
        
        Returns:
        --------
        lines : list of tuples
            List of (rho, theta, segments) for detected lines
            where segments is a list of ((x1,y1), (x2,y2), length)
        """
        logger.debug("  Creating accumulator space...")
        h, w = edges.shape
           
        # Calculate diagonal length for max rho
        diag_len = int(np.sqrt(h**2 + w**2))
        # Get edge points
        edge_points = np.argwhere(edges > 0)
        logger.debug(f"  Found {len(edge_points)} edge points")
        
        if len(edge_points) == 0:
            return []
        
        # Theta ranges from -90 to 90 degrees (in radians)
        theta_res = np.pi / 180  # 1 degree resolution
        thetas = np.arange(-np.pi/2, np.pi/2, theta_res)
        
        # Rho ranges from -diag_len to diag_len
        rho_res = 1  # 1 pixel resolution
        rhos = np.arange(-diag_len, diag_len, rho_res)
                
        logger.debug(f"  Accumulator size: {len(rhos)}, {len(thetas)}")
        logger.debug("  Voting in parameter space...")
        
        accumulator = self.hough_transform_vectorized(edge_points, thetas, rhos, rho_res)
        logger.debug(f"  Finding lines above threshold {threshold}...")
        
        # Find lines above threshold
        line_indices = np.argwhere(accumulator >= threshold)
        
        logger.debug(f"  Found {len(line_indices)} line candidates")
        lines = self.extract_lines_vectorized(accumulator, rhos, thetas, line_indices)
        
        filtered_lines = self.filter_lines_vectorized(lines, rho_threshold=20, theta_threshold=0.1)
        
        logger.debug(f"  After filtering: {len(filtered_lines)} unique lines")
        
        # Measure actual line segments for each detected line
        logger.debug(f"  Measuring line segments (min_length={min_line_length}, max_gap={max_line_gap})...")
        lines_with_segments = []
        
        for rho, theta, votes in filtered_lines:
            segments = self.measure_line_segments(rho, theta, min_line_length, max_line_gap)
            if segments:  # Only keep lines that have valid segments
                lines_with_segments.append((rho, theta, segments))
        
        logger.debug(f"  Lines with valid segments: {len(lines_with_segments)}")
        
        return lines_with_segments
    
    def get_line_endpoints(self, rho, theta, img_shape, extend=1000):
        """
        Calculate line endpoints from rho and theta.
        
        Parameters:
        -----------
        rho : float
            Distance from origin to line
        theta : float
            Angle of line in radians
        img_shape : tuple
            (height, width) of image
        extend : int
            How far to extend the line
        
        Returns:
        --------
        (x1, y1, x2, y2) : tuple
            Line endpoints
        """
        h, w = img_shape
        
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        
        # Point on the line closest to origin
        x0 = rho * cos_theta
        y0 = rho * sin_theta
        
        # Calculate endpoints
        x1 = int(x0 + extend * (-sin_theta))
        y1 = int(y0 + extend * (cos_theta))
        x2 = int(x0 - extend * (-sin_theta))
        y2 = int(y0 - extend * (cos_theta))
        
        # Clip to image boundaries
        def clip_line(x1, y1, x2, y2, w, h):
            """Clip line to image boundaries."""
            # Simple clipping
            x1 = max(0, min(w-1, x1))
            y1 = max(0, min(h-1, y1))
            x2 = max(0, min(w-1, x2))
            y2 = max(0, min(h-1, y2))
            return x1, y1, x2, y2
        
        return clip_line(x1, y1, x2, y2, w, h)
        
    def plot_lines(self, lines, color=None, linewidth=None):
        if linewidth is None:
          linewidth = 3
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        if len(lines) > 0:
            # Draw lines on original image
            output_img = Image.fromarray(self.img_array)
            draw = ImageDraw.Draw(output_img)
            
            logger.debug("Detected lines:")
            logger.debug(f"{'#':<4} {'Rho':<10} {'Theta (deg)':<15} {'Segments':<10} {'Total Length':<15}")
            logger.debug("-" * 70)
            
            colors = [
                (0, 255, 0),    # Green
                (255, 0, 0),    # Red
                (0, 0, 255),    # Blue
                (255, 165, 0),  # Orange
                (128, 0, 128),  # Purple
                (0, 255, 255),  # Cyan
                (255, 192, 203),  # Pink
                (165, 42, 42),  # Brown
            ]
            
            for i, (rho, theta, segments) in enumerate(lines):
                if color is None:
                   color = colors[i % len(colors)]
                
                # Draw each segment
                total_length = 0
                for (x1, y1), (x2, y2), length in segments:
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=linewidth)
                    total_length += length
                
                # Print line info
                theta_deg = theta * 180 / np.pi
                logger.debug(f"{i+1:<4} {rho:<10.1f} {theta_deg:<15.1f} {len(segments):<10} {total_length:<15.1f}")
            
            # Save marked image
            marked_filename = os.path.join(self.output_dir, 'lines_detected.png')
            output_img.save(marked_filename)
            logger.debug(f"Saved marked image: {marked_filename}")
            
            # Save edges
            edge_filename = os.path.join(self.output_dir, 'edges.png')
            Image.fromarray(self.edges.astype(np.uint8)).save(edge_filename)
            logger.debug(f"Saved edge image: {edge_filename}")
            
            # Create a visualization with line parameters
            self.create_line_visualization(lines, self.img_array.shape)
                          
    def create_line_visualization(self, lines, img_shape):
        """Create a clean visualization showing just the detected line segments."""
        h, w = img_shape[:2]
        
        # Create blank white canvas
        vis_img = Image.new('RGB', (w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(vis_img)
        
        # Draw each line in different color
        colors = [
            (255, 0, 0),    # Red
            (0, 0, 255),    # Blue
            (255, 165, 0),  # Orange
            (128, 0, 128),  # Purple
            (0, 128, 128),  # Teal
            (255, 192, 203),  # Pink
            (165, 42, 42),  # Brown
            (0, 255, 255),  # Cyan
        ]
        
        for i, (rho, theta, segments) in enumerate(lines):
            color = colors[i % len(colors)]
            
            # Draw each segment
            for (x1, y1), (x2, y2), length in segments:
                draw.line([(x1, y1), (x2, y2)], fill=color, width=4)
        
        vis_filename = os.path.join(self.output_dir, 'lines_visualization.png')
        vis_img.save(vis_filename)
        logger.debug(f"Saved line visualization: {vis_filename}")
                
# Arc Detection - Simplified Approach
# This version detects circles first, then determines which are actually arcs
# by analyzing the angular distribution of edge points


class CircleDetector(FeatureExtract):
    """Extends FeatureExtract to add circle detection capability."""
    def __init__(self, image_path=None, output_dir='output',
                 canny_low=0.05, canny_high=0.15, image_process=None):
       
       if image_process is None:
           super().__init__(image_path, output_dir,
                            canny_low, canny_high)
       else:
           self.edges = image_process.edges
           self.img_array = image_process.img_array
           self.output_dir = image_process.output_dir
                     
    def extract_circles(self, min_radius=15, max_radius=100,
                        threshold=9, min_dist=30):
        """
        Extract circles from an image using pure NumPy implementation.
        
        Parameters:
        -----------
        min_radius : int
            Minimum circle radius
        max_radius : int
            Maximum circle radius
        threshold : int or None
            Accumulator threshold (higher = fewer, stronger circles)
            If None, uses adaptive threshold based on circle circumference
        min_dist : int
            Minimum distance between circle centers
        """
        # Use adaptive threshold if not specified
        if threshold is None:
            # Adaptive threshold based on expected votes for a circle
            # A complete circle of radius r has circumference 2*pi*r
            # With 36 angle samples, we expect roughly 36 votes for a perfect circle
            # In practice, circles are fragmented, so use a fraction
            # avg_radius = (min_radius + max_radius) / 2
            expected_votes = 36  # Number of angles we sample
            # Require at least 20-30% of the circumference to be present
            threshold = max(8, int(expected_votes * 0.25))
            logger.debug(f"  Using adaptive threshold: {threshold}")
        else:
            
            logger.debug(f"  Using manual threshold: {threshold}")
          
        logger.debug(f"Performing Hough Circle Transform (r={min_radius}-{max_radius})...")
        circles = self.hough_circle_transform(self.edges, min_radius, max_radius, threshold, min_dist)
        logger.debug(f"Detected {len(circles)} circles!")
        return circles

    def plot_circles(self, circles, color=None, linewidth=None):
        if linewidth is None:
          linewidth = 3
        if color is None:
           color = [0, 255, 0]
        else:
            color = list(ImageColor.getrgb(color))

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        if len(circles) > 0:
            # Draw circles on original image (FIXED: use self.img_array)
            output_img = self.img_array.copy()
            
            for i, (x, y, r) in enumerate(circles):
                logger.debug(f"  Circle {i+1}: center=({x}, {y}), radius={r}")
                
                # Draw circle outline
                for theta in np.linspace(0, 2*np.pi, 360):
                    x_circle = int(x + r * np.cos(theta))
                    y_circle = int(y + r * np.sin(theta))
                    
                    if 0 <= y_circle < output_img.shape[0] and 0 <= x_circle < output_img.shape[1]:
                        output_img[y_circle, x_circle] = color
                        
                        # Thicker line
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                ny, nx = y_circle + dy, x_circle + dx
                                if 0 <= ny < output_img.shape[0] and 0 <= nx < output_img.shape[1]:
                                    output_img[ny, nx] = color
                
                # Draw center
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < output_img.shape[0] and 0 <= nx < output_img.shape[1]:
                            if dx*dx + dy*dy <= 9:
                                output_img[ny, nx] = [0, 0, 255]  # Red center
                
                # Extract individual circle (FIXED: use self.img_array)
                padding = 10
                y1 = max(0, y - r - padding)
                y2 = min(self.img_array.shape[0], y + r + padding)
                x1 = max(0, x - r - padding)
                x2 = min(self.img_array.shape[1], x + r + padding)
                
                circle_roi = self.img_array[y1:y2, x1:x2].copy()
                
                # Create circular mask
                mask = np.zeros((y2-y1, x2-x1), dtype=bool)
                center_y, center_x = y - y1, x - x1
                
                for ry in range(y2-y1):
                    for rx in range(x2-x1):
                        if (rx - center_x)**2 + (ry - center_y)**2 <= r**2:
                            mask[ry, rx] = True
                
                # Apply mask
                circle_extracted = circle_roi.copy()
                if len(circle_extracted.shape) == 3:
                    for c in range(3):
                        circle_extracted[:, :, c] = circle_extracted[:, :, c] * mask
                else:
                    circle_extracted = circle_extracted * mask
                
                # Save individual circle
                # circle_filename = os.path.join(self.output_dir, f'circle_{i+1:02d}_r{r}.png')
                # Image.fromarray(circle_extracted).save(circle_filename)
            
            # Save marked image
            marked_filename = os.path.join(self.output_dir, 'circles_detected.png')
            Image.fromarray(output_img).save(marked_filename)
            logger.debug(f"Saved marked image: {marked_filename}")
            
            # Save edges for debugging (FIXED: use self.edges)
            edge_filename = os.path.join(self.output_dir, 'edges.png')
            Image.fromarray(self.edges.astype(np.uint8)).save(edge_filename)
            logger.debug(f"Saved edge image: {edge_filename}")

    def hough_circle_transform(self, edges, min_radius, max_radius, threshold, min_dist=30):
        """
        Perform Hough Circle Transform to detect circles.
        
        Parameters:
        -----------
        edges : numpy array
            Binary edge image
        min_radius : int
            Minimum circle radius
        max_radius : int
            Maximum circle radius
        threshold : int
            Accumulator threshold (higher = fewer circles)
        min_dist : int
            Minimum distance between circle centers
        
        Returns:
        --------
        circles : list of tuples
            List of (x, y, radius) for detected circles
        """
        logger.debug("  Creating accumulator space...")
        h, w = edges.shape
        
        # Get edge points
        edge_points = np.argwhere(edges > 0)
        logger.debug(f"  Found {len(edge_points)} edge points")
        
        if len(edge_points) == 0:
            return []
        
        # Create accumulator for each radius
        circles = []
        
        radii_range = range(min_radius, max_radius + 1)
        # total_radii = len(radii_range)
        
        for r_idx, r in enumerate(radii_range):
            if r_idx % 10 == 0:
                logger.debug(f"  Processing radius {r}/{max_radius}.. {len(circles)} so far")
            
            # Accumulator for this radius
            accumulator = np.zeros((h, w), dtype=np.int32)
            
            # Precompute sin/cos for this radius
            angles = np.linspace(0, 2*np.pi, 36)
            cos_angles = r * np.cos(angles)
            sin_angles = r * np.sin(angles)
            accumulator = self.circular_hough_voting_vectorized(accumulator, edge_points, cos_angles, sin_angles)
            """
            # Vote in accumulator space
            for y, x in edge_points:
                # For each edge point, draw circles in accumulator
                for cos_a, sin_a in zip(cos_angles, sin_angles):
                    a = int(x - cos_a)
                    b = int(y - sin_a)
                    
                    if 0 <= a < w and 0 <= b < h:
                        accumulator[b, a] += 1
            """
            # Find local maxima in accumulator
            max_val = accumulator.max()
            if max_val < threshold:
                continue
            
            # Find peaks
            potential_centers = np.argwhere(accumulator >= threshold)
            
            for b, a in potential_centers:
                # Check if this is a local maximum
                region = accumulator[max(0, b-2):min(h, b+3), max(0, a-2): min(w, a+3)]
                if accumulator[b, a] == region.max():
                    circles.append((a, b, r, accumulator[b, a]))
            
        logger.debug(f"  Found {len(circles)} candidate circles")
        
        # Non-maximum suppression: remove overlapping circles
        if len(circles) > 0:
            circles = sorted(circles, key=lambda c: c[3], reverse=True)  # Sort by votes
            
            filtered_circles = []
            for x, y, r, votes in circles:
                # Check distance to already accepted circles
                too_close = False
                for fx, fy, fr, _ in filtered_circles:
                    dist = np.sqrt((x - fx)**2 + (y - fy)**2)
                    if dist < min_dist:
                        too_close = True
                        break
                
                if not too_close:
                    filtered_circles.append((x, y, r, votes))
            
            circles = [(x, y, r) for x, y, r, _ in filtered_circles]
        
        return circles
        
    def circular_hough_voting_vectorized(self, accumulator, edge_points, cos_angles, sin_angles):
        """
        Vectorized Circular Hough Accumulator voting.
        edge_points: Nx2 array of (y, x) coordinates
        cos_angles: 1D array of r * cos(theta)
        sin_angles: 1D array of r * sin(theta)
        """
        h, w = accumulator.shape
    
        # 1. Extract x and y as column vectors (Shape: N x 1)
        y = edge_points[:, 0][:, np.newaxis]
        x = edge_points[:, 1][:, np.newaxis]
    
        # 2. Use broadcasting to calculate all possible centers (a, b)
        # (N x 1) - (1 x M) -> (N x M) matrix of all possible centers
        a_centers = (x - cos_angles).astype(np.int32)
        b_centers = (y - sin_angles).astype(np.int32)
    
        # 3. Flatten the arrays to simplify filtering and voting
        a_flat = a_centers.ravel()
        b_flat = b_centers.ravel()
    
        # 4. Filter for centers that fall within the image boundaries
        valid_mask = (a_flat >= 0) & (a_flat < w) & (b_flat >= 0) & (b_flat < h)
        
        a_valid = a_flat[valid_mask]
        b_valid = b_flat[valid_mask]
    
        # 5. Perform the vote using np.add.at (unbuffered addition)
        # This is the vectorized equivalent of the += 1 loop
        np.add.at(accumulator, (b_valid, a_valid), 1)
        
        return accumulator
    
        
class ArcDetector(FeatureExtract):
    """Extends FeatureExtract to add arc detection capability."""
    def __init__(self, image_path=None, output_dir='output',
                 canny_low=0.05, canny_high=0.15, image_process=None):
       
       if image_process is None:
           super().__init__(image_path, output_dir,
                            canny_low, canny_high)
       else:
           self.edges = image_process.edges
           self.img_array = image_process.img_array
           self.output_dir = image_process.output_dir
            
    def extract_arcs(self, min_radius=15, max_radius=100, threshold=None,
                     min_arc_angle=30, max_arc_angle=330, min_dist=30,
                     max_coverage=0.9, circle_detector=None):
        """
        Extract arcs by first detecting circles, then filtering for incomplete ones.
        
        Parameters:
        -----------
        min_radius, max_radius, threshold, min_dist : same as extract_circles
        min_arc_angle : float
            Minimum arc span in degrees
        max_arc_angle : float
            Maximum arc span in degrees
        max_coverage : float
            Maximum coverage (0-1) to be considered an arc (default 0.9 = 90%)
        """
        # First, detect all circles (including partial ones)
        logger.debug("Step 1: Detecting circular features...")
        if circle_detector is None:
            logger.debug("No circle detector referenced")
            return []
        circles = circle_detector.extract_circles(min_radius, max_radius, threshold, min_dist)
        
        if len(circles) == 0:
            logger.debug("No circular features detected")
            return []
        
        # Analyze each circle to see if it's an arc
        logger.debug(f"Step 2: Analyzing {len(circles)} circles for arc characteristics...")
        arcs = []
        
        for i, (x, y, r) in enumerate(circles):
            is_arc, start, end, span, coverage = self.analyze_circle_completeness(x, y, r)
            
            # Check if it meets arc criteria
            if coverage <= max_coverage and min_arc_angle <= span <= max_arc_angle:
                arcs.append((x, y, r, start, end, span, coverage))
                logger.debug(f"  Arc {len(arcs)}: center=({x},{y}), r={r}, "
                             f"span={span:.0f}°, coverage={coverage:.1%}")
        
        logger.debug(f"Detected {len(arcs)} arcs (from {len(circles)} circular features)")
        return arcs
            
    def analyze_circle_completeness(self, x, y, r):
        """
        Analyze a detected circle to determine if it's an arc and its angular extent.
        
        Returns: (is_arc, arc_start_angle, arc_end_angle, arc_span, coverage)
        """
        # Get edge points near this circle
        edge_points = np.argwhere(self.edges > 0)
        
        if len(edge_points) == 0:
            return False, 0, 0, 0, 0
        
        # Find points that are close to the circle perimeter
        y_coords = edge_points[:, 0]
        x_coords = edge_points[:, 1]
        
        # Distance from each edge point to circle perimeter
        distances = np.sqrt((x_coords - x)**2 + (y_coords - y)**2)
        on_circle = np.abs(distances - r) < 2.0  # Within 2 pixels of perimeter
        
        circle_points = edge_points[on_circle]
        
        if len(circle_points) < 5:
            return False, 0, 0, 0, 0
        
        # Calculate angles of points on the circle
        angles = np.arctan2(circle_points[:, 0] - y, circle_points[:, 1] - x)
        angles_deg = np.rad2deg(angles)  # -180 to 180
        
        # Create angular histogram (36 bins = 10Â° each)
        num_bins = 36
        hist, bin_edges = np.histogram(angles_deg, bins=num_bins, range=(-180, 180))
        
        # Find bins with points
        active_bins = hist > 0
        num_active = np.sum(active_bins)
        
        # Calculate coverage
        coverage = num_active / num_bins
        
        # Find contiguous arc segments
        segments = self.find_contiguous_segments_vectorized(active_bins)
        
        if len(segments) == 0:
            return False, 0, 0, 0, coverage
        
        # Find the largest segment
        largest_segment = max(segments, key=lambda s: s[1] - s[0])
        start_bin, end_bin = largest_segment
        
        # Convert bins to angles
        bin_size = 360.0 / num_bins
        arc_start = -180 + start_bin * bin_size
        arc_end = -180 + end_bin * bin_size
        
        # Calculate span
        span_bins = end_bin - start_bin
        arc_span = span_bins * bin_size
        
        # Determine if it's an arc (not a complete circle)
        # If coverage is < 90%, it's an arc
        is_arc = coverage < 0.9
        
        return is_arc, arc_start, arc_end, arc_span, coverage
    
    def _find_contiguous_segments(self, active_bins):
        """Find contiguous True segments in a boolean array."""
        segments = []
        in_segment = False
        start = 0
        
        # Extend to handle wrap-around
        extended = np.concatenate([active_bins, active_bins])
        
        for i in range(len(extended)):
            if extended[i]:
                if not in_segment:
                    start = i
                    in_segment = True
            else:
                if in_segment:
                    end = i
                    # Only record segments that start in first half
                    if start < len(active_bins):
                        segments.append((start % len(active_bins),
                                        (end - 1) % len(active_bins)))
                    in_segment = False
        
        # Handle segment that goes to end
        if in_segment and start < len(active_bins):
            segments.append((start % len(active_bins),
                            (len(extended) - 1) % len(active_bins)))
        
        return segments

    def find_contiguous_segments_vectorized(self, active_bins):
        n = len(active_bins)
        # Concatenate to handle the wrap-around logic from your loop
        extended = np.concatenate([active_bins, active_bins])
        
        # Prepend and Append a False to catch segments starting at index 0 or ending at the last index
        # This allows diff to catch the transition
        padded = np.concatenate([[False], extended, [False]])
        
        # Calculate the difference (True - False = 1, False - True = -1)
        diff = np.diff(padded.astype(np.int8))
        
        # Starts are where diff is 1; Ends are where diff is -1
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0] - 1  # Subtract 1 to get the inclusive end index
        
        # Filter: Only record segments that start in the first half (per your original logic)
        mask = starts < n
        valid_starts = starts[mask]
        valid_ends = ends[mask]
        
        # Apply modulo for the wrap-around indices
        final_starts = valid_starts % n
        final_ends = valid_ends % n
        
        # Return as a list of tuples to match your original output format
        return list(zip(final_starts, final_ends))
    
    def plot_arcs(self, arcs):
        """Plot detected arcs with visual indicators."""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        if len(arcs) == 0:
            logger.debug("No arcs to plot")
            return
        
        output_img = self.img_array.copy()
        
        logger.debug("Detected arcs:")
        logger.debug(f"{'#':<4} {'Center':<15} {'Radius':<8} {'Span':<10} {'Coverage':<10} "
                     f"{'Start°':<10} {'End°':<10}")
        logger.debug("-" * 80)
        
        for i, (x, y, r, start_angle, end_angle, arc_span, coverage) in enumerate(arcs):
            logger.debug(f"{i+1:<4} ({x:3d}, {y:3d})    {r:<8} {arc_span:<10.1f} "
                         f"{coverage:<10.1%} {start_angle:<10.1f} {end_angle:<10.1f}")
            
            # Draw the arc in green
            start_rad = np.deg2rad(start_angle)
            end_rad = np.deg2rad(end_angle)
            
            # Generate points along the arc
            num_points = int(arc_span * 2)  # 2 points per degree
            angles = np.linspace(start_rad, end_rad, num_points)
            
            for theta in angles:
                x_arc = int(x + r * np.cos(theta))
                y_arc = int(y + r * np.sin(theta))
                
                if 0 <= y_arc < output_img.shape[0] and 0 <= x_arc < output_img.shape[1]:
                    # Green arc
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            ny, nx = y_arc + dy, x_arc + dx
                            if (0 <= ny < output_img.shape[0]
                                and 0 <= nx < output_img.shape[1]
                                and dx*dx + dy*dy <= 4):
                                output_img[ny, nx] = [0, 255, 0]
            
            # Draw center (blue)
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < output_img.shape[0] and
                        0 <= nx < output_img.shape[1] and
                        dx*dx + dy*dy <= 16):
                        output_img[ny, nx] = [0, 0, 255]
            
            # Draw endpoints (red)
            for angle in [start_rad, end_rad]:
                x_end = int(x + r * np.cos(angle))
                y_end = int(y + r * np.sin(angle))
                
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        ny, nx = y_end + dy, x_end + dx
                        if (0 <= ny < output_img.shape[0] and
                            0 <= nx < output_img.shape[1] and
                            dx*dx + dy*dy <= 9):
                            output_img[ny, nx] = [255, 0, 0]
        
        # Save
        marked_filename = os.path.join(self.output_dir, 'arcs_detected.png')
        Image.fromarray(output_img).save(marked_filename)
        logger.debug(f"Saved: {marked_filename}")


class ContourDetector(FeatureExtract):
    """Extends FeatureExtract to add contour detection capability."""
    def __init__(self, image_path=None, output_dir='output',
                 canny_low=0.05, canny_high=0.15, image_process=None):
       
       if image_process is None:
           super().__init__(image_path, output_dir,
                            canny_low, canny_high)
       else:
           self.edges = image_process.edges
           self.img_array = image_process.img_array
           self.output_dir = image_process.output_dir
 
    def find_contours_numpy(self, img):
        """Scans the image to find all external contours."""
        img_binary = (img > 220).astype(np.uint8)
        # img_binary = self.detect_edges(img)
        # img_binary = (img_binary > 10).astype(np.uint8)
        plt.figure(figsize=(8, 8))
        plt.imshow(img_binary, cmap='gray', interpolation='nearest')
        plt.show()
        # Define colors for different contours
        colors = ['cyan', 'lime', 'red']
                
        visited = np.zeros_like(img_binary, dtype=bool)
        # first white pixel
        r_start, c_start = tuple(np.min(np.argwhere(img_binary == 1), axis=0))
        contours = []
        colors = ['cyan', 'lime', 'red']
        i = 0
        for r in range(r_start, img_binary.shape[0]):
            for c in range(c_start, img_binary.shape[1]):
                if img_binary[r, c] == 1 and not visited[r, c]:
                    # External boundary check: pixel to the left should be 0
                    if c == 0 or img_binary[r, c-1] == 0:
                        cnt = self.trace_contour(img_binary, (r, c), visited)
                        
                        contour_l = np.min(cnt, axis=0)
                        contour_t = np.max(cnt, axis=0)
                        contour_area = np.prod(contour_t - contour_l)
                        scaled_contour_area = contour_area / img.size
                        if len(cnt) > 100 and scaled_contour_area > 0.015:
                            # reduce number of points
                            cnt = cnt[::20]
                            contours.append(cnt)
                            self.plot_contour(cnt, color=colors[i % len(colors)])
                            i += 1
        return contours
        
    def trace_contour(self, img, start_pixel, visited_mask):
        """Moore-Neighbor Tracing algorithm to follow a boundary."""
        contour = []
        current_pixel = start_pixel
        # Initial 'back' pixel is the one to the left of start
        back_pixel = (start_pixel[0], start_pixel[1] - 1)
        
        first_run = True
        while first_run or current_pixel != start_pixel:
            first_run = False
            contour.append(current_pixel)
            visited_mask[current_pixel] = True
            
            neighbors = self.get_neighbors(current_pixel)
            
            # Start searching clockwise from the background pixel we just came from
            try:
                start_search_idx = neighbors.index(back_pixel)
            except ValueError:
                start_search_idx = 0
                
            for i in range(1, 9):
                idx = (start_search_idx + i) % 8
                neighbor = neighbors[idx]
                
                # Check bounds and if it's a foreground pixel
                if (0 <= neighbor[0] < img.shape[0] and
                    0 <= neighbor[1] < img.shape[1]):
                    if img[neighbor] == 1:
                        # Update back_pixel to the last background pixel checked
                        back_pixel = neighbors[(idx - 1) % 8]
                        current_pixel = neighbor
                        break
        return np.array(contour)
        
    def extract_features(self, dilated, min_size=10):
        rows, cols = dilated.shape
        # Ensure binary (0 or 1)
        binary = (dilated == 255).astype(int)
        
        # We will use a standard connected component labeling logic.
        # Since we can't use scipy, we use an iterative approach that
        # minimizes Python overhead by processing blocks.
        
        # 1. Labeling (Iterative Propagation)
        # This is a 'Vectorized' version of the BFS logic
        labels = np.arange(rows * cols).reshape(rows, cols)
        labels[binary == 0] = -1
        
        # Iterate until labels stop changing (usually few iterations)
        for _ in range(max(rows, cols)):
            old_labels = labels.copy()
            
            # Shift and take the max to propagate labels to neighbors
            # We check 8-way neighbors
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    
                    # Create shifted views
                    # (Same logic as our dilation/perimeter code)
                    r_start, r_end = max(0, dr), rows + min(0, dr)
                    c_start, c_end = max(0, dc), cols + min(0, dc)
                    r_orig_s, r_orig_e = max(0, -dr), rows + min(0, -dr)
                    c_orig_s, c_orig_e = max(0, -dc), cols + min(0, -dc)
                    
                    neighbor_vals = labels[r_start:r_end, c_start:c_end]
                    labels[r_orig_s:r_orig_e, c_orig_s:c_orig_e] = np.maximum(
                        labels[r_orig_s:r_orig_e, c_orig_s:c_orig_e],
                        neighbor_vals
                    )
            
            # Re-mask to keep background at -1
            labels[binary == 0] = -1
            if np.array_equal(labels, old_labels):
                break
    
        # 2. Vectorized Filtering
        # Now we count occurrences of each label
        unique_labels, counts = np.unique(labels, return_counts=True)
        
        # Ignore background label (-1)
        mask = unique_labels != -1
        unique_labels = unique_labels[mask]
        counts = counts[mask]
        
        # Identify labels that meet our size criteria
        valid_labels = unique_labels[counts > min_size]
        
        # 3. Extracting coordinates
        features = []
        for label in valid_labels:
            # np.argwhere is vectorized and much faster than manual loops
            coords = np.argwhere(labels == label)
            # sorted_points = self.greedy_path(coords) #self.sort_outline_points(coords)
            features.append(coords)
            
        return features
        
    def filter_features(self, features, img_size, decimate=50):
        filtered_features = []
        for feature in features:
            feature_bl = np.min(feature, axis=0)
            feature_tr = np.max(feature, axis=0)
            feature_area = np.prod(feature_tr - feature_bl)
            scaled_contour_area = feature_area / img_size
            if scaled_contour_area >= 0.015:
                decimated = feature[::decimate]
                sorted = self.sort_outline_points(decimated)
                
                filtered_features.append(sorted)
        return filtered_features
                                                               
    def sort_outline_points(self, points):
        if not points:
            return []
    
        # Convert to list to allow mutation (popping)
        unvisited = list(points)
        # Start with the first point (or pick one specifically, like the leftmost)
        current_point = unvisited.pop(0)
        sorted_path = [current_point]
    
        while unvisited:
            # Find the point in 'unvisited' that is closest to 'current_point'
            next_point = min(unvisited, key=lambda p: get_distance(current_point, p))
            
            # Move to that point
            unvisited.remove(next_point)
            sorted_path.append(next_point)
            current_point = next_point
    
        return sorted_path
        
    def plot_contour(self, contour, color):
        plot_data = np.vstack([contour, contour[0]])
        plt.plot(plot_data[:, 1], plot_data[:, 0],
                 color=color,
                 linewidth=3)
       
        plt.title("NumPy Manual Contour Tracing", fontsize=14)
        # plt.legend()
        plt.axis('off')
        plt.show()


class FastContourDetector(FeatureExtract):
    """Extends FeatureExtract to add contour detection capability
       returns only closed shapes."""
    def __init__(self, image_path=None, output_dir='output',
                 canny_low=0.05, canny_high=0.15, image_process=None):
       
       if image_process is None:
           super().__init__(image_path, output_dir,
                            canny_low, canny_high)
       else:
           self.edges = image_process.edges
           self.img_array = image_process.img_array
           self.output_dir = image_process.output_dir
    """
    Fast contour detection using parallel labeling approach.
    Pure numpy implementation - no scipy required.
    Much faster than sequential Moore-Neighbor tracing for multiple contours.
    """
    def label_connected_components(self, binary_img):
        """
        Two-pass connected component labeling algorithm (8-connectivity).
        Args:
            binary_img: Binary image (0s and 1s)
            
        Returns:
            labeled_img: Image with each component having a unique label
            num_labels: Number of unique components found
        """
        h, w = self.edges.shape
        labels = np.zeros((h, w), dtype=np.int32)
        next_label = 1
        equivalences = {}  # Union-find structure
        
        def find(x):
            """Find root of equivalence class"""
            if x not in equivalences:
                equivalences[x] = x
            if equivalences[x] != x:
                equivalences[x] = find(equivalences[x])  # Path compression
            return equivalences[x]
        
        def union(x, y):
            """Merge two equivalence classes"""
            root_x, root_y = find(x), find(y)
            if root_x != root_y:
                equivalences[root_y] = root_x
        
        # First pass: assign provisional labels
        for i in range(h):
            for j in range(w):
                if self.edges[i, j] == 0:
                    continue
                
                # Check 8-connected neighbors (only previous ones)
                neighbors = []
                for di, dj in [(-1, -1), (-1, 0), (-1, 1), (0, -1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < h and 0 <= nj < w and labels[ni, nj] > 0:
                        neighbors.append(labels[ni, nj])
                
                if not neighbors:
                    # New component
                    labels[i, j] = next_label
                    next_label += 1
                else:
                    # Assign minimum neighbor label
                    min_label = min(neighbors)
                    labels[i, j] = min_label
                    # Record equivalences
                    for neighbor_label in neighbors:
                        if neighbor_label != min_label:
                            union(min_label, neighbor_label)
        
        # Second pass: resolve equivalences
        label_map = {}
        new_label = 0
        for i in range(h):
            for j in range(w):
                if labels[i, j] > 0:
                    root = find(labels[i, j])
                    if root not in label_map:
                        new_label += 1
                        label_map[root] = new_label
                    labels[i, j] = label_map[root]
        
        return labels, new_label        
    
    def binary_erosion(self, img: np.ndarray) -> np.ndarray:
        """
        Fast binary erosion with 3x3 structuring element (8-connectivity).
        
        Args:
            img: Binary image
            
        Returns:
            Eroded binary image
        """
        h, w = img.shape
        eroded = np.zeros_like(img)
        
        # Vectorized erosion using array slicing
        # A pixel is kept only if all 8 neighbors + itself are foreground
        eroded[1:-1, 1:-1] = (
            img[1:-1, 1:-1] &
            img[0:-2, 0:-2] & img[0:-2, 1:-1] & img[0:-2, 2:] &
            img[1:-1, 0:-2] &                    img[1:-1, 2:] &
            img[2:, 0:-2]   & img[2:, 1:-1] & img[2:, 2:]
        )
        
        return eroded
    
    def find_all_contours(self, min_contour_length=4, max_contour_length=None):
        """
        Find all contours in a binary image using parallel labeling.
        
        Args:
            min_contour_length: Minimum number of pixels to be considered a contour
            max_contour_length: Maximum number of pixels to be considered a contour
        Returns:
            List of contours, where each contour is an Nx2 array of (row, col) coordinates
        
        """
        # Ensure binary image (0 and 1)
        binary_img = (self.edges > 0).astype(np.uint8)
        
        # Step 1: Label all connected components
        labeled_img, num_features = self.label_connected_components(binary_img)
        
        if num_features == 0:
            return []
        
        # Step 2: Extract boundary pixels for all components at once
        # Boundary = original XOR eroded (gives outer boundary)
        eroded = self.binary_erosion(binary_img)
        boundaries = binary_img ^ eroded  # XOR gives boundary pixels
        
        # Step 3: Extract contours for each labeled component
        contours = []
        
        for label_id in range(1, num_features + 1):
            # Get all boundary pixels for this component
            component_boundary = (labeled_img == label_id) & (boundaries == 1)
            boundary_coords = np.column_stack(np.where(component_boundary))
            boundary_coords = np.fliplr(boundary_coords)  # swap x and y
            if len(boundary_coords) < min_contour_length:
                continue
            if max_contour_length and len(boundary_coords) > max_contour_length:
                continue
            contours.append(boundary_coords)
        
        return contours
    
    def find_all_contours_ordered(self, min_contour_length=4, max_contour_length=None):
        """
        Find all contours with ordered boundary pixels (proper chain).
        Slower than find_all_contours but gives contours in tracing order.
        
        Args:
            min_contour_length: Minimum number of pixels to be considered a contour
            max_contour_length: Maximum number of pixels to be considered a contour
                                primarily for debugging
            
        Returns:
            List of ordered contours
        """
        contours = self.find_all_contours(min_contour_length, max_contour_length)
        ordered_contours = []
        
        for contour in contours:
            if len(contour) == 0:
                continue
            
            ordered = self._order_contour_points(contour, threshold=3)
            if len(ordered) > 0:
               ordered_contours.append(ordered)
        
        return ordered_contours

    def _order_contour_points(self, points, threshold=1.0):
        if len(points) <= 1:
            return points
    
        n_points = len(points)
        ordered = np.zeros_like(points)
        
        mask = np.ones(n_points, dtype=bool)
        
        # Start with the first point
        current_idx = 0
        start_point = points[current_idx]
        ordered[0] = start_point
        mask[current_idx] = False
        
        points_placed = 1
    
        for i in range(1, n_points):
            current = ordered[i-1]
            
            # Early Exit Logic
            # Check if current point is close to start_point
            # and we have traveled at least half the total points
            if i > n_points / 2:
                dist_to_start = np.sum(np.abs(current - start_point))
                if dist_to_start < threshold:
                    # Return only the portion of the array we actually filled
                    return ordered[:i]

            remaining_indices = np.where(mask)[0]
            if len(remaining_indices) == 0:
                break
                
            remaining_points = points[remaining_indices]
            
            # Manhattan distance calculation
            dists = np.sum(np.abs(remaining_points - current), axis=1)
            
            local_idx = np.argmin(dists)
            current_idx = remaining_indices[local_idx]
            
            ordered[i] = points[current_idx]
            mask[current_idx] = False
            points_placed += 1
            
        # filter non closed arcs
        dist_to_start = np.sum(np.abs(current - start_point))
        if dist_to_start > threshold:
            return []
        return ordered[:points_placed]
            
    def pca(self, coords):
        """ unrotate a shape using Principal_Component_Analysis"""
        # Center the coordinates
        centroid = coords.mean(axis=0)
        centered = coords - centroid
       
        # Use PCA to find principal axes
        cov_matrix = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
        
        # Sort by eigenvalue (largest first)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Rotate points to align with principal axes
        rotated = centered @ eigenvectors
        return rotated, eigenvalues
        
    def is_rounded_rectangle(self, coords, tolerance=0):
        """
        Detect if coordinates form a rounded rectangle at any angle using only numpy.
        
        Parameters:
        coords: numpy array of shape (N, 2) with x,y coordinates
        """
        rectangle = False
        if len(coords) < 10:
            return False, False
        
        rotated, eigenvalues = self.pca(coords)
        # Get bounding box in rotated coordinates
        x_min, y_min = rotated.min(axis=0)
        x_max, y_max = rotated.max(axis=0)
        width = x_max - x_min
        height = y_max - y_min
        
        if width == 0 or height == 0:
            return False, False
        
        # 1. Check edge alignment in rotated coordinates
        edge_threshold = 0.1 * min(width, height)
        
        left_edge = np.sum(np.abs(rotated[:, 0] - x_min) < edge_threshold)
        right_edge = np.sum(np.abs(rotated[:, 0] - x_max) < edge_threshold)
        bottom_edge = np.sum(np.abs(rotated[:, 1] - y_min) < edge_threshold)
        top_edge = np.sum(np.abs(rotated[:, 1] - y_max) < edge_threshold)
        
        edge_points = left_edge + right_edge + bottom_edge + top_edge
        edge_ratio = edge_points / len(coords)
        
        # Most points should be near edges
        # if so it must be a rectangle
        if edge_ratio < 0.7:
            return False, False
        else:
            rectangle = True
        # 2. Check corners for rounding
        corner_threshold = 0.2 * min(width, height)
        corners_rounded = 0
                
        # try a different routine
        # find radius of end
        # find if all coordinates to left of radius are close to circle
        radius_l = x_min + height / 2
        radius_r = x_max - height/2
        # slice left coordinates
        left_end = rotated[rotated[:, 0] < radius_l]
        right_end = rotated[rotated[:, 0] > radius_r]
        distances_l = np.sqrt((left_end[:, 0] - radius_l)**2 + left_end[:, 1]**2)
        total_l = distances_l - height / 2
        close_l = np.all(total_l < corner_threshold)
        distances_r = np.sqrt((right_end[:, 0] - radius_r)**2 + right_end[:, 1]**2)
        total_r = (distances_r - height / 2)
        close_r = np.all(total_r < corner_threshold)
        corners_rounded = 2*close_l + 2*close_r
        
        # 3. Check aspect ratio
        aspect_ratio = max(width, height) / min(width, height)
        
        # 4. Check eigenvalue ratio (should be significantly different for rectangles)
        eigenvalue_ratio = eigenvalues[0] / eigenvalues[1] if eigenvalues[1] > 0 else 0
        is_rectangle = (rectangle and
                           edge_ratio > 0.7 and
                           aspect_ratio < 20 and
                           eigenvalue_ratio > 1.5)  # Rectangle has directional variance
        # At least 3 corners rounded, good edge alignment
        is_rounded_rect = (corners_rounded >= 3 and
                           edge_ratio > 0.7 and
                           aspect_ratio < 20 and
                           eigenvalue_ratio > 1.5)  # Rectangle has directional variance
        
        return is_rounded_rect, is_rectangle

    def analyze_shapes(self, features):
        results = []
        
        for pixels in features:
            # Area is simply the number of pixels in the component
            area = len(pixels)
            
            # Calculate Centroid (Average Y, Average X)
            sum_r = sum(p[0] for p in pixels)
            sum_c = sum(p[1] for p in pixels)
            centroid = (sum_r / area, sum_c / area)
            
            # Calculate Perimeter (Rough estimate: pixels with at least one black neighbor)
            # For simplicity, we'll use a bounding box approach or pixel count
            # A more accurate perimeter uses the outer edge pixels
            perimeter = self.estimate_perimeter(pixels)
            
            # Calculate Euclidean distance from centroid
            # axis=1 calculates the norm for each row (point)
            distances = np.linalg.norm(pixels - np.array(centroid), axis=1)
            radius = np.mean(distances)
            span =  np.var(distances) / radius
            if span < 1:
               circularity = 1 - span
            else:
               circularity = 0
            rounded_rectangle, rectangle = self.is_rounded_rectangle(pixels, tolerance=0.05)
            if rounded_rectangle:
               circularity = 10
            elif rectangle:
                circularity = -10
            results.append(Shape(
                centroid=(int(centroid[0]), int(centroid[1])),
                perimeter=int(perimeter),
                circularity=round(circularity, 3),
                coordinates=pixels
            ))
        return results

    def estimate_perimeter(self, pixels):
        if len(pixels) == 0:
            return 0
    
        # 1. Normalize and move to a grid
        pixels = np.unique(pixels, axis=0)
        min_coords = pixels.min(axis=0)
        shifted_pixels = pixels - min_coords
        
        # Create grid with 1-pixel padding to avoid index errors during shifts
        shape = shifted_pixels.max(axis=0) + 3
        grid = np.zeros(shape, dtype=bool)
        grid[shifted_pixels[:, 0] + 1, shifted_pixels[:, 1] + 1] = True
        
        # 2. Check 4-way neighbors by shifting the grid
        # We look for pixels that are True, but have a False neighbor
        up = grid[:-2, 1:-1]
        down = grid[2:, 1:-1]
        left = grid[1:-1, :-2]
        right = grid[1:-1, 2:]
        center = grid[1:-1, 1:-1]
        
        # A pixel is on the edge if it's True AND any neighbor is False
        # (center) & ~(all neighbors are True)
        interior = up & down & left & right
        edge_mask = center & ~interior
        
        return np.sum(edge_mask)
                
    def plot_contours(self, contours, color=None, linewidth=None, shapes=None):
        if linewidth is None:
          linewidth = 3
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        if len(contours) > 0:
            # Draw lines on original image
            output_img = Image.fromarray(self.img_array)
            draw = ImageDraw.Draw(output_img)
            
            logger.debug("Detected contours:")
            
            color_iter = cycle([
                (0, 255, 0),    # Green
                (255, 0, 0),    # Red
                (0, 0, 255),    # Blue
                (255, 165, 0),  # Orange
                (128, 0, 128),  # Purple
                (0, 255, 255),  # Cyan
                (255, 192, 203),  # Pink
                (165, 42, 42),  # Brown
            ])

            if shapes:
                for shape in shapes:
                   contour = shape.coordinates
                   color = 'red' if shape.is_circle else 'green'
                   if color is None:
                      color = next(color_iter)
                   # contour = np.fliplr(contour)
                   # Draw each segment
                   total_length = 0
                   p0 = contour[0]
                   for p1 in contour[1:]:
                       draw.line([tuple(p0), tuple(p1)], fill=color, width=linewidth)
                       p0 = p1
                       total_length += get_distance(p0, p1)
            else:
                for contour in contours:
                    if color is None:
                       color = next(color_iter)
                    # contour = np.fliplr(contour)
                    # Draw each segment
                    total_length = 0
                    p0 = contour[0]
                    for p1 in contour[1:]:
                        draw.line([tuple(p0), tuple(p1)], fill=color, width=linewidth)
                        p0 = p1
                        total_length += get_distance(p0, p1)
                
                # Print line info
                
                # logger.debug(f"{contour[0]} {len(contour):<10} {total_length:<15.1f}")
            
            # Save marked image
            marked_filename = os.path.join(self.output_dir, 'contours_detected.png')
            output_img.save(marked_filename)
            logger.debug(f"Saved marked image: {marked_filename}")
            
            # Save edges
            edge_filename = os.path.join(self.output_dir, 'edges.png')
            Image.fromarray(self.edges.astype(np.uint8)).save(edge_filename)
            logger.debug(f"Saved edge image: {edge_filename}")
            
    def filter_duplicates(self, shapes, threshold=5.0):
        """ removes shapes with same centroid, leaving the largest
        shape is {'centroid': (1594, 176), 'no_points': 230, 'perimeter': 230, 'circularity': 0.055, 'is_circle': False} """
    
        if not shapes:
            return []
    
        # Sort by size descending so the largest version of a shape is encountered first
        # This makes the comparison logic much cleaner
        sorted_shapes = sorted(shapes, key=attrgetter('no_points'), reverse=True)
        unique_shapes = []
    
        for s in sorted_shapes:
            is_duplicate = False
            c1 = s.centroid
            
            for u in unique_shapes:
                c2 = u.centroid
                # Euclidean distance: sqrt((x2-x1)^2 + (y2-y1)^2)
                dist = math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                
                if dist <= threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_shapes.append(s)
                
        return unique_shapes
        
    def calculate_shape_features(self, coords):
        """Calculate geometric features to identify the shape
        produced by Claude Sonnet 4.5."""
        x, y = coords[:, 0], coords[:, 1]
        # Center the data
        x_center = np.mean(x)
        y_center = np.mean(y)
        x_centered = x - x_center
        y_centered = y - y_center
        
        # Calculate distances from center
        distances = np.sqrt(x_centered**2 + y_centered**2)
        
        # Calculate angles
        angles = np.arctan2(y_centered, x_centered)
        
        # Sort by angle to analyze shape progression
        sorted_indices = np.argsort(angles)
        sorted_distances = distances[sorted_indices]
        sorted_angles = angles[sorted_indices]
        sorted_x = x_centered[sorted_indices]
        sorted_y = y_centered[sorted_indices]
        
        # Feature 1: Coefficient of variation of distances (for circle detection)
        distance_std = np.std(distances)
        distance_mean = np.mean(distances)
        cv_distance = distance_std / distance_mean if distance_mean > 0 else 0
        
        # Feature 2: Aspect ratio (width to height ratio)
        width = np.max(x) - np.min(x)
        height = np.max(y) - np.min(y)
        aspect_ratio = width / height if height > 0 else 0
        
        # Feature 3: Smoothness - check for corners (rectangles have sharp transitions)
        # Calculate second derivative approximation (curvature)
        # Use larger window to reduce noise sensitivity
        window = 10
        if len(sorted_x) > 2 * window:
            # Calculate tangent directions using centered differences
            tangent_angles = []
            for i in range(window, len(sorted_x) - window):
                dx = sorted_x[i + window] - sorted_x[i - window]
                dy = sorted_y[i + window] - sorted_y[i - window]
                tangent_angles.append(np.arctan2(dy, dx))
            
            tangent_angles = np.array(tangent_angles)
            angle_changes = np.abs(np.diff(tangent_angles))
            # Wrap around for angles near ±π
            angle_changes = np.minimum(angle_changes, 2*np.pi - angle_changes)
        else:
            dx = np.diff(sorted_x)
            dy = np.diff(sorted_y)
            angles_diff = np.arctan2(dy, dx)
            angle_changes = np.abs(np.diff(angles_diff))
            angle_changes = np.minimum(angle_changes, 2*np.pi - angle_changes)
        
        max_angle_change = np.max(angle_changes)
        mean_angle_change = np.mean(angle_changes)
        # Std of angle changes - high for rectangles (concentrated corners)
        std_angle_change = np.std(angle_changes)
        
        # Feature 4: Test for four-fold symmetry (rectangles)
        # Check if distances are consistent within quadrants
        quadrant_distances = []
        for i in range(4):
            angle_start = -np.pi + i * np.pi/2
            angle_end = -np.pi + (i+1) * np.pi/2
            mask = (sorted_angles >= angle_start) & (sorted_angles < angle_end)
            if np.sum(mask) > 0:
                quadrant_distances.append(np.mean(sorted_distances[mask]))
        
        if len(quadrant_distances) == 4:
            quadrant_std = np.std(quadrant_distances)
            quadrant_variation = quadrant_std / np.mean(quadrant_distances)
        else:
            quadrant_variation = 0
        
        # Feature 5: Bounding box area vs actual area (rectangularity test)
        # Approximate area using shoelace formula
        area_shoelace = 0.5 * np.abs(np.sum(sorted_x[:-1] * sorted_y[1:] - sorted_x[1:] * sorted_y[:-1]))
        area_bbox = width * height
        area_ratio = area_shoelace / area_bbox if area_bbox > 0 else 0
        
        # Feature 6: Check for corner detection
        # In rectangles, there should be 4 points with high curvature
        # Find peaks in angle changes
        threshold = np.percentile(angle_changes, 95)
        num_corners = np.sum(angle_changes > threshold)
        
        # Feature 7: Teardrop detection - check for asymmetry in end radii
        # Better approach: measure the vertical extent (height) at each end
        # rather than radial distance from center
        
        # Divide shape into segments along x-axis
        x_min_val, x_max_val = np.min(x), np.max(x)
        x_range = x_max_val - x_min_val
        
        # Left 10% of x range (left end)
        left_threshold = x_min_val + 0.1 * x_range
        left_end_mask = x <= left_threshold
        
        # Right 10% of x range (right end)
        right_threshold = x_max_val - 0.1 * x_range
        right_end_mask = x >= right_threshold
        
        # Measure vertical extent at each end
        if np.sum(left_end_mask) > 0:
            left_y_values = y[left_end_mask]
            left_end_height = np.max(left_y_values) - np.min(left_y_values)
        else:
            left_end_height = 0
        
        if np.sum(right_end_mask) > 0:
            right_y_values = y[right_end_mask]
            right_end_height = np.max(right_y_values) - np.min(right_y_values)
        else:
            right_end_height = 0
        
        # Calculate end height ratio (larger / smaller)
        if left_end_height > 0 and right_end_height > 0:
            end_height_ratio = max(left_end_height, right_end_height) / min(left_end_height, right_end_height)
            end_height_asymmetry = abs(left_end_height - right_end_height) / max(left_end_height, right_end_height)
        else:
            end_height_ratio = 1.0
            end_height_asymmetry = 0.0
        
        # Also keep the original radial measurements as backup
        # Divide the shape into left and right halves
        x_mid = (x_max_val + x_min_val) / 2
        
        # Left half
        left_mask = x < x_mid
        left_distances = distances[left_mask]
        left_radius_mean = np.mean(left_distances) if len(left_distances) > 0 else 0
        
        # Right half
        right_mask = x >= x_mid
        right_distances = distances[right_mask]
        right_radius_mean = np.mean(right_distances) if len(right_distances) > 0 else 0
        
        radius_asymmetry = abs(left_radius_mean - right_radius_mean) / max(left_radius_mean, right_radius_mean) if max(left_radius_mean, right_radius_mean) > 0 else 0
        
        return {
            'cv_distance': cv_distance,
            'aspect_ratio': aspect_ratio,
            'max_angle_change': max_angle_change,
            'mean_angle_change': mean_angle_change,
            'std_angle_change': std_angle_change,
            'quadrant_variation': quadrant_variation,
            'area_ratio': area_ratio,
            'num_corners': num_corners,
            'width': width,
            'height': height,
            'mean_distance': distance_mean,
            'radius_asymmetry': radius_asymmetry,
            'end_height_ratio': end_height_ratio,
            'end_height_asymmetry': end_height_asymmetry,
            'left_end_height': left_end_height,
            'right_end_height': right_end_height,
            'left_radius_mean': left_radius_mean,
            'right_radius_mean': right_radius_mean
        }
        
    def identify_teardrop(self, features, min_size_ratio=0.003, stats=False):
        """Identify the a teardrop based on calculated features.
        modified from AI Claude Sonnet 4.5 code to only find
        teardrop of large enough size"""
        
        cv = features['cv_distance']
        aspect_ratio = features['aspect_ratio']
        max_angle = features['max_angle_change']
        std_angle = features['std_angle_change']
        area_ratio = features['area_ratio']
        num_corners = features['num_corners']
        end_height_ratio = features['end_height_ratio']
        end_height_asymmetry = features['end_height_asymmetry']
        radius_asymmetry = features['radius_asymmetry']
        area = features['width'] * features['height']
        image_area = np.prod(self.img_array.shape[:2])
        image_area_ratio = area / image_area
        if stats:
            print("\n" + "="*70)
            print("SHAPE IDENTIFICATION USING NUMPY")
            print("="*70)
            print("\nGeometric Features Calculated:")
            print(f"  {'Feature':<30} {'Value':<15} {'Interpretation'}")
            print(f"  {'-'*30} {'-'*15} {'-'*25}")
            print(f"  {'Coefficient of Variation':<30} {cv:.4f}{'':>11} {'Distance consistency'}")
            print(f"  {'Aspect Ratio (W/H)':<30} {aspect_ratio:.4f}{'':>11} {'Shape elongation'}")
            print(f"  {'Max Angle Change':<30} {max_angle:.4f}{'':>11} {'Corner sharpness'}")
            print(f"  {'Std Angle Change':<30} {std_angle:.4f}{'':>11} {'Curvature variance'}")
            print(f"  {'Image Area Ratio (Shape/BBox)':<30} {image_area_ratio:.4f}{'':>11} {'Space filling'}")
            print(f"  {'Area Ratio (Shape/BBox)':<30} {area_ratio:.4f}{'':>11} {'Space filling'}")
            print(f"  {'Number of Corners':<30} {num_corners:<15} {'Sharp transitions'}")
            print(f"  {'End Height Ratio':<30} {end_height_ratio:.4f}{'':>11} {'End asymmetry'}")
            print(f"  {'End Height Asymmetry %':<30} {end_height_asymmetry:.4f}{'':>11} {'Vertical extent diff'}")
            print(f"  {'Radius Asymmetry':<30} {radius_asymmetry:.4f}{'':>11} {'Left vs Right'}")
            print(f"  {'Left End Height':<30} {features['left_end_height']:.2f}{'':>11}")
            print(f"  {'Right End Height':<30} {features['right_end_height']:.2f}{'':>11}")
            print(f"  {'Width':<30} {features['width']:.2f}{'':>11}")
            print(f"  {'Height':<30} {features['height']:.2f}{'':>11}")
            
            print("\n" + "-"*70)
            print("CLASSIFICATION LOGIC:")
            print("-"*70)
        
        # Decision thresholds
        # Rectangles have very high std (concentrated corners at 90 degrees) and high area ratio
        RECTANGLE_STD_ANGLE_THRESHOLD = 0.5  # Very high std indicates 4 concentrated corners
        MINIMUM_AREA_RATIO = min_size_ratio
        ELLIPSE_ASPECT_THRESHOLD = 1.5
        # Teardrop has asymmetric ends - use vertical height measurements
        TEARDROP_HEIGHT_RATIO_THRESHOLD = 1.5  # One end at least 50% taller than the other
        TEARDROP_HEIGHT_ASYMMETRY_THRESHOLD = 0.20  # At least 20% difference in end heights
        
        # Classify
        # Teardrop: elongated with asymmetric end heights
        is_teardrop = (image_area_ratio > MINIMUM_AREA_RATIO and
                        aspect_ratio > ELLIPSE_ASPECT_THRESHOLD and
                       std_angle < RECTANGLE_STD_ANGLE_THRESHOLD and
                       (end_height_ratio > TEARDROP_HEIGHT_RATIO_THRESHOLD or
                        end_height_asymmetry > TEARDROP_HEIGHT_ASYMMETRY_THRESHOLD))                

        if stats:
            print("\nTeardrop Test:")
            print(f"  • Image Area ratio? area_ratio = {image_area_ratio:.4f} > {MINIMUM_AREA_RATIO}")
            print(f"  • Elongated? aspect_ratio = {aspect_ratio:.4f} > {ELLIPSE_ASPECT_THRESHOLD} = {aspect_ratio > ELLIPSE_ASPECT_THRESHOLD}")
            print(f"  • Smooth curves? std_angle = {std_angle:.4f} < {RECTANGLE_STD_ANGLE_THRESHOLD} = {std_angle < RECTANGLE_STD_ANGLE_THRESHOLD}")
            print(f"  • Asymmetric end heights? end_height_ratio = {end_height_ratio:.4f} > {TEARDROP_HEIGHT_RATIO_THRESHOLD} = {end_height_ratio > TEARDROP_HEIGHT_RATIO_THRESHOLD}")
            print(f"  • OR end_height_asymmetry = {end_height_asymmetry:.4f} > {TEARDROP_HEIGHT_ASYMMETRY_THRESHOLD} = {end_height_asymmetry > TEARDROP_HEIGHT_ASYMMETRY_THRESHOLD}")
            print(f"  → Is Teardrop: {is_teardrop}")
                        
            print("\n" + "="*70)
            print("FINAL IDENTIFICATION:")
            print("="*70)
        
        if is_teardrop:
            shape = "TEARDROP"
            reasoning = [
                f"Significantly elongated (aspect ratio {aspect_ratio:.2f}:1)",
                f"Asymmetric ends: height ratio = {end_height_ratio:.2f}:1",
                f"Left end height: {features['left_end_height']:.1f}, Right end height: {features['right_end_height']:.1f}",
                f"One end is {end_height_asymmetry:.1%} larger than the other",
                f"Smooth, continuous curves (std angle = {std_angle:.4f})",
                "Rounded at one end, more pointed at the other"
            ]
        
        else:
            shape = "UNKNOWN/IRREGULAR"
            reasoning = ["Shape doesn't match standard geometric forms"]
        if stats:
            print(f"\n✓ Shape Identified: {shape}\n")
            print("Reasoning:")
            for i, reason in enumerate(reasoning, 1):
                print(f"  {i}. {reason}")
            
            print("\n" + "="*70 + "\n")
        
        return shape
    

def get_shapes(file_path):
    image_path = file_path
    output_dir = 'output'
    canny_low = 0.5  # Lower = more edges (more noise)
    canny_high = 0.2  # Lower = more edges (more noise)
    min_contour_length = 100
    max_contour_length = None
    
    image_process = FeatureExtract(image_path, output_dir,
                                   canny_low, canny_high)
    
    detector = FastContourDetector(image_process=image_process)
    logger.debug("Finding ordered contours...")
    ordered_contours = detector.find_all_contours_ordered(min_contour_length,
                                                          max_contour_length)
    shapes = detector.analyze_shapes(ordered_contours)
    shapes = detector.filter_duplicates(shapes, threshold=10)
    contours = [shape.coordinates for shape in shapes]
    detector.plot_contours(contours, shapes=shapes, linewidth=8)
    logger.debug(f"Found {len(ordered_contours)} ordered contours")
    
    logger.debug(f"Found {len(contours)} filtered contours")
    for i, shape in enumerate(shapes):
        rotated, eigenvalues = detector.pca(shape.coordinates)
        features = detector.calculate_shape_features(rotated)
        if detector.identify_teardrop(features, stats=False) == 'TEARDROP':
            shape.shape = 'teardrop'
        image = image_process.crop_image(shape.coordinates)
        shape.image = image
        shape.image_size = image.size
        shape.color_names = image_process.closest_colors(image)
        shape.quadrant = '_'.join(image_process.quadrant(shape.centroid))
        shape.description = f"{shape.quadrant} {shape.color_names} {shape.shape}"
        logger.debug(f'{shape.circularity}')
        logger.debug(f"{i}: {shape}")
        image.show()
    # marked_filename = os.path.join(output_dir, 'contours_detected.png')
    # console.quicklook(marked_filename)
    return shapes
    
                                                                                                                                                                                                                          
def main():

    image_path = 'pinball3.png'
    # min_radius = 15      # Smallest circle to detect
    # max_radius = 120     # Largest circle to detect
    # line_threshold = 100
    # circle_threshold = 20     # Adaptive (recommended)
    # arc_threshold = 18
    # min_dist = 100
    # min_arc_angle = 60     # At least 60Â° arc
    # max_arc_angle = 330    # Up to 330Â° (almost complete)
    # max_coverage = 0.5     # Max 90% complete to be an arc
    output_dir = 'output'
    canny_low = 0.5
    canny_high = 0.2
    # min_line_length = 150
    # max_line_gap = 10

    # canny_low=0.05,    # Lower = more edges (more noise)
    # canny_high=0.15    # Lower = more edges (more noise)
    image_process = FeatureExtract(image_path, output_dir,
                                   canny_low, canny_high)
    """
    detector = LineDetector(image_process=image_process)
                         
    lines = detector.extract_lines(min_line_length, max_line_gap, threshold=line_threshold)
    detector.plot_lines(lines, color='green', linewidth=10)
    
    # Use adaptive threshold (best for most cases)
    # For high-quality images with clear circle threshold=15
    # For noisy/fragmented circles threshold=8
    # For very clean, complete circles only threshold=25
    circle_detector = CircleDetector(image_process=image_process)
    circles = circle_detector.extract_circles(
        min_radius,      # Smallest circle to detect
        max_radius,     # Largest circle to detect
        circle_threshold,     # Adaptive (recommended)
        min_dist         # Min distance between centers
    )
    circle_detector.plot_circles(circles, linewidth=5)
   
    detector = ArcDetector(image_process=image_process)
    t = time()
    arcs = detector.extract_arcs(
        min_radius,
        max_radius,
        arc_threshold,          # Low threshold to catch partial circles
        min_arc_angle,     # At least 60Â° arc
        max_arc_angle,    # Up to 330Â° (almost complete)
        max_coverage,    # Max 90% complete to be an arc
        min_dist,
        circle_detector=circle_detector
    )
    detector.plot_arcs(arcs)
    logger.debug(f'Arc detection: {time()-t:.2f}s')
    """
    detector = FastContourDetector(image_process=image_process)
    logger.debug("Finding ordered contours...")
    ordered_contours = detector.find_all_contours_ordered(min_contour_length=130,
                                                          max_contour_length=None)
    shapes = detector.analyze_shapes(ordered_contours)
    shapes = detector.filter_duplicates(shapes)
    contours = [shape.coordinates for shape in shapes]
    detector.plot_contours(contours, shapes=shapes, linewidth=8)
    logger.debug(f"Found {len(ordered_contours)} ordered contours")
    
    logger.debug(f"Found {len(contours)} filtered contours")
    for i, shape in enumerate(shapes):
        image = image_process.crop_image(shape.coordinates)
        shape['image'] = image
        shape['image_size'] = image.size
        logger.debug(f"{i}: {shape.centroid=}, {shape.perimeter=}, {shape.circularity=}, {shape.is_circle=} {shape.image_size=}")
        image.show()
    marked_filename = os.path.join(output_dir, 'contours_detected.png')
    console.quicklook(marked_filename)
    
    
    return shapes
    
    
if __name__ == '__main__':
   #for i in range(1,7):
   #   get_shapes(f'pinball{i}.png' )
   # main()
   cProfile.run('get_shapes("pinball1.png")', sort='cumulative')
"""
Common Issues
“No circles detected”
  1.  Check edge image: output/edges.png
  • Are circle edges visible?
  • If not, adjust canny_low and canny_high
  2.  Lower threshold: Try threshold=5
  3.  Adjust radius range to match your circles
  4.  Check image quality (blur, noise, occlusion)
“Too many circles detected”
  1.  Raise threshold: Try threshold=15 or higher
  2.  Increase min_dist
  3.  Narrow radius range
  4.  Improve edge detection (higher Canny thresholds)
“Circles in wrong locations”
  • Edge detection may be finding other circular features
  • Check edges.png to verify circle edges are clean
  • Adjust Canny parameters for better edge quality
Performance Notes
Circle detection is computationally intensive:
  • Time increases with: (max_radius - min_radius) × num_edge_points
  • For large images or wide radius ranges, expect 10-60 seconds
  • The vectorized implementation is already optimized
"""

