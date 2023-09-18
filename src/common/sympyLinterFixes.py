import sympy

# when these methods are called directly from sympy, it causes the linter
# to hang; this module provides access to these functions/types while preserving
# the integrity of the linter (sympy just takes too much brainpower I guess lol)
createSymbol = eval("sympy.Symbol")
exp = eval("sympy.exp")
log = eval("sympy.log")
ln = eval("sympy.ln")
subsExpr = eval("sympy.Expr.subs")
solveSet = eval("sympy.solveset")
