
import ui
from scene import *
import math

class Joystick(Node):
    """
    A Node that simulates a joystick with two concentric circles.
    Node is positioned, SpriteNodes and LabelNode are positioned 
    relative to this
    """
    def __init__(self, position, color='black', 
                 alpha=0.8, show_xy=True, msg='', 
                 deadzone_x=0.5, deadzone_y=0.5):
        # --- Configuration ---
        self.position = position
        self.joystick_radius = 100.0
        self.thumbstick_radius = 40.0
        self.joystick_color = color
        self.thumbstick_color = 'red'
        self.x = 0
        self.y = 0
        self.scale=1
        self.keys_pressed = set()
        self.deadzone_x = deadzone_x
        self.deadzone_y = deadzone_y
        # --- Private State ---
        self._is_touched = False
        
        # --- Create Nodes ---
        # The background for the joystick
        self.outer_joystick = SpriteNode(
            'iow:disc_256',
            size=(self.joystick_radius * 2,
            self.joystick_radius * 2),
            position = (0, 0),
            color=self.joystick_color,
            alpha=alpha,
            parent=self           
        )

        # The movable inner circle (thumbstick)
        self.inner_joystick = SpriteNode('emj:Black_Circle',            
            size=(self.thumbstick_radius * 2,
            self.thumbstick_radius * 2),
            position = (0, 0),
            color=self.thumbstick_color,
            parent=self
        )
        # A label to display the output
        self.instr_label = LabelNode(
            text=msg,
            font=('Helvetica', 20),
            color='white',
            anchor_point=(0.5, 0.5),
            position = (0, self.thumbstick_radius+20),
            parent=self
        )
        # A label to display the output
        self.output_label = LabelNode(
            text='X: 0.00, Y: 0.00',
            font=('Helvetica', 20),
            color='white',
            position = (0, self.joystick_radius)
        )
        if show_xy:
            self.add_child(self.output_label)

    def touch_began(self, touch):
        """Called when a touch starts."""
        dist = touch.location - self.position        
        # Check if touch is on the thumbstick
        if math.hypot(*dist) <= self.thumbstick_radius:
            self._is_touched = True

    def touch_moved(self, touch):
        """Called when a touch moves across the screen."""
        if not self._is_touched:
            return        
        joystick_center = self.outer_joystick.position
        # Calculate vector from center to touch
        offset = touch.location - self.position
        distance = math.hypot(offset.x, offset.y)
        
        # Calculate the maximum allowed distance for the inner joystick's center
        # to ensure it stays within the outer joystick's boundary.
        # This is the outer radius minus the inner radius.
        max_distance = self.joystick_radius - self.thumbstick_radius
        # If touch is outside the allowed movement area, clamp it to the edge
        if distance > max_distance:
            # Normalize the offset vector and scale it by the new max_distance
            clamped_x = joystick_center.x + (offset.x / distance) * max_distance
            clamped_y = joystick_center.y + (offset.y / distance) * max_distance
            self.inner_joystick.position = (clamped_x, clamped_y)
        else:
            self.inner_joystick.position = offset
        
    def emit_text(self):
        if self.x < -self.deadzone_x:
            self.keys_pressed.add('left')
            self.keys_pressed.discard('right')
        elif self.x > self.deadzone_x:
            self.keys_pressed.add('right')
            self.keys_pressed.discard('left')
        else:
            self.keys_pressed.discard('left')
            self.keys_pressed.discard('right')
        if self.y > self.deadzone_y:
            self.keys_pressed.add('up')
            self.keys_pressed.discard('down')      
        elif self.y < -self.deadzone_y:
            self.keys_pressed.add('down')
            self.keys_pressed.discard('up')
        else:
            self.keys_pressed.discard('up')        
            self.keys_pressed.discard('down')      

    def touch_ended(self, touch):
        """Called when a touch ends."""
        # Reset the thumbstick to the center
        self.inner_joystick.position = self.outer_joystick.position
        self._is_touched = False

    def update(self):
        """
        calculates the normalized output.
        """
        offset = self.inner_joystick.position - self.outer_joystick.position        
                
        # Normalize the x and y positions to a range of -1.0 to +1.0
        # The divisor for normalization should now be the maximum allowed travel distance
        normalized_x = offset.x / (self.joystick_radius - self.thumbstick_radius)
        normalized_y = offset.y / (self.joystick_radius - self.thumbstick_radius)
        
        # Update the display label
        self.output_label.text = f'X: {normalized_x:.2f}, Y: {normalized_y:.2f}'
        
        self.x = normalized_x
        self.y = normalized_y
        
        self.emit_text()

# use case               
class MyScene(Scene):
  def setup(self):
     self.background_color='green'
     self.joystick = Joystick(position=Point(500, 200))
     self.add_child(self.joystick)
     
  def update(self):
    self.joystick.update()
    
  def touch_began(self, touch):
    if self.joystick.bbox.contains_point(touch.location):
       self.joystick.touch_began(touch)
       
  def touch_moved(self, touch):
    self.joystick.touch_moved(touch)
    
  def touch_ended(self, touch):
    self.joystick.touch_ended(touch)
  
# --- Run the Scene ---
if __name__ == '__main__':
    run(MyScene(), show_fps=False)
