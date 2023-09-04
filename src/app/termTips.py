from typing import Iterable

from rich.console import RenderableType

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
        self._renderer = TextRenderer()
        self._terms: dict[str, TermTip | str] = {
            'identifiers': 'identifier',
            'identifier': TermTip(
                "Identifier",
                (
                    "A word or other group of letters/numbers acting as a label to some value.",
                    
                    # TODO: edit this when aliasing is implemented
                    "The only \"identifiers\" currently implemented by " \
                    "Solver Pro are the variables contained in expressions and relations." \
                    "Identifiers consist of letters and numbers (but no spaces -- " \
                    "use underscores), with at least one letter present. Unlike most " \
                    "other programs, Solver Pro permits a number to start an identifier " \
                    "name, as long as at least one letter appears in the name later.",

                    # TODO: when colors are implemented, make sure to change these to the right ones
                    f"Identifiers: [{Colors.textPlain.hex}]a  my_var  train2Car3  3rdBox[/]",

                    f"Not Identifiers: [{Colors.textPlain.hex}]345  1.5  +  ()[/]",
                )
            ),
            'integer': TermTip(
                "Number: Integer",
                (
                    "A whole number without a decimal or exponent part.",

                    "Of all the kinds of numbers Solver Pro supports, integers are the most" \
                    "precise. Use them as much as possible.",
                )
            ),
            'float': TermTip(
                "Number: Floating Point",
                (
                    "A number representing a decimal or a scientific number.",

                    "Floats are inherently inaccurate according to their precision. " \
                    "While they are handy for expressing very small/large values, they can " \
                    "theoretically lead to inaccurate calculations. Integers and integer-rationals " \
                    "should be preferred if at all possible.",
                )
            ),
            'rational': TermTip(
                "Number: Rational",
                (
                    "Two numbers forming a ratio, one divided by another.",

                    "Integer-rationals (ratios formed by two integers) are the most robust " \
                    "and will provide the highest accuracy over many calculations. Prefer integer-rationals " \
                    "over alternatives if possible.",
                ),
            ),
            # TODO: can probably consolidate these into one entry (then point to it from paren_open/paren_close)
            'paren_open': TermTip(
                "Parenthesis (Opening)",
                (
                    "The opening parenthesis \"(\" of a pair of parentheses.",

                    # TODO: distinguish from brackets and braces when they are implemented
                )
            ),
            'paren_close': TermTip(
                "Parenthesis (Closing)",
                (
                    "The closing parenthesis \")\" of a pair of parentheses.",

                    # TODO: distinguish from brackets and braces when they are implemented
                )
            ),
            # TODO: entries on braces (and add a TODO for when objects are implemented)
            'equals': TermTip(
                "Operator: Equate",
                (
                    "The bridge between two expressions in an equality relation.",

                    "Only relations require equals signs; Expressions cannot contain them.",
                )
            ),
            'plus': TermTip(
                "Operator: Plus",
                (
                    "A binary/unary operator signifying either the addition of two values or single positive values.",

                    "Binary addition:",

                    self._renderer.formatInputLog("a + b", True),

                    "Unary positivity:",

                    self._renderer.formatInputLog("+a", True),
                )
            ),
            'dash': TermTip(
                "Operator: Minus",
                (
                    "A binary/unary operator signifying either the subtraction of two values or single negative values.",

                    "Binary subtraction:",

                    self._renderer.formatInputLog("a - b", True),

                    "Unary negation:",

                    self._renderer.formatInputLog("-a", True),
                )
            ),
            'star': TermTip(
                "Operator: Asterisk",
                (
                    "A binary operator signifying the multiplication of two values.",

                    "Multiplication:",

                    self._renderer.formatInputLog("a*b", True),
                )
            ),
            'slash': TermTip(
                "Operator: Slash",
                (
                    "A binary operator signifying the division of two values.",

                    "Dividing integers will be treated as a true ratio. Dividing floats will " \
                    "calculate a new (possibly slightly inaccurate) floating point value.",

                    "Division:",

                    self._renderer.formatInputLog("a/b", True),
                )
            ),
            'carrot': TermTip(
                "Operator: Carrot",
                (
                    "A binary operator signifying the exponentiation of two values.",

                    "Prefer integer-ratios when performing roots. Using floating point values " \
                    "as the exponent will yield an approximate floating point result.",

                    "Exponentiation:",

                    self._renderer.formatInputLog("a^b", True),
                )
            ),
            'end of line': 'eol',
            'eol': TermTip(
                "End of Line",
                (
                    "An invisible delimiter that indicates the end of a line of input.",

                    "If an end of line is \"unexpected\", that indicates an incomplete command " \
                    "was entered."
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
