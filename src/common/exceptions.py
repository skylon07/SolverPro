from abc import ABC, abstractmethod
from typing import Iterable, Collection

from src.common.types import FormattedStr
from src.parsing.lexer import LexerToken


class HandledException(Exception, ABC):
    pass # intentionally blank type


class TracebackException(HandledException, ABC):
    @abstractmethod
    def __init__(self, message: FormattedStr, tokens: Collection[LexerToken], badTokenIdxs: Iterable[int], grayOutAfterBadTokens: bool = False):
        self.message = message
        self.tokens = tokens
        self.badTokenIdxs = badTokenIdxs
        self.grayOutAfterBadTokens = grayOutAfterBadTokens
        
        super().__init__(message, tokens, badTokenIdxs)

class MultilineException(HandledException, ABC):
    @abstractmethod
    def __init__(self, messageLines: Iterable[FormattedStr]):
        self.messageLines = messageLines
        super().__init__(messageLines)
