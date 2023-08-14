import re

import sympy
from rich.markup import render as renderMarkup

from src.common.types import FormattedStr
from src.common.exceptions import TracebackException, HandledException, MultilineException
from src.parsing.lexer import LexerToken, LexerTokenTypes
from src.algebrasolver.solver import Relation


class TextRenderer:
    def __init__(self):
        powRegex = re.compile(r"\*\*")
        self._powReplace = lambda exprStr: powRegex.sub("^", exprStr)

    def renderRelation(self, relation: Relation, warnRedundant: bool):
        relationStr = self._correctSyntaxes(f"{relation.leftExpr} = {relation.rightExpr}")
        linesList = [relationStr]
        if warnRedundant:
            linesList = [
                "[yellow]Relation is redundant and provided no new inferences[/yellow]",
                *linesList,
            ]
        joinedLines = self._prefixAndJoinLines(linesList)
        return self._renderLines(joinedLines)

    def renderExpressions(self, exprs: tuple[sympy.Expr, ...]):
        joinedLines = self._prefixAndJoinLines(
            self._correctSyntaxes(str(expr))
            for expr in exprs
        )
        return self._renderLines(joinedLines)

    def renderException(self, exception: Exception):
        if isinstance(exception, TracebackException):
            assert len([
                eolToken
                for eolToken in exception.tokens
                if eolToken.type is LexerTokenTypes.EOL
            ]) <= 1, "Exception rendering cannot yet handle multiple input lines"
            
            formattingMap = {tokenIdx: "red" for tokenIdx in exception.badTokenIdxs}
            exprLine = self._formatTokens(exception.tokens, formattingMap)
            joinedLines = self._prefixAndJoinLinesForException((
                f"[white]{exprLine}[/white]",
                exception.message,
            ), exception)
            return self._renderLines(f"[#b0b0b0]{joinedLines}[/#b0b0b0]")
        
        elif isinstance(exception, MultilineException):
            joinedLines = self._prefixAndJoinLinesForException((
                self._correctSyntaxes(line)
                for line in exception.messageLines
            ), exception)
            return self._renderLines(f"[#b0b0b0]{joinedLines}[/#b0b0b0]")
        
        elif isinstance(exception, HandledException):
            joinedLines = self._prefixAndJoinLinesForException((
                str(exception),
                "",
                "[magenta]This error is missing a rendering rule, and the message above was generated automatically.",
                "If you see this, please submit an issue at [blue underline]https://github.com/skylon07/SolverPro/issues/new[/blue underline]",
                "with an explanation of how you got this message to show up.[/magenta]",
            ), exception)
            return self._renderLines(f"[#b0b0b0]{joinedLines}[/#b0b0b0]")
        
        else:
            joinedLines = self._prefixAndJoinLinesForException((
                f"[bold red]{type(exception).__name__}:[/bold red] [red]{str(exception)}[/red]",
            ), exception)
            return self._renderLines(joinedLines)

    def _prefixAndJoinLinesForException(self, lines: tuple[FormattedStr, ...], exception: Exception):
        isHandledException = isinstance(exception, HandledException)
        if isHandledException:
            return self._prefixAndJoinLines((
                "[red]Error![/red]",
                *lines,
            ))
        else:
            return self._prefixAndJoinLines((
                "[magenta]An unexpected error occurred![/magenta]",
                *lines,
                "",
                "[magenta]This is probably an issue with Solver Pro internally.",
                "If you see this, please submit an issue at [blue underline]https://github.com/skylon07/SolverPro/issues/new[/blue underline]",
                "with an explanation of how you got this message to show up.[/magenta]",
            ))

    def _prefixAndJoinLines(self, lines: tuple[FormattedStr, ...]):
        linePrefix = "    "
        prefixedLinesStr = linePrefix + f"\n{linePrefix}".join(lines)
        return prefixedLinesStr
    
    def _formatTokens(self, tokens: tuple[LexerToken, ...], formattingMap: dict[int, str]):
        formattedStr = ""
        lastToken = None
        for (tokenIdx, token) in enumerate(tokens):
            if lastToken is not None:
                idxDiff = token.matchIdx - lastToken.matchIdx
                numSpaces = idxDiff - len(lastToken.match)
                formattedStr += " " * numSpaces
            
            if tokenIdx in formattingMap:
                format = formattingMap[tokenIdx]
                formattedStr += f"[{format}]"
            formattedStr += token.match
            if tokenIdx in formattingMap:
                format = formattingMap[tokenIdx]
                formattedStr += f"[/{format}]"
            lastToken = token
        return formattedStr
    
    def _renderLines(self, linesStr: FormattedStr):
        return renderMarkup(linesStr)
    
    def _correctSyntaxes(self, exprStr: str):
        return self._powReplace(exprStr)
