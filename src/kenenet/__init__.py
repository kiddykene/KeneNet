import inspect, sys, zhmiscellany, keyboard, mss, time, sys

global timings
timings = {}
def adding(a, b):
    return a + b

def _quick_print(message, l=None):
    if l:
        sys.stdout.write(f"\033[38;2;0;255;26m{l} || {message}\033[0m\n")
    else:
        sys.stdout.write(f"\033[38;2;0;255;26m {message}\033[0m\n")


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

def time_it(clock=1):
    if clock in timings:
        elapsed = time.time() - timings[clock]
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        _quick_print(f'Timer {clock} took \033[97m{elapsed}\033[0m seconds', lineno)
        del timings[clock]
    else:
        timings[clock] = time.time()

    
class k:
    pass

current_module = sys.modules[__name__]
for name, func in inspect.getmembers(current_module, inspect.isfunction):
    if not name.startswith('_'):
        setattr(k, name, func)

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
