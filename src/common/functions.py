from typing import Callable, Iterable, TypeVar

import sympy


def getVersion():
    return "0.3.0"

def iterDifference(iter1, iter2):
    for item in iter1:
        if item not in iter2:
            yield item

_firstNoDefault = object()
_IterableType = TypeVar("_IterableType")
_DefaultType = TypeVar("_DefaultType")
def first(iterable: Iterable[_IterableType], default: _DefaultType = _firstNoDefault) -> _IterableType | _DefaultType:
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
    
def surroundJoin(items: Iterable, prefix: str, suffix: str, separator: str):
    fullSeparator = suffix + separator + prefix
    return prefix + fullSeparator.join(items) + suffix

def isNonSymbolicValue(value: sympy.Basic):
    if isinstance(value, sympy.Number):
        return True
    elif value is sympy.I:
        return True
    elif isinstance(value, sympy.Symbol):
        return False
    elif isinstance(value, sympy.Expr):
        return all(isNonSymbolicValue(arg) for arg in value.args)
    else:
        return False

# mostly for testing
def runForError(fn: Callable[[], None]):
    try:
        fn()
        return None
    except Exception as exception:
        return exception
