import re
from typing import Iterable, Callable

import sympy
from textual.color import Color
from rich.markup import render as renderMarkup
from rich.text import Text

from src.common.types import FormattedStr
from src.common.exceptions import TracebackException, HandledException, MultilineException
from src.app.widgets.colors import Colors
from src.parsing.lexer import LexerToken, LexerTokenTypes, CommandLexer
from src.parsing.parser import AliasTemplate
from src.algebrasolver.solver import Relation


TokenFormatFn = Callable[[tuple[LexerToken, ...], int], Color]


class TextRenderer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        isAlreadyInitialized = getattr(self, "_initialized", False)
        if isAlreadyInitialized:
            return
        
        self._initialized = True
        self._lexer = CommandLexer()
        self._driver = None

    def useAliasProvider(self, aliasProvider):
        from src.app.appDriver import AppDriver
        assert aliasProvider is None or type(aliasProvider) is AppDriver
        self._driver = aliasProvider
    
    def formatInputLog(self, inputStr: str, succeeded: bool, *, highlightSyntax: bool = True):
        marker = f"[{Colors.textGreen.hex}]✓[/]" if succeeded \
            else f"[{Colors.textRed.hex}]✕[/]"
        if highlightSyntax:
            inputStr = self.formatLexerSyntax(inputStr)
        return self._formatLines([marker + f" [{Colors.textPlain.hex}]{inputStr}[/]"])
    
    def formatLexerSyntax(self, text: str):
        tokenFormats = {
            LexerTokenTypes.IDENTIFIER:     self._identifierFormat,
            LexerTokenTypes.INTEGER:        Colors.number,
            LexerTokenTypes.FLOAT:          Colors.number,
            LexerTokenTypes.PAREN_OPEN:     Colors.punctuation,
            LexerTokenTypes.PAREN_CLOSE:    Colors.punctuation,
            LexerTokenTypes.BRACE_OPEN:     Colors.punctuation,
            LexerTokenTypes.BRACE_CLOSE:    Colors.punctuation,
            LexerTokenTypes.BACKTICK:       Colors.punctuation,
            LexerTokenTypes.COMMA:          Colors.punctuation,
            LexerTokenTypes.EQUALS:         Colors.operator,
            LexerTokenTypes.COLON_EQUALS:   Colors.operator,
            LexerTokenTypes.PLUS:           Colors.operator,
            LexerTokenTypes.DASH:           Colors.operator,
            LexerTokenTypes.STAR:           Colors.operator,
            LexerTokenTypes.SLASH:          Colors.operator,
            LexerTokenTypes.CARROT:         Colors.operator,
            LexerTokenTypes.INVALID:        Colors.textRed,
        }
        tokens = tuple(self._lexer.findTokens(text))
        replacements = {
            tokenIdx: tokenFormats[token.type]
            for (tokenIdx, token) in enumerate(tokens)
            if token.type in tokenFormats
        }
        return self._sanitizeInput(f"[{Colors.textPlain.hex}]{self._formatTokens(tokens, replacements)}[/]")
    
    def _identifierFormat(self, tokens: tuple[LexerToken, ...], tokenIdx: int):
        token = tokens[tokenIdx]
        if self._driver is not None:
            if token.match in self._driver.getAllAliasNames():
                return Colors.alias
        if tokenIdx + 1 < len(tokens):
            nextToken = tokens[tokenIdx + 1]
            if nextToken.type in (LexerTokenTypes.PAREN_OPEN, LexerTokenTypes.COLON_EQUALS):
                return Colors.alias
        return Colors.identifier

    def formatRelation(self, relation: Relation, *, warnRedundant: bool = False, highlightSyntax: bool = False):
        relationStr = self._correctExprSyntaxes(f"{relation.leftExpr} = {relation.rightExpr}")
        if highlightSyntax:
            relationStr = self.formatLexerSyntax(relationStr)
        linesList = [relationStr]
        if warnRedundant:
            linesList.append(f"[{Colors.textYellow.hex}]Relation is redundant and provided no new inferences[/]")
        return self._formatLines(linesList)
    
    def formatRelationsRecorded(self, relationsData: list[tuple[Relation, bool]], *, highlightSyntax: bool = False):
        return self._formatLines(
            self.formatRelation(relation, warnRedundant = isRedundant, highlightSyntax = highlightSyntax)
            for (relation, isRedundant) in relationsData
        )
    
    def formatRelationReplaced(self, oldRelation: Relation, newRelation: Relation, *, warnRedundant: bool, highlightSyntax: bool = False):
        return self._formatLines([
            f"[{Colors.textMuted.hex}]Relation[/]",
            self.formatRelation(oldRelation, warnRedundant = False, highlightSyntax = highlightSyntax),
            f"[{Colors.textMuted.hex}]was replaced by[/]",
            self.formatRelation(newRelation, warnRedundant = warnRedundant, highlightSyntax = highlightSyntax),
        ])
    
    def formatRelationDeleted(self, relation: Relation, *, highlightSyntax: bool = False):
        return self._formatLines([
            f"[{Colors.textMuted.hex}]Relation[/]",
            self.formatRelation(relation, warnRedundant = False, highlightSyntax = highlightSyntax),
            f"[{Colors.textMuted.hex}]was deleted[/]",
        ])
    
    def formatExpressions(self, exprs: Iterable[sympy.Expr], *, highlightSyntax: bool = False):
        return self._formatLines([
            self.formatLexerSyntax(exprStr) if highlightSyntax
                else exprStr
            for expr in exprs
            for exprStr in [self._correctExprSyntaxes(str(expr))]
        ])
    
    def formatAliasTemplate(self, aliasTemplate: AliasTemplate, *, highlightSyntax: bool = False):
        aliasStr = aliasTemplate.name
        if aliasTemplate.numArgs > 0:
            aliasStr += "(" + ", ".join(aliasTemplate.argNames) + ")"
        aliasStr += " := " + self._formatTokens(aliasTemplate.templateTokens, dict())
        return self._sanitizeInput(self._formatLines([
            self.formatLexerSyntax(aliasStr) if highlightSyntax
                else aliasStr
        ]))
    
    def formatException(self, exception: Exception, *, withErrorHeader: bool):
        if isinstance(exception, TracebackException):
            assert len([
                eolToken
                for eolToken in exception.tokens
                if eolToken.type is LexerTokenTypes.EOL
            ]) <= 1, "Exception rendering cannot yet handle multiple input lines"
            
            formattingMap: dict[int, Color | TokenFormatFn] = {tokenIdx: Colors.textRed for tokenIdx in exception.badTokenIdxs}
            if exception.grayOutAfterBadTokens:
                formattingMap.update({
                    tokenIdx: Colors.textMuted
                    for tokenIdx in range(max(exception.badTokenIdxs) + 1, len(exception.tokens))
                })
            exprLine = self._formatTokens(tuple(exception.tokens), formattingMap)
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
            formattedStr = indentSpaces + re.compile("\n").sub(f"\n{indentSpaces}", formattedStr)
        finalizedStr = self._injectTermLinks(formattedStr)
        rendering = renderMarkup(finalizedStr)
        return Text(
            self._restoreSanitizedChars(str(rendering)),
            style       = rendering.style,
            justify     = rendering.justify,
            overflow    = rendering.overflow,
            no_wrap     = rendering.no_wrap,
            end         = rendering.end,
            tab_size    = rendering.tab_size,
            spans       = rendering.spans
        )
        
    def _formatLines(self, lines: Iterable[FormattedStr]):
        return "\n".join(lines)
    
    def _formatLinesForException(self, lines: Iterable[FormattedStr], exception: Exception, *, withErrorHeader: bool):
        if withErrorHeader:
            lines = [
                f"[bold {Colors.textRed.hex}]Error![/]",
                *lines,
            ]
        return self._sanitizeInput(self._formatLines(lines))
    
    def _formatTokens(self, tokens: tuple[LexerToken, ...], formattingMap: dict[int, Color | TokenFormatFn]):
        formattedStr = ""
        lastToken = None
        for (tokenIdx, token) in enumerate(tokens):
            formattedStr += token.makeWhitespaceTo(lastToken)
            
            if tokenIdx in formattingMap:
                formatRule = formattingMap[tokenIdx]
                if isinstance(formatRule, Color):
                    format = formatRule.hex
                else:
                    format = formatRule(tokens, tokenIdx).hex
                formattedStr += f"[{format}]"
                formattedStr += token.match
                formattedStr += f"[/{format}]"
            else:
                formattedStr += token.match
            lastToken = token
        return formattedStr
    
    def _correctExprSyntaxes(self, exprStr: str):
        exprStr = re.compile(r"\*\*").sub("^", exprStr)
        exprStr = re.compile(r"(?<![a-zA-z0-9])E(?![a-zA-z0-9])").sub("e", exprStr)
        exprStr = re.compile(r"(?<![a-zA-z0-9])I(?![a-zA-z0-9])").sub("i", exprStr)
        exprStr = re.compile(r"(?<![a-zA-z0-9])sqrt(?![a-zA-z0-9])").sub("√", exprStr)
        exprStr = re.compile(r"(?<![a-zA-z0-9])cbrt(?![a-zA-z0-9])").sub("∛", exprStr)
        return exprStr
    
    def _sanitizeInput(self, linesStr: FormattedStr) -> FormattedStr:
        return linesStr.replace("\\", "◊")
    
    def _restoreSanitizedChars(self, linesStr: FormattedStr):
        return linesStr.replace("◊", "\\")
    
    def _injectTermLinks(self, text: FormattedStr) -> FormattedStr:
        # done in reverse to avoid keeping track of index offsets after replacement
        for match in reversed(tuple(re.compile(r"\[@termtip\].*?\[/@termtip\]").finditer(text))):
            (matchStartIdx, matchEndIdx) = match.span()
            textBeforeMatch = text[:matchStartIdx]
            matchedText = match.group()
            labelStartLength = len("[@termtip]")
            labelEndLength = len("[/@termtip]")
            term = matchedText[labelStartLength : -labelEndLength]
            textAfterMatch = text[matchEndIdx:]
            text = f"{textBeforeMatch}[@click=showTermTip('{term}')][underline]{term}[/underline][/@click]{textAfterMatch}"
        return text
