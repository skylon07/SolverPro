import sympy
# from sympy.printing.pretty.pretty import PrettyPrinter
from sympy.printing.str import StrPrinter
from sympy.printing.precedence import precedence

sympy.init_printing(use_unicode = True)


class SolverProExprPrinter(StrPrinter):
    def _print_Exp1(self, expr: sympy.E):
        return "e"
    
    def _print_ImaginaryUnit(self, expr: sympy.I):
        return "i"

    def _print_Pow(self, expr: sympy.Pow, rational: bool = False):
        # code below is a modified form of super()._print_Pow()
        prec = precedence(expr)

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
                return "%s/∛(%s)" % tuple((self._print(arg) for arg in (sympy.S.One, expr.base)))
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
