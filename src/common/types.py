from abc import ABC as AbstractClass, abstractmethod


class Displayable(AbstractClass):
    @abstractmethod
    def __repr__(self):
        return  # a string representation of this object


class Hashable(AbstractClass):    
    @abstractmethod
    def __hash__(self):
        return # a unique integer for this instance

    @abstractmethod
    def __eq__(self, other):
        return # if self is equal to other


class Comparable(AbstractClass):
    @abstractmethod
    def __lt__(self, other):
        return # if self is less than other

    @abstractmethod
    def __eq__(self, other):
        return # if self is equal to other

