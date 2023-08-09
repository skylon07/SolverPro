import sympy
from rich.console import Console

from src.common.exceptions import TracebackException, HandledException
from src.parsing.lexer import LexerToken, LexerTokenTypes


class TextRenderer:
    def __init__(self):
        self._renderConsole = Console()
    
    def renderRelation(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        relationStr = f"{leftExpr} = {rightExpr}"
        joinedLines = self._prefixAndJoinLines([relationStr])
        return self._renderConsole.render_str(joinedLines)

    def renderExpressions(self, exprs: tuple[sympy.Expr, ...]):
        joinedLines = self._prefixAndJoinLines(str(expr) for expr in exprs)
        return self._renderConsole.render_str(joinedLines)

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
                exprLine,
                exception.message,
            ), exception)
            return self._renderConsole.render_str(joinedLines)
        
        elif isinstance(exception, HandledException):
            joinedLines = self._prefixAndJoinLinesForException((
                str(exception),
            ), exception)
        
        else:
            joinedLines = self._prefixAndJoinLinesForException((
                f"[bold red]{type(exception).__name__}:[/bold red] [red]{str(exception)}[/red]",
            ), exception)
            return self._renderConsole.render_str(joinedLines)

    def _prefixAndJoinLinesForException(self, lines: tuple[str, ...], exception: Exception):
        isHandledException = isinstance(exception, HandledException)
        if isHandledException:
            return self._prefixAndJoinLines((
                "[red]Error![/red]",
                *lines,
            ))
        else:
            return self._prefixAndJoinLines((
                "[magenta]An unhandled error occurred![/magenta]",
                *lines,
                "",
                "This is probably an issue with Solver Pro.",
                "You can report it at https://github.com/skylon07/SolverPro/issues/new",
            ))

    def _prefixAndJoinLines(self, lines: tuple[str, ...]):
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
