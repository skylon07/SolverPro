import sympy

from src.common.sympyLinterFixes import log, ln, exp
from src.parsing.parserHelpers import *
from src.parsing.parserTypes import *


def isNonSymbolicValue(value: sympy.Basic):
    if isinstance(value, sympy.Number):
        return True
    elif value is sympy.I:
        return True
    elif isinstance(value, sympy.Symbol):
        return False
    elif isinstance(value, sympy.Expr):
        return all(isNonSymbolicValue(arg) for arg in value.args)
    else:
        return False
    
def isExpressionListSymbol(value: sympy.Symbol):
    symbolStr = str(value)
    if symbolStr[0] == "{" and symbolStr[-1] == "}":
        exprListStr = symbolStr[1:-1]
        if "{" not in exprListStr and "}" not in exprListStr:
            return True
    return False

def freeSymbolsOf(expr: sympy.Expr, *, includeExpressionLists: bool = True) -> set[sympy.Symbol]:
    symbols = expr.free_symbols
    assert all(type(symbol) is sympy.Symbol for symbol in symbols)
    return {
        symbol
        for symbol in symbols
        if not isExpressionListSymbol(symbol) or includeExpressionLists # type: ignore
    }


class CommandParser:
    builtinAliases = {
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

    @classmethod
    def parseCommand(cls, commandTokens: tuple[LexerToken, ...]):
        while len(commandTokens) > 0:
            sequencer = CommandParserSequencer(commandTokens, cls.builtinAliases)
            command = sequencer.sequenceCommand()
            yield command
            commandTokens = commandTokens[sequencer.numTokensParsed:]

    @classmethod
    def parseExpressionList(cls, exprListTokens: tuple[LexerToken, ...]):
        sequencer = CommandParserSequencer(exprListTokens, cls.builtinAliases)
        expressions = sequencer.sequenceExpressionList()
        return expressions

    @classmethod
    def preprocessAliases(cls, tokens: tuple[LexerToken, ...], aliases: dict[str, "AliasTemplate"]):
        sequencer = CommandAliasSequencer(tokens, aliases)
        processedTokens = sequencer.sequenceExpression(isPrimary = True)
        return processedTokens
