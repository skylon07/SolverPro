import sympy

from src.algebramaster.structures import *


(a, b) = sympy.symbols("a, b")


class SubDictTester:
    def testSubDictCanEqualDict(self):
        origDict = {a: 2, b: 5}
        subDict = SubDict(origDict)
        
        assert subDict == origDict

class SubDictListTester:
    def testSubDictListCanEqualListOfDicts(self):
        origList = [{a: 2, b: 5}, {a: -2, b: -5}]
        subDictList = SubDictList([SubDict(origDict) for origDict in origList])

        assert subDictList == origList
