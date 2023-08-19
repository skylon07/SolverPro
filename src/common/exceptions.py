from abc import ABC, abstractmethod
from typing import Iterable

from src.common.types import FormattedStr
from src.parsing.lexer import LexerToken


class HandledException(Exception, ABC):
    pass # intentionally blank type


class TracebackException(HandledException, ABC):
    @abstractmethod
    def __init__(self, message: FormattedStr, tokens: Iterable[LexerToken], badTokenIdxs: Iterable[int]):
        self.message = message
        self.tokens = tokens
        self.badTokenIdxs = badTokenIdxs
        
        super().__init__(message, tokens, badTokenIdxs)

class MultilineException(HandledException, ABC):
    @abstractmethod
    def __init__(self, messageLines: Iterable[FormattedStr]):
        self.messageLines = messageLines
        super().__init__(messageLines)
