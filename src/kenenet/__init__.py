import inspect, sys, zhmiscellany, keyboard, mss, time, linecache, types, os, random, pyperclip
import numpy as np
from PIL import Image
global timings, ospid
from pydub import AudioSegment
from pydub.playback import play
ospid = None
timings = {}

def quick_print(message, l=None):
    if l: sys.stdout.write(f"\033[38;2;0;255;26m{l} || {message}\033[0m\n")
    else: sys.stdout.write(f"\033[38;2;0;255;26m {message}\033[0m\n")


def get_pos(key='f10', kill=False):
    coordinates = []
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
            coordinates.append({'coord': (x,y), 'RGB': rgb})
            pyperclip.copy(coordinates)
            quick_print(f"Added Coordinates: ({x}, {y}), RGB: {rgb} {color}████████{reset} to clipboard", lineno)
            if kill:
                quick_print('killing process')
                zhmiscellany.misc.die()
    quick_print(f'Press {key} when ever you want the location')
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    _get_pos(key, kill)
    # zhmiscellany.processing.start_daemon(target=_get_pos, args=(key, lineno, ))

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


def make_trace_function(ignore_special_vars=True, ignore_functions=True, ignore_classes=True, ignore_modules=True, ignore_file_path=True):
    special_vars = {
        "__name__", "__doc__", "__package__", "__loader__",
        "__spec__", "__annotations__", "__file__", "__cached__"
    }
    
    def trace_lines(frame, event, arg):
        if event == 'line':
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            code_line = linecache.getline(filename, lineno).strip()
            
            # Prevent spamming by ensuring we aren't tracing internal Python locks or infinite loops
            if not code_line:
                return trace_lines
            
            header = f"Executing line {lineno}:" if ignore_file_path else f"Executing {filename}:{lineno}:"
            quick_print("=" * 60)
            quick_print(header, lineno)
            quick_print(f"  {code_line}", lineno)
            quick_print("-" * 60, lineno)
            quick_print("Local Variables:", lineno)
            
            for var, value in frame.f_locals.items():
                if ignore_special_vars and var in special_vars:
                    continue
                if ignore_modules and isinstance(value, types.ModuleType):
                    continue
                if ignore_functions and isinstance(value, types.FunctionType):
                    continue
                if ignore_classes and isinstance(value, type):
                    continue
                try:
                    quick_print(f"  {var} = {repr(value)}", lineno)
                except (AttributeError, TypeError, Exception):
                    quick_print(f"  {var} = [unreadable]", lineno)
            
            quick_print("=" * 60, lineno)
        
        return trace_lines
    
    return trace_lines


def activate_tracing(ignore_special_vars=True, ignore_functions=True, ignore_classes=True, ignore_modules=True, ignore_file_path=True):
    trace_func = make_trace_function(
        ignore_special_vars=ignore_special_vars,
        ignore_functions=ignore_functions,
        ignore_classes=ignore_classes,
        ignore_modules=ignore_modules,
        ignore_file_path=ignore_file_path
    )
    sys.settrace(trace_func)
    sys._getframe().f_trace = trace_func
    quick_print("Tracing activated.")


def deactivate_tracing():
    sys.settrace(None)
    quick_print("Tracing deactivated.")

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

def save_img(img, name='', reset=True, file='temp_screenshots'):
    global ospid
    if ospid is None:
        if os.path.exists(file):
            if reset:
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
        img.save(f'{file}/{save_name}.png')
        quick_print(f'Saved image as {save_name}', lineno)
    else:
        quick_print(f"Your img is not a fucking numpy array you twat, couldn't save {name}", lineno)

def load_audio(mp3_path):
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
