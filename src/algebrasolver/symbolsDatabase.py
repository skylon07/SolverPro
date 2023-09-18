from typing import TypeVar

import sympy

from src.parsing.lexer import CommandLexer
from src.parsing.parser import CommandParser, isExpressionListSymbol
from src.algebrasolver.types import *

class SymbolsDatabase:
    """
    A database for known symbols. Logically this is a union between two dictionaries:
    1. An initially empty dictionary of variable/value mappings, added to as values are inferred
    2. An infinite dictionary mapping "expression list symbols" to a list of actual expressions 
    """

    _DefaultType = TypeVar("_DefaultType")

    def __init__(self):
        # a mapping of a variable to its potential values and conditions
        # (like b = 4 when a = 2 and b = 5 when a = -1)
        self._symbolValues: dict[sympy.Symbol, set[ConditionalValue[sympy.Expr]]] = dict()
        # a mapping of symbols to conditional values for "expression list symbols"
        self._exprListSymbolValues: dict[sympy.Symbol, set[ConditionalValue[sympy.Expr]]] = dict()
        # the order in which symbols are iterated over (for substitution)
        self._symbolResolutionOrder: list[tuple[int, sympy.Symbol]] = list()

    def __getitem__(self, key: sympy.Symbol):
        if isExpressionListSymbol(key):
            if key not in self._exprListSymbolValues:
                self._exprListSymbolValues[key] = self._parseExprListSymbol(key)
                # resolution order doesn't include expression list symbols;
                # the generator knows how to handle this
                # self._insertSymbolToResolutionOrder(key)
            return self._exprListSymbolValues[key]
        else:
            return self._symbolValues[key]
    
    def __setitem__(self, key: sympy.Symbol, value: set[ConditionalValue[sympy.Expr]]):
        if isExpressionListSymbol(key):
            raise ValueError("Cannot set values for expression list symbols")
        if key in self._symbolValues:
            self._popSymbolFromResolutionOrder(key)
        self._symbolValues[key] = value
        self._insertSymbolToResolutionOrder(key)

    def __iter__(self):
        for (rank, symbol) in self._symbolResolutionOrder:
            yield symbol

    def __contains__(self, key: sympy.Symbol):
        return key in self._symbolValues or isExpressionListSymbol(key)

    def copy(self):
        newDatabase = SymbolsDatabase()
        newDatabase._symbolValues = dict(self._symbolValues)
        newDatabase._exprListSymbolValues = dict(self._exprListSymbolValues)
        newDatabase._symbolResolutionOrder = list(self._symbolResolutionOrder)
        return newDatabase
    
    def get(self, key: sympy.Symbol, default: _DefaultType = None) -> set[ConditionalValue[sympy.Expr]] | _DefaultType:
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key: sympy.Symbol):
        if isExpressionListSymbol(key):
            raise ValueError("Cannot pop values for expression list symbols")
        self._popSymbolFromResolutionOrder(key)
        return self._symbolValues.pop(key)

    def _parseExprListSymbol(self, exprListSymbol: sympy.Symbol) -> set[ConditionalValue[sympy.Expr]]:
        assert isExpressionListSymbol(exprListSymbol)
        exprListStr = str(exprListSymbol)[1:-1]
        exprTokens = tuple(CommandLexer.findTokens(exprListStr))
        expressionList = CommandParser.parseExpressionList(exprTokens)
        return {
            ConditionalValue(expression, dict())
            for expression in expressionList
        }
    
    def _insertSymbolToResolutionOrder(self, symbol: sympy.Symbol):
        assert symbol in self, "Should not insert symbol's resolution order before it has values"
        symbolSortRank = self._calculateSymbolResolutionRank(symbol)
        if symbolSortRank == 0:
            self._symbolResolutionOrder.insert(0, (symbolSortRank, symbol))
        else:
            insertIdx = len(self._symbolResolutionOrder) + 1
            rankBeforeInsert = None
            while rankBeforeInsert is None or rankBeforeInsert > symbolSortRank:
                insertIdx -= 1
                if insertIdx == 0:
                    break
                (rankBeforeInsert, symbolBeforeInsert) = self._symbolResolutionOrder[insertIdx - 1]
            self._symbolResolutionOrder.insert(insertIdx, (symbolSortRank, symbol))

    def _calculateSymbolResolutionRank(self, symbol: sympy.Symbol):
        if isExpressionListSymbol(symbol):
            return 0
        else:
            conditionSymbols = {
                symbol
                for conditionValue in self[symbol]
                for symbol in conditionValue.conditions.keys()
            }
            rank = 1 + sum(
                self._calculateSymbolResolutionRank(symbol)
                for symbol in conditionSymbols
            )
            return rank

    def _popSymbolFromResolutionOrder(self, symbol: sympy.Symbol):
        symbolIdx = [
            symbol
            for (rank, symbol) in self._symbolResolutionOrder
        ].index(symbol)
        return self._symbolResolutionOrder.pop(symbolIdx)


