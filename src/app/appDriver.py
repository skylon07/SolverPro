from typing import Collection

import sympy

from src.common.functions import surroundJoin, first
from src.common.sympyLinterFixes import log, ln, exp
from src.common.exceptions import TracebackException, MultilineException
from src.app.textRenderer import TextRenderer
from src.app.widgets.colors import Colors
from src.algebrasolver.solver import AlgebraSolver, Relation
from src.parsing.lexer import CommandLexer, LexerToken, LexerTokenTypes
from src.parsing.parser import CommandParser, Command, CommandType, AliasTemplate, BuiltinAlias, IdType, IdTypes, freeSymbolsOf


class AppDriver:
    def __init__(self):
        self._solver = AlgebraSolver()

        self._inputHistory: list[str] = list()
        self._historySearchTerm: str = ""
        self._currHistoryIdx: int = -1

        self._aliases: dict[str, AliasTemplate] = dict()
        self._builtinAliases = {
            "pi": BuiltinAlias("pi", 0, lambda: sympy.pi),
            "e": BuiltinAlias("i", 0, lambda: sympy.E),
            "exp": BuiltinAlias("exp", 1, lambda pow: exp(pow)),
            "i": BuiltinAlias("i", 0, lambda: sympy.I),
            "sqrt": BuiltinAlias("sqrt", 1, lambda expr: sympy.sqrt(expr)),
            "√": BuiltinAlias("√", 1, lambda expr: sympy.sqrt(expr)),
            "cbrt": BuiltinAlias("cbrt", 1, lambda expr: sympy.cbrt(expr)),
            "∛": BuiltinAlias("∛", 1, lambda expr: sympy.cbrt(expr)),
            "root": BuiltinAlias("root", 2, lambda n, base: sympy.root(n, base)),
            "log": BuiltinAlias("log", 2, lambda n, base: log(n, base)),
            "ln": BuiltinAlias("ln", 1, lambda n: ln(n)),
        }
        self._idTypes: dict[str, IdType] = {
            aliasName: IdTypes.BUILTIN_ALIAS
            for aliasName in self._builtinAliases
        }

        self._warmUpSimplify()

    def processCommandLines(self, commandsStr: str):
        try:
            tokensWithAliases = tuple(CommandLexer.findTokens(commandsStr))

            shouldParseAliases = not any(token.type is LexerTokenTypes.COLON_EQUALS for token in tokensWithAliases)
            if shouldParseAliases:
                lastProcessedTokens = None
                processedTokens = tokensWithAliases
                roundCount = 0
                while processedTokens != lastProcessedTokens:
                    lastProcessedTokens = processedTokens
                    processedCommandsStr = CommandParser.preprocessAliases(processedTokens, self._aliases)
                    processedTokens = tuple(CommandLexer.findTokens(processedCommandsStr))
                    roundCount += 1
                    if roundCount == 999:
                        raise RecursiveTemplatesException()
            else:
                processedTokens = tokensWithAliases

            anyNonEmptyCommands = False
            for command in CommandParser.parseCommand(processedTokens, self._idTypes, self._builtinAliases):
                if command.type is not Command.EMPTY:
                    anyNonEmptyCommands = True
                yield self._processCommand(command, processedTokens)
            
            if anyNonEmptyCommands:
                self._inputHistory.insert(0, commandsStr)
        
        except Exception as exception:
            self._inputHistory.insert(0, commandsStr)
            raise exception

        finally:
            self.resetHistoryState()

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
            commandHasMultipleRelations = len([char for char in newRelationCommand if char == "="]) > 1
            if commandHasMultipleRelations:
                raise TooManyRelationsException(oldRelation, newRelationCommand)

            result = first(self.processCommandLines(newRelationCommand), None)
            if result is None or result.type is not Command.RECORD_RELATIONS:
                raise NotARelationException(oldRelation, newRelationCommand)
            else:
                return result
        except Exception as exception:
            self._solver.recordRelation(oldRelation)
            raise exception
        
    def getAllAliasNames(self):
        return tuple((
            *self._builtinAliases.keys(),
            *self._aliases.keys(),
        ))
        
    def getInputHistory(self):
        return tuple(self._inputHistory)
    
    def resetHistoryState(self):
        self._historySearchTerm = ""
        self._currHistoryIdx = -1
    
    def recordHistorySearchTerm(self, searchTerm: str):
        self._historySearchTerm = searchTerm

    def loadPreviousHistory(self):
        lastValidHistoryIdx = self._currHistoryIdx
        historyChanged = False
        while self._currHistoryIdx < len(self._inputHistory):
            if historyChanged:
                currHistory = self._inputHistory[self._currHistoryIdx]
                if self._historySearchTerm in currHistory and historyChanged:
                    break
            self._currHistoryIdx += 1
            historyChanged = True
        
        if self._currHistoryIdx < len(self._inputHistory):
            return self._inputHistory[self._currHistoryIdx]
        else:
            self._currHistoryIdx = lastValidHistoryIdx
            return None
        
    def loadNextHistory(self):
        if self._currHistoryIdx == -1:
            return None
        
        lastValidHistoryIdx = self._currHistoryIdx
        historyChanged = False
        while self._currHistoryIdx >= 0:
            if historyChanged:
                currHistory = self._inputHistory[self._currHistoryIdx]
                if self._historySearchTerm in currHistory and historyChanged:
                    break
            self._currHistoryIdx -= 1
            historyChanged = True
        
        if self._currHistoryIdx >= 0:
            return self._inputHistory[self._currHistoryIdx]
        else:
            self._currHistoryIdx = lastValidHistoryIdx
            return None

    def _processCommand(self, command: Command, tokens: tuple[LexerToken, ...]):
        # the paradigm here: `command` is something that needs to happen, the `result`
        # is what's returned after doing what needs to happen (the `type` for either
        # representing the `type` of work that needs to be/was done)

        if command.type is Command.EMPTY:
            return ProcessResult(Command.EMPTY, None)
        
        elif command.type is Command.RECORD_RELATIONS:
            relations = [
                Relation(leftExpr, rightExpr)
                for (leftExprIdx, leftExpr) in enumerate(command.data)
                for rightExpr in [
                    command.data[leftExprIdx + 1]
                    if leftExprIdx + 1 < len(command.data)
                    else command.data[-1]
                ]
                if leftExprIdx + 1 < len(command.data)
            ]
            
            for relation in relations:
                for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False):
                    identifierPath = str(symbol)
                    if identifierPath not in self._idTypes:
                        # relations define new symbols
                        assert self._idTypes.get(identifierPath, IdTypes.SYMBOL) is IdTypes.SYMBOL, \
                            "Parser did not throw when trying to change identifier type to SYMBOL"
                        self._idTypes[identifierPath] = IdTypes.SYMBOL
            
            relationsWithRedundancies = [
                (relation, isRedundant)
                for relation in relations
                for isRedundant in [self._solver.recordRelation(relation)]
            ]
            return ProcessResult(Command.RECORD_RELATIONS, relationsWithRedundancies)
        
        elif command.type is Command.EVALUATE_EXPRESSION:
            expr: sympy.Expr = command.data
            assert isinstance(expr, sympy.Expr)

            undefinedSymbolStrs: list[str] = list()
            for symbol in freeSymbolsOf(expr, includeExpressionLists = False):
                symbolIdPath = str(symbol)
                symbolUnknown = symbolIdPath not in self._idTypes
                if symbolUnknown:
                    undefinedSymbolStrs.append(str(symbol))
                    assert len(self._solver.getRelationsWithSymbol(symbol)) == 0
                else:
                    assert self._idTypes[symbolIdPath] is IdTypes.SYMBOL
                    assert len(self._solver.getRelationsWithSymbol(symbol)) > 0
            
            if len(undefinedSymbolStrs) > 0:
                raise UndefinedIdentifiersException(tokens, undefinedSymbolStrs)
            
            subExprs = self._solver.substituteKnownsFor(expr)
            return ProcessResult(Command.EVALUATE_EXPRESSION, subExprs)
        
        elif command.type is Command.RECORD_ALIAS:
            data: tuple[str, tuple[str, ...], str] = command.data
            (aliasName, aliasArgs, aliasTemplateStr) = data
            assert type(aliasName) is str
            assert isinstance(aliasArgs, tuple)
            assert type(aliasTemplateStr) is str

            assert self._idTypes.get(aliasName, IdTypes.ALIAS) is IdTypes.ALIAS, \
                "Parser did not throw when trying to change identifier type to ALIAS"
            self._idTypes[aliasName] = IdTypes.ALIAS

            aliasTemplate = AliasTemplate(aliasName, aliasArgs, tuple(CommandLexer.findTokens(aliasTemplateStr)))
            self._aliases[aliasName] = aliasTemplate
            return ProcessResult(Command.RECORD_ALIAS, aliasTemplate)
        
        elif command.type is Command.SIMPLIFY_EXPRESSION:
            expr: sympy.Expr = command.data
            assert isinstance(expr, sympy.Expr)
            expr = sympy.simplify(expr)
            return ProcessResult(Command.SIMPLIFY_EXPRESSION, {expr})
        
        else:
            raise NotImplementedError(f"Processing command of type {command.type} not implemented")
        
    def _warmUpSimplify(self):
        # for some reason, the first call to this is a tad slow...
        # this just gets that out of the way so the app doesn't feel sluggish
        return sympy.simplify("x + x")

   
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
            f"Undefined [@termtip]identifier{plural}[/@termtip] {badIdentifiersStr}",
            tokens,
            badTokenIdxs
        )


class NotARelationException(MultilineException):
    def __init__(self, oldRelation: Relation, nonRelationStr: str | None):
        if nonRelationStr is None or nonRelationStr == "":
            nonRelationStr = "(empty input)"
        renderer = TextRenderer.instance
        super().__init__((
            "Cannot replace relation",
            renderer.formatRelation(oldRelation, highlightSyntax = True),
            "with non-relation",
            renderer.formatLexerSyntax(nonRelationStr),
        ))


class TooManyRelationsException(MultilineException):
    def __init__(self, oldRelation: Relation, relationsStr: str):
        renderer = TextRenderer.instance
        super().__init__((
            "Cannot replace single relation",
            renderer.formatRelation(oldRelation, highlightSyntax = True),
            "with multiple relations",
            renderer.formatLexerSyntax(relationsStr),
        ))


class RecursiveTemplatesException(MultilineException):
    def __init__(self):
        super().__init__((
            "Too many dependent aliases",
            "Double-check your alias templates don't have circular dependencies",
        ))
