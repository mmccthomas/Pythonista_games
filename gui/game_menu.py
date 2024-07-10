# This module implements the menu that is used by all game examples. It doesn't do much by itself.

from scene import *
import ui
import sound
A = Action

class ButtonNode (SpriteNode):
	def __init__(self, title, *args, **kwargs):
		SpriteNode.__init__(self, 'pzl:Button1', *args, **kwargs)
		button_font = ('Avenir Next', 20)
		self.title_label = LabelNode(title, font=button_font, color='black', position=(0, 1), parent=self)
		self.title = title

class MenuScene (Scene):
	''' added possibility to control layout of buttons
	layout is in form [no in first line, no in second line, no in 3rd line etc]'''
	def __init__(self, title, subtitle, button_titles, layout=None):
		Scene.__init__(self)
		self.title = title
		self.subtitle = subtitle
		self.button_titles = button_titles
		self.layout=layout
	
	def process_layout(self, layout):
		y_indexes=[]
		idx = 0
		for i in layout:
			for j in range(i):
 				y_indexes.append(idx)
			idx +=1
		y_indexes = list(reversed(y_indexes))
		
		x_indexes = []
		for i in layout:
			x_indexes.extend(list(range(i)))
		x_indexes = list(reversed(x_indexes))
		
		x_widths = []
		for i in layout:
			x_widths.extend(list([i for _ in range(i)]))	
		x_widths = list(reversed(x_widths))
		
		return x_widths, x_indexes, y_indexes
		
	def setup(self):
		button_font = ('Avenir Next', 15)
		title_font = ('Avenir Next', 36)
		num_buttons = len(self.button_titles)
		if self.layout:
			layout = self.layout
		else:
			layout = [1 for i in range(num_buttons)]
			
		self.bg = SpriteNode(color='black', parent=self)
		if self.layout:
			bg_shape = ui.Path.rounded_rect(0, 0, 260, max(layout) * 64 + 140, 8)
		else:
			bg_shape = ui.Path.rounded_rect(0, 0, 260, num_buttons * 64 + 140, 8)
		bg_shape.line_width = 4
		shadow = ((0, 0, 0, 0.35), 0, 0, 20)
		self.menu_bg = ShapeNode(bg_shape, (1,1,1,0.9), '#15a4ff', shadow=shadow, parent=self)
		self.title_label = LabelNode(self.title, font=title_font, color='black', position=(0, self.menu_bg.size.h/2 - 40), parent=self.menu_bg)
		self.title_label.anchor_point = (0.5, 1)
		self.subtitle_label = LabelNode(self.subtitle, font=button_font, position=(0, self.menu_bg.size.h/2 - 100), color='black', parent=self.menu_bg)
		self.subtitle_label.anchor_point = (0.5, 1)
		
		self.buttons = []
		# updated to allow layout spec
		# create list of row indexes
		x_widths, x_indexes, y_indexes = self.process_layout(layout)
		
		for i, title in enumerate(reversed(self.button_titles)):
			btn = ButtonNode(title, parent=self.menu_bg)
			btn.size = (btn.size.w // x_widths[i], btn.size.h)
			btn.anchor_point =(0.5,0.5)
			x = x_indexes[i] * btn.size.w - (x_widths[i]-1) * btn.size.w / 2
			y = (max(y_indexes) - y_indexes[i]) * 64   - max(y_indexes) * btn.size.h + 50
			btn.position = x, y
	
			self.buttons.append(btn)
			
		self.did_change_size()
		self.menu_bg.scale = 0
		self.bg.alpha = 0
		self.bg.run_action(A.fade_to(0.4))
		self.menu_bg.run_action(A.scale_to(1, 0.3, TIMING_EASE_OUT_2))
		self.background_color = 'white'
		
	def did_change_size(self):
		self.bg.size = self.size + (2, 2)
		self.bg.position = self.size/2
		self.menu_bg.position = self.size/2
	
	def touch_began(self, touch):
		touch_loc = self.menu_bg.point_from_scene(touch.location)
		for btn in self.buttons:
			if touch_loc in btn.frame:
				sound.play_effect('8ve:8ve-tap-resonant')
				size = (btn.size.w, btn.size.h)
				btn.texture = Texture('pzl:Button2')
				btn.size = size
				
	def touch_ended(self, touch):
		
		touch_loc = self.menu_bg.point_from_scene(touch.location)
		
		for btn in self.buttons:
			if self.presenting_scene and touch_loc in btn.frame:
				new_title = self.presenting_scene.menu_button_selected(btn.title)
				if new_title:
					btn.title = new_title
					btn.title_label.text = new_title

if __name__ == '__main__':
	run(MenuScene('Title', 'Subtitle', ['Foo', 'Bar', 'Baz']))
