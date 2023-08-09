from typing import Iterable, Generator, Any

import sympy

from src.common.functions import first, iterDifference


class AlgebraSolver:
    def __init__(self):
        # a list of relational expressions with an implied equality to zero
        self._recordedRelations: list[sympy.Expr] = list()
        # a mapping of a variable to its potential values (like var = ±2)
        self._symbolValues: dict[sympy.Symbol, sympy.FiniteSet] = dict()

    def recordRelation(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        # TODO: check for contradictions
        self._recordedRelations.append(self.toRelation(leftExpr, rightExpr))
        self._inferSymbolValuesFromRelations()

    def toRelation(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        # relation = leftExpr == rightExpr
        relation = leftExpr - rightExpr # == 0
        return relation

    def getSymbolValues(self, symbol: sympy.Symbol):
        return self._symbolValues.get(symbol)
    
    def getRelationsWithSymbol(self, symbol: sympy.Symbol):
        return [
            relation
            for relation in self._recordedRelations
            if symbol in relation.free_symbols
        ]
    
    def substituteKnownsFor(self, expression: sympy.Expr) -> Generator[sympy.Expr, Any, None]:
        return {
            expression.subs(symbolValueCombination)
            for symbolValueCombination in self._generateSymbolValueCombinations()
        }

    def _inferSymbolValuesFromRelations(self):
        anySymbolsUpdated = False
        for relationExpr in self._recordedRelations:
            relationListOfSubbedKnowns = self.substituteKnownsFor(relationExpr)
            relationsWithSingleUnknown = (
                relation
                for relation in relationListOfSubbedKnowns
                if len(relation.free_symbols) == 1
            )
            symbolValuePairs = self._solveRelationsForSingleUnknown(relationsWithSingleUnknown)
            (symbol, solutionSet) = self._condenseSymbolValuePairs(symbolValuePairs)
            if symbol is not None:
                self._symbolValues[symbol] = solutionSet
                anySymbolsUpdated = True
            
        if anySymbolsUpdated:
            self._inferSymbolValuesFromRelations()

    def _solveRelationsForSingleUnknown(self, relations: Iterable[sympy.Expr]):
        for relation in relations:
            assert(len(relation.free_symbols) == 1), \
                "Relation had more than one unknown symbol to solve for"
            unknownSymbol = first(relation.free_symbols)
            solutionSet = sympy.solveset(relation, unknownSymbol)
            yield (unknownSymbol, solutionSet)

    def _condenseSymbolValuePairs(self, symbolValuePairs: Iterable[tuple[sympy.Symbol, sympy.FiniteSet]]):
        if __debug__:
            symbolValuePairs = tuple(symbolValuePairs)
            if len(symbolValuePairs) > 0:
                symbolSolved = symbolValuePairs[0][0]
                allSymbolsTheSame = all(symbol == symbolSolved for (symbol, value) in symbolValuePairs)
                assert allSymbolsTheSame, \
                    "Substitutions in relation led to different unknown variables"

        symbol = None
        totalSolutionSet = sympy.FiniteSet()
        for (symbol, solutionSet) in symbolValuePairs:
            totalSolutionSet += solutionSet
        return (symbol, totalSolutionSet)      

    def _generateSymbolValueCombinations(self, currSymbolValueCombination: dict[sympy.Symbol, sympy.Basic] = None) -> Generator[dict[sympy.Symbol, sympy.Basic], Any, None]:
        if currSymbolValueCombination is None:
            currSymbolValueCombination = dict()

        symbolToInclude = first(iterDifference(self._symbolValues, currSymbolValueCombination), None)
        noSymbolsLeftToInclude = symbolToInclude is None
        if noSymbolsLeftToInclude:
            finishedCombination = currSymbolValueCombination
            yield finishedCombination
        else:
            for currValue in self._symbolValues[symbolToInclude]:
                # overwritten to save on memory (instead of copying and creating a bunch of dicts)
                currSymbolValueCombination[symbolToInclude] = currValue
                for finishedCombination in self._generateSymbolValueCombinations(currSymbolValueCombination):
                    yield finishedCombination
                # have to pop to allow re-including in repeated calls from parent
                # (aka have to pop so iterDifference() doesn't ignore it thinking it's already handled)
                currSymbolValueCombination.pop(symbolToInclude)
