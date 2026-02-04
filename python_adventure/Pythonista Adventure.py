# port Colossal  Caves to Pythonista
# using adventure by Brandon Rhodes
# implement GUI in ui.View
# instead of using the console.
# implement onscreen minimal qwerty keyboard
# and predictive buttons to select options
# new code will use adventure classes and functions
# TextView will receive game output
# game input will receive TexField change
# need to override save and resume to use fixed savefile
# Chris Thomas Feb 2026

import ui
import re
import os
import sys
import pathlib
from time import sleep
from collections import defaultdict
from operator import attrgetter
from objc_util import on_main_thread
from adventure.game import Game
from adventure.data import parse
from qwerty_keyboard import QWERTYKeyboard
from change_screensize import get_screen_size
import csv
import traceback
# Increase to a higher value, e.g., 10000
sys.setrecursionlimit(10000)

               
class Adventure():
  
  def __init__(self, walkthru=None):
      self.walkthru = walkthru
      self.response = None
      self.seed = 0
      self.zoom_level = .25
      self.delay = .5
      self.quit_ = False
      self.pause_run = False
      self.input_word = ''
      self.command_words = ['', '']
      self.word_no = 0
      if walkthru:
          walkthru = pathlib.Path('adventure', 'tests', walkthru)
          self.get_walkthru(walkthru)
      # print(self.seed)
      self.game_ = Game(self.seed)
      self.load_advent_dat(self.game_)
      self.game_visited_locations = []
      self.load_location_map()
      # self.get_travel_network()
      self.get_vocabulary(_print=False)
      self.setup_ui_pyui()
      self.set_predict_buttons([('yes', 'black'), ('no', 'black')])
      self.draw_position_on_map(rooms=range(1, 140), blanks=False)
      self.run()

  def run(self):
      self.game_.start()
      self.output_frame.text += self.capitalize_sentences(self.game_.output)
      self.scroll_to_bottom()
      # self.game_.lamp_turns = 150 # limited power
      if self.walkthru:
          walkthru = pathlib.Path('adventure', 'tests', self.walkthru)
          self.run_walkthru(walkthru)
      else:
          # respond to gui
          pass
                  
  def get_vocabulary(self, _print=False):
      vocabulary = defaultdict(list)
      for word in self.game_.vocabulary.values():
         vocabulary[word.kind].append(word.text)
      self.vocabulary = {key: sorted(list(set(words))) for key, words in vocabulary.items()}
      if _print:
          for kind, words in self.vocabulary.items():
              print(kind.upper(), words)
      
  def get_travel_network(self):
      """ get all interconnected locations """
      table = {}
      for room, room_data in self.game_.rooms.items():
         link_desc = f'{room_data.travel_table}'
         link_desc = self.replace_statements(
             link_desc,
             [("YOU'RE IN ", ""), ("YOU'RE AT ", ""),
              (".\n", ""), ("YOU'RE ", ""),
              ("YOU ARE IN A ", "")])
         table[room] = f' {link_desc.lower()}'
         
      for room, links in table.items():
          print(f'{room}-> {links}')
      return table
      
  def load_advent_dat(self, data):
      """ load and parse datafile to produce self.game_ """
      datapath = os.path.join(os.path.dirname(__file__), 'adventure', 'advent.dat')
      with open(datapath, 'r', encoding='ascii') as datafile:
          parse(data, datafile)
                       
  def load_location_map(self):
      """ read location map with x,y locations on Map.JPG """
      with open('locations.csv', newline='') as csvfile:
          reader = csv.DictReader(csvfile)
          self.locations = {}
          for row in reader:
              self.locations[int(row['ID'])] = {'Label': row['Label'], 'x': float(row['x']), 'y': float(row['y'])}
                 
  def trap_save_resume(self, words):
      """ handle save, restore keywords.
      remove these and implement save and restore
      this is done to allow use of a single savefile
      """
      match words[0]:
          case 'save':
              self.save_game(None)
              return None
          case 'resume':
              self.restore_game(None)
              return None
      return words
      
  def save_game(self, send_commander):
      """ save the game in fixed file,
      deleting previous version"""
      self.pause_game(None)
      savefile = 'temp.pkl'
      if os.path.exists(savefile):
          os.remove(savefile)
      self.game_.t_suspend('save', savefile)
      self.pause_game(None)
      self.output_frame.text += 'GAME SAVED\n'
      
  def restore_game(self, sender):
      self.pause_game(None)
      savefile = 'temp.pkl'
      self.game_ = self.game_.resume(savefile)
      self.pause_game(None)
      self.output_frame.text += 'GAME RESTORED\n'
      self.send('look')
      self.show_inventory()
      
  def capitalize_sentences(self, text):
      # This regex finds the first character of the string OR
      # any character that follows a '.', '!', or '?' and optional whitespace.
      # We use a lambda function to uppercase the matched character.
      text = text.lower()
      return re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
         
  def run_walkthru(self, walkthru):
      """ iterate through specified walkthru """
      for command in self.get_walkthru(walkthru):
          if self.quit_:
              break
          while self.pause_run:
              # allow suspend of game with pause button
              sleep(.1)
          self.send(command)
          sleep(self.delay)
         
  @staticmethod
  def replace_statements(commandlist, to_replace):
      for replace_ in to_replace:
          if isinstance(commandlist, list):
              commandlist = [command.replace(*replace_) for command in commandlist]
          else:
              commandlist = commandlist.replace(*replace_)
      return commandlist
      
  @staticmethod
  def remove_statements(commandlist, to_remove):
      for remove_ in to_remove:
          commandlist = [w for w in commandlist if not w.startswith(remove_)]
      return commandlist
                          
  def get_walkthru(self, filename):
      """ process walkthrough text """
      def extract_between(text):
          # Regex breakdown:
          # >>>    : Matches the literal characters '>>> '
          # (.*?)  : Captures any character (except newline) in a group
          #          The '?' makes it non-greedy (stops at the first \n)
          # \n     : Matches the literal newline character
          pattern = r'>>> (.*?)\n'
          return re.findall(pattern, text)
         
      with open(filename, 'r') as f:
          d = f.read()
      commandlist = extract_between(d)
      commandlist = self.replace_statements(commandlist, [('(', ' '), (')', ''), ('adventure.', '')])
      
      # get seed
      for w in commandlist:
          if w.startswith('play'):
              self.seed = int(w[-1])
              break
      commandlist = self.remove_statements(commandlist, ['import', 'play', 'savefile'])
      return commandlist
               
  # GUI PROCESSING ############################################
  def layout(self):
      # 1. Setup Constants
      sidebar_w = self.width * 0.3
      output_h = self.height * 0.55
      main_w = self.width - sidebar_w
      row_h = 44  # Fixed height for input/prediction bars
      
      # 2. Position Left Column
      self.output_frame.frame = (0, 0, main_w, output_h)
      
      y_offset = self.output_frame.height
      self.input_frame.frame = (0, y_offset, main_w, row_h)
      
      y_offset += row_h
      self.prediction_frame.frame = (0, y_offset, main_w, row_h)
      
      y_offset += row_h
      self.custom_view.frame = (0, y_offset, main_w, (self.height - y_offset))
      
      # 3. Position Right Column (Sidebar)
      self.scroll.frame = (main_w, 0, sidebar_w, self.output_frame.height + (row_h * 2))
      
      # Inventory takes the remaining space on the bottom right
      inv_y = self.scroll.height
      self.inventory_frame.frame = (main_w, inv_y, sidebar_w, self.height - inv_y)
      
  @on_main_thread
  def setup_ui_pyui(self):
      self.width, self.height = get_screen_size()
      self.frame = ui.load_view('Python_adventure.pyui')
      self.add_buttons()
      self.frame.left_button_items = [self.exit, self.pause, self.save, self.restore]
      self.frame.right_button_items = [self.zoomin, self.zoomout]
      self.frame.name = 'Adventure'
      self.frame.frame = (0, 0, self.width, self.height)
      self.frame.flex = 'WH'
      for subview in self.frame.subviews:
          setattr(self, subview.name, self.frame[subview.name])
      self.layout()
      # deal with keyboard, tricky to get this positioned correctly
      x, y, w, h = self.custom_view.frame
      self.keyboard = QWERTYKeyboard(frame=(0, 0, 0.95 * w, 0.8*h), action=self.button_tapped)
      keyboard_off = ((x + w/2) - (0.975*w/2), (y + h/3) - (0.975*h/2), 0.95*w, 0.8*h)  # empirical
      self.keyboard.frame = keyboard_off
      self.keyboard.layout()
      self.frame.add_subview(self.keyboard)
      for key in self.keyboard.subviews:
         if key.title == 'Enter':
             self.return_key = key
             break
      for key in self.keyboard.subviews:
         if key.title == 'Space':
             self.space_key = key
             break
                      
      self.output_frame.autocapitalization_type = ui.AUTOCAPITALIZE_SENTENCES
      self.input_frame.action = self.next_command
      self.prediction_frame.directional_lock_enabled = True
               
      self.inventory_frame.autocapitalization_type = ui.AUTOCAPITALIZE_SENTENCES
                
      # place a scrollable map
      self.map_image = ui.Image.named('Map.JPG')
      image_w, image_h = self.map_image.size
      # If you miss this, it won't scroll!
      self.scroll.content_size = image_w, image_h
      self.map_frame = ui.ImageView(frame=(0, 0, image_w, image_h))
      self.map_frame.image = self.map_image
      self.overlay = ui.ImageView(frame=(0, 0, image_w, image_h))
      self.scroll.add_subview(self.map_frame)
      self.map_frame.add_subview(self.overlay)
      # self.frame.size_to_fit()
      self.frame.present('popover', popover_location=(0, 0))
               
  def set_predict_buttons(self, matches):
      fontsize = 20
      spacing = 8
      
      # 1. Calculate the total width of all buttons combined
      total_content_width = sum((len(word) * fontsize * 0.8) + spacing for word, color in matches)
      
      # 2. Determine the starting X (Container width minus content width)
      # We use max() to ensure it doesn't go off-screen to the left if content is too wide
      container_width = self.prediction_frame.width
      start_x = max(spacing, container_width - total_content_width)
      
      x = start_x
      for word, color in matches:
          button = ui.Button(title=word, action=self.select_predict_word)
          width = len(word) * fontsize * 0.8
          
          button.frame = (x, 10, width, 1.2 * fontsize)
          button.font = ('Avenir Next', fontsize)
          button.tint_color = color
          button.border_width = 1
          button.border_color = 'black'
          
          self.prediction_frame.add_subview(button)
          x += (width + spacing)
      return x
          
  def prediction(self, letters, word_no=0, compass=None):
      """ create a set of buttons with words starting with current letters"""
      # remove all buttons
      children = self.prediction_frame.subviews
      for child in children:
          self.prediction_frame.remove_subview(child)
          
      colors = {'travel': 'black',
                'noun': 'blue',
                'verb': 'green',
                'snappy_comeback': 'red'}
      # these words will list inventory
      list_inventory_items = ('detonate', 'devour', 'discard', 'drink', 'drop',
                              'dump', 'eat', 'extinguish', 'fill', 'ignite',
                              'light', 'pour', 'rub', 'shake',
                              'swing', 'throw', 'toss', 'wave')
      # these words will list objects at location
      list_objects_here_items = ('attack', 'blast', 'blowup', 'break', 'calm',
                                 'capture', 'carry', 'catch', 'close', 'disturb',
                                 'explore', 'feed', 'fight', 'find', 'follow',
                                 'free', 'get', 'hit', 'keep', 'kill',
                                 'lock', 'open', 'peruse', 'placate', 'pour', 'read',
                                 'release', 'rub', 'say', 'shatter', 'sing', 'smash',
                                 'steal', 'strike', 'take', 'tame', 'tote',
                                 'turn', 'unlock', 'utter', 'wake')
      if compass:
         matches = [(dir, colors['travel']) for dir in ['North', 'South', 'East', 'West', 'Up', 'Down']]
         try:
           if self.game_.inventory or self.game_.objects_here:
              matches.extend([('Drop', colors['verb']), ('Get', colors['verb'])])
         except AttributeError:
             pass
      elif letters:
          # matches will be a list of word, color tuples
          if word_no == 0:
              keys = ['travel', 'verb', 'snappy_comeback']
          else:
              keys = ['travel', 'noun', 'snappy_comeback']
          vocab = [(word, colors[k]) for k in keys for word in self.vocabulary[k]]
          matches = [(word, color) for word, color in vocab if word.startswith(letters)]
          matches = sorted(matches, key=lambda x: len(x[0]))
      else:
          match self.command_words[0].lower():
              case word if word in list_objects_here_items:
                  matches = [(obj.names[0], colors['noun']) for obj in self.game_.objects_here]
                  # print(matches)
              case word if word in list_inventory_items:
                  matches = [(obj.names[0], colors['noun']) for obj in self.game_.inventory]
                  # print(matches)
              case _:
                  matches = []
      
      width = self.set_predict_buttons(matches)
      self.prediction_frame.content_size = (width, 50)
      
  def select_predict_word(self, sender):
      """ called when pressing match word buttons """
      letter = sender.title
      self.input_word = letter.lower()
      self.command_words[self.word_no] = self.input_word
      self.input_frame.text = ' '.join(self.command_words)
      if self.command_words[0] in ['north', 'south', 'east', 'west', 'up', 'down']:
         self.button_tapped(self.return_key)
         return
      if self.word_no == 0:
          self.button_tapped(self.space_key)
      else:
          self.button_tapped(self.return_key)
       
  def show_inventory(self):
      """ display current inventory """
      max_length = 40
      inventory = self.game_.inventory
      if not inventory:
          return
      inventory_message = 'INVENTORY\n'
      msg = []
      inventory = sorted(inventory, key=attrgetter('inventory_message'))
      for obj in inventory:
         inventory_text = obj.inventory_message.capitalize()
         inventory_names = '/'.join(obj.names)
         if 'lamp' in inventory_names:
             inventory_names += f' power {self.game_.lamp_turns}'
         msg.append(f'{inventory_text} ({inventory_names})')
                              
      self.inventory_frame.text = '\n'.join(msg)
                   
  def button_tapped(self, sender):
      try:
         letter = sender.title
         match letter:
             case str(letter) if len(letter) == 1 and letter.isalpha():
                 self.input_word += letter.lower()
                 # Trigger matching logic
                 self.prediction(self.input_word, self.word_no)
                 self.command_words[self.word_no] = self.input_word
                 
             case 'Return' | 'Enter':
                 # Finalize command
                 self.input_frame.text = ' '.join(self.command_words).strip()
                 self.next_command(self.input_frame)
                 self.input_frame.text = ''
                 self.input_word = ''
                 self.command_words = ['', '']
                 self.word_no = 0
                 self.prediction('', 0, compass=True)
                 self.scroll_to_bottom()
                 
             case 'Del' | '⌫':
                 self.input_word = self.input_word[:-1]
                 
             case 'Space':
                 # Commit current word to the list
                 if self.word_no < len(self.command_words):
                     self.command_words[self.word_no] = self.input_word
                 self.input_word = ''
                 self.word_no = 1
                 self.prediction('', 1, compass=False)

      except Exception:
          print(traceback.format_exc())

      # UPDATE: Include the active input_word so you can see it while typing
      display_list = list(self.command_words)
      if self.word_no < len(display_list):
          display_list[self.word_no] = self.input_word
          
      self.input_frame.text = ' '.join(display_list).strip()
      
  def next_command(self, sender):
      cmd_text = sender.text.lower().strip()
      if not cmd_text:
          return
      
      self.output_frame.text += f'\n>>> {cmd_text.upper()}\n'
      words = cmd_text.split()
      words = self.trap_save_resume(words)
      # print('words to send', words)
      if words:
          self.game_.do_command(words)
          self.output_frame.text += f'loc({self.game_.loc.n}) {self.capitalize_sentences(self.game_.output)}'
             
          # Immediate UI Updates
          self.game_visited_locations.append(self.game_.loc.n)
          self.draw_position_on_map(rooms=self.game_visited_locations, blanks=True)
          self.show_inventory()
          self.scroll_to_bottom()
      
  def create_mask_overlay(self):
      w, h = self.map_frame.width, self.map_frame.height
      with ui.ImageContext(w, h) as ctx:
          # 1. Draw the base grey rectangle
          ui.set_color((0, 0, 0, 0.9))  # Grey with 60% opacity
          ui.Path.rect(0, 0, w, h).fill()
      return ctx.get_image()
    
  def create_holes(self, location_list, r):
      # 2. Use 'destination_out' blend mode to "punch" the hole
      # This removes the color where the next shape is drawn
      w, h = self.map_frame.width, self.map_frame.height
      
      with ui.ImageContext(w, h) as ctx:
          # 1. Draw the base grey rectangle
          ui.set_color((0, 0, 0, 0.9))  # Grey with 60% opacity
          base_path = ui.Path.rect(0, 0, w, h)
          base_path.fill()
          ui.set_blend_mode(ui.BLEND_DESTINATION_OUT)
          ui.set_shadow('black', 0, 0, 30)
          # combine the holes to a single path for speed
          # fill and blend are slow
          combined_path = ui.Path()
          for _, x, y in location_list:
              combined_path.append_path(ui.Path.oval(x - r, y - r, r * 2, r * 2))
          combined_path.fill()
          overlay_image = ctx.get_image()
      return overlay_image
          
  def draw_dots(self, location_list, radius):
      for n, x, y in location_list:
          path = ui.Path.oval(x - radius, y - radius, radius * 2, radius * 2)
          ui.set_color('blue')
          path.stroke()
          if n == location_list[-1][0]:
              ui.set_color('red')
          else:
              ui.set_color('cyan')
          path.fill()
          ui.draw_string(str(n),
                         rect=(x-radius, y-radius, x+radius, y+radius),
                         font=('<system>', 12),
                         color='black',
                         alignment=ui.ALIGN_LEFT)
        
  def draw_position_on_map(self, rooms, blanks=True):
      # rooms is a list
      radius = 10
      r = 15 * radius
      w, h = self.map_frame.width, self.map_frame.height
      location_list = []
      for room in rooms:
          try:
              x, y = (self.locations[room]['x'], self.locations[room]['y'])
              x, y = x * w, y * h
              location_list.append((room, x, y))
          except (AttributeError, KeyError):
              pass
      
      with ui.ImageContext(w, h) as ctx:
          self.map_image.draw(0, 0, w, h)
          self.overlay.image = None
          ui.set_blend_mode(ui.BLEND_NORMAL)
          self.draw_dots(location_list, radius)
          self.map_frame.image = ctx.get_image()
      if blanks:
          self.overlay.image = self.create_holes(location_list, r)
      self.center_on_point(x, y)
                             
  @on_main_thread
  def center_on_point(self, x, y):
      # 1. Calculate the center of the scrollview's visible frame
      half_width = self.scroll.width / 2
      half_height = self.scroll.height / 2
      
      # 2. Determine the new top-left corner (offset)
      off_x = x - half_width
      off_y = y - half_height
      
      # 3. Constrain the offsets so we don't scroll into 'dead space'
      # Max offset is (content_size - frame_size)
      max_x = max(0, self.scroll.content_size[0] - self.scroll.width)
      max_y = max(0, self.scroll.content_size[1] - self.scroll.height)
      
      final_x = min(max(0, off_x), max_x)
      final_y = min(max(0, off_y), max_y)
      
      # 4. Apply the offset
      self.scroll.content_offset = (final_x, final_y)
         
  @on_main_thread
  def scroll_to_bottom(self):
      # Get the total length of the text
      # need this delay to allow content to be updated
      sleep(0.4)
      self.output_frame.content_offset = (0, self.output_frame.content_size[1]-self.output_frame.height)
            
  def add_buttons(self):
      self.exit = ui.ButtonItem(title='Exit', action=self.quit, tint_color='black')
      self.pause = ui.ButtonItem(title='Pause', action=self.pause_game, tint_color='black')
      self.save = ui.ButtonItem(title='Save', action=self.save_game, tint_color='black')
      self.restore = ui.ButtonItem(title='Restore', action=self.restore_game, tint_color='black')
      self.zoomin = ui.ButtonItem(title='ZoomIn', action=self.zoom, tint_color='black')
      self.zoomout = ui.ButtonItem(title='ZoomOut', action=self.zoom, tint_color='black')
      
  def quit(self, sender):
      self.frame.close()
      self.quit_ = True
      sys.exit()
      
  def pause_game(self, sender):
      self.pause_run = not self.pause_run
      self.pause.tint_color = 'red' if self.pause_run else 'black'
   
  def send(self, txt):
      """ programmatically send text """
      self.command_words = txt.split(' ')
      self.button_tapped(self.return_key)
          
  @on_main_thread
  def zoom(self, sender):
      image_w, image_h = self.map_image.size
      if sender is self.zoomout:
          if self.zoom_level > 0.25:
              self.zoom_level -= 0.1
      else:
          self.zoom_level += 0.1
      # print(self.zoom_level)
      new_w = int(image_w * self.zoom_level)
      new_h = int(image_h * self.zoom_level)
      self.map_frame.frame = (0, 0, new_w, new_h)
      self.overlay.frame = (0, 0, new_w, new_h)
      self.scroll.content_size = (new_w, new_h)
      self.scroll.set_needs_display()

                                           
if __name__ == '__main__':
   Adventure(walkthru="walkthrough2.txt")

