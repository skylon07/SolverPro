import sympy

from src.common.types import Enum, EnumString
from src.common.exceptions import TracebackException
from src.parsing.lexer import LexerTokenType, LexerTokenTypes, LexerToken


class CommandParser:
    def parse(self, commandTokens: tuple[LexerToken, ...]):
        while len(commandTokens) > 0:
            sequencer = CommandParserSequencer(commandTokens)
            command = sequencer.sequenceCommand()
            yield command
            commandTokens = commandTokens[sequencer.numTokensParsed:]


class CommandParserSequencer:
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

    def __init__(self, commandTokens: tuple[LexerToken, ...]):
        self._tokens = commandTokens
        self._setNumTokensParsed(0)

    def _setNumTokensParsed(self, numParsed: int):
        self.numTokensParsed = numParsed
        self._moreTokens = self.numTokensParsed < len(self._tokens)

    @property
    def _currToken(self):
        if self._moreTokens:
            currToken = self._tokens[self.numTokensParsed]
            return currToken
        self._throwEolException()

    def _consumeCurrToken(self, expectedTokenType: LexerTokenType):
        if self._currToken.type is not expectedTokenType:
            if self._currToken.type is LexerTokenTypes.EOL:
                self._throwEolException()
            self._throwParseException((expectedTokenType,))
        
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
                    # TODO: does the token index need to be overridden?
                    self._throwParseException(self._lowPrecOpers)
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
                    # TODO: does the token index need to be overridden?
                    self._throwParseException(self._midPrecOpers)
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
                    # TODO: does the token index need to be overridden?
                    self._throwParseException(self._highPrecOpers)
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
                    # TODO: does the token index need to be overridden?
                    self._throwParseException(self._maxPrecOpers)
        return finalExpr

    def _throwParseException(self, expectedTypes: tuple[LexerTokenType, ...]):
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
            relation = self._sequenceRelation()
            self._consumeCurrToken(LexerTokenTypes.EOL)
            return Command.recordRelation(relation)
        
        # default branch: expression EOL
        expression = self._sequenceExpression()
        self._consumeCurrToken(LexerTokenTypes.EOL)
        return Command.evaluateExpression(expression)
    
    def _sequenceRelation(self):
        # default branch: expression EQUALS expression
        leftExpr = self._sequenceExpression()
        self._consumeCurrToken(LexerTokenTypes.EQUALS)
        rightExpr = self._sequenceExpression()
        return (leftExpr, rightExpr)
    
    def _sequenceExpression(self):
        # default branch: lowPrecExpr
        lowPrecExprList = self._sequenceLowPrecExpr()
        expression = self._convertLowPrecExprList(lowPrecExprList)
        return expression
    
    def _sequenceLowPrecExpr(self):
        # (all branches)
        midPrecExprList = self._sequenceMidPrecExpr()

        # branch: midPrecExpr operLow lowPrecExpr
        if self._moreTokens and self._currToken.type in self._lowPrecOpers:
            lowPrecOperToken = self._sequenceOperLow()
            expandedExprList = self._sequenceLowPrecExpr()
            expandedExprList.insert(0, lowPrecOperToken)
            expandedExprList.insert(0, midPrecExprList)
            return expandedExprList
        
        # default branch: midPrecExpr
        return [midPrecExprList]
    
    def _sequenceMidPrecExpr(self):
        # (all branches)
        highPrecExprList = self._sequenceHighPrecExpr()

        # branch: highPrecExpr operMid midPrecExpr
        if self._moreTokens and self._currToken.type in self._midPrecOpers:
            midPrecOperToken = self._sequenceOperMid()
            expandedExprList = self._sequenceMidPrecExpr()
            expandedExprList.insert(0, midPrecOperToken)
            expandedExprList.insert(0, highPrecExprList)
            return expandedExprList
        
        # default branch: highPrecExpr
        return [highPrecExprList]
    
    def _sequenceHighPrecExpr(self):
        # branch: operHigh highPrecExpr
        if self._moreTokens and self._currToken.type in self._highPrecOpers:
            highPrecOperToken = self._sequenceOperHigh()
            expandedExprList = self._sequenceHighPrecExpr()
            expandedExprList.insert(0, highPrecOperToken)
            return expandedExprList
        
        # default branch: maxPrecExpr
        maxPrecExprList = self._sequenceMaxPrecExpr()
        return [maxPrecExprList]
    
    def _sequenceMaxPrecExpr(self):
        # (all branches)
        evaluation = self._sequenceEvaluation()

        # branch: evaluation operMax maxPrecExpr
        if self._moreTokens and self._currToken.type in self._maxPrecOpers:
            maxPrecOperToken = self._sequenceOperMax()
            expandedExprList = self._sequenceMaxPrecExpr()
            expandedExprList.insert(0, maxPrecOperToken)
            expandedExprList.insert(0, evaluation)
            return expandedExprList
        
        # default branch: evaluation
        return [evaluation]

    def _sequenceOperLow(self):
        # branch: PLUS/DASH
        validLowOpers = (
            LexerTokenTypes.PLUS,
            LexerTokenTypes.DASH,
        )
        if self._currToken.type in validLowOpers:
            lowPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return lowPrecOperToken
        
        self._throwParseException(validLowOpers)

    def _sequenceOperMid(self):
        # branch: STAR/SLASH
        validMidOpers = (
            LexerTokenTypes.STAR,
            LexerTokenTypes.SLASH,
        )
        if self._currToken.type in validMidOpers:
            midPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return midPrecOperToken
        
        self._throwParseException(validMidOpers)
    
    def _sequenceOperHigh(self):
        # branch: PLUS/DASH
        validHighOpers = (
            LexerTokenTypes.PLUS,
            LexerTokenTypes.DASH,
        )
        if self._currToken.type in validHighOpers:
            highPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return highPrecOperToken
        
        self._throwParseException(validHighOpers)
    
    def _sequenceOperMax(self):
        # branch: CARROT
        validMaxOpers = (
            LexerTokenTypes.CARROT,
        )
        if self._currToken.type in validMaxOpers:
            maxPrecOperToken = self._currToken
            self._consumeCurrToken(self._currToken.type)
            return maxPrecOperToken
        
        self._throwParseException(validMaxOpers)

    def _sequenceEvaluation(self):
        # branch: PAREN_OPEN expression PAREN_CLOSE
        if self._currToken.type is LexerTokenTypes.PAREN_OPEN:
            self._consumeCurrToken(self._currToken.type)
            expression = self._sequenceExpression()
            self._consumeCurrToken(LexerTokenTypes.PAREN_CLOSE)
            return expression

        # default branch: value
        (tokenType, valueStr) = self._sequenceValue()
        return (tokenType, valueStr)

    def _sequenceValue(self):
        tokenType = self._currToken.type

        # branch: number
        numberFirsts = (
            LexerTokenTypes.INT,
            LexerTokenTypes.FLOAT,
        )
        if self._currToken.type in numberFirsts:
            # both branches
            number = self._sequenceNumber()
            return (tokenType, number)
        
        # default branch: IDENTIFIER
        identifierStr = self._currToken.match
        self._consumeCurrToken(LexerTokenTypes.IDENTIFIER)
        return (tokenType, identifierStr)
    
    def _sequenceNumber(self):
        # branch: INT/FLOAT
        validNumbers = (
            LexerTokenTypes.INT,
            LexerTokenTypes.FLOAT,
        )
        if self._currToken.type in validNumbers:
            numberStr = self._currToken.match
            self._consumeCurrToken(self._currToken.type)
            return numberStr

        return self._throwParseException(validNumbers) # `return` fixes type inference...?
    

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

        expectedTypesStr = " or ".join(f"[green]{{{tokenType}}}[/green]".lower() for tokenType in expectedTypes)
        firstLetterIsVowel = str(expectedTypes[0])[0].lower() in "aeiou"
        gramaticalN = "n" if firstLetterIsVowel else ""
        fullMessage = f"Unexpected [red]{unexpectedToken.match}[/red]; expected a{gramaticalN} {expectedTypesStr}"
        super().__init__(fullMessage, tokens, [unexpectedTokenIdx])


class EolException(TracebackException):
    def __init__(self, tokens: tuple[LexerToken, ...], unexpectedTokenIdx: int):
        super().__init__("Unexpected end of line", tokens, [unexpectedTokenIdx])
