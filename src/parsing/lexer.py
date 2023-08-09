import re

from src.common.types import Enum, EnumString


class LexerTokenType(EnumString):
    pass


class LexerTokenTypes(Enum):
    IDENTIFIER  = LexerTokenType("IDENTIFIER")
    INT         = LexerTokenType("INT")
    FLOAT       = LexerTokenType("FLOAT")
    PAREN_OPEN  = LexerTokenType("PAREN_OPEN")
    PAREN_CLOSE = LexerTokenType("PAREN_CLOSE")
    EQUALS      = LexerTokenType("EQUALS")
    PLUS        = LexerTokenType("PLUS")
    DASH        = LexerTokenType("DASH")
    STAR        = LexerTokenType("STAR")
    SLASH       = LexerTokenType("SLASH")
    CARROT      = LexerTokenType("CARROT")
    EOL         = LexerTokenType("EOL")
    INVALID     = LexerTokenType("INVALID")


class LexerToken:
    def __init__(self, matchedStr: str, tokenType: LexerTokenType, matchIdx: int):
        self.match = matchedStr
        self.type = tokenType
        self.matchIdx = matchIdx

    def __repr__(self):
        return f"LexerToken<{self.type}>('{self.match}', {self.matchIdx})"
    
    def __eq__(self, other):
        if type(other) != LexerToken:
            return False
        
        return \
            self.match == other.match and \
            self.type == other.type and \
            self.matchIdx == other.matchIdx


class CommandLexer:
    types = LexerTokenTypes()
    
    def __init__(self):
        self._recognizers = (
            LexerRecognizer(
                r"(?!_)[0-9_]+(?<!_)",
                LexerTokenTypes.INT
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
                r"=",
                LexerTokenTypes.EQUALS
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
                r"[_a-zA-Z][_a-zA-Z0-9]*",
                LexerTokenTypes.IDENTIFIER
            ), # yields to other keywords
            LexerRecognizer(
                r"(?!_)[0-9_]*(?<!_)[.]?(?!_)[0-9_]*(?<!_)([eE][+-]?(?!_)[0-9_]*(?<!_))?",
                LexerTokenTypes.FLOAT
            ), # yields to INT or PERIOD
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
        # newline intentionally left out
        whitespaces = "\t "
        while idx < len(lineData) and lineData[idx] in whitespaces:
            idx += 1
        return lineData[idx:]


class LexerRecognizer:
    def __init__(self, regex: str, matchType: LexerTokenType):
        self.regex = re.compile(regex)
        self.matchType = matchType

    def __repr__(self):
        regexStartIdx = len("re.compile('")
        regexEndIdx = -len("')")
        regexStr = repr(self.regex)[regexStartIdx : regexEndIdx]
        return f"LexerRecognizer:{self.matchType}<{regexStr}>"

    def match(self, data: str):
        result = self.regex.match(data)
        numMatched = (result.end() - result.start()) if result is not None else 0
        return LexerRecognizerResult(numMatched, self.matchType)


class LexerRecognizerResult:
    def __init__(self, numMatched: int, matchType: LexerTokenType):
        self.numMatched = numMatched
        self.matchType = matchType
