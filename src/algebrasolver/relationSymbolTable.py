from typing import TypeVar, overload

import sympy

from src.algebrasolver.types import *

class RelationSymbolTable:
    """
    Dictionaries are cool, but they only map keys to values. What if you
    want a two-way dictionary that records pairs of symbols and relations?
    Well then, you probably want this table.

    As it was suggested, if I have a table initialized as such

    ```raw
    (a, b) = sympy.symbols("a, b")
    table[a] = Relation(a + b, 6)
    table[Relation(b, a - 2)] = b
    ```

    then it follows that

    ```raw
    assert table[Relation(a + b, 6)] == a
    assert table[b] == Relation(b, a - 2)
    ```
    """

    _DefaultType = TypeVar("_DefaultType")

    def __init__(self):
        self._inferredSymbols: dict[Relation, sympy.Symbol] = dict()
        self._solvedRelations: dict[sympy.Symbol, Relation] = dict()

    @overload
    def __getitem__(self, key: sympy.Symbol) -> Relation: ...
    @overload
    def __getitem__(self, key: Relation) -> sympy.Symbol: ...

    def __getitem__(self, key: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            return self._solvedRelations[key]
        elif type(key) is Relation:
            return self._inferredSymbols[key]
        else:
            raise KeyError(key)

    @overload 
    def __setitem__(self, key: sympy.Symbol, value: Relation) -> None: ...
    @overload
    def __setitem__(self, key: Relation, value: sympy.Symbol) -> None: ...

    def __setitem__(self, key: sympy.Symbol | Relation, value: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            assert type(value) is Relation
            self._solvedRelations[key] = value
            self._inferredSymbols[value] = key
        elif type(key) is Relation:
            assert type(value) is sympy.Symbol
            self._inferredSymbols[key] = value
            self._solvedRelations[value] = key
        else:
            raise KeyError(key)
        
    @overload
    def __contains__(self, key: sympy.Symbol) -> bool: ...
    @overload
    def __contains__(self, key: Relation) -> bool: ...

    def __contains__(self, key: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            return key in self._solvedRelations
        elif type(key) is Relation:
            return key in self._inferredSymbols
        else:
            raise KeyError(key)
        
    def copy(self):
        newTable = RelationSymbolTable()
        newTable._inferredSymbols = dict(self._inferredSymbols)
        newTable._solvedRelations = dict(self._solvedRelations)
        return newTable
        
    @overload
    def get(self, key: sympy.Symbol, default: _DefaultType = None) -> Relation | _DefaultType: ...
    @overload
    def get(self, key: Relation, default: _DefaultType = None) -> sympy.Symbol | _DefaultType: ...

    def get(self, key: sympy.Symbol | Relation, default: _DefaultType = None) -> sympy.Symbol | Relation | _DefaultType:
        if type(key) is sympy.Symbol:
            return self._solvedRelations.get(key, default)
        elif type(key) is Relation:
            return self._inferredSymbols.get(key, default)
        else:
            # return default?
            # naw...
            # if you pass in the wrong type of thing, that's a bug!
            raise KeyError(key)
    
    @overload
    def pop(self, key: sympy.Symbol) -> Relation: ...
    @overload
    def pop(self, key: Relation) -> sympy.Symbol: ...

    def pop(self, key: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            value = self._solvedRelations.pop(key)
            self._inferredSymbols.pop(value)
            return value
        elif type(key) is Relation:
            value = self._inferredSymbols.pop(key)
            self._solvedRelations.pop(value)
            return value
        else:
            raise KeyError(key)
        

