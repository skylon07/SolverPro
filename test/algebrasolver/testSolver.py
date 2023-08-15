import sympy

from src.common.functions import runForError
from src.algebrasolver.solver import AlgebraSolver, ConditionalValue, Relation, ContradictionException, NoSolutionException


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
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(-13, {
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10,
                }),
            }, \
            "Solver did not correctly substitute valid combinations (by subtraction) of two related symbols"
        
        assert solver1.substituteKnownsFor(sympy.parse_expr("a * b")) == {-30, 12} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a * b")) == {
                ConditionalValue(12, {
                    sympy.parse_expr("a"): 3,
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(-30, {
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10,
                }),
            }, \
            "Solver did not correctly substitute valid combinations (by multiplication) of two related symbols"
        
        assert solver1.substituteKnownsFor(sympy.parse_expr("a + b")) == {7} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a + b")) == {
                ConditionalValue(7, {
                    sympy.parse_expr("a"): 3,
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(7, {
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10,
                }),
            }, \
            "Solver did not correctly substitute and condense the value of two related symbols"

        solver2 = AlgebraSolver()
        
        solver2.recordRelation(Relation(sympy.parse_expr("a**2 + b**2"), sympy.parse_expr("c**2")))
        solver2.recordRelation(Relation(sympy.parse_expr("a**2"), sympy.parse_expr("9")))
        solver2.recordRelation(Relation(sympy.parse_expr("c**2"), sympy.parse_expr("25")))
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("a**2")) == {9} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a**2")) == {
                ConditionalValue(9, {
                    sympy.parse_expr("a"): 3,
                }),
                ConditionalValue(9, {
                    sympy.parse_expr("a"): -3,
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {-3, 3} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a")) == {
                ConditionalValue(3, {
                    sympy.parse_expr("a"): 3,
                }),
                ConditionalValue(-3, {
                    sympy.parse_expr("a"): -3,
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("b**2")) == {16} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("b**2")) == {
                ConditionalValue(16, {
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(16, {
                    sympy.parse_expr("b"): -4,
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("b")) == {-4, 4} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("b")) == {
                ConditionalValue(4, {
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(-4, {
                    sympy.parse_expr("b"): -4,
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("c**2")) == {25} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("c**2")) == {
                ConditionalValue(25, {
                    sympy.parse_expr("c"): 5,
                }),
                ConditionalValue(25, {
                    sympy.parse_expr("c"): -5,
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("c")) == {-5, 5} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("c")) == {
                ConditionalValue(5, {
                    sympy.parse_expr("c"): 5,
                }),
                ConditionalValue(-5, {
                    sympy.parse_expr("c"): -5,
                }),
            }

    def testSolverCatchesRedundantRelations(self):
        solver1 = AlgebraSolver()
        
        isRedundant1_1 = solver1.recordRelation(Relation(sympy.parse_expr("a"), 12))
        assert isRedundant1_1 is False, \
            "Solver claimed new relation was redundant"
        
        isRedundant2_1 = solver1.recordRelation(Relation(sympy.parse_expr("a"), 12))
        assert isRedundant2_1 is True, \
            "Solver claimed redundant relation was needed"

        solver2 = AlgebraSolver()
        
        isRedundant1_2 = solver2.recordRelation(Relation(sympy.parse_expr("a**2"), 9))
        assert isRedundant1_2 is False, \
            "Solver claimed new conditional relation was redundant"
        
        isRedundant2_2 = solver2.recordRelation(Relation(sympy.parse_expr("a**2"), 9))
        assert isRedundant2_2 is True, \
            "Solver claimed redundant conditional relation was needed"

    def testSolverDetectsContradictions(self):
        solver = AlgebraSolver()
        
        solver.recordRelation(Relation(sympy.parse_expr("a"), 3))
        def recordContradiction1():
            solver.recordRelation(Relation(sympy.parse_expr("a"), 4))
        error1 = runForError(recordContradiction1)
        
        assert type(error1) is ContradictionException
        assert list(error1.poorSymbols) == [], \
            "Solver should not have any implementation for offended symbols (yet) in single-var case"
        assert error1.badRelation == Relation(sympy.parse_expr("a"), 4), \
            "Solver found contradiction in the wrong relation for single-var case"
        
        solver.recordRelation(Relation(sympy.parse_expr("b"), 8))
        def recordNonContradiction2():
            solver.recordRelation(Relation(sympy.parse_expr("b**2"), 64))
        error2 = runForError(recordNonContradiction2)
        
        assert error2 is None, \
            "Solver should not find a contradiction after adding a redundant relation (just with more solutions)"
        
        solver.recordRelation(Relation(sympy.parse_expr("c**2"), 25))
        def recordNonContradiction3():
            solver.recordRelation(Relation(sympy.parse_expr("c"), 5))
        error3 = runForError(recordNonContradiction3)
        
        assert error3 is None, \
            "Solver should not find a contradiction when restricting known values"
        
        solver.recordRelation(Relation(sympy.parse_expr("x + y"), 4))
        solver.recordRelation(Relation(sympy.parse_expr("x - y"), 4))
        def recordContradiction4():
            solver.recordRelation(Relation(sympy.parse_expr("x"), 1))
        error4 = runForError(recordContradiction4)
        
        assert type(error4) is ContradictionException
        assert list(error4.poorSymbols) == [], \
            "Solver should not have any implementation for offended symbols (yet) in two-var case"
        assert error4.badRelation == Relation(sympy.parse_expr("x"), 1), \
            "Solver found contradiction in the wrong relation for two-var case"
        
    def testSolverCanRestrictSolutions(self):
        solver1 = AlgebraSolver()

        solver1.recordRelation(Relation(sympy.parse_expr("a**2"), 16))
        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {-4, 4}

        solver1.recordRelation(Relation(sympy.parse_expr("a"), 4))
        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {4}, \
            "Solver did not restrict known values for new relation"
        
        solver2 = AlgebraSolver()

        solver2.recordRelation(Relation(sympy.parse_expr("a**2 + b"), 6))
        solver2.recordRelation(Relation(sympy.parse_expr("b"), 2))
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {-2, 2} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a")) == {
                ConditionalValue(-2, {
                    sympy.parse_expr("a"): -2,
                }),
                ConditionalValue(2, {
                    sympy.parse_expr("a"): 2,
                }),
            }
        
        solver2.recordRelation(Relation(sympy.parse_expr("a"), -2))
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {-2} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a")) == {
                ConditionalValue(-2, {
                    sympy.parse_expr("a"): -2,
                }),
            }, "Solver did not restrict known values (and conditionals) for new relation"
    
    def testSolverResetsOnError(self):
        pass # TODO

    # TODO: tests for robustness from old solver pro
