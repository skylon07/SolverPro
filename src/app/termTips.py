from typing import Iterable

from src.common.types import FormattedStr
from src.app.textRenderer import TextRenderer
from src.app.widgets.colors import Colors


class TermTip:
    def __init__(self, term: FormattedStr, definitionLines: Iterable[FormattedStr]):
        self.term = term
        self.definitionLines = tuple(
            f"[{Colors.textMuted.hex}]{line}[/]" if type(line) is str
                else line
            for line in definitionLines
        )


class TermTips:
    def __init__(self):
        self._renderer = TextRenderer.instance
        self._terms: dict[str, TermTip | str] = {
            'alias': TermTip(
                "Abstract: Alias Template",
                (
                    "A special expression that allows the substitution of arbitrary " \
                    "expressions or partial expressions in a repeatable way.",

                    "Alias templates are fundamentally different than evaluating expressions. " \
                    "While they both substitute their variables with values, alias templates " \
                    "logically perform their substitutions directly into the input string, as " \
                    "if you wrote their evaluated template out by hand. Consider this example:",

                    self._renderer.formatLexerSyntax("plus(a, b) := a + (b)"),

                    self._renderer.formatLexerSyntax("1 + plus(2, 3) + 4"),

                    "The second expression would resolve to:",

                    self._renderer.formatLexerSyntax("1 + 2 + (3) + 4"),

                    "Which would then evaluate to:",

                    self._renderer.formatLexerSyntax("10"),

                    "It is important to note that the template (the expression after `:=`) " \
                    "is not parsed before it is resolved. This is evident by the " + \
                    self._renderer.formatLexerSyntax("(3)") + " " + \
                    "still being surrounded by parentheses, indicating the " + \
                    self._renderer.formatLexerSyntax("(b)") + " " + \
                    "was stored with parentheses around it as well. This allows for " \
                    "some creativity, since the templates don't need to resolve " \
                    "to \"valid\" expressions. Consider this completely valid example:",

                    self._renderer.formatLexerSyntax("squared := ^2"),

                    self._renderer.formatLexerSyntax("5 squared() + 5"),

                    "(Parentheses are optional when the alias takes no arguments)",
                )
            ),
            'built-in alias': TermTip(
                "Abstract: Built-in Alias",
                (
                    "A predefined alias that provides special kinds of expressions.",

                    "Built-in aliases are similar in concept to user-defined alias " \
                    "templates, however there are two important distinctions.",
                    
                    "First, these pre-defined aliases work directly with expressions, " \
                    "which means they take entire expressions as parameters and can " \
                    "only be written in places where expressions (or variables) are " \
                    "permitted. This means you can't pass partial expressions or " \
                    "backticks as arguments to them, unlike user-defined alias templates.",

                    "Second, because of the above, built-in aliases will appear to be " \
                    "processed after user-defined alias templates, or in the case of " \
                    "an error, not at all. This behavior is expected from Solver Pro." 
                )
            ),
            'command': TermTip(
                "Abstract: Command",
                (
                    "A special syntax that allows Solver Pro to perform extended " \
                    "functionality.",

                    "Commands are generally run to perform uncommon actions " \
                    "(that is, an action that isn't \"solve this\" or \"tell me what " \
                    "this variable is\"). A command is run by typing its name, " \
                    "followed by a colon, at the beginning of a line.",

                    "Currently available commands:",

                    self._renderer.formatLexerSyntax("simplify: expr") + "\n" + \
                    "Processes an expression without substituting known/inferred values.",
                )
            ),
            'identifiers': 'identifier',
            'identifier': TermTip(
                "Abstract: Identifier",
                (
                    "A word or other group of letters/numbers acting as a label to some value.",
                    
                    "Identifiers can be variables contained in expressions and relations, " \
                    "or they can be the names of alias templates. Identifiers consist of " \
                    "letters and numbers (but no spaces -- use underscores instead), " \
                    "with at least one letter present. Unlike most other programs, " \
                    "Solver Pro permits a number to start an identifier name, as long " \
                    "as at least one letter appears in the name later.",

                    "Identifier:     " + self._renderer.formatLexerSyntax("a  my_var  train2Car3  3rdBox"),

                    "Non-identifier: " + self._renderer.formatLexerSyntax("345  1.5  +  ()"),
                )
            ),
            'end of line': 'eol',
            'eol': TermTip(
                "Abstract: End of Line",
                (
                    "An invisible delimiter that indicates the end of a line of input.",

                    "If an end of line is \"unexpected\", that indicates an incomplete command " \
                    "was entered."
                )
            ),
            'integer': TermTip(
                "Number: Integer",
                (
                    "A whole number without a decimal or exponent part.",

                    "Of all the kinds of numbers Solver Pro supports, integers are the " \
                    "most precise. Use them over other kinds of numbers if possible.",

                    "Integer:     " + self._renderer.formatLexerSyntax("4  15  500_000_000"),

                    "Non-integer: " + self._renderer.formatLexerSyntax("4.5  2/5  6.21e-5"),
                )
            ),
            'float': TermTip(
                "Number: Floating Point",
                (
                    "A number representing a decimal or a scientific number.",

                    "Floats are inherently inaccurate according to their precision. " \
                    "While they are handy for expressing very small/large values, they can " \
                    "theoretically lead to inaccurate calculations. Integers and " \
                    "integer-rationals should be preferred if at all possible.",

                    "Decimal notation:    " + self._renderer.formatLexerSyntax("1.5  4.  16.0  .8"),

                    "Scientific notation: " + self._renderer.formatLexerSyntax("3e4  .2e-3  81.7E+2"),

                    "Non-floating-point:  " + self._renderer.formatLexerSyntax("56  14/4")
                )
            ),
            'rational': TermTip(
                "Number: Rational",
                (
                    "Two numbers forming a ratio, one divided by another.",

                    "Integer-rationals (ratios formed by two integers) are the most robust " \
                    "and will provide the highest accuracy over many calculations. Prefer " \
                    "integer-rationals over alternatives if possible.",

                    "Integer ratio (precise): " + self._renderer.formatLexerSyntax("1/4  12/6"),

                    "Float value (imprecise): " + self._renderer.formatLexerSyntax("0.25  2.0"),
                ),
            ),
            'paren_open': 'parentheses',
            'paren_close': 'parentheses',
            'parentheses': TermTip(
                "Punctuation: Parentheses",
                (
                    "Round braces paired together to denote a higher-precedence expression.",

                    "Parentheses must always come in pairs, with an expression enclosed " \
                    "between them. For example:",
                    
                    self._renderer.formatLexerSyntax("a*(b + c)/d"),
                    
                    "In the expression above, the sub-expression " + \
                    self._renderer.formatLexerSyntax("b + c") + " " + \
                    "would be evaluated first, since it is given priority over both " + \
                    self._renderer.formatLexerSyntax("a*...") + " " + \
                    "and " + \
                    self._renderer.formatLexerSyntax(".../d"),
                    # TODO: distinguish from brackets and braces when they are implemented
                )
            ),
            'brace_open': 'braces',
            'brace_close': 'braces',
            'braces': TermTip(
                "Punctuation: Braces",
                (
                    "Curly braces paired together to denote a set of expressions/relations.",

                    # TODO: edit this when objects are implemented
                    "Currently, braces are only used when evaluating multiple values " \
                    "in-place inside the same expression/relation. This is primarily " \
                    "useful when a variable should be related to several values. At " \
                    "the moment, only numerics (that is integers, floats, and rationals) " \
                    "are permitted inside of a set of expressions."

                    "Expression set (valid):   " + self._renderer.formatLexerSyntax("a = {-3, 3}   1 + {-5, 5}*2"),

                    "Expression set (invalid): " + self._renderer.formatLexerSyntax("a = {4, b + 3}   1 + {x, y}^2"),
                )
            ),
            'backtick': TermTip(
                "Punctuation: Backticks",
                (
                    "A paired punctuation that provides a way to explicitly specify " \
                    "alias template arguments.",

                    "Alias templates permit partial syntax. That means the parameters " \
                    "you put in (and the result that comes out) don't have to be valid " \
                    "expressions. Consider these commands:",

                    self._renderer.formatLexerSyntax("plus(a, b) := a + b"),

                    self._renderer.formatLexerSyntax("plus((1, 2))"),

                    "The second command would result in an error of not enough arguments, "\
                    "since parenthesized groups are still respected (even though " + \
                    self._renderer.formatLexerSyntax("1, 2") + " " + \
                    "is not a valid expression). To get around this, backticks can be used " \
                    "to define arguments explicitly:",

                    self._renderer.formatLexerSyntax("plus(`(1`, `2)`)"),

                    "which will evaluate to",

                    self._renderer.formatLexerSyntax("(1 + 2)"),
                )
            ),
            'equals': TermTip(
                "Operator: Equate",
                (
                    "The bridge between two expressions in an equality relation.",

                    "Only relations require equals signs; Expressions cannot contain them.",
                )
            ),
            'colon_equals': TermTip(
                "Operator: Define Alias",
                (
                    "The center bewtween an alias' name/signature and its template.",

                    "This operator is key when creating alias templates. Remember that " \
                    "aliases are fundamentally different than equality relations. You " \
                    "can read more about them in their dedicated dictionary entry."
                )
            ),
            'plus': TermTip(
                "Operator: Plus",
                (
                    "A binary/unary operator signifying either the addition of two values or single positive values.",

                    "Binary addition:  " + self._renderer.formatLexerSyntax("a + b"),

                    "Unary positivity: " + self._renderer.formatLexerSyntax("+a"),
                )
            ),
            'dash': TermTip(
                "Operator: Minus",
                (
                    "A binary/unary operator signifying either the subtraction of two values or single negative values.",

                    "Binary subtraction: " + self._renderer.formatLexerSyntax("a - b"),

                    "Unary negation:     " + self._renderer.formatLexerSyntax("-a"),
                )
            ),
            'star': TermTip(
                "Operator: Asterisk",
                (
                    "A binary operator signifying the multiplication of two values.",

                    "Multiplication: " + self._renderer.formatLexerSyntax("a*b"),
                )
            ),
            'slash': TermTip(
                "Operator: Slash",
                (
                    "A binary operator signifying the division of two values.",

                    "Dividing integers will be treated as a true ratio. Dividing floats will " \
                    "calculate a new (possibly slightly inaccurate) floating point value.",

                    "Division: " + self._renderer.formatLexerSyntax("a/b"),
                )
            ),
            'carrot': TermTip(
                "Operator: Carrot",
                (
                    "A binary operator signifying the exponentiation of two values.",

                    "Prefer integer-ratios when performing roots. Using floating point values " \
                    "as the exponent will yield an approximate floating point result.",

                    "Exponentiation: " + self._renderer.formatInputLog("a^b", True),
                )
            ),
        }

    def lookupTerm(self, term: str):
        item = term.lower()
        while type(item) is str:
            item = self._terms.get(
                item,
                TermTip(
                    "Unknown Term",
                    (
                        f"The requested term [{Colors.textRed.hex}]{term}[/] is unavailable.",
                        f"Please report this as an issue at [{Colors.textBlue.hex} underline]https://github.com/skylon07/SolverPro/issues/new[/]",
                    )
                )
            )
        assert type(item) is TermTip
        return item
    
    def getTermTips(self):
        for (term, tip) in self._terms.items():
            if type(tip) is TermTip:
                yield (term, tip)
