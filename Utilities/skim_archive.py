# This Pythonista GUI allows simple browsing
# and searching of the recently released  forum archives
# it uses the json dump of the archive to list and search
# The web links in the json dump are used to fetch 
# individual pages from omz-software.com

# create a view with scrollable textview beside
# webview
# hold both open permanently
# selecting touchview item changes web address
# Chris Thomas April 2025
# https://github.com/mmccthomas

from time import sleep
import json
import ui
import re
try:
    from change_screensize import get_screen_size
except ImportError:
    from scene import get_screen_size
BASE_ADDR = 'https://omz-software.com/forum/archive'
JSON_FILE = 'JSON.json'

class WebSelection():
    def __init__(self):
        self.selection = ''
        self.offset = 0
        self.search_text = ''
        self.get_data()
        self.setup_views()
        self.run()

        
    def get_data(self):
        """ get json data dump
        find topic_id number
        and link to web page on omz-software.com
        """
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
        topics = data['topics']
        #latest first 
        self.topic_list = [f'{topic["tid"]}, {topic["title"]}'
                           for topic in topics][::-1]
        self.topic_address = {topic["tid"]: f'{BASE_ADDR}/{topic["slug"].replace("/", "_")}.html'
                              for topic in topics}
        
    def setup_views(self):
        """ Create GUI """
        
        lb = ui.ButtonItem(image=ui.Image.named('iob:skip_forward_32'),
                           enabled=True,
                           action=self.to_end)
        lb1 = ui.ButtonItem(image=ui.Image.named('iob:arrow_right_a_32'),
                            enabled=True,
                            action=self.forward_page)
        lb2 = ui.ButtonItem(image=ui.Image.named('iob:arrow_left_a_32'),
                            enabled=True,
                            action=self.back_page)
        lb3 = ui.ButtonItem(image=ui.Image.named('iob:ios7_search_strong_32'),
                            enabled=True,
                            action=self.search)
        lb4 = ui.ButtonItem(image=ui.Image.named('iob:home_32'),
                            enabled=True,
                            action=self.reset_list)
                           
        self.w, self.h = get_screen_size()
        self.main = ui.View(frame=(0, 0, self.w, self.h))
        self.main.left_button_items = [lb4, lb3, lb, lb1, lb2]
        self.main.content_size = (self.w / 2, self.h - 120)
        # Webview container
        self.wv = ui.WebView(frame=(self.w / 2, 0, *self.main.content_size),
                             bordered=True,
                             border_width=2)
        self.wv.load_url('https://omz-software.com/forum/archive/')
        
        # List to select post
        self.t = ui.TableView(
                              frame=(0, 0,  *self.main.content_size),
                              text_color='black',
                              bordered=True,
                              border_width=2)
        self.t.row_height = 30
        self.no_visible_rows = self.h / self.t.row_height - 5
        data = ui.ListDataSource(items=self.topic_list)
        data.action = self.text_input
        self.t.data_source = self.t.delegate = data
        
        # search box
        self.search_view = ui.TextField(
                frame=(self.w / 2 - 405, 5, 400, 50),
                name='textfield',
                bordered=True,
                border_width=2,
                border_color='red',
                autocapitalization_type=ui.AUTOCAPITALIZE_NONE,
                autocorrection_type=False,
                clear_button_mode='always')
        self.search_view.anchor_point = (0, 0)
        self.search_view.action = self.input_text
        
        self.main.add_subview(self.t)
        self.main.add_subview(self.wv)
        self.main.add_subview(self.search_view)
        self.search_view.send_to_back()
        self.main.present('sheet')
         
    def text_input(self, sender):
        self.selection = sender.items[sender.selected_row]
        self.selected_row = sender.selected_row
        return self.selection, self.selected_row
        
    def scroll_to(self, line):
        self.t.content_offset = (0, line * self.t.row_height)
        
    def to_end(self, sender):
        end = len(self.topic_list) - self.no_visible_rows
        self.scroll_to(end)
        
    def forward_page(self, sender):
        if self.offset < len(self.topic_list) - self.no_visible_rows:
            self.offset += self.no_visible_rows
            self.scroll_to(self.offset)
    
    def back_page(self, sender):
        if self.offset > self.no_visible_rows:
            self.offset -= self.no_visible_rows
            self.scroll_to(self.offset)
        
    def search(self, sender):
        self.search_view.bring_to_front()
        self.search_view.placeholder = 'search terms A B = any, A+B = all'
        
    def input_text(self, sender):
        self.search_text = sender.text.strip()
        sender.send_to_back()
        terms = self.search_text
        possibles = []
        if '+' in terms:
            term_list = terms.split('+')
            for topic in self.topic_list:
                if all([term.lower() in topic.lower() for term in term_list]):
                    possibles.append(topic)
        else:
            #possibles = list(self.fuzzyfinder(terms, self.topic_list))
            
            term_list = terms.split(' ')
            for topic in self.topic_list:           
                if any([term.lower() in topic.lower() for term in term_list]):           
                   possibles.append(topic)

        self.t.data_source = self.t.delegate = ui.ListDataSource(items=possibles)
        self.t.data_source.action = self.text_input
        self.t.reload()
        
    def reset_list(self, sender):
        self.t.data_source = self.t.delegate = ui.ListDataSource(items=self.topic_list)
        self.t.data_source.action = self.text_input
        self.t.reload()
               
    def did_scroll(self):
        offset = int(self.t.content_offset[1] // self.t.row_height)
        if offset != self.offset:
           self.offset = offset
           return offset
        else:
            return None
            
    def fuzzyfinder(self, input, collection, accessor=lambda x: x, sort_results=True):
        suggestions = []
        input = str(input) if not isinstance(input, str) else input
        pat = '.*?'.join(map(re.escape, input))
        pat = '(?=({0}))'.format(pat)
        regex = re.compile(pat, re.IGNORECASE)
        for item in collection:
            r = list(regex.finditer(accessor(item[0])))
            print(r)
            if r:
                best = min(r, key=lambda x: len(x.group(1)))
                print(best)
                suggestions.append((len(best.group(1)), best.start(), accessor(item), item))
        if sort_results:
            return (z[-1] for z in sorted(suggestions))
        else:
            return (z[-1] for z in sorted(suggestions, key=lambda x: x[:2]))
                    
    def run(self):
       while True:
           sleep(0.1)
           self.did_scroll()
           if self.selection != '':
              topic_no, topic_query, *a = self.selection.split(',')
              item = self.topic_address[topic_no]
              self.wv.load_url(item)
              self.selection = ''


if __name__ == '__main__':
    WebSelection()
