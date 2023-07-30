from abc import ABC


class EnumInstance(ABC):
    def __init__(self, reprStr: str):
        self.reprStr = reprStr
    
    def __repr__(self):
        return self.reprStr


class Enum(ABC):
    __reservedNames = ("listInstances",)

    @classmethod
    def listInstances(cls):
        return tuple(
            propName
            for propName in dir(cls)
            if propName[:1] != "_" and propName not in cls.__reservedNames
        )
