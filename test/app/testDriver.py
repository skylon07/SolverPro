import sympy

from src.common.functions import runForError
from src.app.appDriver import AppDriver, ProcessResult, Command, UndefinedIdentifiersException, RecursiveTemplatesException
from src.algebrasolver.solver import Relation


class AppDriverTester:
    def testEvaluatesExpressions(self):
        driver = AppDriver()

        results1 = tuple(driver.processCommandLines("-3 + 4"))
        assert results1 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {1}),
        ), "Driver did not correctly evaluate simple numeric expression"

        results2 = tuple(driver.processCommandLines("6^2 + 2*2"))
        assert results2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {40}),
        ), "Driver did not correctly evaluate complicated numeric expression"

    def testRecordsRelations(self):
        driver = AppDriver()

        relationResults = tuple(driver.processCommandLines("5 = b"))
        assert relationResults == (
            ProcessResult(Command.RECORD_RELATIONS, [(Relation(5, sympy.parse_expr("b")), False)]), # type: ignore
        ), "Driver didn't record a simple variable relation"
        
        evaluateResults = tuple(driver.processCommandLines("b"))
        assert evaluateResults == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {5}),
        ), "Driver didn't correctly acquire variable value"
        
    def testSolvesRelations(self):
        driver1 = AppDriver()

        relationResults1 = tuple(driver1.processCommandLines("1 + c = 4"))
        assert relationResults1 == (
            ProcessResult(Command.RECORD_RELATIONS, [(Relation(sympy.parse_expr("1 + c"), 4), False)]), # type: ignore
        ), "Driver did not correctly record simple solvable relation"
        
        evaluateResults1_1 = tuple(driver1.processCommandLines("c"))
        assert evaluateResults1_1 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {3}),
        ), "Driver did not correctly solve a simple solvable relation"

        driver2 = AppDriver()

        relationResults1_2 = tuple(driver2.processCommandLines("a*b = c + 5"))
        assert relationResults1_2 == (
            ProcessResult(Command.RECORD_RELATIONS, [(Relation(sympy.parse_expr("a*b"), sympy.parse_expr("c + 5")), False)]),
        ), "Driver did not record the first relation in a series of solvable relations"

        relationResults2_2 = tuple(driver2.processCommandLines("a + b = 5"))
        assert relationResults2_2 == (
            ProcessResult(Command.RECORD_RELATIONS, [(Relation(sympy.parse_expr("a + b"), 5), False)]), # type: ignore
        ), "Driver did not record the second relation in a series of solvable relations"

        relationResults3_2 = tuple(driver2.processCommandLines("b = 2"))
        assert relationResults3_2 == (
            ProcessResult(Command.RECORD_RELATIONS, [(Relation(sympy.parse_expr("b"), 2), False)]), # type: ignore
        ), "Driver did not record the third relation in a series of solvable relations"
        
        evaluateResults1_2 = tuple(driver2.processCommandLines("a"))
        assert evaluateResults1_2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {3}),
        ), "Driver did not correctly infer first variable in a series of solvable relations"
        
        evaluateResults2_2 = tuple(driver2.processCommandLines("b"))
        assert evaluateResults2_2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {2}),
        ), "Driver did not correctly infer first variable in a series of solvable relations"
        
        evaluateResults3_2 = tuple(driver2.processCommandLines("c"))
        assert evaluateResults3_2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {1}),
        ), "Driver did not correctly infer first variable in a series of solvable relations"

    # TODO: test getting list of relations

    def testDetectsUndefinedIdentifiers(self):
        driver = AppDriver()

        tuple(driver.processCommandLines("defined = 10"))

        def attemptBadCommand1():
            return tuple(driver.processCommandLines("undefined"))
        error1 = runForError(attemptBadCommand1)
        assert type(error1) is UndefinedIdentifiersException, \
            "Driver did not throw on undefined indentifier"
        assert error1.badTokenIdxs == (0,), \
            "Driver did not detect the index of the bad identifier"

        def attemptBadCommand2():
            return tuple(driver.processCommandLines("defined/undefined + undefined"))
        error2 = runForError(attemptBadCommand2)
        assert type(error2) is UndefinedIdentifiersException, \
            "Driver did not throw with multiple of the same undefined identifier present"
        assert error2.badTokenIdxs == (2, 4), \
            "Driver did not detect all indexes of the undefined identifier tokens"
        
        def attemptBadCommand3():
            return tuple(driver.processCommandLines("a + b + defined + c/b*defined^z - f/g"))
        error3 = runForError(attemptBadCommand3)
        assert type(error3) is UndefinedIdentifiersException, \
            "Driver did not throw with multiple unidentified identifiers present"
        assert error3.badTokenIdxs == (0, 2, 6, 8, 12, 14, 16), \
            "Driver did not detect all indexes of all the undidentified identifier tokens"
        
    # TODO: test creating aliases
        
    def testProcessesAliasTemplateDependencies(self):
        driver = AppDriver()

        tuple(driver.processCommandLines("quadruple(n) := double(double(n))"))
        tuple(driver.processCommandLines("double(n) := plus(n, n)"))
        tuple(driver.processCommandLines("plus(a, b) := a + b"))

        evaluateResults = tuple(driver.processCommandLines("quadruple(2)"))
        assert evaluateResults == (
            ProcessResult(Command.EVALUATE_EXPRESSION, {8}),
        ), "Driver didn't correctly process multi-layered alias templates"

    def testCanSimplifyExpressions(self):
        driver = AppDriver()

        results1 = tuple(driver.processCommandLines("simplify: x + x - y * y"))
        assert results1 == (
            ProcessResult(Command.SIMPLIFY_EXPRESSION, {sympy.parse_expr("x + x - y * y")}),
        )

    def testThrowsOnRecursiveDependencies(self):
        driver = AppDriver()

        tuple(driver.processCommandLines("add(a, b) := plus(a, b)"))
        tuple(driver.processCommandLines("plus(a, b) := add(a, b)"))

        def attemptBadCommand3():
            return tuple(driver.processCommandLines("plus(1, 2)"))
        error3 = runForError(attemptBadCommand3)
        assert type(error3) is RecursiveTemplatesException, \
            "Driver did not detect recursive templates"
        
    # TODO: test popping relations

    # TODO: add tests for robustness (from old project)
