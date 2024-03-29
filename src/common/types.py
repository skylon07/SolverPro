from abc import ABC


class EnumInstance(ABC):
    def __init__(self, *args):
        self._args = args
    
    def __repr__(self):
        return repr(list(self._args))[1:-1]
    
    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        
        return self._args == other._args
    
    def __hash__(self):
        return hash(self._args)


class EnumString(ABC):
    def __init__(self, reprStr: str):
        self._reprStr = reprStr
    
    def __repr__(self):
        return self._reprStr
    
    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        
        return self._reprStr == other._reprStr
    
    def __hash__(self):
        return hash(self._reprStr)


class Enum(ABC):
    __reservedNames = ("listInstances",)

    @classmethod
    def listInstances(cls):
        return tuple(
            propName
            for propName in dir(cls)
            if propName[:1] != "_" and propName not in cls.__reservedNames
        )

FormattedStr = str
