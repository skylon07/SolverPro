from typing import Iterable, Generator, Any, Union, Generic, TypeVar

import sympy

from src.common.functions import first, iterDifference
from src.common.exceptions import MultilineException

_ValueType = TypeVar("_ValueType")
class ConditionalValue(Generic[_ValueType]):
    def __init__(self, value: _ValueType, conditions: dict[sympy.Symbol, sympy.Atom]):
        self.value = value
        self.conditions = conditions

    def __repr__(self):
        return f"ConditionalValue({self.value}, {self.conditions})"
    
    def __hash__(self):
        conditionsHash = 1
        for (symbol, value) in self.conditions.items():
            conditionsHash *= symbol - value
        return hash((self.value, conditionsHash))

    def __eq__(self, other):
        if type(other) is not ConditionalValue:
            return False
        
        return self.value == other.value and self.conditions == other.conditions


class AlgebraSolver:
    def __init__(self):
        # a list of relational expressions with an implied equality to zero
        self._recordedRelations: list[sympy.Expr] = list()
        # a mapping of a variable to its potential values and conditions
        # (like b = 4 when a = 2 and b = 5 when a = -1)
        self._symbolValues: dict[sympy.Symbol, set[ConditionalValue[sympy.Atom]]] = dict()
        # the order in which symbols are substituted
        self._symbolResolutionOrder: list[tuple[int, sympy.Symbol]] = list()

    def recordRelation(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        newRelation = self.toRelation(leftExpr, rightExpr)
        (isContradictory, isRedundant) = self._checkForContradictions(newRelation)
        if isContradictory:
            raise ContradictionException(newRelation)
        self._recordedRelations.append(newRelation)
        self._inferSymbolValuesFromRelations()
        return (newRelation, isRedundant)

    def toRelation(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        # relation << (leftExpr             == rightExpr)
        # relation << (leftExpr - rightExpr == 0)
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
    
    def substituteKnownsFor(self, expression: sympy.Expr):
        conditionals = self._generateSubstitutionsFor(expression)
        values = {
            conditional.value
            for conditional in conditionals
        }
        return values
    
    def substituteKnownsWithConditions(self, expression: sympy.Expr):
        conditionals = self._generateSubstitutionsFor(expression)
        return set(conditionals)
    
    def _generateSubstitutionsFor(self, expression: sympy.Expr) -> Generator[ConditionalValue[sympy.Expr], Any, None]:
        for symbolValueCombination in self._generateSubstitutionCombinations():
            conditions = {
                symbol: conditionalValue
                for (symbol, conditionalValue) in symbolValueCombination.items()
                if symbol in expression.free_symbols
            }
            subExpr = expression.subs(symbolValueCombination)
            yield ConditionalValue(subExpr, conditions)

    def _checkForContradictions(self, relation: sympy.Expr):
        relationIsContradictory = False
        relationIsRedundant = False
        for conditionalSubbedRelation in self._generateSubstitutionsFor(relation):
            subbedRelation = conditionalSubbedRelation.value
            if len(subbedRelation.free_symbols) == 0:
                if subbedRelation == 0:
                    relationIsRedundant = True
                else:
                    relationIsContradictory = True
        return (relationIsContradictory, relationIsRedundant)

    def _inferSymbolValuesFromRelations(self):
        anySymbolsUpdated = False
        for relationExpr in self._recordedRelations:
            relationConditionsWithKnownsSubbed = self._generateSubstitutionsFor(relationExpr)
            if __debug__:
                relationConditionsWithKnownsSubbed = tuple(relationConditionsWithKnownsSubbed)
                assert all(
                    relationCondition.value == 0
                    for relationCondition in relationConditionsWithKnownsSubbed
                    if len(relationCondition.value.free_symbols) == 0
                ), "Every (completely known) relation should be exactly equal to zero (are there contradictions between stored relations?)"

            relationConditionsWithSingleUnknown = (
                relationCondition
                for relationCondition in relationConditionsWithKnownsSubbed
                if len(relationCondition.value.free_symbols) == 1
            )
            
            conditionalValueSets = self._solveRelationsForSingleUnknown(relationConditionsWithSingleUnknown)
            if __debug__:
                conditionalValueSets = tuple(conditionalValueSets)
                assert all(type(conditionalSet.value) is sympy.FiniteSet for (symbol, conditionalSet) in conditionalValueSets), \
                    "Solver got a solution set that wasn't a FiniteSet"
            
            (symbol, conditionalSolutionSet) = self._convertConditionalSetsToSetsOfConditions(conditionalValueSets)
            someSubbedRelationWasSolvable = symbol is not None
            if someSubbedRelationWasSolvable:
                self._symbolValues[symbol] = conditionalSolutionSet
                self._insertSymbolToResolutionOrder(symbol, conditionalSolutionSet)
                anySymbolsUpdated = True
            
        if anySymbolsUpdated:
            self._inferSymbolValuesFromRelations()

    def _solveRelationsForSingleUnknown(self, relationConditions: Iterable[ConditionalValue[sympy.Expr]]) -> Generator[tuple[sympy.Symbol, ConditionalValue[sympy.Set]], Any, None]:
        for relationCondition in relationConditions:
            relation = relationCondition.value
            assert(len(relation.free_symbols) == 1), \
                "Relation had more than one unknown symbol to solve for"
            unknownSymbol = first(relation.free_symbols)
            solutionSet = sympy.solveset(relation, unknownSymbol)
            yield (unknownSymbol, ConditionalValue(solutionSet, relationCondition.conditions))

    def _convertConditionalSetsToSetsOfConditions(self, conditionalValueSets: Iterable[tuple[sympy.Symbol, ConditionalValue[sympy.FiniteSet]]]):
        if __debug__:
            conditionalValueSets = tuple(conditionalValueSets)
            if len(conditionalValueSets) > 0:
                symbolSolved = conditionalValueSets[0][0]
                allSymbolsTheSame = all(symbol == symbolSolved for (symbol, conditionalValue) in conditionalValueSets)
                assert allSymbolsTheSame, \
                    "Substitutions in relation led to different unknown variables"

        symbol = None
        totalSolutionSet: set[ConditionalValue[sympy.Atom]] = set()
        for (symbol, conditionalValueSet) in conditionalValueSets:
            valueSet = conditionalValueSet.value
            conditions = conditionalValueSet.conditions
            for value in valueSet:
                assert isinstance(value, sympy.Atom), \
                    "Solver makes false assumption that FiniteSets only contain Atoms"
                totalSolutionSet.add(ConditionalValue(value, conditions))
        return (symbol, totalSolutionSet)
    
    def _insertSymbolToResolutionOrder(self, symbol: sympy.Symbol, conditionalSolutions: set[ConditionalValue[sympy.Atom]]):
        symbolSortRank = max(len(conditional.conditions) for conditional in conditionalSolutions)
        insertIdx = -1
        insertRank = None
        while insertRank is None or insertRank < symbolSortRank:
            insertIdx += 1
            if insertIdx == len(self._symbolResolutionOrder):
                break
            (rankAtInsert, symbolAtInsert) = self._symbolResolutionOrder[insertIdx]
        self._symbolResolutionOrder.insert(insertIdx, (symbolSortRank, symbol))

    def _generateSubstitutionCombinations(self, currCombination: dict[sympy.Symbol, sympy.Atom] = None, resolutionIdx = 0) -> Generator[dict[sympy.Symbol, sympy.Atom], Any, None]:
        if currCombination is None:
            currCombination = dict()
        
        noSymbolsLeftToInclude = resolutionIdx == len(self._symbolResolutionOrder)
        if noSymbolsLeftToInclude:
            # copied to avoid the side-effects of changing currCombination
            finishedCombination = dict(currCombination)
            yield finishedCombination
        
        else:
            (symbolRank, symbolToInclude) = self._symbolResolutionOrder[resolutionIdx]
            anyConditionsMet = False
            for conditionalValue in self._symbolValues[symbolToInclude]:
                if self._testConditionsMet(conditionalValue, currCombination):
                    anyConditionsMet = True
                    # overwritten to save on memory (instead of copying and creating a bunch of dicts)
                    currCombination[symbolToInclude] = conditionalValue.value
                    for finishedCombination in self._generateSubstitutionCombinations(currCombination, resolutionIdx + 1):
                        yield finishedCombination
            assert anyConditionsMet, "Solver failed to find a valid condition"

    def _testConditionsMet(self, conditionalValue: ConditionalValue[Any], currCombination: dict[sympy.Symbol, sympy.Atom]):
        for (symbol, value) in conditionalValue.conditions.items():
            if currCombination[symbol] != value:
                return False
        return True


class ContradictionException(MultilineException):
    def __init__(self, badRelation: sympy.Expr):
        super().__init__((
            "Relation contradicts known values",
            f"[red]{badRelation}[/red]",
        ))
