import sympy

from src.common.types import Enum, EnumString
from src.common.exceptions import TracebackException
from src.parsing.lexer import LexerTokenType, LexerTokenTypes, LexerToken


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


class _CommandParserSequencer:
    _lowPrecOpers = (
        LexerTokenTypes.PLUS,
        LexerTokenTypes.DASH,
    )
    _midPrecOpers = (
        LexerTokenTypes.STAR,
        LexerTokenTypes.SLASH,
    )
    _highPrecOpers = (
        LexerTokenTypes.PLUS,
        LexerTokenTypes.DASH,
    )
    _maxPrecOpers = (
        LexerTokenTypes.CARROT,
    )
    _valueTypes = (
        LexerTokenTypes.INTEGER,
        LexerTokenTypes.FLOAT,
        LexerTokenTypes.IDENTIFIER,
    )

    def __init__(self, commandTokens: tuple[LexerToken, ...]):
        self._tokens = commandTokens
        self._setNumTokensParsed(0)
        self._allowExpressionList = True

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
        for (idx, item) in enumerate(highPrecExprList):
            if type(item) is list:
                maxPrecExprList = item
                highPrecExprList[idx] = self._convertMaxPrecExprList(maxPrecExprList)
        
        # reversed since we want to parse right-to-left
        finalExpr: sympy.Expr = highPrecExprList[-1]
        for (revIdx, operToken) in enumerate(reversed(highPrecExprList)):
            if type(operToken) is LexerToken:
                idx = -(revIdx + 1)
                if operToken.type is LexerTokenTypes.PLUS:
                    finalExpr = +finalExpr
                elif operToken.type is LexerTokenTypes.DASH:
                    finalExpr = -finalExpr
                else:
                    raise NotImplementedError(f"Unconsidered token type {operToken.type}(high prec)")
        return finalExpr

    def _convertMaxPrecExprList(self, maxPrecExprList: list) -> sympy.Expr:
        for (idx, valuePair) in enumerate(maxPrecExprList):
            if type(valuePair) is tuple:
                (valueType, valueStr) = valuePair
                if valueType is LexerTokenTypes.IDENTIFIER:
                    value = sympy.Symbol(valueStr)
                else:
                    value = sympy.parse_expr(valueStr)
                maxPrecExprList[idx] = value
        
        # reversed since we want to parse right-to-left
        finalExpr: sympy.Expr = maxPrecExprList[-1]
        for (revIdx, operToken) in enumerate(reversed(maxPrecExprList)):
            if type(operToken) is LexerToken:
                idx = -(revIdx + 1)
                if operToken.type is LexerTokenTypes.CARROT:
                    operand = maxPrecExprList[idx - 1]
                    finalExpr = operand ** finalExpr
                else:
                    raise NotImplementedError(f"Unconsidered token type {operToken.type}(max prec)")
        return finalExpr
    
    def _throwUnexpectedToken(self, expectedTypes: tuple[LexerTokenType, ...]):
        if self._currToken.type is LexerTokenTypes.EOL:
            return self._throwEolException()
        else:
            raise ParseException(expectedTypes, self._tokens, self.numTokensParsed)
    
    def _throwEolException(self):
        raise EolException(self._tokens, self.numTokensParsed)

    def sequenceCommand(self):
        # branch: EOL
        if self._currToken.type is LexerTokenTypes.EOL:
            self._consumeCurrToken(self._currToken.type)
            return Command.empty()
        
        # distinguish branches: relation, expression
        idx = self.numTokensParsed
        isRelation = False
        while idx < len(self._tokens):
            token = self._tokens[idx]
            if token.type is LexerTokenTypes.EQUALS:
                isRelation = True
                break
            idx += 1

        # branch: relation EOL
        if isRelation:
            relation = self.sequenceRelation()
            self._consumeCurrToken(LexerTokenTypes.EOL)
            return Command.recordRelation(relation)
        
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
            self._consumeCurrToken(self._currToken.type)
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
        if self._moreTokens and self._currToken.type in self._highPrecOpers:
            highPrecOperToken = self.sequenceOperHigh()
            expandedExprList = self.sequenceHighPrecExpr()
            expandedExprList.insert(0, highPrecOperToken)
            return expandedExprList
        
        # default branch: maxPrecExpr
        maxPrecExprList = self.sequenceMaxPrecExpr()
        return [maxPrecExprList]
    
    def sequenceMaxPrecExpr(self):
        # (all branches)
        evaluation = self.sequenceEvaluation()

        # branch: evaluation operMax maxPrecExpr
        if self._moreTokens and self._currToken.type in self._maxPrecOpers:
            maxPrecOperToken = self.sequenceOperMax()
            expandedExprList = self.sequenceMaxPrecExpr()
            expandedExprList.insert(0, maxPrecOperToken)
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
    
    def sequenceOperHigh(self):
        # branch: PLUS/DASH
        validHighOpers = (
            LexerTokenTypes.PLUS,
            LexerTokenTypes.DASH,
        )
        if self._currToken.type in validHighOpers:
            highPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return highPrecOperToken
        
        return self._throwUnexpectedToken(validHighOpers)
    
    def sequenceOperMax(self):
        # branch: CARROT
        validMaxOpers = (
            LexerTokenTypes.CARROT,
        )
        if self._currToken.type in validMaxOpers:
            maxPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return maxPrecOperToken
        
        return self._throwUnexpectedToken(validMaxOpers)

    def sequenceEvaluation(self):
        # branch: PAREN_OPEN expression PAREN_CLOSE
        if self._currToken.type is LexerTokenTypes.PAREN_OPEN:
            self._consumeCurrToken(self._currToken.type)
            expression = self.sequenceExpression()
            self._consumeCurrToken(LexerTokenTypes.PAREN_CLOSE)
            return expression
        
        # branch: BRACE_OPEN expressionList BRACE_CLOSE
        elif self._currToken.type is LexerTokenTypes.BRACE_OPEN and self._allowExpressionList:
            self._consumeCurrToken(self._currToken.type)
            self._allowExpressionList = False
            expressions = self.sequenceExpressionList()
            self._allowExpressionList = True
            self._consumeCurrToken(LexerTokenTypes.BRACE_CLOSE)
            expressionsStr = ", ".join(str(expr) for expr in expressions)
            return sympy.Symbol(f"{{{expressionsStr}}}")

        # # default branch: value
        (tokenType, valueStr) = self.sequenceValue()
        return (tokenType, valueStr)

    def sequenceValue(self):
        tokenType = self._currToken.type

        # (all valid branches)
        if self._currToken.type in self._valueTypes:
            valueStr = self._currToken.match
            self._consumeCurrToken(self._currToken.type)
            return (tokenType, valueStr)
        
        return self._throwUnexpectedToken(self._valueTypes) # `return` fixes type inference...?
    

class CommandType(EnumString):
    pass


class Command(Enum):
    EMPTY = CommandType("EMPTY")
    RECORD_RELATION = CommandType("RECORD_RELATION")
    EVALUATE_EXPRESSION = CommandType("EVALUATE_EXPRESSION")

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


class ParseException(TracebackException):
    def __init__(self, expectedTypes: tuple[LexerTokenType, ...], tokens: tuple[LexerToken, ...], unexpectedTokenIdx: int):
        unexpectedToken = tokens[unexpectedTokenIdx]

        expectedTypesStr = " or ".join(f"[green]__{tokenType}__[/green]".lower() for tokenType in expectedTypes)
        firstLetterIsVowel = str(expectedTypes[0])[0].lower() in "aeiou"
        gramaticalN = "n" if firstLetterIsVowel else ""
        fullMessage = f"Unexpected [red]{unexpectedToken.match}[/red]; expected a{gramaticalN} {expectedTypesStr}"
        super().__init__(fullMessage, tokens, [unexpectedTokenIdx], True)


class EolException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...], unexpectedTokenIdx: int):
        super().__init__("Unexpected [red]{end of line}[/red]", tokens, [unexpectedTokenIdx], True)
