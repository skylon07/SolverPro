import re

from src.common.types import Enum, EnumString


class LexerTokenType(EnumString):
    pass # intentionally left blank


class LexerTokenTypes(Enum):
    IDENTIFIER      = LexerTokenType("IDENTIFIER")
    INTEGER         = LexerTokenType("INTEGER")
    FLOAT           = LexerTokenType("FLOAT")
    PAREN_OPEN      = LexerTokenType("PAREN_OPEN")
    PAREN_CLOSE     = LexerTokenType("PAREN_CLOSE")
    BRACE_OPEN      = LexerTokenType("BRACE_OPEN")
    BRACE_CLOSE     = LexerTokenType("BRACE_CLOSE")
    BACKTICK        = LexerTokenType("BACKTICK")
    COMMA           = LexerTokenType("COMMA")
    EQUALS          = LexerTokenType("EQUALS")
    COLON_EQUALS    = LexerTokenType("COLON_EQUALS")
    PLUS            = LexerTokenType("PLUS")
    DASH            = LexerTokenType("DASH")
    STAR            = LexerTokenType("STAR")
    SLASH           = LexerTokenType("SLASH")
    CARROT          = LexerTokenType("CARROT") # TODO: ~~CARROT~~ --> CARET
    EOL             = LexerTokenType("EOL")
    INVALID         = LexerTokenType("INVALID")


class LexerToken:
    def __init__(self, matchedStr: str, tokenType: LexerTokenType, matchIdx: int):
        self.match = matchedStr
        self.type = tokenType
        self.matchIdx = matchIdx

    def __repr__(self):
        return f"LexerToken('{self.match}', {self.type}, {self.matchIdx})"
    
    def __eq__(self, other):
        if type(other) != LexerToken:
            return False
        
        return \
            self.match == other.match and \
            self.type == other.type and \
            self.matchIdx == other.matchIdx
    
    def makeWhitespaceTo(self, otherToken: "LexerToken | None"):
        if otherToken is not None:
            firstToken = self if self.matchIdx < otherToken.matchIdx else otherToken
            secondToken = otherToken if firstToken is self else self
            positionDiff = secondToken.matchIdx - firstToken.matchIdx
            numSpaces = positionDiff - len(firstToken.match)
        else:
            numSpaces = self.matchIdx
        return " " * numSpaces
    

# really this is just here to avoid circular imports, and it sort-of fits here
class AliasTemplate:
    def __init__(self, name: str, argNames: tuple[str, ...], templateTokens: tuple[LexerToken, ...]):
        self.name = name
        self.argNames = argNames
        self.numArgs = len(argNames)
        self.templateTokens = templateTokens

    def __repr__(self):
        return f"AliasTemplate({self.name}, {self.argNames})"
    
    def __call__(self, *argVals):
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


class CommandLexer:
    types = LexerTokenTypes()
    
    def __init__(self):
        self._recognizers = (
            LexerRecognizer(
                r"(?!_)[0-9_]+(?<!_)",
                LexerTokenTypes.INTEGER
            ),
            LexerRecognizer(
                r"\(",
                LexerTokenTypes.PAREN_OPEN
            ),
            LexerRecognizer(
                r"\)",
                LexerTokenTypes.PAREN_CLOSE
            ),
            LexerRecognizer(
                r"\{",
                LexerTokenTypes.BRACE_OPEN
            ),
            LexerRecognizer(
                r"\}",
                LexerTokenTypes.BRACE_CLOSE
            ),
            LexerRecognizer(
                r"`",
                LexerTokenTypes.BACKTICK
            ),
            LexerRecognizer(
                r",",
                LexerTokenTypes.COMMA
            ),
            LexerRecognizer(
                r"=",
                LexerTokenTypes.EQUALS
            ),
            LexerRecognizer(
                r":=",
                LexerTokenTypes.COLON_EQUALS
            ),
            LexerRecognizer(
                r"\+",
                LexerTokenTypes.PLUS
            ),
            LexerRecognizer(
                r"-",
                LexerTokenTypes.DASH
            ),
            LexerRecognizer(
                r"\*",
                LexerTokenTypes.STAR
            ),
            LexerRecognizer(
                r"/",
                LexerTokenTypes.SLASH
            ),
            LexerRecognizer(
                r"\^",
                LexerTokenTypes.CARROT
            ),

            # lower priority recognizers
            LexerRecognizer(
                r"([0-9][0-9_]*(?<!_)[.]?(?!_)[0-9_]*|[0-9_]*(?<!_)[.]?(?!_)[0-9][0-9_]*)(?<!_)([eE][+-]?(?!_)[0-9_]+(?<!_))?",
                LexerTokenTypes.FLOAT
            ), # yields to INTEGER or PERIOD
            LexerRecognizer(
                r"[_a-zA-Z0-9]+",
                LexerTokenTypes.IDENTIFIER
            ), # yields to other keywords and INTEGER/FLOAT
        )

    def findTokens(self, data: str, withEol = True):
        dataCharsProcessed = 0
        for lineData in data.split("\n"):
            while len(lineData) > 0:
                lenBeforeStrip = len(lineData)
                lineData = self.stripWhitespace(lineData)
                lenAfterStrip = len(lineData)
                numCharsStripped = lenBeforeStrip - lenAfterStrip
                dataCharsProcessed += numCharsStripped

                if len(lineData) == 0:
                    break

                maxResult = LexerRecognizerResult(0, LexerTokenTypes.INVALID)
                for recognizer in self._recognizers:
                    result = recognizer.match(lineData)
                    if result.numMatched > maxResult.numMatched:
                        maxResult = result

                tokenType = maxResult.matchType
                if maxResult.numMatched == 0:
                    matchedStr = lineData[:1]
                else:
                    matchedStr = lineData[:maxResult.numMatched]
                
                yield LexerToken(matchedStr, tokenType, dataCharsProcessed)
                lineData = lineData[len(matchedStr):]
                dataCharsProcessed += len(matchedStr)
            if withEol:
                yield LexerToken("", self.types.EOL, dataCharsProcessed)
            dataCharsProcessed += len("\n")

    def stripWhitespace(self, lineData: str):
        idx = 0
        # newline left out to preserve individual lines
        whitespaces = "\t "
        while idx < len(lineData) and lineData[idx] in whitespaces:
            idx += 1
        return lineData[idx:]


class LexerRecognizer:
    def __init__(self, regex: str, matchType: LexerTokenType):
        self.regex = re.compile(regex)
        self.matchType = matchType

    def __repr__(self):
        return f"LexerRecognizer({self.regex}, {self.matchType})"

    def match(self, data: str):
        result = self.regex.match(data)
        numMatched = (result.end() - result.start()) if result is not None else 0
        return LexerRecognizerResult(numMatched, self.matchType)


class LexerRecognizerResult:
    def __init__(self, numMatched: int, matchType: LexerTokenType):
        self.numMatched = numMatched
        self.matchType = matchType
