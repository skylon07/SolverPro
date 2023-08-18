import sympy

from src.common.functions import surroundJoin
from src.common.exceptions import TracebackException
from src.algebrasolver.solver import AlgebraSolver, Relation
from src.parsing.lexer import CommandLexer, LexerToken, LexerTokenTypes
from src.parsing.parser import CommandParser, Command, CommandType


class AppDriver:
    def __init__(self):
        self._solver = AlgebraSolver()
        self._lexer = CommandLexer()
        self._parser = CommandParser()

    def processCommandLines(self, commandsStr: str):
        tokens = tuple(self._lexer.findTokens(commandsStr))
        for command in self._parser.parse(tokens):
            # TODO: make this transactional in the case of erroring
            yield self._processCommand(command, tokens)

    def validateSingleLine(self, commandStr: str):
        if "\n" in commandStr:
            raise NotImplementedError("Multiline commands not supported")

    def _processCommand(self, command: Command, tokens: tuple[LexerToken, ...]):
        if command.type is Command.EMPTY:
            return ProcessResult(Command.EMPTY, None)
        
        elif command.type is Command.RECORD_RELATION:
            (leftExpr, rightExpr) = command.data
            newRelation = Relation(leftExpr, rightExpr)
            isRedundant = self._solver.recordRelation(newRelation)
            return ProcessResult(Command.RECORD_RELATION, (newRelation, isRedundant))
        
        elif command.type is Command.EVALUATE_EXPRESSION:
            expr: sympy.Expr = command.data
            undefinedSymbolStrs: list[str] = list()
            for symbol in expr.free_symbols:
                relations = self._solver.getRelationsWithSymbol(symbol)
                noRelationsForSymbol = len(relations) == 0
                if noRelationsForSymbol:
                    undefinedSymbolStrs.append(str(symbol))
            if len(undefinedSymbolStrs) > 0:
                raise UndefinedIdentifiersException(tokens, undefinedSymbolStrs)
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


class UndefinedIdentifiersException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...], badIdentifiers: tuple[str, ...]):
        badTokenIdxs = tuple(
            tokenIdx
            for (tokenIdx, token) in enumerate(tokens)
            if token.match in badIdentifiers
        )
        plural = "s" if len(badIdentifiers) > 1 else ""
        badIdentifiersStr = surroundJoin(badIdentifiers, "[red]", "[/red]", ", ")
        super().__init__(
            f"Undefined identifier{plural} {badIdentifiersStr}",
            tokens,
            badTokenIdxs
        )
