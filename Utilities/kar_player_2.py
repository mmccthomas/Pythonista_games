# karaoke player
# present a list to choose
# extract lyrics (if any) and put these into a dictionary,
# keyed with time in 1ms integer
# play midi file, and repeatedly get playing time to display appropriate
# lyrics
# display all lyrics at once, then background colour part of lyric
# in sync with time
# Display a piano keyboard and highlight keys in time with melody track
# requires installation of mido library
# Chris Thomas November 2025
# TODO start / stop doesnt work correctly
# should be able to stop , choose new file or track, and resume
# TODO some out of sync. eg allnightlong.kar

import sound
import zipfile
import ui
from scene import Color
import time
import dialogs
import os
import re
import numpy as np
import string
# import traceback
from itertools import chain
from objc_util import NSRange, on_main_thread, ObjCClass
from objc_util import ObjCInstance, c_void_p, c, CGSize, ns
from mido import mido
import logging

soundfont = 'OmegaGMGS2.sf2'

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s]: %(message)s'
    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set root logger level to DEBUG
           

class Key (object):
  def __init__(self, frame):
    self.frame = ui.Rect(*frame)
    self.name = None
    self.color = Color(1, 1, 1, 1)
    self.highlight_color = Color(0.9, 0.9, 0.9, 1)
    

class Karaoke():
    def __init__(self, zip_file_path):
       self.kar_only = False
       self.filelist = self.get_zipfile_names(zip_file_path)
       self.temp_file_path = 'temp.mid'
       self.zip_file_path = zip_file_path
       self.gui = ui.load_view('karaoke_player.pyui')
       self.lyrics = self.gui['lyrics']
       self.image_view = self.gui['noteview']
              
       self.text_lines = None
       self.midiplay = None
       self.mid = None
       self.lyrics_dict = {}
       self.vocal_notes = None
       self.tracknames = []
       self.stop = False
       
       self.gui.present('sheet')
       self.construct_piano()
       self.display_piano()
       
    # -------GUI Interface -------------------------------------- #
    #@ui.in_background
    def select_file(self, sender, test=None):
        """ select karaoke file from midi.zip"""
        if not test:
            selection = dialogs.list_dialog('Select file', self.filelist)
        else:
            selection = test
            print(test)
        if selection:
            self.extract_zip_item_to_temp(selection)
            if self.open_midifile(self.temp_file_path):
                self.lyrics_dict, selected_notes, best_track_id = self.parse()
                if not self.lyrics_dict:
                   self.all_text = f'No Lyrics:  {self.tracknames[0]}'
                else:
                    text_lines = [text.replace('\\', '\n\n').replace('/', '\n')
                                  for text in self.lyrics_dict.values()]
                    # produce all text as single string
                    self.all_text = ''.join(text_lines)
                    
                    # if not delimiters, replace period with CR after          
                    if '/' not in self.all_text:
                        self.all_text = self.all_text.replace('.', '\n')
                   
                self.lyrics.text = self.all_text
                
                self.init_colours()
                self.text_height = self.get_text_height_pixels()
                name = self.tracknames[best_track_id]
                self.vocal_range(selected_notes)
                max_note_time = max(list(selected_notes))
                self.gui.name = f'{selection}    ({max_note_time:.2f}s)'
                self.gui['track'].title = name
            
    @ui.in_background
    def select_track(self, sender):
        """ manually select a track with melody or vocal notes
            all midi files have different names for tracks
        """
        if self.tracknames:
            tracklist = [f'{track_no}-{track_name}'
                         for track_no, track_name in self.tracknames.items()]
            selection = dialogs.list_dialog('Select trackname', tracklist)
            if selection:
                track_id = int(selection.split('-')[0])
                all_tracks_notes = self.get_notes()                                    
                self.selected_notes = all_tracks_notes.get(track_id, {})                        
                self.vocal_range(self.selected_notes)
                self.gui['track'].title = selection
                
    #@ui.in_background  
    def stop_midi(self, sender):
       if self.midiplay:
           self.midiplay.stop()
           self.midiplay = None
       self.stop = True
       
    def set_karaoke_only(self, sender):      
        self.kar_only = sender.value       
        self.filelist = self.get_zipfile_names(self.zip_file_path)
        self.gui['label1'].text = 'KAR only' if self.kar_only else ''
        
    @on_main_thread
    def init_colours(self, r=1.0, g=0.9, b=0.3, a=1.0):
        """ allow coloured text background in TextView object """
        UIColor = ObjCClass('UIColor')
        self.UIfont = ObjCClass('UIFont').fontWithName_size_(*self.lyrics.font)
        self.textview_objc = ObjCInstance(self.lyrics)
        self.textview_objc.setAllowsEditingTextAttributes_(True)
        self.string_objc = ObjCClass(
            'NSMutableAttributedString').alloc().initWithString_(self.lyrics.text)
        self.string_objc.addAttribute_value_range_(
            ObjCInstance(c_void_p.in_dll(c, 'NSFontAttributeName')),
            self.UIfont, NSRange(0, len(self.lyrics.text)))
        
        self.colors = {
            'red': UIColor.redColor(),
            'green': UIColor.greenColor(),
            'blue': UIColor.blueColor(),
            'cyan': UIColor.cyanColor(),
            'magenta': UIColor.magentaColor(),
            'black': UIColor.blackColor(),
            'yellow': UIColor.yellowColor(),
            'orange': UIColor.orangeColor(),
            'purple': UIColor.purpleColor(),
            'clear': UIColor.clearColor(),
            'custom': UIColor.color(red=r, green=g, blue=b, alpha=a)}

    @on_main_thread
    def get_text_height_pixels(self):
        """
        Calculates the pixel height of a text string using the font
        from a ui.TextView.
        :return: The height of the text in pixels (CGFloat, a float value).
        """
        text = 'abcdefg'  # includes descender
        attributes = ns({'NSFont': self.textview_objc.font()})
        ns_text = ns(text)
        
        # Define a bounding size constraint
        # The width is set to 'inf' to ensure it's measured as a single line.
        constraint_size = CGSize(float('inf'), float('inf'))
        rect = ns_text.boundingRectWithSize_options_attributes_context_(
            constraint_size,
            1,  # NSStringDrawingUsesLineFragmentOrigin
            attributes,
            None)
        return rect.size.height
        
    @on_main_thread
    # apparently this must be called on main thread for textview
    def colour_display(self, start, end, color='red', background=False):
        """
        This code colours a selected portion of the text as color
        start and end are the indexes of the text contents
        """
        # clear all colours
        if background:
           self.string_objc.addAttribute_value_range_(
            'NSBackgroundColor', self.colors['clear'],
            NSRange(0, len(self.all_text)))
           self.textview_objc.setAttributedText_(self.string_objc)
           self.string_objc.addAttribute_value_range_(
              'NSBackgroundColor', self.colors[color],
              NSRange(start, end - start))
        else:
            # self.string_objc.addAttribute_value_range_(
            #    'NSColor', self.colors['black'],
            #    NSRange(0, len(self.all_text)))
            # self.textview_objc.setAttributedText_(self.string_objc)
            self.string_objc.addAttribute_value_range_(
               'NSColor', self.colors[color],
               NSRange(start, end - start))
        self.textview_objc.setAttributedText_(self.string_objc)
   
    def construct_piano(self, min_octave=3, max_octave=7):
        """ create piano key objects for later drawing """
        octave_range = range(min_octave, max_octave + 1)
        no_octaves = len(octave_range)
        self.white_keys = []
        self.black_keys = []
        white_key_names = [f'{k}{oct}' for oct in octave_range
                           for k in 'CDEFGAB']
        black_key_names = [f'{k}#{oct}' for oct in octave_range
                           for k in 'CDFGA']
        white_positions = range(7)
        black_positions = [0.75, 1.75, 3.75, 4.75, 5.75]
        key_h = self.image_view.height - 20
        key_w = self.image_view.width / (no_octaves * 7) - 0.5
        for octave in range(no_octaves):
            for i, position in enumerate(white_positions):
                pos = position + (octave * 7)
                key = Key((pos * key_w + 5, 10,
                           key_w, key_h))
                key.name = white_key_names[i + octave * 7]
                self.white_keys.append(key)
            for i, position in enumerate(black_positions):
                pos = position + (octave * 7)
                key = Key((pos * key_w + 5, 10,
                           key_w * 0.5, key_h * 0.6))
                key.name = black_key_names[i + octave * 5]
                key.color = Color(0, 0, 0, 1)
                self.black_keys.append(key)
             
        # top line to cover rounded edges
        # right x is end of last white key
        left_x = self.white_keys[0].frame.x
        right_x = self.white_keys[-1].frame.max_x
        y = self.white_keys[0].frame.y + 2
        self.topline = (left_x, right_x, y)
        
    def display_piano(self, pressed_keys=None):
        """perform ui plotting of piano keyboard
           pressed_keys is list of note_name
        """
        
        if pressed_keys is None:
            pressed_keys = []
             
        def draw_top_line():
            # top line to cover rounded edges of keys
            left_x, right_x, y = self.topline
            ui.set_color('grey')
            p = ui.Path()
            p.line_cap_style = ui.LINE_CAP_ROUND
            p.line_width = 7
            p.move_to(left_x, y)
            p.line_to(right_x, y)
            p.stroke()
                    
        with ui.ImageContext(self.image_view.width,
                             self.image_view.height) as ctx:
            # t1=time.time() 
            for key in chain(self.white_keys, self.black_keys):
                # outline                
                ui.set_color('black')                
                box = ui.Path.rounded_rect(*key.frame, 6)
                box.line_width = 2
                box.stroke()                
                # fill colour
                if key.name in pressed_keys:
                    color = key.highlight_color.as_tuple()
                else:
                    color = key.color.as_tuple()
                ui.set_color(color)
                box.fill() 
                                            
            draw_top_line()
               
            # white key note names
            for key in self.white_keys:
                ui.draw_string(key.name,
                               rect=(key.frame.x, key.frame.h - 20, 30, 10),
                               font=('Arial', 10),
                               color='black',
                               alignment=ui.ALIGN_CENTER)
                          
            self.image_view.image = ctx.get_image()
            # print(time.time()-t1)
    @ui.in_background
    def play_midi(self, sender):
        # play the midi file and display lyrics
        
        if True: #self.lyrics_dict:
            if os.path.exists(soundfont):
                self.midiplay = sound.MIDIPlayer(self.temp_file_path, soundfont)
            else:
                self.midiplay = sound.MIDIPlayer(self.temp_file_path)
            # self.midiplay.stop()
            # Merge events for playback
            # Event tuple: (time, type, content)
            lyrics_ = [(t, 'LYRIC', text)
                       for t, text in self.lyrics_dict.items()]
            notes_ = [(t, 'NOTE', notes)    
                      for t, notes in self.selected_notes.items()]
            timeline = lyrics_ + notes_
                
            # Sort by time
            timeline.sort(key=lambda x: x[0])

            # start playing
            self.stop = False
            self.midiplay.play()
            start_time = time.time()
            start_index = 0
            for event_time, event_type, content in timeline:
                if self.stop:
                    return
                # Wait until it's time for this event
                while True:
                    current_offset = time.time() - start_time #self.midiplay.current_time
                    self.gui['current_time'].text = f' Time: {current_offset:.2f}s'
                    if current_offset >= event_time:
                        break
                    time.sleep(0.001)  # Short sleep to prevent CPU hogging
                   
                # Formatted Output
                time_str = f"{event_time:05.2f}"
                self.gui['current_time'].text = f' Time: {current_offset:.2f}s'
                if event_type == 'LYRIC':
                    self.gui['lyric'].text = content
                    # print(f"{time_str} LYRICS {content}")
                    length = len(content)
                    end_index = start_index + length
                    self.colour_display(start_index, end_index, color='red')
                    start_index = end_index
                    # count number of CR for scrolling
                    line_count = self.all_text[:end_index].count('\n')
                    # scroll towards the end of screen
                    text_height = line_count * self.text_height
                    if text_height > self.lyrics.height - 3 * self.text_height:
                        self.lyrics.content_offset = (0, text_height - self.lyrics.height + 3 * self.text_height)
                else:
                    self.display_piano(content)
                    self.gui['notes'].text = " ".join(content)
                    # print(f'{time_str} NOTES {" ".join(content)}')                                 
                    
            print("\n--- END OF PLAYBACK ---")
            self.stop = True
            return
            
    def vocal_range(self, vocal_notes):
        """ Find range of vocal track and display """
        unique_names = set(sum(vocal_notes.values(), []))
        unique_notes = [self.midi_note_to_number(note_name)
                        for note_name in unique_names]
        min_note = self.midi_number_to_note(min(unique_notes))
        max_note = self.midi_number_to_note(max(unique_notes))
        min_octave = int(self.midi_number_to_note(min(unique_notes))[-1])
        max_octave = int(self.midi_number_to_note(max(unique_notes))[-1])
        
        
        self.construct_piano(min_octave, max_octave)
        self.display_piano(None)
        
        notespan = f' {min_note}:  {max_note}'
        self.gui['notespan'].text = notespan
                                            
        self.gui['starts'].text = f" Lyric starts: {min(vocal_notes):0.1f}s"
        return self.vocal_notes
            
    # -------MIDI Processing -------------------------------- #
    def get_zipfile_names(self, zip_file_path):
        # get all filenames from zip file
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                if self.kar_only:
                    file_list = sorted([name
                                        for name in zip_ref.namelist()
                                        if name.lower().endswith('.kar')])
                else:
                    file_list = sorted([name
                                        for name in zip_ref.namelist()])
                return file_list
        except zipfile.BadZipFile:
            logger.info(f"Error: {zip_file_path} is not a valid zip file.")
            return None
        except FileNotFoundError:
            logger.info(f"Error: The file {zip_file_path} was not found.")
            return None
    
    def extract_zip_item_to_temp(self, item_name):
        """
        Opens a zip file, extracts a specific item's content, and saves it
        to a temporary file temp.mid
        """
        try:
            # 1. Open the Zip File
            with zipfile.ZipFile(self.zip_file_path, 'r') as zf:
                # 2. Check if the item exists in the archive
                if item_name not in zf.namelist():
                    logger.info(f"Error: Item '{item_name}' not found in the zip file.")
                    return None
                # 3. Create a Temporary File
                with open(self.temp_file_path, mode='wb') as temp_file:
                    # 4. Read the item's content and write to the temporary file
                    content = zf.read(item_name)
                    temp_file.write(content)
                return self.temp_file_path
        except FileNotFoundError:
            logger.info(f"Error: Zip file not found at {self.zip_filepath}")
            return None
        except Exception as e:
            logger.info(f"An unexpected error occurred: {e}")
            # Clean up the temp file if it was created but an error occurred later
            if self.temp_file_path and os.path.exists(self.temp_file_path):
                os.remove(self.temp_file_path)
            return None
                  
    def open_midifile(self, file_path):
        """ Opens and reads  MIDI file """
        try:
            self.mid = mido.MidiFile(file_path)
            return self.mid
        except FileNotFoundError:
            logger.info(f"Error: File not found at {file_path}")
            return None
        except Exception as e:
            logger.info(f"Error reading MIDI file: {e}")
            return None
            
    def get_tracknames(self):
       # get tracknames, filter any non-ascii characters
        tracknames = {}
        for i, track in enumerate(self.mid.tracks):
            for msg in track:
                if hasattr(msg, 'name'):
                    printable = ''.join(filter(lambda x: x in string.printable, msg.name))
                    tracknames[i] = printable
                    break
            else:
                tracknames[i] = 'Noname'
        return tracknames
        
    def _build_tempo_map(self):
        """
        Scans all tracks for tempo changes to create a function
        that converts absolute ticks to absolute seconds.
        """
        # Find all tempo messages across all tracks
        tempo_events = []
        for track in self.mid.tracks:
            curr_ticks = 0
            for msg in track:
                curr_ticks += msg.time
                if msg.type == 'set_tempo':
                    tempo_events.append((curr_ticks, msg.tempo))
        
        tempo_events.sort(key=lambda x: x[0])
        
        # Create a conversion lookup
        # We process segments between tempo changes
        timeline = []  # (tick_start, time_start, micro_per_tick)
        
        current_tempo = 500000  # Default MIDI tempo (120 BPM)
        current_abs_time = 0.0
        last_tick = 0
        
        for tick, tempo in tempo_events:
            delta_ticks = tick - last_tick
            if delta_ticks > 0:
                seconds = mido.tick2second(delta_ticks, self.ticks_per_beat, current_tempo)
                current_abs_time += seconds
                
            timeline.append({
                'tick': tick,
                'seconds': current_abs_time,
                'tempo': tempo
            })
            last_tick = tick
            current_tempo = tempo
            
        return timeline

    def get_seconds_at_tick(self, target_tick):
        """Converts a specific tick timestamp to seconds using the timeline."""
        current_tempo = 500000
        acc_time = 0.0
        last_tick = 0
        
        # Determine starting point from timeline
        # (Optimization: could use binary search, but linear is fine for MIDI size)
        for point in self.tick_seconds_map:
            if target_tick < point['tick']:
                break
            current_tempo = point['tempo']
            acc_time = point['seconds']
            last_tick = point['tick']
            
        delta = target_tick - last_tick
        acc_time += mido.tick2second(delta, self.ticks_per_beat, current_tempo)
        return acc_time

    def get_notes(self):
        # Parse Tracks for Notes
        # Format: {track_index: {time_in_seconds: [note_names]}}
        all_tracks_notes = {}
        
        for i, track in enumerate(self.mid.tracks):
            curr_ticks = 0
            track_notes = {}
            has_notes = False
            for msg in track:
                curr_ticks += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    has_notes = True
                    t_sec = self.get_seconds_at_tick(curr_ticks)
                    note_name = self.midi_number_to_note(msg.note)
                    
                    # Rounding to 2 decimal places to group simultaneous chords
                    t_key = round(t_sec, 2)
                    
                    if t_key not in track_notes:
                        track_notes[t_key] = []
                    track_notes[t_key].append(note_name)
            
            if has_notes:
                all_tracks_notes[i] = track_notes
        return all_tracks_notes
   
    def parse(self):
        self.ticks_per_beat = self.mid.ticks_per_beat
        
        # 1. Build a map of Tick -> Absolute Seconds based on tempo changes
        self.tick_seconds_map = self._build_tempo_map()
                
        self.lyrics_dict, self.lyric_timestamps = self.get_lyrics()
        if not self.lyrics_dict:
            print("Warning: No lyrics found in this MIDI file.")
        else:
            print(f"Found {len(self.lyrics_dict)} lyric events.")

        all_tracks_notes = self.get_notes()

        # Find Best Matching Track
        best_track_id = self.get_melody_track(all_tracks_notes)
        if not best_track_id:
            best_track_id = self.get_best_matching_melody_track(all_tracks_notes)

        self.selected_notes = all_tracks_notes.get(best_track_id, {})
        print(f"Selected Track {best_track_id} {self.tracknames[best_track_id]} as the melody match.")
        
        return self.lyrics_dict, self.selected_notes, best_track_id
            
    def get_lyrics(self):
        # Extract Lyrics
        # Format: {time_in_seconds: "lyric_text"}
        lyrics_dict = {}
        lyric_timestamps = []
        
        for track in self.mid.tracks:
            curr_ticks = 0
            for msg in track:
                curr_ticks += msg.time
                if msg.type in ['lyrics', 'text', 'marker']:
                    # Filter out non-lyrical meta text if possible, but keep simple
                    if msg.text.strip():
                        t_sec = self.get_seconds_at_tick(curr_ticks)
                        lyrics_dict[t_sec] = msg.text
                        lyric_timestamps.append(t_sec)
        return lyrics_dict, lyric_timestamps

    def get_melody_track(self, all_tracks_notes):
        self.tracknames = self.get_tracknames()
        # if track is obviously named, choose it if it contains notes
        best_track_id = None                
        for reserved in ['voice', 'melody','vocal', 'male']:
            for i, trackname in self.tracknames.items():
                if reserved in trackname.lower():
                    if i in all_tracks_notes:
                       best_track_id = i
                       return best_track_id
                       
    def get_best_matching_melody_track(self, all_track_notes):
        """guess melody track from start time """
                
        def resize_and_compare(target, candidate):
            """ find match score of two arrays for values and length
                Dynamic Time Warping algorithm
                https://en.wikipedia.org/wiki/Dynamic_time_warping"""
            target_indices = np.linspace(0, len(candidate)-1, len(target))
            # Interpolate candidate to match target length
            candidate_resized = np.interp(target_indices, np.arange(len(candidate)), np.array(list(candidate)))
            return np.linalg.norm(np.array(list(target) - candidate_resized))  # Euclidean distance
                
        # if track is obviously named, choose it
        track_id = self.get_melody_track(all_track_notes)
        if track_id:
            return track_id, None
                     
        # else find best fit to lyric track
        lyric_times = self.lyrics_dict.keys()
        # rate scores from DTW
        scores = {track: resize_and_compare(lyric_times, times.keys())
                  for track, times in all_track_notes.items()}
        # return name of track with lowest score
        best = sorted(scores.items(), key=lambda item: item[1])[0]
        if best[1] == 0.0: # no valid best
            # choose track with least notes
            lengths = {k: len(v) for k, v in all_track_notes.items()}           
            best = (min(lengths, key=lengths.get), 0)
        logger.debug(f'Best match {best}')
        for number, score in scores.items():
            logger.debug(f'{number} {self.tracknames[number]} {int(score)}')
                                                 
        return best[0]
                      
    def midi_number_to_note(self, number):
        """Converts a MIDI number (e.g., 60) to a note name (e.g., C4)."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = number // 12 - 1
        note_name = notes[number % 12]
        return f"{note_name}{octave}"
        
    def midi_note_to_number(self, note_name):
        """Converts a MIDI number (e.g., 60) to a note name (e.g., C4).
        Allow negative octave"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        match = re.match(r"^([A-G][b#]?)(-?\d+)$", note_name.strip(), re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid note format: '{note_name}'. Format should be Note+Octave (e.g., 'C4').")
        note, octave = match.groups()                
        midi_number = (int(octave) + 1) * 12 + notes.index(note.upper())
 
        if not (0 <= midi_number <= 127):
           raise ValueError(f"Note '{note_name}' results in MIDI {midi_number}, which is out of range (0-127).")

        return midi_number

def main():
    ZIP_FILE = 'midis.zip'
    k = Karaoke(ZIP_FILE)    
    #k.select_file(None, 'I Will.mid')    
    #for f in k.filelist
    #    k.select_file(None, f)
        
if __name__ == "__main__":
    import cProfile
    main()
    #cProfile.run('main()')

    
    
