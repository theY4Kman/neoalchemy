import sys

try:
    import threading
except ImportError:
    import dummy_threading as threading


py32 = sys.version_info >= (3, 2)
py3k = sys.version_info >= (3, 0)
py2k = sys.version_info <= (3, 0)


if py3k:
    string_types = str,

    import itertools
    itertools_filterfalse = itertools.filterfalse

    if py32:
        callable = callable
    else:
        def callable(fn):
            return hasattr(fn, '__call__')
else:
    string_types = basestring,

    import itertools
    itertools_filterfalse = itertools.ifilterfalse

    callable = callable
