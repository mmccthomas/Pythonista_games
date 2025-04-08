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

"""kye.dialogs - classes for dialog boxes used by the interface."""

from os.path import exists
from common_cmt import kyepaths, version
import ui
import dialogs


def getimage(image_name):
	return ui.Image.named('images/' + image_name + '.png')

		
class GotoDialog():
    """A dialog box for the player to select or type a level name to go to."""
    def __init__(self, parent=None, knownlevs=()):
      sel = dialogs.list_dialog("Known levels.", knownlevs)

    def get_level(self):
        """Returns the selected level name."""
        return self.cb.child.get_text()


class KyeHelpDialog(ui.View):
    """Help dialog box."""
    def __init__(self):

      self.itemlist=[{'image': getimage("kye"), 'title': "You are Kye. Move by point-and-click with the mouse, or the arrow keys or numeric keypad on the keyboard (note that you can move diagonally, even using the keyboard)"},
        {'image': getimage("diamond_1"), 'title': "The object of the game is to collect all the diamonds." },
        {'image': getimage("wall5"), 'title':  "These are solid walls."},
        {'image': getimage("block"), 'title': "These are blocks, which you can push."},
        {'image': getimage("slider_right"), 'title': "Sliders move in the direction of the arrow until they hit"},
        {'title': "		 an obstacle."},
        {'image': getimage("rocky_right"), 'title': "Rockies move like sliders, but they roll around round"},
        {'title': "   		 objects, like rounded walls and other rockies."},
        {'image': getimage("blocke"), 'title': "Soft blocks you can destroy by moving into them."},
        {'image': getimage("blob_1"), 'title': "Monsters kill you if they touch you."},
        {'title': "				 You do have 3 lives, though."},
        {'image': getimage("gnasher_1"), 'title': ".     Gnasher"},
        {'image': getimage("spike_1"),   'title': ".     Spike"},
        {'image': getimage("twister_1"), 'title': ".     Twister"},
        {'image': getimage("snake_1"),   'title': ".     Snake"},
        {'image': getimage("sentry_right"), 'title': "Sentries pace back and forward, and push other objects."},
        {'image': getimage("black_hole_1"), 'title': "Objects entering a black hole are destroyed." },
        {'image': getimage("slider_shooter_right"), 'title': "Shooters create new sliders or rockies."},
        {'image': getimage("block_timer_5"), 'title': "Timer blocks disappear when their time runs out." },
        {'image': getimage("turner_clockwise"), 'title': "Turning blocks change the direction of sliders and rockies."},
        {'image': getimage("sticky_horizontal"), 'title': "Magnets (also called sticky blocks) allow you to pull objects."},
        {'image': getimage("oneway_right_1"), 'title': "One-way doors only allow Kye though, and only in one direction."},
        {'image': getimage("kye"), 'title': "If you make a mistake, or get stuck in a level,"},
        {'title': "go to the Level menu and select Restart Level."},
        {'title': "To skip to a particular level select from Level menu and select Goto Level."},
        {'title': "You can load a new set of levels by opening it via the File menu."},
        {'title': "Credit"},
        {'title': "http://games.moria.org.uk/kye/pygtk"},
        {'title': "Chris Thomas <mmccthomas@gmail.com> for the ios frontend"},
        {'title': "Colin Phipps <cph@moria.org.uk>"},
        {'title': "Copyright (C) 2004-2007, 2010 Colin Phipps <cph@moria.org.uk>"},
        {'title': "Based on the original Kye for Windows, by Colin Garbutt"},
        {'title': "Distributed under the GNU General Public License"},
        {'image': getimage("kye")}

        ]

      self.list = ui.ListDataSource(items=self.itemlist)
      
    def show_menu(self):
      dialogs.list_dialog('Help', self.list.items)


class ViewMenu(ui.View):
  def __init__(self):
    try:
        sel = dialogs.alert('Level', button1='Restart', button2='Goto Level')
        if sel == 1:
          self.restart()
        elif sel == 2:
          self.startgoto()
    except (KeyboardInterrupt):
        pass


def kyeffilter():
  pass
  """Constructs a gtk.FileFilter for .kye files
    kfilter = gtk.FileFilter()
    kfilter.set_name("Kye Levels")
    kfilter.add_pattern("*.kye")
    return kfilter"""


def kyerfilter():
    pass
    """Constructs a gtk.FileFilter for .kyr files
    kfilter = gtk.FileFilter()
    kfilter.set_name("Kye Recordings")
    kfilter.add_pattern("*.kyr")
    return kfilter"""


def getopendialog():
    pass


def KyeAboutDialog():
    pass
