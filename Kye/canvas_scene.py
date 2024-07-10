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

"""kye.canvas - module containing the KCanvas class,
which implements the display of the game itself."""

from common import xsize, ysize, tsize, findfile, KyeImageDir, image_dict, device_size
import ui
import os
from PIL import Image
from scene import *
from random import randint, choice


class Tile(SpriteNode):
	"""
	A single tile on the grid.
	"""
	def __init__(self, tile, row=0, col=0, ts=tsize):
		# put these at front with z_position
		SpriteNode.__init__(self, tile, z_position=10)
		self.size = (ts, ts)
		self.anchor_point = 0, 0
		self.number = 1
		self.name = ''
		self.set_pos(row, col)
		
	def set_pos(self, row, col=0, animation=True):
		"""
		Sets the position of the tile in the grid.
		"""
		if isinstance(row, tuple):
			row, col = row
		if col < 0 or col >= xsize:
			return
		if row < 0 or row >= ysize:
			return
		self.col = int(col)
		self.row = int(row)
		
		pos = Vector2()
		pos.x = col * self.size[0] + 10
		pos.y = (ysize - 1 - row) * self.size[1] + 10
		self.position = pos

				
class KCanvas(Scene):
    """A Scene object which draws the game."""

    def __init__(self, responder, tilesize, app):
        Scene.__init__(self)
        # Set up mouse event handling.
        self.responder = responder
        self.mouseto = responder.touch_motion_event
        self.bpress = responder.touch_press_event
        self.brelease = responder.touch_release_event
        self.tilesize = tilesize
        # Remember the tilesize, and set the canvas size appropriately
        self.size = (self.tilesize * xsize, self.tilesize * ysize)
        device = device_size()
        if device == 'ipad_landscape':
          self.position = (0, 0)
        elif device == 'ipad13_landscape':
          self.position = (0, 0)  
        elif device == 'ipad_portrait':
          self.position = (0, 0)
        elif device == 'iphone_landscape':
          self.position = (150, 320)

        self.game = app._KyeApp__game
        self.all_changed = [1] * (xsize * ysize)
        
        self.background_color = 'lightgrey'
        
        self.grid = Node(parent=self)
        
        self.images = {}
        # Get the image directory and create the rendered image cache.
        imgdirname = findfile("images")
        if imgdirname is None:
          console.hud_alert("Could not find tileset")
          # raise Exception( "aborting, no tileset")
        self.imgdir = 'images'
        
        # Set up array holding the on-screen state.
        self.showboard = ['blank'] * (xsize*ysize)
        
        self.image_dict = image_dict  # from common
        self.initialise_board()
        # self.test_icons()
        self.game_redraw(self.game, self.all_changed)
        
    def change_size(self):
        pass
    
    def did_change_size(self):
      print('changed size')
    
    def test_icons(self):
      for i, item in enumerate(self.image_dict.values()):
        x = (i % 10)
        y = int(i / 10)
        t = self.tile_at(y, x)
        if t:
          t.texture = item
          t.size = (self.tilesize, self.tilesize)
	
    def get_tiles(self, exclude=None):
      """ Returns an iterator over all tile objects"""
      if exclude is None:
        exclude = []
      for o in self.grid.children:
        if isinstance(o, Tile) and o not in exclude:
          yield o

    def tile_at(self, row, col):
      """ return tile at location, else None """
      for t in self.get_tiles():
        if t.row == row and t.col == col:
          return t
      return None

    def game_redraw(self, game, changed_squares):
        """Update the displayed game from the game in memory
          (e.g. after a game tick has run).

        game  -- the game object (we call get_tile on this to get the new state.
        changed_squares -- array containing true/false values to indicate which
        squares (may) have changed since the last rendering.
        Note that this is flattened, so it contains values
        for (0,0), (1,0), ..., (30,0), (0, 1), ... etc.
        """
        i = -1
        for y in range(ysize):
          for x in range(xsize):
            i = i + 1
            if changed_squares[i] == 1:
              try:
                piece = game.get_tile(x, y)
                self.showboard[xsize*y+x] = piece
                self.drawcell(x, y, piece)
              except (AttributeError, IndexError) as e:
                pass
         
    def get_image(self, tilename):
      return self.image_dict[tilename]

    def settilesize(self, tsize):
        """Sets the size for tiles; causes the canvas to resize and be redrawn."""
        self.tilesize = tsize
        self.size = (self.tilesize * xsize, self.tilesize * ysize)
        self.initialise_board()
        self.game_redraw(self.game, self.all_changed)
     
    def clear_board(self):
      '''change to blank tile'''
      for i in range(xsize):
        for j in range(ysize):
          t = self.tile_at(j, i)
          t.texture = self.image_dict['blank']
          t.size = (self.tilesize, self.tilesize)
    
    def initialise_board(self):
      '''add blank tile to every location, redraws will just change texture'''
      for i in self.grid.children:
        i.remove_from_parent()
      for i in range(xsize):
        for j in range(ysize):
          self.grid.add_child(
            Tile(self.image_dict['blank'], j, i, ts=self.tilesize))

    def drawcell(self, i, j, tile=None):
        """Draw the cell at i, j, using the supplied graphics context."""
        piece = self.showboard[i + j * xsize]
        t = self.tile_at(j, i)
        t.texture = self.image_dict[piece]
        t.size = (self.tilesize, self.tilesize)
          
    def touch_convert(self, touch):
      x = int(touch.location.x / self.tilesize)
      y = ysize - 1 - int(touch.location.y / self.tilesize)
      return x, y
      
    def touch_began(self, touch):
      x, y = self.touch_convert(touch)
      self.bpress(self.responder, x, y)
      
    def touch_moved(self, touch):
      x, y = self.touch_convert(touch)
      self.mouseto(self.responder, x, y)
      
    def touch_ended(self, touch):
      x, y = self.touch_convert(touch)
      self.brelease(self.responder, x, y)
