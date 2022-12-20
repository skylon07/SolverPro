from abc import ABC as AbstractClass

import sympy

from src.common.types import Displayable, Hashable


class Model(Displayable, AbstractClass):
    pass # intentionally empty; provides a common abstract type to inherit from


class SubDict(Model, dict):
    def __init__(self, dictLike = {}, conditions = None):
        if conditions is None:
            if type(dictLike) is SubDict:
                conditions = dictLike._conditions
            else:
                conditions = set()
        
        dictLike = self._assertValidSubDictLike(dictLike)
        super().__init__(dictLike)
        self.conditions = conditions

    def __str__(self):
        return repr(self)

    def __repr__(self):
        dictRepr = super().__repr__(self)
        conditionsRepr = str(self._conditions)[1:-1] if len(self._conditions) > 0 else ""
        return f"SD{dictRepr}<{conditionsRepr}>"

    @property
    def conditions(self):
        return self._conditions

    @conditions.setter
    def conditions(self, newConditions):
        self._conditions = set(newConditions)
        assert all(self._isValidKey(condition) for condition in self._conditions), "SubDict conditions should be a set of valid items"

    def __setitem__(self, key, val):
        assert self._isValidKey(key), "SubDict item should be set by a valid key"
        assert self._isValidVal(val), "SubDict item should be a valid value"
        return super().__setitem__(key, val)

    def update(self, dictLike):
        dictLike = self._assertValidSubDictLike(dictLike)
        return super().update(dictLike)

    def _assertValidSubDictLike(self, dictLike):
        if __debug__:
            dictLike = dict(dictLike)
            assert all(self._isValidKey(key) and self._isValidVal(val) for key in dictLike for val in [key]), "SubDict got invalid key-value pairs"
        return dictLike

    def _isValidKey(self, key):
        return isinstance(key, sympy.Expr)

    def _isValidVal(self, val):
        return isNumeric(val) or isinstance(val, sympy.Basic)


class SubDictList(Model, list):
    def __init__(self, listLike = []):
        listLike = self._assertValidItems(listLike)
        super().__init__(listLike)

    def __repr__(self):
        return "SL{}".format(super().__repr__())

    def __str__(self):
        return repr(self)

    def append(self, subDict):
        assert type(subDict) is SubDict, "SubDictList item must be a SubDict"
        super().append(subDict)

    def extend(self, listLike):
        listLike = self._assertValidItems(listLike)
        super().update(listLike)

    def insert(self, index, subDict):
        assert type(subDict) is SubDict, "SubDictList item must be a SubDict"
        super().insert(index, subDict)

    def _assertValidItems(self, listLike):
        if __debug__:
            listLike = list(listLike)
            assert all(type(subDict) is SubDict for subDict in listLike), "SubDictList items must be SubDicts"
        return listLike


# TODO: other Models


class ValueModel(Model, Hashable, AbstractClass):
    pass # intentionally empty; provides a common abstract type to inherit from


class Identifier(ValueModel):
    def __init__(self, idStr):
        assert type(idStr) is str, "idStr must be a string"
        self._idStr = idStr

    def __repr__(self):
        return "<Identifier: {}>".format(self._idStr)

    def __str__(self):
        return self._idStr

    def __hash__(self):
        return hash(self._idStr)

    def __eq__(self, other):
        return type(other) is Identifier and self._idStr == other._idStr

    @property
    def idStr(self):
        return self._idStr


# TODO: other ValueModels


def isNumeric(obj):
    # TODO: implement RoundedFloat
    class RoundedFloat:
        pass
    objTypeRecognized = isinstance(obj, (int, float, RoundedFloat, sympy.Number, sympy.NumberSymbol))
    if objTypeRecognized:
        return True
    try:
        obj = float(obj)
        return True
    except TypeError:
        return False
