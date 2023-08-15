from abc import ABC, abstractmethod
from typing import Iterable, Generator, Any, Generic, TypeVar

import sympy

from src.common.functions import first
from src.common.types import FormattedStr
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
    

class Relation:
    def __init__(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        self.leftExpr = leftExpr
        self.rightExpr = rightExpr
        # (leftExpr             = rightExpr)
        # (leftExpr - rightExpr = 0)
        self.asExprEqToZero = leftExpr - rightExpr # = 0

    def __repr__(self):
        return f"Relation({self.leftExpr}, {self.rightExpr})"

    def __eq__(self, other):
        if type(other) is not Relation:
            return False
        
        return self.leftExpr == other.leftExpr and self.rightExpr == other.rightExpr


class AlgebraSolver:
    def __init__(self):
        # a list of relational expressions with an implied equality to zero
        self._recordedRelations: list[Relation] = list()
        # a mapping of a variable to its potential values and conditions
        # (like b = 4 when a = 2 and b = 5 when a = -1)
        self._symbolValues: dict[sympy.Symbol, set[ConditionalValue[sympy.Atom]]] = dict()
        # the order in which symbols are substituted
        self._symbolResolutionOrder: list[tuple[int, sympy.Symbol]] = list()

    def recordRelation(self, relation: Relation):
        # TODO: use transactional data types that can be reversed more efficiently
        oldRelations = list(self._recordedRelations)
        oldSymbolValues = dict(self._symbolValues)
        oldResolutionOrder = list(self._symbolResolutionOrder)
        
        try:
            isRedundant = self._checkForRedundancies(relation)
            
            self._recordedRelations.append(relation)
            self._inferSymbolValuesFromRelations()
            return isRedundant
        
        except Exception as exception:
            self._recordedRelations = oldRelations
            self._symbolValues = oldSymbolValues
            self._symbolResolutionOrder = oldResolutionOrder
            raise exception

    def getSymbolValues(self, symbol: sympy.Symbol):
        return self._symbolValues.get(symbol)
    
    def getRelationsWithSymbol(self, symbol: sympy.Symbol):
        return [
            relation
            for relation in self._recordedRelations
            if symbol in relation.asExprEqToZero.free_symbols
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

    def _checkForRedundancies(self, relation: Relation):
        for conditionalSubbedRelationExpr in self._generateSubstitutionsFor(relation.asExprEqToZero):
            subbedRelationExpr = conditionalSubbedRelationExpr.value
            if subbedRelationExpr != 0:
                return False
        return True

    def _inferSymbolValuesFromRelations(self):
        anySymbolsUpdated = False
        for relation in self._recordedRelations:
            relationsWithKnownsSubbed = tuple(self._generateSubstitutionsFor(relation.asExprEqToZero))
            if not all(
                relationExprCondition.value == 0
                for relationExprCondition in relationsWithKnownsSubbed
                if len(relationExprCondition.value.free_symbols) == 0
            ):
                newestRelation = self._recordedRelations[-1]
                raise ContradictionException(tuple(), newestRelation)

            relationsWithSingleUnknown = (
                relationExprCondition
                for relationExprCondition in relationsWithKnownsSubbed
                if len(relationExprCondition.value.free_symbols) == 1
            )
            
            conditionalSolutionPairs = self._solveRelationExprsForSingleUnknown(relationsWithSingleUnknown)
            if __debug__:
                conditionalSolutionPairs = tuple(conditionalSolutionPairs)
                assert all(type(conditionalSolutionSet.value) is set for (symbol, conditionalSolutionSet) in conditionalSolutionPairs), \
                    "Solver got a solution set that wasn't a FiniteSet"
            
            (symbol, conditionalSolutions) = self._convertConditionalSolutionsToSetsOfConditions(conditionalSolutionPairs)
            someSubbedRelationWasSolvable = symbol is not None
            if someSubbedRelationWasSolvable:
                self._symbolValues[symbol] = conditionalSolutions
                self._insertSymbolToResolutionOrder(symbol, conditionalSolutions)
                anySymbolsUpdated = True
            
        if anySymbolsUpdated:
            self._inferSymbolValuesFromRelations()

    def _solveRelationExprsForSingleUnknown(self, relationExprConditions: Iterable[ConditionalValue[sympy.Expr]]) -> Generator[tuple[sympy.Symbol, ConditionalValue[sympy.Set]], Any, None]:
        for relationExprCondition in relationExprConditions:
            relationExpr = relationExprCondition.value
            assert(len(relationExpr.free_symbols) == 1), \
                "Relation had more than one unknown symbol to solve for"
            unknownSymbol = first(relationExpr.free_symbols)
            solution = sympy.solveset(relationExpr, unknownSymbol)
            solutionSet = self._interpretSympySolution(unknownSymbol, solution)
            yield (unknownSymbol, ConditionalValue(solutionSet, relationExprCondition.conditions))

    def _interpretSympySolution(self, symbol: sympy.Symbol, solution: sympy.Set):
        # normal solutions to problem
        # example:
        #   a^2 = 4; a = {2, -2}
        if type(solution) is sympy.FiniteSet:
            return set(solution)
        
        # solved such that no solutions are available
        # example:
        #   a/(b - 1) = 5; b = 1; a = {}
        elif solution is sympy.EmptySet:
            newestRelation = self._recordedRelations[-1]
            raise NoSolutionException([symbol], newestRelation)
        
        else:
            raise NotImplementedError(f"Solver reached unconsidered set: {type(solution).__name__}")

    def _convertConditionalSolutionsToSetsOfConditions(self, conditionalSolutionPairs: Iterable[tuple[sympy.Symbol, ConditionalValue[sympy.FiniteSet]]]):
        if __debug__:
            conditionalSolutionPairs = tuple(conditionalSolutionPairs)
            if len(conditionalSolutionPairs) > 0:
                symbolSolved = conditionalSolutionPairs[0][0]
                allSymbolsTheSame = all(symbol == symbolSolved for (symbol, conditionalValue) in conditionalSolutionPairs)
                assert allSymbolsTheSame, \
                    "Substitutions in relation led to different unknown variables"

        symbol = None
        totalSolutionSet: set[ConditionalValue[sympy.Atom]] = set()
        for (symbol, conditionalValueSet) in conditionalSolutionPairs:
            valueSet = conditionalValueSet.value
            conditions = conditionalValueSet.conditions
            for value in valueSet:
                # TODO: fix x*I cases (I = √-1)
                assert isinstance(value, sympy.Atom), \
                    "Solver makes false assumption that FiniteSets only contain Atoms"
                totalSolutionSet.add(ConditionalValue(value, conditions))
        return (symbol, totalSolutionSet)
    
    def _insertSymbolToResolutionOrder(self, symbol: sympy.Symbol, conditionalSolutions: set[ConditionalValue[sympy.Atom]]):
        assert symbol in self._symbolValues, "Should not insert symbol's resolution order before it has values"
        symbolSortRank = self._calculateSymbolResolutionRank(symbol)
        insertIdx = len(self._symbolResolutionOrder) + 1
        rankBeforeInsert = None
        while rankBeforeInsert is None or rankBeforeInsert > symbolSortRank:
            insertIdx -= 1
            if insertIdx == 0:
                break # I don't think this is even possible...
            (rankBeforeInsert, symbolBeforeInsert) = self._symbolResolutionOrder[insertIdx - 1]
        self._symbolResolutionOrder.insert(insertIdx, (symbolSortRank, symbol))

    def _calculateSymbolResolutionRank(self, symbol: sympy.Symbol):
        conditionSymbols = {
            symbol
            for conditionValue in self._symbolValues[symbol]
            for symbol in conditionValue.conditions.keys()
        }
        rank = 1 + sum(
            self._calculateSymbolResolutionRank(symbol)
            for symbol in conditionSymbols
        )
        return rank


    def _popSymbolFromResolutionOrder(self, symbol: sympy.Symbol):
        symbolIdx = [
            symbol
            for (rank, symbol) in self._symbolResolutionOrder
        ].index(symbol)
        return self._symbolResolutionOrder.pop(symbolIdx)

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


class BadRelationException(MultilineException, ABC):
    @abstractmethod
    def __init__(self, message: FormattedStr, poorSymbols: tuple[sympy.Symbol, ...], badRelation: Relation):
        self.poorSymbols = poorSymbols
        self.badRelation = badRelation
        
        leftExprFormatted = self.substitutePoorSymbols(badRelation.leftExpr, poorSymbols)
        rightExprFormatted = self.substitutePoorSymbols(badRelation.rightExpr, poorSymbols)
        super().__init__((
            message,
            f"[red]{leftExprFormatted} = {rightExprFormatted}[/red]",
        ))

    def formatPoorSymbols(self, poorSymbols: tuple[sympy.Symbol, ...]):
        return f"[yellow]{'[/yellow], [yellow]'.join(str(symbol) for symbol in poorSymbols)}[/yellow]"
    
    def substitutePoorSymbols(self, expr: sympy.Expr, poorSymbols: tuple[sympy.Symbol, ...]) -> sympy.Expr:
        return expr.subs({
            poorSymbol: sympy.Symbol(f"[yellow]{poorSymbol}[/yellow]")
            for poorSymbol in poorSymbols
        })

class ContradictionException(BadRelationException):
    def __init__(self, contradictedSymbols: tuple[sympy.Symbol, ...], badRelation: Relation):
        symbolsStr = f" for {self.formatPoorSymbols(contradictedSymbols)}" \
            if len(contradictedSymbols) > 0 else ""
        super().__init__(
            f"Relation contradicts known/inferred values{symbolsStr}",
            contradictedSymbols,
            badRelation
        )

class NoSolutionException(BadRelationException):
    def __init__(self, symbolsMissingSolutions: tuple[sympy.Symbol, ...], badRelation: Relation):
        symbolsStr = f" for {self.formatPoorSymbols(symbolsMissingSolutions)}" \
            if len(symbolsMissingSolutions) > 0 else ""
        super().__init__(
            f"Relation leads to unsolvable state{symbolsStr}",
            symbolsMissingSolutions,
            badRelation
        )
