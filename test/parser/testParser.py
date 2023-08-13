import sympy

from src.parsing.parser import CommandParser, Command
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
            LexerToken("15",    LexerTokenTypes.INT, 0),
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
            LexerToken("123",           LexerTokenTypes.INT,        0),
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
            LexerToken('+',     LexerTokenTypes.PLUS,       2),
            LexerToken('b',     LexerTokenTypes.IDENTIFIER, 4),
            LexerToken('=',     LexerTokenTypes.EQUALS,     6),
            LexerToken('c',     LexerTokenTypes.IDENTIFIER, 8),
            LexerToken('-',     LexerTokenTypes.DASH,       10),
            LexerToken('12.34', LexerTokenTypes.FLOAT,      12),
            LexerToken('',      LexerTokenTypes.EOL,        17),
        ))) == [Command.recordRelation((sympy.parse_expr("a+b"), sympy.parse_expr("c-12.34")))], \
            "Parser failed to parse 2-term relation"
        
        assert list(parser.parse((
            LexerToken('ke',        LexerTokenTypes.IDENTIFIER, 0),
            LexerToken('+',         LexerTokenTypes.PLUS,       3),
            LexerToken('extra',     LexerTokenTypes.IDENTIFIER, 5),
            LexerToken('=',         LexerTokenTypes.EQUALS,     11),
            LexerToken('1',         LexerTokenTypes.INT,        13),
            LexerToken('/',         LexerTokenTypes.SLASH,      14),
            LexerToken('2',         LexerTokenTypes.INT,        15),
            LexerToken('*',         LexerTokenTypes.STAR,       17),
            LexerToken('mass',      LexerTokenTypes.IDENTIFIER, 19),
            LexerToken('*',         LexerTokenTypes.STAR,       24),
            LexerToken('velocity',  LexerTokenTypes.IDENTIFIER, 26),
            LexerToken('^',         LexerTokenTypes.CARROT,     34),
            LexerToken('2',         LexerTokenTypes.INT,        35),
            LexerToken('+',         LexerTokenTypes.PLUS,       37),
            LexerToken('-',         LexerTokenTypes.DASH,       39),
            LexerToken('4.6',       LexerTokenTypes.FLOAT,      40),
            LexerToken('',          LexerTokenTypes.EOL,        43),
        ))) == [Command.recordRelation((sympy.parse_expr("ke+extra"), sympy.parse_expr("1/2*mass*velocity**2+-4.6")))], \
            "Parser failed to parse the modified kinetic energy relation"
        
        assert list(parser.parse((
            LexerToken('(',    LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken('1',    LexerTokenTypes.INT,            1),
            LexerToken('+',    LexerTokenTypes.PLUS,           3),
            LexerToken('x',    LexerTokenTypes.IDENTIFIER,     5),
            LexerToken(')',    LexerTokenTypes.PAREN_CLOSE,    6),
            LexerToken('*',    LexerTokenTypes.STAR,           8),
            LexerToken('(',    LexerTokenTypes.PAREN_OPEN,     10),
            LexerToken('4',    LexerTokenTypes.INT,            11),
            LexerToken('*',    LexerTokenTypes.STAR,           12),
            LexerToken('-',    LexerTokenTypes.DASH,           13),
            LexerToken('(',    LexerTokenTypes.PAREN_OPEN,     14),
            LexerToken('1',    LexerTokenTypes.INT,            15),
            LexerToken('+',    LexerTokenTypes.PLUS,           16),
            LexerToken('a',    LexerTokenTypes.IDENTIFIER,     17),
            LexerToken('/',    LexerTokenTypes.SLASH,          18),
            LexerToken('2',    LexerTokenTypes.INT,            19),
            LexerToken(')',    LexerTokenTypes.PAREN_CLOSE,    20),
            LexerToken('+',    LexerTokenTypes.PLUS,           22),
            LexerToken('5',    LexerTokenTypes.INT,            24),
            LexerToken(')',    LexerTokenTypes.PAREN_CLOSE,    25),
            LexerToken('+',    LexerTokenTypes.PLUS,           27),
            LexerToken('(',    LexerTokenTypes.PAREN_OPEN,     29),
            LexerToken('4',    LexerTokenTypes.INT,            30),
            LexerToken('/',    LexerTokenTypes.SLASH,          31),
            LexerToken('2',    LexerTokenTypes.INT,            32),
            LexerToken(')',    LexerTokenTypes.PAREN_CLOSE,    33),
            LexerToken('^',    LexerTokenTypes.CARROT,         34),
            LexerToken('2',    LexerTokenTypes.INT,            35),
            LexerToken('',     LexerTokenTypes.EOL,            36),
        ))) == [Command.evaluateExpression(sympy.parse_expr("(1+x)*(4*-(1+a/2)+5)+(4/2)**2"))], \
            "Parser failed to parse an order of operations nightmare (can you blame it?)"
        
    def testParserForRobustness(self):
        parser = CommandParser()

        assert list(parser.parse(
            LexerToken("45",    LexerTokenTypes.INT, 0),
            LexerToken("",      LexerTokenTypes.EOL, 2),
        )) == [Command.evaluateExpression(sympy.parse_expr("45"))]

        assert list(parser.parse(
            LexerToken("5.6",   LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    3),
        )) == [Command.evaluateExpression(sympy.parse_expr("5.6"))]

        assert list(parser.parse(
            LexerToken("2e10",  LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    4),
        )) == [Command.evaluateExpression(sympy.parse_expr("2e10"))]

        assert list(parser.parse(
            LexerToken("4.7E-7",    LexerTokenTypes.FLOAT,  0),
            LexerToken("",          LexerTokenTypes.EOL,    6),
        )) == [Command.evaluateExpression(sympy.parse_expr("4.7E-7"))]

        assert list(parser.parse(
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )) == [Command.evaluateExpression(sympy.parse_expr("a + b"))]

        assert list(parser.parse(
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )) == [Command.evaluateExpression(sympy.parse_expr("a - b"))]

        assert list(parser.parse(
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("*", LexerTokenTypes.STAR,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )) == [Command.evaluateExpression(sympy.parse_expr("a*b"))]

        assert list(parser.parse(
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("/", LexerTokenTypes.SLASH,      1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )) == [Command.evaluateExpression(sympy.parse_expr("a/d"))]

        assert list(parser.parse(
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^", LexerTokenTypes.CARROT,     1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )) == [Command.evaluateExpression(sympy.parse_expr("a^b"))]

        assert list(parser.parse(
            LexerToken("14",    LexerTokenTypes.INT,    0),
            LexerToken("",      LexerTokenTypes.EOL,    2),
        )) == [Command.evaluateExpression(sympy.parse_expr("14"))]

        assert list(parser.parse(
            LexerToken("20.21", LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    5),
        )) == [Command.evaluateExpression(sympy.parse_expr("20.21"))]

        assert list(parser.parse(
            LexerToken("45e-2", LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    5),
        )) == [Command.evaluateExpression(sympy.parse_expr("45e-2"))]

        assert list(parser.parse(
            LexerToken("0.00123E+45",   LexerTokenTypes.FLOAT,  0),
            LexerToken("",              LexerTokenTypes.EOL,    11),
        )) == [Command.evaluateExpression(sympy.parse_expr("0.00123E+45"))]
        

    # TODO: more tests for failure cases

