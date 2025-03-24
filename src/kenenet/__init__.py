import sys, zhmiscellany, keyboard, mss, time, os, random, pyperclip, inspect, datetime, atexit
import numpy as np
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play
global timings, ospid, debug_mode
ospid, debug_mode = None, False
timings = {}

def quick_print(message, l=None):
    if l: sys.stdout.write(f"\033[38;2;0;255;26m{l} || {message}\033[0m\n")
    else: sys.stdout.write(f"\033[38;2;0;255;26m {message}\033[0m\n")


def get_pos(key='f10', kill=False):
    coord_rgb = []
    coords = []
    def _get_pos(key, kill=False):
        while True:
            keyboard.wait(key)
            x, y = zhmiscellany.misc.get_mouse_xy()
            with mss.mss() as sct:
                region = {"left": x, "top": y, "width": 1, "height": 1}
                screenshot = sct.grab(region)
                rgb = screenshot.pixel(0, 0)
            color = f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
            reset = "\033[38;2;0;255;26m"
            coord_rgb.append({'coord': (x,y), 'RGB': rgb})
            coords.append((x,y))
            pyperclip.copy(f'coords_rgb = {coord_rgb}\ncoords = {coords}')
            quick_print(f"Added Coordinates: ({x}, {y}), RGB: {rgb} {color}████████{reset} to clipboard", lineno)
            if kill:
                quick_print('killing process')
                zhmiscellany.misc.die()
    quick_print(f'Press {key} when ever you want the location')
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    _get_pos(key, kill)

def timer(clock=1):
    if clock in timings:
        elapsed = time.time() - timings[clock]
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        quick_print(f'Timer {clock} took \033[97m{elapsed}\033[0m seconds', lineno)
        del timings[clock]
        return elapsed
    else:
        timings[clock] = time.time()


class Config:
    EXCLUDED_NAMES = {'Config', 'VariableTracker', 'track_variables', 'stop_tracking',
                      'track_frame', 'sys', 'inspect', 'types', 'datetime',
                      'self', 'cls', 'args', 'kwargs', '__class__'}
    EXCLUDED_FILES = {'<string>', '<frozen importlib', 'importlib', 'abc.py', 'typing.py', '_collections_abc.py'}
    SHOW_TIMESTAMPS = True
    EXCLUDE_INTERNALS = True


# ==========================================================================
# CORE TRACKING FUNCTIONALITY
# ==========================================================================

class VariableTracker:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VariableTracker()
        return cls._instance
    
    def __init__(self):
        self.active = False
        self.frame_locals = {}
        self.global_vars = {}
    
    def format_value(self, value):
        try:
            return repr(value)
        except:
            return f"<{type(value).__name__} object>"
    
    def print_change(self, name, old, new, scope="Global"):
        timestamp = f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] " if Config.SHOW_TIMESTAMPS else ""
        print(f"{timestamp}{scope} '{name}' changed from {self.format_value(old)} to {self.format_value(new)}")
    
    def _should_track(self, name):
        return not (name.startswith('_') and name not in ('__name__', '__file__')) and name not in Config.EXCLUDED_NAMES
    
    def start_tracking(self, module_name):
        if self.active: return
        module = sys.modules[module_name]
        self.global_vars = {name: value for name, value in module.__dict__.items() if self._should_track(name)}
        sys.settrace(track_frame)
        self.active = True
        print(f"Variable tracking started at {datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    def stop_tracking(self):
        if not self.active: return
        sys.settrace(None)
        self.frame_locals.clear()
        self.global_vars.clear()
        self.active = False
        print(f"Variable tracking stopped at {datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}")


# ==========================================================================
# TRACE FUNCTION
# ==========================================================================

def track_frame(frame, event, arg):
    tracker = VariableTracker.get_instance()
    if not tracker.active or event != 'line': return track_frame
    scope = "Global" if frame.f_code.co_name == '<module>' else f"Local in '{frame.f_code.co_name}'"
    current_vars = {name: value for name, value in (frame.f_locals if scope != "Global" else frame.f_globals).items() if tracker._should_track(name)}
    
    if scope == "Global":
        for name, value in current_vars.items():
            if name not in tracker.global_vars:
                tracker.print_change(name, None, value, scope)
            elif tracker.global_vars[name] != value:
                tracker.print_change(name, tracker.global_vars[name], value, scope)
        tracker.global_vars.update(current_vars)
    else:
        frame_id = id(frame)
        if frame_id not in tracker.frame_locals:
            for name, value in current_vars.items():
                tracker.print_change(name, None, value, scope)
        else:
            for name, value in current_vars.items():
                if name not in tracker.frame_locals[frame_id]:
                    tracker.print_change(name, None, value, scope)
                elif tracker.frame_locals[frame_id][name] != value:
                    tracker.print_change(name, tracker.frame_locals[frame_id][name], value, scope)
        tracker.frame_locals[frame_id] = current_vars
    if event == 'return' and scope != "Global": del tracker.frame_locals[id(frame)]
    return track_frame


# ==========================================================================
# PUBLIC API
# ==========================================================================

def debug():
    global debug_mode
    if not debug_mode:
        debug_mode = True
        caller_frame = inspect.currentframe().f_back
        module_name = caller_frame.f_globals['__name__']
        tracker = VariableTracker.get_instance()
        tracker.start_tracking(module_name)
        caller_frame.f_trace = track_frame
    if debug_mode:
        debug_mode = False
        VariableTracker.get_instance().stop_tracking()


def stop_debug():
    VariableTracker.get_instance().stop_tracking()

def pp(msg='caca', subdir=None, pps=3):
    import os, subprocess
    os_current = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    if subdir: os.chdir(subdir)
    def push(message):
        os.system('git add .')
        os.system(f'git commit -m "{message}"')
        os.system('git push -u origin master')
    def pull():
        os.system('git pull origin master')
    def push_pull(message):
        push(message)
        pull()
    result = subprocess.run(['git', 'rev-list', '--count', '--all'], capture_output=True, text=True)
    result = int(result.stdout.strip()) + 1
    for i in range(pps):
        push_pull(msg)
    quick_print('PP finished B======D')
    os.chdir(os_current)

def save_img(img, name=' ', reset=True, file='temp_screenshots', mute=False):
    global ospid
    if os.path.exists(file):
        if reset and ospid is None:
            zhmiscellany.fileio.empty_directory(file)
            quick_print(f'Cleaned folder {file}')
    else:
        quick_print(f'New folder created {file}')
        zhmiscellany.fileio.create_folder(file)
    ospid = True
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    if isinstance(img, np.ndarray):
        save_name = name + f'{time.time()}'
        img = Image.fromarray(img)
        img.save(fr'{file}\{save_name}.png')
        if not mute: quick_print(f'Saved image as {save_name}', lineno)
    else:
        quick_print(f"Your img is not a fucking numpy array you twat, couldn't save {name}", lineno)

def load_audio(mp3_path):
    from zhmiscellany._processing_supportfuncs import _ray_init_thread; _ray_init_thread.join()
    return AudioSegment.from_mp3(mp3_path)
    
def play_audio(file_sound, range=(0.9, 1.1)):
    sound = file_sound
    sound = sound._spawn(sound.raw_data, overrides={'frame_rate': int(sound.frame_rate * random.uniform(*range))})
    zhmiscellany.processing.multiprocess_threaded(play, (sound,))
    
class k:
    pass

current_module = sys.modules[__name__]
for name, func in inspect.getmembers(current_module, inspect.isfunction):
    if not name.startswith('_'):
        setattr(k, name, func)

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
