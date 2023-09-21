import sympy

from src.common.functions import runForError
from src.common.sympyLinterFixes import createSymbol
from src.parsing.parser import CommandParser, Command, AliasTemplate, BuiltinAlias, ParseException, EolException, UnknownAliasException, AliasArgumentCountException, UnknownCommandException
from src.parsing.lexer import CommandLexer, LexerToken, LexerTokenTypes


class CommandParserTester:
    def testCommandResults(self):
        assert list(CommandParser.parseCommand((
            LexerToken("myVar", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        5)
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("myVar"))], \
            "Parser did not correctly parse a single identifier"

        assert list(CommandParser.parseCommand((
            LexerToken("15",    LexerTokenTypes.INTEGER, 0),
            LexerToken("",      LexerTokenTypes.EOL, 2),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("15"))], \
            "Parser did not correctly parse a single integer"

        assert list(CommandParser.parseCommand((
            LexerToken("15.56e+3",  LexerTokenTypes.FLOAT,  0),
            LexerToken("",          LexerTokenTypes.EOL,    8),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("15.56e+3"))], \
            "Parser did not correctly process a single float"
        
    def testHandlesMultiEols(self):
        assert list(CommandParser.parseCommand((
            LexerToken("", LexerTokenTypes.EOL, 0),
        ), dict(), dict())) == [Command.empty()], \
            "Parser did not correctly handle an empty command"

        assert list(CommandParser.parseCommand((
            LexerToken("", LexerTokenTypes.EOL, 0),
            LexerToken("", LexerTokenTypes.EOL, 1),
            LexerToken("", LexerTokenTypes.EOL, 2),
            LexerToken("", LexerTokenTypes.EOL, 3),
        ), dict(), dict())) == [
            Command.empty(),
            Command.empty(),
            Command.empty(),
            Command.empty(),
        ], "Parser did not correctly handle multiple empty commands"

        assert list(CommandParser.parseCommand((
            LexerToken("123",           LexerTokenTypes.INTEGER,    0),
            LexerToken("",              LexerTokenTypes.EOL,        3),
            LexerToken("someVariable",  LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("",              LexerTokenTypes.EOL,        16),
        ), dict(), dict())) == [
            Command.evaluateExpression(sympy.parse_expr("123")),
            Command.evaluateExpression(sympy.parse_expr("someVariable")),
        ], "Parser did not correctly handle multiple command lines"
        
    def testHandlesArithmetic(self):
        assert list(CommandParser.parseCommand((
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+",     LexerTokenTypes.PLUS,       2),
            LexerToken("b",     LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("=",     LexerTokenTypes.EQUALS,     6),
            LexerToken("c",     LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("-",     LexerTokenTypes.DASH,       10),
            LexerToken("12.34", LexerTokenTypes.FLOAT,      12),
            LexerToken("",      LexerTokenTypes.EOL,        17),
        ), dict(), dict())) == [Command.recordRelations([sympy.parse_expr("a+b"), sympy.parse_expr("c-12.34")])], \
            "Parser failed to parse 2-term relation"
        
        assert list(CommandParser.parseCommand((
            LexerToken("ke",        LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+",         LexerTokenTypes.PLUS,       3),
            LexerToken("extra",     LexerTokenTypes.IDENTIFIER, 5),
            LexerToken("=",         LexerTokenTypes.EQUALS,     11),
            LexerToken("1",         LexerTokenTypes.INTEGER,    13),
            LexerToken("/",         LexerTokenTypes.SLASH,      14),
            LexerToken("2",         LexerTokenTypes.INTEGER,    15),
            LexerToken("*",         LexerTokenTypes.STAR,       17),
            LexerToken("mass",      LexerTokenTypes.IDENTIFIER, 19),
            LexerToken("*",         LexerTokenTypes.STAR,       24),
            LexerToken("velocity",  LexerTokenTypes.IDENTIFIER, 26),
            LexerToken("^",         LexerTokenTypes.CARET,      34),
            LexerToken("2",         LexerTokenTypes.INTEGER,    35),
            LexerToken("+",         LexerTokenTypes.PLUS,       37),
            LexerToken("-",         LexerTokenTypes.DASH,       39),
            LexerToken("4.6",       LexerTokenTypes.FLOAT,      40),
            LexerToken("",          LexerTokenTypes.EOL,        43),
        ), dict(), dict())) == [Command.recordRelations([sympy.parse_expr("ke+extra"), sympy.parse_expr("1/2*mass*velocity**2+-4.6")])], \
            "Parser failed to parse the modified kinetic energy relation"
        
        assert list(CommandParser.parseCommand((
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("1",    LexerTokenTypes.INTEGER,        1),
            LexerToken("+",    LexerTokenTypes.PLUS,           3),
            LexerToken("x",    LexerTokenTypes.IDENTIFIER,     5),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    6),
            LexerToken("*",    LexerTokenTypes.STAR,           8),
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     10),
            LexerToken("4",    LexerTokenTypes.INTEGER,        11),
            LexerToken("*",    LexerTokenTypes.STAR,           12),
            LexerToken("-",    LexerTokenTypes.DASH,           13),
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     14),
            LexerToken("1",    LexerTokenTypes.INTEGER,        15),
            LexerToken("+",    LexerTokenTypes.PLUS,           16),
            LexerToken("a",    LexerTokenTypes.IDENTIFIER,     17),
            LexerToken("/",    LexerTokenTypes.SLASH,          18),
            LexerToken("2",    LexerTokenTypes.INTEGER,        19),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    20),
            LexerToken("+",    LexerTokenTypes.PLUS,           22),
            LexerToken("5",    LexerTokenTypes.INTEGER,        24),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    25),
            LexerToken("+",    LexerTokenTypes.PLUS,           27),
            LexerToken("(",    LexerTokenTypes.PAREN_OPEN,     29),
            LexerToken("4",    LexerTokenTypes.INTEGER,        30),
            LexerToken("/",    LexerTokenTypes.SLASH,          31),
            LexerToken("2",    LexerTokenTypes.INTEGER,        32),
            LexerToken(")",    LexerTokenTypes.PAREN_CLOSE,    33),
            LexerToken("^",    LexerTokenTypes.CARET,          34),
            LexerToken("2",    LexerTokenTypes.INTEGER,        35),
            LexerToken("",     LexerTokenTypes.EOL,            36),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("(1+x)*(4*-(1+a/2)+5)+(4/2)**2"))], \
            "Parser failed to parse an order of operations nightmare (can you blame it?)"
        
    def testHandlesMultipleRelations(self):
        assert list(CommandParser.parseCommand((
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+",     LexerTokenTypes.PLUS,       2),
            LexerToken("b",     LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("=",     LexerTokenTypes.EQUALS,     6),
            LexerToken("c",     LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("-",     LexerTokenTypes.DASH,       10),
            LexerToken("12.34", LexerTokenTypes.FLOAT,      12),
            LexerToken("=",     LexerTokenTypes.EQUALS,     14),
            LexerToken("d",     LexerTokenTypes.IDENTIFIER, 16),
            LexerToken("+",     LexerTokenTypes.PLUS,       18),
            LexerToken("E",     LexerTokenTypes.IDENTIFIER, 20),
            LexerToken("=",     LexerTokenTypes.EQUALS,     22),
            LexerToken("f",     LexerTokenTypes.IDENTIFIER, 24),
            LexerToken("*",     LexerTokenTypes.STAR,       25),
            LexerToken("g",     LexerTokenTypes.FLOAT,      26),
            LexerToken("",      LexerTokenTypes.EOL,        27),
        ), dict(), dict())) == [Command.recordRelations([sympy.parse_expr("a+b"), sympy.parse_expr("c-12.34"), createSymbol("d") + createSymbol("E"), sympy.parse_expr("f*g")])], \
            "Parser failed to parse 4-term relation"
        
    def testHandlesExpressionListSymbols(self):
        assert list(CommandParser.parseCommand((
            LexerToken("{",     LexerTokenTypes.BRACE_OPEN,     0),
            LexerToken("6",     LexerTokenTypes.INTEGER,        1),
            LexerToken(",",     LexerTokenTypes.COMMA,          2),
            LexerToken("22",    LexerTokenTypes.INTEGER,        4),
            LexerToken("}",     LexerTokenTypes.BRACE_CLOSE,    6),
            LexerToken("",      LexerTokenTypes.EOL,            7),
        ), dict(), dict())) == [Command.evaluateExpression(createSymbol("{6, 22}"))], \
            "Parser failed to parse an expression with two expression list symbols"
        
        assert list(CommandParser.parseCommand((
            LexerToken("4",     LexerTokenTypes.INTEGER,        0),
            LexerToken("+",     LexerTokenTypes.PLUS,           2),
            LexerToken("{",     LexerTokenTypes.BRACE_OPEN,     4),
            LexerToken("10",    LexerTokenTypes.INTEGER,        5),
            LexerToken("+",     LexerTokenTypes.PLUS,           8),
            LexerToken("2",     LexerTokenTypes.INTEGER,        10),
            LexerToken("}",     LexerTokenTypes.BRACE_CLOSE,    11),
            LexerToken("/",     LexerTokenTypes.SLASH,          13),
            LexerToken("{",     LexerTokenTypes.BRACE_OPEN,     15),
            LexerToken("4",     LexerTokenTypes.INTEGER,        16),
            LexerToken(",",     LexerTokenTypes.COMMA,          17),
            LexerToken("5",     LexerTokenTypes.INTEGER,        18),
            LexerToken("}",     LexerTokenTypes.BRACE_CLOSE,    19),
            LexerToken("",      LexerTokenTypes.EOL,            20),
        ), dict(), dict())) == [Command.evaluateExpression(
            4 + createSymbol("{12}") / createSymbol("{4, 5}") # type: ignore
        )], "Parser failed to parse an expression with two expression list symbols"

        assert list(CommandParser.parseCommand((
            LexerToken("{",     LexerTokenTypes.BRACE_OPEN,     0),
            LexerToken("3",     LexerTokenTypes.INTEGER,        1),
            LexerToken(",",     LexerTokenTypes.COMMA,          2),
            LexerToken("2",     LexerTokenTypes.INTEGER,        4),
            LexerToken(",",     LexerTokenTypes.COMMA,          5),
            LexerToken("1",     LexerTokenTypes.INTEGER,        7),
            LexerToken("}",     LexerTokenTypes.BRACE_CLOSE,    8),
            LexerToken("",      LexerTokenTypes.EOL,            9),
        ), dict(), dict())) == [Command.evaluateExpression(createSymbol("{1, 2, 3}"))], \
            "Parser failed to sort expression list before making it a symbol"

    def testProcessesExpressionLists(self):
        assert list(CommandParser.parseExpressionList((
            LexerToken("1", LexerTokenTypes.INTEGER,    0),
            LexerToken("+", LexerTokenTypes.PLUS,       1),
            LexerToken("2", LexerTokenTypes.INTEGER,    2),
            LexerToken(",", LexerTokenTypes.COMMA,      3),
            LexerToken("5", LexerTokenTypes.INTEGER,    5),
            LexerToken(",", LexerTokenTypes.COMMA,      6),
            LexerToken("2", LexerTokenTypes.INTEGER,    8),
            LexerToken("*", LexerTokenTypes.STAR,       9),
            LexerToken("2", LexerTokenTypes.INTEGER,    10),
            LexerToken("",  LexerTokenTypes.EOL,        11),
        )))
        
    def testEvaluatesAliases(self):
        aliases = {
            "alias0": AliasTemplate(
                "alias0",
                tuple(),
                (
                    LexerToken("ALIAS0", LexerTokenTypes.IDENTIFIER, 0),
                ),
            ),
            "alias1": AliasTemplate(
                "alias1",
                tuple(["a"]),
                (
                    LexerToken("ALIAS1",    LexerTokenTypes.IDENTIFIER, 0),
                    LexerToken("-",         LexerTokenTypes.DASH,       7),
                    LexerToken("a",         LexerTokenTypes.IDENTIFIER, 9),
                ),
            ),
            "alias2": AliasTemplate(
                "alias2",
                tuple(["a", "b"]),
                (
                    LexerToken("ALIAS2",    LexerTokenTypes.IDENTIFIER, 0),
                    LexerToken("-",         LexerTokenTypes.DASH,       7),
                    LexerToken("a",         LexerTokenTypes.IDENTIFIER, 9),
                    LexerToken("-",         LexerTokenTypes.DASH,       11),
                    LexerToken("b",         LexerTokenTypes.IDENTIFIER, 13),
                ),
            ),
            "alias3": AliasTemplate(
                "alias3",
                tuple(["a", "b", "c"]),
                (
                    LexerToken("ALIAS3",    LexerTokenTypes.IDENTIFIER, 0),
                    LexerToken("-",         LexerTokenTypes.DASH,       7),
                    LexerToken("a",         LexerTokenTypes.IDENTIFIER, 9),
                    LexerToken("-",         LexerTokenTypes.DASH,       11),
                    LexerToken("b",         LexerTokenTypes.IDENTIFIER, 13),
                    LexerToken("-",         LexerTokenTypes.DASH,       15),
                    LexerToken("c",         LexerTokenTypes.IDENTIFIER, 17),
                ),
            ),
        }

        assert CommandParser.preprocessAliases((
            LexerToken("alias0",    LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("",          LexerTokenTypes.EOL,            6),
        ), aliases) == "ALIAS0"

        assert CommandParser.preprocessAliases((
            LexerToken("alias0",    LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     5),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    28),
            LexerToken("",          LexerTokenTypes.EOL,            29),
        ), aliases) == "ALIAS0"

        assert CommandParser.preprocessAliases((
            LexerToken("alias1",    LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     5),
            LexerToken("param1",    LexerTokenTypes.IDENTIFIER,     6),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    28),
            LexerToken("",          LexerTokenTypes.EOL,            29),
        ), aliases) == "ALIAS1 - param1"

        assert CommandParser.preprocessAliases((
            LexerToken("alias2",    LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     5),
            LexerToken("param1",    LexerTokenTypes.IDENTIFIER,     6),
            LexerToken(",",         LexerTokenTypes.COMMA,          12),
            LexerToken("param2",    LexerTokenTypes.IDENTIFIER,     14),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    28),
            LexerToken("",          LexerTokenTypes.EOL,            29),
        ), aliases) == "ALIAS2 - param1 - param2"

        assert CommandParser.preprocessAliases((
            LexerToken("alias3",    LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     5),
            LexerToken("param1",    LexerTokenTypes.IDENTIFIER,     6),
            LexerToken(",",         LexerTokenTypes.COMMA,          12),
            LexerToken("param2",    LexerTokenTypes.IDENTIFIER,     14),
            LexerToken(",",         LexerTokenTypes.COMMA,          20),
            LexerToken("param3",    LexerTokenTypes.IDENTIFIER,     22),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    28),
            LexerToken("",          LexerTokenTypes.EOL,            29),
        ), aliases) == "ALIAS3 - param1 - param2 - param3"

        assert CommandParser.preprocessAliases((
            LexerToken("PADDING",   LexerTokenTypes.IDENTIFIER,     4),
            LexerToken("TEST",      LexerTokenTypes.IDENTIFIER,     12),
            LexerToken("alias3",    LexerTokenTypes.IDENTIFIER,     18),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     24),
            LexerToken("param1",    LexerTokenTypes.IDENTIFIER,     25),
            LexerToken(",",         LexerTokenTypes.COMMA,          31),
            LexerToken("param2",    LexerTokenTypes.IDENTIFIER,     33),
            LexerToken(",",         LexerTokenTypes.COMMA,          39),
            LexerToken("param3",    LexerTokenTypes.IDENTIFIER,     41),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    47),
            LexerToken("",          LexerTokenTypes.EOL,            51),
        ), aliases) == "    PADDING TEST  ALIAS3 - param1 - param2 - param3"

    def testEvaluatesBuiltinAliases(self):
        builtinAliases = {
            "sqrt": BuiltinAlias("sqrt", 1, lambda x: sympy.sqrt(x)),
        }
        
        assert list(CommandParser.parseCommand((
            LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("+",         LexerTokenTypes.PLUS,           10),
            LexerToken("sqrt",      LexerTokenTypes.IDENTIFIER,     12),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     16),
            LexerToken("4",         LexerTokenTypes.INTEGER,        17),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    18),
            LexerToken("",          LexerTokenTypes.EOL,            19),
        ), dict(), builtinAliases)) == [Command.evaluateExpression(sympy.parse_expr("something + 2"))]

    def testRecordingAliasCommand(self):
        assert list(CommandParser.parseCommand((
            LexerToken("add",       LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     3),
            LexerToken("param1",    LexerTokenTypes.IDENTIFIER,     4),
            LexerToken(",",         LexerTokenTypes.COMMA,          10),
            LexerToken("param2",    LexerTokenTypes.IDENTIFIER,     12),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    18),
            LexerToken(":=",        LexerTokenTypes.COLON_EQUALS,   20),
            LexerToken("param1",    LexerTokenTypes.IDENTIFIER,     23),
            LexerToken("+",         LexerTokenTypes.PLUS,           30),
            LexerToken("param2",    LexerTokenTypes.IDENTIFIER,     32),
            LexerToken("",          LexerTokenTypes.EOL,            38),
        ), dict(), dict())) == [Command.recordAlias(("add", ("param1", "param2"), "param1 + param2"))]
        
    def testForRobustness(self):
        assert list(CommandParser.parseCommand((
            LexerToken("45",    LexerTokenTypes.INTEGER,    0),
            LexerToken("",      LexerTokenTypes.EOL,        2),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("45"))]

        assert list(CommandParser.parseCommand((
            LexerToken("5.6",   LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    3),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("5.6"))]

        assert list(CommandParser.parseCommand((
            LexerToken("2e10",  LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    4),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("2e10"))]

        assert list(CommandParser.parseCommand((
            LexerToken("4.7E-7",    LexerTokenTypes.FLOAT,  0),
            LexerToken("",          LexerTokenTypes.EOL,    6),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("4.7E-7"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a+b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a-b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("*", LexerTokenTypes.STAR,       1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a*b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("/", LexerTokenTypes.SLASH,      1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a/b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^", LexerTokenTypes.CARET,      1),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a**b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("14",    LexerTokenTypes.INTEGER,    0),
            LexerToken("",      LexerTokenTypes.EOL,    2),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("14"))]

        assert list(CommandParser.parseCommand((
            LexerToken("20.21", LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    5),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("20.21"))]

        assert list(CommandParser.parseCommand((
            LexerToken("45e-2", LexerTokenTypes.FLOAT,  0),
            LexerToken("",      LexerTokenTypes.EOL,    5),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("45e-2"))]

        assert list(CommandParser.parseCommand((
            LexerToken("0.00123E+45",   LexerTokenTypes.FLOAT,  0),
            LexerToken("",              LexerTokenTypes.EOL,    11),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("0.00123E+45"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("=", LexerTokenTypes.EQUALS,     6),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("+", LexerTokenTypes.PLUS,       10),
            LexerToken("d", LexerTokenTypes.IDENTIFIER, 12),
            LexerToken("",  LexerTokenTypes.EOL,        13),
        ), dict(), dict())) == [Command.recordRelations([sympy.parse_expr("a+b"), sympy.parse_expr("c+d")])]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+", LexerTokenTypes.PLUS,       2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("",  LexerTokenTypes.EOL,        5),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a+b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("+", LexerTokenTypes.PLUS,       6),
            LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
            LexerToken("*", LexerTokenTypes.STAR,       10),
            LexerToken("d", LexerTokenTypes.IDENTIFIER, 12),
            LexerToken("/", LexerTokenTypes.SLASH,      14),
            LexerToken("z", LexerTokenTypes.IDENTIFIER, 16),
            LexerToken("^", LexerTokenTypes.CARET,      18),
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
            LexerToken("4", LexerTokenTypes.INTEGER,    44),
            LexerToken("-", LexerTokenTypes.DASH,       46),
            LexerToken("5", LexerTokenTypes.INTEGER,    48),
            LexerToken("^", LexerTokenTypes.CARET,      50),
            LexerToken("7", LexerTokenTypes.INTEGER,    52),
            LexerToken("",  LexerTokenTypes.EOL,        53),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a-b+c*d/z**f-g+h/a*j/l+4-5**7"))]
        
        assert list(CommandParser.parseCommand((
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
            LexerToken("z", LexerTokenTypes.IDENTIFIER, 20),
            LexerToken("",  LexerTokenTypes.EOL,        21),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a+-b*-c/-d--z"))]
        
        assert list(CommandParser.parseCommand((
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
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("--a---b+-----c"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^",     LexerTokenTypes.CARET,      1),
            LexerToken("-",     LexerTokenTypes.DASH,       2),
            LexerToken("b",     LexerTokenTypes.IDENTIFIER, 3),
            LexerToken("",      LexerTokenTypes.EOL,        4),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a**-b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^",     LexerTokenTypes.CARET,      1),
            LexerToken("-",     LexerTokenTypes.DASH,       2),
            LexerToken("-",     LexerTokenTypes.DASH,       3),
            LexerToken("-",     LexerTokenTypes.DASH,       4),
            LexerToken("b",     LexerTokenTypes.IDENTIFIER, 5),
            LexerToken("",      LexerTokenTypes.EOL,        6),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a**---b"))]

        assert list(CommandParser.parseCommand((
            LexerToken("-", LexerTokenTypes.DASH,       0),
            LexerToken("2", LexerTokenTypes.INTEGER,    1),
            LexerToken("^", LexerTokenTypes.CARET,      2),
            LexerToken("-", LexerTokenTypes.DASH,       3),
            LexerToken("3", LexerTokenTypes.INTEGER,    4),
            LexerToken("^", LexerTokenTypes.CARET,      5),
            LexerToken("-", LexerTokenTypes.DASH,       6),
            LexerToken("2", LexerTokenTypes.INTEGER,    7),
            LexerToken("",  LexerTokenTypes.EOL,        8),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("-2**-3**-2"))]
        
        assert list(CommandParser.parseCommand((
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("-", LexerTokenTypes.DASH,       2),
            LexerToken("+", LexerTokenTypes.PLUS,       4),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 6),
            LexerToken("",  LexerTokenTypes.EOL,        7),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("a-+b"))]
        
        assert list(CommandParser.parseCommand((
            LexerToken("(",             LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("expression",    LexerTokenTypes.IDENTIFIER,     1),
            LexerToken(")",             LexerTokenTypes.PAREN_CLOSE,    11),
            LexerToken("",              LexerTokenTypes.EOL,            12),
        ), dict(), dict())) == [Command.evaluateExpression(sympy.parse_expr("(expression)"))]

        # sympy.parse_expr("as") throws an error! (as well as other python keywords)
        # make sure parser guards against this
        assert list(CommandParser.parseCommand((
            LexerToken("as",    LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        2),
        ), dict(), dict())) == [Command.evaluateExpression(createSymbol("as"))], \
            "Parser did not correctly evaluate symbol 'as'"
        assert list(CommandParser.parseCommand((
            LexerToken("if",    LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        2),
        ), dict(), dict())) == [Command.evaluateExpression(createSymbol("if"))], \
            "Parser did not correctly evaluate symbol 'if'"
        assert list(CommandParser.parseCommand((
            LexerToken("while", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("",      LexerTokenTypes.EOL,        5),
        ), dict(), dict())) == [Command.evaluateExpression(createSymbol("while"))], \
            "Parser did not correctly evaluate symbol 'while'"

    def testAliasResolutionForRobustness(self):
        aliases = {
            "plus": AliasTemplate(
                "plus",
                ("a", "b"),
                (
                    LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                    LexerToken("+", LexerTokenTypes.IDENTIFIER, 2),
                    LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                )
            ),
        }

        builtinAliases = {
            "sqrt": BuiltinAlias("sqrt", 1, lambda x: sympy.sqrt(x)),
        }

        assert list(CommandParser.parseCommand(tuple(CommandLexer.findTokens(CommandParser.preprocessAliases((
            LexerToken("plus",          LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",             LexerTokenTypes.PAREN_OPEN,     4),
            LexerToken("something",     LexerTokenTypes.IDENTIFIER,     5),
            LexerToken(",",             LexerTokenTypes.COMMA,          14),
            LexerToken("plus",          LexerTokenTypes.IDENTIFIER,     16),
            LexerToken("(",             LexerTokenTypes.PAREN_OPEN,     20),
            LexerToken("1",             LexerTokenTypes.INTEGER,        21),
            LexerToken(",",             LexerTokenTypes.COMMA,          22),
            LexerToken("aThing",        LexerTokenTypes.IDENTIFIER,     24),
            LexerToken(")",             LexerTokenTypes.PAREN_CLOSE,    30),
            LexerToken(")",             LexerTokenTypes.PAREN_CLOSE,    31),
            LexerToken("",              LexerTokenTypes.EOL,            32),
        ), aliases))), dict(), builtinAliases)) == [Command.evaluateExpression(sympy.parse_expr("something + 1 + aThing"))], \
            "Parser failed to correctly process one nested alias template"

        assert list(CommandParser.parseCommand(tuple(CommandLexer.findTokens(CommandParser.preprocessAliases((
            LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     4),
            LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     5),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     9),
            LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     10),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     14),
            LexerToken("1",         LexerTokenTypes.INTEGER,        15),
            LexerToken(",",         LexerTokenTypes.COMMA,          16),
            LexerToken("1",         LexerTokenTypes.INTEGER,        18),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    19),
            LexerToken(",",         LexerTokenTypes.COMMA,          20),
            LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     22),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     26),
            LexerToken("1",         LexerTokenTypes.INTEGER,        27),
            LexerToken(",",         LexerTokenTypes.COMMA,          28),
            LexerToken("1",         LexerTokenTypes.INTEGER,        30),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    31),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    32),
            LexerToken(",",         LexerTokenTypes.COMMA,          33),
            LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     35),
            LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     39),
            LexerToken("1",         LexerTokenTypes.INTEGER,        40),
            LexerToken(",",         LexerTokenTypes.COMMA,          41),
            LexerToken("aThing",    LexerTokenTypes.IDENTIFIER,     43),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    49),
            LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    50),
            LexerToken("",          LexerTokenTypes.EOL,            51),
        ), aliases))), dict(), builtinAliases)) == [Command.evaluateExpression(sympy.parse_expr("1 + 1 + 1 + 1 + 1 + aThing"))], \
            "Parser failed to correctly process multiple nested alias templates"
        
        assert list(CommandParser.parseCommand(tuple(CommandLexer.findTokens(CommandParser.preprocessAliases((
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     4),
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     5),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     9),
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     10),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     14),
            LexerToken("64",    LexerTokenTypes.INTEGER,        15),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    17),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    18),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    19),
            LexerToken("",      LexerTokenTypes.EOL,            20),
        ), aliases))), dict(), builtinAliases)) == [Command.evaluateExpression(sympy.parse_expr("sqrt(sqrt(sqrt(64)))"))], \
            "Parser failed to correctly process multiple nested builtin aliases"
        
        assert list(CommandParser.parseCommand(tuple(CommandLexer.findTokens(CommandParser.preprocessAliases((
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     4),
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     5),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     9),
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     10),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     14),
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     15),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     19),
            LexerToken("4",     LexerTokenTypes.INTEGER,        20),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    21),
            LexerToken(",",     LexerTokenTypes.COMMA,          22),
            LexerToken("2",     LexerTokenTypes.INTEGER,        24),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    25),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    26),
            LexerToken(",",     LexerTokenTypes.COMMA,          27),
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     29),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     33),
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     34),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     38),
            LexerToken("1",     LexerTokenTypes.INTEGER,        39),
            LexerToken(",",     LexerTokenTypes.COMMA,          40),
            LexerToken("1",     LexerTokenTypes.INTEGER,        42),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    43),
            LexerToken(",",     LexerTokenTypes.COMMA,          44),
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     46),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     50),
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     51),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     55),
            LexerToken("sqrt",  LexerTokenTypes.IDENTIFIER,     56),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     60),
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     61),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     65),
            LexerToken("2",     LexerTokenTypes.INTEGER,        66),
            LexerToken(",",     LexerTokenTypes.COMMA,          67),
            LexerToken("2",     LexerTokenTypes.INTEGER,        69),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    70),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    71),
            LexerToken(",",     LexerTokenTypes.COMMA,          72),
            LexerToken("2",     LexerTokenTypes.INTEGER,        74),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    75),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    76),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    77),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    78),
            LexerToken("",      LexerTokenTypes.EOL,            79),
        ), aliases))), dict(), builtinAliases)) == [Command.evaluateExpression(sympy.parse_expr("sqrt(sqrt(4) + 2) + 1 + 1 + sqrt(sqrt(2 + 2) + 2)"))], \
            "Parser failed to correctly process multiple nested aliases of various types"
        
        assert list(CommandParser.parseCommand(tuple(CommandLexer.findTokens(CommandParser.preprocessAliases((
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     4),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     5),
            LexerToken("2",     LexerTokenTypes.INTEGER,        6),
            LexerToken("-",     LexerTokenTypes.DASH,           7),
            LexerToken("1",     LexerTokenTypes.INTEGER,        8),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    9),
            LexerToken(",",     LexerTokenTypes.COMMA,          10),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     12),
            LexerToken("4",     LexerTokenTypes.INTEGER,        13),
            LexerToken("-",     LexerTokenTypes.DASH,           14),
            LexerToken("2",     LexerTokenTypes.INTEGER,        15),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    16),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    17),
            LexerToken("",      LexerTokenTypes.EOL,            18),
        ), aliases))), dict(), builtinAliases)) == [Command.evaluateExpression(sympy.parse_expr("(2-1) + (4-2)"))]
        
        assert list(CommandParser.parseCommand(tuple(CommandLexer.findTokens(CommandParser.preprocessAliases((
            LexerToken("plus",  LexerTokenTypes.IDENTIFIER,     0),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     4),
            LexerToken("`",     LexerTokenTypes.BACKTICK,       5),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     6),
            LexerToken("{",     LexerTokenTypes.BRACE_OPEN,     7),
            LexerToken("1",     LexerTokenTypes.INTEGER,        8),
            LexerToken(",",     LexerTokenTypes.COMMA,          9),
            LexerToken("2",     LexerTokenTypes.INTEGER,        10),
            LexerToken(",",     LexerTokenTypes.COMMA,          11),
            LexerToken("3",     LexerTokenTypes.INTEGER,        12),
            LexerToken("}",     LexerTokenTypes.BRACE_CLOSE,    13),
            LexerToken("`",     LexerTokenTypes.BACKTICK,       14),
            LexerToken(",",     LexerTokenTypes.COMMA,          15),
            LexerToken("1",     LexerTokenTypes.INTEGER,        17),
            LexerToken("`",     LexerTokenTypes.BACKTICK,       18),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    19),
            LexerToken("`",     LexerTokenTypes.BACKTICK,       20),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    21),
            LexerToken("",      LexerTokenTypes.EOL,            22),
        ), aliases))), dict(), builtinAliases)) == [Command.evaluateExpression(createSymbol("{1, 2, 3}") + 1)]

    def testCommandProcessing(self):
        assert list(CommandParser.parseCommand((
            LexerToken("simplify",  LexerTokenTypes.IDENTIFIER, 0),
            LexerToken(":",         LexerTokenTypes.COLON,      8),
            LexerToken("x",         LexerTokenTypes.IDENTIFIER, 9),
            LexerToken("",          LexerTokenTypes.EOL,        10),
        ), dict(), dict())) == [Command.simplifyExpression(sympy.parse_expr("x"))]
        
    def testEolExceptionsMakeEolVisible(self):
        def attempt():
            return list(CommandParser.parseCommand((
                LexerToken("(", LexerTokenTypes.PAREN_OPEN, 0),
                LexerToken("",  LexerTokenTypes.EOL,        1),
            ), dict(), dict()))
        error = runForError(attempt)
        assert type(error) is EolException
        assert error.tokens == (
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN, 0),
            LexerToken(" ...",  LexerTokenTypes.EOL,        1),
        )

    def testErrorCases(self):
        def attempt1():
            return list(CommandParser.parseCommand((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("=", LexerTokenTypes.EQUALS,     2),
                LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                LexerToken("=", LexerTokenTypes.EQUALS,     6),
                LexerToken("c", LexerTokenTypes.IDENTIFIER, 8),
                LexerToken("",  LexerTokenTypes.EOL,        9),
            ), dict(), dict()))
        error1 = runForError(attempt1)
        assert error1 is None

        def attempt2():
            return list(CommandParser.parseCommand((
                LexerToken("4.",    LexerTokenTypes.FLOAT,  0),
                LexerToken(".5",    LexerTokenTypes.FLOAT,  2),
                LexerToken("",      LexerTokenTypes.EOL,    4),
            ), dict(), dict()))
        error2 = runForError(attempt2)
        assert type(error2) is ParseException
        assert error2.tokens == (
            LexerToken("4.",    LexerTokenTypes.FLOAT,  0),
            LexerToken(".5",    LexerTokenTypes.FLOAT,  2),
            LexerToken("",      LexerTokenTypes.EOL,    4),
        )
        assert error2.badTokenIdxs == [1]

        def attempt3():
            return list(CommandParser.parseCommand((
                LexerToken("this",      LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("is",        LexerTokenTypes.IDENTIFIER, 5),
                LexerToken("invalid",   LexerTokenTypes.IDENTIFIER, 8),
                LexerToken("",          LexerTokenTypes.EOL,        15),
            ), dict(), dict()))
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
            return list(CommandParser.parseCommand((
                LexerToken("=", LexerTokenTypes.EQUALS,     0),
                LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
                LexerToken("",  LexerTokenTypes.EOL,        3),
            ), dict(), dict()))
        error4 = runForError(attempt4)
        assert type(error4) is ParseException
        assert error4.tokens == (
            LexerToken("=", LexerTokenTypes.EQUALS,     0),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2),
            LexerToken("",  LexerTokenTypes.EOL,        3),
        )
        assert error4.badTokenIdxs == [0]

        def attempt5():
            return list(CommandParser.parseCommand((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("=", LexerTokenTypes.EQUALS,     2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            ), dict(), dict()))
        error5 = runForError(attempt5)
        assert type(error5) is EolException
        assert error5.tokens == (
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("=",     LexerTokenTypes.EQUALS,     2),
            LexerToken(" ...",  LexerTokenTypes.EOL,        4),
        )
        assert error5.badTokenIdxs == [2]

        def attempt6():
            return list(CommandParser.parseCommand((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("+", LexerTokenTypes.PLUS,       2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            ), dict(), dict()))
        error6 = runForError(attempt6)
        assert type(error6) is EolException
        assert error6.tokens == (
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("+",     LexerTokenTypes.PLUS,       2),
            LexerToken(" ...",  LexerTokenTypes.EOL,        4),
        )
        assert error6.badTokenIdxs == [2]

        def attempt7():
            return list(CommandParser.parseCommand((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("/", LexerTokenTypes.SLASH,      2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            ), dict(), dict()))
        error7 = runForError(attempt7)
        assert type(error7) is EolException
        assert error7.tokens == (
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("/",     LexerTokenTypes.SLASH,      2),
            LexerToken(" ...",  LexerTokenTypes.EOL,        4),
        )
        assert error7.badTokenIdxs == [2]

        def attempt8():
            return list(CommandParser.parseCommand((
                LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                LexerToken("^", LexerTokenTypes.CARET,      2),
                LexerToken("",  LexerTokenTypes.EOL,        4),
            ), dict(), dict()))
        error8 = runForError(attempt8)
        assert type(error8) is EolException
        assert error8.tokens == (
            LexerToken("a",     LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("^",     LexerTokenTypes.CARET,      2),
            LexerToken(" ...",  LexerTokenTypes.EOL,        4),
        )
        assert error8.badTokenIdxs == [2]

        def attempt9():
            return list(CommandParser.parseCommand((
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
                LexerToken("a", LexerTokenTypes.IDENTIFIER,     1),
                LexerToken("+", LexerTokenTypes.PLUS,           3),
                LexerToken("b", LexerTokenTypes.IDENTIFIER,     5),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    6),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
                LexerToken("",  LexerTokenTypes.EOL,            8),
            ), dict(), dict()))
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
            return list(CommandParser.parseCommand((
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     0),
                LexerToken("(", LexerTokenTypes.PAREN_OPEN,     1),
                LexerToken("a", LexerTokenTypes.IDENTIFIER,     2),
                LexerToken("+", LexerTokenTypes.PLUS,           4),
                LexerToken("b", LexerTokenTypes.IDENTIFIER,     6),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    7),
                LexerToken("",  LexerTokenTypes.EOL,            8),
            ), dict(), dict()))
        error10 = runForError(attempt10)
        assert type(error10) is EolException
        assert error10.tokens == (
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     0),
            LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     1),
            LexerToken("a",     LexerTokenTypes.IDENTIFIER,     2),
            LexerToken("+",     LexerTokenTypes.PLUS,           4),
            LexerToken("b",     LexerTokenTypes.IDENTIFIER,     6),
            LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    7),
            LexerToken(" ...",  LexerTokenTypes.EOL,            8),
        )
        assert error10.badTokenIdxs == [6]

        def attempt11():
            return list(CommandParser.parseCommand((
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
                LexerToken("z", LexerTokenTypes.IDENTIFIER,     22),
                LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    23),
                LexerToken("/", LexerTokenTypes.SLASH,          25),
                LexerToken("d", LexerTokenTypes.IDENTIFIER,     27),
                LexerToken("",  LexerTokenTypes.EOL,            28),
            ), dict(), dict()))
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
            LexerToken("z", LexerTokenTypes.IDENTIFIER,     22),
            LexerToken(")", LexerTokenTypes.PAREN_CLOSE,    23),
            LexerToken("/", LexerTokenTypes.SLASH,          25),
            LexerToken("d", LexerTokenTypes.IDENTIFIER,     27),
            LexerToken("",  LexerTokenTypes.EOL,            28),
        )
        assert error11.badTokenIdxs == [14]

        # sympy parses this and just returns "1";
        # this test makes sure the app's parser does its actual job
        def attempt_pythonLikeExpr():
            return list(CommandParser.parseCommand((
                LexerToken("1",     LexerTokenTypes.INTEGER,    0),
                LexerToken("if",    LexerTokenTypes.IDENTIFIER, 2),
                LexerToken("1",     LexerTokenTypes.INTEGER,    5),
                LexerToken("else",  LexerTokenTypes.IDENTIFIER, 7),
                LexerToken("0",     LexerTokenTypes.INTEGER,    12),
                LexerToken("",      LexerTokenTypes.EOL,        13),
            ), dict(), dict()))
        error_pythonLikeExpr = runForError(attempt_pythonLikeExpr)
        assert type(error_pythonLikeExpr) is ParseException
        assert error_pythonLikeExpr.badTokenIdxs == [1]

        def attempt_emptyExpressionList():
            return list(CommandParser.parseCommand((
                LexerToken("{", LexerTokenTypes.BRACE_OPEN,     0),
                LexerToken("}", LexerTokenTypes.BRACE_CLOSE,    1),
                LexerToken("",  LexerTokenTypes.EOL,            2),
            ), dict(), dict()))
        error_emptyExpressionList = runForError(attempt_emptyExpressionList)
        assert type(error_emptyExpressionList) is ParseException
        assert error_emptyExpressionList.badTokenIdxs == [1]

        def attempt12():
            return list(CommandParser.parseCommand((
                LexerToken("{",     LexerTokenTypes.BRACE_OPEN,     0),
                LexerToken("a",     LexerTokenTypes.IDENTIFIER,     1),
                LexerToken("+",     LexerTokenTypes.PLUS,           2),
                LexerToken("r",     LexerTokenTypes.IDENTIFIER,     3),
                LexerToken("*",     LexerTokenTypes.STAR,           4),
                LexerToken("b",     LexerTokenTypes.IDENTIFIER,     5),
                LexerToken(",",     LexerTokenTypes.COMMA,          6),
                LexerToken("(",     LexerTokenTypes.PAREN_OPEN,     8),
                LexerToken("a",     LexerTokenTypes.IDENTIFIER,     9),
                LexerToken("+",     LexerTokenTypes.PLUS,           10),
                LexerToken("b",     LexerTokenTypes.IDENTIFIER,     11),
                LexerToken(")",     LexerTokenTypes.PAREN_CLOSE,    12),
                LexerToken("/",     LexerTokenTypes.SLASH,          13),
                LexerToken("d",     LexerTokenTypes.IDENTIFIER,     14),
                LexerToken(",",     LexerTokenTypes.COMMA,          15),
                LexerToken("14",    LexerTokenTypes.INTEGER,        17),
                LexerToken("-",     LexerTokenTypes.DASH,           19),
                LexerToken("12",    LexerTokenTypes.INTEGER,        20),
                LexerToken("*",     LexerTokenTypes.STAR,           22),
                LexerToken("a",     LexerTokenTypes.IDENTIFIER,     23),
                LexerToken("}",     LexerTokenTypes.BRACE_CLOSE,    24),
                LexerToken("",      LexerTokenTypes.EOL,            25),
            ), dict(), dict()))
        error12 = runForError(attempt12)
        assert type(error12) is ParseException
        assert error12.badTokenIdxs == [1]

        def attempt13():
            return list(CommandParser.parseCommand((
                LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
                LexerToken("+",         LexerTokenTypes.PLUS,           10),
                LexerToken("undefined", LexerTokenTypes.IDENTIFIER,     12),
                LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     21),
                LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    22),
                LexerToken("",          LexerTokenTypes.EOL,            23),
            ), dict(), dict()))
        error13 = runForError(attempt13)
        assert type(error13) is UnknownAliasException
        assert error13.badTokenIdxs == [2]

        def attempt14():
            builtinAliases = {
                "sqrt": BuiltinAlias("sqrt", 1, lambda x: sympy.sqrt(x)),
            }
            return list(CommandParser.parseCommand((
                LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
                LexerToken("+",         LexerTokenTypes.PLUS,           10),
                LexerToken("sqrt",      LexerTokenTypes.IDENTIFIER,     12),
                LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     16),
                LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    17),
                LexerToken("",          LexerTokenTypes.EOL,            18),
            ), dict(), builtinAliases))
        error14 = runForError(attempt14)
        assert type(error14) is AliasArgumentCountException
        assert error14.badTokenIdxs == [4]

        def attempt15():
            aliases = {
                "plus": AliasTemplate(
                    "plus",
                    ("a", "b"),
                    (
                        LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                        LexerToken("+", LexerTokenTypes.IDENTIFIER, 2),
                        LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                    )
                ),
            }
            return list(CommandParser.preprocessAliases((
                LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
                LexerToken("+",         LexerTokenTypes.PLUS,           10),
                LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     12),
                LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     16),
                LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    17),
                LexerToken("",          LexerTokenTypes.EOL,            18),
            ), aliases))
        error15 = runForError(attempt15)
        assert type(error15) is AliasArgumentCountException
        assert error15.badTokenIdxs == [4]

        def attempt16():
            aliases = {
                "plus": AliasTemplate(
                    "plus",
                    ("a", "b"),
                    (
                        LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                        LexerToken("+", LexerTokenTypes.IDENTIFIER, 2),
                        LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                    )
                ),
            }
            return list(CommandParser.preprocessAliases((
                LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
                LexerToken("+",         LexerTokenTypes.PLUS,           10),
                LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     12),
                LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     16),
                LexerToken("4",         LexerTokenTypes.INTEGER,        17),
                LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    18),
                LexerToken("",          LexerTokenTypes.EOL,            19),
            ), aliases))
        error16 = runForError(attempt16)
        assert type(error16) is AliasArgumentCountException
        assert error16.badTokenIdxs == [5]

        def attempt17():
            aliases = {
                "plus": AliasTemplate(
                    "plus",
                    ("a", "b"),
                    (
                        LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                        LexerToken("+", LexerTokenTypes.IDENTIFIER, 2),
                        LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                    )
                ),
            }
            return list(CommandParser.preprocessAliases((
                LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
                LexerToken("+",         LexerTokenTypes.PLUS,           10),
                LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     12),
                LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     16),
                LexerToken("2",         LexerTokenTypes.INTEGER,        17),
                LexerToken(",",         LexerTokenTypes.COMMA,          18),
                LexerToken("4",         LexerTokenTypes.INTEGER,        20),
                LexerToken(",",         LexerTokenTypes.COMMA,          21),
                LexerToken("6",         LexerTokenTypes.INTEGER,        23),
                LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    24),
                LexerToken("",          LexerTokenTypes.EOL,            25),
            ), aliases))
        error17 = runForError(attempt17)
        assert type(error17) is AliasArgumentCountException
        assert error17.badTokenIdxs == [7, 8]

        def attempt18():
            aliases = {
                "plus": AliasTemplate(
                    "plus",
                    ("a", "b"),
                    (
                        LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
                        LexerToken("+", LexerTokenTypes.IDENTIFIER, 2),
                        LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
                    )
                ),
            }
            return list(CommandParser.preprocessAliases((
                LexerToken("something", LexerTokenTypes.IDENTIFIER,     0),
                LexerToken("+",         LexerTokenTypes.PLUS,           10),
                LexerToken("plus",      LexerTokenTypes.IDENTIFIER,     12),
                LexerToken("(",         LexerTokenTypes.PAREN_OPEN,     16),
                LexerToken("2",         LexerTokenTypes.INTEGER,        17),
                LexerToken(",",         LexerTokenTypes.COMMA,          18),
                LexerToken("4",         LexerTokenTypes.INTEGER,        20),
                LexerToken(",",         LexerTokenTypes.COMMA,          21),
                LexerToken("6",         LexerTokenTypes.INTEGER,        23),
                LexerToken(",",         LexerTokenTypes.COMMA,          24),
                LexerToken("6",         LexerTokenTypes.INTEGER,        26),
                LexerToken(")",         LexerTokenTypes.PAREN_CLOSE,    27),
                LexerToken("",          LexerTokenTypes.EOL,            25),
            ), aliases))
        error18 = runForError(attempt18)
        assert type(error18) is AliasArgumentCountException
        assert error18.badTokenIdxs == [7, 8, 9, 10]

        def attempt19():
            return list(CommandParser.parseCommand((
                LexerToken("undefinedCmd",  LexerTokenTypes.IDENTIFIER,     0),
                LexerToken(":",             LexerTokenTypes.COLON,          11),
            ), dict(), dict()))
        error19 = runForError(attempt19)
        assert type(error19) is UnknownCommandException
        assert error19.badTokenIdxs == [0]

        # TODO: test defining an alias over a variable name
