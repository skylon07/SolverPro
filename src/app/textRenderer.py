import re
from typing import Iterable

import sympy
from rich.markup import render as renderMarkup

from src.common.types import FormattedStr
from src.common.functions import surroundJoin
from src.common.exceptions import TracebackException, HandledException, MultilineException
from src.parsing.lexer import LexerToken, LexerTokenTypes
from src.algebrasolver.solver import Relation


class TextRenderer:
    def __init__(self):
        powRegex = re.compile(r"\*\*")
        self._powReplace = lambda exprStr: powRegex.sub("^", exprStr)

    def renderInputLog(self, inputStr: str, succeeded: bool):
        marker = "[green]✓[/green]" if succeeded \
            else "[red]✕[/red]"
        return self._renderLines(marker + f" {inputStr}")

    def renderRelation(self, relation: Relation, warnRedundant: bool, replacedRelation: Relation | None = None, wasDeleted: bool = False):
        relationStr = self._correctSyntaxes(f"[white]{relation.leftExpr} = {relation.rightExpr}[/white]")
        wasReplaced = replacedRelation is not None
        if wasReplaced:
            linesList = [
                "[#b0b0b0]Info: Relation[/#b0b0b0]",
                self._correctSyntaxes(f"[white]{replacedRelation.leftExpr} = {replacedRelation.rightExpr}[/white]"),
                "[#b0b0b0]was replaced by[/#b0b0b0]",
                relationStr,
            ]
        elif wasDeleted:
            linesList = [
                "[#b0b0b0]Info: Relation[/#b0b0b0]",
                relationStr,
                "[#b0b0b0]was deleted[/#b0b0b0]",
            ]
        else:
            linesList = [relationStr]
        
        if warnRedundant:
            linesList.append("[yellow]Relation is redundant and provided no new inferences[/yellow]")
        joinedLines = self._prefixAndJoinLines(linesList)
        return self._renderLines(joinedLines)

    def renderExpressions(self, exprs: tuple[sympy.Expr, ...]):
        joinedLines = self._prefixAndJoinLines(
            self._correctSyntaxes(str(expr))
            for expr in exprs
        )
        return self._renderLines(joinedLines)

    def renderException(self, exception: Exception, withErrorHeader: bool = True):
        if isinstance(exception, TracebackException):
            assert len([
                eolToken
                for eolToken in exception.tokens
                if eolToken.type is LexerTokenTypes.EOL
            ]) <= 1, "Exception rendering cannot yet handle multiple input lines"
            
            formattingMap = {tokenIdx: "red" for tokenIdx in exception.badTokenIdxs}
            if exception.grayOutAfterBadTokens:
                formattingMap.update({
                    tokenIdx: "#b0b0b0"
                    for tokenIdx in range(max(exception.badTokenIdxs) + 1, len(exception.tokens))
                })
            exprLine = self._formatTokens(exception.tokens, formattingMap)
            joinedLines = self._prefixAndJoinLinesForException((
                f"[white]{exprLine}[/white]",
                exception.message,
            ), exception, withErrorHeader)
            return self._renderLines(f"[#b0b0b0]{joinedLines}[/#b0b0b0]")
        
        elif isinstance(exception, MultilineException):
            joinedLines = self._prefixAndJoinLinesForException((
                self._correctSyntaxes(line)
                for line in exception.messageLines
            ), exception, withErrorHeader)
            return self._renderLines(f"[#b0b0b0]{joinedLines}[/#b0b0b0]")
        
        elif isinstance(exception, HandledException):
            joinedLines = self._prefixAndJoinLinesForException((
                str(exception),
                "",
                "[magenta]This error is missing a rendering rule, and the message above was generated automatically.",
                "If you see this, please submit an issue at [blue underline]https://github.com/skylon07/SolverPro/issues/new[/blue underline]",
                "with an explanation of how you got this message to show up.[/magenta]",
            ), exception, withErrorHeader)
            return self._renderLines(f"[#b0b0b0]{joinedLines}[/#b0b0b0]")
        
        else:
            joinedLines = self._prefixAndJoinLinesForException((
                f"[bold red]{type(exception).__name__}:[/bold red] [red]{str(exception)}[/red]",
            ), exception, withErrorHeader)
            return self._renderLines(joinedLines)

    def _prefixAndJoinLinesForException(self, lines: Iterable[FormattedStr], exception: Exception, renderErrorHeader: bool):
        isHandledException = isinstance(exception, HandledException)
        if isHandledException:
            lines = list(lines)
            if renderErrorHeader:
                lines.insert(0, "[red]Error![/red]")
            return self._prefixAndJoinLines(lines)
        else:
            return self._prefixAndJoinLines((
                "[magenta]An unexpected error occurred![/magenta]",
                *lines,
                "",
                "[magenta]This is probably an issue with Solver Pro internally.",
                "If you see this, please submit an issue at [blue underline]https://github.com/skylon07/SolverPro/issues/new[/blue underline]",
                "with an explanation of how you got this message to show up.[/magenta]",
            ))

    def _prefixAndJoinLines(self, lines: Iterable[FormattedStr]):
        linePrefix = "    "
        prefixedLinesStr = surroundJoin(lines, linePrefix, "", "\n")
        return prefixedLinesStr
    
    def _formatTokens(self, tokens: Iterable[LexerToken], formattingMap: dict[int, str]):
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
        return renderMarkup(self._injectTermLinks(self._sanitize(linesStr)))
    
    def _sanitize(self, linesStr: FormattedStr):
        return linesStr.replace("\\", "�")
    
    def _correctSyntaxes(self, exprStr: str):
        return self._powReplace(exprStr)
    
    def _injectTermLinks(self, text: FormattedStr):
        # done in reverse to avoid keeping track of index offsets after replacement
        for match in reversed(tuple(re.compile(r"__.*?__").finditer(text))):
            (matchStartIdx, matchEndIdx) = match.span()
            textBeforeMatch = text[:matchStartIdx]
            matchedText = match.group()
            syntaxLength = len("__")
            term = matchedText[syntaxLength : -syntaxLength]
            textAfterMatch = text[matchEndIdx:]
            text = f"{textBeforeMatch}[@click=showTermTip('{term}')][underline]{term}[/underline][/@click]{textAfterMatch}"
        return text
