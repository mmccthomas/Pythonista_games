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

"""Input handling code - touch input and recorded input."""

from os.path import basename

#from common import version
# these have been made global as they possibly
# run across threads
mousemoving = False
currentmouse = None


class KMoveInput:
    """Gets movement input, and converts it into game actions."""
    def __init__(self):
        self.clear()

    def clear(self):
        """Clears the current state of mouse buttons/keyboard keys held."""
        global mousemoving, currentmouse
        self.heldkeys = []
        self.keyqueue = []
        mousemoving = None
        currentmouse = None

    def touch_motion_event(self, x, y):
        """Update touch position after a touch move."""
        global mousemoving, currentmouse
        currentmouse = ("abs", x, y)
        mousemoving = True
        
    def touch_press_event(self, x, y):
      global mousemoving
      mousemoving = True
      
    def touch_release_event(self, x, y):
      global mousemoving
      mousemoving = False

    def _get_move(self):
        """Gets the move from the current keys/mouse state."""
        global mousemoving, currentmouse
        # Then, if the mouse is pressed, do it
        if mousemoving and currentmouse:
            return currentmouse
        # No action
        return None

    def get_move(self):
        """Gets the move from the current keys/mouse state"""
        m = self._get_move()        
        return m




