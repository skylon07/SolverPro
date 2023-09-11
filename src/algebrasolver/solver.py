from abc import ABC, abstractmethod
from typing import Iterable, Collection, Generator, Any, Generic, TypeVar, overload

import sympy

from src.common.functions import first, surroundJoin, freeSymbolsOf
from src.common.types import FormattedStr
from src.common.exceptions import MultilineException
from src.app.widgets.colors import Colors
from src.parsing.lexer import CommandLexer
from src.parsing.parser import CommandParser, isExpressionListSymbol, isNonSymbolicValue


SolutionSet = set[sympy.Expr]

# so the linter doesn't HANG forever...
createSymbol = eval("sympy.Symbol")
subsExpr = eval("sympy.Expr.subs")
solveSet = eval("sympy.solveset")


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
        self.asExprEqToZero: sympy.Expr = leftExpr - rightExpr # = 0    # type: ignore
        assert isinstance(self.asExprEqToZero, sympy.Expr)

    def __repr__(self):
        return f"Relation({self.leftExpr}, {self.rightExpr})"
    
    def __hash__(self):
        return hash((self.leftExpr, self.rightExpr))

    def __eq__(self, other):
        if type(other) is not Relation:
            return False
        
        return self.leftExpr == other.leftExpr and self.rightExpr == other.rightExpr


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


class AlgebraSolver:
    def __init__(self):
        # a list of relational expressions with an implied equality to zero
        self._recordedRelations: list[Relation] = list()
        self._symbolValuesDatabase = _SymbolsDatabase()
        self._inferenceTable = _RelationSymbolTable()
        self._contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None] = dict()

    def recordRelation(self, relation: Relation):
        # TODO: use transactional data types that can be reversed more efficiently
        #       (this API also needs to be public for the driver -- there's a TODO about this)
        relationsBackup = list(self._recordedRelations)
        databaseBackup = self._symbolValuesDatabase.copy()
        inferenceTableBackup = self._inferenceTable.copy()
        
        # if there is a contradiction, it would be with these
        self._contradictedSymbolValues = {
            symbol: {
                conditional.value
                for conditional in self._symbolValuesDatabase[symbol]
            }
            for symbol in freeSymbolsOf(relation.asExprEqToZero)
            if symbol in self._symbolValuesDatabase and not isExpressionListSymbol(symbol)
        }
        try:
            (isRedundant, isRedundantWithContradictions) = self._checkForRedundancies(relation)
            if isRedundantWithContradictions:
                # test for restricted redefinition case, which is when a
                # relation is restricting what some variable's values are
                # example: if `a` is already known, {-4, 2, 5}, and a new
                # relation `a = 2` comes in, this is "redundant" (aka no new
                # information about other variables) but also contradictory
                # (because -4 ≠ 2 and 5 ≠ 2)
                nonExprSymbols = tuple(symbol for symbol in freeSymbolsOf(relation.asExprEqToZero) if not isExpressionListSymbol(symbol))
                couldBeRestrictRedefCase = len(nonExprSymbols) == 1
                if couldBeRestrictRedefCase:
                    symbol = first(nonExprSymbols)
                    assert type(symbol) is sympy.Symbol

                    isRestrictionOfExpressionList = self._dependsOnExpressionListSymbols(symbol)
                    if isRestrictionOfExpressionList:
                        raise ContradictionException(self._contradictedSymbolValues, relation)

                    (oldSolutions, oldRelation) = self._popInferredSolutions(symbol)
                    
                    try:
                        (newSymbol, newSolutions) = self._calculateAnySolutionsFromRelation(relation)
                    except ContradictionException:
                        # shouldn't be possible... but just in case!
                        raise RuntimeError("A contradiction was realized during restriction calculation (no new relations added...?)")
                    assert symbol == newSymbol, "Restriction solutions don't match found symbol" # this shouldn't be possible either!
                    if symbol is not None:
                        oldSolutionValues = tuple(solution.value for solution in oldSolutions)
                        newValuesAreActuallyRestrictions = len(newSolutions) < len(oldSolutions) and \
                            all(solution.value in oldSolutionValues for solution in newSolutions)
                        if newValuesAreActuallyRestrictions:
                            newSolutionValues = {condition.value for condition in newSolutions}
                            newSolutionsWithCorrectConditions = {
                                condition
                                for condition in oldSolutions
                                if condition.value in newSolutionValues
                            }
                            self._setInferredSolutions(symbol, newSolutionsWithCorrectConditions, relation)
                            isRedundant = False # since it technically did provide new information...
                            
                            # TODO: (optimization) remove other symbol values that relied on any conditions now not present
                            #       (since other symbols might have conditions that will never be true when substituted,
                            #       due to the values that were just removed)
                        else:
                            self._setInferredSolutions(symbol, oldSolutions, oldRelation)
            
            self._recordedRelations.append(relation)
            self._inferSymbolValuesFromRelations()
            return isRedundant
        
        except Exception as exception:
            self._recordedRelations = relationsBackup
            self._symbolValuesDatabase = databaseBackup
            self._inferenceTable = inferenceTableBackup
            self._contradictedSymbolValues = dict()
            raise exception

    def getSymbolConditionalValues(self, symbol: sympy.Symbol):
        return self._symbolValuesDatabase.get(symbol)
    
    def getRelations(self):
        return tuple(self._recordedRelations)
    
    def getRelationsWithSymbol(self, symbol: sympy.Symbol):
        return tuple(
            relation
            for relation in self._recordedRelations
            if symbol in freeSymbolsOf(relation.asExprEqToZero)
        )
    
    def popRelation(self, relation: Relation):
        self._recordedRelations.remove(relation)
        inferredSymbol = self._inferenceTable.get(relation)
        databaseDependsOnRelation = inferredSymbol is not None
        if databaseDependsOnRelation:
            self._popInferredSolutions(inferredSymbol)
            poppedSymbols = {inferredSymbol}
            # TODO: there's probably some dependency-path optimization that could be made here
            anyPopped = True
            while anyPopped:
                anyPopped = False
                for symbol in self._symbolValuesDatabase:
                    for conditionalValue in self._symbolValuesDatabase[symbol]:
                        conditions = conditionalValue.conditions
                        symbolDependsOnPoppedSymbols = any(poppedSymbol in conditions for poppedSymbol in poppedSymbols)
                        if symbolDependsOnPoppedSymbols:
                            self._popInferredSolutions(symbol)
                            poppedSymbols.add(symbol)
                            anyPopped = True
                            break # to move on to the next symbol

        # in case redundant relations can re-infer lost values
        self._inferSymbolValuesFromRelations()
    
    def substituteKnownsFor(self, expression: sympy.Expr):
        conditionals = _CombinationsSubstituter({expression}, self._symbolValuesDatabase).substitute()
        values = {
            conditional.value
            for conditional in conditionals
        }
        return values
    
    def substituteKnownsWithConditions(self, expression: sympy.Expr):
        conditionals = _CombinationsSubstituter({expression}, self._symbolValuesDatabase).substitute()
        return set(conditionals)
    
    def _setInferredSolutions(self, symbol: sympy.Symbol, solutions: set[ConditionalValue[sympy.Expr]], associatedRelation: Relation):
        self._symbolValuesDatabase[symbol] = solutions
        self._inferenceTable[symbol] = associatedRelation

    def _popInferredSolutions(self, symbol: sympy.Symbol):
        solutions = self._symbolValuesDatabase.pop(symbol)
        associatedRelation = self._inferenceTable.pop(symbol)
        return (solutions, associatedRelation)

    def _checkForRedundancies(self, relation: Relation):
        isRedundantWithContradictions = False
        for conditionalSubbedRelationExpr in _CombinationsSubstituter({relation.asExprEqToZero}, self._symbolValuesDatabase).substitute():
            subbedRelationExpr = conditionalSubbedRelationExpr.value
            if subbedRelationExpr != 0:
                if len(freeSymbolsOf(subbedRelationExpr)) == 0:
                    isRedundantWithContradictions = True
                else:
                    return (False, None)
        return (True, isRedundantWithContradictions)
    
    def _dependsOnExpressionListSymbols(self, symbol: sympy.Symbol, symbolsChecked: set[sympy.Symbol] | None = None):
        if symbolsChecked is None:
            symbolsChecked = set()
        
        if symbol not in symbolsChecked:
            symbolsChecked.add(symbol)
            for conditionalValue in self._symbolValuesDatabase[symbol]:
                for conditionalSymbol in conditionalValue.conditions:
                    if isExpressionListSymbol(conditionalSymbol) or self._dependsOnExpressionListSymbols(conditionalSymbol, symbolsChecked):
                        return True
        return False

    def _inferSymbolValuesFromRelations(self):
        anySymbolsUpdated = False
        for relation in self._recordedRelations:
            if relation in self._inferenceTable:
                # optimization: we know it's already provided information for a symbol!
                continue

            (symbol, conditionalSolutions) = self._calculateAnySolutionsFromRelation(relation)
            someSubbedRelationWasSolvable = symbol is not None
            if someSubbedRelationWasSolvable:
                assert relation not in self._inferenceTable, "Solver inferred new value from already consumed relation" # impossible... unless things aren't getting recorded/popped right
                assert symbol not in self._inferenceTable, "Solver inferred new value for already inferred symbol" # impossible... because it should have subbed, right?
                self._setInferredSolutions(symbol, conditionalSolutions, relation)
                
                inferredValues = {
                    solution.value
                    for solution in conditionalSolutions
                }
                # just in case there ever is a contradiction...
                # (otherwise the user will never be able to see what the value
                # was, since it'll be "forgotten")
                self._contradictedSymbolValues[symbol] = inferredValues
                
                anySymbolsUpdated = True
            
        # TODO: there's probably some dependency-path optimization that could be made here
        if anySymbolsUpdated:
            self._inferSymbolValuesFromRelations()
        self._contradictedSymbolValues = dict()

    def _calculateAnySolutionsFromRelation(self, relation: Relation):
        relationsWithKnownsSubbed = tuple(_CombinationsSubstituter({relation.asExprEqToZero}, self._symbolValuesDatabase).substitute())
        assert not any(
            isExpressionListSymbol(symbol) # type: ignore
            for conditionalExpr in relationsWithKnownsSubbed
            for symbol in freeSymbolsOf(conditionalExpr.value)
        )
        if not all(
            relationExprCondition.value == 0
            for relationExprCondition in relationsWithKnownsSubbed
            if len(freeSymbolsOf(relationExprCondition.value)) == 0
        ):
            raise ContradictionException(self._contradictedSymbolValues, relation)

        relationsWithSingleUnknown = (
            relationExprCondition
            for relationExprCondition in relationsWithKnownsSubbed
            # no expression list symbols are present; they've all been substituted
            if len(freeSymbolsOf(relationExprCondition.value)) == 1
        )
        
        conditionalSolutionPairs = self._solveRelationExprsForSingleUnknown(relationsWithSingleUnknown, relation)
        if __debug__:
            conditionalSolutionPairs = tuple(conditionalSolutionPairs)
            assert all(type(conditionalSolutionSet.value) is set for (symbol, conditionalSolutionSet) in conditionalSolutionPairs), \
                "Solver got a solution set that wasn't a FiniteSet"
        
        (symbol, conditionalSolutions) = self._convertConditionalSolutionsToSetsOfConditions(conditionalSolutionPairs)
        assert not isExpressionListSymbol(symbol) # type: ignore
        return (symbol, conditionalSolutions)

    def _solveRelationExprsForSingleUnknown(self, relationExprConditions: Iterable[ConditionalValue[sympy.Expr]], baseRelation: Relation) -> Generator[tuple[sympy.Symbol, ConditionalValue[SolutionSet]], Any, None]:
        for relationExprCondition in relationExprConditions:
            relationExpr = relationExprCondition.value
            assert(len(freeSymbolsOf(relationExpr)) == 1), \
                "Relation had more than one unknown symbol to solve for"
            unknownSymbol = first(freeSymbolsOf(relationExpr))
            assert type(unknownSymbol) is sympy.Symbol
            solution = solveSet(relationExpr, unknownSymbol)
            solutionSet = self._interpretSympySolution(unknownSymbol, solution, baseRelation)
            yield (unknownSymbol, ConditionalValue(solutionSet, relationExprCondition.conditions))

    def _interpretSympySolution(self, symbol: sympy.Symbol, solution: sympy.Set, baseRelation: Relation) -> set[sympy.Expr]:
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
            raise NoSolutionException([symbol], self._contradictedSymbolValues, baseRelation)
        
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
    

class _RelationSymbolTable:
    _DefaultType = TypeVar("_DefaultType")

    def __init__(self):
        self._inferredSymbols: dict[Relation, sympy.Symbol] = dict()
        self._solvedRelations: dict[sympy.Symbol, Relation] = dict()

    @overload
    def __getitem__(self, key: sympy.Symbol) -> Relation: ...
    @overload
    def __getitem__(self, key: Relation) -> sympy.Symbol: ...

    def __getitem__(self, key: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            return self._solvedRelations[key]
        elif type(key) is Relation:
            return self._inferredSymbols[key]
        else:
            raise KeyError(key)

    @overload 
    def __setitem__(self, key: sympy.Symbol, value: Relation) -> None: ...
    @overload
    def __setitem__(self, key: Relation, value: sympy.Symbol) -> None: ...

    def __setitem__(self, key: sympy.Symbol | Relation, value: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            assert type(value) is Relation
            self._solvedRelations[key] = value
            self._inferredSymbols[value] = key
        elif type(key) is Relation:
            assert type(value) is sympy.Symbol
            self._inferredSymbols[key] = value
            self._solvedRelations[value] = key
        else:
            raise KeyError(key)
        
    @overload
    def __contains__(self, key: sympy.Symbol) -> bool: ...
    @overload
    def __contains__(self, key: Relation) -> bool: ...

    def __contains__(self, key: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            return key in self._solvedRelations
        elif type(key) is Relation:
            return key in self._inferredSymbols
        else:
            raise KeyError(key)
        
    def copy(self):
        newTable = _RelationSymbolTable()
        newTable._inferredSymbols = dict(self._inferredSymbols)
        newTable._solvedRelations = dict(self._solvedRelations)
        return newTable
        
    @overload
    def get(self, key: sympy.Symbol, default: _DefaultType = None) -> Relation | _DefaultType: ...
    @overload
    def get(self, key: Relation, default: _DefaultType = None) -> sympy.Symbol | _DefaultType: ...

    def get(self, key: sympy.Symbol | Relation, default: _DefaultType = None) -> sympy.Symbol | Relation | _DefaultType:
        if type(key) is sympy.Symbol:
            return self._solvedRelations.get(key, default)
        elif type(key) is Relation:
            return self._inferredSymbols.get(key, default)
        else:
            # return default?
            # naw...
            # if you pass in the wrong type of thing, that's a bug!
            raise KeyError(key)
    
    @overload
    def pop(self, key: sympy.Symbol) -> Relation: ...
    @overload
    def pop(self, key: Relation) -> sympy.Symbol: ...

    def pop(self, key: sympy.Symbol | Relation):
        if type(key) is sympy.Symbol:
            value = self._solvedRelations.pop(key)
            self._inferredSymbols.pop(value)
            return value
        elif type(key) is Relation:
            value = self._inferredSymbols.pop(key)
            self._solvedRelations.pop(value)
            return value
        else:
            raise KeyError(key)
        

class _InferenceOrderSolver:
    def __init__(self, relations: list[Relation], knownSymbols: set[sympy.Symbol]):
        self._relations = relations
        self._knownSymbols = knownSymbols
        self._potentialInferencesTable = _RelationSymbolTable()


    def findSolveOrder(self):
        unknownSymbolCounts = self._countUnknownSymbols()
        for relation in self._relations:
            unknownSymbolsInRelation: list[tuple[sympy.Symbol, int]] = [
                (symbol, unknownSymbolCounts[symbol])
                for symbol in freeSymbolsOf(relation.asExprEqToZero)
                if symbol not in self._knownSymbols and symbol not in self._potentialInferencesTable and not isExpressionListSymbol(symbol)
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
                        return {
                            (symbolToInfer, relationToInferFrom)
                            for symbolToInfer in symbolsInFamily
                            for relationToInferFrom in [self._potentialInferencesTable[symbolToInfer]]
                        }
        return None
    
    def _testSolidInferenceFamily(self, baseRelation: Relation, relationsChecked: set[Relation] | None = None, symbolsInFamily: set[sympy.Symbol] | None = None):
        if relationsChecked is None:
            relationsChecked = {baseRelation}
        if symbolsInFamily is None:
            symbolsInFamily = set()

        for symbol in freeSymbolsOf(baseRelation.asExprEqToZero):
            if symbol in self._potentialInferencesTable:
                symbolsInFamily.add(symbol)
                relation = self._potentialInferencesTable[symbol]
                if relation not in relationsChecked:
                    relationsChecked.add(relation)
                    holeExists = not self._testSolidInferenceFamily(relation, relationsChecked, symbolsInFamily)
                    if holeExists:
                        return (False, symbolsInFamily)
            elif symbol not in self._knownSymbols:
                return (False, symbolsInFamily)
        return (True, symbolsInFamily)


    def _countUnknownSymbols(self):
        unknownSymbolCounts: dict[sympy.Symbol, int] = dict()
        for relation in self._relations:
            for symbol in freeSymbolsOf(relation.asExprEqToZero):
                if symbol in unknownSymbolCounts:
                    unknownSymbolCounts[symbol] += 1
                elif symbol not in self._knownSymbols:
                    unknownSymbolCounts[symbol] = 1
        return unknownSymbolCounts
    

class _CombinationsSubstituter:
    def __init__(self, expressions: set[sympy.Expr], database: _SymbolsDatabase):
        self._expressions = expressions
        self._symbolValuesDatabase = database
        self._currCombination = dict()
        self._resolutionOrder = tuple(database)
        self._exprListSymbols = tuple(
            exprListSymbol
            for expression in expressions
            for exprListSymbol in freeSymbolsOf(expression)
            if isExpressionListSymbol(exprListSymbol)
        )

    def substitute(self) -> Generator[ConditionalValue[sympy.Expr], Any, None]:
        for symbolValueCombination in self._generateCombinations(0, 0):
            for expression in self._expressions:
                conditions = {
                    symbol: conditionalValue
                    for (symbol, conditionalValue) in symbolValueCombination.items()
                    if symbol in freeSymbolsOf(expression)
                }
                subExpr = subsExpr(expression, symbolValueCombination)
                yield ConditionalValue(subExpr, conditions)
    
    def substituteForMapping(self) -> dict[sympy.Expr, ConditionalValue[sympy.Expr]]:
        return dict(self._substituteForMapPairs())

    def _substituteForMapPairs(self) -> Generator[tuple[sympy.Expr, ConditionalValue[sympy.Expr]], Any, None]:
        for symbolValueCombination in self._generateCombinations(0, 0):
            for expression in self._expressions:
                conditions = {
                    symbol: conditionalValue
                    for (symbol, conditionalValue) in symbolValueCombination.items()
                    if symbol in freeSymbolsOf(expression)
                }
                yield (expression, ConditionalValue(subExpr, conditions))
    
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
                for finishedCombination in self._generateCombinations(numExprListsResolved, resolutionIdx):
                    yield finishedCombination

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
            f"[{Colors.textRed.hex}]{leftExprFormatted} = {rightExprFormatted}[/]",
            *[
                f"[{Colors.textYellow.hex}]({poorSymbol} = {first(valueSet)})[/]" if valueSet is not None and len(valueSet) == 1
                    else f"[{Colors.textYellow.hex}]({poorSymbol} = {valueSet})[/]" if valueSet is not None
                    else f"[{Colors.textYellow.hex}]({poorSymbol}: unsolved)[/]"
                for (poorSymbol, valueSet) in poorSymbolValues.items()
            ]
        ))

    def formatPoorSymbols(self, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]):
        return surroundJoin(
            (str(symbol) for symbol in poorSymbolValues.keys()),
            f"[{Colors.textYellow.hex}]",
            f"[/{Colors.textYellow.hex}]",
            ", "
        )
    
    def substitutePoorSymbols(self, expr: sympy.Expr, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]) -> sympy.Basic:
        return subsExpr(expr, {
            poorSymbol: createSymbol(f"[{Colors.textYellow.hex}]{poorSymbol}[/]")
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
