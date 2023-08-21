# type: ignore
import sympy

from src.common.functions import runForError
from src.parsing.parser import CommandParser, Command, ParseException, EolException
from src.parsing.lexer import LexerToken, LexerTokenTypes


class CommandParserTester:
    def testParserCallbackChains(self):
        parser = CommandParser()

        assert list(parser.parse((
            LexerToken("myVar", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        5)
        ))) == [Command.evaluateExpression(sympy.parse_expr("myVar"))], \
            "Parser did not correctly parse a single identifier"

        assert list(parser.parse((
            LexerToken("15",    LexerTokenTypes.INTEGER, 0),
            LexerToken("",      LexerTokenTypes.EOL, 2),
        ))) == [Command.evaluateExpression(sympy.parse_expr("15"))], \
            "Parser did not correctly parse a single integer"

        assert list(parser.parse((
            LexerToken("15.56e+3",  LexerTokenTypes.FLOAT,  0),
            LexerToken("",          LexerTokenTypes.EOL,    8),
        ))) == [Command.evaluateExpression(sympy.parse_expr("15.56e+3"))], \
            "Parser did not correctly process a single float"
        

    def testParserHandlesMultiEols(self):
        parser = CommandParser()

        assert list(parser.parse((
            LexerToken("", LexerTokenTypes.EOL, 0),
        ))) == [Command.empty()], \
            "Parser did not correctly handle an empty command"

        assert list(parser.parse((
            LexerToken("", LexerTokenTypes.EOL, 0),
            LexerToken("", LexerTokenTypes.EOL, 1),
            LexerToken("", LexerTokenTypes.EOL, 2),
            LexerToken("", LexerTokenTypes.EOL, 3),
        ))) == [
            Command.empty(),
            Command.empty(),
            Command.empty(),
            Command.empty(),
        ], "Parser did not correctly handle multiple empty commands"

        assert list(parser.parse((
            LexerToken("123",           LexerTokenTypes.INTEGER,        0),
            LexerToken("",              LexerTokenTypes.EOL,        3),
            LexerToken("someVariable",  LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("",              LexerTokenTypes.EOL,        16),
        ))) == [
            Command.evaluateExpression(sympy.parse_expr("123")),
            Command.evaluateExpression(sympy.parse_expr("someVariable")),
        ], "Parser did not correctly handle multiple command lines"
        
    def testParserHandlesArithmetic(self):
        parser = CommandParser()

        assert list(parser.parse((
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+",     LexerTokenTypes.PLUS,       2),
            LexerToken("b",     LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("=",     LexerTokenTypes.EQUALS,     6),
            LexerToken("c",     LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("-",     LexerTokenTypes.DASH,       10),
            LexerToken("12.34", LexerTokenTypes.FLOAT,      12),
            LexerToken("",      LexerTokenTypes.EOL,        17),
        ))) == [Command.recordRelation((sympy.parse_expr("a+b"), sympy.parse_expr("c-12.34")))], \
            "Parser failed to parse 2-term relation"
        
        assert list(parser.parse((
            LexerToken("ke",        LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+",         LexerTokenTypes.PLUS,       3),
            LexerToken("extra",     LexerTokenTypes.IDENTIFIER, 5),
            LexerToken("=",         LexerTokenTypes.EQUALS,     11),
            LexerToken("1",         LexerTokenTypes.INTEGER,        13),
            LexerToken("/",         LexerTokenTypes.SLASH,      14),
            LexerToken("2",         LexerTokenTypes.INTEGER,        15),
            LexerToken("*",         LexerTokenTypes.STAR,       17),
            LexerToken("mass",      LexerTokenTypes.IDENTIFIER, 19),
            LexerToken("*",         LexerTokenTypes.STAR,       24),
            LexerToken("velocity",  LexerTokenTypes.IDENTIFIER, 26),
            LexerToken("^",         LexerTokenTypes.CARROT,     34),
            LexerToken("2",         LexerTokenTypes.INTEGER,        35),
            LexerToken("+",         LexerTokenTypes.PLUS,       37),
            LexerToken("-",         LexerTokenTypes.DASH,       39),
            LexerToken("4.6",       LexerTokenTypes.FLOAT,      40),
            LexerToken("",          LexerTokenTypes.EOL,        43),
        ))) == [Command.recordRelation((sympy.parse_expr("ke+extra"), sympy.parse_expr("1/2*mass*velocity**2+-4.6")))], \
            "Parser failed to parse the modified kinetic energy relation"
        
        assert list(parser.parse((
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("1",    LexerTokenTypes.INTEGER,            1),
            LexerToken("+",    LexerTokenTypes.PLUS,           3),
            LexerToken("x",    LexerTokenTypes.IDENTIFIER,     5),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    6),
            LexerToken("*",    LexerTokenTypes.STAR,           8),
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     10),
            LexerToken("4",    LexerTokenTypes.INTEGER,            11),
            LexerToken("*",    LexerTokenTypes.STAR,           12),
            LexerToken("-",    LexerTokenTypes.DASH,           13),
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     14),
            LexerToken("1",    LexerTokenTypes.INTEGER,            15),
            LexerToken("+",    LexerTokenTypes.PLUS,           16),
            LexerToken("a",    LexerTokenTypes.IDENTIFIER,     17),
            LexerToken("/",    LexerTokenTypes.SLASH,          18),
            LexerToken("2",    LexerTokenTypes.INTEGER,            19),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    20),
            LexerToken("+",    LexerTokenTypes.PLUS,           22),
            LexerToken("5",    LexerTokenTypes.INTEGER,            24),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    25),
            LexerToken("+",    LexerTokenTypes.PLUS,           27),
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     29),
            LexerToken("4",    LexerTokenTypes.INTEGER,            30),
            LexerToken("/",    LexerTokenTypes.SLASH,          31),
            LexerToken("2",    LexerTokenTypes.INTEGER,            32),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    33),
            LexerToken("^",    LexerTokenTypes.CARROT,         34),
            LexerToken("2",    LexerTokenTypes.INTEGER,            35),
            LexerToken("",     LexerTokenTypes.EOL,            36),
        ))) == [Command.evaluateExpression(sympy.parse_expr("(1+x)*(4*-(1+a/2)+5)+(4/2)**2"))], \
            "Parser failed to parse an order of operations nightmare (can you blame it?)"
        
    def testParserForRobustness(self):
        parser = CommandParser()

        assert list(parser.parse((
            LexerToken("45",    LexerTokenTypes.INTEGER, 0),
            LexerToken("",      LexerTokenTypes.EOL, 2),
        ))) == [Command.evaluateExpression(sympy.parse_expr("45"))]

        assert list(parser.parse((
            LexerToken("5.6",   LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    3),
        ))) == [Command.evaluateExpression(sympy.parse_expr("5.6"))]

        assert list(parser.parse((
            LexerToken("2e10",  LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    4),
        ))) == [Command.evaluateExpression(sympy.parse_expr("2e10"))]

        assert list(parser.parse((
            LexerToken("4.7E-7",    LexerTokenTypes.FLOAT,  0),
            LexerToken("",          LexerTokenTypes.EOL,    6),
        ))) == [Command.evaluateExpression(sympy.parse_expr("4.7E-7"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a+b"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a-b"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("*", LexerTokenTypes.STAR,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a*b"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("/", LexerTokenTypes.SLASH,      1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a/b"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^", LexerTokenTypes.CARROT,     1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a**b"))]

        assert list(parser.parse((
            LexerToken("14",    LexerTokenTypes.INTEGER,    0),
            LexerToken("",      LexerTokenTypes.EOL,    2),
        ))) == [Command.evaluateExpression(sympy.parse_expr("14"))]

        assert list(parser.parse((
            LexerToken("20.21", LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    5),
        ))) == [Command.evaluateExpression(sympy.parse_expr("20.21"))]

        assert list(parser.parse((
            LexerToken("45e-2", LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    5),
        ))) == [Command.evaluateExpression(sympy.parse_expr("45e-2"))]

        assert list(parser.parse((
            LexerToken("0.00123E+45",   LexerTokenTypes.FLOAT,  0),
            LexerToken("",              LexerTokenTypes.EOL,    11),
        ))) == [Command.evaluateExpression(sympy.parse_expr("0.00123E+45"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("=", LexerTokenTypes.EQUALS,     6),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("+", LexerTokenTypes.PLUS,       10),
            LexerToken("d", LexerTokenTypes.IDENTIFIER, 12),
            LexerToken("",  LexerTokenTypes.EOL,        13),
        ))) == [Command.recordRelation((sympy.parse_expr("a+b"), sympy.parse_expr("c+d")))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("",  LexerTokenTypes.EOL,        5),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a+b"))]

        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("+", LexerTokenTypes.PLUS,       6),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("*", LexerTokenTypes.STAR,       10),
            LexerToken("d", LexerTokenTypes.IDENTIFIER, 12),
            LexerToken("/", LexerTokenTypes.SLASH,      14),
            LexerToken("e", LexerTokenTypes.IDENTIFIER, 16),
            LexerToken("^", LexerTokenTypes.CARROT,     18),
            LexerToken("f", LexerTokenTypes.IDENTIFIER, 20),
            LexerToken("-", LexerTokenTypes.DASH,       22),
            LexerToken("g", LexerTokenTypes.IDENTIFIER, 24),
            LexerToken("+", LexerTokenTypes.PLUS,       26),
            LexerToken("h", LexerTokenTypes.IDENTIFIER, 28),
            LexerToken("/", LexerTokenTypes.SLASH,      30),
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 32),
            LexerToken("*", LexerTokenTypes.STAR,       34),
            LexerToken("j", LexerTokenTypes.IDENTIFIER, 36),
            LexerToken("/", LexerTokenTypes.SLASH,      38),
            LexerToken("l", LexerTokenTypes.IDENTIFIER, 40),
            LexerToken("+", LexerTokenTypes.PLUS,       42),
            LexerToken("4", LexerTokenTypes.INTEGER,        44),
            LexerToken("-", LexerTokenTypes.DASH,       46),
            LexerToken("5", LexerTokenTypes.INTEGER,        48),
            LexerToken("^", LexerTokenTypes.CARROT,     50),
            LexerToken("7", LexerTokenTypes.INTEGER,        52),
            LexerToken("",  LexerTokenTypes.EOL,        53),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a-b+c*d/e**f-g+h/a*j/l+4-5**7"))]
        
        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       2),
            LexerToken("-", LexerTokenTypes.DASH,       4),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 5),
            LexerToken("*", LexerTokenTypes.STAR,       7),
            LexerToken("-", LexerTokenTypes.DASH,       9),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 10),
            LexerToken("/", LexerTokenTypes.SLASH,      12),
            LexerToken("-", LexerTokenTypes.DASH,       14),
            LexerToken("d", LexerTokenTypes.IDENTIFIER, 15),
            LexerToken("-", LexerTokenTypes.DASH,       17),
            LexerToken("-", LexerTokenTypes.DASH,       19),
            LexerToken("e", LexerTokenTypes.IDENTIFIER, 20),
            LexerToken("",  LexerTokenTypes.EOL,        21),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a+-b*-c/-d--e"))]
        
        assert list(parser.parse((
            LexerToken("-", LexerTokenTypes.DASH,       0),
            LexerToken("-", LexerTokenTypes.DASH,       1),
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("-", LexerTokenTypes.DASH,       4),
            LexerToken("-", LexerTokenTypes.DASH,       6),
            LexerToken("-", LexerTokenTypes.DASH,       7),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("+", LexerTokenTypes.PLUS,       10),
            LexerToken("-", LexerTokenTypes.DASH,       12),
            LexerToken("-", LexerTokenTypes.DASH,       14),
            LexerToken("-", LexerTokenTypes.DASH,       15),
            LexerToken("-", LexerTokenTypes.DASH,       16),
            LexerToken("-", LexerTokenTypes.DASH,       18),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 19),
            LexerToken("",  LexerTokenTypes.EOL,        20),
        ))) == [Command.evaluateExpression(sympy.parse_expr("--a---b+-----c"))]
        
        assert list(parser.parse((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       2),
            LexerToken("+", LexerTokenTypes.PLUS,       4),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 6),
            LexerToken("",  LexerTokenTypes.EOL,        7),
        ))) == [Command.evaluateExpression(sympy.parse_expr("a-+b"))]
        
        assert list(parser.parse((
            LexerToken("(",             LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("expression",    LexerTokenTypes.IDENTIFIER,     1),
            LexerToken(")",             LexerTokenTypes.PAREN_CLOSE,    11),
            LexerToken("",              LexerTokenTypes.EOL,            12),
        ))) == [Command.evaluateExpression(sympy.parse_expr("(expression)"))]

        # sympy.parse_expr("as") throws an error! (as well as other python keywords)
        # make sure parser guards against this
        assert list(parser.parse((
            LexerToken("as",    LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        2),
        ))) == [Command.evaluateExpression(sympy.Symbol("as"))], \
            "Parser did not correctly evaluate symbol 'as'"
        assert list(parser.parse((
            LexerToken("if",    LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        2),
        ))) == [Command.evaluateExpression(sympy.Symbol("if"))], \
            "Parser did not correctly evaluate symbol 'if'"
        assert list(parser.parse((
            LexerToken("while", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        5),
        ))) == [Command.evaluateExpression(sympy.Symbol("while"))], \
            "Parser did not correctly evaluate symbol 'while'"

    def testParserErrorCases(self):
        parser = CommandParser()

        def attempt1():
            return list(parser.parse((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("=", LexerTokenTypes.EQUALS,     2),
                LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                LexerToken("=", LexerTokenTypes.EQUALS,     6),
                LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
                LexerToken("",  LexerTokenTypes.EOL,        9),
            )))
        error1 = runForError(attempt1)
        assert type(error1) is ParseException
        assert error1.tokens == (
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("=", LexerTokenTypes.EQUALS,     2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("=", LexerTokenTypes.EQUALS,     6),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("",  LexerTokenTypes.EOL,        9),
        )
        assert error1.badTokenIdxs == [3]

        def attempt2():
            return list(parser.parse((
                LexerToken("4.",    LexerTokenTypes.FLOAT,  0),
                LexerToken(".5",    LexerTokenTypes.FLOAT,  2),
                LexerToken("",      LexerTokenTypes.EOL,    4),
            )))
        error2 = runForError(attempt2)
        assert type(error2) is ParseException
        assert error2.tokens == (
            LexerToken("4.",    LexerTokenTypes.FLOAT,  0),
            LexerToken(".5",    LexerTokenTypes.FLOAT,  2),
            LexerToken("",      LexerTokenTypes.EOL,    4),
        )
        assert error2.badTokenIdxs == [1]

        def attempt3():
            return list(parser.parse((
                LexerToken("this",      LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("is",        LexerTokenTypes.IDENTIFIER, 5),
                LexerToken("invalid",   LexerTokenTypes.IDENTIFIER, 8),
                LexerToken("",          LexerTokenTypes.EOL,        15),
            )))
        error3 = runForError(attempt3)
        assert type(error3) is ParseException
        assert error3.tokens == (
            LexerToken("this",      LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("is",        LexerTokenTypes.IDENTIFIER, 5),
            LexerToken("invalid",   LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("",          LexerTokenTypes.EOL,        15),
        )
        assert error3.badTokenIdxs == [1]

        def attempt4():
            return list(parser.parse((
                LexerToken("=", LexerTokenTypes.EQUALS,     0),
                LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
                LexerToken("",  LexerTokenTypes.EOL,        3),
            )))
        error4 = runForError(attempt4)
        assert type(error4) is ParseException
        assert error4.tokens == (
            LexerToken("=", LexerTokenTypes.EQUALS,     0),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )
        assert error4.badTokenIdxs == [0]

        def attempt5():
            return list(parser.parse((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("=", LexerTokenTypes.EQUALS,     2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            )))
        error5 = runForError(attempt5)
        assert type(error5) is EolException
        assert error5.tokens == (
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("=", LexerTokenTypes.EQUALS,     2),
            LexerToken("",  LexerTokenTypes.EOL,        4),
        )
        assert error5.badTokenIdxs == [2]

        def attempt6():
            return list(parser.parse((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("+", LexerTokenTypes.PLUS,       2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            )))
        error6 = runForError(attempt6)
        assert type(error6) is EolException
        assert error6.tokens == (
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       2),
            LexerToken("",  LexerTokenTypes.EOL,        4),
        )
        assert error6.badTokenIdxs == [2]

        def attempt7():
            return list(parser.parse((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("/", LexerTokenTypes.SLASH,      2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            )))
        error7 = runForError(attempt7)
        assert type(error7) is EolException
        assert error7.tokens == (
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("/", LexerTokenTypes.SLASH,      2),
            LexerToken("",  LexerTokenTypes.EOL,        4),
        )
        assert error7.badTokenIdxs == [2]

        def attempt8():
            return list(parser.parse((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("^", LexerTokenTypes.CARROT,     2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            )))
        error8 = runForError(attempt8)
        assert type(error8) is EolException
        assert error8.tokens == (
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^", LexerTokenTypes.CARROT,     2),
            LexerToken("",  LexerTokenTypes.EOL,        4),
        )
        assert error8.badTokenIdxs == [2]

        def attempt9():
            return list(parser.parse((
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
                LexerToken("a", LexerTokenTypes.IDENTIFIER,     1),
                LexerToken("+", LexerTokenTypes.PLUS,           3),
                LexerToken("b", LexerTokenTypes.IDENTIFIER,     5),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    6),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
                LexerToken("",  LexerTokenTypes.EOL,            8),
            )))
        error9 = runForError(attempt9)
        assert type(error9) is ParseException
        assert error9.tokens == (
            LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("a", LexerTokenTypes.IDENTIFIER,     1),
            LexerToken("+", LexerTokenTypes.PLUS,           3),
            LexerToken("b", LexerTokenTypes.IDENTIFIER,     5),
            LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    6),
            LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
            LexerToken("",  LexerTokenTypes.EOL,            8),
        )
        assert error9.badTokenIdxs == [5]

        def attempt10():
            return list(parser.parse((
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     1),
                LexerToken("a", LexerTokenTypes.IDENTIFIER,     2),
                LexerToken("+", LexerTokenTypes.PLUS,           4),
                LexerToken("b", LexerTokenTypes.IDENTIFIER,     6),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
                LexerToken("",  LexerTokenTypes.EOL,            8),
            )))
        error10 = runForError(attempt10)
        assert type(error10) is EolException
        assert error10.tokens == (
            LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("(", LexerTokenTypes.PAREN_OPEN,     1),
            LexerToken("a", LexerTokenTypes.IDENTIFIER,     2),
            LexerToken("+", LexerTokenTypes.PLUS,           4),
            LexerToken("b", LexerTokenTypes.IDENTIFIER,     6),
            LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
            LexerToken("",  LexerTokenTypes.EOL,            8),
        )
        assert error10.badTokenIdxs == [6]

        def attempt11():
            return list(parser.parse((
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
                LexerToken("a", LexerTokenTypes.IDENTIFIER,     1),
                LexerToken("+", LexerTokenTypes.PLUS,           3),
                LexerToken("+", LexerTokenTypes.PLUS,           5),
                LexerToken("b", LexerTokenTypes.IDENTIFIER,     6),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
                LexerToken("-", LexerTokenTypes.DASH,           9),
                LexerToken("-", LexerTokenTypes.DASH,           11),
                LexerToken("+", LexerTokenTypes.PLUS,           12),
                LexerToken("c", LexerTokenTypes.IDENTIFIER,     13),
                LexerToken("*", LexerTokenTypes.STAR,           15),
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     17),
                LexerToken("d", LexerTokenTypes.IDENTIFIER,     18),
                LexerToken("+", LexerTokenTypes.PLUS,           20),
                LexerToken("*", LexerTokenTypes.STAR,           21),
                LexerToken("e", LexerTokenTypes.IDENTIFIER,     22),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    23),
                LexerToken("/", LexerTokenTypes.SLASH,          25),
                LexerToken("d", LexerTokenTypes.IDENTIFIER,     27),
                LexerToken("",  LexerTokenTypes.EOL,            28),
            )))
        error11 = runForError(attempt11)
        assert type(error11) is ParseException
        assert error11.tokens == (
            LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("a", LexerTokenTypes.IDENTIFIER,     1),
            LexerToken("+", LexerTokenTypes.PLUS,           3),
            LexerToken("+", LexerTokenTypes.PLUS,           5),
            LexerToken("b", LexerTokenTypes.IDENTIFIER,     6),
            LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
            LexerToken("-", LexerTokenTypes.DASH,           9),
            LexerToken("-", LexerTokenTypes.DASH,           11),
            LexerToken("+", LexerTokenTypes.PLUS,           12),
            LexerToken("c", LexerTokenTypes.IDENTIFIER,     13),
            LexerToken("*", LexerTokenTypes.STAR,           15),
            LexerToken("(", LexerTokenTypes.PAREN_OPEN,     17),
            LexerToken("d", LexerTokenTypes.IDENTIFIER,     18),
            LexerToken("+", LexerTokenTypes.PLUS,           20),
            LexerToken("*", LexerTokenTypes.STAR,           21),
            LexerToken("e", LexerTokenTypes.IDENTIFIER,     22),
            LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    23),
            LexerToken("/", LexerTokenTypes.SLASH,          25),
            LexerToken("d", LexerTokenTypes.IDENTIFIER,     27),
            LexerToken("",  LexerTokenTypes.EOL,            28),
        )
        assert error11.badTokenIdxs == [14]

        # sympy parses this and just returns "1";
        # this test makes sure the app's parser does its actual job
        def attempt_pythonLikeExpr():
            return list(parser.parse((
                LexerToken("1",     LexerTokenTypes.INTEGER,        0),
                LexerToken("if",    LexerTokenTypes.IDENTIFIER, 2),
                LexerToken("1",     LexerTokenTypes.INTEGER,        5),
                LexerToken("else",  LexerTokenTypes.IDENTIFIER, 7),
                LexerToken("0",     LexerTokenTypes.INTEGER,        12),
                LexerToken("",      LexerTokenTypes.EOL,        13),
            )))
        error_pythonLikeExpr = runForError(attempt_pythonLikeExpr)
        assert type(error_pythonLikeExpr) is ParseException
        assert error_pythonLikeExpr.badTokenIdxs == [1]
