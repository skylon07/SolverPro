from typing import Iterable, Callable

import sympy

from src.common.types import Enum, EnumString
from src.common.exceptions import TracebackException
from src.app.widgets.colors import Colors
from src.parsing.lexer import LexerToken, LexerTokenTypes, LexerTokenType

class AliasTemplate:
    def __init__(self, name: str, argNames: tuple[str, ...], templateTokens: tuple[LexerToken, ...]):
        self.name = name
        self.argNames = argNames
        self.numArgs = len(argNames)
        self.templateTokens = templateTokens

    def __repr__(self):
        return f"AliasTemplate({self.name}, {self.argNames})"
    
    def evaluate(self, *argVals: str):
        assert len(argVals) == self.numArgs
        replacements = dict(zip(self.argNames, argVals))
        finalStr = ""
        lastToken = None
        for token in self.templateTokens:
            finalStr += token.makeWhitespaceTo(lastToken)
            if token.type is LexerTokenTypes.IDENTIFIER and token.match in replacements:
                tokenReplacement = replacements[token.match]
                finalStr += tokenReplacement
            else:
                finalStr += token.match
            lastToken = token
        return finalStr
    

class BuiltinAlias:
    def __init__(self, name: str, numArgs: int, evalFn: Callable[..., sympy.Expr]):
        self.name = name
        self.numArgs = numArgs
        self._evalFn = evalFn

    def __repr__(self):
        return f"BuiltinAlias({self.name})"
    
    def evaluate(self, *argVals: sympy.Expr):
        return self._evalFn(*argVals)


class CommandType(EnumString):
    pass # intentionally left blank


class Command(Enum):
    EMPTY = CommandType("EMPTY")
    RECORD_RELATIONS = CommandType("RECORD_RELATIONS")
    EVALUATE_EXPRESSION = CommandType("EVALUATE_EXPRESSION")
    SIMPLIFY_EXPRESSION = CommandType("SIMPLIFY_EXPRESSION")
    RECORD_ALIAS = CommandType("RECORD_ALIAS")

    def __init__(self, commandType: CommandType, data):
        self.type = commandType
        self.data = data

    def __eq__(self, other):
        if type(other) is not Command:
            return False
        
        return self.type == other.type and self.data == other.data

    @classmethod
    def empty(cls):
        return cls(cls.EMPTY, None)
    
    @classmethod
    def recordRelations(cls, relations: list[sympy.Expr]):
        return cls(cls.RECORD_RELATIONS, relations)
    
    @classmethod
    def evaluateExpression(cls, expression: sympy.Expr):
        return cls(cls.EVALUATE_EXPRESSION, expression)
    
    @classmethod
    def simplifyExpression(cls, expression: sympy.Expr):
        return cls(cls.SIMPLIFY_EXPRESSION, expression)
    
    @classmethod
    def recordAlias(cls, aliasTemplate: tuple[str, tuple[str, ...], str]):
        return cls(cls.RECORD_ALIAS, aliasTemplate)
    

class ParseException(TracebackException):
    def __init__(self, expectedTypes: tuple[LexerTokenType, ...], tokens: tuple[LexerToken, ...], unexpectedTokenIdx: int):
        unexpectedToken = tokens[unexpectedTokenIdx]

        expectedTypesStr = " or ".join(f"[{Colors.textGreen.hex}][@termtip]{tokenType}[/@termtip][/]".lower() for tokenType in expectedTypes)
        firstLetterIsVowel = str(expectedTypes[0])[0].lower() in "aeiou"
        gramaticalN = "n" if firstLetterIsVowel else ""
        fullMessage = f"Unexpected [{Colors.textRed.hex}]{unexpectedToken.match}[/]; expected a{gramaticalN} {expectedTypesStr}"
        super().__init__(fullMessage, tokens, [unexpectedTokenIdx], True)


class EolException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...]):
        lastToken = tokens[-1]
        if lastToken.type is LexerTokenTypes.EOL:
            tokens = tokens[:-1]
            eolPosition = lastToken.matchIdx
        else:
            eolPosition = lastToken.matchIdxEnd
        newEolToken = LexerToken(f" ...", LexerTokenTypes.EOL, eolPosition)
        tokens = tokens + (newEolToken,)
        super().__init__(f"Unexpected [{Colors.textRed.hex}][@termtip]end of line[/@termtip][/]", tokens, [len(tokens) - 1], True)


class UnknownAliasException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...], aliasTokenIdx: int):
        aliasName = tokens[aliasTokenIdx].match
        message = f"[@termtip]Alias[/@termtip] [{Colors.textRed.hex}]{aliasName}[/] is not defined"
        super().__init__(message, tokens, [aliasTokenIdx], True)


class AliasArgumentCountException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...], expectedCount: int, actualCount: int, unexpectedTokenIdxs: Iterable[int]):
        tooManyArguments = actualCount > expectedCount
        if tooManyArguments:
            receivedGrammarStr = "received too many"
        else:
            receivedGrammarStr = "did not receive enough"
        gramaticalS = "s" if expectedCount != 1 else ""
        fullMessage = f"[@termtip]Alias[/@termtip] expected [{Colors.textGreen.hex}]{expectedCount} argument{gramaticalS}[/], but [{Colors.textRed.hex}]{receivedGrammarStr}[/]"
        super().__init__(fullMessage, tokens, unexpectedTokenIdxs, True)

class UnknownCommandException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...], commandIdentifierTokenIdx: int):
        commandName = tokens[commandIdentifierTokenIdx].match
        message = f"Unknown [@termtip]command[/@termtip] [{Colors.textRed.hex}]{commandName}[/]"
        super().__init__(message, tokens, [commandIdentifierTokenIdx], grayOutAfterBadTokens = True)
