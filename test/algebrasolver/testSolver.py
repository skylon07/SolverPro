import sympy

from src.common.functions import runForError
from src.common.sympyLinterFixes import createSymbol
from src.algebrasolver.solver import AlgebraSolver, ConditionalValue, Relation, ContradictionException, NoSolutionException


class AlgebraSolverTester:
    def testRecordsRelations(self):
        solver = AlgebraSolver()
        solver.recordRelation(Relation(sympy.parse_expr("2*a"), sympy.parse_expr("b + c")))
        assert solver._recordedRelations == [Relation(sympy.parse_expr("2*a"), sympy.parse_expr("b + c"))], \
            "Solver did not record relation as a single expression equal to zero"
        
    def testSubstitutesKnownVariables(self):
        solver = AlgebraSolver()
        
        solver.recordRelation(Relation(sympy.parse_expr("a"), 4)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("b"), 3)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("c"), 7)) # type: ignore
        
        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {4}, \
            "Solver did not correctly substitute single variable expression"
        assert solver.substituteKnownsFor(sympy.parse_expr("a + b")) == {7}, \
            "Solver did not correctly substitute double variable expression"
        assert solver.substituteKnownsFor(sympy.parse_expr("a**(b - 1) - c")) == {9}, \
            "Solver did not correctly substitute complicated expression"
        assert solver.substituteKnownsFor(sympy.parse_expr("a*c + b*d")) == {sympy.parse_expr("3*d + 28")}, \
            "Solver did not correctly substitute expression with leftover variable"
        
    def testSubstitutesConditionalsCorrectly(self):
        solver1 = AlgebraSolver()
        
        solver1.recordRelation(Relation(sympy.parse_expr("a**2"), 9)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("a + b"), 7)) # type: ignore
        
        assert solver1.substituteKnownsFor(sympy.parse_expr("a - b")) == {-1, -13} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a - b")) == {
                ConditionalValue(-1, { # type: ignore
                    sympy.parse_expr("a"): 3,
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(-13, { # type: ignore
                    sympy.parse_expr("a"): -3,
                    sympy.parse_expr("b"): 10,
                }),
            }, \
            "Solver did not correctly substitute valid combinations (by subtraction) of two related symbols"
        
        assert solver1.substituteKnownsFor(sympy.parse_expr("a * b")) == {-30, 12} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a * b")) == {
                ConditionalValue(12, {
                    sympy.parse_expr("a"): 3, # type: ignore
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(-30, {
                    sympy.parse_expr("a"): -3, # type: ignore
                    sympy.parse_expr("b"): 10,
                }),
            }, \
            "Solver did not correctly substitute valid combinations (by multiplication) of two related symbols"
        
        assert solver1.substituteKnownsFor(sympy.parse_expr("a + b")) == {7} and \
            solver1.substituteKnownsWithConditions(sympy.parse_expr("a + b")) == {
                ConditionalValue(7, {
                    sympy.parse_expr("a"): 3, # type: ignore
                    sympy.parse_expr("b"): 4,
                }),
                ConditionalValue(7, {
                    sympy.parse_expr("a"): -3, # type: ignore
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
                    sympy.parse_expr("a"): 3, # type: ignore
                }),
                ConditionalValue(9, {
                    sympy.parse_expr("a"): -3, # type: ignore
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {-3, 3} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a")) == {
                ConditionalValue(3, {
                    sympy.parse_expr("a"): 3, # type: ignore
                }),
                ConditionalValue(-3, {
                    sympy.parse_expr("a"): -3, # type: ignore
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("b**2")) == {16} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("b**2")) == {
                ConditionalValue(16, {
                    sympy.parse_expr("b"): 4, # type: ignore
                }),
                ConditionalValue(16, {
                    sympy.parse_expr("b"): -4, # type: ignore
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("b")) == {-4, 4} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("b")) == {
                ConditionalValue(4, {
                    sympy.parse_expr("b"): 4, # type: ignore
                }),
                ConditionalValue(-4, {
                    sympy.parse_expr("b"): -4, # type: ignore
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("c**2")) == {25} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("c**2")) == {
                ConditionalValue(25, {
                    sympy.parse_expr("c"): 5, # type: ignore
                }),
                ConditionalValue(25, {
                    sympy.parse_expr("c"): -5, # type: ignore
                }),
            }
        
        assert solver2.substituteKnownsFor(sympy.parse_expr("c")) == {-5, 5} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("c")) == {
                ConditionalValue(5, {
                    sympy.parse_expr("c"): 5, # type: ignore
                }),
                ConditionalValue(-5, {
                    sympy.parse_expr("c"): -5, # type: ignore
                }),
            }
        
    def testSolvesByBackSubstitution(self):
        # previously, the solver could only solve for variables in relations
        # with a single unknown; this test case proves the true power of Solver Pro!
        solver = AlgebraSolver()
        
        # three friends wish to split their money proportionally with each other
        # to pay for a project they are working on
        solver.recordRelation(Relation(sympy.parse_expr("projectCost"), 500)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("alexBalance"), 300)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("bobBalance"), 200)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("jakeBalance"), 500)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("alexContribution/alexBalance"), sympy.parse_expr("bobContribution/bobBalance"))) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("bobContribution/bobBalance"), sympy.parse_expr("jakeContribution/jakeBalance"))) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("alexContribution + bobContribution + jakeContribution"), sympy.parse_expr("projectCost"))) # type: ignore

        assert solver.substituteKnownsFor(sympy.parse_expr("alexContribution")) == {150}
        assert solver.substituteKnownsFor(sympy.parse_expr("bobContribution")) == {100}
        assert solver.substituteKnownsFor(sympy.parse_expr("jakeContribution")) == {250}
        
    def testHandlesComplexValues(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("a**2"), -4)) # type: ignore

        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {
            sympy.parse_expr("-2*I"),
            sympy.parse_expr("2*I"),
        }

    def testGetsRelationsInOrder(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("a"), 1)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("b + c"), 2)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("c"), 3)) # type: ignore

        assert solver.getRelations() == (
            Relation(sympy.parse_expr("a"), 1),  # type: ignore
            Relation(sympy.parse_expr("b + c"), 2), # type: ignore
            Relation(sympy.parse_expr("c"), 3), # type: ignore
        )
        
    def testGetsSymbolValues(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("a"), 5)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("b**2"), 4)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("c + b"), 5)) # type: ignore

        assert solver.getSymbolConditionalValues(sympy.parse_expr("a")) == {
            ConditionalValue(5, dict()),
        }, "Solver did not return correct values for a symbol with one value"
        assert solver.getSymbolConditionalValues(sympy.parse_expr("b")) == {
            ConditionalValue(-2, dict()),
            ConditionalValue(2, dict()),
        }, "Solver did not return correct values for a symbol with two values"
        assert solver.getSymbolConditionalValues(sympy.parse_expr("c")) == {
            ConditionalValue(3, { 
                sympy.parse_expr("b"): 2, # type: ignore
            }),
            ConditionalValue(7, {
                sympy.parse_expr("b"): -2, # type: ignore
            }),
        }, "Solver did not return correct values for a symbol with two conditional values"
        assert solver.getSymbolConditionalValues(sympy.parse_expr("nonexistant")) is None

    def testFindsRelationsWithSymbol(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("a + d"), 14)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("b**2 - c"), 8)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("2*c - d"), 9)) # type: ignore

        assert solver.getRelationsWithSymbol(sympy.parse_expr("a")) == (
            Relation(sympy.parse_expr("a + d"), 14), # type: ignore
        ), "Solver did not retrieve correct relations (case 1)"
        assert solver.getRelationsWithSymbol(sympy.parse_expr("b")) == (
            Relation(sympy.parse_expr("b**2 - c"), 8), # type: ignore
        ), "Solver did not retrieve correct relations (case 2)"
        assert solver.getRelationsWithSymbol(sympy.parse_expr("c")) == (
            Relation(sympy.parse_expr("b**2 - c"), 8), # type: ignore
            Relation(sympy.parse_expr("2*c - d"), 9), # type: ignore
        ), "Solver should preserve relations in order of recording (case 1)"
        assert solver.getRelationsWithSymbol(sympy.parse_expr("d")) == (
            Relation(sympy.parse_expr("a + d"), 14), # type: ignore
            Relation(sympy.parse_expr("2*c - d"), 9), # type: ignore
        ), "Solver should preserve relations in order of recording (case 2)"
        assert solver.getRelationsWithSymbol(sympy.parse_expr("nonexistant")) == tuple()

    def testCatchesRedundantRelations(self):
        solver1 = AlgebraSolver()
        
        isRedundant1_1 = solver1.recordRelation(Relation(sympy.parse_expr("a"), 12)) # type: ignore
        assert isRedundant1_1 is False, \
            "Solver claimed new relation was redundant"
        
        isRedundant2_1 = solver1.recordRelation(Relation(sympy.parse_expr("a"), 12)) # type: ignore
        assert isRedundant2_1 is True, \
            "Solver claimed redundant relation was needed"

        solver2 = AlgebraSolver()
        
        isRedundant1_2 = solver2.recordRelation(Relation(sympy.parse_expr("a**2"), 9)) # type: ignore
        assert isRedundant1_2 is False, \
            "Solver claimed new conditional relation was redundant"
        
        isRedundant2_2 = solver2.recordRelation(Relation(sympy.parse_expr("a**2"), 9)) # type: ignore
        assert isRedundant2_2 is True, \
            "Solver claimed redundant conditional relation was needed"

        solver3 = AlgebraSolver()
        
        isRedundant1_3 = solver3.recordRelation(Relation(sympy.parse_expr("a + c"), sympy.parse_expr("a + c")))
        assert isRedundant1_3 is True, \
            "Solver claimed symmetrical relation was not redundant"
        
        solver4 = AlgebraSolver()

        isRedundant1_4 = solver4.recordRelation(Relation(sympy.parse_expr("a"), createSymbol("{1, 2}")))
        assert isRedundant1_4 is False
        
        isRedundant2_4 = solver4.recordRelation(Relation(sympy.parse_expr("a"), createSymbol("{1, 2}")))
        assert isRedundant2_4 is True

    def testDetectsContradictions(self):
        solver = AlgebraSolver()
        
        solver.recordRelation(Relation(sympy.parse_expr("a"), 3)) # type: ignore
        def recordContradiction1():
            solver.recordRelation(Relation(sympy.parse_expr("a"), 4)) # type: ignore
        error1 = runForError(recordContradiction1)
        
        assert type(error1) is ContradictionException
        assert error1.poorSymbolValues == { # type: ignore
            sympy.parse_expr("a"): {3},
        }, "Solver did not find correct contradicting symbols in single-var case"
        assert error1.contradictingRelation == Relation(
            sympy.parse_expr("a"), 4 # type: ignore
        ), "Solver found contradiction in the wrong relation for single-var case"
        
        solver.recordRelation(Relation(sympy.parse_expr("b"), 8)) # type: ignore
        def recordNonContradiction2():
            solver.recordRelation(Relation(sympy.parse_expr("b**2"), 64)) # type: ignore
        error2 = runForError(recordNonContradiction2)
        
        assert error2 is None, \
            "Solver should not find a contradiction after adding a redundant relation (just with more solutions)"
        
        solver.recordRelation(Relation(sympy.parse_expr("c**2"), 25)) # type: ignore
        def recordNonContradiction3():
            solver.recordRelation(Relation(sympy.parse_expr("c"), 5)) # type: ignore
        error3 = runForError(recordNonContradiction3)
        
        assert error3 is None, \
            "Solver should not find a contradiction when restricting known values"
        
        solver.recordRelation(Relation(sympy.parse_expr("x + y + z"), 6)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("x - y + z"), 6)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("z"), 2)) # type: ignore
        def recordContradiction4():
            solver.recordRelation(Relation(sympy.parse_expr("x"), 1)) # type: ignore
        error4 = runForError(recordContradiction4)
        
        assert type(error4) is ContradictionException
        assert error4.poorSymbolValues == {
            sympy.parse_expr("x"): {4},
        }, "Solver did not recognize contradiction after forward substitution of two variables"
        assert error4.contradictingRelation == Relation(
            sympy.parse_expr("x"), 1 # type: ignore
        ), "Solver found contradiction in the wrong relation for two-var case"

    def testFindsContradictionsWithExpressionLists(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("a"), createSymbol("{1, 2}")))
        solver.recordRelation(Relation(sympy.parse_expr("b"), createSymbol("{4, 8}")))
        solver.recordRelation((Relation(sympy.parse_expr("c"), createSymbol("{1, 2, 3, 4}"))))
        solver.recordRelation((Relation(sympy.parse_expr("d"), sympy.parse_expr("c"))))

        def recordContradiction1():
            solver.recordRelation(Relation(sympy.parse_expr("a"), createSymbol("{1, 2, 3}")))
        error1 = runForError(recordContradiction1)
        
        assert type(error1) is ContradictionException
        assert error1.poorSymbolValues == {
            sympy.parse_expr("a"): {1, 2},
        }
        assert error1.contradictingRelation == Relation(sympy.parse_expr("a"), createSymbol("{1, 2, 3}")), \
            "Solver did not find a contradiction in solutions with extra values"

        def recordContradiction2():
            solver.recordRelation(Relation(sympy.parse_expr("b"), 4)) # type: ignore
        error2 = runForError(recordContradiction2)
        
        assert type(error2) is ContradictionException
        assert error2.poorSymbolValues == {
            sympy.parse_expr("b"): {4, 8},
        }
        assert error2.contradictingRelation == Relation(sympy.parse_expr("b"), 4) # type: ignore

        def recordContradiction3():
            solver.recordRelation(Relation(sympy.parse_expr("d"), createSymbol("{2, 3}")))
        error3 = runForError(recordContradiction3)

        assert type(error3) is ContradictionException
        assert error3.poorSymbolValues == {
            sympy.parse_expr("d"): {1, 2, 3, 4}
        }
        assert error3.contradictingRelation == Relation(sympy.parse_expr("d"), createSymbol("{2, 3}"))
        
    def testSolutionRestricting(self):
        solver1 = AlgebraSolver()

        solver1.recordRelation(Relation(sympy.parse_expr("a**2"), 16)) # type: ignore
        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {-4, 4}

        solver1.recordRelation(Relation(sympy.parse_expr("a"), 4)) # type: ignore
        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {4}, \
            "Solver did not restrict known values for new relation"
        
        solver2 = AlgebraSolver()

        solver2.recordRelation(Relation(sympy.parse_expr("a**2 + b"), 6)) # type: ignore
        solver2.recordRelation(Relation(sympy.parse_expr("b"), 2)) # type: ignore
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {-2, 2} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a")) == {
                ConditionalValue(-2, {
                    sympy.parse_expr("a"): -2, # type: ignore
                }),
                ConditionalValue(2, {
                    sympy.parse_expr("a"): 2, # type: ignore
                }),
            }
        
        solver2.recordRelation(Relation(sympy.parse_expr("a"), -2)) # type: ignore
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {-2} and \
            solver2.substituteKnownsWithConditions(sympy.parse_expr("a")) == {
                ConditionalValue(-2, {
                    sympy.parse_expr("a"): -2, # type: ignore
                }),
            }, "Solver did not restrict known values (and conditionals) for new relation"
        
        solver3 = AlgebraSolver()

        solver3.recordRelation(Relation(sympy.parse_expr("a**2"), 4)) # type: ignore
        solver3.recordRelation(Relation(sympy.parse_expr("(a + b)**2"), 9)) # type: ignore
        assert solver3.substituteKnownsFor(sympy.parse_expr("b")) == {-5, -1, 1, 5}

        solver3.recordRelation(Relation(sympy.parse_expr("b"), createSymbol("{-1, 1, 5}")))
        assert solver3.substituteKnownsFor(sympy.parse_expr("b")) == {-1, 1, 5}, \
            "Solver did not restrict variable to multiple values *and* preserve its conditions"
        
        solver4 = AlgebraSolver()

        solver4.recordRelation(Relation(sympy.parse_expr("a**2"), 4)) # type: ignore
        solver4.recordRelation(Relation(sympy.parse_expr("(a + b)**2"), 16)) # type: ignore
        assert solver4.substituteKnownsFor(sympy.parse_expr("b")) == {-6, -2, 2, 6}
        assert solver4.substituteKnownsFor(sympy.parse_expr("b**a")) == {
            sympy.parse_expr("36"),     # (-6)^2
            sympy.parse_expr("1/4"),    # (-2)^-2
            sympy.parse_expr("4"),      # (2)^2
            sympy.parse_expr("1/36"),   # (6)^-2
        }

        solver4.recordRelation(Relation(sympy.parse_expr("b"), createSymbol("{-6, 2}")))
        assert solver4.substituteKnownsFor(sympy.parse_expr("b**a")) == {36, 4}, \
            "Solver did not correctly substitute only valid combinations of variables in multi-conditional expression"
    
    def testResetsOnBadRecord(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("v"), 2)) # type: ignore
        
        assert solver.substituteKnownsWithConditions(sympy.parse_expr("v")) == {
            ConditionalValue(2, {
                sympy.parse_expr("v"): 2, # type: ignore
            }),
        }
        
        def attemptContradiction1():
            solver.recordRelation(Relation(sympy.parse_expr("v"), 5)) # type: ignore
        error1 = runForError(attemptContradiction1)

        assert type(error1) is ContradictionException
        assert solver.substituteKnownsWithConditions(sympy.parse_expr("v")) == {
            ConditionalValue(2, {
                sympy.parse_expr("v"): 2, # type: ignore
            }),
        }, "Solver should retain old value after bad variable relation"

        solver.recordRelation(Relation(sympy.parse_expr("a + b + c"), 5)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("a - b + c"), 5)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("c"), 1)) # type: ignore

        assert solver.substituteKnownsWithConditions(sympy.parse_expr("c")) == {
            ConditionalValue(1, {
                sympy.parse_expr("c"): 1, # type: ignore
            }),
        }
        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {4}
        assert solver.substituteKnownsFor(sympy.parse_expr("b")) == {0}

        def attemptContradiction2():
            solver.recordRelation(Relation(sympy.parse_expr("a"), 1)) # type: ignore
        error2 = runForError(attemptContradiction2)

        assert type(error2) is ContradictionException
        assert solver.substituteKnownsWithConditions(sympy.parse_expr("c")) == {
            ConditionalValue(1, {
                sympy.parse_expr("c"): 1, # type: ignore
            }),
        }
        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {4}, \
            "Solver should forget inferred values made from new relations that contradict later"
        assert solver.substituteKnownsFor(sympy.parse_expr("b")) == {0}, \
            "Solver should forget deeply inferred values made from new relations that contradict later"

        solver.recordRelation(Relation(sympy.parse_expr("x/(y - 2)"), 6)) # type: ignore

        assert solver.substituteKnownsWithConditions(sympy.parse_expr("x")) == {
            ConditionalValue(sympy.parse_expr("x"), dict()),
        }
        assert solver.substituteKnownsWithConditions(sympy.parse_expr("y")) == {
            ConditionalValue(sympy.parse_expr("y"), dict()),
        }

        def attemptUnsolvable3():
            solver.recordRelation(Relation(sympy.parse_expr("y"), 2)) # type: ignore
        error3 = runForError(attemptUnsolvable3)

        assert type(error3) is NoSolutionException
        assert solver.substituteKnownsWithConditions(sympy.parse_expr("x")) == {
            ConditionalValue(sympy.parse_expr("x"), dict()),
        }, "Solver should never record values for unsolvable variables"
        assert solver.substituteKnownsWithConditions(sympy.parse_expr("y")) == {
            ConditionalValue(sympy.parse_expr("y"), dict()),
        }, "Solver should forget inferred values after finding an unsolvable variable"

    def testRelationPopping(self):
        solver = AlgebraSolver()

        solver.recordRelation(Relation(sympy.parse_expr("a"), 1)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("b"), 2)) # type: ignore
        solver.recordRelation(Relation(sympy.parse_expr("c"), 3)) # type: ignore

        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {1}
        assert solver.substituteKnownsFor(sympy.parse_expr("b")) == {2}
        assert solver.substituteKnownsFor(sympy.parse_expr("c")) == {3}

        solver.popRelation(Relation(sympy.parse_expr("a"), 1)) # type: ignore

        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {sympy.parse_expr("a")}
        assert solver.substituteKnownsFor(sympy.parse_expr("b")) == {2}
        assert solver.substituteKnownsFor(sympy.parse_expr("c")) == {3}

        solver.popRelation(Relation(sympy.parse_expr("b"), 2)) # type: ignore

        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {sympy.parse_expr("a")}
        assert solver.substituteKnownsFor(sympy.parse_expr("b")) == {sympy.parse_expr("b")}
        assert solver.substituteKnownsFor(sympy.parse_expr("c")) == {3}

        solver.popRelation(Relation(sympy.parse_expr("c"), 3)) # type: ignore

        assert solver.substituteKnownsFor(sympy.parse_expr("a")) == {sympy.parse_expr("a")}
        assert solver.substituteKnownsFor(sympy.parse_expr("b")) == {sympy.parse_expr("b")}
        assert solver.substituteKnownsFor(sympy.parse_expr("c")) == {sympy.parse_expr("c")}

    def testForgetsVariablesWhenRelationPops(self):
        solver1 = AlgebraSolver()

        solver1.recordRelation(Relation(sympy.parse_expr("a + b"), 3)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("c + d"), 7)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("c"), 3)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("b"), sympy.parse_expr("d / 2")))

        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {1}
        assert solver1.substituteKnownsFor(sympy.parse_expr("b")) == {2}
        assert solver1.substituteKnownsFor(sympy.parse_expr("c")) == {3}
        assert solver1.substituteKnownsFor(sympy.parse_expr("d")) == {4}

        solver1.popRelation(Relation(sympy.parse_expr("c"), 3)) # type: ignore

        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {sympy.parse_expr("a")}
        assert solver1.substituteKnownsFor(sympy.parse_expr("b")) == {sympy.parse_expr("b")}
        assert solver1.substituteKnownsFor(sympy.parse_expr("c")) == {sympy.parse_expr("c")}
        assert solver1.substituteKnownsFor(sympy.parse_expr("d")) == {sympy.parse_expr("d")}

        solver1.recordRelation(Relation(sympy.parse_expr("c"), 3)) # type: ignore

        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {1}
        assert solver1.substituteKnownsFor(sympy.parse_expr("b")) == {2}
        assert solver1.substituteKnownsFor(sympy.parse_expr("c")) == {3}
        assert solver1.substituteKnownsFor(sympy.parse_expr("d")) == {4}

        solver1.popRelation(Relation(sympy.parse_expr("b"), sympy.parse_expr("d / 2")))

        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {sympy.parse_expr("a")}
        assert solver1.substituteKnownsFor(sympy.parse_expr("b")) == {sympy.parse_expr("b")}
        assert solver1.substituteKnownsFor(sympy.parse_expr("c")) == {3}
        assert solver1.substituteKnownsFor(sympy.parse_expr("d")) == {4}

        # TODO: more cases...

    def testKeepsVariablesWhenPoppingRedundancy(self):
        solver1 = AlgebraSolver()

        solver1.recordRelation(Relation(sympy.parse_expr("2*a"), 4)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("3*a"), 6)) # type: ignore

        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {2}

        solver1.popRelation(Relation(sympy.parse_expr("2*a"), 4)) # type: ignore

        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {2}

        # TODO: more cases...
        
    def testForRobustness(self):
        # a + b = 4
        # a - b = 2
        solver1 = AlgebraSolver()
        solver1.recordRelation(Relation(sympy.parse_expr("a + b"), 4)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("a - b"), 2)) # type: ignore
        solver1.recordRelation(Relation(sympy.parse_expr("a"), 3)) # type: ignore
        # (a = 3)
        # (b = 1)
        assert solver1.substituteKnownsFor(sympy.parse_expr("a")) == {3}
        assert solver1.substituteKnownsFor(sympy.parse_expr("b")) == {1}
        
        # a + 2b + c = 20
        # -a = -4
        # 2a + c = 14
        solver2 = AlgebraSolver()
        solver2.recordRelation(Relation(sympy.parse_expr("a + 2*b + c"), 20)) # type: ignore
        solver2.recordRelation(Relation(sympy.parse_expr("-a"), -4)) # type: ignore
        solver2.recordRelation(Relation(sympy.parse_expr("2*a + c"), 14)) # type: ignore
        # (a = 4)
        # (b = 5)
        # (c = 6)
        assert solver2.substituteKnownsFor(sympy.parse_expr("a")) == {4}
        assert solver2.substituteKnownsFor(sympy.parse_expr("b")) == {5}
        assert solver2.substituteKnownsFor(sympy.parse_expr("c")) == {6}
        
        # a + b = 6
        # b - c = 7
        # c = d - 8
        # d + e = -7
        # 2 + -3*b = -10
        solver3 = AlgebraSolver()
        solver3.recordRelation(Relation(sympy.parse_expr("a + b"), 6)) # type: ignore
        solver3.recordRelation(Relation(sympy.parse_expr("b - c"), 7)) # type: ignore
        solver3.recordRelation(Relation(sympy.parse_expr("c"), sympy.parse_expr("d - 8")))
        solver3.recordRelation(Relation(sympy.parse_expr("d + e"), -7)) # type: ignore
        solver3.recordRelation(Relation(sympy.parse_expr("2 + -3*b"), -10)) # type: ignore
        # (a = 2)
        # (b = 4)
        # (c = -3)
        # (d = 5)
        # (e = -12)
        assert solver3.substituteKnownsFor(sympy.parse_expr("a")) == {2}
        assert solver3.substituteKnownsFor(sympy.parse_expr("b")) == {4}
        assert solver3.substituteKnownsFor(sympy.parse_expr("c")) == {-3}
        assert solver3.substituteKnownsFor(sympy.parse_expr("d")) == {5}
        assert solver3.substituteKnownsFor(sympy.parse_expr("e")) == {-12}

        # f = m * a
        # f = 80
        # m = 20
        solver4 = AlgebraSolver()
        solver4.recordRelation(Relation(sympy.parse_expr("f"), sympy.parse_expr("m*a")))
        solver4.recordRelation(Relation(sympy.parse_expr("f"), 80)) # type: ignore
        solver4.recordRelation(Relation(sympy.parse_expr("m"), 20)) # type: ignore
        # (f = 80)
        # (m = 20)
        # (a = 4)
        assert solver4.substituteKnownsFor(sympy.parse_expr("f")) == {80}
        assert solver4.substituteKnownsFor(sympy.parse_expr("m")) == {20}
        assert solver4.substituteKnownsFor(sympy.parse_expr("a")) == {4}

        # k1i = 1125
        # k2i = 800
        # k1f = 125
        # kt = 1925
        # k2f = 1800
        # v2f = ±15
        # m1 = 10
        # m2 = 16
        # v1i = 15
        # v2i = 10
        # v1f = 5

        # k1i = 1/2 * m1 * v1i^2
        # k2i = 1/2 * m2 * v2i^2
        # k1f = 1/2 * m1 * v1f^2
        # k2f = 1/2 * m2 * v2f^2
        # kt = k1i + k2i
        # kt = k1f + k2f
        # m1 = 10
        # m2 = 16
        # v1i = 15
        # v2i = 10
        # v1f = 5
        solver5 = AlgebraSolver()
        solver5.recordRelation(Relation(sympy.parse_expr("k1i"), sympy.parse_expr("1/2*m1*v1i**2")))
        solver5.recordRelation(Relation(sympy.parse_expr("k1f"), sympy.parse_expr("1/2*m1*v1f**2")))
        solver5.recordRelation(Relation(sympy.parse_expr("k2i"), sympy.parse_expr("1/2*m2*v2i**2")))
        solver5.recordRelation(Relation(sympy.parse_expr("k2f"), sympy.parse_expr("1/2*m2*v2f**2")))
        solver5.recordRelation(Relation(sympy.parse_expr("kt"), sympy.parse_expr("k1i + k2i")))
        solver5.recordRelation(Relation(sympy.parse_expr("kt"), sympy.parse_expr("k1f + k2f")))
        # putting single-variable definition relations afterward checks that relations are sorted
        # and inferred from in the correct order (aka tests against "variable trapping")
        solver5.recordRelation(Relation(sympy.parse_expr("m1"), 10)) # type: ignore
        solver5.recordRelation(Relation(sympy.parse_expr("m2"), 16)) # type: ignore
        solver5.recordRelation(Relation(sympy.parse_expr("v1i"), 15)) # type: ignore
        solver5.recordRelation(Relation(sympy.parse_expr("v2i"), 10)) # type: ignore
        solver5.recordRelation(Relation(sympy.parse_expr("v1f"), 5)) # type: ignore

        # (m1 = 10)
        # (m2 = 16)
        # (v1i = 15)
        # (v2i = 10)
        # (v1f = 5)
        # (v2f = 15 OR -15)
        # (k1i = 1125)
        # (k2i = 800)
        # (kt = 1925)
        # (k1f = 125)
        # (k2f = 1800)
        assert solver5.substituteKnownsFor(sympy.parse_expr("m1")) == {10}
        assert solver5.substituteKnownsFor(sympy.parse_expr("m2")) == {16}
        assert solver5.substituteKnownsFor(sympy.parse_expr("v1i")) == {15}
        assert solver5.substituteKnownsFor(sympy.parse_expr("v2i")) == {10}
        assert solver5.substituteKnownsFor(sympy.parse_expr("v1f")) == {5}
        assert solver5.substituteKnownsFor(sympy.parse_expr("v2f")) == {-15, 15}
        assert solver5.substituteKnownsFor(sympy.parse_expr("k1i")) == {1125}
        assert solver5.substituteKnownsFor(sympy.parse_expr("k2i")) == {800}
        assert solver5.substituteKnownsFor(sympy.parse_expr("kt")) == {1925}
        assert solver5.substituteKnownsFor(sympy.parse_expr("k1f")) == {125}
        assert solver5.substituteKnownsFor(sympy.parse_expr("k2f")) == {1800}

        solver5.recordRelation(Relation(sympy.parse_expr("v2f"), 15)) # type: ignore
        assert solver5.substituteKnownsFor(sympy.parse_expr("v2f")) == {15}

        # a + c = a + 3
        # d - a = 2*c
        # a*d = 4*(b + c)
        # a/2 = 2
        solver6 = AlgebraSolver()
        solver6.recordRelation(Relation(sympy.parse_expr("a + c"), sympy.parse_expr("a + 3")))
        solver6.recordRelation(Relation(sympy.parse_expr("d - a"), sympy.parse_expr("2*c")))
        solver6.recordRelation(Relation(sympy.parse_expr("a*d"), sympy.parse_expr("4*(b + c)")))
        solver6.recordRelation(Relation(sympy.parse_expr("a/2"), sympy.parse_expr("2")))
        # (a = 4)
        # (b = 7)
        # (c = 3)
        # (d = 10)
        assert solver6.substituteKnownsFor(sympy.parse_expr("a")) == {4}
        assert solver6.substituteKnownsFor(sympy.parse_expr("b")) == {7}
        assert solver6.substituteKnownsFor(sympy.parse_expr("c")) == {3}
        assert solver6.substituteKnownsFor(sympy.parse_expr("d")) == {10}

        # x*y = z + 2
        # x + y = 7
        # z = 2*(x + 1)
        solver7 = AlgebraSolver()
        solver7.recordRelation(Relation(sympy.parse_expr("x*y"), sympy.parse_expr("z + 2")))
        solver7.recordRelation(Relation(sympy.parse_expr("x + y"), sympy.parse_expr("7")))
        solver7.recordRelation(Relation(sympy.parse_expr("z"), sympy.parse_expr("2*(x + 1)")))
        # (x = {4, 1})
        # (y = {3, 6})
        # (z = {10, 4})
        assert solver7.substituteKnownsFor(sympy.parse_expr("x")) == {4, 1}
        assert solver7.substituteKnownsFor(sympy.parse_expr("y")) == {3, 6}
        assert solver7.substituteKnownsFor(sympy.parse_expr("z")) == {10, 4}

        # x*y = z + 2
        # x + y = 11
        # z = 2*(x + 3)
        solver8 = AlgebraSolver()
        solver8.recordRelation(Relation(sympy.parse_expr("x*y"), sympy.parse_expr("z + 2")))
        solver8.recordRelation(Relation(sympy.parse_expr("x + y"), sympy.parse_expr("11")))
        solver8.recordRelation(Relation(sympy.parse_expr("z"), sympy.parse_expr("2*(x + 3)")))
        # (x = {1, 8})
        # (y = {10, 3})
        # (z = {8, 22})
        assert solver8.substituteKnownsFor(sympy.parse_expr("x")) == {1, 8}
        assert solver8.substituteKnownsFor(sympy.parse_expr("y")) == {10, 3}
        assert solver8.substituteKnownsFor(sympy.parse_expr("z")) == {8, 22}
