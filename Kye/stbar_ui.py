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

"""Classes for the status bar for the Kye game GUI."""

from scene import *
from canvas_scene import Tile
from common_cmt import image_dict, device_size
        
class StatusBar(Scene):
    """Kye status bar."""
    string_map = {
        "diamonds"  :   "Diamonds left", 
        "levelnum"  :   "Level",
        "hint"      :   "Hint"
    }

    def __init__(self):
        Scene.__init__(self)
        self.hint = None
        self.levelnum = None
        self.diamonds = None
        self.no_kyes = 3
        self.grid = Node(parent=self)
        self.background_color='white'
        device = device_size()
        if device== 'iphone_landscape':
          self.position = (100,100)
        else:
          self.position = (0,0)
        self.image_dict = image_dict #load_images()
        self.kye_icon = image_dict['kye']
        self.blank = image_dict['blank']
        xpos = 15
        ypos = 15
        for i in range(3):
          x= Tile(self.kye_icon,0,i, ts=16)
          x.position =(xpos + i*22,ypos+5)
       	  self.grid.add_child(x)
        xpos += 100
        self.st_dict = {'diamonds': LabelNode("",color='black',anchor_point=(0,0),position=(xpos,ypos)), 
                        'levelnum': LabelNode("",color='black',anchor_point=(0,0),position=(xpos + 170, ypos)), 
                        'hint': LabelNode("", color='black',anchor_point=(0,0),position=(xpos + 300, ypos))}
        for i in self.st_dict.values():
        	self.grid.add_child(i)
           
      
    def update_bar(self, **keywords):
        """Update data displayed in the status bar."""
        for k, value in keywords.items():
            # The string labels we update; the kye count, we pass to the special kyes widget.
            if k in self.st_dict:
                self.st_dict[k].text = f"{StatusBar.string_map[k]}:{str(value)}"
                
            elif k == "kyes":
              if value != self.no_kyes:
                self.no_kyes = value  
                for i in range(3):
                	self.grid.children[i].texture = self.blank  
                for i in range(value):
                  self.grid.children[i].texture = self.kye_icon
                  self.grid.children[i].size=(16,16)
                
                
    def set_size_request(self, ts):
     	pass
              
