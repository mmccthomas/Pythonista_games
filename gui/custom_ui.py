import ui
import sound


class TickedSliderView(ui.View):
    """A slider with a tick-mark background that handles real-world value mapping.
       Calling sender.value returns real word value
       call sender.label.text = ... to set label"""
    def __init__(self, min_val=0, max_val=360, num_ticks=24, major_ticks_every=8,
                 labels=None, action=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Range and Logic
        self.min_val = min_val
        self.max_val = max_val
        self.num_ticks = num_ticks
        self.major_ticks_every = major_ticks_every
        self.tick_labels = labels
        self.external_action = action

        # 1. The Label (Top)
        self.label = ui.Label(frame=(0, 0, self.width, 20), flex='W')
        self.label.font = ('<system>', 14)
        self.label.text_color = '#333'
        self.add_subview(self.label)

        # 2. The Slider (Middle)
        self.slider = ui.Slider(flex='W')
        self.slider.background_color = 'transparent'
        self.slider.continuous = False  # Smoother UI updates
        self.slider.action = self._internal_action
        self.add_subview(self.slider)

        # 3. The Tick Drawing Layer (Overlay)
        self.overlay = ui.View(flex='WH')
        self.overlay.touch_enabled = False
        self.overlay.background_color = 'clear'
        self.overlay.alpha = 0.1
        # self.overlay.draw = self.draw_ticks
        self.add_subview(self.overlay)
        for k, v in kwargs.items():
          setattr(self, k, v)
        if hasattr(self, 'color'):
           self.overlay.background_color = self.color
        # Initial UI update
        self.value = min_val

    @property
    def value(self):
        """Returns the mapped real-world value."""
        return self.min_val + (self.slider.value * (self.max_val - self.min_val))

    @value.setter
    def value(self, val):
        """Sets the slider position based on a real-world value."""
        # Clamp value between min and max
        val = max(self.min_val, min(self.max_val, val))
        self.slider.value = (val - self.min_val) / (self.max_val - self.min_val)
        self._update_ui_elements()

    def _internal_action(self, sender):
            
        # 1. Calculate which 'tick' we are closest to (0.0 to 1.0)
        tick_step = 1.0 / self.num_ticks
        snapped_fraction = round(sender.value / tick_step) * tick_step
        
        # 2. Update the slider handle position visually
        sender.value = snapped_fraction
        sound.play_effect('ui:click5')
        # 3. Update the label and notify the parent
        self._update_ui_elements()
        if callable(self.external_action):
            self.external_action(self)
        
    def set_text(self, text):
        self.label.text = text
        
    def _update_ui_elements(self):
        self.label.text = f"{int(self.value)}°"
        # If you want ticks to change color or highlights, trigger a redraw:
        # self.overlay.set_needs_display()

    def layout(self):
        # Center the slider vertically
        self.slider.frame = (0, (self.height - 32)/2 + 5, self.width, 32)
        self.overlay.frame = self.bounds
        self.label.frame = (10, 0, self.width, 20)

    def draw(self):
        ui.background = 'red'
        margin = 16
        track_width = self.width - (margin * 2)
        mid_y = self.height / 2 + 5
        
        ui.set_color('black')
        path = ui.Path()
        path.line_width = 1
        
        # Map labels to specific tick indices
        label_map = {}
        if self.tick_labels is not None:
            M = len(self.tick_labels)
            for i, text in enumerate(self.tick_labels):
                idx = round(i * self.num_ticks / (M - 1))
                label_map[idx] = str(text)

        for i in range(self.num_ticks + 1):
            x = margin + (i * (track_width / self.num_ticks))
            
            # Draw Ticks
            is_major = (i % self.major_ticks_every == 0)
            length = 15 if is_major else 5
            path.move_to(x, mid_y - length)
            path.line_to(x, mid_y + length)
            
            # Draw Text for mapped labels
            if i in label_map:
                ui.draw_string(label_map[i],
                               rect=(x - 18, mid_y + 18, 36, 12),
                               font=('<system>', 10),
                               color='black',
                               alignment=ui.ALIGN_CENTER)
        path.stroke()
            
