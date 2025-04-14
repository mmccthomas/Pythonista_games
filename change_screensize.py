# coding: utf-8

# @omz

# https://forum.omz-software.com/topic/2167/iphone-screen-size-on-an-ipad/2

from objc_util import *
from scene import Size
# NOTES: width/height values refer to portrait orientation -- they're automatically
# swapped if the app is in landscape mode. When this is run with the same values
# again, the default window size (full-screen) is restored.

# Some things don't work correctly with a non-default window size, e.g. the copy/paste
# menu is positioned incorrectly.
sizes ={'iphone': (393, 852), 'ipad': (834, 1112),
        'ipad13': (1024, 1366), 'ipad_mini': (744, 1133)}

UIWindow = ObjCClass('UIWindow')
UIApplication = ObjCClass('UIApplication')
UIScreen = ObjCClass('UIScreen')

def get_screen_size():              
        app = UIApplication.sharedApplication().keyWindow() 
        for window in UIApplication.sharedApplication().windows():
            ws = window.bounds().size.width
            hs = window.bounds().size.height
            break
        return Size(ws,hs)
        
@on_main_thread
def resize_main_window(w, h):
  app = UIApplication.sharedApplication()
  win = app.keyWindow()
  wb = win.bounds()
  sb = UIScreen.mainScreen().bounds()
  if sb.size.width > sb.size.height:
    w, h = h, w
  if w == wb.size.width and h == wb.size.height:
    w, h = sb.size.width, sb.size.height
    
  win.setBounds_(((0, 0), (w, h)))
  win.setClipsToBounds_(True)
  
  print(get_screen_size())
  
if __name__ == '__main__':
    if len(sys.argv) > 1:
        selection = sys.argv[1]
    else:
        selection = 'ipad'
    resize_main_window(*sizes[selection])
  

