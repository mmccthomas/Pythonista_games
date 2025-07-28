import importlib
import re
import inspect
from pathlib import Path
import console
import dialogs
import editor
import glob
import traceback
import base_path

""" Utility to present module as a tree, parsing the
code of each function to extract class function calls
intended to be installed as editor action
"""
# find items self.abcd(
pattern = re.compile('self.[a-z_A-Z]+\(')

      
def create_tree(top_class):
   global top_class_functions, file_
   space = '    '
   branch = '│   '
   tee = '├── '
   last = '└── '
   
   def get_fn(text):
       global top_class_functions
       for (txt, fn_) in top_class_functions:
           if text == txt:
               return fn_
                             
   def get_child(function, depth):
       global file_
       if depth == -1 or depth > 3:
           return
       if not function:
           return
     
       fn_source = inspect.getsource(function)
       matches = set(pattern.findall(fn_source))
       if not matches:
          return False
       for i, match in enumerate(matches):
           text = match[5:-1]
           b = last if i == len(matches)-1 else tee
           fn_ = get_fn(text)
           try:
               parent = fn_.__module__
               show_parent = f'({parent})' if file_.stem not in parent else ''
               print(f'{(branch + space)*(depth)}{b}{text}{show_parent}')
               if fn_ != function:
                   get_child(fn_, depth+1)
           except AttributeError:
               pass
                    
   top_class_functions = inspect.getmembers(top_class, inspect.isfunction)
   print(f'{top_class.__name__}(class)')
   depth = 0
   for i, (name, fn) in enumerate(top_class_functions):
     parent = fn.__module__
     if file_.stem not in parent and depth == 0:
         continue     
     # print(f'{last}{name}')         
     print(f'{tee}{name}')
     get_child(fn, depth+1)


def get_module(filename):
    """ If call_tree is called directly , select the python file
    from a dialog selection
    else try to import from editor action
    """
    global file_
    p = glob.iglob('../**/*.py', root_dir='.', recursive=True)
    if filename.stem == Path(__file__).stem:
      select = dialogs.pick_document(types=['public.python-script'])
      filename = Path(select)
      for item in p:
        if filename.stem in item:
          item = Path(item)
          filename = item
          base_path.add_paths(filename)
          break
    file_ = filename
    base_path.add_paths(file_)
    # print([p for p in sys.path if 'Pythonista_games' in p])
    try:
      # need a string of module import in search path
      print(f'Filename = {filename.parent.name}.{filename.stem}')
      module = importlib.import_module(f'{filename.parent.name}.{filename.stem}')
    except ImportError as e:
      raise ImportError(e, filename)
    return module

            
def main(filename):
  global file_
  console.clear()
  module_ = get_module(filename)
  class_members = inspect.getmembers(module_, inspect.isclass)
  classes = [c[1] for c in class_members if file_.stem in c[1].__module__]  
  for c in classes:
      create_tree(c)


if __name__ == '__main__':
    try:
      filename = Path(editor.get_path())
      main(filename)
    except Exception:
      print(traceback.format_exc())
    # sys.path.append(os.path.expanduser('~/Documents/Pythonista_games/Word_Games'))
  
