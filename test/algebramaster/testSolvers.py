import sympy

from src.algebramaster.solver import AlgebraSolver, _BackSubstituterSolver, _SympySolveTools
from src.algebramaster.structures import SubDict, SubDictList


(a, b, c, d, e, two) = sympy.symbols("a, b, c, d, e, two")


class SympySolveToolsTester:
    def testReverseSubstituteForBadNumerics(self):
        expr = a + b**two
        equation = 2 - expr
        solution = _SympySolveTools._Solution(sympy.solveset(equation, 2))
        solution.reverseSubstitutionOfNumeric({two: 2})
        assert solution.set == sympy.FiniteSet(a + b**2)

    def testSolveSetPerformsSolving(self):
        expr = a + b*c - 4
        
        # a + b*c - 4 = 0
        # a + b*c = 4
        actualSolution1 = {4}
        toolsSolution1 = _SympySolveTools.solveSet(expr, a + b*c)
        assert toolsSolution1 == actualSolution1

        # a + b*c - 4 = 0
        # a - 4 = -b*c
        # -(a - 4) = b*c
        actualSolution2 = {b*c}
        toolsSolution2 = _SympySolveTools.solveSet(expr, -(a - 4))
        assert toolsSolution2 == actualSolution2

    def testSolveSetSolvesForNumerics(self):
        expr = 2 + 2*a + b
        
        # 2 + 2*a + b = 0
        # 2 + 2*a = -b
        # 2*(1 + a) = -b
        # 2 = -b/(1 + a)
        actualSolution1 = {-b/(1 + a)}
        toolsSolution1 = _SympySolveTools.solveSet(expr, 2)
        assert toolsSolution1 == actualSolution1
    
    def testSolveSetSolvesForNumerics_ignoresExponents(self):
        expr = a + b**2 - 2
        
        # a + b**2 - 2 = 0
        # -2 = -(a + b**2)
        # 2 = a + b**2      <-- should ignore `**2`!
        actualSolution1 = {a + b**2}
        toolsSolution1 = _SympySolveTools.solveSet(expr, 2)
        assert toolsSolution1 == actualSolution1

    def testSolvesSpecialOnesCaseByIgnoringMultiplies(self):
        expr = -a + b - 1

        # -a + b = 1
        # simple, right? NOPE!
        # sympy.solveset(expr, 1) yields b/(a + 1)
        # this is why:
        #   -a + b - 1 = 0
        #   -a     - 1 = -b
        #    a     + 1 =  b
        #         1    =  b/(a + 1)
        # so... technically not wrong, but we wanted it to solve
        # for the 1 already there, not for the 1 that was created
        # during the identity division (might also have to do with
        # it trying to solve for the 1 in -a, aka -1 * a)
        assert sympy.solveset(expr, 1) == {b/(a + 1)}

        wantedSolution = {-a + b}
        toolsSolution = _SympySolveTools.solveSet(expr, 1)
        assert toolsSolution == wantedSolution


class BackSubstituterTester:
    def testGetsCorrectSolutionsFromSingleUniverse(self):
        # a + b = 4
        # a - b = 2
        # (a = 3)
        # (b = 1)
        baseSubs1 = SubDict({
            a + b: 4,
            a - b: 2,
        })
        actualSolutions1 = SubDictList.fromList([{a: 3, b: 1}])
        solver1 = _BackSubstituterSolver(baseSubs1)
        solverSolutions1 = solver1.getSolutions()
        assert solverSolutions1 == actualSolutions1

        # a + 2*b + c = 20
        # 2*a + c = 14
        # b - a = 1
        # (a = 4)
        # (b = 5)
        # (c = 6)
        baseSubs2 = SubDict({
            a + 2*b + c: 20,
            2*a + c: 14,
            b - a: 1,
        })
        actualSolutions2 = SubDictList.fromList([{a: 4, b: 5, c: 6}])
        solver2 = _BackSubstituterSolver(baseSubs2)
        solverSolutions2 = solver2.getSolutions()
        assert solverSolutions2 == actualSolutions2

        # a + b = 6
        # b - c = 7
        # c = d - 8
        # d + e = -7
        # e + a = -10
        # (a = 2)
        # (b = 4)
        # (c = -3)
        # (d = 5)
        # (e = -12)
        baseSubs3 = SubDict({
            a + b: 6,
            b - c: 7,
            c - d: -8,
            d + e: -7,
            e + a: -10,
        })
        actualSolutions3 = SubDictList.fromList([{a: 2, b: 4, c: -3, d: 5, e: -12}])
        solver3 = _BackSubstituterSolver(baseSubs3)
        solverSolutions3 = solver3.getSolutions()
        assert solverSolutions3 == actualSolutions3

    def testGetsCorrectSolutionsFromTwoUniverses(self):
        # a**2 = 4
        # (a = 2, -2)
            # baseSubs1 = SubDict({
            #     a**2: 4,
            # })
            # actualSolutions1 = SubDictList.fromList([
            #     ({a: 2}, {a - 2}),
            #     ({a: -2}, {a + 2}),
            # ])
            # solver1 = _BackSubstituterSolver(baseSubs1)
            # solverSolutions1 = solver1.getSolutions()
            # assert solverSolutions1 == actualSolutions1

        # a + b**2 = 14
        # b = sqrt(14 - a)
        # a = 14 - b**2
        # a + b = 8
        # (a = 5, 10)
        # (b = 3, -2)
        baseSubs2 = SubDict({
            a + b**2: 14,
            a + b: 8,
        })
        actualSolutions2 = SubDictList.fromList([
            ({
                a: 5,
                b: 3,
            }, {b: 3}),
            ({
                a: 10,
                b: -2,
            }, {b: -2}),
        ])
        solver2 = _BackSubstituterSolver(baseSubs2)
        solverSolutions2 = solver2.getSolutions()
        assert solverSolutions2 == actualSolutions2

    def testGetsCorrectSolutionsFromMultipleUniverses(self):
        pass # TODO

    def testReturnsSymbolStack(self):
        assert __debug__ == True

        baseSubs = SubDict({
            a + 2*b + c: 20,
            2*a + c: 14,
            b - a: 1,
        })
        solver = _BackSubstituterSolver(baseSubs)
        solverSolutions = solver.getSolutions()
        assert '_symbolStack' in solverSolutions[0].__dict__


class AlgebraSolverTester:
    def testSolvesBasicEquations(self):
        solver = AlgebraSolver()
        solver.recordRelation(a - 4)
        solver.recordRelation(b - 5)

        assert solver.universes == [
            {
                a: 4,
                b: 5,
            },
        ]

    def testSolvesInSteps(self):
        solver = AlgebraSolver()
        assert solver.universes == []

        # a + 2*b + c = 20
        # 2*a + c = 14
        # b - a = 1
        # (a = 4)
        # (b = 5)
        # (c = 6)

        solver.recordRelation(a + 2*b + c --- 20)
        assert solver.universes == [
            {
                # a + 2*b + c  =  20
                a + 2*b + c: 20,
                # a + 2*b + c  =  20
                #     2*b      =  20 - a - c
                #     2        = (20 - a - c)/b
                (20 - a - c)/b: 2,
            }
        ]

        solver.recordRelation(2*a + c --- 14)
        assert solver.universes == [
            {
                a + 2*b + c: 20,
                (20 - a - c)/b: 2,
                # 2*a + c  =  14
                2*a + c: 14,
                # 2*a + c  =  14
                # 2*a      =  14 - c
                # 2        = (14 - c)/a
                (14 - c)/a: 2,
            }
        ]

        solver.recordRelation(b - a --- 1)
        assert solver.universes == [
            {
                a + 2*b + c: 20,
                (20 - a - c)/b: 2,
                2*a + c: 14,
                (14 - c)/a: 2,
                # b - a = 1
                b - a: 1,
                # (solutions for a, b, c)
                a: 4,
                b: 5,
                c: 6,
            }
        ]