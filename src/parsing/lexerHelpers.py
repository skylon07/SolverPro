import re

from src.parsing.lexerTypes import *


class LexerRecognizerResult:
    def __init__(self, numMatched: int, matchType: LexerTokenType):
        self.numMatched = numMatched
        self.matchType = matchType


class LexerRecognizer:
    invalidResult = LexerRecognizerResult(0, LexerTokenTypes.INVALID)

    def __init__(self, regex: str, matchType: LexerTokenType):
        self.regex = re.compile(regex)
        self.matchType = matchType

    def __repr__(self):
        return f"LexerRecognizer({self.regex}, {self.matchType})"

    def match(self, data: str):
        result = self.regex.match(data)
        numMatched = (result.end() - result.start()) if result is not None else 0
        return LexerRecognizerResult(numMatched, self.matchType)
