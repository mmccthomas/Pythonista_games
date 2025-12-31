# compare files in local Pythonista files and cloud/Pythonista/Pythonista_games
# create a list of Paths for each folder
# using Paths means that position of item does not need to be same in each
# Only  compare file contents rather than datetime
# if file does not match, show differences
#
# open dialog to allow difference inspection and choice of which to keep
# Included new files created since last modified date in cloud
# 
# must get path or depth, not just name, else matches to other named files
# find text above to get parent?

import filecmp
import os
from itertools import islice
from pathlib import Path
import difflib
import shutil
from itertools import zip_longest
import ui
try:
    from change_screensize import get_screen_size
except ImportError:
    from scene import get_screen_size
import console
from objc_util import NSRange, on_main_thread, ObjCClass, ObjCInstance, c_void_p, c
from datetime import datetime
import base_path
base_path.add_paths(__file__)
from setup_logging import logger, is_debug_level


class CompareCloud():

    def __init__(self, source):
        self.cloud_base= '/private/var/mobile/Containers/Data/Application/24BEC035-C28E-496A-A41A-CEC669E05513/Documents/'
        #self.cloud_base = '/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/'
        self.source = source
        self.dest = self.cloud_base + self.source
        self.index = 0
        self.spacing = 50
        self.use_colour = True
        
    def latest_modified(self, which=None):
        # get latest modified file and datetime in either cloud or local
        if which is None:
            which = self.dest
        dir_which = Path(which).glob('**/*')
        filetimes = {path: datetime.fromtimestamp(os.stat(path).st_mtime)
                     for path in dir_which}
        latest = max(filetimes, key=filetimes.get)
        latest_time = filetimes[latest]
        return latest, latest_time
        
    def get_deleted_files(self):
        # return the path of any files deleted from source
        dir_src = list(Path(self.source).glob('**/*'))
        dir_dest = Path(self.dest).glob('**/*')
        dir_dest_rel = [p.relative_to(self.cloud_base) for p in dir_dest]
        return [d for d in dir_dest_rel if not d in dir_src]

        
    def get_new_files(self):
        # return the path and datetime of any files created
        # after latest cloud file
        dir_src = Path(self.source).glob('**/*')
        latest_file, latest_dest_time = self.latest_modified(self.dest)
        new_files = {p: datetime.fromtimestamp(os.stat(p).st_birthtime)
                     for p in dir_src
                     if datetime.fromtimestamp(os.stat(p).st_birthtime) > latest_dest_time}
        return new_files
        
    def show_diffs(self, file1, file2):
        """get differences between 2 files """

        def file_mtime(path):
            # file modified time
            t = datetime.fromtimestamp(os.stat(path).st_mtime)
            return t.strftime('%a %d %b %Y, %I:%M%p')

        try:
            with open(file1, 'r', encoding='utf-8') as hosts0:
                with open(file2, 'r', encoding='utf-8') as hosts1:

                    diff = difflib.context_diff(hosts0.readlines(),
                                                hosts1.readlines(),
                                                fromfile='local',
                                                tofile='cloud',
                                                fromfiledate=file_mtime(file1),
                                                tofiledate=file_mtime(file2))
                    """
                    diff = difflib.HtmlDiff().make_table(
                        hosts0.readlines(),
                        hosts1.readlines(),
                        fromdesc='local',
                        todesc='cloud',
                        context=True, numlines=5)
                    """
        except UnicodeDecodeError:
            diff = ['unicode error in file']
        return diff

    def tree(self,
             dir_path: Path,
             level: int = -1,
             limit_to_directories: bool = False,
             length_limit: int = 1000,
             no_print=False,
             exclude=[]):
        """Given a directory Path object print a visual tree structure
           from stackoverflow"""
        space = '    '
        branch = '│   '
        tee = '├── '
        last = '└── '
        dir_path = Path(dir_path)  # accept string coerceable to Path
        self.files = 0
        self.directories = 0

        def inner(dir_path: Path, prefix: str = '', level=-1):
            if not level:
                return  # 0, stop iterating
            if limit_to_directories:
                contents = sorted([d for d in dir_path.iterdir() if d.is_dir()])
            else:
                contents = sorted(list(dir_path.iterdir()))
            pointers = [tee] * (len(contents) - 1) + [last]
            for pointer, path in zip(pointers, contents):
                if path.is_dir() and path.name in exclude:
                    continue
                if path.is_dir():
                    yield prefix + pointer + path.name
                    self.directories += 1
                    extension = branch if pointer == tee else space
                    yield from inner(path,
                                     prefix=prefix + extension,
                                     level=level - 1)
                elif not limit_to_directories:
                    yield prefix + pointer + path.name
                    self.files += 1

        iterator = inner(dir_path, level=level)
        if no_print:
            return iterator
        else:
            print(dir_path.name)
            for line in islice(iterator, length_limit):
                print(line)
            if next(iterator, None):
                print(f'... length_limit, {length_limit}, reached, counted:')
            print(f'\n{self.directories} directories' +
                  (f', {self.files} files' if self.files else ''))

    def not_excluded(self, f):
        # decide if file should be included in comparison
        if f.name.split('.')[-1] in [
                'npy', 'npz', 'pkl', 'json', 'gitignore', 'git'
        ]:
            return False
        if '.git' in f.parts:
            return False
        return True

    def compare(self):
        """compare two directory trees
        use Path objects to allow matching
        """
        dir_src = Path(self.source).glob('**/*')
        dir_dest = list(Path(self.dest).glob('**/*'))
        # make cloud version have same path
        dir_dest_rel = [p.relative_to(self.cloud_base) for p in dir_dest]
        self.new_files = self.get_new_files()
        self.deleted_files = self.get_deleted_files()
        
        # iterate paths
        result_dict = {}
        for src in dir_src:
            if src.is_file() and self.not_excluded(src):
                if src in self.new_files:
                    try:
                        with open(src, 'r', encoding='utf-8') as f:
                            content = f.read()
                        result_dict[src] = content
                    except UnicodeDecodeError:
                        result_dict[dest] = 'Binary File'
                elif src in dir_dest_rel:
                    dest = dir_dest[dir_dest_rel.index(src)]

                    if filecmp.cmp(src, dest, shallow=False):
                        pass
                        # print('match')
                    else:
                        self.diffs = self.show_diffs(src, dest)
                        result_dict[src] = [list(self.diffs)]
                        CR = '\n'
                        logger.debug('#' * 78)
                        logger.debug(f'found {src}')
                        logger.debug('no match')
                        logger.debug(f'{CR.join([line for line in self.diffs])}')
        # now deal with deleted files
        for dest in self.deleted_files:
            fullpath = Path.joinpath(Path(self.cloud_base), dest)
            if fullpath.is_file() and self.not_excluded(fullpath):
                try:         
                    with open(fullpath, 'r', encoding='utf-8') as f:
                            content = f.read()
                    result_dict[dest] = content
                except UnicodeDecodeError:
                    result_dict[dest] = 'Binary File'
        return result_dict
        
    @on_main_thread
    def init_colours(self):
        UIColor = ObjCClass('UIColor')
        self.UIfont = ObjCClass('UIFont').fontWithName_size_(*self.t.font)
        self.tvo = ObjCInstance(self.t)
        self.tvo.setAllowsEditingTextAttributes_(True)
        self.stro = ObjCClass(
            'NSMutableAttributedString').alloc().initWithString_(self.t.text)
        self.stro.addAttribute_value_range_(
            ObjCInstance(c_void_p.in_dll(c, 'NSFontAttributeName')),
            self.UIfont, NSRange(0, len(self.t.text)))
        
        self.colors = {
            'red': UIColor.redColor(),
            'green': UIColor.greenColor(),
            'blue': UIColor.blueColor(),
            'cyan': UIColor.cyanColor(),
            'magenta': UIColor.magentaColor(),
            'black': UIColor.blackColor(),
            'yellow': UIColor.yellowColor()
        }
        
    def setup_views(self):
        """ Create GUI """
        def image_scale(name, wi=100, string=''):
            # bigger buttons
            img = ui.Image.named(name)
            w,h = img.size
            hi = wi*h/w
            with ui.ImageContext(wi,hi) as ctx:
                img.draw(0,0,wi,hi)
                ui.draw_string(string, rect=(0,4*hi/5,wi, hi), color='black', font=('Menlo',12))
                ui_resize = ctx.get_image()
            
            return ui_resize

        rb = ui.ButtonItem(# title='Local->Cloud',
                           image=image_scale('iob:ios7_cloud_upload_32', 72),
                           enabled=True,
                           tint_color='darkred',
                           action=self.to_cloud)
        rb1 = ui.ButtonItem(# title='Cloud->Local',
                            image=image_scale('iob:ios7_cloud_download_32', 72),
                            enabled=True,
                            tint_color='darkred',
                            action=self.to_local)
        rb2 = ui.ButtonItem(image=image_scale('iob:ios7_arrow_forward_32', 64), enabled=True, action=self.skip)
        rb3 = ui.ButtonItem(image=image_scale('iob:ios7_arrow_back_32', 64), enabled=True, action=self.back)

        lb4 = ui.ButtonItem(image=ui.Image.named('iob:refresh_32'), enabled=True, action=self.refresh, tint_color='black')
        lb5 = ui.ButtonItem(image=ui.Image.named('emj:Palm_Tree'), enabled=True, action=self.trees, tint_color='black')

        self.w, self.h = get_screen_size()
        self.main = ui.View(frame=(0, 0, self.w, self.h))
        self.main.left_button_items = [lb4, lb5]
        self.main.right_button_items = [rb2, rb3, rb, rb1]
        self.main.content_size = (self.w, self.h)

        # List to select post
        self.t = ui.TextView(frame=(0, 0, *self.main.content_size),
                             text_color='black',
                             bordered=True,
                             border_width=2,
                             font=('Menlo', 20))
        # self.wv = ui.WebView(frame=(0, 0, *self.main.content_size),
        #                     bordered=True,
        #                     border_width=2)
        # self.wv.load_html(self.diffs)
        # set up objc instance

        self.t.delegate = self
        self.main.add_subview(self.t)
        # self.main.add_subview(self.wv)
        # self.wv.bring_to_front()
        # calculate number of characters across textview
        # only true for monospaced fonts
        w, h = ui.measure_string('#####', font=self.t.font)
        self.chars = int(5 * self.w / w)
        self.spacing = self.chars // 2
        
        self.main.present('sheet')
        
    @ui.in_background
    def to_local(self, sender):
        # overwrite local file with cloud
        if self.items:
            local = self.items[self.index]
            cloud = Path(self.cloud_base + str(local))
            # for deleted file allow reconsideration
            if local in self.deleted_files:
               try:
                   console.alert(f'Recover File {local}?', button1='OK')                   
               except KeyboardInterrupt:
                   return 
            shutil.copyfile(cloud, local)
            self.refresh(None)

    def to_cloud(self, sender):
        # overwrite cloud file with local
        if self.items:
            local = self.items[self.index]
            cloud = Path(self.cloud_base + str(local))
            if local in self.deleted_files:
                os.remove(cloud)               
            else:
                shutil.copyfile(local, cloud)
            self.refresh(None)

    def skip(self, sender):
        if self.index < len(self.items) - 1:
            self.index += 1
            self.display()

    def back(self, sender):
        if self.index > 0:
            self.index -= 1
            self.display()

    def refresh(self, sender):
        self.t.text = ''
        self.result_dict = self.compare()
        self.items = list(self.result_dict.keys())
        self.index = 0
        self.display()

    def trees(self, sender):
        # get trees for local folder and its corresponding cloud version
        length_limit = 10000
        s = self.spacing
        iterator_dest = self.tree(self.dest,
                                  length_limit=length_limit,
                                  no_print=True,
                                  exclude=['.git'])
        iterator_src = self.tree(self.source,
                                 length_limit=length_limit,
                                 no_print=True,
                                 exclude=['.git'])

        lines_dest = [line for line in islice(iterator_dest, length_limit)]
        header_dest = f'{self.directories} directories' + (
            f', {self.files} files' if self.files else '')
        self.directories = self.files = 0
        lines_src = [line for line in islice(iterator_src, length_limit)]
        header_src = f'{self.directories} directories' + (
            f', {self.files} files' if self.files else '')
        tmod_d = 'Last mod: ' + self.latest_modified(self.dest)[1].strftime('%a %d %b %Y, %I:%M%p')
        tmod_s = 'Last mod: ' + self.latest_modified(self.source)[1].strftime('%a %d %b %Y, %I:%M%p')
        
        text = f'Local {self.source:<{s}} Repository\n'        
        text += f'{header_src:<{s}} {header_dest}\n'
        text += f'{tmod_s:<{s}} {tmod_d:>}\n'

        for line_src, line_dest in zip_longest(lines_src,
                                               lines_dest,
                                               fillvalue=''):
            # format the trees to fill the textview
            # make all lines spacing length
            line_src = f'{line_src[:s]:<{s}}'
            line_dest = f'{line_dest[:s]}'
            text += f'{line_src} {line_dest} \n'
        self.t.text = text
        if self.use_colour:
            self.colour_tree_items()
            
    def display(self):
        if self.items:
            text = self.result_dict[self.items[self.index]]
            if self.items[self.index] in self.new_files:
                self.t.text = text
                self.main.name = f'{self.index+1}/{len(self.items)}  {self.items[self.index]}  -- New File'
            elif self.items[self.index] in self.deleted_files:
                self.t.text = text
                self.main.name = f'{self.index+1}/{len(self.items)}  {self.items[self.index]}  -- Deleted File'
            else:
                self.t.text = ''.join(text[0])
                self.main.name = f'{self.index+1}/{len(self.items)}  {self.items[self.index]}  -- Existing File'
                if self.use_colour:
                    self.colour_display()
        else:
            self.main.name = 'No Differences'.upper()
            
    @on_main_thread
    def colour_tree_items(self):
        """
        This code is to add colour to modified files in tree
        New files are green, modified files are cyan
        """
        self.init_colours()
        colors = [self.colors['cyan'], self.colors['green']]
        lines = self.t.text.split('\n')

        for index, line in enumerate(lines):
            for item in self.result_dict:
                if item.name in line:
                    for column in range(2):  # allow for item.name on same line
                        try:
                            pos = line.index(item.name, column * self.spacing)
                            
                            if self.get_parent(lines, index, item, column):
                                start = pos + len('\n'.join(
                                    lines[:index]))  # length of all lines so far
                                end = start + len(item.name) + 1                                
                                color = colors[int(item in self.new_files)]
                                self.stro.addAttribute_value_range_(
                                    'NSBackgroundColor', color,
                                    NSRange(start, end - start))
                                self.tvo.setAttributedText_(self.stro)
                        except ValueError:
                            continue
            
    def get_parent(self, lines, index, item, column=0):
        """
        Check if item.name is under correct folder
        as filenames can be repeated, e.g. __init__.py
        lines is all lines in textview
        index is current line number containing item
        column (0/1) will search from start or mid line
        """
        pos = lines[index].index(item.name, column * self.spacing)
        depth = (pos % self.spacing) // 4
        parent_name = item.parts[-2]
        # search up to find parent
        i = index
        while i >= 0:
           # only search in column
           if pos >= self.spacing:
               line = lines[i][self.spacing:]
           else:
               line = lines[i][:self.spacing]
           # find position of first alphanumeric character
           pos_line = line.find(next(filter(str.isalpha, line)))
           if pos_line == -1:  # not found
               i -= 1
               continue
           parent_depth = (pos_line % self.spacing) // 4
           if parent_depth == depth - 1:  # corrent depth
               return parent_name == line[pos_line:].strip()
           i -= 1
        return False
                        
    @on_main_thread
    # apparently this must be called on main thread for textview
    def colour_display(self):
        """
        This code is to add colour to text differences
        find initial string then
        find start text
        then find all lines beginning  '!'
        sounds like a state machine to me!
        """
        self.init_colours()
        start_texts = ['*** ', '---']
        colors = [self.colors['cyan'], self.colors['green']]
        init_str = '*' * 15

        lines = self.t.text.split('\n')
        started = False
        found_start_text = False
        color = colors[0]

        for index, line in enumerate(lines):
            if line.startswith(init_str):
                started = True
            elif line.startswith('!'):
                if found_start_text:
                    start = len('\n'.join(
                        lines[:index]))  # length of all lines so far
                    end = start + len(lines[index]) + 1
                    self.stro.addAttribute_value_range_(
                        'NSBackgroundColor', color,
                        NSRange(start, end - start))
                    self.tvo.setAttributedText_(self.stro)
            elif line.startswith(start_texts[0]):
                if started:
                    found_start_text = True
                    color = colors[0]
            elif line.startswith(start_texts[1]):
                if started:
                    found_start_text = True
                    color = colors[1]

    def run(self):
        if is_debug_level():
            self.tree(self.source)
            self.get_new_files()
        self.result_dict = self.compare()
        self.setup_views()
        logger.debug(self.result_dict)
        self.items = list(self.result_dict.keys())
        self.display()


if __name__ == '__main__':
    CompareCloud(source='Pythonista_games').run()
