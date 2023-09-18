from src.parsing.lexerHelpers import *
from src.parsing.lexerTypes import *


class CommandLexer:
    types = LexerTokenTypes()
    
    _recognizers = (
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
            LexerTokenTypes.CARET
        ),
        LexerRecognizer(
            r":",
            LexerTokenTypes.COLON
        ),

        # lower priority recognizers
        LexerRecognizer(
            r"([0-9][0-9_]*(?<!_)[.]?(?!_)[0-9_]*|[0-9_]*(?<!_)[.]?(?!_)[0-9][0-9_]*)(?<!_)([eE][+-]?(?!_)[0-9_]+(?<!_))?",
            LexerTokenTypes.FLOAT
        ), # yields to INTEGER or PERIOD
        LexerRecognizer(
            r"[_a-zA-Z0-9]+|√|∛",
            LexerTokenTypes.IDENTIFIER
        ), # yields to other keywords and INTEGER/FLOAT
    )

    @classmethod
    def findTokens(cls, data: str, withEol = True):
        dataCharsProcessed = 0
        for lineData in data.split("\n"):
            while len(lineData) > 0:
                lenBeforeStrip = len(lineData)
                lineData = cls.stripWhitespace(lineData)
                lenAfterStrip = len(lineData)
                numCharsStripped = lenBeforeStrip - lenAfterStrip
                dataCharsProcessed += numCharsStripped

                if len(lineData) == 0:
                    break

                maxResult = LexerRecognizer.invalidResult
                for recognizer in cls._recognizers:
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
                yield LexerToken("", cls.types.EOL, dataCharsProcessed)
            dataCharsProcessed += len("\n")

    @classmethod
    def stripWhitespace(cls, lineData: str):
        idx = 0
        # newline left out to preserve individual lines
        whitespaces = "\t "
        while idx < len(lineData) and lineData[idx] in whitespaces:
            idx += 1
        return lineData[idx:]
