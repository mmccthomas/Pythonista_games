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
#
# modified to allow remote call from editor
# If in remote mode, game should not allow selection of file or level
# and level should restart when finished
# August 2025 CMT

import ui
from scene import *
import dialogs
import sys
import os
import inspect
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


def find_file(image_filename):
    """
    Finds a file in the same directory as the calling module.

    Args:
        image_filename (str): The name of the file to find.

    Returns:
        str or None: The full path to the image file, or None if not found.
    """
    # Get the file path of the calling module
    calling_frame = inspect.currentframe().f_back
    calling_module_path = inspect.getfile(calling_frame)

    # Get the directory of the calling module
    module_directory = os.path.dirname(os.path.abspath(calling_module_path))

    # Construct the full path to the image file
    image_path = os.path.join(module_directory, image_filename)

    # Check if the file exists before returning the path
    if os.path.exists(image_path):
        return image_path
    else:
        return None
            
def main(**kwargs):

  global v, defaults
  # Load settings file.
  defaults = KyeDefaults()
  
  try:
      defaults.set_current(file=kwargs['file'], level_name=kwargs['level_name'])
  except (KeyError, AttributeError):
      pass
  
  kyeapp = KyeApp(defaults=defaults, playfile="intro.kye")
  
  # Create GUI and run the app. This doesn't return until the user exits.
  device = device_size()
  if device == 'ipad_landscape':    
    tilesize = 32
    ui_file = 'kye_ui.pyui'
    frame = (0, 0, 1113, 834)
  elif device == 'ipad_portrait':
    tilesize = 27
    ui_file = 'kye_ui_portrait.pyui'
  elif device == 'ipad13_landscape':
    tilesize = 43
    ui_file = 'kye13_ui.pyui'
    frame = (0, 0, 1300, 1000)
  elif device == 'iphone_landscape':
    tilesize = 16
    ui_file = 'kye_ui.pyui'
    frame = (0, 0, 850, 352)
  elif device == 'ipad_mini_landscape':
    tilesize = 32
    ui_file = 'kye_ui.pyui'
    frame = (0, 0, 1133, 744)
  else:
    dialogs.hud_alert('Iphone portrait not supported')
    sys.exit()
    
  try:
     v = ui.load_view(find_file(ui_file))
     if frame:
        v.frame = frame
  except FileNotFoundError:
     dialogs.hud_alert(f'{ui_file} not found')
     sys.exit()
   
  v['status'].scene = StatusBar()
  v['canvas'].scene = KCanvas(KMoveInput, tilesize, kyeapp)
  v['sceneview'].scene = KFrame(kyeapp, recentlevels=defaults.get_recent(),
                                settings=defaults.settings, tilesize=tilesize)
  
  if device == 'iphone_landscape':
    v['status'].position = (0, 0)
  elif device == 'ipad_landscape':
    v['status'].position = (0, 0)
  else:
     v['status'].position = (0, 0) 
  
  build_menu(v)
  if kwargs:
     # if calling remotely dont allow switch away     
     v['file_button'].enabled = False
     v['level_button'].enabled = False       
     kyeapp.remote = True            
  kyeapp.run(v)
  
  v.present('fullscreen', hide_title_bar=True)
  # Save settings before exit
  defaults.save()
  return v


if __name__ == "__main__":
  # call for remote operation
  # disables file and level
  #main(file='intro.kye', level_name='ROCKIES')
  main()

