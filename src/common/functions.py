def iterDifference(iter1, iter2):
    for item in iter1:
        if item not in iter2:
            yield item

_firstNoDefault = object()
def first(iterable, default = _firstNoDefault):
    try:
        for item in iterable:
            firstItem = item
            # because we...
            return firstItem
    except StopIteration:
        pass
    if default is _firstNoDefault:
        raise ValueError("Iterable contained no elements (and no default value was given)")
    else:
        return default
