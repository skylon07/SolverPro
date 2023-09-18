from typing import Generator, Any

import sympy

from src.parsing.parser import freeSymbolsOf, isExpressionListSymbol
from src.common.sympyLinterFixes import subsExpr
from src.algebrasolver.symbolsDatabase import SymbolsDatabase
from src.algebrasolver.types import *


class CombinationsSubstituter:
    def __init__(self, expressions: set[sympy.Expr], database: SymbolsDatabase, *, restrictRedefSymbol: sympy.Symbol | None = None):
        self._expressions = expressions
        self._symbolValuesDatabase = database
        self._currCombination: dict[sympy.Symbol, sympy.Expr] = dict()
        self._resolutionOrder = tuple(database)
        self._exprListSymbols = tuple(
            exprListSymbol
            for expression in expressions
            for exprListSymbol in freeSymbolsOf(expression)
            if isExpressionListSymbol(exprListSymbol)
        )
        self._restrictRedefSymbol = restrictRedefSymbol

    def substitute(self) -> Generator[ConditionalValue[sympy.Expr], Any, None]:
        for symbolValueCombination in self._generateCombinations(0, 0):
            for expression in self._expressions:
                conditions = {
                    symbol: conditionalValue
                    for (symbol, conditionalValue) in symbolValueCombination.items()
                    if symbol in freeSymbolsOf(expression)
                }
                subExpr = self._subsUntilFixed(expression, symbolValueCombination)
                yield ConditionalValue(subExpr, conditions)
    
    def substituteForMapping(self) -> dict[sympy.Expr, set[ConditionalValue[sympy.Expr]]]:
        result: dict[sympy.Expr, set[ConditionalValue[sympy.Expr]]] = dict()
        for (expression, conditionalValue) in self._substituteForMapPairs():
            valueSet = result.get(expression, set())
            valueSet.add(conditionalValue)
            result[expression] = valueSet
        return result

    def _substituteForMapPairs(self) -> Generator[tuple[sympy.Expr, ConditionalValue[sympy.Expr]], Any, None]:
        for symbolValueCombination in self._generateCombinations(0, 0):
            for expression in self._expressions:
                conditions = {
                    symbol: conditionalValue
                    for (symbol, conditionalValue) in symbolValueCombination.items()
                    if symbol in freeSymbolsOf(expression)
                }
                subExpr = self._subsUntilFixed(expression, symbolValueCombination)
                yield (expression, ConditionalValue(subExpr, conditions))

    def _subsUntilFixed(self, expression: sympy.Expr, combination: dict[sympy.Symbol, sympy.Expr]):
        lastExpression = None
        while lastExpression != expression:
            lastExpression = expression
            expression = subsExpr(expression, combination)
        return expression
    
    def _generateCombinations(self, numExprListsResolved, resolutionIdx):
        noExprListsLeft = numExprListsResolved == len(self._exprListSymbols)
        if noExprListsLeft:
            noSymbolsLeftToInclude = resolutionIdx == len(self._resolutionOrder)
            if noSymbolsLeftToInclude:
                # copied to avoid the side-effects of changing currCombination across iterations
                finishedCombination = dict(self._currCombination)
                yield finishedCombination
                return
            
            else:
                symbolToInclude = self._resolutionOrder[resolutionIdx]
                resolutionIdx += 1
        else:
            symbolToInclude = self._exprListSymbols[numExprListsResolved]
            numExprListsResolved += 1
        for conditionalValue in self._symbolValuesDatabase[symbolToInclude]:
            if self._testConditionsMet(conditionalValue):
                # overwritten to save on memory (instead of copying and creating a bunch of dicts)
                self._currCombination[symbolToInclude] = conditionalValue.value
                yield from self._generateCombinations(numExprListsResolved, resolutionIdx)

    def _testConditionsMet(self, conditionalValue: ConditionalValue[Any]):
        for (symbol, value) in conditionalValue.conditions.items():
            if isExpressionListSymbol(symbol):
                # expression list symbols from the expression are resolved first;
                # if we're testing a condition based on it, and it isn't in the
                # combination, it therefore isn't in the expression and can't lead
                # to contradictions during substitution
                conditionIsIrrelevant = symbol not in self._currCombination
                if conditionIsIrrelevant:
                    continue 
            if symbol not in self._currCombination:
                # we just pretend the conditions match; the contradiction checking will be done later
                assert self._restrictRedefSymbol == symbol, "Symbol was expected to be in combination but was missing (and wasn't a redefinition case)"
            elif self._currCombination[symbol] != value:
                return False
        return True


