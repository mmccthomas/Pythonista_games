import scene
import sound # For simple sound effects
import random
from math import floor

# --- Constants ---
# Board dimensions (number of cells)
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
# Size of each block in pixels
BLOCK_SIZE = 0
# Fall speed (seconds per step)
INITIAL_FALL_SPEED = 0.8
FALL_SPEED_DECREMENT = 0.05 # How much speed increases per level
MIN_FALL_SPEED = 0.1
SOFT_DROP_MULTIPLIER = 5 # How much faster piece falls on soft drop

# Tetromino shapes and their colors
# Each shape is a list of (row, col) offsets from a pivot point
TETROMINOES = {
    'I': {'shape': [(0, -2), (0, -1), (0, 0), (0, 1)], 'color': 'cyan', 'pivot': (0.5, -0.5)},
    'O': {'shape': [(0, 0), (0, 1), (1, 0), (1, 1)], 'color': 'yellow', 'pivot': (0.5, 0.5)},
    'T': {'shape': [(0, -1), (0, 0), (0, 1), (1, 0)], 'color': 'purple', 'pivot': (0,0)},
    'S': {'shape': [(0, 0), (0, 1), (1, -1), (1, 0)], 'color': 'green', 'pivot': (0,0)},
    'Z': {'shape': [(0, -1), (0, 0), (1, 0), (1, 1)], 'color': 'red', 'pivot': (0,0)},
    'J': {'shape': [(0, -1), (0, 0), (0, 1), (1, 1)], 'color': 'blue', 'pivot': (0,0)}, # Pivot adjusted
    'L': {'shape': [(0, -1), (0, 0), (0, 1), (1, -1)], 'color': 'orange', 'pivot': (0,0)} # Pivot adjusted
}
# Corrected pivots for J and L for better rotation feel (relative to top-left of a 3x3 or 4x4 box)
# For simplicity, we'll use a common pivot logic in rotation.
# The 'pivot' in TETROMINOES is more of a hint for initial positioning or complex rotation.
# We'll use a simpler bounding box center for rotation.

# Colors for Pythonista scene
COLORS = {
    'cyan': (0, 1, 1, 1),
    'yellow': (1, 1, 0, 1),
    'purple': (0.5, 0, 0.5, 1),
    'green': (0, 1, 0, 1),
    'red': (1, 0, 0, 1),
    'blue': (0, 0, 1, 1),
    'orange': (1, 0.65, 0, 1),
    'gray': (0.5, 0.5, 0.5, 1), # For grid lines
    'darkgray': (0.2, 0.2, 0.2, 1), # For landed blocks
    'black': (0,0,0,1),
    'white': (1,1,1,1)
}

class TetrisGame(scene.Scene):
    def setup(self):
        global BLOCK_SIZE # Allow modification of global BLOCK_SIZE

        # --- Dynamic Sizing ---
        # Calculate BLOCK_SIZE based on screen height to fit the board
        # Leave some space for score display at the top
        usable_height = self.size.h * 0.9
        BLOCK_SIZE = floor(usable_height / BOARD_HEIGHT)

        self.board_pixel_width = BOARD_WIDTH * BLOCK_SIZE
        self.board_pixel_height = BOARD_HEIGHT * BLOCK_SIZE

        # Center the board on the screen
        self.board_origin_x = (self.size.w - self.board_pixel_width) / 2
        self.board_origin_y = (self.size.h - self.board_pixel_height) / 2 # Bottom of the board

        # --- Game State Variables ---
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.game_over = False
        self.fall_speed = INITIAL_FALL_SPEED
        self.current_fall_speed = self.fall_speed # Can be modified by soft drop
        self.last_fall_time = self.t # `self.t` is current time in scene

        # --- Current Piece ---
        self.current_piece = None
        self.current_piece_shape_key = None
        self.current_piece_coords = [] # List of (row, col) on the board
        self.current_piece_color = None
        self.current_piece_pivot_board = (0,0) # (row, col) pivot on board

        #self.spawn_new_piece()

        # --- UI Elements ---
        self.score_label = scene.LabelNode(
            f'Score: {self.score} Level: {self.level}',
            font=('Helvetica', 20),
            position=(self.size.w / 2, self.size.h - 30),
            parent=self
        )
        self.score_label.color = COLORS['white']

        self.game_over_label = scene.LabelNode(
            'Game Over!',
            font=('Helvetica-Bold', 40),
            position=(self.size.w / 2, self.size.h / 2 + self.board_origin_y + self.board_pixel_height / 2), # Centered on board
            parent=self,
            alpha=0 # Initially hidden
        )
        self.game_over_label.color = COLORS['red']
        
        self.instructions_label = scene.LabelNode(
            'Tap L/R to Move, Mid to Rotate, Swipe Down to Drop',
            font=('Helvetica', 14),
            position=(self.size.w / 2, self.board_origin_y - 20), # Below board
            parent=self
        )
        self.instructions_label.color = COLORS['white']


        # --- Sound Effects (optional) ---
        try:
            sound.set_volume(0.5)
            self.clear_line_sound = 'digital:PowerUp7' # Example sound
            self.game_over_sound = 'game:Error'
            self.move_sound = 'ui:click1' # Example sound
            self.rotate_sound = 'ui:switch1' # Example sound
            self.drop_sound = 'ui:switch2'
        except Exception as e:
            print(f"Sound effects disabled: {e}")
            self.clear_line_sound = None
            self.game_over_sound = None
            self.move_sound = None
            self.rotate_sound = None
            self.drop_sound = None

        # Background color
        self.background_color = COLORS['black']
        self.is_soft_dropping = False
        self.spawn_new_piece()

    def spawn_new_piece(self):
        if self.game_over:
            return

        self.current_piece_shape_key = random.choice(list(TETROMINOES.keys()))
        piece_data = TETROMINOES[self.current_piece_shape_key]
        self.current_piece = [list(p) for p in piece_data['shape']] # Make mutable copy
        self.current_piece_color = COLORS[piece_data['color']]

        # Initial position: centered horizontally, at the top
        start_col = BOARD_WIDTH // 2 -1 # Adjust for typical piece width
        start_row = BOARD_HEIGHT - 1 # Start above visible board, will drop in

        # Calculate current piece coordinates on the board
        self.current_piece_pivot_board = (start_row, start_col)
        
        temp_coords = self.get_piece_board_coords(self.current_piece, self.current_piece_pivot_board)

        # Adjust start_row if piece is too high (e.g. I piece vertical)
        min_r = min(p[0] for p in self.current_piece)
        self.current_piece_pivot_board = (start_row - min_r, start_col)
        
        self.current_piece_coords = self.get_piece_board_coords(self.current_piece, self.current_piece_pivot_board)

        if not self.is_valid_position(self.current_piece_coords):
            pass
            # self.trigger_game_over()


    def get_piece_board_coords(self, piece_shape, pivot_board_pos):
        """Converts piece's local relative coords to absolute board coords."""
        pivot_r, pivot_c = pivot_board_pos
        return [(pivot_r + p_r, pivot_c + p_c) for p_r, p_c in piece_shape]

    def is_valid_position(self, piece_coords, check_board_bottom=True):
        """Checks if the piece at its current coordinates is in a valid position."""
        for r, c in piece_coords:
            if not (0 <= c < BOARD_WIDTH): # Check horizontal bounds
                return False
            if check_board_bottom and not (0 <= r < BOARD_HEIGHT ): # Check vertical bounds (bottom)
                 return False
            if r < 0 and check_board_bottom : # Allow pieces to be above board when spawning
                continue
            if r < BOARD_HEIGHT and (self.board[r][c] is not None): # Check collision with landed blocks
                return False
        return True

    def move_piece(self, dr, dc):
        if self.game_over:
            return False

        new_pivot_r = self.current_piece_pivot_board[0] + dr
        new_pivot_c = self.current_piece_pivot_board[1] + dc
        
        potential_coords = self.get_piece_board_coords(self.current_piece, (new_pivot_r, new_pivot_c))

        if self.is_valid_position(potential_coords):
            self.current_piece_pivot_board = (new_pivot_r, new_pivot_c)
            self.current_piece_coords = potential_coords
            if self.move_sound and (dc != 0): sound.play_effect(self.move_sound)
            return True
        return False

    def rotate_piece(self):
        if self.game_over or not self.current_piece:
            return

        # Simple rotation: (x, y) -> (-y, x) for clockwise around (0,0)
        # For Tetris, pivot is usually within the piece's bounding box.
        # We'll rotate relative to the piece's local origin (0,0 in its definition)
        
        rotated_shape = []
        for r_offset, c_offset in self.current_piece:
            # Clockwise rotation: new_c = r_offset, new_r = -c_offset
            # But typically Tetris uses new_x = -y, new_y = x if (0,0) is center
            # Let's use standard 90-deg clockwise: (x,y) -> (y,-x) if origin is top-left
            # For our (row, col) with row increasing downwards: (r,c) -> (c, -r) is not quite right
            # Let's use: new_local_c = -old_local_r, new_local_r = old_local_c
            # This corresponds to rotating points (c, -r) around origin (0,0)
            # where positive r is down.
            # (c, -r) -> (-(-r), c) -> (r,c) ... no, this is not right.
            # Standard 2D rotation: x' = x cos(a) - y sin(a), y' = x sin(a) + y cos(a)
            # For 90 deg clockwise (a = -90): x' = y, y' = -x
            # So, (c_offset, r_offset) -> (r_offset, -c_offset)
            rotated_shape.append((c_offset, -r_offset))


        potential_coords = self.get_piece_board_coords(rotated_shape, self.current_piece_pivot_board)

        # Basic wall kick: try to shift if out of bounds
        # This is a very simplified wall kick. Real Tetris has complex SRS.
        shifts_to_try = [(0,0), (0,1), (0,-1), (0,2), (0,-2), (1,0), (-1,0)] # (dr, dc) for pivot

        original_pivot = self.current_piece_pivot_board
        
        for dr_shift, dc_shift in shifts_to_try:
            shifted_pivot = (original_pivot[0] + dr_shift, original_pivot[1] + dc_shift)
            potential_coords_shifted = self.get_piece_board_coords(rotated_shape, shifted_pivot)
            if self.is_valid_position(potential_coords_shifted):
                self.current_piece = rotated_shape
                self.current_piece_pivot_board = shifted_pivot
                self.current_piece_coords = potential_coords_shifted
                if self.rotate_sound: sound.play_effect(self.rotate_sound)
                return True
        
        return False # Rotation failed


    def lock_piece(self):
        if not self.current_piece_coords: return

        for r, c in self.current_piece_coords:
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                self.board[r][c] = self.current_piece_color
            elif r >= BOARD_HEIGHT : # Piece trying to lock partially off-screen (top)
                # This can happen if piece spawns and immediately collides high up
                # This should ideally be caught by game over logic earlier
                pass


        if self.drop_sound: sound.play_effect(self.drop_sound)
        self.clear_lines()
        self.spawn_new_piece()
        self.is_soft_dropping = False # Reset soft drop status
        self.current_fall_speed = self.fall_speed


    def clear_lines(self):
        lines_cleared_this_turn = 0
        new_board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        write_row = BOARD_HEIGHT - 1 # Start filling from the bottom of new_board

        for r in range(BOARD_HEIGHT - 1, -1, -1): # Iterate from bottom row up
            if all(self.board[r]): # If row is full
                lines_cleared_this_turn += 1
            else:
                if write_row >= 0 : # Ensure we don't write out of bounds if many lines cleared
                    new_board[write_row] = list(self.board[r]) # Copy the row
                    write_row -= 1
        
        self.board = new_board

        if lines_cleared_this_turn > 0:
            if self.clear_line_sound: sound.play_effect(self.clear_line_sound)
            # Scoring: 1 line = 40, 2 = 100, 3 = 300, 4 (Tetris) = 1200 (scaled by level)
            if lines_cleared_this_turn == 1:
                self.score += 40 * self.level
            elif lines_cleared_this_turn == 2:
                self.score += 100 * self.level
            elif lines_cleared_this_turn == 3:
                self.score += 300 * self.level
            elif lines_cleared_this_turn >= 4: # Tetris!
                self.score += 1200 * self.level
            
            self.lines_cleared_total += lines_cleared_this_turn
            
            # Update level (e.g., every 10 lines)
            new_level = (self.lines_cleared_total // 10) + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = max(MIN_FALL_SPEED, INITIAL_FALL_SPEED - (self.level -1) * FALL_SPEED_DECREMENT)
                # Don't override soft drop speed if it's active
                if not self.is_soft_dropping:
                    self.current_fall_speed = self.fall_speed

            self.score_label.text = f'Score: {self.score} Level: {self.level}'


    def trigger_game_over_(self):
        self.game_over = True
        self.game_over_label.alpha = 1 # Show "Game Over"
        if self.game_over_sound: sound.play_effect(self.game_over_sound)
        # Optional: Add a "Tap to Restart" functionality here or in touch_began

    def update(self):
        if self.game_over:
            return

        # --- Piece Falling Logic ---
        if self.t - self.last_fall_time >= self.current_fall_speed:
            if not self.move_piece(-1, 0): # Try to move down
                # If cannot move down, lock the piece
                self.lock_piece()
                # Check for game over again after locking, in case spawn fails
                if self.game_over: return
            self.last_fall_time = self.t
        
        # Update current piece coordinates after any move/rotation
        if self.current_piece:
             self.current_piece_coords = self.get_piece_board_coords(self.current_piece, self.current_piece_pivot_board)


    def draw_block(self, r, c, color, origin_x, origin_y):
        """Draws a single block on the screen."""
        # Convert board (row, col) to screen coordinates
        # Board (0,0) is bottom-left cell. Screen (0,0) is bottom-left.
        screen_x = origin_x + c * BLOCK_SIZE
        screen_y = origin_y + r * BLOCK_SIZE
        scene.rect(screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE)


    def draw(self):
        # scene.background(0,0,0) # Set in setup
        
        # --- Draw Board Outline & Grid (optional) ---
        scene.stroke(0.3, 0.3, 0.3, 1) # Grid line color
        scene.stroke_weight(1)
        # Vertical lines
        for c in range(BOARD_WIDTH + 1):
            x = self.board_origin_x + c * BLOCK_SIZE
            scene.line(x, self.board_origin_y, x, self.board_origin_y + self.board_pixel_height)
        # Horizontal lines
        for r in range(BOARD_HEIGHT + 1):
            y = self.board_origin_y + r * BLOCK_SIZE
            scene.line(self.board_origin_x, y, self.board_origin_x + self.board_pixel_width, y)

        # --- Draw Landed Blocks ---
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                if self.board[r][c] is not None:
                    scene.fill(*self.board[r][c]) # Unpack color tuple
                    self.draw_block(r, c, self.board[r][c], self.board_origin_x, self.board_origin_y)

        # --- Draw Current Falling Piece ---
        if self.current_piece and not self.game_over:
            scene.fill(*self.current_piece_color)
            for r_board, c_board in self.current_piece_coords:
                 if r_board < BOARD_HEIGHT : # Only draw parts of piece that are on visible board
                    self.draw_block(r_board, c_board, self.current_piece_color, self.board_origin_x, self.board_origin_y)
        
        # Score and other UI elements are LabelNodes, drawn automatically by scene.

    def touch_began(self, touch):
        if self.game_over:
            # Simple restart on tap when game is over
            # self.setup() # This would re-initialize everything.
            # For a cleaner restart, you might want to re-run the scene:
            # main_view = self.view
            # main_view.remove_subview(main_view.subviews[0]) # remove current scene view
            # main_view.add_subview(scene.SceneView(TetrisGame()))
            # This is tricky. For now, just stop interaction.
            # Or, more simply:
            # game = TetrisGame()
            # self.view.present(game, hide_title_bar=True, animated=False)
            # return
            pass


        x, y = touch.location
        
        # Determine which third of the screen was tapped for L/R/Rotate
        screen_third_width = self.size.w / 3

        if x < screen_third_width: # Left third
            self.move_piece(0, -1)
        elif x > 2 * screen_third_width: # Right third
            self.move_piece(0, 1)
        else: # Middle third
            self.rotate_piece()
            
        # Store initial touch Y for swipe detection
        self.touch_start_y = y
        self.is_soft_dropping = False # Reset on new touch

    def touch_moved(self, touch):
        if self.game_over:
            return
            
        # Swipe down for soft drop
        # A simple check: if current y is significantly lower than start y
        if self.touch_start_y - touch.location.y > BLOCK_SIZE * 1.5: # Swipe down threshold
            if not self.is_soft_dropping:
                self.is_soft_dropping = True
                self.current_fall_speed = self.fall_speed / SOFT_DROP_MULTIPLIER
                self.last_fall_time = self.t # Force an immediate fall check

    def touch_ended(self, touch):
        if self.game_over:
            return
        # Reset soft drop when touch ends if it was active
        if self.is_soft_dropping:
            self.is_soft_dropping = False
            self.current_fall_speed = self.fall_speed


if __name__ == '__main__':
    # Run the game
    # Note: BLOCK_SIZE is calculated in setup based on screen size.
    # We pass arbitrary initial dimensions here; they'll be overridden by the scene's actual size.
    game_scene = TetrisGame()
    
    # For Pythonista, you typically run a scene using scene.run() or by presenting it in a SceneView
    # If running directly as a script in Pythonista:
    #main_view = scene.SceneView(frame=scene.get_screen_size())
    #main_view.scene = game_scene
    #main_view.present('fullscreen', hide_title_bar=True, animated=False)
    scene.run(TetrisGame(), show_fps=True) # Alternative way to run
