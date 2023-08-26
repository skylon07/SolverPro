from typing import Iterable

from rich.console import RenderableType

from src.common.types import FormattedStr
from src.app.textRenderer import TextRenderer


class TermTip:
    def __init__(self, term: FormattedStr, definitionLines: Iterable[RenderableType]):
        self.term = term
        self.definitionLines = tuple(
            f"[#b0b0b0]{line}[/#b0b0b0]" if type(line) is str
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
                    "While numbers are allowed in identifier names, the identifier must start with a " \
                    "non-number character. The only \"identifiers\" currently implemented by " \
                    "Solver Pro are the variables contained in expressions and relations.",

                    # TODO: when colors are implemented, make sure to change these to the right ones
                    "Identifiers: [white]a  my_var  train2Car3[/white]",

                    "Not Identifiers: [white]1.5  3rdBox  +  ()[/white]",
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

                    self._renderer.renderInputLog("a + b", True),

                    "Unary positivity:",

                    self._renderer.renderInputLog("+a", True),
                )
            ),
            'dash': TermTip(
                "Operator: Minus",
                (
                    "A binary/unary operator signifying either the subtraction of two values or single negative values.",

                    "Binary subtraction:",

                    self._renderer.renderInputLog("a - b", True),

                    "Unary negation:",

                    self._renderer.renderInputLog("-a", True),
                )
            ),
            'star': TermTip(
                "Operator: Asterisk",
                (
                    "A binary operator signifying the multiplication of two values.",

                    "Multiplication:",

                    self._renderer.renderInputLog("a*b", True),
                )
            ),
            'slash': TermTip(
                "Operator: Slash",
                (
                    "A binary operator signifying the division of two values.",

                    "Dividing integers will be treated as a true ratio. Dividing floats will " \
                    "calculate a new (possibly slightly inaccurate) floating point value.",

                    "Division:",

                    self._renderer.renderInputLog("a/b", True),
                )
            ),
            'carrot': TermTip(
                "Operator: Carrot",
                (
                    "A binary operator signifying the exponentiation of two values.",

                    "Prefer integer-ratios when performing roots. Using floating point values " \
                    "as the exponent will yield an approximate floating point result.",

                    "Exponentiation:",

                    self._renderer.renderInputLog("a^b", True),
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
                        f"The requested term [red]{term}[/red] is unavailable.",
                        f"Please report this as an issue at [blue underline]https://github.com/skylon07/SolverPro/issues/new[/blue underline]",
                    )
                )
            )
        assert type(item) is TermTip
        return item
    
    def getTermTips(self):
        for (term, tip) in self._terms.items():
            if type(tip) is TermTip:
                yield (term, tip)
