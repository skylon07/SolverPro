import sympy

from src.algebrasolver.solver import AlgebraSolver

(a, b, c, d) = sympy.symbols("a, b, c, d")

class AlgebraSolverTester:
    def testSolverConvertsRelations(self):
        solver = AlgebraSolver()
        relation = solver.toRelation(a, b)
        assert relation == a - b, \
            "Solver did not correctly convert two expressions to single expression equal to zero"
    
    def testSolverRecordsRelations(self):
        solver = AlgebraSolver()
        solver.recordRelation(2*a, b + c)
        assert solver._recordedRelations == [2*a - (b + c)], \
            "Solver did not record relation as a single expression equal to zero"

    def testSolverInfersSingleVariableValues(self):
        solver1 = AlgebraSolver()
        solver1.recordRelation(a, 4)
        assert solver1._symbolValues == {a: {4}}, \
            "Solver did not record single variable value from equality"
        
        solver2 = AlgebraSolver()
        solver2.recordRelation(b, 5)
        solver2.recordRelation(3, c)
        assert solver2._symbolValues == {b: {5}, c: {3}}, \
            "Solver did not record multiple variables from variable-value equalities"
        
    def testSolverSubstitutesKnownVariables(self):
        solver = AlgebraSolver()
        solver.recordRelation(a, 4)
        solver.recordRelation(b, 3)
        solver.recordRelation(c, 7)
        assert list(solver.substituteKnownsFor(a)) == [4], \
            "Solver did not correctly substitute single variable expression"
        assert list(solver.substituteKnownsFor(a + b)) == [7], \
            "Solver did not correctly substitute double variable expression"
        assert list(solver.substituteKnownsFor(a**(b - 1) - c)) == [9], \
            "Solver did not correctly substitute complicated expression"
        assert list(solver.substituteKnownsFor(a*c + b*d)) == [3*d + 28], \
            "Solver did not correctly substitute expression with leftover variable"

    def testSolverInfersVariableSolutions(self):
        solver1 = AlgebraSolver()
        solver1.recordRelation(2*b, 8)
        assert solver1._symbolValues == {b: {4}}, \
            "Solver did not correctly solve simple single variable relation"

        solver2 = AlgebraSolver()
        solver2.recordRelation(9, a**2)
        assert solver2._symbolValues == {a: {3, -3}}, \
            "Solver did not correctly solve exponent single variable relation"

        solver3 = AlgebraSolver()
        solver3.recordRelation(a, 2*b)
        solver3.recordRelation(b, 5)
        assert solver3._symbolValues == {a: {10}, b: {5}}, \
            "Solver did not correctly infer value of second related variable from the first"
        
        solver4 = AlgebraSolver()
        solver4.recordRelation(a**2, 4)
        solver4.recordRelation(a + b, 5)
        assert solver4._symbolValues == {a: {2, -2}, b: {3, 7}}, \
            "Solver did not correctly infer multiple values from relation with multiple outcomes"

    # TODO: edge cases and error throwing tests
