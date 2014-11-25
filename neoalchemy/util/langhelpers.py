from . import compat


class _symbol(int):
    def __new__(self, name, doc=None, canonical=None):
        """Construct a new named symbol."""
        assert isinstance(name, compat.string_types)
        if canonical is None:
            canonical = hash(name)
        v = int.__new__(_symbol, canonical)
        v.name = name
        if doc:
            v.__doc__ = doc
        return v

    def __reduce__(self):
        return symbol, (self.name, "x", int(self))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "symbol(%r)" % self.name

_symbol.__name__ = 'symbol'


class symbol(object):
    """A constant symbol.

    >>> symbol('foo') is symbol('foo')
    True
    >>> symbol('foo')
    <symbol 'foo>

    A slight refinement of the MAGICCOOKIE=object() pattern.  The primary
    advantage of symbol() is its repr().  They are also singletons.

    Repeated calls of symbol('name') will all return the same instance.

    The optional ``doc`` argument assigns to ``__doc__``.  This
    is strictly so that Sphinx autoattr picks up the docstring we want
    (it doesn't appear to pick up the in-module docstring if the datamember
    is in a different module - autoattribute also blows up completely).
    If Sphinx fixes/improves this then we would no longer need
    ``doc`` here.

    """
    symbols = {}
    _lock = compat.threading.Lock()

    def __new__(cls, name, doc=None, canonical=None):
        cls._lock.acquire()
        try:
            sym = cls.symbols.get(name)
            if sym is None:
                cls.symbols[name] = sym = _symbol(name, doc, canonical)
            return sym
        finally:
            symbol._lock.release()


_creation_order = 1


def set_creation_order(instance):
    """Assign a '_creation_order' sequence to the given instance.

    This allows multiple instances to be sorted in order of creation
    (typically within a single thread; the counter is not particularly
    threadsafe).

    """
    global _creation_order
    instance._creation_order = _creation_order
    _creation_order += 1


NoneType = type(None)
