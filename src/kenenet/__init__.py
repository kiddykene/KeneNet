import inspect, sys

def adding(a, b):
    return a + b

def subtracting(a, b):
    return a - b

class k:
    pass

# Automatically attach all global functions to class k,
# filtering out any that start with an underscore (like __init__)
current_module = sys.modules[__name__]
for name, func in inspect.getmembers(current_module, inspect.isfunction):
    if not name.startswith('_'):
        setattr(k, name, func)

# Optional: update __main__ if needed
if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
