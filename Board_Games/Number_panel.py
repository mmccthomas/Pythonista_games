# coding: utf-8

import ui


class NumberPanel(ui.View):
  view_main = None
  
  def __init__(self, gui, position=(100,100), present=True, allows_multiple_selection=False):
    super().__init__(self)
    NumberPanel.view_main = ui.load_view()
    self.gui = gui
    self.buttons = [NumberPanel.view_main[f'button{n}'] for n in range(1,10)]
    self.position = position
    NumberPanel.view_main.frame = (self.position[0], self.position[1], 357, 257)
    self.multiple_selection =  allows_multiple_selection
    if present:
        NumberPanel.view_main.present('sheet')

  def button_tapped(self, sender):
    '@type sender: ui.Button'
    # Get the button's title for the following logic:
    t = sender.title
    # Get the labels:
    label = sender.superview['label1']
    items = []
    if t in '0123456789':    
        if not self.multiple_selection:
          sender.background_color='yellow'
          if self.gui:
             self.gui.selection = t
             self.gui.selection_row = None
          sender.background_color='white'
        else:
          sender.background_color='yellow'
          items.append(t)
          
    if t == 'Return':
       if self.gui:
           self.gui_selection = items.copy()
           self.gui.selection_row = None
       items = []
       for button in self.buttons:
          button.background_color='white'
        
  
def main():
  NumberPanel(None, position=(100,100), allows_multiple_selection=False)
  
if __name__ == '__main__':
  main()

  
  

