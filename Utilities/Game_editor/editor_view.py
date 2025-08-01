# editor_view.py (Refactored to include Pan/Zoom/Undo)
import ui
import math
import console
from collections import deque
import numpy as np

class EditorView(ui.View):
 
    def __init__(self):
        #def __init__(self, sprite_manager, level_manager, *args, **kwargs):
        #super().__init__(*args, **kwargs)
        
        # --- Game Editor Specifics ---
        self.grid_width = 20 # Default level width
        self.grid_height = 15 # Default level height
        self.base_sprite_size = 16 # Ideal size of one sprite cell at zoom 1.0

        self.current_level_name = "Level 1"
        self.current_level_data = None
        #if not self.current_level_data:
        #    # Initialize a new empty level if it doesn't exist
        #    self.current_level_data = [[' ' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        #    self.level_manager.levels[self.current_level_name] = self.current_level_data
            
        #self.selected_sprite_char = list(self.sprite_manager.sprite_map)[0] # Default selected sprite for placement
        self.selected_sprite_char = ' '
        # --- Pan/Zoom/Undo from PixelEditor ---
        
        self.current_scale = 1.0
        self.min_scale = 0.5 # Allow slight zoom out
        self.max_scale = 8.0 # Max zoom in for sprite details
        
        self.offset_x = 0
        self.offset_y = 0
        self.initial_touch_location = None
        self.moved = False
        self.multitouch_enabled = True
        self.touches = {}
        self.initial_dist = None
        self.initial_center = None
        self.update_interval = 0.5
        self.undo_stack = deque()
        
        #self.add_history() # Add initial empty level to undo history

        # --- Editor Tools/Modes ---
        # Instead of `self.mode = self.pencil`, you'd have:
        self.tool_mode = self.place_sprite # Default tool: placing sprites
        # You'd have other modes like self.erase_sprite, self.pan_tool, etc.
        
        self.layout() # Initial layout calculation
        
    def load_map(self):
        self.current_level_data = self.level_manager.get_level_data(self.level_manager.current_level_name)
        self.current_level_name = self.level_manager.current_level_name
        # print(f'{self.current_level_name=}, {self.current_level_data=}')
        self.grid_height, self.grid_width = self.current_level_data.shape   
        # print(f'{self.grid_width=}, {self.grid_height=}')
        self.layout()
        self.add_history()
        self.set_needs_display()
        
        
    def add_history(self):
        # Store a deep copy of the current level data for undo
        #current_state = [row[:] for row in self.current_level_data]
        current_state = np.copy(self.current_level_data)
        if not self.undo_stack or  not np.array_equal(current_state, self.undo_stack[-1]):
            self.undo_stack.append(current_state)
            if len(self.undo_stack) > 20: # Limit history size
                self.undo_stack.popleft()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.current_level_data = self.undo_stack.pop()
            self.set_needs_display()
            # You might want to update a UI element indicating the current level state

    def layout(self):
        # Determine the available drawing area for the grid
        self.drawing_area_width = self.width
        self.drawing_area_height = self.height
        
        effective_base_sprite_size = max(1, self.base_sprite_size) 
        
        scale_x = self.drawing_area_width / (self.grid_width * effective_base_sprite_size)
        scale_y = self.drawing_area_height / (self.grid_height * effective_base_sprite_size)

        base_display_scale = min(scale_x, scale_y)
        self.display_size = effective_base_sprite_size * base_display_scale * self.current_scale
        
        # Centering and clamping logic (copied from PixelEditor)
        grid_total_width = self.grid_width * self.display_size
        grid_total_height = self.grid_height * self.display_size

        if grid_total_width < self.drawing_area_width:
             self.offset_x = (self.drawing_area_width - grid_total_width) / 2
        else:
            self.offset_x = max(min(self.offset_x, 0), self.drawing_area_width - grid_total_width)
            
        if grid_total_height < self.drawing_area_height:
             self.offset_y = (self.drawing_area_height - grid_total_height) / 2
        else:
            self.offset_y = max(min(self.offset_y, 0), self.drawing_area_height - grid_total_height)
            
    def update(self):        
     self.draw()
        
    def draw(self):
            #with ui.GState():
            ui.set_color('white')
            ui.fill_rect(0, 0, self.width, self.height) # Editor background

            clip_path = ui.Path.rect(0, 0, self.width, self.height)
            clip_path.add_clip()
            self.display_size = 40
            # --- Drawing Sprites (instead of pixels) ---
            if self.current_level_data is not None:
              for r_idx, row in enumerate(self.current_level_data):
                  for c_idx, char in enumerate(row):
                      if char != ' ': # Only draw if there's a sprite
                          sprite_image = self.sprite_manager.get_sprite_image(char)
                          if sprite_image:
                              x = c_idx * self.display_size + self.offset_x
                              y = r_idx * self.display_size + self.offset_y
                              #print(f'{r_idx},{c_idx}:{x:.1f}, {y:.1f}, {self.display_size:.1f}')
                              sprite_image.draw(x, y, self.display_size, self.display_size)
            
            # --- Drawing Grid Lines (copied from PixelEditor) ---
            ui.set_color('gray')
            line_width = 1.0 / self.current_scale
            if line_width < 0.5: line_width = 0.5
            # print(self.grid_width, self.grid_height)
            for x in range(self.grid_width + 1):
                path = ui.Path()
                path.line_width = line_width
                path.move_to(x * self.display_size + self.offset_x, self.offset_y)
                path.line_to(x * self.display_size + self.offset_x, self.display_size * self.grid_height + self.offset_y)
                path.stroke()
                
            for y in range(self.grid_height + 1):
                path = ui.Path()
                path.line_width = line_width
                path.move_to(self.offset_x, y * self.display_size + self.offset_y)
                path.line_to(self.display_size * self.grid_width + self.offset_x, y * self.display_size + self.offset_y)
                path.stroke()

            # --- Drawing selection/paste preview (adapt as needed for sprites) ---
            # ... (similar logic as PixelEditor, but for sprites/characters)

    def touch_to_grid(self, touch_location):
        # Convert touch location to grid coordinates, considering pan offset
        x_grid = int((touch_location.x - self.offset_x) / self.display_size)
        y_grid = int((touch_location.y - self.offset_y) / self.display_size)
        
        # Clamp to grid boundaries
        x_grid = max(0, min(x_grid, self.grid_width - 1))
        y_grid = max(0, min(y_grid, self.grid_height - 1))
        return x_grid, y_grid

    def touch_began(self, touch):
        self.selected_existing = False
        self.initial_touch_location = touch.location
        self.moved = False        
        # ... (multi-touch handling for zoom/pan - copy from PixelEditor)
        
        self.x_grid_initial, self.y_grid_initial = self.touch_to_grid(touch.location)
        if self.current_level_data[self.y_grid_initial, self.x_grid_initial] != ' ':
          self.selected_existing = True
          self.char_to_move = self.current_level_data[self.y_grid_initial, self.x_grid_initial]
          self.stored = np.copy(self.current_level_data)
          self.add_history()

    def touch_moved(self, touch):
        # --- Pan logic (copied from PixelEditor) ---
        if self.selected_existing:
           self.current_level_data[self.y_grid_initial, self.x_grid_initial] = ' '
           x, y = self.touch_to_grid(touch.location)
           self.current_level_data[(y,x)] = self.char_to_move 
           
           self.layout()
           self.set_needs_display()
        elif self.current_scale > self.min_scale and len(self.touches) == 1: # Single finger pan only if zoomed in
            self.moved = True
            delta_x = touch.location.x - self.initial_touch_location.x
            delta_y = touch.location.y - self.initial_touch_location.y
            
            self.offset_x += delta_x
            self.offset_y += delta_y
            
            self.layout()
            self.set_needs_display()
            self.initial_touch_location = touch.location # Update for continuous pan
        
         
        else: # Drawing/Placing Sprites mode
            current_x_grid, current_y_grid = self.touch_to_grid(touch.location)
            if (0 <= current_x_grid < self.grid_width and 0 <= current_y_grid < self.grid_height and
                (current_x_grid != self.x_grid_initial or current_y_grid != self.y_grid_initial)):
                
                # Apply current tool mode (e.g., place_sprite, erase_sprite)
                self.tool_mode(current_x_grid, current_y_grid) 
                self.x_grid_initial = current_x_grid
                self.y_grid_initial = current_y_grid
                self.moved = True

    def touch_ended(self, touch):
        x_grid, y_grid = self.touch_to_grid(touch.location)
        if self.selected_existing:
           self.current_level_data = self.stored
           self.current_level_data[(y_grid,x_grid)] = self.char_to_move 
           self.current_level_data[self.y_grid_initial, self.x_grid_initial] = ' '
           
        elif not self.moved: # Only process as a tap
            if 0 <= x_grid < self.grid_width and 0 <= y_grid < self.grid_height:
                self.tool_mode(x_grid, y_grid) # Apply tool on tap
        
        # Reset touch tracking
        self.initial_touch_location = None
        self.initial_dist = None
        self.initial_center = None
        self.moved = False
        self.layout()
        self.set_needs_display()
    # --- Tool Modes for Sprite Editor ---
    def place_sprite(self, x_grid, y_grid):
        char_to_place = self.selected_sprite_char
        if self.current_level_data[y_grid][x_grid] != char_to_place:
            self.add_history()
            self.current_level_data[y_grid][x_grid] = char_to_place
            self.set_needs_display()

    def erase_sprite(self, x_grid, y_grid):
        if self.current_level_data[y_grid][x_grid] != ' ': # ' ' for empty
            self.add_history()
            self.current_level_data[y_grid][x_grid] = ' '
            self.set_needs_display()

    # --- Pan/Zoom Methods (Copied directly, only name changed if needed) ---
    def zoom_in(self, factor=2.0): # Use a smaller factor for smoother zoom
        new_scale = self.current_scale * factor
        new_scale = min(new_scale, self.max_scale)
        self._apply_zoom(new_scale)

    def zoom_out(self, factor=2.0):
        new_scale = self.current_scale / factor
        new_scale = max(new_scale, self.min_scale)
        self._apply_zoom(new_scale)

    def _apply_zoom(self, new_scale):
        current_visible_center_x = (-self.offset_x + self.width / 2) / self.display_size
        current_visible_center_y = (-self.offset_y + self.height / 2) / self.display_size
        
        self.current_scale = new_scale
        #self.layout()

        self.offset_x = self.width / 2 - (current_visible_center_x * self.display_size)
        self.offset_y = self.height / 2 - (current_visible_center_y * self.display_size)

        self.layout() 
        self.set_needs_display()
        # Update UI for scale display (e.g., in toolbar)

    def reset_zoom(self):
        self._apply_zoom(1.0)
        self.offset_x = 0
        self.offset_y = 0
        self.layout()
        self.set_needs_display()

    def set_level(self, level_name):
        # Update grid dimensions based on the loaded level
        level_data = self.level_manager.get_level_data(level_name)
        if level_data is not None:
            self.current_level_name = level_name
            self.current_level_data = level_data
            self.grid_height, self.grid_width = level_data.shape
            self.add_history() # Add new level to history
            self.reset_zoom() # Reset zoom/pan when changing levels
            self.set_needs_display()
            # Update main_view name with new level dimensions
        else:
            console.hud_alert(f"Level '{level_name}' not found.", 'error', 0.8)

    # ... (Other methods for selection, cut, copy, paste, etc., adapted for sprites)

