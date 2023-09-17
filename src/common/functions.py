from typing import Callable, Iterable, TypeVar, Any, overload

import sympy


def getVersion():
    return "0.4.0"

def iterDifference(iter1, iter2):
    for item in iter1:
        if item not in iter2:
            yield item

_firstNoDefault = object()
_IterableType = TypeVar("_IterableType")
_DefaultType = TypeVar("_DefaultType")
@overload
def first(iterable: Iterable[_IterableType]) -> _IterableType: ...
@overload
def first(iterable: Iterable[_IterableType], default: _DefaultType) -> _IterableType | _DefaultType: ...
def first(iterable: Iterable[_IterableType], default: _DefaultType = _firstNoDefault) -> _IterableType | _DefaultType:
    try:
        for item in iterable:
            firstItem = item
            # because we...
            return firstItem
    except StopIteration:
        pass
    if default is _firstNoDefault:
        raise ValueError("Iterable contained no elements (and no default value was given)")
    else:
        return default
    
def surroundJoin(items: Iterable, prefix: str, suffix: str, separator: str):
    fullSeparator = suffix + separator + prefix
    return prefix + fullSeparator.join(items) + suffix

def lazyImportSolverProApp():
    # prevents the "circular import" exception stuff;
    # this function is really only ever needed to assert types,
    # so when building the program in optimized mode,
    # these should be cut out from assert statements anyway
    from src.app.widgets.solverProApp import SolverProApp
    return SolverProApp

def toExprStr(expr: sympy.Expr):
    return SolverProExprPrinter().doprint(expr)

# mostly for testing
def runForError(fn: Callable[[], Any]):
    try:
        fn()
        return None
    except Exception as exception:
        return exception
    

# TODO: implement pretty printing
#       https://docs.sympy.org/latest/modules/printing.html#prettyprinter-class
#       looks like https://docs.sympy.org/latest/_images/consoleunicode.png
# from sympy.printing.pretty.pretty import PrettyPrinter
from sympy.printing.str import StrPrinter
sympy.init_printing(use_unicode = True)

from sympy.printing.precedence import precedence as _precedence

class SolverProExprPrinter(StrPrinter):
    def _print_Exp1(self, expr: sympy.E):
        return "e"
    
    def _print_ImaginaryUnit(self, expr: sympy.I):
        return "i"

    def _print_Pow(self, expr: sympy.Pow, rational: bool = False):
        # code below is a modified form of super()._print_Pow()
        prec = _precedence(expr)

        if expr.exp is sympy.S.Half and not rational:
            return "√(%s)" % self._print(expr.base)
        if isinstance(expr.exp, sympy.Rational) and expr.exp == sympy.Rational(1, 3):
            return "∛(%s)" % self._print(expr.base)

        if expr.is_commutative:
            if -expr.exp is sympy.S.Half and not rational:
                # Note: Don't test "expr.exp == -S.Half" here, because that will
                # match -0.5, which we don't want.
                return "%s/√(%s)" % tuple((self._print(arg) for arg in (sympy.S.One, expr.base)))
            if isinstance(expr.exp, sympy.Rational) and expr.exp == sympy.Rational(-1, 3):
                return "∛(%s)" % self._print(expr.base)
            if expr.exp is -sympy.S.One:
                # Similarly to the S.Half case, don't test with "==" here.
                return "%s/%s" % (
                    self._print(sympy.S.One),
                    self.parenthesize(expr.base, prec, strict=False)
                )

        e = self.parenthesize(expr.exp, prec, strict=False)
        if self.printmethod == '_sympyrepr' and expr.exp.is_Rational and expr.exp.q != 1: # type: ignore
            # the parenthesized exp should be '(Rational(a, b))' so strip parens,
            # but just check to be sure.
            if e.startswith('(Rational'):
                return '%s^%s' % (self.parenthesize(expr.base, prec, strict=False), e[1:-1])
        return '%s^%s' % (self.parenthesize(expr.base, prec, strict=False), e)
    
    def _print_exp(self, expr: sympy.exp, rational: bool = False):
        assert len(expr.args) == 1, "exp() didn't take only one argument"
        return self._print_Pow(sympy.E ** expr.args[0], rational)
    
    def _print_log(self, expr: sympy.log):
        return "ln(%s)" % self._print(expr.args[0])
