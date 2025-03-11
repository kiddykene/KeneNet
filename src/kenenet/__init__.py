import inspect, sys


def adding(a, b):
    return a + b


class k:
    pass


k.adding = adding


if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['k'] = k
