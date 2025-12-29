# class to add suplementary panels to Gui
# scrollbox
# input_text_list (a smarter list)
# letter panel
# number panel
import ui

class GuiPanel():
 
    def __init__(self, parent):
        self.v = parent.v
        self.gs = parent.gs
        self.selection = ''
        self.selection_row = 0
        self.selection_rows = []
        
        # Panel-specific attributes
        self.number_panel = None
        self.letter_panel = None
        self.text_box = None
        self.number_items = []
        self.letter_items = []
        self.buttons = []
        self.prompt = None
        self._panel = None
        self._itemlist = None
        
        # Default settings
        self.font = ('Avenir Next', 32)
        self.width = 200
        self.allows_multiple_selection = False
        self.autocorrect_type = False
     
     
    def scrollview_h(self, x, y, w, h, text='', **kwargs):       
            scroll_view = ui.ScrollView()
            scroll_view.frame = (x,y,w,h)
            scroll_view.anchor_point=(0,0)
            text_view = ui.TextView()
            text_view.text = text
            scroll_view.add_subview(text_view)
            self.v.add_subview(scroll_view)
            x, y, w, h = scroll_view.bounds
            scroll_view.content_size = w * 2, h
            for k, v in kwargs.items():
                setattr(scroll_view, k, v)
            text_view.frame = x, y, w * 2, h
            return scroll_view, text_view
        
    def scroll_text_box(self, text='', **kwargs):
        """ create a scroll view"""
        scrollview = ui.TextView(bg_color='black')
        scrollview.border_color = 'white'
        scrollview.corner_radius = 10
        scrollview.border_width = 2
        scrollview.name = 'chris'
        scrollview.text = text
        scrollview.color = 'white'
        scrollview.bg_color = 'black'
        scrollview.text_color = 'white'
        scrollview.shows_vertical_scroll_indicator = True
        for k, v in kwargs.items():
            setattr(scrollview, k, v)
        self.v.add_subview(scrollview)
        return scrollview

    def input_text_list(self, prompt='', position=None, items=None, **kwargs):
        ''' show a single line text box with an ok and a cancel button
        try to adapt size to number of list items'''
        if position is None:
            # place to right of game field
            x, y, w, h = self.gs.game_field.bbox
            position = (x + w + 100, 40)
        self.font = ('Avenir Next', 32)
        self.width = 200
        self.allows_multiple_selection = False
        self.autocorrect_type=False

        for k, v in kwargs.items():
            setattr(self, k, v)

        # allow for 2 lines of prompt
        self.text_box = ui.View(bg_color='lightgrey',
                                frame=(position[0], position[1], self.width, 550))
        lb = ui.ButtonItem(image=ui.Image.named('iob:close_32'),
                           enabled=True,
                           action=self.cancel)
        self.text_box.left_button_items = [lb]
        self.data = ui.ListDataSource(items=items)
        if self.allows_multiple_selection:
            pass
        else:
            self.data.action = self.text_input
        # set table size to hold data
        no_items = len(items)
        req_height = no_items * self.font[1] * 1.40
        height = min(req_height, 400)
        self.t = ui.TableView(name='text',
                              frame=(10, 45, self.width - 30, height),
                              font=self.font,
                              text_color='black',
                              bordered=True,
                              autocorrect_type=self.autocorrect_type)
        # change frame size to fit list
        self.text_box.frame = (0, 0, self.width, height + 55)
        self.t.data_source = self.t.delegate = self.data
        self.t.allows_multiple_selection = self.allows_multiple_selection
        self.text_box.add_subview(self.t)

        label = ui.Label(frame=(5, 5, self.width - 20, 40),
                         font=('Avenir Next', 18),
                         text=prompt,
                         number_of_lines=0,
                         line_break_mode=ui.LB_WORD_WRAP)
        self.text_box.add_subview(label)
        if self.allows_multiple_selection:
            # Enter button
            rb = ui.ButtonItem(
                image=ui.Image.named('iob:arrow_return_left_32'),
                action=self.enter)
            self.text_box.right_button_items = [rb]

        if self.gs.device.startswith('ipad'):
            self.text_box.present('popover', popover_location=position)
        else:  # iphone
            self.text_box.present('sheet')
        # self.v.add_subview(self.text_box)
        return self.text_box

    def enter(self, sender):
        ''' completes multiple selection '''
        selected_rows = self.t.selected_rows  # a list of (section, row)
        data = [self.data.items[row] for _, row in selected_rows]
        self.selection = data
        self.selection_rows = self.t.selected_rows
        try:
            sender.superview.close()
            # self.v.remove_subview(self.text_box)
        except (AttributeError):
            self.text_box.close()
            # self.v.remove_subview(self.text_box)

    def text_input(self, sender):
        self.selection = sender.items[sender.selected_row]
        self.selection_row = sender.selected_row
        sender.tableview.superview.close()
        # self.v.remove_subview(self.text_box)

    def cancel(self, sender):
        self.selection = 'Cancelled_'
        try:
            sender.superview.close()
            # self.v.remove_subview(self.text_box)
        except (AttributeError):
            self.text_box.close()
            # self.v.remove_subview(self.text_box)

    def button_tapped(self, sender):
        '@type sender: ui.Button'
        # Get the button's title for the following logic:
        t = sender.title
        # get calling item are we in number panel or letter panel
        # print(sender.superview.name)
        if sender.superview.name == 'Letters':
           self._panel = self.letter_panel
           self._itemlist = self.letter_items
        else:
            self._panel = self.number_panel
            self._itemlist = self.number_items           

        # Get the labels:
        label = sender.superview['label1']
        if t.isnumeric():
            if not self.number_panel.allows_multiple_selection:
                sender.background_color = 'yellow'
                self.selection = t
                self.selection_row = None
                sender.background_color = 'white'
                sender.superview.close()
                self.v.remove_subview(self.number_panel)
            else:
                sender.background_color = 'yellow'
                if t in self.number_items:
                    self.number_items.remove(t)
                    sender.background_color = 'white'
                else:
                    self.number_items.append(t)
                    self.prompt.text = ' '.join(self.number_items)

        elif t in 'abcdefghijklmnopqrstuvwxyz ':
            if not self.letter_panel.allows_multiple_selection:
                sender.background_color = 'yellow'
                self.selection = t
                self.selection_row = None
                sender.background_color = 'white'
                sender.superview.close()
                self.v.remove_subview(self.letter_panel)
            else:
                sender.background_color = 'yellow'
                self.letter_items.append(t)
                self.prompt.text = ' '.join(self.letter_items)

        elif t == 'Return':
            # send selected items
            self.selection = self._itemlist.copy()
            if hasattr(self._panel, 'letter_panel'):
                self.selection_row = self._panel.direction
            self.v.remove_subview(self._panel)

            for button in self.buttons:
                button.background_color = 'white'
            sender.superview.close()

        elif t == 'Delete':
            # remove last item
            if self._itemlist:
                removed = self._itemlist.pop()
                self.prompt.text = ' '.join(self._itemlist)
                self._panel[f'button{removed}'].background_color = 'white'

        elif t == 'Across' or t == 'Down':
            # change across or down direction
            self.letter_panel.direction = self.across_down(t)

    def across_down(self, direction):
        # a = {'across': (False, 'yellow'), 'down': (True, 'white')}
        if direction == 'Across':
            self._panel[f'button_across'].enabled = False
            self._panel[f'button_down'].enabled = True
            self._panel[f'button_down'].background_color = 'white'
            self._panel[f'button_across'].background_color = 'yellow'
        else:
            self._panel[f'button_across'].enabled = True
            self._panel[f'button_down'].enabled = False
            self._panel[f'button_down'].background_color = 'yellow'
            self._panel[f'button_across'].background_color = 'white'
        return direction
        
    def align_frame(self, number_panel, position, align):
        x, y = position
        match align:
            case (0, 0): # TL
                return (x, y,
                        number_panel.frame.w,
                        number_panel.frame.h)
            case (1, 0): #TR
                return (x-number_panel.frame.w, y,
                        number_panel.frame.w,
                        number_panel.frame.h)
            case (0, 1): #BL
                return (x, y-number_panel.frame.h,
                        number_panel.frame.w,
                        number_panel.frame.h)
            case (1, 1): #BR
                return (x-number_panel.frame.w, y-number_panel.frame.h,
                        number_panel.frame.w,
                        number_panel.frame.h)
            case (0.5, 0.5): #CENTRE
                return (x-number_panel.frame.w/2, y-number_panel.frame.h/2,
                        number_panel.frame.w,
                        number_panel.frame.h)
    def input_numbers(self,
                      prompt='',
                      position=None,
                      items=None,
                      panel='Number_panel.pyui',
                      align = (0,0),
                      **kwargs):
        """ pop up a number panel """
        # if panel != 'Number_panel.pyui':
        self.number_panel = ui.load_view(panel)
        self.buttons = [
            button for button in self.number_panel.subviews
            if isinstance(button, ui.Button)
        ]
        self.prompt = self.number_panel['prompt']
        self.prompt.text = prompt
        self.prompt.font = ('Avenir Next', 30)
        self.position = position
        self.align = align
        self.number_panel.frame = self.align_frame(self.number_panel, self.position, self.align)
        self.number_panel.allows_multiple_selection = False
        for k, v in kwargs.items():
            setattr(self.number_panel, k, v)
        self.number_items = []
        self._panel = self.number_panel
        self._itemlist = self.number_items     
        self.v.add_subview(self.number_panel)
        return self.number_panel

    def input_letters(self, prompt='', position=None, items=None, **kwargs):
        """ pop up a letter panel """
        self.letter_panel = ui.load_view('Letter_panel.pyui')
        self.buttons = [
            self.letter_panel[f'button{n}']
            for n in 'abcdefghijklmnopqrstuvwxyz '
        ]
        self.prompt = self.letter_panel['prompt']
        self.prompt.text = prompt
        self.prompt.font = ('Avenir Next', 30)
        self.position = position
        self.letter_panel.frame = (self.position[0], self.position[1], 345,
                                   550)
        self.letter_panel.allows_multiple_selection = False
        self.letter_panel.direction = 'Across'
        for k, v in kwargs.items():
            setattr(self.letter_panel, k, v)
        self.letter_items = []
        self._panel = self.letter_panel
        self._itemlist = self.letter_items
        self.across_down(self.letter_panel.direction.capitalize())

        self.v.add_subview(self.letter_panel)
        return self.letter_panel
