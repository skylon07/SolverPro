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
    """
    This class is tasked with extrapolating solutions for individual variables
    given a single "universe" by a "base numerical substitution dictionary" and
    a list of keys present in the dictionary to extrapolate from.

    A "base numerical substitution dictionary" is a *dictionary* containing
    *substitutions* from expressions to *numerics* that they equal. It is
    considered the *base* set of relations to extrapolate solutions from

    This class will provide valid solutions via `getNewSolutions()` only if
        - the substitutions in the base dictionary represent equalities (ie
            {a + b: 2} implies that a + b = 2)
        - the dictionary's values are all numeric (ie {a + b: 2} is valid, but
            {a: 2 - b} is not)
    """

    def __init__(self, exprKeys, baseNumericalSubs):
        self._exprKeyOrder = tuple(self._sortExprKeys(exprKeys))
        self._unusedExprKeyIdx = 0
        self._baseNumericalSubs = baseNumericalSubs
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
        return sorted(exprKeys, key = lambda expr: len(expr.free_symbols))
    
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
            return "NORMAL"

        @property
        def EMPTY(self):
            return "EMPTY"

        @property
        def COMPLEXES(self):
            return "COMPLEXES"

        @property
        def COMPLEMENT(self):
            return "COMPLEMENT"

        @property
        def CONDITIONAL(self):
            return "CONDITIONAL"
    
    _solutionTypes = _SolutionTypes()

    @classmethod
    def solveSet(cls, expr, atom):
        if isNumeric(atom):
            # solving for variables in exponents leads to errors with no clean fixes,
            # so we just ignore them by converting them to symbols first
            atomSub = sympy.Symbol(":NUMERIC {}:".format(atom))
            exprWithNumericSubbed = cls._substituteNumericInBadTerms(atom, atomSub, expr)
            solution = cls._solveSetForAtom(exprWithNumericSubbed, atom)
            solution.reverseSubstitutionOfNumeric({atomSub: atom})
        else:
            solution = cls._solveSetForAtom(expr, atom)
        return cls._interpretSolution(solution)

    @classmethod
    def _substituteNumericInBadTerms(cls, numericAtom, numericAtomSub, expr):
        isBadExpr = expr.is_Pow
        if isBadExpr:
            return expr.subs(numericAtom, numericAtomSub)
        elif expr.is_Atom:
            return expr
        else:
            # this is a neat way to traverse expression trees as given by
            # https://docs.sympy.org/latest/tutorials/intro-tutorial/manipulation.html#recursing-through-an-expression-tree
            expr: sympy.Expr = expr
            return expr.func(*(
                cls._substituteNumericInBadTerms(numericAtom, numericAtomSub, term)
                for term in expr.args
            ))

    @classmethod
    def _solveSetForAtom(cls, expr, atom):
        solutionSet = sympy.solveset(expr, atom)
        return cls._Solution(solutionSet)
    
    @classmethod
    def _interpretSolution(cls, solution):
        types = cls._solutionTypes
        if solution.type is types.NORMAL:
            return set(solution.set)
        elif solution.type is types.COMPLEXES:
            # this means a variable can be any value and still hold true in the relation,
            # which ultimately means the relation provided no new information for the symbol
            return None
        elif solution.type is types.EMPTY:
            # similar to the above case, except we ended up with some kind of
            # invalid/impossible relation, a "4 = 0 case" (say, 1 + 3*(b + 1)/(b + 1))
            return set()
        elif solution.type is types.COMPLEMENT:
            if solution.set.args[0] is not sympy.Complexes:
                # this happens when the solver is forced to put a variable in the denominator of a fraction;
                # this generates a solution with (calculus) "holes", which can be ignored
                # (happens in cases like solving a/b - 4 for b)
                return set(solution.set.args[0])
            elif solution.set.args[0] is sympy.Complexes:
                # this happens in cases similar to the above, except sort of reversed;
                # here, the solver found that anything is possible *except* for certain
                # "holes", which are actually the solutions (TODO: example case needed)
                return set(solution.set.args[1])
    
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
            types = _SympySolveTools._solutionTypes
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

        def reverseSubstitutionOfNumeric(self, subsDict: dict):
            self._solutionSet = self._performSubsOnSet(self._solutionSet, subsDict)

        def _performSubsOnSet(self, sympySet, subsDict):
            types = _SympySolveTools._solutionTypes
            setType = self._getSetType(sympySet)
            if setType is types.NORMAL:
                returnSet = sympy.FiniteSet(*(
                    expr.subs(subsDict)
                    for expr in sympySet
                ))
            elif setType is types.EMPTY:
                # there is nothing to substitute in the empty set {}
                returnSet = sympySet
            elif setType is types.COMPLEXES:
                # sort of like the above case, except it's everything
                returnSet = sympySet
            elif setType is types.COMPLEMENT:
                (mainSet, complementSet) = sympySet.args
                mainSetSubbed = self._performSubsOnSet(mainSet, subsDict)
                complementSetSubbed = self._performSubsOnSet(complementSet, subsDict)
                return sympy.Complement(mainSetSubbed, complementSetSubbed)
            elif setType is types.CONDITIONAL:
                (symbol, eqCondition, baseSet) = sympySet.args
                assert type(eqCondition) is sympy.Eq, "sympy ConditionSet was assumed to always have Eq() as the second argument"
                (eqLeft, eqRight) = eqCondition.args
                symbolSubbed = symbol.subs(subsDict)
                if isNumeric(symbolSubbed):
                    # ConditionSets really don't like numerics as their first arg... this gets around that
                    # (of course, this means the extractor will need to convert it back later...)
                    # TODO: create NumericSymbol class
                    symbolSubbed = NumericSymbol(symbolSubbed)
                eqConditionSubbed = sympy.Eq(eqLeft.subs(subsDict), eqRight.subs(subsDict))
                baseSetSubbed = self._performSubsOnSet(baseSet, subsDict)
                return sympy.ConditionSet(symbolSubbed, eqConditionSubbed, baseSetSubbed)
            else:
                raise NotImplementedError("Tried to substitute the set for an unconsidered solution type")
            
            assert not any(symbolKey in expr.atoms() for expr in returnSet for symbolKey in subsDict)
            return returnSet
