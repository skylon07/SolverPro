from typing import Callable, Iterable, TypeVar, Any, overload


def getVersion():
    return "0.4.0"

def iterDifference(iter1, iter2):
    for item in iter1:
        if item not in iter2:
            yield item

_firstNoDefault = object()
_IterableType = TypeVar("_IterableType")
_DefaultType = TypeVar("_DefaultType")
@overload
def first(iterable: Iterable[_IterableType]) -> _IterableType: ...
@overload
def first(iterable: Iterable[_IterableType], default: _DefaultType) -> _IterableType | _DefaultType: ...
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

def lazyImportSolverProApp():
    # prevents the "circular import" exception stuff;
    # this function is really only ever needed to assert types,
    # so when building the program in optimized mode,
    # these should be cut out from assert statements anyway
    from src.app.widgets.solverProApp import SolverProApp
    return SolverProApp

# mostly for testing
def runForError(fn: Callable[[], Any]):
    try:
        fn()
        return None
    except Exception as exception:
        return exception
