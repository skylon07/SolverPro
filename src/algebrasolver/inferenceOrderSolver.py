import sympy

from src.parsing.parser import freeSymbolsOf
from src.algebrasolver.symbolsDatabase import SymbolsDatabase
from src.algebrasolver.relationSymbolTable import RelationSymbolTable
from src.algebrasolver.types import *


class InferenceOrderSolver:
    def __init__(self, relations: list[Relation], knownSymbols: SymbolsDatabase):
        self._relations = relations
        self._knownSymbols = knownSymbols
        self._potentialInferencesTable = RelationSymbolTable()

    def findSolveOrder(self):
        symbolCounts = self._countSymbols()
        # relations must be sorted to prevent "trapping" a variable from being known:
        # a + b + c + d = 123
        # a + b + d = 234
        # a + b - d = 432
        # c = 8
        # in the above, `c` is chosen for the first relation (since it has the
        # lowest count), however this "traps" it since it won't be chosen for the
        # last relation, which actually provides its value
        assert self._testRelationsSorted(), "Relations for inference solver must be sorted!"
        for relation in self._relations:
            unknownSymbolsInRelation: list[tuple[sympy.Symbol, int]] = [
                (symbol, symbolCounts[symbol])
                for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False)
                if symbol not in self._knownSymbols and symbol not in self._potentialInferencesTable
            ]

            (symbolToSolve, symbolCount) = min(
                unknownSymbolsInRelation,
                key = lambda symbolAndCount: symbolAndCount[1],
                default = (None, None)
            )
            if symbolToSolve is not None:
                self._potentialInferencesTable[symbolToSolve] = relation

                # optimization: inference family cannot be solid unless this relation
                # has potential inferences for all of its symbols
                wasLastUnknownSymbol = len(unknownSymbolsInRelation) == 1
                if wasLastUnknownSymbol:
                    (canBackSubstitute, symbolsInFamily) = self._testSolidInferenceFamily(relation)
                    if canBackSubstitute:
                        return sorted(
                            [
                                (symbolToInfer, relationToInferFrom)
                                for symbolToInfer in symbolsInFamily
                                for relationToInferFrom in [self._potentialInferencesTable[symbolToInfer]]
                            ],
                            key = lambda data: len(freeSymbolsOf(data[1].asExprEqToZero, includeExpressionLists = False))
                        )
        return None
    
    def _testSolidInferenceFamily(self, baseRelation: Relation, relationsChecked: set[Relation] | None = None, symbolsInFamily: set[sympy.Symbol] | None = None):
        if relationsChecked is None:
            relationsChecked = {baseRelation}
        if symbolsInFamily is None:
            symbolsInFamily = set()

        for symbol in freeSymbolsOf(baseRelation.asExprEqToZero, includeExpressionLists = False):
            if symbol in self._potentialInferencesTable:
                symbolsInFamily.add(symbol)
                relation = self._potentialInferencesTable[symbol]
                if relation not in relationsChecked:
                    relationsChecked.add(relation)
                    (isSolid, symbolsInFamily_extraRef) = self._testSolidInferenceFamily(relation, relationsChecked, symbolsInFamily)
                    holeExists = not isSolid
                    if holeExists:
                        return (False, symbolsInFamily)
            elif symbol not in self._knownSymbols:
                return (False, symbolsInFamily)
        return (True, symbolsInFamily)

    def _countSymbols(self):
        unknownSymbolCounts: dict[sympy.Symbol, int] = dict()
        for relation in self._relations:
            for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False):
                if symbol in unknownSymbolCounts:
                    unknownSymbolCounts[symbol] += 1
                elif symbol not in self._knownSymbols:
                    unknownSymbolCounts[symbol] = 1
        return unknownSymbolCounts
    
    def _testRelationsSorted(self):
        lastNumSymbols = -1
        for relation in self._relations:
            numSymbols = len(freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False))
            if numSymbols < lastNumSymbols:
                return False
            lastNumSymbols = numSymbols
        return True


