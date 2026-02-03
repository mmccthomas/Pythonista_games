# read a spritesheet (irregular) and extract coordinates of each sprite
# they are ordered in y then x
# need to loose sort so that small differences in y do not affect order
import os
from PIL import Image, ImageDraw
import numpy as np
from scene import Rect
from collections import defaultdict
from operator import itemgetter
#take a spritesheet and decode the sprites

    
def flatten_to_strings(listOfLists):
    """Flatten a list of (lists of (lists of strings)) for any level 
    of nesting"""
    result = []

    for i in listOfLists:
        # Only append if i is a basestring (superclass of string)
        if isinstance(i, str):
            result.append(i)
        # Otherwise call this function recursively
        else:
            result.extend(flatten_to_strings(i))
    return result



def find_connected_components(binary_mask):
    """
    Finds connected components in a binary mask using a two-pass algorithm.
    Returns a labeled array and a list of bounding box (slice) objects.
    """
    height, width = binary_mask.shape
    labeled_array = np.zeros_like(binary_mask, dtype=int)
    next_label = 1
    
    # Store equivalences (label -> parent label in a disjoint set)
    # Using a simple list for parent array. parent[i] is the parent of label i.
    # We will use 0 for background, so labels start from 1.
    parent = [0] # parent[0] is unused, parent[1] refers to label 1, etc.

    def find_root(label_id):
        """Finds the root of a label's set (path compression)."""
        root = label_id
        while parent[root] != root:
            root = parent[root]
        # Path compression: make all nodes on the path point directly to the root
        current = label_id
        while parent[current] != root:
            next_node = parent[current]
            parent[current] = root
            current = next_node
        return root

    def union_sets(label1, label2):
        """Unites two sets by linking their roots."""
        root1 = find_root(label1)
        root2 = find_root(label2)
        if root1 != root2:
            # Union by rank/size could be added for efficiency, but simple union is fine for demonstration
            parent[max(root1, root2)] = min(root1, root2) # Merge larger into smaller root
            return True
        return False

    # Pass 1: Labeling and recording equivalences
    for y in range(height):
        for x in range(width):
            if binary_mask[y, x]: # If it's a foreground pixel
                neighbors_labels = set()

                # Check 8-connectivity (top, left)
                if y > 0 and x>0 and labeled_array[y - 1, x-1] != 0:            # Top left neighbor
                    neighbors_labels.add(labeled_array[y - 1, x-1])
                if y > 0 and labeled_array[y - 1, x] != 0: # Top neighbor
                    neighbors_labels.add(labeled_array[y - 1, x])
                if y > 0 and x<width-1 and labeled_array[y - 1, x+1] != 0:            # Top right neighbor
                    neighbors_labels.add(labeled_array[y - 1, x+1])   
                if x > 0 and labeled_array[y, x - 1] != 0: # Left neighbor
                    neighbors_labels.add(labeled_array[y, x - 1])
                    
                
                
                
                # Check 8-connectivity (top-left, top-right, bottom-left, bottom-right) if desired
                # This makes components "stickier" and can merge more shapes.
                # For sprite sheets, 4-connectivity is often sufficient to avoid merging thin gaps.
                # If your sprites can be separated by a single pixel, stick to 4-connectivity.
                # If they can be separated by a diagonal gap of background, use 8-connectivity.
                # Here, we'll keep it simple with 4-connectivity for clarity and common use.

                if not neighbors_labels: # No labeled neighbors, assign a new label
                    next_label += 1
                    parent.append(next_label - 1) # Each new label is initially its own root
                    labeled_array[y, x] = next_label - 1
                else: # Has labeled neighbors
                    min_neighbor_label = min(neighbors_labels)
                    labeled_array[y, x] = min_neighbor_label
                    for label_id in neighbors_labels:
                        if label_id != min_neighbor_label:
                            union_sets(min_neighbor_label, label_id)

    # Resolve equivalences
    final_labels_map = {} # Map temporary label to final canonical label
    for i in range(1, next_label): # Iterate through all labels assigned in pass 1
        root = find_root(i)
        if root not in final_labels_map:
            final_labels_map[root] = len(final_labels_map) + 1 # Assign new consecutive labels
        final_labels_map[i] = final_labels_map[root] # Map all equivalent labels to this canonical one

    # Pass 2: Relabeling and collecting bounding boxes
    final_labeled_array = np.zeros_like(binary_mask, dtype=int)
    
    # Track min/max coordinates for each final label
    # Initialise with values that will be easily overwritten
    min_x = {v: width for v in final_labels_map.values()}
    max_x = {v: -1 for v in final_labels_map.values()}
    min_y = {v: height for v in final_labels_map.values()}
    max_y = {v: -1 for v in final_labels_map.values()}

    for y in range(height):
        for x in range(width):
            temp_label = labeled_array[y, x]
            if temp_label != 0: # If it's a foreground pixel that was labeled
                final_label = final_labels_map[temp_label]
                final_labeled_array[y, x] = final_label

                # Update bounding box coordinates
                min_x[final_label] = min(min_x[final_label], x)
                max_x[final_label] = max(max_x[final_label], x)
                min_y[final_label] = min(min_y[final_label], y)
                max_y[final_label] = max(max_y[final_label], y)

    # Prepare bounding box slices
    bounding_boxes = []
    # Sort labels to ensure consistent output order if desired, though not strictly necessary
    sorted_labels = sorted([label_val for label_val in final_labels_map.values() if label_val != 0])
    
    for label_val in sorted_labels:
        if label_val != 0: # Ensure we don't process background
            # Add 1 to max_x and max_y for slice object as slice upper bounds are exclusive
            bbox = (min_x[label_val], min_y[label_val], max_x[label_val] + 1, max_y[label_val] + 1)
            bounding_boxes.append(bbox)

    return final_labeled_array, bounding_boxes

def loose_sort(boxes, tolerance=4):
    # sort the boxes so that they appear in correct order of y then x, allowing for small
    # differences in y
    """
    Args:
        data: A list of tuples, where each tuple is an (x, y) pair.
        tolerance: The maximum allowable difference in y-coordinates for grouping.

    Returns:
        A new list containing the sorted (x, y) pairs.
    """
    def key_func(item):
        x, y, w, h = item
        return (int(tolerance*(y +1)/ 32), x)  # Group by y and integer part of y/tolerance

    return sorted(boxes, key=key_func)
    

def separate_irregular_sprites(sprite_sheet_path, 
                                              min_sprite_area=100, background_color=None,
                                              threshold_value=200, invert_threshold=True,
                                              use_alpha=True,
                                              sprite_names=None):
    """
    Separates individual sprites from a sprite sheet with irregular spacing using Pillow and NumPy,
    implementing connected components labeling manually.

    Args:
        sprite_sheet_path (str): Path to the input sprite sheet image.
        min_sprite_area (int): Minimum pixel area for a detected sprite.
                                  Adjust this to filter out noise.
        background_color (tuple, optional): A tuple (R, G, B) or (R, G, B, A) representing the
                                            background color to be treated as background.
                                            If None, it tries to detect transparent background
                                            or uses grayscale thresholding.
        threshold_value (int): Grayscale threshold value (0-255) for background detection
                                  if no transparent or specific background color is given.
        invert_threshold (bool): If True, pixels *below* threshold_value are considered sprites
                                 (useful for dark sprites on light backgrounds). If False,
                                 pixels *above* threshold_value are sprites.
    """
    
    try:
        original_img = Image.open(sprite_sheet_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Could not load image from {sprite_sheet_path}")
        return

    img_array = np.array(original_img)
    
    # 1. Create a binary mask for the sprites
    # Mask will be True for foreground (sprite) pixels, False for background
    binary_mask = np.zeros(img_array.shape[:2], dtype=bool)

    if original_img.mode == 'RGBA' and use_alpha:
        alpha_channel = img_array[:, :, 3]
        binary_mask = alpha_channel > 0
    elif background_color is not None:
        if len(background_color) == 3: # RGB background color
            bg_color_arr = np.array(background_color, dtype=np.uint8)
            binary_mask = ~np.all(img_array[:, :, :3] == bg_color_arr, axis=-1)
        elif len(background_color) == 4: # RGBA background color
            bg_color_arr = np.array(background_color, dtype=np.uint8)
            binary_mask = ~np.all(img_array == bg_color_arr, axis=-1)
        else:
            print(f"Warning: Invalid background_color format: {background_color}. Falling back to thresholding.")
            gray_img = original_img.convert('L')
            gray_array = np.array(gray_img)
            binary_mask = gray_array < threshold_value if invert_threshold else gray_array > threshold_value
    else:
        gray_img = original_img.convert('L')
        gray_array = np.array(gray_img)
        binary_mask = gray_array < threshold_value if invert_threshold else gray_array > threshold_value
    
    # 2. Find Connected Components
    # We pass the boolean mask to our custom connected components function
    #nclasses, labels = partition(~binary_mask.astype(int), 1)
    labeled_array, bounding_boxes = find_connected_components(binary_mask)

    if not bounding_boxes:
        print("No sprites detected after connected components labeling. Adjust mask parameters.")
        return

    # 3. Extract and Save Sprites
    sprite_count = 0
    boxes = defaultdict()
    
    for bbox in bounding_boxes:
        x_min, y_min, x_max, y_max = bbox # These are PIL crop coordinates

        width = x_max - x_min
        height = y_max - y_min

        if (width * height) < min_sprite_area:
            continue
        boxes[Rect(x_min, y_min, width, height)] = original_img.crop(bbox)
        
        #output_filename = os.path.join(output_dir, f"sprite_{sprite_count:04d}.png")
        #sprite_image.save(output_filename)
        #print(f"Saved {output_filename}")
        sprite_count += 1
    
    keys = loose_sort(boxes)
    sorted_boxes =  {k: boxes[k] for k in keys}
    if sprite_count == 0:
        print("No sprites detected after filtering by min_sprite_area. Adjust 'min_sprite_area'.")
    else:
        if sprite_names:
           sprite_names = flatten_to_strings(sprite_names)
           for i, (box, image) in enumerate(sorted_boxes.items()):
               print(sprite_names[i], box)
               image.show()
        else:
             for i, (box, image) in enumerate(sorted_boxes.items()):
               print(i, box)
               image.show()
    return sorted_boxes, sprite_names
        
        
# --- How to use the function (same dummy data as before) ---
if __name__ == "__main__":
    NAME = 'defender.png'
    #NAME = 'image.png'

    sprite_names = ['mutant1', 'mutant2',
    'podexpl','swarmexpl',  
    'pod1', 'pod2',
    'humanoid1', 
    [f'bomber{i}' for i in range(1,6)],
    'purple circle',
    [f'bomb{i}' for i in range(1,5)], 
    'swarmer1', 'swarmer2',   
    [f'lander{i}' for i in range(1,4)],
    [f'bomber{i}' for i in range(6,9)],
    [f'lander{i}' for i in range(4,7)],
    [f'baiter{i}' for i in range(1,7)],
    'ship1', 'ship2',
    'ship3', 'ship4',   
    'littleship',
    'smartbomb',
    '2', '5', '0',
    '2', '5', '0',
    '500', '10', '00',
    '500', '10', '00', 
    [f'largefont{i}' for i in range(10)],
    '?',
    [f'largefont{i.upper()}' for i in 'abcdefghijklmnopqrstuvwxyz']]
      
    separate_irregular_sprites(NAME,
                               background_color=(0, 0, 0),
                               use_alpha=False, sprite_names=sprite_names)
