import sympy

from src.algebramaster.solver import AlgebraSolver, _SympySolveTools


(a, b, c, two) = sympy.symbols("a, b, c, two")


class SympySolveToolsTester:
    def testReverseSubstituteForBadNumerics(self):
        expr = a + b**two
        equation = 2 - expr
        solution = _SympySolveTools._Solution(sympy.solveset(equation, 2))
        solution.reverseSubstitutionOfNumeric({two: 2})
        assert solution.set == sympy.FiniteSet(a + b**2)

    def testSolveSetPerformsSolving(self):
        expr = a + b*c - 4
        
        actualSolution1 = {4}
        toolsSolution1 = _SympySolveTools.solveSet(expr, a + b*c)
        assert toolsSolution1 == actualSolution1

        actualSolution2 = {b*c}
        toolsSolution2 = _SympySolveTools.solveSet(expr, -(a - 4))
        assert toolsSolution2 == actualSolution2

    def testSolveSetSolvesForNumerics(self):
        expr = a + b**2 - 2
        
        actualSolution1 = {a + b**2}
        toolsSolution1 = _SympySolveTools.solveSet(expr, 2)
        assert toolsSolution1 == actualSolution1
