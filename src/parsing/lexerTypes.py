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
    COLON           = LexerTokenType("COLON")
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

    @property
    def matchIdxEnd(self):
        return self.matchIdx + len(self.match)

    def __repr__(self):
        return f"LexerToken('{self.match}', {self.type}, {self.matchIdx})"
    
    def __eq__(self, other):
        if type(other) != LexerToken:
            return False
        
        return \
            self.match == other.match and \
            self.type == other.type and \
            self.matchIdx == other.matchIdx
    
    def spacesBetween(self, otherToken: "LexerToken | None"):
        if otherToken is not None:
            firstToken = self if self.matchIdx < otherToken.matchIdx else otherToken
            secondToken = otherToken if firstToken is self else self
            firstTokenMatchIdxEnd = firstToken.matchIdx + len(firstToken.match)
            numSpaces = secondToken.matchIdx - firstTokenMatchIdxEnd
        else:
            numSpaces = self.matchIdx
        return numSpaces
    
    def makeWhitespaceTo(self, otherToken: "LexerToken | None"):
        return " " * self.spacesBetween(otherToken)