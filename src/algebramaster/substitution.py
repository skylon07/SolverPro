import sympy

from .structures import *


def substituteAllKnowns(expr, subDicts):
    """
    if
    ```
    expr = a + b + 2
    subDictList = [{a: 4, b: a}, {b: c + 1}]
    ```
    then
    ```
    result = [10, a + c + 3]
    ```
    """

    subDictList = _convertToSubDictList(subDicts)
    _assertSubDictList(subDictList)
    
    try:
        if isNumeric(expr):
            return [expr]
    except ValueError as error:
        if "could not convert" in str(error):
            _assertSympyExpr(expr)
        else:
            raise error
    _assertSympyExpr(expr)

    # TODO: should probably refactor all of these functions to not use lists
    #       when only subbing one dict (aka _convertToSubDictList() is bad)
    finalList = SubDictList.fromList(
        ({expr: _subDictUntilFixed(expr, subDict)}, subDict.conditions)
        for subDict in subDictList
    )
    
    # SubDicts (expr --> subbedExpr) are returned to carry the conditions
    # of the substitution
    if type(subDicts) is SubDict:
        return finalList[0]
    else:
        return finalList

def substituteToNumerics(expr, subDicts):
    """
    if
    ```
    expr = a + b + 2
    subDictList = [{a: 4, b: 3}, {b: 5}]
    ```
    then
    ```
    result = [9, a + 7]
    ```
    """

    subDictList = _convertToSubDictList(subDicts)
    _assertSubDictList(subDictList)
    assert all(isNumeric(val) for subDict in subDictList for val in subDict.values()), "substituteToNumerics() sub dicts' values must be numerics"

    return substituteAllKnowns(expr, subDictList)

def forwardSubstituteByElimination(expr, subDicts, forSymbol):
    """
    if
    ```
    expr = a + b + c + 2
    subDictList = [{a: b - c, b: c + 2}, ...]
    forSymbol = c
    ```
    then
    ```
    result = [c + 4, ...]
    ```
    """

    subDictList = _convertToSubDictList(subDicts)
    _assertSubDictList(subDictList)
    
    result = substituteAllKnowns(expr, subDictList)
    if __debug__:
        if type(result) is SubDict:
            resultList = SubDictList.fromList([result])
        else:
            resultList = result
        
        allSymbols = {
            symbol
            for subDict in subDictList
            for subDictExprKey in subDict.keys()
            for symbol in subDictExprKey.free_symbols
        }
        resultExprs = [
            resultExpr
            for resultDict in resultList
            for resultExpr in [resultDict[expr]]
        ]
        assert not any(symbol in resultExpr.free_symbols for resultExpr in resultExprs for symbol in allSymbols), "subDict should have expression keys with unidirectional dependencies to eliminate all symbols (can't have {a: b + c, b: a * c} or {a + b: b + 1}, but CAN have {a: b + c, b: 2 * c})"
        assert all(forSymbol in resultExpr.free_symbols for resultExpr in resultExprs), "subDict should resolve to expressions containing the wanted symbol"
    return result

def backSubstituteByInference(subDicts, forSymbol):
    """
    if
    ```
    subDictList = [{a: b - c + d, b: c + 2, c: 1}, ...]
    forSymbol = a
    ```
    then
    ```
    result = [d + 2, ...]
    ```
    """
    
    subDictList = _convertToSubDictList(subDicts)
    _assertSubDictList(subDictList)
    _assertSympySymbol(forSymbol)
    assert all(forSymbol in subDict for subDict in subDictList), "Substitutions for `forSymbol` should be given in all subDicts"

    finalList = substituteAllKnowns(forSymbol, subDictList)

    # SubDicts (expr --> subbedExpr) are returned to carry the conditions
    # of the substitution
    if type(subDicts) is SubDict:
        return finalList[0]
    else:
        return finalList
    

def _subDictUntilFixed(expr: sympy.Expr, subDict):
    lastExpr = None
    iters = 0
    while lastExpr is not expr:
        lastExpr = expr
        expr = expr.subs(subDict)
        iters += 1
        assert iters < 9999, "Substitution probably should have stopped by now..."
    return expr


def _convertToSubDictList(subDicts):
    if type(subDicts) is SubDict:
        subDict = subDicts
        return SubDictList.fromList([subDict])
    elif type(subDicts) is SubDictList:
        return subDicts
    else:
        raise TypeError("Substitution argument must be a SubDict or a SubDictList")
    

def _assertSubDictList(subDictList):
    assert type(subDictList) is SubDictList, "subDictList should be a SubDictList"

def _assertSympyExpr(expr):
    assert isinstance(expr, sympy.Expr), "expr should be a sympy.Expr"

def _assertSympySymbol(symbol):
    assert type(symbol) is sympy.Symbol, "symbol should be a sympy.Symbol"
