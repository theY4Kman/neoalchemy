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
