import sympy

from src.algebrasolver.solver import AlgebraSolver, ConditionalValue, Relation


class AlgebraSolverTester:
    def testSolverRecordsRelations(self):
        solver = AlgebraSolver()
        solver.recordRelation(Relation(sympy.parse_expr("2*a"), sympy.parse_expr("b + c")))
        assert solver._recordedRelations == [Relation(sympy.parse_expr("2*a"), sympy.parse_expr("b + c"))], \
            "Solver did not record relation as a single expression equal to zero"
        
    def testSolverSubstitutesKnownVariables(self):
        solver = AlgebraSolver()
        solver.recordRelation(Relation(sympy.parse_expr("a"), 4))
        solver.recordRelation(Relation(sympy.parse_expr("b"), 3))
        solver.recordRelation(Relation(sympy.parse_expr("c"), 7))
        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {4}, \
            "Solver did not correctly substitute single variable expression"
        assert solver.substituteKnownsFor(sympy.parse_expr("a + b")) == {7}, \
            "Solver did not correctly substitute double variable expression"
        assert solver.substituteKnownsFor(sympy.parse_expr("a**(b - 1) - c")) == {9}, \
            "Solver did not correctly substitute complicated expression"
        assert solver.substituteKnownsFor(sympy.parse_expr("a*c + b*d")) == {sympy.parse_expr("3*d + 28")}, \
            "Solver did not correctly substitute expression with leftover variable"
        
    def testSolverSubstitutesConditionalsCorrectly(self):
        solver1 = AlgebraSolver()
        solver1.recordRelation(Relation(sympy.parse_expr("a**2"), 9))
        solver1.recordRelation(Relation(sympy.parse_expr("a + b"), 7))
        assert solver1.substituteKnownsFor(sympy.parse_expr("a - b")) == {-1, -13} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a - b")) == {
                ConditionalValue(-1, {
                    sympy.parse_expr("a"): 3,
                    sympy.parse_expr("b"): 4}
                ),
                ConditionalValue(-13, {
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10}
                ),
            }, \
            "Solver did not correctly substitute valid combinations (by subtraction) of two related symbols"
        assert solver1.substituteKnownsFor(sympy.parse_expr("a * b")) == {-30, 12} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a * b")) == {
                ConditionalValue(12, {
                    sympy.parse_expr("a"): 3,
                    sympy.parse_expr("b"): 4}
                ),
                ConditionalValue(-30, {
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10}
                ),
            }, \
            "Solver did not correctly substitute valid combinations (by multiplication) of two related symbols"
        assert solver1.substituteKnownsFor(sympy.parse_expr("a + b")) == {7} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a + b")) == {
                ConditionalValue(7, {
                    sympy.parse_expr("a"): 3,
                    sympy.parse_expr("b"): 4}
                ),
                ConditionalValue(7, {
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10}
                ),
            }, \
            "Solver did not correctly substitute and condense the value of two related symbols"

        # TODO: more cases

    # TODO: error throwing tests
    
    def testSolverResetsOnError(self):
        pass # TODO

    # TODO: tests for robustness from old solver pro
