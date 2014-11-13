import sys
import threading


py3k = sys.version_info >= (3, 0)
py2k = sys.version_info <= (3, 0)


if py3k:
    string_types = str,

    import itertools
    itertools_filterfalse = itertools.filterfalse
else:
    string_types = basestring,

    import itertools
    itertools_filterfalse = itertools.ifilterfalse
