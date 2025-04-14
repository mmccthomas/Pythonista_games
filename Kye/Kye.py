#!/usr/bin/env puzzle game ''

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
#    GNU General Public License for more details. '
#
#    You should have received a copy of the GNU General Public License 
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# completely modified bu Chris Thomas for ipad using Pythonista
# Drawing surfaces are using scene module
# Menu uses ui module buttons
import ui
from scene import *
import dialogs
import sys
from frame_scene import KFrame
from canvas_scene import KCanvas
from stbar_ui import StatusBar
from input_ui import KMoveInput
from defaults_cmt import KyeDefaults
from app import KyeApp

from common_cmt import tsize, device_size


def build_menu(view):
  """Build the menubar  menus"""
  frame = view['sceneview'].scene
   
  _dict = {'close_button': quit,
           'file_button': frame.open_file_menu,
           'level_button': frame.open_level_menu,
           'view_button': frame.open_view_menu,
           'help_button': frame.helpdialog}
  for item in view.subviews:
    try:
      item.action = _dict[item.name]
    except (Exception) as e:
      continue


def quit(responder):
  global v, defaults
  v.close()
  defaults.save()

            
def main(**argv):

  global v, defaults
  # Load settings file.
  defaults = KyeDefaults()
  kyeapp = KyeApp(defaults=defaults, playfile="intro.kye")
  # Create GUI and run the app. This doesn't return until the user exits.
  device = device_size()
  if device == 'ipad_landscape':    
    tilesize = 32
    v = ui.load_view('kye_ui.pyui')
    v.frame = (0, 0, 1113, 834)
  elif device == 'ipad_portrait':
    tilesize = 27
    v = ui.load_view('kye_ui_portrait.pyui')
  elif device == 'ipad13_landscape':
    tilesize = 43
    v = ui.load_view('kye13_ui.pyui')
    v.frame = (0, 0, 1300, 1000)
  elif device == 'iphone_landscape':
    tilesize = 16
    v = ui.load_view('kye_ui.pyui')
    v.frame = (0, 0, 850, 352)
  elif device == 'ipad_mini_landscape':
    tilesize = 32
    v = ui.load_view('kye_ui.pyui')
    v.frame = (0, 0, 1133, 744)
  else:
    dialogs.hud_alert('Iphone portrait not supported')
    sys.exit()
  
  v['status'].scene = StatusBar()
  v['canvas'].scene = KCanvas(KMoveInput, tilesize, kyeapp)
  v['sceneview'].scene = KFrame(kyeapp, recentlevels=defaults.get_recent(),
                                settings=defaults.settings, tilesize=tilesize)
  if device == 'iphone_landscape':
    v['status'].position = (0, 150)
  elif device == 'ipad':
    v['status'].position = (0, 50)

  build_menu(v)
  kyeapp.run(v)
  v.present('fullscreen', hide_title_bar=True)
  # Save settings before exit
  defaults.save()


if __name__ == "__main__":
  main()

