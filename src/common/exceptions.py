from abc import ABC, abstractmethod

from src.parser.lexer import LexerToken


class HandledException(Exception, ABC):
    pass # intentionally blank type


class TracebackException(HandledException, ABC):
    @abstractmethod
    def __init__(self, message: str, tokens: tuple[LexerToken, ...], badTokenIdxs: tuple[int, ...]):
        self.message = message
        self.tokens = tokens
        self.badTokenIdxs = badTokenIdxs
        
        super().__init__(message)
