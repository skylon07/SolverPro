from src.algebrasolver.solver import AlgebraSolver
from src.parser.lexer import CommandLexer
from src.parser.parser import CommandParser, Command, CommandType

class AppDriver:
    def __init__(self):
        self._solver = AlgebraSolver()
        self._lexer = CommandLexer()
        self._parser = CommandParser()

    def processCommandLines(self, commandsStr: str):
        tokens = tuple(self._lexer.findTokens(commandsStr))
        for command in self._parser.parse(tokens):
            yield self.processCommand(command)

    def processCommand(self, command: Command):
        if command.type is Command.EMPTY:
            return ProcessResult(Command.EMPTY, None)
        
        elif command.type is Command.RECORD_RELATION:
            (leftExpr, rightExpr) = command.data
            self._solver.recordRelation(leftExpr, rightExpr)
            return ProcessResult(Command.RECORD_RELATION, None)
        
        elif command.type is Command.EVALUATE_EXPRESSION:
            expr = command.data
            subExprs = tuple(self._solver.substituteKnownsFor(expr))
            return ProcessResult(Command.EVALUATE_EXPRESSION, subExprs)
        
        else:
            raise NotImplementedError(f"Processing command of type {command.type} not implemented")

   
class ProcessResult:
    def __init__(self, commandType: CommandType, data):
        self.type = commandType
        self.data = data
