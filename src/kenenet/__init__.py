import inspect, sys


def get_defined_objects():
    current_module = sys.modules[__name__]
    objects = {}
    
    for name, obj in globals().items():
        # Ignore built-in functions and modules
        if name.startswith("__") or inspect.ismodule(obj):
            continue
        
        # Ignore imported objects (they will have a different module)
        if hasattr(obj, "__module__") and obj.__module__ != current_module.__name__:
            continue
        
        # Ignore objects defined inside functions (nested scope)
        if inspect.isfunction(obj) and obj.__qualname__ != obj.__name__:
            continue
        if inspect.isclass(obj) and "." in obj.__qualname__:
            continue
        
        objects[name] = obj
    
    return objects


def adding(a, b):
    return a + b

class k:
    pass

objs = get_defined_objects()
for ob in objs:
    setattr(k, ob.__name__, ob)

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k