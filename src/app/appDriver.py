from typing import Iterable, Collection

import sympy

from src.common.functions import surroundJoin, first
from src.common.exceptions import TracebackException, MultilineException
from src.app.textRenderer import TextRenderer
from src.app.widgets.colors import Colors
from src.algebrasolver.solver import AlgebraSolver, Relation
from src.parsing.lexer import CommandLexer, LexerToken
from src.parsing.parser import CommandParser, Command, CommandType, isExpressionListSymbol


class AppDriver:
    def __init__(self):
        self._solver = AlgebraSolver()
        self._lexer = CommandLexer()
        self._parser = CommandParser()

    def processCommandLines(self, commandsStr: str):
        tokens = tuple(self._lexer.findTokens(commandsStr))
        for command in self._parser.parseCommand(tokens):
            yield self._processCommand(command, tokens)

    def validateSingleLine(self, commandStr: str):
        if "\n" in commandStr:
            raise NotImplementedError("Multiline commands not supported")
        
    def getRelations(self):
        return self._solver.getRelations()
    
    def deleteRelation(self, relation: Relation):
        self._solver.popRelation(relation)

    def replaceRelation(self, oldRelation: Relation, newRelationCommand: str):
        self.validateSingleLine(newRelationCommand)
        # TODO: this would be a good use case for transactional solver stuff when that's implemented
        self._solver.popRelation(oldRelation)
        try:
            result = first(self.processCommandLines(newRelationCommand), None)
            if result is None or result.type is not Command.RECORD_RELATION:
                raise NotARelationException(oldRelation, newRelationCommand)
            else:
                return result
        except Exception as exception:
            self._solver.recordRelation(oldRelation)
            raise exception

    def _processCommand(self, command: Command, tokens: tuple[LexerToken, ...]):
        # the paradigm here: `command` is something that needs to happen, the `result`
        # is what's returned after doing what needs to happen (the `type` for either
        # representing the `type` of work that needs to be/was done)

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
                assert type(symbol) is sympy.Symbol
                relations = self._solver.getRelationsWithSymbol(symbol)
                noRelationsForSymbol = len(relations) == 0
                if noRelationsForSymbol and not isExpressionListSymbol(symbol):
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
    def __init__(self, tokens: Collection[LexerToken], badIdentifiers: Collection[str]):
        badTokenIdxs = tuple(
            tokenIdx
            for (tokenIdx, token) in enumerate(tokens)
            if token.match in badIdentifiers
        )
        plural = "s" if len(badIdentifiers) > 1 else ""
        badIdentifiersStr = surroundJoin(badIdentifiers, f"[{Colors.textRed.hex}]", f"[/{Colors.textRed.hex}]", ", ")
        super().__init__(
            f"Undefined __identifier{plural}__ {badIdentifiersStr}",
            tokens,
            badTokenIdxs
        )


class NotARelationException(MultilineException):
    def __init__(self, oldRelation: Relation, nonRelationStr: str | None):
        if nonRelationStr is None or nonRelationStr == "":
            nonRelationStr = "(empty input)"
        super().__init__((
            "Cannot replace relation",
            TextRenderer().formatRelation(oldRelation),
            "with non-relation",
            nonRelationStr,
        ))
