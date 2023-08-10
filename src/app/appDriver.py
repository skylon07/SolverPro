from src.common.functions import first
from src.algebrasolver.solver import AlgebraSolver
from src.parsing.lexer import CommandLexer, LexerTokenTypes
from src.parsing.parser import CommandParser, Command, CommandType, EolException

class AppDriver:
    def __init__(self):
        self._solver = AlgebraSolver()
        self._lexer = CommandLexer()
        self._parser = CommandParser()

    def processCommandLines(self, commandsStr: str):
        tokens = tuple(self._lexer.findTokens(commandsStr))
        for command in self._parser.parse(tokens):
            # TODO: make this transactional in the case of erroring
            yield self._processCommand(command)

    def validateSingleLine(self, commandStr: str):
        if "\n" in commandStr:
            raise NotImplementedError("Multiline commands not supported")

    def _processCommand(self, command: Command):
        if command.type is Command.EMPTY:
            return ProcessResult(Command.EMPTY, None)
        
        elif command.type is Command.RECORD_RELATION:
            (leftExpr, rightExpr) = command.data
            (newRelation, isRedundant) = self._solver.recordRelation(leftExpr, rightExpr)
            return ProcessResult(Command.RECORD_RELATION, (leftExpr, rightExpr, isRedundant))
        
        elif command.type is Command.EVALUATE_EXPRESSION:
            expr = command.data
            subExprs = self._solver.substituteKnownsFor(expr)
            return ProcessResult(Command.EVALUATE_EXPRESSION, subExprs)
        
        else:
            raise NotImplementedError(f"Processing command of type {command.type} not implemented")

   
class ProcessResult:
    def __init__(self, commandType: CommandType, data):
        self.type = commandType
        self.data = data

    def __repr__(self):
        return f"ProcessResult({self.type}, {self.data})"

    def __eq__(self, other):
        if type(other) is not ProcessResult:
            return False
        
        return self.type == other.type and self.data == other.data
