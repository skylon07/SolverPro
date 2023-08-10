import sympy

from src.algebrasolver.solver import AlgebraSolver, ConditionalValue

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
        
    def testSolverSubstitutesKnownVariables(self):
        solver = AlgebraSolver()
        solver.recordRelation(a, 4)
        solver.recordRelation(b, 3)
        solver.recordRelation(c, 7)
        assert solver.substituteKnownsFor(a) == {4}, \
            "Solver did not correctly substitute single variable expression"
        assert solver.substituteKnownsFor(a + b) == {7}, \
            "Solver did not correctly substitute double variable expression"
        assert solver.substituteKnownsFor(a**(b - 1) - c) == {9}, \
            "Solver did not correctly substitute complicated expression"
        assert solver.substituteKnownsFor(a*c + b*d) == {3*d + 28}, \
            "Solver did not correctly substitute expression with leftover variable"
        
    def testSolverSubstitutesConditionalsCorrectly(self):
        solver1 = AlgebraSolver()
        solver1.recordRelation(a**2, 9)
        solver1.recordRelation(a + b, 7)
        assert solver1.substituteKnownsFor(a - b) == {-1, -13} and \
            solver1.substituteKnownsWithConditions(a - b) == {
                ConditionalValue(-1, {a: 3, b: 4}),
                ConditionalValue(-13, {a: -3, b: 10}),
            }, \
            "Solver did not correctly substitute valid combinations (by subtraction) of two related symbols"
        assert solver1.substituteKnownsFor(a * b) == {-30, 12} and \
            solver1.substituteKnownsWithConditions(a * b) == {
                ConditionalValue(12, {a: 3, b: 4}),
                ConditionalValue(-30, {a: -3, b: 10}),
            }, \
            "Solver did not correctly substitute valid combinations (by multiplication) of two related symbols"
        assert solver1.substituteKnownsFor(a + b) == {7} and \
            solver1.substituteKnownsWithConditions(a + b) == {
                ConditionalValue(7, {a: 3, b: 4}),
                ConditionalValue(7, {a: -3, b: 10}),
            }, \
            "Solver did not correctly substitute and condense the value of two related symbols"

        # TODO: more cases

    # TODO: edge cases and error throwing tests
