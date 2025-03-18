# -*- coding: utf-8 -*-
#    Kye - classic puzzle game
#    Copyright (C) 2005, 2006, 2007, 2010 Colin Phipps <cph@moria.org.uk>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
"""kye.frame - classes and data for the frame and menus for the Kye game.
frame contains menubar, statusbar and canvas
very important to add @ui.in_background decorator"""

from common import image_dict, interval, xsize, ysize, kyepaths
from os.path import basename, join
from os import listdir
import time
import ui
import defaults_cmt
import console
import dialogs
import pickle
from dialogs import _ListDialogController
from scene import *
from canvas_scene import KCanvas
from input_ui import KMoveInput
from stbar_ui import StatusBar
from dialogs_ui import GotoDialog, KyeHelpDialog, KyeAboutDialog
from dialogs_ui import getopendialog
from queue import Queue
from copy import deepcopy
""" menus has File, Level, View and Help"""


class KFrame(Scene):
    """Class implementing the frame surrounging the game area,
       including the menus and status bar."""
       
    def destroy(self, data=None):
        """Handle window destroy by exiting GUI."""
        self.view.close()
         
    def prepare_file_list(self):
      """ list recent files first latest first, then all others.
    """
      # get levels from multiple directories, sort each and flatten arrays
      # p.upper()+'.kye'
      levels = [sorted(listdir(p)) for p in kyepaths]
      # add a title line in front ofeach list
      levels =[[f'\t\t\t\t\t\t{path.upper()}.:'] + level for level, path in zip(levels, kyepaths)]
      levels = sum(levels,[])
      recent = self.recent_levels
      check_icon = ui.Image.named('iob:flag_24')
      # white so invisible
      other_icon = ui.Image.named('iow:flag_24')
      # remove any other files and recent files
      for i in levels:
        if i.split('.')[1] not in ['kye', 'KYE', ':']:
          levels.remove(i)
        if i in recent:
          levels.remove(i)
            
      # now create dictionary with icons
      recents = [{'title': i, 'accessory_type': 'checkmark'}
                 for i in reversed(recent)]
      others = [{'title': i,  'accessory_type': 'disclosure_indicator' if i.endswith(':') else 'None'} for i in levels]
      return recents + others
      
    @ui.in_background      
    def open_file_menu(self, touch):
      """button open"""
      item_list = self.prepare_file_list()
      sel = dialogs.list_dialog('Open  File.. \t\t\t\t\t\t\t\t Recent files',
                              item_list)
      if sel:
          if sel['accessory_type'] != 'disclosure_indicator':
                self.doopen(sel['title'])   
      
    def setup_view(self, v, buttons):
      ''' a list of buttons in a frame'''
      for index, button in enumerate(buttons):
        b = ui.Button()
        b.background_image = ui.Image.named('pzl:Gray8')
        b.title = button['title']
        b.tint_color = 'black'
        b.action = button['action']
        b.frame=(10,0,100,50)
        b.y = index * 55
        v.add_subview(b)
            
    def open_level_menu(self, touch):
       ''' a menu with 4 buttons '''
       buttons = [{'title': 'Restart', 'action': self.restart},
                  {'title': 'Select Level', 'action': self.startgoto},
                  {'title': 'Goto Level', 'action': self.gotolevel_name}, # not working on ipad pro
                  {'title': 'Next level', 'action': self.nextlevel},
                  {'title': 'Save state', 'action': self.savestate},
                  {'title': 'Restore state', 'action': self.restorestate}
                  ]
       l = len(buttons)
       v = ui.View(bg_color='white',frame=(0,0,120, (50 + len(buttons) * 50)))
       self.setup_view(v, buttons)
       #print(v['Restore state'])
       v.present('popover', popover_location = (220, 40))
       v.close()         
                 
    def open_view_menu(self, touch):
       buttons = [{'title': 'Tiny', 'action': self.selsize},
                  {'title': 'Small', 'action': self.selsize},
                  {'title': 'Large', 'action': self.selsize},
                  {'title': 'Cancel', 'action': self.selsize}]
       l = len(buttons)
       v = ui.View(bg_color='white',frame=(0,0,120, (20 + len(buttons) * 50)))
       self.setup_view(v, buttons)
       v.present('popover', popover_location = (330, 40))
       v.close()
       
    @ui.in_background         
    def selsize(self, responder):
       txt = responder.title
       if txt == 'Tiny':  
         self.settilesize(8)
       elif txt == 'Small':
         self.settilesize(16)
       elif txt == 'Large':
         self.settilesize(self.tilesize_original)
       else:
         pass
       responder.superview.close() 


    def __init__(self, app, settings, recentlevels=[], tilesize=16):
        """ init """
        Scene.__init__(self)
        self.app = app
        self.frame_time = interval
        self.timer = interval
        self.settings = settings
        self.saved_state = None
        self.recent_levels = recentlevels
        self.set_recent(recentlevels)
        self.tilesize = tilesize
        self.tilesize_original = tilesize
        self.__title = ['KYE   ', '']
        # if "Size" in self.settings:
        #   self.tilesize = int(self.settings["Size"])
        self.moveinput = KMoveInput()
      
    def update(self):
      """ sets delay to control game frame rate"""
      self.timer -= self.dt
      if self.timer <= 0:
        self.timer = self.frame_time
        # now trigger game tick
        self.app.do_tick()
      
    def __set_title(self):
        """(Re)set the window title."""
        self.view.superview['title'].text = "  ".join(self.__title)

    def level_title(self, file_title, level_title):
        """Update the title of the level in the window title."""
        file_title = file_title.split('.')[0]
        self.__title[1] = f'File: {file_title}  ----- Level: {level_title}'
        self.__set_title()
        self.extra_title(f'      ( {self.app._KyeApp__game.levels} levels)')

    def extra_title(self, extitle):
        """Set an addition to the window title after the level name."""
        try:
            del self.__title[2]
        except (IndexError) as e:
            pass
        if extitle is not None:
            self.__title.append(extitle)
        self.__set_title()

    def set_recent(self, recentlevels):
        """Set the list of recently-played level sets,
           for the recent files menu."""
        self.recent_levels = recentlevels
        if not recentlevels:
          return

    def opendialog(self, w):
        """Not used"""
        pass

    def restart(self, r):
        """Menu requested restart of the current level."""
        r.superview.close()
        # self.saved_state = None
        self.app.restart()       

    def doopen(self, filename):
        """Tell the game to open the given level set."""
        self.app.open(filename)
        print('attemption open ', filename)
        
    @ui.in_background   
    def gotolevel_name(self, responder):
      responder.superview.close()
      responder.superview.hidden = True
      sel = dialogs.input_alert('Level Name')
      try:
        # self.saved_state = None
        self.app.goto(sel)
      except (Exception) as e:
        dialogs.hud_alert(f'Level {sel} not known')
      #responder.superview.close()
      
    def nextlevel(self, responder):
      responder.superview.close()
      # self.saved_state = None
      self.app.goto(self.app._KyeApp__game.nextlevel)
      
    @ui.in_background    
    def startgoto(self, responder):
      """Let the user select or type a level to go to,
         and jump to that level."""
      #responder.superview.close()
      responder.superview.hidden = True
      """ add a tick to levels already completed """
      level_list = []
      for i in self.app.known_levels():
        icon = 'checkmark' if i in self.app.completed_levels() else 'none'
        level_list.append({'title': i,  'accessory_type': icon })
      sel = dialogs.list_dialog("Known levels\t\t\t\t\t\t\t\tCompleted", level_list)    
      responder.superview.close()  
      try:
        if sel:
          # self.saved_state = None
          self.app.goto(sel['title'])
      except (Exception) as e:
        print(e, sel)           

    def settilesize(self, ts):
        """Set the tile size based on the selected menu item,
         and push that change to relevant GUI elements."""
        self.app._canvas.settilesize(ts)
        self.app._status.set_size_request(ts)
        # self.settings["Size"] = ts
        self.tilesize = ts
        self.app.restart()
        
    def savestate(self, responder):
      responder.superview.close()
      self.saved_state = deepcopy(self.app._KyeApp__game)
      print(self.saved_state)
      with open('saved_state.pkl', 'wb') as f:
          pickle.dump(self.saved_state, f)
      
      
    def restorestate(self, responder):      
      responder.superview.close()
      print('restored', self.saved_state)
      try:
          with open('saved_state.pkl', 'rb') as f:
              saved_state = pickle.load(f)
          if saved_state:
             self.app._KyeApp__game = deepcopy(saved_state)
             self.app.do_tick()
      except:
        print('No saved state')
        
    @ui.in_background   
    def endleveldialog(self, nextlevel, endmsg):
        """Call when the level ends, to give the between-level messages."""
        if nextlevel != "":
            end_title = f"Level completed.  {endmsg[0]}secs\n\n {endmsg[1]}\n\n Entering level {nextlevel}"
        else:
            end_title = f"All levels completed.\n\n Returning to first level"
            
        dialogs.alert(end_title,button1="OK", hide_cancel_button=True)
        # And start the new level.
        self.app.goto(nextlevel)

    def helpdialog(self, responder):
        """Show the help dialog box."""
        KyeHelpDialog().show_menu()

    def error_message(self, message):
        """Show an error message in a dialog box."""
        print('error message', message)
        # console.alert(message)



