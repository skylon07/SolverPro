from typing import Generator, Any

import sympy

from src.parsing.parser import freeSymbolsOf, isExpressionListSymbol
from src.common.sympyLinterFixes import subsExpr
from src.algebrasolver.symbolsDatabase import SymbolsDatabase
from src.algebrasolver.types import *


class CombinationsSubstituter:
    """
    This class creates a single-use substituter object which is tasked with
    substituting a set of expressions with some mapping of known values.
    Because of the computational labor involved with performing a substitution,
    it is possible to substitute multiple expressions with the same mapping at
    once, yielding results faster than creating a substituter for each
    expression individually.

    Substitution in Solver Pro is not as trivial a task as it might seem at
    first glance. Because it is possible for relations to be true under multiple
    conditions, the substitution algorithm must take into account that a single
    variable can simultaneously represent multiple values.

    This simple fact defines the overall signature of this substituter:
    Put an expression in, get multiple expressions out. Because `sympy` does not
    have any built-in functionality that allows symbols to be substituted with
    multiple values at a time, this class provides a conversion of the
    "one --> many" substitution we need in terms of "one --> one" substitutions.
    This work is done by `_generateCombinations()`, whose job is to iterate
    through all the possible `symbol: value` combinations given the
    `symbol: valueSet` pairs we started with.

    However, this task is not as simple as just substituting all the
    combinations of the variables' values. Consider this example:

    ```raw
    a^2 = 16
    b = a/2
    (a = {-4, 4})
    (b = {-2, 2})
    ```

    What would happen if we substituted the expression `a + b` in this way?
    The combinations are:

    ```raw
    {a: -4, b: -2}
    {a: -4, b:  2}
    {a:  4, b: -2}
    {a:  4, b:  2}
    ```

    which would yield the (incorrect) results:
    
    ```raw
    -4 + -2 = -6
    -4 +  2 = -2
     4 + -2 =  2
     4 +  2 =  6
    ```

    The values `-2` and `2` are impossible solutions to our original relations.
    It is not true for `b = a/2` that `(2) = (-4)/2`, nor `(-2) = (4)/2`. This
    is because our solution to `b` *depends* on the values of `a`. These
    "dependencies" must be taken into account for the substitution algorithm
    to work. In this case, this is done by using `ConditionalValue` objects.
    Once these objects are considered and respected, the substitution of `a + b`
    yields only `-6` and `6`. This process is described in more detail in the
    documentation for `_generateCombinations()`.
    """

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
        """Initiates the substitution and yields the resulting expressions"""

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
        """
        Initiates the substitution and returns a dictionary mapping given
        expressions to their substituted ones
        """

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
        """
        `sympy` expressions do not recursively perform substitutions when
        given a dictionary. It seems the intention behind `Expr.subs()` was
        that each substitution could either be performed one at a time, or all
        would be performed once simultaneously.

        ```raw
        (a + b).subs({
            a: 4,
            b: a - 1,
        }) == ((4) + (a - 1))
        ```
        
        This is not the behavior we want. The desired result is

        ```raw
        (a + b).subs({
            a: 4,
            b: a - 1,
        }) == ((4) + (a - 1)).subs({...})
           == ( 4  + (4)- 1 )
           == 7
        ```

        This function performs exactly this operation; that is, "keep
        substituting until the expression doesn't change anymore."
        """

        lastExpression = None
        while lastExpression != expression:
            lastExpression = expression
            expression = subsExpr(expression, combination)
        return expression
    
    def _generateCombinations(self, numExprListsResolved, resolutionIdx):
        """
        This function is the main workhorse for the substitution algorithm.
        It generates combinations of single values for variables by recursive
        generation (that is, it is a generator that calls itself recursively,
        where each call will iterate over the values of one variable).

        As described above in the main class docs, it is important to keep track
        of the "dependencies", or "conditions" each variable depends on, when
        performing the substitution. This is done by essentially filtering the
        results by `_testConditionsMet()`; If the conditions are not currently
        met, it is not a valid combination, and is simply ignored.

        It is important to resolve variables in the order they depend in
        ("resolve" meaning "add them to the resulting subs dict"). If `b` was
        inferred by values known for `a`, then each of `a`'s values should be
        resolved before `b`'s. This function assumes that this
        `_resolutionOrder` is known upon construction of the substituter.

        Expression lists (aka the symbols used to represent multiple values,
        like `Symbol("{1,2,3}")`) are treated with the highest priority, since
        their values do not depend on anything else, and are resolved before
        the other symbols listed in the `_resolutionOrder`.
        """

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
        """
        This tests the current "combination" dictionary with a given conditional
        value. The test will past if all the current values in the combination
        satisfy the conditions in the conditional value. (This assumes that all
        the necessary variables are already included in the combination
        dictionary *before* performing this test, something that should be
        guaranteed by utilizing a valid `_resolutionOrder`.)
        """
        
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


