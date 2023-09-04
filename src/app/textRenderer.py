import re
from typing import Iterable

import sympy
from rich.markup import render as renderMarkup

from src.common.types import FormattedStr
from src.common.exceptions import TracebackException, HandledException, MultilineException
from src.app.widgets.colors import Colors
from src.parsing.lexer import LexerToken, LexerTokenTypes
from src.algebrasolver.solver import Relation


class TextRenderer:
    def formatInputLog(self, inputStr: str, succeeded: bool):
        marker = f"[{Colors.textGreen.hex}]✓[/]" if succeeded \
            else f"[{Colors.textRed.hex}]✕[/]"
        return self._formatLines([marker + f" [{Colors.textPlain.hex}]{inputStr}[/]"])

    def formatRelation(self, relation: Relation, *, warnRedundant: bool = False):
        relationStr = self._correctExprSyntaxes(f"[{Colors.textPlain.hex}]{relation.leftExpr} = {relation.rightExpr}[/]")
        linesList = [relationStr]
        if warnRedundant:
            linesList.append(f"[{Colors.textYellow.hex}]Relation is redundant and provided no new inferences[/]")
        return self._formatLines(linesList)
    
    def formatRelationReplaced(self, oldRelation: Relation, newRelation: Relation, *, warnRedundant: bool):
        return self._formatLines([
            f"[{Colors.textMuted.hex}]Info: Relation[/]",
            self.formatRelation(oldRelation, warnRedundant = False),
            f"[{Colors.textMuted.hex}]was replaced by[/]",
            self.formatRelation(newRelation, warnRedundant = warnRedundant),
        ])
    
    def formatRelationDeleted(self, relation: Relation):
        return self._formatLines([
            f"[{Colors.textMuted.hex}]Info: Relation[/]",
            self.formatRelation(relation, warnRedundant = False),
            f"[{Colors.textMuted.hex}]was deleted[/]",
        ])
    
    def formatExpressions(self, exprs: Iterable[sympy.Expr]):
        return self._formatLines([
            self._correctExprSyntaxes(str(expr))
            for expr in exprs
        ])
    
    def formatException(self, exception: Exception, *, withErrorHeader: bool):
        if isinstance(exception, TracebackException):
            assert len([
                eolToken
                for eolToken in exception.tokens
                if eolToken.type is LexerTokenTypes.EOL
            ]) <= 1, "Exception rendering cannot yet handle multiple input lines"
            
            formattingMap = {tokenIdx: Colors.textRed.hex for tokenIdx in exception.badTokenIdxs}
            if exception.grayOutAfterBadTokens:
                formattingMap.update({
                    tokenIdx: Colors.textMuted.hex
                    for tokenIdx in range(max(exception.badTokenIdxs) + 1, len(exception.tokens))
                })
            exprLine = self._formatTokens(exception.tokens, formattingMap)
            return self._formatLinesForException(
                (
                    f"[{Colors.textPlain.hex}]{exprLine}[/]",
                    exception.message,
                ), 
                exception,
                withErrorHeader = withErrorHeader,
            )
        
        elif isinstance(exception, MultilineException):
            return self._formatLinesForException(
                (
                    self._correctExprSyntaxes(line)
                    for line in exception.messageLines
                ),
                exception, 
                withErrorHeader = withErrorHeader,
            )
        
        elif isinstance(exception, HandledException):
            return self._formatLinesForException(
                (
                    str(exception),
                    "",
                    f"[{Colors.textPurple.hex}]This error is missing a rendering rule, and the message above was generated automatically.",
                    f"If you see this, please submit an issue at [{Colors.textBlue.hex} underline]https://github.com/skylon07/SolverPro/issues/new[/]",
                    f"with an explanation of how you got this message to show up.[/{Colors.textPurple.hex}]",
                ),
                exception,
                withErrorHeader = withErrorHeader,
            )
        
        else:
            return self._formatLinesForException(
                (
                    f"[{Colors.textPurple.hex}]An unexpected error occurred![/]",
                    f"[bold {Colors.textRed.hex}]{type(exception).__name__}:[/] [{Colors.textRed.hex}]{str(exception)}[/]",
                    "",
                    f"[{Colors.textPurple.hex}]This is probably an issue with Solver Pro internally.",
                    f"If you see this, please submit an issue at [{Colors.textBlue.hex} underline]https://github.com/skylon07/SolverPro/issues/new[/]",
                    f"with an explanation of how you got this message to show up.[/{Colors.textPurple.hex}]",
                ),
                exception,
                withErrorHeader = withErrorHeader,
            )
        
    def render(self, formattedStr: FormattedStr, *, indent: bool = False):
        if indent:
            indentSpaces = "    "
            formattedStr = re.compile("\n").sub(f"\n{indentSpaces}", formattedStr)
        finalizedStr = self._sanitize(self._injectTermLinks(formattedStr))
        return renderMarkup(finalizedStr)
        
    def _formatLines(self, lines: Iterable[FormattedStr]):
        return "\n".join(lines)
    
    def _formatLinesForException(self, lines: Iterable[FormattedStr], exception: Exception, *, withErrorHeader: bool):
        if withErrorHeader:
            lines = [
                f"[bold {Colors.textRed.hex}]Error![/]",
                *lines,
            ]
        return self._formatLines(lines)
    
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
    
    def _correctExprSyntaxes(self, exprStr: str):
        exprStr = re.compile(r"\*\*").sub("^", exprStr)
        return exprStr
    
    def _sanitize(self, linesStr: FormattedStr) -> FormattedStr:
        return linesStr.replace("\\", "�")
    
    def _injectTermLinks(self, text: FormattedStr) -> FormattedStr:
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
