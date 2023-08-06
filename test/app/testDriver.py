from src.app.appDriver import AppDriver, ProcessResult, Command

class AppDriverTester:
    def testDriverEvaluatesExpressions(self):
        driver = AppDriver()

        results1 = tuple(driver.processCommandLines("-3 + 4"))
        assert results1 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (1,)),
        ), "Driver did not correctly evaluate simple numeric expression"

        results2 = tuple(driver.processCommandLines("6^2 + 2*2"))
        assert results2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (40,)),
        ), "Driver did not correctly evaluate complicated numeric expression"

    def testDriverRecordsRelations(self):
        driver = AppDriver()

        relationResults = tuple(driver.processCommandLines("5 = b"))
        assert relationResults == (
            ProcessResult(Command.RECORD_RELATION, None),
        ), "Driver didn't record a simple variable relation"
        
        evaluateResults = tuple(driver.processCommandLines("b"))
        assert evaluateResults == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (5,)),
        ), "Driver didn't correctly acquire variable value"
        
    def testDriverSolvesRelations(self):
        driver1 = AppDriver()

        relationResults1 = tuple(driver1.processCommandLines("1 + c = 4"))
        assert relationResults1 == (
            ProcessResult(Command.RECORD_RELATION, None),
        ), "Driver did not correctly record simple solvable relation"
        
        evaluateResults1_1 = tuple(driver1.processCommandLines("c"))
        assert evaluateResults1_1 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (3,)),
        ), "Driver did not correctly solve a simple solvable relation"

        driver2 = AppDriver()

        relationResults1_2 = tuple(driver2.processCommandLines("a*b = c + 5"))
        assert relationResults1_2 == (
            ProcessResult(Command.RECORD_RELATION, None),
        ), "Driver did not record the first relation in a series of solvable relations"

        relationResults2_2 = tuple(driver2.processCommandLines("a + b = 5"))
        assert relationResults2_2 == (
            ProcessResult(Command.RECORD_RELATION, None),
        ), "Driver did not record the second relation in a series of solvable relations"

        relationResults3_2 = tuple(driver2.processCommandLines("b = 2"))
        assert relationResults3_2 == (
            ProcessResult(Command.RECORD_RELATION, None),
        ), "Driver did not record the third relation in a series of solvable relations"
        
        evaluateResults1_2 = tuple(driver2.processCommandLines("a"))
        assert evaluateResults1_2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (3,)),
        ), "Driver did not correctly infer first variable in a series of solvable relations"
        
        evaluateResults2_2 = tuple(driver2.processCommandLines("b"))
        assert evaluateResults2_2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (2,)),
        ), "Driver did not correctly infer first variable in a series of solvable relations"
        
        evaluateResults3_2 = tuple(driver2.processCommandLines("c"))
        assert evaluateResults3_2 == (
            ProcessResult(Command.EVALUATE_EXPRESSION, (1,)),
        ), "Driver did not correctly infer first variable in a series of solvable relations"
