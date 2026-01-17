import sys, zhmiscellany, keyboard, mss, time, linecache, os, random, pyperclip, inspect, re, ast
import numpy as np
from PIL import Image
from collections import defaultdict
import threading
from pydub import AudioSegment
import zhmiscellany.processing
import math
import pyautogui
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import win32gui
import win32process
import psutil
import cv2
import io
global timings, ospid, debug_mode
ospid, debug_mode = None, False
timings = {}

def quick_print(message, l=None):
    if l: sys.stdout.write(f"\033[38;2;0;255;26m{l} || {message}\033[0m\n")
    else: sys.stdout.write(f"\033[38;2;0;255;26m {message}\033[0m\n")

def get_pos(timer=3.0, key='f7', timed_key='f8', kill=False):
    coord_rgb = []
    coords = []
    def _get_pos(x, y):
        with mss.mss() as sct:
            region = {"left": x, "top": y, "width": 1, "height": 1}
            screenshot = sct.grab(region)
            rgb = screenshot.pixel(0, 0)
        color = f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
        reset = "\033[38;2;0;255;26m"
        coord_rgb.append({'coord': (x,y), 'RGB': rgb})
        coords.append((x,y))
        pyperclip.copy(f'coords_rgb = {coord_rgb}\ncoords = {coords}')
        quick_print(f"Added Coordinates: ({str(x).rjust(3)},{str(y).rjust(3)}), RGB: {str(rgb).ljust(15)} {color}████████{reset} to clipboard")
        if kill:
            quick_print('killing process')
            zhmiscellany.misc.die()
            
    def _non_timer():
        x, y = zhmiscellany.misc.get_mouse_xy()
        _get_pos(x, y)
    
    def _timer():
        x, y = zhmiscellany.misc.get_mouse_xy()
        quick_print(f'waiting {timer} seconds')
        time.sleep(timer)
        _get_pos(x, y)
        
    quick_print(f'Press {key} for cursor info (or {timed_key} for a {timer}s wait before), automatically copies coords/rgb to clipboard')
    keyboard.on_press_key('f7', lambda e: _non_timer())
    keyboard.on_press_key('f8', lambda e: _timer())
    while True:
        time.sleep(5)

def timer(clock=1):
    if clock in timings:
        elapsed = time.time() - timings[clock][0]
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        if clock == 1:
            quick_print(f'Timer took \033[97m{elapsed}\033[0m seconds', f'{timings[clock][1]}-{lineno}')
        else:
            quick_print(f'Timer {clock} took \033[97m{elapsed}\033[0m seconds', f'{timings[clock][1]}-{lineno}')
        del timings[clock]
        return elapsed
    else:
        ct = time.time()
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        timings[clock] = (ct, lineno)

class _Config:
    EXCLUDED_NAMES = {'Config', 'VariableTracker', 'track_variables', 'stop_tracking',
                      'track_frame', 'sys', 'inspect', 'types', 'datetime', 'quick_print',
                      'self', 'cls', 'args', 'kwargs', '__class__'}
    EXCLUDED_FILES = {'<string>', '<frozen importlib', 'importlib', 'abc.py', 'typing.py', '_collections_abc.py'}
    SHOW_TIMESTAMPS = True
    EXCLUDE_INTERNALS = True

class _VariableTracker:
    _instance = None
    
    @classmethod
    def _get_instance(cls):
        if cls._instance is None:
            cls._instance = _VariableTracker()
        return cls._instance
    
    def __init__(self):
        self.active = False
        self.frame_locals = {}
        self.global_vars = {}
    
    def _format_value(self, value):
        try:
            return repr(value)
        except:
            return f"<{type(value).__name__} object>"
    
    def _print_change(self, name, old, new, lineno, scope="Global"):
        quick_print(f"{scope} '{name}' changed from {self._format_value(old)} -> {self._format_value(new)}", lineno)
    
    def _should_track(self, name):
        return not (name.startswith('_') and name not in ('__name__', '__file__')) and name not in _Config.EXCLUDED_NAMES
    
    def _start_tracking(self, module_name):
        if self.active: return
        module = sys.modules[module_name]
        self.global_vars = {name: value for name, value in module.__dict__.items() if self._should_track(name)}
        sys.settrace(_track_frame)
        self.active = True
        frame = inspect.currentframe().f_back.f_back
        lineno = frame.f_lineno
        quick_print(f"Started debugging", lineno)
    
    def _stop_tracking(self):
        if not self.active: return
        sys.settrace(None)
        self.frame_locals.clear()
        self.global_vars.clear()
        self.active = False
        frame = inspect.currentframe().f_back.f_back
        lineno = frame.f_lineno
        quick_print(f"Stopped debugging", lineno)

def _track_frame(frame, event, arg):
    tracker = _VariableTracker._get_instance()
    if not tracker.active or event != 'line': return _track_frame
    # Skip tracking if function name is 'quick_print'
    if frame.f_code.co_name == 'quick_print':
        return _track_frame
    scope = "Global" if frame.f_code.co_name == '<module>' else f"Local in '{frame.f_code.co_name}'"
    current_vars = {name: value for name, value in (frame.f_locals if scope != "Global" else frame.f_globals).items() if tracker._should_track(name)}
    line_number = frame.f_lineno  # Capture the line number where the change occurred
    if scope == "Global":
        for name, value in current_vars.items():
            if name not in tracker.global_vars:
                tracker._print_change(name, None, value, line_number, scope)
            elif tracker.global_vars[name] != value:
                tracker._print_change(name, tracker.global_vars[name], value, line_number, scope)
        tracker.global_vars.update(current_vars)
    else:
        frame_id = id(frame)
        if frame_id not in tracker.frame_locals:
            for name, value in current_vars.items():
                tracker._print_change(name, None, value, line_number, scope)
        else:
            for name, value in current_vars.items():
                if name not in tracker.frame_locals[frame_id]:
                    tracker._print_change(name, None, value, line_number, scope)
                elif tracker.frame_locals[frame_id][name] != value:
                    tracker._print_change(name, tracker.frame_locals[frame_id][name], value, line_number, scope)
        tracker.frame_locals[frame_id] = current_vars
    if event == 'return' and scope != "Global": del tracker.frame_locals[id(frame)]
    return _track_frame

def debug():
    global debug_mode
    if not debug_mode:
        debug_mode = True
        caller_frame = inspect.currentframe().f_back
        module_name = caller_frame.f_globals['__name__']
        tracker = _VariableTracker._get_instance()
        tracker._start_tracking(module_name)
        caller_frame.f_trace = _track_frame
    else:
        debug_mode = False
        _VariableTracker._get_instance()._stop_tracking()

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

class _load_audio:
    def __init__(self):
        pygame.mixer.init()
        self.handles = []
        self.cached_audios = {}
    
    def change_speed(self, sound, speed=1.0):
        new_frame_rate = int(sound.frame_rate * speed)
        new_sound = sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate})
        # Resample back to the original frame rate for compatibility
        return new_sound.set_frame_rate(sound.frame_rate)
    
    class SoundHandle:
        def __init__(self, thread, stop_event, sound_channel=None):
            self.thread = thread
            self.stop_event = stop_event
            self.sound_channel = sound_channel
        
        def stop(self):
            self.stop_event.set()
            if self.sound_channel is not None:
                self.sound_channel.stop()
            if hasattr(self.thread, 'kill'):
                self.thread.kill()
            self.thread.join(timeout=1.0)
    
    def play(self, file_path, volume=1.0, speed=1, loop=False):
        # Handle random speed selection
        if isinstance(speed, tuple):
            speed = random.uniform(speed[0], speed[1])
        
        # Load or use cached audio
        if file_path not in self.cached_audios:
            sound = AudioSegment.from_file(file_path)
            self.cached_audios[file_path] = sound
        else:
            sound = self.cached_audios[file_path]
        
        # Adjust volume: pydub uses decibels.
        # To convert a multiplier to dB change, use: gain = 20 * log10(volume)
        if volume <= 0:
            gain = -120
        else:
            gain = 20 * math.log10(volume)
        sound = sound.apply_gain(gain)
        
        # Apply speed change if needed
        if speed != 1.0:
            sound = self.change_speed(sound, speed)
        
        # Convert to in-memory file object that pygame can read
        buffer = io.BytesIO()
        sound.export(buffer, format="wav")
        buffer.seek(0)
        
        # Create a pygame Sound object
        pygame_sound = pygame.mixer.Sound(buffer)
        
        # Set volume (pygame uses 0.0 to 1.0)
        pygame_sound.set_volume(min(1.0, max(0.0, volume)))
        
        stop_event = threading.Event()
        channel = None
        
        def play_sound():
            nonlocal channel
            try:
                # Find an available channel
                channel = pygame.mixer.find_channel()
                if channel is None:
                    # If no channel is available, create a new one
                    current_channels = pygame.mixer.get_num_channels()
                    pygame.mixer.set_num_channels(current_channels + 1)
                    channel = pygame.mixer.Channel(current_channels)
                
                # Start playing
                channel.play(pygame_sound, loops=-1 if loop else 0)
                
                # Wait until sound is done or stopped
                while channel.get_busy() and not stop_event.is_set():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error playing sound: {e}")
                if channel:
                    channel.stop()
        
        # Start playback in a separate thread so it's nonblocking
        thread = threading.Thread(target=play_sound, daemon=True)
        thread.start()
        
        handle = self.SoundHandle(thread, stop_event, channel)
        self.handles.append(handle)
        return handle
    
play_audio = _load_audio()

def time_func(func, loop=10000, *args, **kwargs):
    func_name = getattr(func, '__name__', repr(func))
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    start = time.time()
    for _ in range(loop):
        func(*args, **kwargs)
    elapsed = time.time() - start
    quick_print(f'{loop:,}x {func_name} took {elapsed}', lineno)
    return elapsed

def time_loop(iterable, cutoff_time=0.1):
    start_time = time.time()
    end_time = start_time + cutoff_time
    for item in iterable:
        yield item
        if time.time() > end_time:
            break
            
ct = time_loop

def get_focused_process_name(mute=False):
    hwnd = win32gui.GetForegroundWindow()
    if hwnd == 0:
        return None
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        pname = psutil.Process(pid).name()
        if not mute:
            quick_print(pname)
        return pname
    except psutil.NoSuchProcess:
        return None

def rgb_at_coord(coord=None):
    """
    returns the rgb value of a single pixel
    """
    if coord is not None:
        with mss.mss() as sct:
            region = {"left": coord[0], "top": coord[1], "width": 1, "height": 1}
            screenshot = sct.grab(region)
            rgb = screenshot.pixel(0, 0)
        return rgb
    else: return None

cr = rgb_at_coord

def rgb_is_at_coord(coord=None, rgb=None, range=1):
    """
    returns a bool based on if an rgb is at a coord
    """
    if not coord or not rgb:
        return False
    with mss.mss() as sct:
        region = {"left": coord[0], "top": coord[1], "width": 1, "height": 1}
        rgb_ac = sct.grab(region).pixel(0, 0)
    return all(abs(a - b) <= range for a, b in zip(rgb_ac, rgb))

irac = rgb_is_at_coord

def if_condition(s):
    """
    goes over a long string of conditions and evaluates each one for debugging
    """
    e = s.strip()[3:] if s.strip().startswith("if ") else s
    tree = ast.parse(e, mode="eval").body
    ctx = {**inspect.currentframe().f_back.f_globals, **inspect.currentframe().f_back.f_locals}
    full = eval(compile(ast.Expression(tree), "<ast>", "eval"), ctx)
    parts = tree.values if isinstance(tree, ast.BoolOp) and isinstance(tree.op, ast.And) else [tree]
    out = []
    for p in parts:
        code = ast.unparse(p)
        val = eval(compile(ast.Expression(p), "<ast>", "eval"), ctx)
        out.append(f"'{code}': {val}")
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    quick_print(f"Overall: {str(full).upper()}, " + ", ".join(out), lineno)
    
if_cond = if_condition

def find_template(image_source, threshold=0.6, compression=0.0, grayscale=False, data=False):
    """
    matches a screenshot of a button to where it is on your screen
    """
    if isinstance(image_source, str):
        template = cv2.imread(image_source, 0 if grayscale else 1)
    else:
        template = image_source
    if template is None:
        return None
    
    scale = max(0.01, 1.0 - min(max(compression, 0), 1))
    screenshot = np.array(pyautogui.screenshot())
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY if grayscale else cv2.COLOR_RGB2BGR)
    t_h, t_w = template.shape[:2]
    if scale < 1.0:
        new_t_size = (max(1, int(t_w * scale)), max(1, int(t_h * scale)))
        new_s_size = (max(1, int(screenshot.shape[1] * scale)), max(1, int(screenshot.shape[0] * scale)))
        template = cv2.resize(template, new_t_size, interpolation=cv2.INTER_AREA)
        screenshot = cv2.resize(screenshot, new_s_size, interpolation=cv2.INTER_AREA)
    res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None if data else None
    
    if data:
        return {
            'coord': (int(max_loc[0] / scale), int(max_loc[1] / scale)),
            'dim': (t_w, t_h),
            'conf': max_val
        }
    h_p, w_p = template.shape[:2]
    return (int((max_loc[0] + w_p // 2) / scale), int((max_loc[1] + h_p // 2) / scale))

click_image = find_template

class k:
    pass

current_module = sys.modules[__name__]
for name, func in inspect.getmembers(current_module, inspect.isfunction):
    if not name.startswith('_'):
        setattr(k, name, func)

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
