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


class UnorderedList(list):
    """
    A list that contains elements that are logically considered unordered.
    The main difference between this and a `set` is that `set`s require
    their elements to be hashable. An `UnorderedList` does not.
    """

    def __eq__(self, other):
        if not isinstance(other, list):
            return False
        
        for item in self:
            if item not in other:
                return False
        
        return True
