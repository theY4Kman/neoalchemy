class Node(object):
    """Base class for OGM Nodes"""

    __label__ = None

    @property
    def key(self):
        return self.__class__.__module__ + '.' + self.__class__.__name__
