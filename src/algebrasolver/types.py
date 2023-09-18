from abc import ABC, abstractmethod
from typing import Generic, Collection, TypeVar

import sympy

from src.common.functions import first, surroundJoin
from src.common.sympyLinterFixes import subsExpr, createSymbol
from src.common.types import FormattedStr
from src.common.exceptions import MultilineException
from src.app.widgets.colors import Colors


SolutionSet = set[sympy.Expr]


_ValueType = TypeVar("_ValueType")
class ConditionalValue(Generic[_ValueType]):
    """
    This class ultimately just represents a single value of any type, but also
    attaches some data representing "conditions" on that value. Each "condition"
    is just a mapping of some symbol to some expression it should be equal to.

    This is mainly useful when doing substitution, but it is also used in some
    other places. See the `CombinationsSubstituter` for details on this.
    Basically, each condition is treated as a mini-relation that must be true in
    order for the substitution algorithm to proceed. The truth-ness of these
    mini-relations ends up keeping track of which symbol-value combinations
    depend on whatever other symbols, and ultimately filters out invalid
    symbol-value combinations when substituting.
    """
    
    def __init__(self, value: _ValueType, conditions: dict[sympy.Symbol, sympy.Expr]):
        self.value = value
        self.conditions = conditions

    def __repr__(self):
        return f"ConditionalValue({self.value}, {self.conditions})"
    
    def __hash__(self):
        conditionsHash = 1
        for (symbol, value) in self.conditions.items():
            conditionsHash *= symbol - value # type: ignore
        return hash((self.value, conditionsHash))

    def __eq__(self, other):
        if type(other) is not ConditionalValue:
            return False
        
        return self.value == other.value and self.conditions == other.conditions
    

class Relation:
    """
    Represents an equality between two expressions.

    (Could I use `sympy.Eq`? Probably. But I made this first, so whatever.)
    """
    
    def __init__(self, leftExpr: sympy.Expr, rightExpr: sympy.Expr):
        if not isinstance(leftExpr, sympy.Expr) and type(leftExpr) in (int, float):
            leftExpr = sympy.parse_expr(str(leftExpr))
        if not isinstance(rightExpr, sympy.Expr) and type(rightExpr) in (int, float):
            rightExpr = sympy.parse_expr(str(rightExpr))
        
        self.leftExpr = leftExpr
        self.rightExpr = rightExpr
        # (leftExpr             = rightExpr)
        # (leftExpr - rightExpr = 0)
        self.asExprEqToZero: sympy.Expr = leftExpr - rightExpr # = 0    # type: ignore
        assert isinstance(self.asExprEqToZero, sympy.Expr)

    def __repr__(self):
        return f"Relation({self.leftExpr}, {self.rightExpr})"
    
    def __hash__(self):
        return hash((self.leftExpr, self.rightExpr))

    def __eq__(self, other):
        if type(other) is not Relation:
            return False
        
        return self.leftExpr == other.leftExpr and self.rightExpr == other.rightExpr


class BadRelationException(MultilineException, ABC):
    """An extension of MultilineException that handles "bad" relations of some kind"""
    
    @abstractmethod
    def __init__(self, message: FormattedStr, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None], contradictingRelation: Relation):
        self.poorSymbolValues = poorSymbolValues
        self.contradictingRelation = contradictingRelation
        
        super().__init__((
            message,
            f"[{Colors.textRed.hex}]{self.renderer.formatRelation(contradictingRelation)}[/]",
            *[
                f"[{Colors.textYellow.hex}]({poorSymbol} = {first(valueSet)})[/]" if valueSet is not None and len(valueSet) == 1
                    else f"[{Colors.textYellow.hex}]({poorSymbol} = {valueSet})[/]" if valueSet is not None
                    else f"[{Colors.textYellow.hex}]({poorSymbol}: unsolved)[/]"
                for (poorSymbol, valueSet) in poorSymbolValues.items()
            ]
        ))

    def formatPoorSymbols(self, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]):
        return surroundJoin(
            (str(symbol) for symbol in poorSymbolValues.keys()),
            f"[{Colors.textYellow.hex}]",
            f"[/{Colors.textYellow.hex}]",
            ", "
        )
    
    def substitutePoorSymbols(self, expr: sympy.Expr, poorSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None]) -> sympy.Expr:
        return subsExpr(expr, {
            poorSymbol: createSymbol(f"[{Colors.textYellow.hex}]{poorSymbol}[/]")
            for poorSymbol in poorSymbolValues.keys()
        })

class ContradictionException(BadRelationException):
    """Represents a relation that implies contradictory values to one or more already known symbols"""

    def __init__(self, contradictedSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None], badRelation: Relation):
        symbolsStr = f" for {self.formatPoorSymbols(contradictedSymbolValues)}" \
            if len(contradictedSymbolValues) > 0 else ""
        super().__init__(
            f"Relation contradicts known/inferred values{symbolsStr}",
            contradictedSymbolValues,
            badRelation
        )

class NoSolutionException(BadRelationException):
    """Represents a relation that makes it impossible to extract values for some symbol"""

    def __init__(self, symbolsMissingSolutions: Collection[sympy.Symbol], badSymbolValues: dict[sympy.Symbol, set[sympy.Expr] | None], badRelation: Relation):
        symbolsStr = f" for {self.formatPoorSymbols({symbol: None for symbol in symbolsMissingSolutions})}" \
            if len(symbolsMissingSolutions) > 0 else ""
        for unsolvedSymbol in symbolsMissingSolutions:
            if unsolvedSymbol not in badSymbolValues:
                badSymbolValues[unsolvedSymbol] = None
        super().__init__(
            f"Relation leads to unsolvable state{symbolsStr}",
            badSymbolValues,
            badRelation
        )

