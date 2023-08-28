from abc import ABC, abstractmethod
from typing import Iterable, Collection, Generator, Any, Generic, TypeVar

import sympy

from src.common.functions import first, surroundJoin
from src.common.types import FormattedStr
from src.common.exceptions import MultilineException
from src.parsing.lexer import CommandLexer
from src.parsing.parser import CommandParser, isExpressionListSymbol, isNonSymbolicValue


SolutionSet = set[sympy.Expr]


_ValueType = TypeVar("_ValueType")
class ConditionalValue(Generic[_ValueType]):
    def __init__(self, value: _ValueType, conditions: dict[sympy.Symbol, sympy.Expr]):
        self.value = value
        self.conditions = conditions

    def __repr__(self):
        return f"ConditionalValue({self.value}, {self.conditions})"
    
    def __hash__(self):
        conditionsHash = 1
        for (symbol, value) in self.conditions.items():
            conditionsHash *= symbol - value # type: ignore
        return hash((self.value, conditionsHash))

    def __eq__(self, other):
        if type(other) is not ConditionalValue:
            return False
        
        return self.value == other.value and self.conditions == other.conditions
    

class Relation:
    def __init__(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        if not isinstance(leftExpr, sympy.Expr) and type(leftExpr) in (int, float):
            leftExpr = sympy.parse_expr(str(leftExpr))
        if not isinstance(rightExpr, sympy.Expr) and type(rightExpr) in (int, float):
            rightExpr = sympy.parse_expr(str(rightExpr))
        
        self.leftExpr = leftExpr
        self.rightExpr = rightExpr
        # (leftExpr             = rightExpr)
        # (leftExpr - rightExpr = 0)
        self.asExprEqToZero = leftExpr - rightExpr # = 0    # type: ignore

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
        self._database = _SymbolsDatabase()

    def recordRelation(self, relation: Relation):
        # TODO: use transactional data types that can be reversed more efficiently
        oldRelations = list(self._recordedRelations)
        oldDatabase = self._database.copy()
        
        # if there is a contradiction, it would be with these
        contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None] = {
            symbol: {
                conditional.value
                for conditional in self._database[symbol]
            }
            for symbol in relation.asExprEqToZero.free_symbols
            if symbol in self._database and not isExpressionListSymbol(symbol)
        }
        try:
            (isRedundant, isRedundantWithContradictions) = self._checkForRedundancies(relation)
            if isRedundantWithContradictions:
                # a restricted redefinition case is when a relation is
                # restricting what some variable's values are
                # example: if `a` is already known, {-4, 2, 5}, and a new
                # relation `a = 2` comes in, this is "redundant" (aka no new
                # information about other variables) but also contradictory
                # (because -4 ≠ 2 and 5 ≠ 2); this is a clear indication that
                # the variable's values should be restricted
                couldBeRestrictRedefCase = len(relation.asExprEqToZero.free_symbols) == 1
                if couldBeRestrictRedefCase:
                    symbol = first(relation.asExprEqToZero.free_symbols)
                    assert type(symbol) is sympy.Symbol
                    oldSolutions = self._database.pop(symbol)
                    
                    try:
                        (newSymbol, newSolutions) = self._calculateAnySolutionsFromRelation(relation, dict())
                    except ContradictionException:
                        # shouldn't be possible... but just in case!
                        raise RuntimeError("A contradiction was realized during restriction calculation (no new relations added...?)")
                    assert symbol == newSymbol, "Restriction solutions don't match found symbol" # this shouldn't be possible either!
                    if symbol is not None:
                        oldSolutionValues = tuple(solution.value for solution in oldSolutions)
                        newValuesAreRestrictions = len(newSolutions) < len(oldSolutions) and \
                            all(solution.value in oldSolutionValues for solution in newSolutions)
                        if newValuesAreRestrictions:
                            self._database[symbol] = newSolutions
                            isRedundant = False # since it technically did provide new information...
                            # TODO: (optimization) remove other symbol values that relied on any conditions now not present
                            #       (since other symbols might have conditions that will never be true when substituted,
                            #       due to the values that were just removed)
                        else:
                            self._database[symbol] = oldSolutions
            
            self._recordedRelations.append(relation)
            self._inferSymbolValuesFromRelations(contradictedSymbolValues)
            return isRedundant
        
        except Exception as exception:
            self._recordedRelations = oldRelations
            self._database = oldDatabase
            raise exception

    def getSymbolConditionalValues(self, symbol: sympy.Symbol):
        return self._database.get(symbol)
    
    def getRelationsWithSymbol(self, symbol: sympy.Symbol):
        return tuple(
            relation
            for relation in self._recordedRelations
            if symbol in relation.asExprEqToZero.free_symbols
        )
    
    def substituteKnownsFor(self, expression: sympy.Expr):
        conditionals = _CombinationsSubstituter(expression, self._database)
        values = {
            conditional.value
            for conditional in conditionals
        }
        return values
    
    def substituteKnownsWithConditions(self, expression: sympy.Expr):
        conditionals = _CombinationsSubstituter(expression, self._database)
        return set(conditionals)

    def _checkForRedundancies(self, relation: Relation):
        isRedundantWithContradictions = False
        for conditionalSubbedRelationExpr in _CombinationsSubstituter(relation.asExprEqToZero, self._database):
            subbedRelationExpr = conditionalSubbedRelationExpr.value
            if subbedRelationExpr != 0:
                if len(subbedRelationExpr.free_symbols) == 0:
                    isRedundantWithContradictions = True
                else:
                    return (False, None)
        return (True, isRedundantWithContradictions)

    def _inferSymbolValuesFromRelations(self, contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]):
        anySymbolsUpdated = False
        for relation in self._recordedRelations:
            (symbol, conditionalSolutions) = self._calculateAnySolutionsFromRelation(relation, contradictedSymbolValues)
            someSubbedRelationWasSolvable = symbol is not None
            if someSubbedRelationWasSolvable:
                self._database[symbol] = conditionalSolutions
                
                inferredValues = {
                    solution.value
                    for solution in conditionalSolutions
                }
                # just in case there ever is a contradiction...
                # (otherwise the user will never be able to see what the value
                # was, since it'll be "forgotten")
                contradictedSymbolValues[symbol] = inferredValues
                
                anySymbolsUpdated = True
            
        if anySymbolsUpdated:
            self._inferSymbolValuesFromRelations(contradictedSymbolValues)

    def _calculateAnySolutionsFromRelation(self, relation: Relation, contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]):
        relationsWithKnownsSubbed = tuple(_CombinationsSubstituter(relation.asExprEqToZero, self._database))
        assert not any(
            isExpressionListSymbol(symbol) # type: ignore
            for conditionalExpr in relationsWithKnownsSubbed
            for symbol in conditionalExpr.value.free_symbols
        )
        if not all(
            relationExprCondition.value == 0
            for relationExprCondition in relationsWithKnownsSubbed
            if len(relationExprCondition.value.free_symbols) == 0
        ):
            raise ContradictionException(contradictedSymbolValues, relation)

        relationsWithSingleUnknown = (
            relationExprCondition
            for relationExprCondition in relationsWithKnownsSubbed
            # no expression list symbols are present; they've all been substituted
            if len(relationExprCondition.value.free_symbols) == 1
        )
        
        conditionalSolutionPairs = self._solveRelationExprsForSingleUnknown(relationsWithSingleUnknown, relation, contradictedSymbolValues)
        if __debug__:
            conditionalSolutionPairs = tuple(conditionalSolutionPairs)
            assert all(type(conditionalSolutionSet.value) is set for (symbol, conditionalSolutionSet) in conditionalSolutionPairs), \
                "Solver got a solution set that wasn't a FiniteSet"
        
        (symbol, conditionalSolutions) = self._convertConditionalSolutionsToSetsOfConditions(conditionalSolutionPairs)
        assert not isExpressionListSymbol(symbol) # type: ignore
        return (symbol, conditionalSolutions)

    def _solveRelationExprsForSingleUnknown(self, relationExprConditions: Iterable[ConditionalValue[sympy.Expr]], baseRelation: Relation, contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]) -> Generator[tuple[sympy.Symbol, ConditionalValue[SolutionSet]], Any, None]:
        for relationExprCondition in relationExprConditions:
            relationExpr = relationExprCondition.value
            assert(len(relationExpr.free_symbols) == 1), \
                "Relation had more than one unknown symbol to solve for"
            unknownSymbol = first(relationExpr.free_symbols)
            assert type(unknownSymbol) is sympy.Symbol
            solution = sympy.solveset(relationExpr, unknownSymbol)
            solutionSet = self._interpretSympySolution(unknownSymbol, solution, baseRelation, contradictedSymbolValues)
            yield (unknownSymbol, ConditionalValue(solutionSet, relationExprCondition.conditions))

    def _interpretSympySolution(self, symbol: sympy.Symbol, solution: sympy.Set, baseRelation: Relation, contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]) -> set[sympy.Expr]:
        # normal solutions to problem
        # example:
        #   a^2 = 4; a = {2, -2}
        if type(solution) is sympy.FiniteSet:
            solutionSet = set(solution)
            assert all(isinstance(item, sympy.Expr) for item in solutionSet)
            return solutionSet # type: ignore
        
        # solved such that no solutions are available
        # example:
        #   a/(b - 1) = 5; b = 1; a = {}
        elif solution is sympy.EmptySet:
            raise NoSolutionException([symbol], contradictedSymbolValues, baseRelation)
        
        else:
            raise NotImplementedError(f"Solver reached unconsidered set: {type(solution).__name__}")

    def _convertConditionalSolutionsToSetsOfConditions(self, conditionalSolutionPairs: Iterable[tuple[sympy.Symbol, ConditionalValue[SolutionSet]]]):
        if __debug__:
            conditionalSolutionPairs = tuple(conditionalSolutionPairs)
            if len(conditionalSolutionPairs) > 0:
                symbolSolved = conditionalSolutionPairs[0][0]
                allSymbolsTheSame = all(symbol == symbolSolved for (symbol, conditionalValue) in conditionalSolutionPairs)
                assert allSymbolsTheSame, \
                    "Substitutions in relation led to different unknown variables"

        symbol = None
        totalSolutionSet: set[ConditionalValue[sympy.Expr]] = set()
        for (symbol, conditionalValueSet) in conditionalSolutionPairs:
            valueSet = conditionalValueSet.value
            conditions = conditionalValueSet.conditions
            for value in valueSet:
                assert isNonSymbolicValue(value), \
                    "Solver makes false assumption that FiniteSets only contain non-symbolic values"
                totalSolutionSet.add(ConditionalValue(value, conditions))
        return (symbol, totalSolutionSet)
    

class _SymbolsDatabase:
    """
    A database for known symbols. Logically this is a union between two dictionaries:
    1. An initially empty dictionary of variable/value mappings, added to as values are inferred
    2. An infinite dictionary mapping "expression list symbols" to a list of actual expressions 
    """

    _DefaultType = TypeVar("_DefaultType")

    def __init__(self):
        # a mapping of a variable to its potential values and conditions
        # (like b = 4 when a = 2 and b = 5 when a = -1)
        self._symbolValues: dict[sympy.Symbol, set[ConditionalValue[sympy.Expr]]] = dict()
        # a mapping of symbols to conditional values for "expression list symbols"
        self._exprListSymbolValues: dict[sympy.Symbol, set[ConditionalValue[sympy.Expr]]] = dict()
        # the order in which symbols are iterated over (for substitution)
        self._symbolResolutionOrder: list[tuple[int, sympy.Symbol]] = list()

        self._expressionLexer = CommandLexer()
        self._expressionParser = CommandParser()

    def __getitem__(self, key: sympy.Symbol):
        if isExpressionListSymbol(key):
            if key not in self._exprListSymbolValues:
                self._exprListSymbolValues[key] = self._parseExprListSymbol(key)
                # resolution order doesn't include expression list symbols;
                # the generator knows how to handle this
                # self._insertSymbolToResolutionOrder(key)
            return self._exprListSymbolValues[key]
        else:
            return self._symbolValues[key]
    
    def __setitem__(self, key: sympy.Symbol, value: set[ConditionalValue[sympy.Expr]]):
        if isExpressionListSymbol(key):
            raise ValueError("Cannot set values for expression list symbols")
        if key in self._symbolValues:
            self._popSymbolFromResolutionOrder(key)
        self._symbolValues[key] = value
        self._insertSymbolToResolutionOrder(key)

    def __iter__(self):
        for (rank, symbol) in self._symbolResolutionOrder:
            yield symbol

    def __contains__(self, key: sympy.Symbol):
        return key in self._symbolValues or isExpressionListSymbol(key)

    def copy(self):
        newDatabase = _SymbolsDatabase()
        newDatabase._symbolValues = dict(self._symbolValues)
        newDatabase._exprListSymbolValues = dict(self._exprListSymbolValues)
        newDatabase._symbolResolutionOrder = list(self._symbolResolutionOrder)
        return newDatabase
    
    def get(self, key: sympy.Symbol, default: _DefaultType = None) -> set[ConditionalValue[sympy.Expr]] | _DefaultType:
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key: sympy.Symbol):
        if isExpressionListSymbol(key):
            raise ValueError("Cannot pop values for expression list symbols")
        self._popSymbolFromResolutionOrder(key)
        return self._symbolValues.pop(key)

    def _parseExprListSymbol(self, exprListSymbol: sympy.Symbol) -> set[ConditionalValue[sympy.Expr]]:
        assert isExpressionListSymbol(exprListSymbol)
        exprListStr = str(exprListSymbol)[1:-1]
        exprTokens = tuple(self._expressionLexer.findTokens(exprListStr))
        expressionList = self._expressionParser.parseExpressionList(exprTokens)
        return {
            ConditionalValue(expression, dict())
            for expression in expressionList
        }
    
    def _insertSymbolToResolutionOrder(self, symbol: sympy.Symbol):
        assert symbol in self, "Should not insert symbol's resolution order before it has values"
        symbolSortRank = self._calculateSymbolResolutionRank(symbol)
        if symbolSortRank == 0:
            self._symbolResolutionOrder.insert(0, (symbolSortRank, symbol))
        else:
            insertIdx = len(self._symbolResolutionOrder) + 1
            rankBeforeInsert = None
            while rankBeforeInsert is None or rankBeforeInsert > symbolSortRank:
                insertIdx -= 1
                if insertIdx == 0:
                    break
                (rankBeforeInsert, symbolBeforeInsert) = self._symbolResolutionOrder[insertIdx - 1]
            self._symbolResolutionOrder.insert(insertIdx, (symbolSortRank, symbol))

    def _calculateSymbolResolutionRank(self, symbol: sympy.Symbol):
        if isExpressionListSymbol(symbol):
            return 0
        else:
            conditionSymbols = {
                symbol
                for conditionValue in self[symbol]
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
    

class _CombinationsSubstituter:
    def __init__(self, expression: sympy.Expr, database: _SymbolsDatabase):
        self._expression = expression
        self._database = database
        self._currCombination = dict()
        self._resolutionOrder = tuple(database)
        self._exprListSymbols = tuple(
            exprListSymbol
            for exprListSymbol in expression.free_symbols
            if type(exprListSymbol) is sympy.Symbol and isExpressionListSymbol(exprListSymbol)
        )

    def __iter__(self) -> Generator[ConditionalValue[sympy.Expr], Any, None]:
        for symbolValueCombination in self._generateCombinations(0, 0):
            conditions = {
                symbol: conditionalValue
                for (symbol, conditionalValue) in symbolValueCombination.items()
                if symbol in self._expression.free_symbols
            }
            subExpr = self._expression.subs(symbolValueCombination)
            yield ConditionalValue(subExpr, conditions) # type: ignore
    
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
        anyConditionsMet = False
        for conditionalValue in self._database[symbolToInclude]:
            if self._testConditionsMet(conditionalValue):
                anyConditionsMet = True
                # overwritten to save on memory (instead of copying and creating a bunch of dicts)
                self._currCombination[symbolToInclude] = conditionalValue.value
                for finishedCombination in self._generateCombinations(numExprListsResolved, resolutionIdx):
                    yield finishedCombination
        assert anyConditionsMet, "Solver failed to find a valid condition"

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
            if self._currCombination[symbol] != value:
                return False
        return True


class BadRelationException(MultilineException, ABC):
    @abstractmethod
    def __init__(self, message: FormattedStr, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None], contradictingRelation: Relation):
        self.poorSymbolValues = poorSymbolValues
        self.contradictingRelation = contradictingRelation
        
        leftExprFormatted = self.substitutePoorSymbols(contradictingRelation.leftExpr, poorSymbolValues)
        rightExprFormatted = self.substitutePoorSymbols(contradictingRelation.rightExpr, poorSymbolValues)
        super().__init__((
            message,
            f"[red]{leftExprFormatted} = {rightExprFormatted}[/red]",
            *[
                f"[yellow]({poorSymbol} = {first(valueSet)})[/yellow]" if valueSet is not None and len(valueSet) == 1
                    else f"[yellow]({poorSymbol} = {valueSet})[/yellow]" if valueSet is not None
                    else f"[yellow]({poorSymbol}: unsolved)[/yellow]"
                for (poorSymbol, valueSet) in poorSymbolValues.items()
            ]
        ))

    def formatPoorSymbols(self, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]):
        return surroundJoin(
            (str(symbol) for symbol in poorSymbolValues.keys()),
            "[yellow]",
            "[/yellow]",
            ", "
        )
    
    def substitutePoorSymbols(self, expr: sympy.Expr, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]) -> sympy.Basic:
        return expr.subs({
            poorSymbol: sympy.Symbol(f"[yellow]{poorSymbol}[/yellow]")
            for poorSymbol in poorSymbolValues.keys()
        })

class ContradictionException(BadRelationException):
    def __init__(self, contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None], badRelation: Relation):
        symbolsStr = f" for {self.formatPoorSymbols(contradictedSymbolValues)}" \
            if len(contradictedSymbolValues) > 0 else ""
        super().__init__(
            f"Relation contradicts known/inferred values{symbolsStr}",
            contradictedSymbolValues,
            badRelation
        )

class NoSolutionException(BadRelationException):
    def __init__(self, symbolsMissingSolutions: Collection[sympy.Symbol], badSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None], badRelation: Relation):
        symbolsStr = f" for {self.formatPoorSymbols({symbol: None for symbol in symbolsMissingSolutions})}" \
            if len(symbolsMissingSolutions) > 0 else ""
        for unsolvedSymbol in symbolsMissingSolutions:
            if unsolvedSymbol not in badSymbolValues:
                badSymbolValues[unsolvedSymbol] = None
        super().__init__(
            f"Relation leads to unsolvable state{symbolsStr}",
            badSymbolValues,
            badRelation
        )
