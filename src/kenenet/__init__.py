import sys, zhmiscellany, keyboard, mss, time, linecache, os, random, pyperclip, inspect, re
import numpy as np
from PIL import Image
from collections import defaultdict
import threading
import pyaudio
from pydub import AudioSegment
from zhmiscellany._processing_supportfuncs import _ray_init_thread
import zhmiscellany.processing
import math
import pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import io
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
            quick_print(f"Added Coordinates: ({str(x).rjust(3)},{str(y).rjust(3)}), RGB: {str(rgb).ljust(15)} {color}████████{reset} to clipboard", lineno)
            if kill:
                quick_print('killing process')
                zhmiscellany.misc.die()
    quick_print(f'Press {key} when ever you want the location, automatically copies coords/rgb to clipboard')
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    _get_pos(key, kill)

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
            if not mute: quick_print(f'Cleaned folder {file}')
    else:
        quick_print(f'New folder created {file}')
        if not mute: zhmiscellany.fileio.create_folder(file)
    ospid = True
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    if isinstance(img, np.ndarray):
        # detect mask arrays: floating-point, single-channel
        is_mask = img.dtype.kind == 'f' and (img.ndim == 2 or (img.ndim == 3 and img.shape[-1] == 1))
        save_name = name + f'{time.time()}'
        if is_mask:
            # scale mask values [0.0,1.0] to [0,255] grayscale
            mask_uint8 = (img.squeeze() * 255).clip(0,255).astype(np.uint8)
            img_to_save = Image.fromarray(mask_uint8)
        else:
            img_to_save = Image.fromarray(img)
        img_to_save.save(fr'{file}\{save_name}.png')
        if not mute:
            quick_print(f'Saved image as {save_name}', lineno)
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


_timings = defaultdict(list)
_block_timings = defaultdict(float)
_current_context = None
_line_start_time = None
_stack = []
_ignore_line = {'frame = inspect.currentframe().f_back', 'filename = frame.f_code.co_filename', 'if _current_context is None:', 'sys.settrace(None)', 'Function: currentframe', 'return sys._getframe(1) if hasattr(sys, "_getframe") else None'}
_seen_lines = set()  # Track lines we've already processed
_current_function = None
_function_lines = defaultdict(set)  # Track which lines belong to which function
_site_packages_dirs = []  # List to store site-packages directories

# Patterns for generated code constructs to ignore
_ignore_function_patterns = {
    '<dictcomp>',
    '<lambda>',
    '<setcomp>',
    '<listcomp>',
    '<genexpr>',
    '<comprehension>',
    '<module>'
}


# Get site-packages directories from sys.path
for path in sys.path:
    if 'site-packages' in path or 'dist-packages' in path:
        _site_packages_dirs.append(path)


def _is_package_code(filename):
    """Check if the given filename is from an imported package."""
    # Skip if it's in site-packages
    for site_dir in _site_packages_dirs:
        if filename.startswith(site_dir):
            return True
    
    # Skip if it's a built-in module
    if '<' in filename and '>' in filename:  # Handles '<frozen importlib._bootstrap>' etc.
        return True
    
    # Skip standard library modules
    for path in sys.path:
        if 'python' in path.lower() and os.path.isdir(path) and not path.endswith('site-packages'):
            if filename.startswith(path):
                return True
    
    return False

def _is_generated_construct(func_name):
    """Check if the function name is a generated construct like <dictcomp>, <lambda>, etc."""
    return any(pattern in func_name for pattern in _ignore_function_patterns)


def time_code(label=None):
    global _current_context, _timings, _line_start_time, _block_timings, _stack, _ignore_line, _seen_lines, _current_function, _function_lines
    
    # Get the frame of the caller
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    
    if _current_context is None:
        # First call - start timing
        _current_context = label or f"timing_{len(_timings)}"
        quick_print(f"Starting timer: {_current_context}")
        _line_start_time = time.time()
        _block_timings.clear()
        _stack = []
        _seen_lines.clear()  # Reset seen lines
        _function_lines.clear()  # Reset function lines mapping
        
        def trace_function(frame, event, arg):
            global _line_start_time, _stack, _seen_lines, _current_function, _function_lines
            
            if _is_package_code(frame.f_code.co_filename):
                return trace_function
            
            if event == 'call':
                func_name = frame.f_code.co_name
                
                # Skip recording generated constructs
                if _is_generated_construct(func_name):
                    return trace_function
                
                if func_name != 'time_code':
                    _stack.append((func_name, time.time()))
                    _current_function = func_name  # Track current function
                return trace_function
            
            elif event == 'return':
                if _stack:
                    func_name, start_time = _stack.pop()
                    
                    if not _is_generated_construct(func_name):
                        elapsed = time.time() - start_time
                        _block_timings[f"Function: {func_name}"] += elapsed
                    
                    if _current_function == func_name and _stack:
                        _current_function = _stack[-1][0]
                    elif not _stack:
                        _current_function = None
                return None
            
            elif event == 'line':
                lineno = frame.f_lineno
                line_content = linecache.getline(frame.f_code.co_filename, lineno).strip()
                line_id = f"{lineno}:{line_content}"
                
                if not line_content or line_content.startswith('#'):
                    return trace_function
                
                if "time_code" in line_content and _current_context is not None:
                    return trace_function
                
                if _current_function and _is_generated_construct(_current_function):
                    return trace_function
                
                current_time = time.time()
                if _line_start_time is not None:
                    elapsed = current_time - _line_start_time
                    
                    if _current_function:
                        _function_lines[_current_function].add(line_id)
                    
                    _timings[_current_context].append((lineno, line_content, elapsed, line_id in _seen_lines))
                    
                    if re.match(r'\s*(for|while)\s+', line_content):
                        loop_id = f"Loop at line {lineno}: {line_content[:40]}{'...' if len(line_content) > 40 else ''}"
                        _block_timings[loop_id] += elapsed
                    
                    # Mark this line as seen
                    _seen_lines.add(line_id)
                
                _line_start_time = current_time
            
            return trace_function
        
        sys.settrace(trace_function)
    
    else:
        sys.settrace(None)
        context = _current_context
        _current_context = None
        _line_start_time = None
        
        if not _timings[context]:
            quick_print(f"No times recorded: {context}")
            return
        
        aggregated_timings = defaultdict(float)
        first_occurrences = {}
        
        for lineno, line_content, elapsed, is_repeat in _timings[context]:
            line_id = f"{lineno}:{line_content}"
            aggregated_timings[line_id] += elapsed
            
            if line_id not in first_occurrences:
                first_occurrences[line_id] = (lineno, line_content, elapsed)
        
        display_timings = [
            (lineno, line_content, aggregated_timings[f"{lineno}:{line_content}"])
            for lineno, line_content, _ in first_occurrences.values()
            if line_content not in _ignore_line
        ]
        
        sorted_timings = sorted(display_timings, key=lambda x: x[2], reverse=True)
        
        quick_print(f"\nTime spent on each line: {context}")
        quick_print("-" * 80)
        quick_print(f"{'Line':>6} | {'Time':>12} | Code")
        quick_print("-" * 80)
        
        for lineno, line_content, elapsed in sorted_timings:
            quick_print(f"{lineno:6d} | {elapsed:12.6f} | {line_content}")
        
        quick_print("-" * 80)
        total_time = sum(elapsed for _, _, elapsed in sorted_timings)
        quick_print(f"Total execution time: {total_time:.6f}")
        
        if _block_timings:
            quick_print("\nTime spent on chunks of code:")
            quick_print("-" * 80)
            quick_print(f"{'Chunks':^40} | {'Time':>12} | {'% of Time Spent':>10}")
            quick_print("-" * 80)
            
            sorted_blocks = sorted(_block_timings.items(), key=lambda x: x[1], reverse=True)
            
            for block, elapsed in sorted_blocks:
                if (not any(ignore in block for ignore in _ignore_line) and
                        not any(pattern in block for pattern in _ignore_function_patterns)):
                    percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
                    quick_print(f"{block[:40]:40} | {elapsed:12.6f} | {percentage:10.2f}%")
            
            quick_print("-" * 80)
        
        del _timings[context]
        _block_timings.clear()
        _seen_lines.clear()
        _function_lines.clear()


def time_loop(iterable, cutoff_time=0.1):
    start_time = time.time()
    end_time = start_time + cutoff_time
    for item in iterable:
        yield item
        if time.time() > end_time:
            break
            
ct = time_loop

class k:
    pass

current_module = sys.modules[__name__]
for name, func in inspect.getmembers(current_module, inspect.isfunction):
    if not name.startswith('_'):
        setattr(k, name, func)

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
