import ui

class QWERTYKeyboard(ui.View):
    def __init__(self, frame=None, action=None ):
        # Define rows with weights (Character, Weight)
        self.layout_data = [
            [('Q', 1), ('W', 1), ('E', 1), ('R', 1), ('T', 1), ('Y', 1), ('U', 1), ('I', 1), ('O', 1), ('P', 1)],
            [(' ', 0.5),('A', 1), ('S', 1), ('D', 1), ('F', 1), ('G', 1), ('H', 1), ('J', 1), ('K', 1), ('L', 1), (' ', 0.5)],
            [(' ', 1),('Z', 1), ('X', 1), ('C', 1), ('V', 1), ('B', 1), ('N', 1), ('M', 1), ('Enter', 2)],
            [(' ', 1), ('Space',6),('⌫', 1),(' ', 2)]
        ]
        if frame:
            self.frame = frame
        # Create buttons programmatically (cleaner than manual pyui placement)
        self.btns = []
        for row in self.layout_data:
            for char, weight in row:
                btn = ui.Button(title=char)
                btn.background_color = '#ffffff'
                btn.tint_color = 'black'
                btn.corner_radius = 10
                btn.weight = weight # Custom property for scaling
                if action:
                    btn.action = action
                self.add_subview(btn)
                self.btns.append(btn)
        #self.layout()
        self.background_color = '#d1d4d9' # Classic keyboard grey
        
    def layout(self):
        # Configuration
        pad = 4
        row_h = (self.height - (pad * (len(self.layout_data) + 1))) / len(self.layout_data)
        
        btn_idx = 0
        for r_idx, row in enumerate(self.layout_data):
            # Calculate total weight of this row to determine unit width
            total_weight = sum(item[1] for item in row)
            unit_w = (self.width - (pad * (len(row) + 1))) / total_weight
            
            current_x = pad
            y = r_idx * (row_h + pad) + pad
            
            for char, weight in row:
                btn = self.btns[btn_idx]
                w = unit_w * weight
                btn.frame = (current_x, y, w, row_h)
                
                # Dynamic font scaling
                btn.font = ('<system-bold>', max(10, row_h * 0.3))
                
                current_x += w + pad
                btn_idx += 1

if __name__ == '__main__':
   # Presenting the view
   v = QWERTYKeyboard()
   v.layout()
   v.present('full_screen')
