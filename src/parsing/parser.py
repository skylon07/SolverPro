from typing import Callable

import sympy

from src.common.types import Enum, EnumString
from src.common.exceptions import TracebackException
from src.app.widgets.colors import Colors
from src.parsing.lexer import LexerTokenType, LexerTokenTypes, LexerToken


# so the dang linter doesn't take FOREVER...
createSymbol = eval("sympy.Symbol")


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


class CommandParser:
    def parseCommand(self, commandTokens: tuple[LexerToken, ...]):
        while len(commandTokens) > 0:
            sequencer = _CommandParserSequencer(commandTokens)
            command = sequencer.sequenceCommand()
            yield command
            commandTokens = commandTokens[sequencer.numTokensParsed:]

    def parseExpressionList(self, exprListTokens: tuple[LexerToken, ...]):
        sequencer = _CommandParserSequencer(exprListTokens)
        expressions = sequencer.sequenceExpressionList()
        return expressions

    def preprocessAliases(self, tokens: tuple[LexerToken, ...], aliases: dict[str, Callable[..., str]]):
        sequencer = _CommandAliasSequencer(tokens, aliases)
        processedTokens = sequencer.sequenceExpression(isPrimary = True)
        return processedTokens


class _Sequencer:
    def __init__(self, tokens: tuple[LexerToken, ...]):
        self._tokens = tokens
        self._setNumTokensParsed(0)

    def _setNumTokensParsed(self, numParsed: int):
        self.numTokensParsed = numParsed
        self._moreTokens = self.numTokensParsed < len(self._tokens)

    @property
    def _currToken(self) -> LexerToken:
        if self._moreTokens:
            currToken = self._tokens[self.numTokensParsed]
            return currToken
        return self._throwEolException()

    def _consumeCurrToken(self, expectedTokenType: LexerTokenType):
        if self._currToken.type is not expectedTokenType:
            self._throwUnexpectedToken((expectedTokenType,))
        
        self._setNumTokensParsed(self.numTokensParsed + 1)

    def _generateSpacesBeforeCurrToken(self):
        if self.numTokensParsed > 0:
            lastToken = self._tokens[self.numTokensParsed - 1]
            positionDiff = self._currToken.matchIdx - lastToken.matchIdx
            numSpaces = positionDiff - len(lastToken.match)
        else:
            numSpaces = self._currToken.matchIdx
        return " " * numSpaces

    def _throwUnexpectedToken(self, expectedTypes: tuple[LexerTokenType, ...]):
        if self._currToken.type is LexerTokenTypes.EOL:
            return self._throwEolException()
        else:
            raise ParseException(expectedTypes, self._tokens, self.numTokensParsed)
    
    def _throwEolException(self):
        raise EolException(self._tokens, self.numTokensParsed)


class _CommandParserSequencer(_Sequencer):
    _lowPrecOpers = (
        LexerTokenTypes.PLUS,
        LexerTokenTypes.DASH,
    )
    _midPrecOpers = (
        LexerTokenTypes.STAR,
        LexerTokenTypes.SLASH,
    )
    _highPrecUnaryOpers = (
        LexerTokenTypes.PLUS,
        LexerTokenTypes.DASH,
    )
    _highPrecBinaryOpers = (
        LexerTokenTypes.CARROT,
    )
    _numberTypes = (
        LexerTokenTypes.INTEGER,
        LexerTokenTypes.FLOAT,
    )
    _valueTypes = _numberTypes + (
        LexerTokenTypes.IDENTIFIER,
    )

    def __init__(self, tokens: tuple[LexerToken, ...]):
        super().__init__(tokens)
        self._allowExpressionList = True
        self._allowIdentifierValues = True

    def _convertLowPrecExprList(self, lowPrecExprList: list) -> sympy.Expr:
        for (idx, item) in enumerate(lowPrecExprList):
            if type(item) is list:
                midPrecExprList = item
                lowPrecExprList[idx] = self._convertMidPrecExprList(midPrecExprList)
        
        finalExpr: sympy.Expr = lowPrecExprList[0]
        for (idx, operToken) in enumerate(lowPrecExprList):
            if type(operToken) is LexerToken:
                if operToken.type is LexerTokenTypes.PLUS:
                    operand = lowPrecExprList[idx + 1]
                    finalExpr = finalExpr + operand
                elif operToken.type is LexerTokenTypes.DASH:
                    operand = lowPrecExprList[idx + 1]
                    finalExpr = finalExpr - operand
                else:
                    raise NotImplementedError(f"Unconsidered token type {operToken.type}(low prec)")
        return finalExpr

    def _convertMidPrecExprList(self, midPrecExprList: list) -> sympy.Expr:
        for (idx, item) in enumerate(midPrecExprList):
            if type(item) is list:
                highPrecExprList = item
                midPrecExprList[idx] = self._convertHighPrecExprList(highPrecExprList)
        
        finalExpr: sympy.Expr = midPrecExprList[0]
        for (idx, operToken) in enumerate(midPrecExprList):
            if type(operToken) is LexerToken:
                if operToken.type is LexerTokenTypes.STAR:
                    operand = midPrecExprList[idx + 1]
                    finalExpr = finalExpr * operand
                elif operToken.type is LexerTokenTypes.SLASH:
                    operand = midPrecExprList[idx + 1]
                    finalExpr = finalExpr / operand
                else:
                    raise NotImplementedError(f"Unconsidered token type {operToken.type}(mid prec)")
        return finalExpr

    def _convertHighPrecExprList(self, highPrecExprList: list) -> sympy.Expr:
        for (idx, valuePair) in enumerate(highPrecExprList):
            if type(valuePair) is tuple:
                (valueType, valueStr) = valuePair
                if valueType is LexerTokenTypes.IDENTIFIER:
                    value = createSymbol(valueStr)
                else:
                    value = sympy.parse_expr(valueStr)
                highPrecExprList[idx] = value
        
        # reversed since these operators parse right-to-left
        finalExpr: sympy.Expr = highPrecExprList[-1]
        for (revIdx, operToken) in enumerate(reversed(highPrecExprList)):
            if type(operToken) is LexerToken:
                idx = -(revIdx + 1)
                if operToken.type is LexerTokenTypes.PLUS:
                    finalExpr = +finalExpr
                elif operToken.type is LexerTokenTypes.DASH:
                    finalExpr = -finalExpr
                elif operToken.type is LexerTokenTypes.CARROT:
                    operand = highPrecExprList[idx - 1]
                    finalExpr = operand ** finalExpr
                else:
                    raise NotImplementedError(f"Unconsidered token type {operToken.type}(high prec)")
        return finalExpr

    def sequenceCommand(self):
        # branch: EOL
        if self._currToken.type is LexerTokenTypes.EOL:
            self._consumeCurrToken(LexerTokenTypes.EOL)
            return Command.empty()
        
        # distinguish branches: relation, expression, aliasTemplate
        idx = self.numTokensParsed
        isRelation = False
        isAliasTemplate = False
        while idx < len(self._tokens):
            token = self._tokens[idx]
            if token.type is LexerTokenTypes.EQUALS:
                isRelation = True
                break
            elif token.type is LexerTokenTypes.COLON_EQUALS:
                isAliasTemplate = True
                break
            idx += 1

        # branch: relation EOL
        if isRelation:
            relation = self.sequenceRelation()
            self._consumeCurrToken(LexerTokenTypes.EOL)
            return Command.recordRelation(relation)
        
        # branch: aliasTemplate EOL
        if isAliasTemplate:
            aliasTemplate = self.sequenceAliasTemplate()
            self._consumeCurrToken(LexerTokenTypes.EOL)
            return Command.recordAlias(aliasTemplate)
        
        # default branch: expression EOL
        expression = self.sequenceExpression()
        self._consumeCurrToken(LexerTokenTypes.EOL)
        return Command.evaluateExpression(expression)
    
    def sequenceRelation(self):
        # default branch: expression EQUALS expression
        leftExpr = self.sequenceExpression()
        self._consumeCurrToken(LexerTokenTypes.EQUALS)
        rightExpr = self.sequenceExpression()
        return (leftExpr, rightExpr)
    
    def sequenceExpression(self):
        # default branch: lowPrecExpr
        lowPrecExprList = self.sequenceLowPrecExpr()
        expression = self._convertLowPrecExprList(lowPrecExprList)
        return expression
    
    def sequenceExpressionList(self) -> list[sympy.Expr]:
        # (all branches)
        expressions = [self.sequenceExpression()]

        # distinguish branches: expression, expression COMMA expression, ...
        while self._currToken.type is LexerTokenTypes.COMMA:
            self._consumeCurrToken(LexerTokenTypes.COMMA)
            expressions.append(self.sequenceExpression())

        # default branch: expression
        # branch: expression COMMA expression
        # branch: expression COMMA expression COMMA expression
        # ...
        return expressions
    
    def sequenceLowPrecExpr(self):
        # (all branches)
        midPrecExprList = self.sequenceMidPrecExpr()

        # branch: midPrecExpr operLow lowPrecExpr
        if self._moreTokens and self._currToken.type in self._lowPrecOpers:
            lowPrecOperToken = self.sequenceOperLow()
            expandedExprList = self.sequenceLowPrecExpr()
            expandedExprList.insert(0, lowPrecOperToken)
            expandedExprList.insert(0, midPrecExprList)
            return expandedExprList
        
        # default branch: midPrecExpr
        return [midPrecExprList]
    
    def sequenceMidPrecExpr(self):
        # (all branches)
        highPrecExprList = self.sequenceHighPrecExpr()

        # branch: highPrecExpr operMid midPrecExpr
        if self._moreTokens and self._currToken.type in self._midPrecOpers:
            midPrecOperToken = self.sequenceOperMid()
            expandedExprList = self.sequenceMidPrecExpr()
            expandedExprList.insert(0, midPrecOperToken)
            expandedExprList.insert(0, highPrecExprList)
            return expandedExprList
        
        # default branch: highPrecExpr
        return [highPrecExprList]
    
    def sequenceHighPrecExpr(self):
        # branch: operHigh highPrecExpr
        if self._moreTokens and self._currToken.type in self._highPrecUnaryOpers:
            highPrecOperToken = self.sequenceUnaryOperHigh()
            expandedExprList = self.sequenceHighPrecExpr()
            expandedExprList.insert(0, highPrecOperToken)
            return expandedExprList
        
        # (rest of branches)
        evaluation = self.sequenceEvaluation()
        
        # branch: evaluation operHigh highPrecExpr
        if self._moreTokens and self._currToken.type in self._highPrecBinaryOpers:
            highPrecOperToken = self.sequenceBinaryOperHigh()
            expandedExprList = self.sequenceHighPrecExpr()
            expandedExprList.insert(0, highPrecOperToken)
            expandedExprList.insert(0, evaluation)
            return expandedExprList
        
        # default branch: evaluation
        return [evaluation]

    def sequenceOperLow(self):
        # branch: PLUS/DASH
        validLowOpers = (
            LexerTokenTypes.PLUS,
            LexerTokenTypes.DASH,
        )
        if self._currToken.type in validLowOpers:
            lowPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return lowPrecOperToken
        
        return self._throwUnexpectedToken(validLowOpers)

    def sequenceOperMid(self):
        # branch: STAR/SLASH
        validMidOpers = (
            LexerTokenTypes.STAR,
            LexerTokenTypes.SLASH,
        )
        if self._currToken.type in validMidOpers:
            midPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return midPrecOperToken
        
        return self._throwUnexpectedToken(validMidOpers)
    
    def sequenceUnaryOperHigh(self):
        # branch: PLUS/DASH
        if self._currToken.type in self._highPrecUnaryOpers:
            highPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return highPrecOperToken
        
        return self._throwUnexpectedToken(self._highPrecUnaryOpers)
    
    def sequenceBinaryOperHigh(self):
        # branch: CARROT
        if self._currToken.type in self._highPrecBinaryOpers:
            highPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return highPrecOperToken
        
        return self._throwUnexpectedToken(self._highPrecBinaryOpers)

    def sequenceEvaluation(self) -> sympy.Expr | tuple[LexerTokenType, str]:
        # branch: PAREN_OPEN expression PAREN_CLOSE
        if self._currToken.type is LexerTokenTypes.PAREN_OPEN:
            self._consumeCurrToken(LexerTokenTypes.PAREN_OPEN)
            expression = self.sequenceExpression()
            self._consumeCurrToken(LexerTokenTypes.PAREN_CLOSE)
            return expression
        
        # branch: BRACE_OPEN expressionList BRACE_CLOSE
        elif self._currToken.type is LexerTokenTypes.BRACE_OPEN and self._allowExpressionList:
            self._consumeCurrToken(LexerTokenTypes.BRACE_OPEN)
            self._allowExpressionList = False
            self._allowIdentifierValues = False
            expressions = self.sequenceExpressionList()
            expressions.sort() # type: ignore (it does work)
            self._allowIdentifierValues = True
            self._allowExpressionList = True
            self._consumeCurrToken(LexerTokenTypes.BRACE_CLOSE)
            expressionsStr = ", ".join(str(expr) for expr in expressions)
            return createSymbol(f"{{{expressionsStr}}}")

        # # default branch: value/number
        if self._allowIdentifierValues:
            (tokenType, valueStr) = self.sequenceValue()
        else:
            (tokenType, valueStr) = self.sequenceNumber()
        return (tokenType, valueStr)

    def sequenceValue(self):
        tokenType = self._currToken.type

        # (all valid branches)
        if self._currToken.type in self._valueTypes:
            valueStr = self._currToken.match
            self._consumeCurrToken(self._currToken.type)
            return (tokenType, valueStr)
        
        return self._throwUnexpectedToken(self._valueTypes)
    
    def sequenceNumber(self):
        tokenType = self._currToken.type

        # (all valid branches)
        if self._currToken.type in self._numberTypes:
            numberStr = self._currToken.match
            self._consumeCurrToken(self._currToken.type)
            return (tokenType, numberStr)
        
        return self._throwUnexpectedToken(self._numberTypes)
    
    def sequenceIdentifier(self):
        identifier = self._currToken.match
        self._consumeCurrToken(LexerTokenTypes.IDENTIFIER)
        return identifier
    
    def sequenceAliasTemplate(self):
        # (all branches)
        aliasName = self._currToken.match
        self._consumeCurrToken(LexerTokenTypes.IDENTIFIER)

        # distinguish branches: IDENTIFIER COLON_EQUALS aliasTemplateStr, IDENTIFIER aliasTemplateArgs COLON_EQUALS aliasTemplateStr
        aliasArgs: tuple[str, ...]
        if self._currToken.type is LexerTokenTypes.PAREN_OPEN:
            aliasArgs = self.sequenceAliasTemplateArgs()
        else:
            aliasArgs = tuple()

        # (all branches)
        self._consumeCurrToken(LexerTokenTypes.COLON_EQUALS)
        templateStr = self.sequenceAliasTemplateStr()

        # default branch: IDENTIFIER
        # branch: IDENTIFIER COLON_EQUALS aliasTemplateStr
        # branch: IDENTIFIER aliasTemplateArgs COLON_EQUALS aliasTemplateStr
        return (aliasName, aliasArgs, templateStr)
    
    def sequenceAliasTemplateArgs(self):
        # (all branches)
        self._consumeCurrToken(LexerTokenTypes.PAREN_OPEN)

        # distinguish branches: PAREN_OPEN PAREN_CLOSE, PAREN_OPEN IDENTIFIER PAREN_CLOSE, ...
        aliasArgNames: list[str]
        if self._currToken.type is not LexerTokenTypes.PAREN_CLOSE:
            # distinguish branches: expression, expression COMMA expression, ...
            aliasArgNames = [self.sequenceIdentifier()]
            while self._currToken.type is LexerTokenTypes.COMMA:
                self._consumeCurrToken(LexerTokenTypes.COMMA)
                aliasArgNames.append(self.sequenceIdentifier())
        else:
            aliasArgNames = list()
        self._consumeCurrToken(LexerTokenTypes.PAREN_CLOSE)

        # default branch: PAREN_OPEN PAREN_CLOSE
        # branch: PAREN_OPEN IDENTIFIER PAREN_CLOSE
        # branch: PAREN_OPEN IDENTIFIER COMMA IDENTIFIER PAREN_CLOSE
        # ...
        return tuple(aliasArgNames)
    
    def sequenceAliasTemplateStr(self):
        # default branch: ... EOL
        templateStr = ""
        while self._currToken.type is not LexerTokenTypes.EOL:
            templateStr += self._generateSpacesBeforeCurrToken()
            templateStr += self._currToken.match
            self._consumeCurrToken(self._currToken.type)
        return templateStr.strip()
    

class _CommandAliasSequencer(_Sequencer):
    _expressionDelimiters = (
        LexerTokenTypes.COMMA,
        LexerTokenTypes.PAREN_CLOSE,
        LexerTokenTypes.EOL,
    )

    def __init__(self, tokens: tuple[LexerToken, ...], aliases: dict[str, Callable[..., str]]):
        super().__init__(tokens)
        self._aliases = aliases
        self._allowBacktickExpressions = False

    def sequenceExpression(self, *, isPrimary: bool) -> str:
        exprStr = ""
        parensToClose = 0
        # branch: ... (delimiter)
        delimiters = (LexerTokenTypes.EOL,) if isPrimary \
            else self._expressionDelimiters
        while self._currToken.type not in delimiters or parensToClose > 0:
            # sub-branch: BACKTICK <any> <any> ... BACKTICK
            if self._currToken.type is LexerTokenTypes.BACKTICK and self._allowBacktickExpressions:
                self._consumeCurrToken(LexerTokenTypes.BACKTICK)
                while self._currToken.type is not LexerTokenTypes.BACKTICK:
                    exprStr += self._generateSpacesBeforeCurrToken()
                    exprStr += self._currToken.match
                    self._consumeCurrToken(self._currToken.type)
                self._consumeCurrToken(LexerTokenTypes.BACKTICK)
            
            # sub-branch: aliasCall
            elif self._currToken.type is LexerTokenTypes.IDENTIFIER and self._currToken.match in self._aliases:
                exprStr += self._generateSpacesBeforeCurrToken()
                aliasValue = self.sequenceAliasCall()
                exprStr += aliasValue
            
            # sub-branch: <any>
            else:
                if self._currToken.type is LexerTokenTypes.PAREN_OPEN:
                    parensToClose += 1
                elif self._currToken.type is LexerTokenTypes.PAREN_CLOSE:
                    parensToClose -= 1
                    assert parensToClose >= 0
                exprStr += self._generateSpacesBeforeCurrToken()
                exprStr += self._currToken.match
                self._consumeCurrToken(self._currToken.type)
        return exprStr
    
    def sequenceAliasCall(self):
        # (all branches)
        aliasName = self._currToken.match
        self._consumeCurrToken(LexerTokenTypes.IDENTIFIER)

        # distinguish branches: IDENTIFIER, IDENTIFIER aliasArgs
        aliasArgs: tuple[str, ...]
        if self._currToken.type is LexerTokenTypes.PAREN_OPEN:
            aliasArgs = self.sequenceAliasCallArgs()
        else:
            aliasArgs = tuple()

        # default branch: IDENTIFIER
        # branch: IDENTIFIER aliasArgs
        # TODO: check function argument length
        aliasValue = self._aliases[aliasName](*aliasArgs)
        return aliasValue
    
    def sequenceAliasCallArgs(self):
        # (all branches)
        self._consumeCurrToken(LexerTokenTypes.PAREN_OPEN)

        # distinguish branches: PAREN_OPEN PAREN_CLOSE, PAREN_OPEN expression PAREN_CLOSE, ...
        aliasArgs: list[str]
        if self._currToken.type is not LexerTokenTypes.PAREN_CLOSE:
            prevAllowBacktickExpressions = self._allowBacktickExpressions
            self._allowBacktickExpressions = True
            # distinguish branches: expression, expression COMMA expression, ...
            aliasArgs = [self.sequenceExpression(isPrimary = False).strip()]
            while self._currToken.type is LexerTokenTypes.COMMA:
                self._consumeCurrToken(LexerTokenTypes.COMMA)
                aliasArgs.append(self.sequenceExpression(isPrimary = False).strip())
            self._allowBacktickExpressions = prevAllowBacktickExpressions
        else:
            aliasArgs = list()
        self._consumeCurrToken(LexerTokenTypes.PAREN_CLOSE)

        # default branch: PAREN_OPEN PAREN_CLOSE
        # branch: PAREN_OPEN expression PAREN_CLOSE
        # branch: PAREN_OPEN expression COMMA expression PAREN_CLOSE
        # ...
        return tuple(aliasArgs)


class CommandType(EnumString):
    pass # intentionally left blank


class Command(Enum):
    EMPTY = CommandType("EMPTY")
    RECORD_RELATION = CommandType("RECORD_RELATION")
    EVALUATE_EXPRESSION = CommandType("EVALUATE_EXPRESSION")
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
    def recordRelation(cls, relation: tuple[sympy.Expr, sympy.Expr]):
        return cls(cls.RECORD_RELATION, relation)
    
    @classmethod
    def evaluateExpression(cls, expression: sympy.Expr):
        return cls(cls.EVALUATE_EXPRESSION, expression)
    
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
    def __init__(self, tokens: tuple[LexerToken, ...], unexpectedTokenIdx: int):
        eolToken = tokens[-1]
        tokens = tokens[:-1] + (LexerToken(f" ...", eolToken.type, eolToken.matchIdx),)
        super().__init__(f"Unexpected [{Colors.textRed.hex}][@termtip]end of line[/@termtip][/]", tokens, [unexpectedTokenIdx], True)
