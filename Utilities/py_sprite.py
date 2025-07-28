import console
import scene
import photos
import clipboard
import ui
import io
import os.path
from PIL import Image, ImageColor
import numpy as np
import math
from collections import deque
from pathlib import Path
import dialogs  # For file picking in Program 2's style
import File_Picker # Assuming this is a custom file picker module

# --- Helper functions from Program 1 ---
def pil_to_ui(img):
  with io.BytesIO() as bIO:
    img.save(bIO, 'png')
    return ui.Image.from_data(bIO.getvalue())
  
def ui_to_pil(img):
  return Image.open(io.BytesIO(img.to_png()))
  
def crop_image(image_data_np):
  """
  Crops a NumPy array image to its non-empty content.
  Assumes input is a 3D NumPy array (height, width, channels).
  """
  image_data_bw = image_data_np.max(axis=2) # Get max value across color channels for BW check

  non_empty_columns = np.where(image_data_bw.max(axis=0)>0)[0]
  non_empty_rows = np.where(image_data_bw.max(axis=1)>0)[0]

  if non_empty_rows.size == 0 or non_empty_columns.size == 0:
      return image_data_np # Return original if entirely empty

  cropBox = (min(non_empty_rows), max(non_empty_rows), min(non_empty_columns), max(non_empty_columns))
  image_data_new = image_data_np[cropBox[0]:cropBox[1]+1, cropBox[2]:cropBox[3]+1 , :]
  return image_data_new

# Helper function to find a subview by name (from Program 1)
def find_subview_by_name(parent_view, name):
    if not parent_view:
        return None
    for subview in parent_view.subviews:
        if hasattr(subview, 'name') and subview.name == name:
            return subview
    return None

# --- Program 2's Helper Functions ---
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
      p = np.cumsum(np.append(0, z))[:-1]  # positions
      return (z, p, ia[i])

def rgba_to_single_value(rgba_array):
   """
   Converts a NumPy 3D array of N x M x [r, g, b, a] (or [r, g, b])
   to an N x M 2D array of combined integer values.
   This allows for easy comparison of pixel values regardless of individual channels.
   Assumes 0-255 range for channel values.
   """
   if rgba_array.ndim != 3:
       raise ValueError("Input array must be 3-dimensional (N x M x Channels).")
   
   N, M, C = rgba_array.shape
   
   if C not in [1, 3, 4]:
       raise ValueError("Last dimension must be 1 (L), 3 (RGB) or 4 (RGBA).")
   
   if rgba_array.dtype != np.uint8:
       rgba_array = rgba_array.astype(np.uint8)
   
   if C == 4: # RGBA
       # Combine into a single 32-bit integer: RRGGBBAA
       result_array = (rgba_array[:, :, 0].astype(np.uint32) << 24) | \
                      (rgba_array[:, :, 1].astype(np.uint32) << 16) | \
                      (rgba_array[:, :, 2].astype(np.uint32) << 8) | \
                      (rgba_array[:, :, 3].astype(np.uint32))
   elif C == 3: # RGB (assume opaque alpha 255)
       # Combine into a single 32-bit integer: RRGGBBFF
       result_array = (rgba_array[:, :, 0].astype(np.uint32) << 24) | \
                      (rgba_array[:, :, 1].astype(np.uint32) << 16) | \
                      (rgba_array[:, :, 2].astype(np.uint32) << 8) | \
                      255
   elif C == 1: # Grayscale (assume opaque alpha 255 and replicate to RGB)
       # Combine into a single 32-bit integer: 0xLLLLLLFF
       val = rgba_array[:, :, 0].astype(np.uint32)
       result_array = (val << 24) | (val << 16) | (val << 8) | 255 # Replicate LLL and add FF alpha
   return result_array

class PixelEditor(ui.View):
  def did_load(self):
    # Initial grid size
    self.grid_width = 16
    self.grid_height = 16
    self.base_pixel_size = 10 # The intended size of one grid pixel without any scaling
    
    self.current_scale = 1.0 # This is now the 'zoom' from Program 2
    self.min_scale = 1.0
    self.max_scale = 16.0 # Max zoom level (increased from original 5.0)
    
    # --- Zoom/Pan related variables ---
    self.offset_x = 0 # Pan offset in screen pixels
    self.offset_y = 0 # Pan offset in screen pixels
    self.initial_touch_location = None # Initial touch location for panning
    self.moved = False # Flag to distinguish tap from pan/drag
    self.multitouch_enabled = True # Enable multitouch for zoom
    self.touches = {} # Store multiple touches for pinch-zoom
    self.initial_dist = None
    self.initial_center = None
    
    # Define padding for the grid drawing area
    self.grid_padding_x = 0 # These paddings are for drawing, not for UI layout
    self.grid_padding_y = 0 # The PixelEditor's frame defines its drawing area

    # Initialize the pixel data with a default color (e.g., transparent)
    # Stored as RGBA tuples (0.0-1.0) for ui.set_color
    self.pixel_data = [[(0, 0, 0, 0) for _ in range(self.grid_width)] for _ in range(self.grid_height)]
    self.undo_stack = deque() # For undo functionality, storing pixel_data states

    self.current_color = (0, 0, 0, 1) # Default drawing color (red from Program 2, but using rgba tuple)
    self.mode = self.pencil # Default mode (pencil, eraser, color_picker, fill)
    self.auto_crop_image = False # From Program 1
    self.fillmode = False # From Program 2
    self.loaded_image_path = None # To store path of loaded image for title bar
    
    
    # --- NEW: Cut and Paste variables ---
    self.selection_start = None # Stores (x,y) of selection drag start
    self.selection_end = None   # Stores (x,y) of selection drag end
    self.selection_rect = None  # Stores final selection as (x, y, w, h)
    self.clipboard_buffer = None # Stores the cut pixel data
    self.last_touch_grid_pos = (0, 0) # For paste preview position
    # Call reset to properly set up the initial grid and image views
    self.reset(self.grid_width, self.grid_height)
    
    # These are placeholder views. Actual drawing happens in self.draw()
    # No need for separate image_view and grid_layout subviews, as all drawing is direct.
    
  def has_image(self):
    return any(color != (0,0,0,0) for row in self.pixel_data for color in row)

  def get_image(self):
    """
    Converts the internal pixel_data to a PIL Image and applies cropping if auto_crop_image is True.
    """
    # Create a new PIL Image from pixel_data
    img_pil = Image.new('RGBA', (self.grid_width * self.base_pixel_size, 
                                 self.grid_height * self.base_pixel_size),
                                  (0, 0, 0, 0)) # Start with transparent background
    pixels = img_pil.load()

    for y_grid in range(self.grid_height):
        for x_grid in range(self.grid_width):
            color_rgba_float = self.pixel_data[y_grid][x_grid]
            
            # Convert float RGBA (0.0-1.0) to int RGBA (0-255)
            color_rgba_int = tuple(int(c * 255) for c in color_rgba_float)
            
            # Fill the N x N block for each grid pixel
            for dy in range(self.base_pixel_size):
                for dx in range(self.base_pixel_size):
                    pixels[x_grid * self.base_pixel_size + dx, y_grid * self.base_pixel_size + dy] = color_rgba_int

    if self.auto_crop_image:
      # Convert PIL Image to NumPy array for cropping
      np_image = np.array(img_pil)
      cropped_np_image = crop_image(np_image)
      # Convert back to PIL Image then ui.Image
      return pil_to_ui(Image.fromarray(cropped_np_image))
    
    return pil_to_ui(img_pil)

  def add_history(self):
    # Store a deep copy of the current pixel_data for undo
    if not self.undo_stack or [row[:] for row in self.pixel_data] != self.undo_stack[-1]: # Only add if different
        self.undo_stack.append([row[:] for row in self.pixel_data])
        # Limit undo stack size (e.g., last 20 states)
        if len(self.undo_stack) > 20:
            self.undo_stack.popleft()

  def undo(self):
    if len(self.undo_stack) > 1: # Need at least two states to undo (current + previous)
      self.pixel_data = self.undo_stack.pop() # Revert to previous state
      self.set_needs_display()
      # Update preview after undo
      toolbar = find_subview_by_name(self.superview, 'toolbar')
      if toolbar:
          toolbar.preview(None) # Force update preview
          
  # --- NEW: Cut Action Button ---
  def cut(self, x_grid, y_grid):
    if not self.pixel_editor:
        self.show_error()
        return
    
    self.add_history()
    self.pixel_editor.cut_selection()
    self.preview(None) # Update preview after cutting

  def pencil(self, x_grid, y_grid):
    if self.pixel_data[y_grid][x_grid] != self.current_color:
      self.add_history()
      self.pixel_data[y_grid][x_grid] = self.current_color
      self.set_needs_display()

  def eraser(self, x_grid, y_grid):
    if self.pixel_data[y_grid][x_grid] != (0,0,0,0): # If not already transparent
      self.add_history()
      self.pixel_data[y_grid][x_grid] = (0, 0, 0, 0) # Transparent
      self.set_needs_display()

  def color_picker(self, x_grid, y_grid):
    picked_color = self.pixel_data[y_grid][x_grid]
    r, g,b, a = picked_color
    colors_view = find_subview_by_name(self.superview, 'colors')
    if colors_view:
        colors_view.set_color(picked_color) # Update the color view
        self.current_color = picked_color # Also update editor's current color
        console.hud_alert(f'Picked color: {r:.2f},{g:.2f},{b:.2f},{a:.2f}', 'info', 0.8) # Provide feedback
  
  # --- NEW: Selection and Paste Tool Modes ---
  def select_area(self, x_grid, y_grid):
    # This is a placeholder. The logic is in touch handlers.
    pass
    
  @ui.in_background     
  def paste_tool(self, x_grid, y_grid):
    # This method finalizes the paste operation.
    if self.clipboard_buffer is None:
        console.hud_alert('Clipboard is empty.', 'error', 0.8)
        return

    self.add_history()
    buffer_height = len(self.clipboard_buffer)
    buffer_width = len(self.clipboard_buffer[0])

    for r in range(buffer_height):
        for c in range(buffer_width):
            paste_y = y_grid + r
            paste_x = x_grid + c
            # Bounds check to avoid pasting outside the grid
            if 0 <= paste_y < self.grid_height and 0 <= paste_x < self.grid_width:
                color = self.clipboard_buffer[r][c]
                # Only paste non-transparent pixels to allow layering
                if color[3] > 0: 
                    self.pixel_data[paste_y][paste_x] = color
    self.set_needs_display()

  # --- NEW: Cut Action ---
  @ui.in_background    
  def cut_selection(self):
    if self.selection_rect is None:
        console.hud_alert('No area selected.', 'error', 0.8)
        return
    
    toolbar_view_instance.buttons['paste_tool'].enabled = True
    toolbar_view_instance.buttons['paste_tool'].tint_color = 'black'
    self.add_history()
    x, y, w, h = self.selection_rect
    
    # Copy the selected area to the clipboard buffer
    self.clipboard_buffer = [[self.pixel_data[r][c] for c in range(x, x + w)] for r in range(y, y + h)]

    # Erase the selected area from the pixel data
    for r in range(y, y + h):
        for c in range(x, x + w):
            self.pixel_data[r][c] = (0, 0, 0, 0) # Transparent
            
    console.hud_alert(f'Cut {w}x{h} area to clipboard.', 'success', 0.8)
    
    # Clear the selection and redraw
    self.selection_rect = None
    self.selection_start = None
    self.selection_end = None
    self.set_needs_display()
    
  # --- NEW: Copy Action ---
  @ui.in_background    
  def copy_selection(self):
    if self.selection_rect is None:
        console.hud_alert('No area selected.', 'error', 0.8)
        return
    toolbar_view_instance.buttons['paste_tool'].enabled = True
    toolbar_view_instance.buttons['paste_tool'].tint_color = 'black'
    self.add_history()
    x, y, w, h = self.selection_rect
    
    # Copy the selected area to the clipboard buffer
    self.clipboard_buffer = [[self.pixel_data[r][c] for c in range(x, x + w)] for r in range(y, y + h)]
    
    console.hud_alert(f'Copy {w}x{h} area to clipboard.', 'success', 0.8)
    
    # Clear the selection and redraw
    self.selection_rect = None
    self.selection_start = None
    self.selection_end = None
    self.set_needs_display()
    
  @ui.in_background      
  def add_circle(self):
      # add a user defined circle
      fields = [  
      {'type': 'number', 'key': 'x', 'value': str(self.grid_width//2), 'title': 'X'},
      {'type': 'number', 'key': 'y', 'value': str(self.grid_height//2), 'title': 'Y'},
      {'type': 'number', 'key': 'radius', 'value': str(5), 'title': 'Radius'}]
      values = dialogs.form_dialog(title='Circle centre and radius', fields=fields)
      if values:
          r = int(values['radius'])
          self.add_history()
          n_segs = 200
          for i in range(n_segs):
            x_grid = round(r * math.cos(2 * math.pi * i / n_segs) + int(values['x']))
            y_grid = round(r * math.sin(2 * math.pi * i / n_segs) + int(values['y']))
            x_grid = max(0, min(x_grid, self.grid_width - 1))
            y_grid = max(0, min(y_grid, self.grid_height - 1))
            
            self.pixel_data[y_grid][x_grid] = self.current_color            
          self.set_needs_display()
      
   
  def flood_fill(self, start_x, start_y, replacement_color):
    """
    Performs a flood fill operation on the pixel_data grid.
    """
    target_color = self.pixel_data[start_y][start_x]
    if target_color == replacement_color:
        return # No need to fill if already the replacement color

    self.add_history() # Add state before filling

    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    q = deque()
    q.append((start_x, start_y))            

    while q:
        curr_x, curr_y = q.popleft()    
        if self.pixel_data[curr_y][curr_x] == target_color:
            self.pixel_data[curr_y][curr_x] = replacement_color
            for dx, dy in directions:
                new_x, new_y = curr_x + dx, curr_y + dy   
                if 0 <= new_y < self.grid_height and 0 <= new_x < self.grid_width:
                    if self.pixel_data[new_y][new_x] == target_color:
                        q.append((new_x, new_y))
    self.set_needs_display()
    
  @ui.in_background
  def reset(self, width=None, height=None):
    # Update grid dimensions
    self.grid_width = width or self.grid_width
    self.grid_height = height or self.grid_height
    
    # Reset pixel data to transparent
    self.pixel_data = [[(0, 0, 0, 0) for _ in range(self.grid_width)] for _ in range(self.grid_height)]
    self.undo_stack.clear() # Clear undo history on reset
    self.add_history() # Add initial clear state to history

    # Reset zoom and pan
    self.current_scale = 1.0
    self.offset_x = 0
    self.offset_y = 0
    
    self.layout() # Recalculate layout based on new grid dimensions and reset zoom
    self.set_needs_display()
    
    # Update title to reflect new dimensions if not loading an image
    if not self.loaded_image_path:    
        self.superview.name = f"Pixel Art Editor ({self.grid_width}x{self.grid_height}) x{int(self.current_scale)}"

  def layout(self):
    # This method is called when the view's frame changes (e.g., orientation)
    # Recalculate display_size to fit the grid within the available drawing area
    
    # Determine the available drawing area for the grid
    # These are internal to PixelEditor, not related to padding from superview
    self.drawing_area_width = self.width - 2 * self.grid_padding_x
    self.drawing_area_height = self.height - 2 * self.grid_padding_y
    
    # Calculate the maximum possible display_size to fit the entire grid at base zoom
    # Ensure base_pixel_size is always positive
    effective_base_pixel_size = max(1, self.base_pixel_size) 
    
    scale_x = self.drawing_area_width / (self.grid_width * effective_base_pixel_size)
    scale_y = self.drawing_area_height / (self.grid_height * effective_base_pixel_size)

    # Choose the smaller scale to ensure the entire grid fits
    base_display_scale = min(scale_x, scale_y)
    
    # Apply the current zoom level to get the actual display_size
    self.display_size = effective_base_pixel_size * base_display_scale * self.current_scale
    
    # Ensure offset_x and offset_y keep the grid centered or within bounds
    # when the layout changes. This is a simplified centering.
    
    grid_total_width = self.grid_width * self.display_size
    grid_total_height = self.grid_height * self.display_size

    # If the grid is smaller than the drawing area, center it
    if grid_total_width < self.drawing_area_width:
         self.offset_x = (self.drawing_area_width - grid_total_width) / 2
    # If zoomed in and scrolled, prevent scrolling too far out
    else:
        self.offset_x = max(min(self.offset_x, 0), self.drawing_area_width - grid_total_width)
        
    if grid_total_height < self.drawing_area_height:
         self.offset_y = (self.drawing_area_height - grid_total_height) / 2
    else:
        self.offset_y = max(min(self.offset_y, 0), self.drawing_area_height - grid_total_height)

  def draw(self):
    # Save the graphics state
    with ui.GState():
        # Set the clipping rectangle for the drawing area
        # Use self.bounds for the clipping path as drawing is within PixelEditor's own frame
        clip_path = ui.Path.rect(0, 0, self.width, self.height)
        clip_path.add_clip()

        # Draw the colored pixels
        for y_grid in range(self.grid_height):
            for x_grid in range(self.grid_width):
                color = self.pixel_data[y_grid][x_grid]
                if color != (0,0,0,0): # Only draw if not transparent
                    ui.set_color(color)
                    ui.fill_rect(x_grid * self.display_size + self.offset_x, 
                                 y_grid * self.display_size + self.offset_y, 
                                 self.display_size, self.display_size)
        
        # Draw the grid lines (overlay on top of pixels)
        ui.set_color('gray')
        # Adjust line width based on zoom for better visibility
        line_width = 1.0 / self.current_scale
        if line_width < 0.5: line_width = 0.5 # Minimum line width
        
        # Draw vertical lines
        for x in range(self.grid_width + 1):
            path = ui.Path()
            path.line_width = line_width
            path.move_to(x * self.display_size + self.offset_x, self.offset_y)
            path.line_to(x * self.display_size + self.offset_x, self.display_size * self.grid_height + self.offset_y)
            path.stroke()
            
        # Draw horizontal lines
        for y in range(self.grid_height + 1):
            path = ui.Path()
            path.line_width = line_width
            path.move_to(self.offset_x, y * self.display_size + self.offset_y)
            path.line_to(self.display_size * self.grid_width + self.offset_x, y * self.display_size + self.offset_y)
            path.stroke()
            
        # --- NEW: Draw selection rectangle ---
        if self.selection_start and self.selection_end:
            x_start, y_start = self.selection_start
            x_end, y_end = self.selection_end
            
            min_x = min(x_start, x_end)
            min_y = min(y_start, y_end)
            max_x = max(x_start, x_end)
            max_y = max(y_start, y_end)
            
            rect_x = min_x * self.display_size + self.offset_x
            rect_y = min_y * self.display_size + self.offset_y
            rect_w = (max_x - min_x + 1) * self.display_size
            rect_h = (max_y - min_y + 1) * self.display_size
            
            path = ui.Path.rect(rect_x, rect_y, rect_w, rect_h)
            path.line_width = 2.0
            ui.set_color('cyan')
            path.set_line_dash([4, 4]) # Dashed line for selection
            path.stroke()

        # --- NEW: Draw paste preview ---
        if self.mode == self.paste_tool and self.clipboard_buffer is not None:
            px, py = self.last_touch_grid_pos
            buffer_h = len(self.clipboard_buffer)
            buffer_w = len(self.clipboard_buffer[0])
            for r in range(buffer_h):
                for c in range(buffer_w):
                    color = list(self.clipboard_buffer[r][c])
                    if color[3] > 0: # Only draw non-transparent pixels
                        color[3] *= 0.6 # Make preview semi-transparent
                        ui.set_color(tuple(color))
                        ui.fill_rect((px + c) * self.display_size + self.offset_x,
                                     (py + r) * self.display_size + self.offset_y,
                                     self.display_size, self.display_size)

  def touch_to_grid(self, touch_location):
    # Convert touch location to grid coordinates, considering pan offset and PixelEditor's own frame
    x_grid = int((touch_location.x - self.offset_x) / self.display_size)
    y_grid = int((touch_location.y - self.offset_y) / self.display_size)
    
    # Clamp to grid boundaries
    x_grid = max(0, min(x_grid, self.grid_width - 1))
    y_grid = max(0, min(y_grid, self.grid_height - 1))
    return x_grid, y_grid

  def touch_began(self, touch):
    self.initial_touch_location = touch.location
    self.moved = False        
    
    # Get initial grid coordinates for single touch actions
    self.x_grid_initial, self.y_grid_initial = self.touch_to_grid(touch.location)
    # --- NEW: Handle selection start ---
    if self.mode == self.select_area:
        self.selection_start = (self.x_grid_initial, self.y_grid_initial)
        self.selection_end = self.selection_start
        self.selection_rect = None # Clear old selection
        self.set_needs_display()

  def touch_moved(self, touch):      
      # Update for paste preview
      
      if self.mode == self.select_area:
          self.moved = True
          self.selection_end = self.touch_to_grid(touch.location)
          self.last_touch_grid_pos = self.selection_end
          self.set_needs_display()
      elif self.mode == self.paste_tool and self.clipboard_buffer:      
          self.moved = True
          self.last_touch_grid_pos = self.touch_to_grid(touch.location)
          self.set_needs_display()      
      elif self.current_scale > self.min_scale: # Panning mode
          self.moved = True
          delta_x = touch.location.x - self.initial_touch_location.x
          delta_y = touch.location.y - self.initial_touch_location.y
          
          self.offset_x += delta_x
          self.offset_y += delta_y
          
          self.layout() # Recalculate layout to clamp offsets
          self.set_needs_display()
          self.initial_touch_location = touch.location # Update for continuous pan
      else: # Drawing mode (no zoom, so single finger draws)
          current_x_grid, current_y_grid = self.touch_to_grid(touch.location)
          
          if (0 <= current_x_grid < self.grid_width and 0 <= current_y_grid < self.grid_height and
              (current_x_grid != self.x_grid_initial or current_y_grid != self.y_grid_initial) and not self.fillmode):
              self.mode(current_x_grid, current_y_grid) # Apply current mode (pencil/eraser)
              self.x_grid_initial = current_x_grid # Update last drawn grid cell
              self.y_grid_initial = current_y_grid
              self.moved = True # Mark as moved if drawing

  def touch_ended(self, touch):
    x_grid, y_grid = self.touch_to_grid(touch.location)
    if not self.moved: # Only process as a tap if not moved (not pan/zoom/drag-draw)
        
        if 0 <= x_grid < self.grid_width and 0 <= y_grid < self.grid_height:
            if self.fillmode:
                self.flood_fill(x_grid, y_grid, self.current_color)
            else:
                self.mode(x_grid, y_grid) # Apply current mode (pencil, eraser, color_picker)
    # --- NEW: Finalize selection ---
    if self.mode == self.select_area and self.selection_start and self.selection_end:
        x_start, y_start = self.selection_start
        x_end, y_end = self.selection_end
        min_x = min(x_start, x_end)
        min_y = min(y_start, y_end)
        width = abs(x_start - x_end) + 1
        height = abs(y_start - y_end) + 1
        self.selection_rect = (min_x, min_y, width, height)        
        toolbar_view_instance.buttons['cut'].enabled = True
        toolbar_view_instance.buttons['copy'].enabled = True
    elif self.mode == self.paste_tool and self.clipboard_buffer:      
        self.mode(x_grid, y_grid) 
    # Don't clear start/end here, draw() needs them until a new selection starts
    self.initial_touch_location = None # Reset for next touch event
    self.initial_dist = None
    self.initial_center = None
    self.moved = False

  def zoom_in(self, factor=2):
      new_scale = self.current_scale * factor
      new_scale = min(new_scale, self.max_scale)
      self._apply_zoom(new_scale)

  def zoom_out(self, factor=2):
      new_scale = self.current_scale / factor
      new_scale = max(new_scale, self.min_scale)
      self._apply_zoom(new_scale)

  def _apply_zoom(self, new_scale):
      # Find the current center of the visible area (in content coordinates)
      current_visible_center_x = (-self.offset_x + self.width / 2) / self.display_size
      current_visible_center_y = (-self.offset_y + self.height / 2) / self.display_size
      
      old_display_size = self.display_size
      self.current_scale = new_scale
      self.layout() # This updates self.display_size based on new_scale

      # Adjust offsets to keep the same content center
      self.offset_x = self.width / 2 - (current_visible_center_x * self.display_size)
      self.offset_y = self.height / 2 - (current_visible_center_y * self.display_size)

      self.layout() # Call layout again to clamp offsets after centralizing
      self.set_needs_display()
      
      # Update toolbar scale text
      toolbar = find_subview_by_name(self.superview, 'toolbar')
      if toolbar and toolbar['scale']:
          toolbar['scale'].text = f'x{int(self.current_scale)}'

  def reset_zoom(self):
    self._apply_zoom(1.0)
    self.offset_x = 0
    self.offset_y = 0
    self.layout()
    self.set_needs_display()

  @ui.in_background
  def load_image_into_grid(self):
    console.hud_alert("Loading image...", 'info', 0.5)
    
    # Use Program 2's file picker
    self.loaded_image_path = File_Picker.file_picker_dialog('Pick an image file', select_dirs=False, file_pattern=r'^.*\.(png|jpg|jpeg)$')       
    
    if self.loaded_image_path:
        img_np_downscaled, inferred_pixel_size = self._infer_scaling_and_downscale(self.loaded_image_path)
        
        if img_np_downscaled is not None:
            console.hud_alert("Image loaded!", 'success', 0.5)
            self.base_pixel_size = inferred_pixel_size 
            self.grid_height, self.grid_width = img_np_downscaled.shape
            
            # Reset the grid with new dimensions
            self.pixel_data = [[(0, 0, 0, 0) for _ in range(self.grid_width)] for _ in range(self.grid_height)]
            self.undo_stack.clear() # Clear undo history for new image

            for r in range(self.grid_height):
                for c in range(self.grid_width):
                    rgba_int = img_np_downscaled[r, c]
                    red = (rgba_int >> 24) & 0xFF
                    g = (rgba_int >> 16) & 0xFF
                    b = (rgba_int >> 8) & 0xFF
                    a = rgba_int & 0xFF
                    
                    # Store as 0-1 float RGBA tuple
                    self.pixel_data[r][c] = (red/255.0, g/255.0, b/255.0, a/255.0)
            
            self.add_history() # Add the loaded image state to history
            
            self.superview.name = f'{Path(self.loaded_image_path).name} ({self.grid_width}x{self.grid_height}) x{int(self.current_scale)}'
            self.zoom = 1 # Reset zoom when loading a new image
            self.offset_x = 0 # Reset pan offset
            self.offset_y = 0
            toolbar_view_instance['pixels'].text = f'{self.grid_width},{self.grid_height}'
            self.layout() # Recalculate display to fit new image size
            self.set_needs_display() # Redraw the view to show the change
            
            # Update preview in toolbar
            toolbar = find_subview_by_name(self.superview, 'toolbar')
            if toolbar:
                toolbar.preview(None)
        else:
            console.hud_alert("Failed to load image.", 'error', 0.8)
    else:
        console.hud_alert("No image selected.", 'info', 0.5)
         
  def _infer_scaling_and_downscale(self, image_path):
      """
      Infers the scaling factor (N) and downscales an image where each original
      pixel has been replicated N times into an N x N block of identical pixels.
  
      Args:
          image_path (str): The file path to the input PNG image.
  
      Returns:
          tuple: A tuple containing:
                 - numpy.ndarray: The downscaled image as a NumPy array (single integer per pixel).
                 - int: The inferred scaling factor (N).
                 Returns (None, 0) if an error occurs or scaling factor cannot be determined.
      """
      try:
          img = Image.open(image_path)
          
          # Convert to RGBA for consistent handling of transparency during inference
          img_rgba_np = np.array(img.convert('RGBA'))
          
          # Convert RGBA array to a 2D array of single integer values for RLE
          img_np_single_value = rgba_to_single_value(img_rgba_np)
          
          img_height, img_width = img_np_single_value.shape
  
          if img_height == 0 or img_width == 0:
              print("Error: Image dimensions are zero.")
              return None, 0
  
          # Find the minimum contiguous block size (scaling factor N)
          n_min = 1e6
          # Iterate along the rows to find minimum N
          # stop if n_min is 1
          for y in range(1, img_height):
              row = img_np_single_value[y, :]
              z, p , ia = rle(row)
              if min(z) < n_min:
                 n_min = min(z)
                 if n_min == 1:
                     break
          if n_min > 1:      
              for x in range(1, img_width):
                  col = img_np_single_value[:, x]
                  z, p , ia = rle(col)
                  if min(z) < n_min:
                     n_min = min(z)
          scaling_factor = int(n_min) # Ensure it's an integer
          
          if scaling_factor == 0:
              print("Error: Inferred scaling factor is zero.")
              return None, 0

          # Downscale by sampling every N-th pixel
          downscaled_img_np = img_np_single_value[::scaling_factor, ::scaling_factor]
  
          return downscaled_img_np, scaling_factor
  
      except FileNotFoundError:
          print(f"Error: File not found at {image_path}")
          return None, 0
      except Exception as e:
          print(f"An error occurred during image inference/downscaling: {e}")
          return None, 0   

class ColorView (ui.View):
  def did_load(self):
    self.color = {'r':0, 'g':0, 'b':0, 'a':1} # Default black
    # Initialize UI elements from .pyui file
    for subview in self.subviews:
      self.init_action(subview)
    self.set_color((0, 0, 0, 1)) # Set initial color to black and update UI

  def init_action(self, subview):
    if hasattr(subview, 'action'):
      self.set_action(subview)
    if hasattr(subview, 'subviews'):
      for sv in subview.subviews:
        self.init_action(sv)

  def set_action(self, subview):
    if subview.name == 'clear_palette': # Renamed from 'clear' to avoid conflict
      subview.action = self.clear_user_palette
    else:
      subview.action = self.choose_color

  def get_color(self):
    return tuple(self.color[i] for i in 'rgba')

  def set_color(self, color=None):
    # Ensure color is a tuple with 4 elements (RGBA)
    if color is None:
        color = self.get_color()
    elif len(color) == 3: # If RGB, assume opaque
        color = (color[0], color[1], color[2], 1.0)
    elif len(color) == 1 and isinstance(color[0], (float, int)): # If grayscale (single float/int)
        color = (color[0], color[0], color[0], 1.0)

    for i, v in enumerate('rgba'):
      if i < len(color): # Ensure index is within color tuple bounds
          if v != 'a': 
              self[v].value = max(0, min(1, color[i])) 
          self.color[v] = color[i]
          
    # Update hex input field and current_color display
    try:
        rgb_to_hex = tuple(int(val * 255) for val in color[:3])
        self['color_input'].text = '#{:02X}{:02X}{:02X}'.format(*rgb_to_hex)
    except Exception as e:
        self['color_input'].text = 'Invalid'
        console.hud_alert(f'Error converting color to hex: {e}', 'error', 0.8)

    self['current_color'].background_color = color
    
    editor_view = find_subview_by_name(self.superview, 'editor')
    if editor_view:
        editor_view.current_color = color # Update the pixel editor's current color

  @ui.in_background
  def choose_color(self, sender):
    if sender.name in self.color: # Slider for R, G, B, A
      self.color[sender.name] = sender.value
      self.set_color()
    elif sender.superview.name == 'palette' and sender.background_color: # Palette buttons
      self.set_color(sender.background_color)
    elif sender.name == 'color_input': # Hex input field
      try: 
        c = sender.text.strip()
        if c.startswith('#') and len(c) == 7: # #RRGGBB format
            r = int(c[1:3], 16) / 255.0
            g = int(c[3:5], 16) / 255.0
            b = int(c[5:7], 16) / 255.0
            self.set_color((r, g, b, self.color['a'])) # Preserve current alpha
        else: # Try evaluating as Python color name/tuple
            # Create a dummy view to leverage ui.View's color parsing
            v = ui.View(background_color=eval(c))
            self.set_color(v.background_color)
      except Exception as e:
        console.hud_alert(f'Invalid Color Input: {e}', 'error', 0.8)

  def clear_user_palette(self, sender):
    console.hud_alert('Clear user palette not implemented', 'info', 0.8)

class ToolbarView (ui.View):
  def did_load(self):
    self.pixel_editor = None 
    self.color_view = None
    self.buttons = {subview.name: subview 
                   for subview in find_subview_by_name(self, 'tools').subviews 
                  if isinstance(subview, ui.Button)}     
    
    # print(self.buttons) 
    # print(self.buttons['pencil']) 
    # print(find_subview_by_name(find_subview_by_name(self, 'tools'), 'pencil'))        
    for subview in self.subviews:
      self.init_actions(subview)
 
  def setup_links(self, editor_view, color_view):
      self.pixel_editor = editor_view
      self.color_view = color_view
            
      if self.pixel_editor and self.color_view: 
          self.pixel_editor.current_color = self.color_view.get_color() 
          
          # Set initial mode to pencil and highlight button
          pencil_button = self.buttons['pencil']       
             
          self.set_mode(pencil_button)
          

          # Set initial crop button state
          crop_button = self.buttons['crop']
          
          # Assuming crop.png is a custom icon
          crop_button.image = ui.Image.named('crop.png')
          self.highlight(crop_button, self.pixel_editor.auto_crop_image)
          
          fill_button = self.buttons['fill']          
          # Assuming fill.png is a custom icon
          fill_button.image = ui.Image.named('fill.png').with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
          self.highlight(fill_button, self.pixel_editor.fillmode)
              
          # --- NEW: Set icons for new buttons ---
          # Make sure you have buttons named 'select_area', 'cut', 'paste_tool' in your .pyui
          select_button = self.buttons['select_area']           
          select_button.image = ui.Image.named('select.png')     
               
          cut_button = self.buttons['cut']
          cut_button.image = ui.Image.named('typb:Cut')
          cut_button.enabled = False
          
          copy_button = self.buttons['copy']
          copy_button.image = ui.Image.named('iob:ios7_copy_32')
          copy_button.enabled = False
          
          paste_button = self.buttons['paste_tool']                      
          paste_button.image = ui.Image.named('paste.png')
          paste_button.enabled = False
          
          # Set initial pixels text
          self['pixels'].text = f'{self.pixel_editor.grid_width},{self.pixel_editor.grid_height}'
          self['scale'].text = f'x{int(self.pixel_editor.current_scale)}'


  def init_actions(self, subview):
    if hasattr(subview, 'action'):
      # Dynamically assign actions based on subview name
      if hasattr(self, subview.name):
        subview.action = getattr(self, subview.name)
      elif subview.superview and subview.superview.name == 'tools': # For mode buttons
        subview.action = self.set_mode
    if hasattr(subview, 'subviews'):
      for sv in subview.subviews:
        self.init_actions(sv)
        
  def show_error(self):
    console.hud_alert('Editor not initialized or has no image', 'error', 0.8)
    
  @ui.in_background   
  def trash(self, sender):
    if not self.pixel_editor:
        self.show_error()
        return
    if not self.pixel_editor.has_image():
        console.hud_alert('No image to clear.', 'info', 0.8)
        return

    msg = 'Are you sure you want to clear the pixel editor? Image will not be saved.'
    if console.alert('Trash', msg, 'Yes', 'No') == 1: # 'Yes' is index 1
      self.pixel_editor.reset()
      self.pixel_editor.loaded_image_path = None # Clear loaded image path
      self.superview.name = f"Pixel Art Editor ({self.pixel_editor.grid_width}x{self.pixel_editor.grid_height}) x{int(self.pixel_editor.current_scale)}"
      self.preview(None) # Clear preview after reset

  @ui.in_background
  def save(self, sender):
    
    if not self.pixel_editor or not self.pixel_editor.has_image():
        self.show_error()
        return
    
    image_to_save = self.pixel_editor.get_image() # This is a ui.Image
    
    option = console.alert('Save Image', '', 'Camera Roll', 'New File', 'Copy image')
    if option == 1: # Camera Roll
      photos.save_image(image_to_save)
      console.hud_alert('Saved to Camera Roll')
    elif option == 2: # New File
      # Convert ui.Image to PIL Image for saving to file system
      pil_image_to_save = ui_to_pil(image_to_save)
      
      initial_name = Path(self.pixel_editor.loaded_image_path).stem if self.pixel_editor.loaded_image_path else 'image'
      
      # Use dialogs.input_alert for file name
      file_name_input = dialogs.input_alert('Save As', 'Enter file name (e.g., my_sprite.png)', initial_name)
      
      if file_name_input:
          if not file_name_input.lower().endswith('.png'):
              file_name_input += '.png'
          pil_image_to_save.save(file_name_input, 'png') 
          console.hud_alert(f'Image saved as "{file_name_input}"')
      else:
          console.hud_alert('Save cancelled.', 'info', 0.8)
    elif option == 3: # Copy image
      clipboard.set_image(image_to_save, format='png')
      console.hud_alert('Copied to clipboard')
      
  def undo(self, sender):
    if not self.pixel_editor:
        self.show_error()
        return
    self.pixel_editor.undo()

  @ui.in_background
  def load_image(self, sender): 
    #if not self.pixel_editor:
    #    self.show_error()
    #    return
    
    if self.pixel_editor.has_image():
        if not console.alert('Load Image', 'This will replace the current image. Continue?', 'Yes', 'No') == 1:
            return 

    self.pixel_editor.load_image_into_grid()
        
  @ui.in_background
  def preview(self, sender):
    if not self.pixel_editor or not self.pixel_editor.has_image():
        # Display a blank preview or message if no image
        preview_v = preview_instance #find_subview_by_name(self, 'preview')
        if preview_v:
            preview_v.image = None
        # self.show_error() # Don't show error for preview if empty
        return
    v = preview_instance 
    v.image = self.pixel_editor.get_image()
    
    # Calculate appropriate size for the preview within its container
    
    max_dim = min(v.width * 0.9, v.height * 0.9)        
    if v.image and v.image.size[0] > 0 and v.image.size[1] > 0:
        aspect_ratio = v.image.size[0] / v.image.size[1]        
    if v.image.size[0] > v.image.size[1]: # Wider than tall
           v.width = max_dim
           v.height = max_dim / aspect_ratio
    else: # Taller than wide, or square
          v.height = max_dim
          v.width = max_dim * aspect_ratio   
        
    v.set_needs_display() # Ensure it redraws
    
  def circle(self, sender):
      self.pixel_editor.add_circle()
      
  def crop(self, sender):
    if not self.pixel_editor:
        self.show_error()
        return
    self.pixel_editor.auto_crop_image = not self.pixel_editor.auto_crop_image # Toggle
    
    # Update button appearance
    self.highlight(sender, self.pixel_editor.auto_crop_image)
    self.preview(None) # Update preview to show cropped or uncropped image

  def zoomin(self, sender):
    if not self.pixel_editor:
        self.show_error()
        return
    self.pixel_editor.zoom_in()
    
  def zoomout(self, sender):
    if not self.pixel_editor:
        self.show_error()
        return
    self.pixel_editor.zoom_out() 
  
  def _select_area(self, sender):
      if not self.pixel_editor:
        self.show_error()
        return
      self.pixel_editor.auto_crop_image = True
      #self.pixel_editor.select_area() 
      
  def cut(self, sender):
      if not self.pixel_editor:
        self.show_error()
        return
      self.pixel_editor.cut_selection() 
      
  def copy(self, sender):
      if not self.pixel_editor:
        self.show_error()
        return
      self.pixel_editor.copy_selection() 
      
  
      
  @ui.in_background
  def pixels(self, sender):
    if not self.pixel_editor:
        self.show_error()
        return
    if self.pixel_editor.has_image():
      console.hud_alert("Can't change size while editing. Clear image first.", "error")
      return 
    try: 
      size_input = sender.text.strip().split(',')
      new_width, new_height = self.pixel_editor.grid_width, self.pixel_editor.grid_height # Start with current

      if len(size_input) == 1:
          size = int(size_input[0])
          new_width, new_height = size, size
      elif len(size_input) == 2:
          new_width = int(size_input[0])
          new_height = int(size_input[1])
      else:
          raise ValueError("Invalid format. Use 'N' or 'N,M'")

      # Clamp dimensions
      new_width = max(1, min(new_width, 64)) 
      new_height = max(1, min(new_height, 64))

      # Only reset if dimensions actually changed
      if new_width != self.pixel_editor.grid_width or new_height != self.pixel_editor.grid_height:
          self.pixel_editor.reset(new_width, new_height) # Pass new dimensions to reset
          self['pixels'].text = f'{new_width},{new_height}' 
          self.preview(None) # Update preview
          #self.superview.name = f"Pixel Art Editor ({new_width}x{new_height}) x{int(self.pixel_editor.current_scale)}"

    except ValueError as e:
      console.hud_alert(f'Invalid size: {e}', 'error', 0.8)
    except Exception as e:
        console.hud_alert(f'An unexpected error occurred: {e}', 'error', 0.8)
        
  
  def set_mode(self, sender):
       
    if not self.pixel_editor:
        self.show_error()
        return    
    # Set the editor's mode based on sender's name
    if hasattr(self.pixel_editor, sender.name):
        self.pixel_editor.mode = getattr(self.pixel_editor, sender.name)
        
        # --- UPDATED: Clear selection when switching away from select tool ---
        if self.pixel_editor.mode == self.pixel_editor.select_area and sender.name != 'select_area':
            self.pixel_editor.selection_rect = None
            self.pixel_editor.selection_start = None
            self.pixel_editor.selection_end = None
            self.pixel_editor.set_needs_display()
            
        # Handle 'fill' mode toggle
        if sender.name == 'fill':
            self.pixel_editor.fillmode = not self.pixel_editor.fillmode
            self.highlight(sender, self.pixel_editor.fillmode)
            
        else: # For other tools, ensure fillmode is off
            self.pixel_editor.fillmode = False
            fill_button = self.buttons['fill']   
            
            self.highlight(fill_button, self.pixel_editor.fillmode)
            
        # Highlight selected tool button, unhighlight others in 'tools' container
        tools_container = find_subview_by_name(self, 'tools')
        if tools_container: 
            for b in tools_container.subviews:
                if b != sender and b.name != 'fill': # Don't unhighlight fill if it's currently active and another tool is selected
                    b.background_color = (0, 0, 0, 0) # Transparent for inactive
                
            if sender.name != 'fill': # If sender is not fill, highlight it
                sender.background_color = '#4C4C4C' # Dark background for active tool
    else:
        console.hud_alert(f"Unknown mode: {sender.name}", 'error', 0.8)

  def fill(self, sender):           
      if not self.pixel_editor:
        self.show_error()
        return
      self.pixel_editor.fillmode = not self.pixel_editor.fillmode
    
      # Update button appearance
      self.highlight(sender,self.pixel_editor.fillmode )
      
      self.preview(None) # Update preview to show filled image
      
  def reset_zoom(self, sender): 
      if self.pixel_editor:
          self.pixel_editor.reset_zoom()
          self['scale'].text = f'x{int(self.pixel_editor.current_scale)}' # Update scale text
          
  def highlight(self, button, mode):       
       # Highlight button if active, unhighlight if inactive
       if mode:
          button.background_color = '#4C4C4C'
          button.tint_color = 'white'
       else:
           button.background_color = (0, 0, 0, 0)
           button.tint_color = 'black' 
  
# --- Main Script Execution ---
if __name__ == '__main__':
    main_view = ui.load_view('pixel_editor') # Load the UI from the .pyui file
    #main_view.frame = (0, 0, 800, 1000) # Set a default size for the main view

    pixel_editor_instance = find_subview_by_name(main_view, 'editor')
    toolbar_view_instance = find_subview_by_name(main_view, 'toolbar')
    color_view_instance = find_subview_by_name(main_view, 'colors')
    preview_instance = find_subview_by_name(main_view, 'preview')
    if pixel_editor_instance and toolbar_view_instance and color_view_instance:
        # Set up initial title
        main_view.name = f"Pixel Art Editor ({pixel_editor_instance.grid_width}x{pixel_editor_instance.grid_height}) x{int(pixel_editor_instance.current_scale)}"
        
        # Link the views together
        toolbar_view_instance.setup_links(pixel_editor_instance, color_view_instance)
        # Ensure initial preview is set up
        toolbar_view_instance.preview(None) 
    else:
        console.hud_alert("Error: One or more UI components not found.", 'error', 2.0)

    main_view.present(style='fullscreen', orientations=['portrait'])

