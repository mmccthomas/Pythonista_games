#    Kye - classic puzzle game
#    Copyright (C) 2006, 2007, 2010 Colin Phipps <cph@moria.org.uk>
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
"""kye.defaults_cmt - contains the KyeDefaults class."""

from os import environ
from os.path import join
import json


class KyeDefaults:
    """Class for reading, querying and saving game preferences,
    including the list of recently-played files and known level names.
    Modified by CMT to use json format
    also stores current file, current level for that file, and known levels
    for file. defaults do not need to be portable."""
    
    def __init__(self):
        # Path to the config file.
        self.settings = None
        self.cf = join('.', "kye_config.json")
        self.content = {}
        # Initialise.
        self.init_content = {'current': {'filename': "intro.kye",
                                         'level_name': 'LOGO'},
                             'known_levels': {"intro.kye": ['LOGO']},
                             'completed_levels': {"intro.kye": ['LOGO']},
                             'recent_files': ["intro.kye"]}
        # Try reading the config file.
        try:
            with open(self.cf) as s:
              self.content = json.load(s)
        except (IOError) as e:
          print("failed to read config", e, 'using init')
          self.content = self.init_content
          self.save()

    def get_known_levels(self, path):
        """Get all known level names for the given filename."""
        known = self.content["known_levels"]  # a dictionary
        if path in known:
            return known[path]
        return []
        
    def get_completed_levels(self, path):
        """Get all completed level names for the given filename."""
        completed = self.content["completed_levels"]  # a dictionary
        if path in completed:
            return completed[path]
        return []
        
    def set_current(self, file, level_name):
      """ add item current
      {"current": {"filename": file, "level_name": level_name}}
      """
      self.content["current"] = {"filename": file, "level_name": level_name}
      self.add_recent(file)

    def get_current(self):
      try:
        return self.content['current']['filename'], self.content['current']['level_name']
      except (IndexError):
        return None, None

    def add_known(self, path, level_name):
        """For this kye file, we now know this level name."""
        known = self.content['known_levels'].setdefault(path, [level_name])
        if level_name not in known:
          known.append(level_name)
          self.content['known_levels'][path] = known
        self.set_current(path, level_name)
        
    def add_completed(self, path, level_name):
        """For this kye file, we have now completed this level name."""
        completed = self.content['completed_levels'].setdefault(path, [level_name])
        if level_name not in completed:
          completed.append(level_name)
          self.content['completed_levels'][path] = completed

    def add_recent(self, file):
      recents = self.content['recent_files']
      if file not in recents:
        recents.append(file)
        self.content['recent_files'] = recents

    def get_recent(self):
        """Returns paths to the five most recently loaded .kye files."""
        try:
          return self.content["recent_files"][-5:]
        except (IndexError):
          return None

    def save(self):
        """Try to save the configuration back to the config file."""
        try:
            with open(self.cf, "w") as s:
              json.dump(self.content, s)
        except (Exception) as e:
          print('save defaults', e)


if __name__ == '__main__':
  a = KyeDefaults()
  print('recent ', a.get_recent())
  print('current ', a.get_current())
  print('known_levels', a.get_known_levels('intro.kye'))

  a.add_known('intro.kye', 'ROCKIES')
  a.set_current('intro.kye', 'ROCKIES')

  print('current ', a.get_current())
  print('known_levels', a.get_known_levels('intro.kye'))

  a.add_known('DANISH1.KYE', 'LABORIOUS')
  print('current ', a.get_current())
  print('known_levels', a.get_known_levels('intro.kye'))
  a.add_known('DANISH1.KYE', 'TRICKER')
  a.save()

