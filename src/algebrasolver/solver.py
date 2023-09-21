from typing import Iterable, Generator, Any
import bisect

import sympy

from src.common.functions import first
from src.common.sympyLinterFixes import solveSet
from src.parsing.parser import isExpressionListSymbol, isNonSymbolicValue, freeSymbolsOf
from src.algebrasolver.relationSymbolTable import RelationSymbolTable
from src.algebrasolver.symbolsDatabase import SymbolsDatabase
from src.algebrasolver.inferenceOrderSolver import InferenceOrderSolver
from src.algebrasolver.combinationsSubstituter import CombinationsSubstituter
from src.algebrasolver.types import *


class AlgebraSolver:
    """
    This is the solving engine that puts everything in this module together.
    Things outside this module should interact with an instance of this.
    This solver is responsible for inferring variable values from given
    relations and substituting symbols in arbitrary expressions with those
    known values.

    All of this is one beast of a process; the AlgebraSolver really is a kind of
    mini math engine with more moving parts than anything else in Solver Pro.
    To summarize its behavior, the AlgebraSolver is used like such:
        - Relations are recorded with `recordRelation()`
            - Any variables whose values can be inferred are solved for using
              back substitution
        - Relations may be optionally deleted
            - This will also subsequently "forget" any inferred values that
              depended on this relation
        - Arbitrary expressions can be given to the solver for substitution of
          known symbols with their values (one symbol *can* map to many values)
    """

    def __init__(self):
        # a list of relational expressions with an implied equality to zero
        self._recordedRelations: list[Relation] = list()
        self._recordedRelationsSorted: list[Relation] = list()
        # database for "known" values of symbols
        self._symbolValuesDatabase = SymbolsDatabase()
        # table relating symbols to the relations they were inferred from
        self._inferenceTable = RelationSymbolTable()
        # temporary table of "bad symbols", reset on every attempt to record a relation
        self._contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None] = dict()

    def recordRelation(self, relation: Relation):
        """
        Records a relation and tries to infer numeric values from any symbols
        this relation might provide information on.

        In some cases, the solver will detect "bad" relations when an attempt to
        record them is made. These are relations that imply values for symbols
        that are contradictory to what was already recorded, and relations that
        make it impossible to infer values for some symbol. Some relations don't
        provide any useful information to make inferences on but also aren't
        contradictory; these are known as "redundant" relations. This function
        returns a boolean indicating if a relation is "redundant" in this way.

        Some examples of contradictory relations:
        
        ```raw
        a = 5
        a = 5 + 1   <-- Contradiction! (since a = 5)

        x * y = z + 2
        x + y = 7
        z = 2*(x + 1)
        x = z - 4   <-- Contradiction! (since x = 4, z = 10)
        ```

        An example of some "unsolvable" relations:

        ```raw
        x/(y - 2) = 6
        y = 2       <-- Unsolvable! (x/0 = 6)
        ```

        (Although you could easily fix the above by reorganizing the first
        relation to something like `x = 6*(y - 2)` or something similar.)

        Some examples of redundant relations:
        
        ```raw
        a = 5
        2*a = 10    <-- (Redundant...)

        x * y = z + 2
        x + y = 7
        z = 2*(x + 1)
        x = z - 6   <-- (Redundant...)
        ```
        """

        # TODO: use transactional data types that can be reversed more efficiently
        #       (this API also needs to be public for the driver -- there's a TODO about this)
        relationsBackup = list(self._recordedRelations)
        relationsSortedBackup = list(self._recordedRelationsSorted)
        databaseBackup = self._symbolValuesDatabase.copy()
        inferenceTableBackup = self._inferenceTable.copy()
        
        # if there is a contradiction, it would be with these
        self._contradictedSymbolValues = {
            symbol: {
                conditional.value
                for conditional in self._symbolValuesDatabase[symbol]
            }
            for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False)
            if symbol in self._symbolValuesDatabase
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
                nonExprSymbols = tuple(symbol for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False))
                wasActuallyRestrictRedefCase = False
                couldBeRestrictRedefCase = len(nonExprSymbols) == 1
                if couldBeRestrictRedefCase:
                    symbol = first(nonExprSymbols)

                    isRestrictionOfExpressionList = self._dependsOnExpressionListSymbols(symbol)
                    if isRestrictionOfExpressionList:
                        raise ContradictionException(self._contradictedSymbolValues, relation)

                    (oldSolutions, oldRelation) = self._popInferredSolutions(symbol)

                    try:
                        (newSymbol, newSolutions, newRelation) = self._solveForRestrictRedefCase(symbol, relation)
                    except ContradictionException:
                        # shouldn't be possible... but just in case!
                        raise RuntimeError("A contradiction was realized during restriction calculation (no new relations added...?)")
                    assert symbol == newSymbol, "Restriction solutions don't match found symbol" # this shouldn't be possible (to fail) either!
                    assert relation == newRelation, "Restriction solution relations don't match" # this ALSO shouldn't be possible (to fail)!
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
                            wasActuallyRestrictRedefCase = True
                            
                            # TODO: (optimization) remove other symbol values that relied on any conditions now not present
                            #       (since other symbols might have conditions that will never be true when substituted,
                            #       due to the values that were just removed)
                
                if not wasActuallyRestrictRedefCase:
                    raise ContradictionException(self._contradictedSymbolValues, relation)
            
            self._recordedRelations.append(relation)
            bisect.insort(
                self._recordedRelationsSorted,
                relation,
                key = lambda relation: len(freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False))
            )
            self._inferSymbolValuesFromRelations()
            return isRedundant
        
        except Exception as exception:
            self._recordedRelations = relationsBackup
            self._recordedRelationsSorted = relationsSortedBackup
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
        """
        This function is logically the inverse of `recordRelation()`; That is,
        if `recordRelation()` remembers a relation and infers certain symbols
        from known relations, then this function forgets a relation and deletes
        values for certain symbols depending on the known relations left over.

        The algorithm is fairly straightforward: Pop the relation and the
        symbol. Check every other symbol's conditions. If the popped symbol ever
        shows up in any of those conditions, those symbols are dependent on the
        popped symbol and should be popped as well. Then just keep repeating
        that process until there aren't any more dependent symbols in the
        database.
        """
        
        self._recordedRelations.remove(relation)
        self._recordedRelationsSorted.remove(relation)
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
        """
        Takes an expression and substitutes its symbols with any values that
        might be known about them. Expression lists (aka symbols that look like
        `Symbol("{1,2,3}")`) are always treated as known symbols (since their
        name is literally the set of values they represent). Multiple
        expressions may be returned if one or more symbols evaluate to multiple
        values.
        """
        
        conditionals = CombinationsSubstituter({expression}, self._symbolValuesDatabase).substitute()
        values = {
            conditional.value
            for conditional in conditionals
        }
        return values
    
    def substituteKnownsWithConditions(self, expression: sympy.Expr):
        """
        This function performs the exact same operation as
        `substituteKnownsFor()`, except each expression also has its conditions
        tied to it (given as a `ConditionalValue` instance).
        """
        
        conditionals = CombinationsSubstituter({expression}, self._symbolValuesDatabase).substitute()
        return set(conditionals)
    
    def _setInferredSolutions(self, symbol: sympy.Symbol, solutions: set[ConditionalValue[sympy.Expr]], associatedRelation: Relation):
        """
        Sets a symbol's solutions by keeping the database and relation-symbol
        table in sync. This should *always* be used instead of modifying the
        database/table directly.
        """

        assert all(isNonSymbolicValue(solution.value) for solution in solutions), "Solver tried to set a variable's inferred values to an unsolved expression"
        self._symbolValuesDatabase[symbol] = solutions
        self._inferenceTable[symbol] = associatedRelation

    def _popInferredSolutions(self, symbol: sympy.Symbol):
        """
        Removes a symbol's solutions from both the database and relation-symbol
        table, keeping them in sync. This should *always* be used instead of
        modifying the database/table directly.
        """

        solutions = self._symbolValuesDatabase.pop(symbol)
        associatedRelation = self._inferenceTable.pop(symbol)
        return (solutions, associatedRelation)

    def _checkForRedundancies(self, relation: Relation):
        isRedundantWithContradictions = False
        for conditionalSubbedRelationExpr in CombinationsSubstituter({relation.asExprEqToZero}, self._symbolValuesDatabase).substitute():
            subbedRelationExpr = conditionalSubbedRelationExpr.value
            if subbedRelationExpr != 0:
                if len(freeSymbolsOf(subbedRelationExpr)) == 0:
                    isRedundantWithContradictions = True
                else:
                    return (False, None)
        return (True, isRedundantWithContradictions)
    
    def _dependsOnExpressionListSymbols(self, symbol: sympy.Symbol, symbolsChecked: set[sympy.Symbol] | None = None):
        """
        Checks if a symbol depends on an expression list (or a symbol that
        depends on one, or a symbol that depends on a symbol that depends on
        one, etc.)
        """
        
        if symbolsChecked is None:
            symbolsChecked = set()
        
        if symbol not in symbolsChecked:
            symbolsChecked.add(symbol)
            for conditionalValue in self._symbolValuesDatabase[symbol]:
                for conditionalSymbol in conditionalValue.conditions:
                    if isExpressionListSymbol(conditionalSymbol) or self._dependsOnExpressionListSymbols(conditionalSymbol, symbolsChecked):
                        return True
        return False
    
    def _solveForRestrictRedefCase(self, symbol: sympy.Symbol, relation: Relation):
        return first(self._forwardSolveSymbols([(symbol, relation)], isRestrictRedefSolve = True))

    def _inferSymbolValuesFromRelations(self):
        """
        This is the main "brain" function of the solver. There are four logical
        stages to how symbol values are inferred:
        1. Find the "inference orders" in the relations that list the
           symbol/relation pairs to solve with
        2. Forward-solve symbolically each relation with its paired symbol
           until you get to the last symbol, which should provide a set of
           numeric values
        3. Back-substitute through the inference orders backwards, chaining
           the substitutions of the symbols with numeric values
        4. Check for contradictions (not actually sure if this is necessary...)

        Each step is described in more detail in the documentation of its
        associated function.
        """
        
        symbolsToSolve = None
        firstLoop = True
        while symbolsToSolve is not None or firstLoop:
            if not firstLoop and symbolsToSolve is not None:
                symbolsToBackSubstitute = reversed(tuple(self._forwardSolveSymbols(symbolsToSolve)))
                self._backSubstituteSymbols(symbolsToBackSubstitute)
                self._checkForContradictions()
            symbolsToSolve = InferenceOrderSolver(self._recordedRelationsSorted, self._symbolValuesDatabase).findSolveOrder()
            firstLoop = False
        
        self._contradictedSymbolValues = dict()

    def _forwardSolveSymbols(self, symbolsToSolve: Iterable[tuple[sympy.Symbol, Relation]], database: SymbolsDatabase | None = None, *, isRestrictRedefSolve: bool = False) -> Generator[tuple[sympy.Symbol, set[ConditionalValue[sympy.Expr]], Relation], Any, None]:
        """
        Forward-solving symbols is the process of repeatedly solving a relation
        for a given symbol and substituting that symbol in all future relations.
        Eventually (assuming the "inference order" `symbolsToSolve` is complete)
        this will lead to solving the last symbol and getting back a numeric
        value, which marks the end of this algorithm.

        Here's the process conceptually:

        ```raw
        a*c/2 = 9           (solve for: a)
        a + b = c + 6       (solve for: b)
        c/2 = a             (solve for: c)

        a*c/2 = 9           (solve for: a)
        a*c   = 18
        a = 18/c

           a   + b = c + 6  (solve for: b)
        (18/c) + b = c + 6
        b +  18/c  = c + 6
        b = c + 6 - 18/c

        c/2 =    a          (solve for: c)
        c/2 = (18/c)
        c   =  36/c
        c^2 =  36
        c = {6, -6}
        ```

        And we're done! After going through that, the function returns all of
        the symbols, their symbolic (or numeric) values, and their paired
        relations.
        """
        
        if database is None:
            database = self._symbolValuesDatabase.copy()
        
        for (symbol, relation) in symbolsToSolve:
            restrictRedefSymbol = None if not isRestrictRedefSolve \
                else symbol
            relationsWithKnownsAndInferredSubbed = CombinationsSubstituter({relation.asExprEqToZero}, database, restrictRedefSymbol = restrictRedefSymbol).substitute()
            flattenedConditionalSolutions = {
                ConditionalValue(solution, conditionalSolutions.conditions)
                for conditionalSolutions in self._solveRelationForSymbol(relationsWithKnownsAndInferredSubbed, relation, symbol)
                for solution in conditionalSolutions.value
            }
            database[symbol] = flattenedConditionalSolutions
            self._contradictedSymbolValues[symbol] = {conditional.value for conditional in flattenedConditionalSolutions}
            yield (symbol, flattenedConditionalSolutions, relation)

    def _backSubstituteSymbols(self, symbolsToBackSubstitute: Iterable[tuple[sympy.Symbol, set[ConditionalValue[sympy.Expr]], Relation]]):
        """
        This substitution function takes a partially solved inference order (as
        `symbolsToBackSubstitute` -- note that it should be reversed) and
        completes the back-substitution solver algorithm by substituting the
        known symbols' values back into previous relations, revealing the values
        of more symbols. Continuing from the example in
        `_forwardSolveSymbols()`:

        ```raw
        a*c/2 = 9           (solve for: a)
        a + b = c + 6       (solve for: b)
        c/2 = a             (solve for: c)

        c = {6, -6}

        b =     c     + 6 - 18/    c
        b = ({6, -6}) + 6 - 18/({6, -6})
        b = {(6) + 6 - 18/(6), (-6) + 6 - 18/(-6)}
        b = {   12   -   3   ,      0   -   -3   }
        b = {9, 3}

        a = 18/    c
        a = 18/({6, -6})
        a = {3, -3}
        ```

        The result is all the symbols being fully solved: `a = 3; b = 9; c = 6`
        and `a = -3; b = 3; c = -6`. Substituting these values back into the
        original relations shows these values are true statements (so long as
        you don't accidentally swap variables between the two scenarios!).
        """
        
        for (symbol, unsolvedConditionalSolutions, relationKnownFrom) in symbolsToBackSubstitute:
            conditionalSolutionsWithKnownSymbols = {
                ConditionalValue(
                    conditional.value,
                    {
                        symbol: condition
                        for (symbol, condition) in conditional.conditions.items()
                        if symbol in self._symbolValuesDatabase
                    }
                )
                for conditional in unsolvedConditionalSolutions
            }
            subbedSolutions = {
                ConditionalValue(
                    subbedConditionalSolution.value,
                    self._unionConditions(
                        subbedConditionalSolution.conditions,
                        conditionalSolution.conditions
                    )
                )
                for (unsubbedSolutionExpr, subbedConditionalSolutions) in CombinationsSubstituter(
                    {conditionalSolution.value for conditionalSolution in unsolvedConditionalSolutions},
                    self._symbolValuesDatabase
                ).substituteForMapping().items()
                for subbedConditionalSolution in subbedConditionalSolutions
                for conditionalSolution in conditionalSolutionsWithKnownSymbols
                if conditionalSolution.value == unsubbedSolutionExpr
            }
            self._setInferredSolutions(symbol, subbedSolutions, relationKnownFrom)
            
            inferredValues = {
                subbedConditionalSolution.value
                for subbedConditionalSolution in subbedSolutions
            }
            # just in case there ever is a contradiction...
            # (otherwise the user will never be able to see what the value
            # was, since it'll be "forgotten")
            self._contradictedSymbolValues[symbol] = inferredValues

    def _checkForContradictions(self):
        # sorted is theoretically faster to detect since it'll check single-variable
        # relations first (which are the most common kinds of contradictions)
        for relation in self._recordedRelationsSorted:
            if relation in self._inferenceTable:
                # can't have contradictions if it's part of where the solution came from...
                continue

            relationsWithKnownsSubbed = CombinationsSubstituter({relation.asExprEqToZero}, self._symbolValuesDatabase).substitute()
            if not all(
                relationExprCondition.value == 0
                for relationExprCondition in relationsWithKnownsSubbed
                if len(relationExprCondition.value.free_symbols) == 0
            ):
                raise ContradictionException(self._contradictedSymbolValues, relation)
            
    def _solveRelationForSymbol(self, relationsWithKnownsSubbed: Iterable[ConditionalValue[sympy.Expr]], fromRelation: Relation, unknownSymbol: sympy.Symbol):
        """This function just serves as a simple wrapper around `sympy.solveSet()`"""
        
        for relationExprCondition in relationsWithKnownsSubbed:
            relationExpr = relationExprCondition.value
            solution = solveSet(relationExpr, unknownSymbol)
            solutionSet = self._interpretSympySolution(unknownSymbol, solution, fromRelation)
            yield ConditionalValue(solutionSet, relationExprCondition.conditions)

    def _interpretSympySolution(self, symbol: sympy.Symbol, solution: sympy.Set, fromRelation: Relation) -> set[sympy.Expr]:
        """Converts a sympy `solveSet()` result into something the solver can use"""
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
            raise NoSolutionException([symbol], self._contradictedSymbolValues, fromRelation)
        
        else:
            raise NotImplementedError(f"Solver reached unconsidered set: {type(solution).__name__}")
        
    def _unionConditions(self, firstConditions: dict[sympy.Symbol, sympy.Expr], secondConditions: dict[sympy.Symbol, sympy.Expr]):
        newConditions = dict(firstConditions)
        for (symbol, condition) in secondConditions.items():
            assert symbol not in newConditions or newConditions[symbol] == condition
            newConditions[symbol] = condition
        return newConditions
