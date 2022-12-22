import sympy

from structures import *

class AlgebraSolver:
    def __init__(self):
        pass # TODO

    def extractKnowledgeFromRelation(self, relation):
        pass # TODO
    
    def _extractNumericsFromRelation(self, relation):
        pass # TODO: return base relational subs for given relation

    def _findSolvableNumerics(self, expr):
        pass # TODO


class _BackSubstituterSolver:
    def __init__(self, exprKeys):
        self._exprKeyOrder = tuple(self._sortExprKeys(exprKeys))
        self._unusedExprKeyIdx = 0
        self._symbolSubs = SubDict()

    def getSolutions(self):
        pass # TODO

    def _sortExprKeys(self, exprKeys):
        """
        this ensures that variables needing to be solved don't get "trapped"
        trying to use an expression they don't exist in; for example:
        
        - solve for a -- a..2b..2c
        - solve for b -- 2a..b..3c
        - solve for c -- 2a..4b -- TRAPPED
        
        what should have happened is something like
        
        - solve for a -- 2a..4b -- not trapped!
        - solve for b -- a..2b..2c
        - solve for c -- 2a..b..3c
        """
        return sorted(exprKeys, key=lambda expr: len(expr.free_symbols))
    
    def _findSolutions(self):
        pass # TODO (from _recursiveSolve...() and _recursiveBranch...())

    def _findNextUsefulRelation(self):
        pass # TODO

    def _findSymbolToSolveFor(self):
        pass # TODO

    def _backSubstitute(self, finalSubDict, symbolToSolveFor):
        pass # TODO

    
class _SympySolveTools:
    class _SolutionTypes:
        @property
        def NORMAL(self):
            """ex. FiniteSet({3, a + 2, b * c})"""
            return "NORMAL"

        @property
        def EMPTY(self):
            """ex. EmptySet() == {}"""
            return "EMPTY"

        @property
        def COMPLEXES(self):
            """ex. TODO"""
            return "COMPLEXES"

        @property
        def COMPLEMENT(self):
            """ex. TODO"""
            return "COMPLEMENT"

        @property
        def CONDITIONAL(self):
            """ex. TODO"""
            return "CONDITIONAL"
    
    solutionTypes = _SolutionTypes()

    @classmethod
    def solveSet(cls, expr, atom):
        pass # TODO

    @classmethod
    def _substituteNumericInBadTerms(cls, numericAtom, numericAtomSub, expr):
        pass # TODO

    @classmethod
    def _solveSetForNonNumeric(cls, expr, atom):
        pass # TODO (and assert atom is not numeric)
    
    @classmethod
    def _interpretSolution(cls, solution):
        pass # TODO
    
    class _Solution:
        def __init__(self, solutionSet):
            self._solutionSet = solutionSet
            self._type = self._getSetType(solutionSet)

        @property
        def type(self):
            return self._type

        @property
        def set(self):
            return self._solutionSet
        
        def _getSetType(self, solutionSet):
            types = _SympySolveTools.solutionTypes
            if type(solutionSet) is sympy.FiniteSet:
                return types.NORMAL
            elif solutionSet is sympy.EmptySet:
                return types.EMPTY
            elif type(solutionSet) is sympy.Complement:
                return types.COMPLEMENT
            elif solutionSet is sympy.Complexes:
                return types.COMPLEXES
            elif type(solutionSet) is sympy.ConditionSet:
                return types.CONDITIONAL
            else:
                raise NotImplementedError("Solution ran into an unconsidered type scenario")

        def reverseSubstitutionOfNumeric(self, subsDict):
            self._solutionSet = self._performSubsOnSet(self._solutionSet, subsDict)

        def _performSubsOnSet(self, sympySet, subsDict):
            pass # TODO
