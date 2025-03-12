import inspect, sys, zhmiscellany, keyboard, mss, time, linecache, types
global timings
timings = {}

def _quick_print(message, l=None):
    if l: sys.stdout.write(f"\033[38;2;0;255;26m{l} || {message}\033[0m\n")
    else: sys.stdout.write(f"\033[38;2;0;255;26m {message}\033[0m\n")


def get_pos(key='f10', kill=False):
    def _get_pos(key, lineno):
        while True:
            keyboard.wait(key)
            x, y = zhmiscellany.misc.get_mouse_xy()
            with mss.mss() as sct:
                region = {"left": x, "top": y, "width": 1, "height": 1}
                screenshot = sct.grab(region)
                rgb = screenshot.pixel(0, 0)
            color = f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
            reset = "\033[0m"
            _quick_print(f"Coordinates: ({x}, {y}), RGB: {rgb} {color}████████{reset}", lineno)
            if kill:
                _quick_print('killing process')
                zhmiscellany.misc.die()
    frame = inspect.currentframe().f_back
    lineno = frame.f_lineno
    zhmiscellany.processing.start_daemon(target=_get_pos, args=(key, lineno, ))

def timer(clock=1):
    if clock in timings:
        elapsed = time.time() - timings[clock]
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        _quick_print(f'Timer {clock} took \033[97m{elapsed}\033[0m seconds', lineno)
        del timings[clock]
    else:
        timings[clock] = time.time()


def _make_trace_function(ignore_special_vars=False, ignore_functions=False, ignore_classes=False, ignore_modules=False, ignore_file_path=False):
    """
    Returns a trace function that prints each executed line along with local variables.

    Parameters:
      ignore_special_vars (bool): If True, ignores special system variables such as:
            __name__, __doc__, __package__, __loader__, __spec__, __annotations__, __file__, __cached__
      ignore_functions (bool): If True, ignores function objects.
      ignore_classes (bool): If True, ignores class objects.
      ignore_modules (bool): If True, ignores module objects.
      ignore_file_path (bool): If True, does not print the file path in the header.
    """
    special_vars = {
        "__name__", "__doc__", "__package__", "__loader__",
        "__spec__", "__annotations__", "__file__", "__cached__"
    }
    
    def trace_lines(frame, event, arg):
        if event == 'line':
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            code_line = linecache.getline(filename, lineno).strip()
            # Header for readability.
            header = f"Executing line {lineno}:" if ignore_file_path else f"Executing {filename}:{lineno}:"
            _quick_print("=" * 60)
            _quick_print(header, lineno)
            _quick_print(f"  {code_line}", lineno)
            _quick_print("-" * 60, lineno)
            _quick_print("Local Variables:", lineno)
            for var, value in frame.f_locals.items():
                if ignore_special_vars and var in special_vars:
                    continue
                if ignore_modules and isinstance(value, types.ModuleType):
                    continue
                if ignore_functions and isinstance(value, types.FunctionType):
                    continue
                if ignore_classes and isinstance(value, type):
                    continue
                _quick_print(f"  {var} = {value}", lineno)
            _quick_print("=" * 60, lineno)
        return trace_lines
    
    return trace_lines


def dbug(ignore_special_vars=True, ignore_functions=True, ignore_classes=True, ignore_modules=True, ignore_file_path=True):
    """
    Activates the line-by-line tracing of code execution.

    Parameters:
      ignore_special_vars (bool): If True, omits special variables (e.g. __name__, __doc__, etc.)
      ignore_functions (bool): If True, omits function objects.
      ignore_classes (bool): If True, omits class objects.
      ignore_modules (bool): If True, omits module objects.
      ignore_file_path (bool): If True, only the line number is shown instead of the full file path.
    """
    trace_func = _make_trace_function(
        ignore_special_vars=ignore_special_vars,
        ignore_functions=ignore_functions,
        ignore_classes=ignore_classes,
        ignore_modules=ignore_modules,
        ignore_file_path=ignore_file_path
    )
    sys.settrace(trace_func)
    # Force the current (global) frame to be traced.
    sys._getframe().f_trace = trace_func
    _quick_print("Tracing activated.")


def dbug_stop():
    """Deactivates the tracing."""
    sys.settrace(None)
    _quick_print("Tracing deactivated.")

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
    _quick_print('PP finished B======D')
    os.chdir(os_current)

class k:
    pass

current_module = sys.modules[__name__]
for name, func in inspect.getmembers(current_module, inspect.isfunction):
    if not name.startswith('_'):
        setattr(k, name, func)

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
