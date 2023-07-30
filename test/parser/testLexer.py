from src.parser.lexer import CommandLexer, LexerToken, LexerTokenTypes


class CommandLexerTester:
    def testTokensCanEqualEachOther(self):
        token1 = LexerToken("match", LexerTokenTypes.IDENTIFIER, 0)
        token2 = LexerToken("match", LexerTokenTypes.IDENTIFIER, 0)
        assert token1 == token2, \
            "LexerTokens with same data didn't equal each other"

        token3 = LexerToken("match1", LexerTokenTypes.IDENTIFIER, 0)
        token4 = LexerToken("match2", LexerTokenTypes.IDENTIFIER, 0)
        assert token3 != token4, \
            "LexerTokens with different matches were equal"

        token5 = LexerToken("match", LexerTokenTypes.INT, 0)
        token6 = LexerToken("match", LexerTokenTypes.FLOAT, 0)
        assert token5 != token6, \
            "LexerTokens with different types were equal"

        token7 = LexerToken("match", LexerTokenTypes.IDENTIFIER, 2)
        token8 = LexerToken("match", LexerTokenTypes.IDENTIFIER, 5)
        assert token7 != token8, \
            "LexerTokens with different match idxs were equal"

    def testLexerProvidesEOL(self):
        lexer = CommandLexer()
        
        assert list(lexer.findTokens("")) == [LexerToken("", LexerTokenTypes.EOL, 0)], \
            "Lexer does not end strings with EOL"
        assert list(lexer.findTokens("", withEOL = False)) == [], \
            "Lexer ended string with EOL when told not to"
    
    def testLexerDetectionForEachToken(self):
        lexer = CommandLexer()
        
        # IDENTIFIER
        assert list(lexer.findTokens("myIdentifier", withEOL = False)) == [
            LexerToken(
                "myIdentifier",
                LexerTokenTypes.IDENTIFIER,
                0
            )
        ], "Lexer did not find a basic IDENTIFIER"
        assert list(lexer.findTokens("myVariable123", withEOL = False)) == [
            LexerToken(
                "myVariable123",
                LexerTokenTypes.IDENTIFIER,
                0
            )
        ], "Lexer did not find an IDENTIFIER with trailing numbers"
        assert list(lexer.findTokens("_my_special_123_variable_456_", withEOL = False)) == [
            LexerToken(
                "_my_special_123_variable_456_",
                LexerTokenTypes.IDENTIFIER, 
                0
            )
        ], "Lexer did not find an IDENTIFIER with underscores"
        
        # INT
        assert list(lexer.findTokens("4", withEOL = False)) == [
            LexerToken(
                "4",
                LexerTokenTypes.INT,
                0
            )
        ], "Lexer did not find a single digit INT"
        assert list(lexer.findTokens("1234567890019293301823081092309", withEOL = False)) == [
            LexerToken(
                "1234567890019293301823081092309",
                LexerTokenTypes.INT,
                0
            )
        ], "Lexer did not find a long INT"
        assert list(lexer.findTokens("1_23456789_00192_9330_182308_1092309", withEOL = False)) == [
            LexerToken(
                "1_23456789_00192_9330_182308_1092309",
                LexerTokenTypes.INT,
                0
            )
        ], "Lexer did not find a long INT with underscores"
        
        # FLOAT
        assert list(lexer.findTokens("4.0", withEOL = False)) == [
            LexerToken(
                "4.0",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a basic FLOAT"
        assert list(lexer.findTokens("1239128394871.12381283123", withEOL = False)) == [
            LexerToken(
                "1239128394871.12381283123",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a large FLOAT"
        assert list(lexer.findTokens("2.", withEOL = False)) == [
            LexerToken(
                "2.",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a FLOAT ending with a decimal"
        assert list(lexer.findTokens(".5", withEOL = False)) == [
            LexerToken(
                ".5",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a FLOAT starting with a decimal"
        assert list(lexer.findTokens("123.456e12", withEOL = False)) == [
            LexerToken(
                "123.456e12",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a FLOAT using scientific notation (lower e)"
        assert list(lexer.findTokens("33.3E3", withEOL = False)) == [
            LexerToken(
                "33.3E3",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a FLOAT using scientific notation (upper E)"
        assert list(lexer.findTokens("123.456e+123", withEOL = False)) == [
            LexerToken(
                "123.456e+123",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a FLOAT using scientific notation (lower e with plus)"
        assert list(lexer.findTokens("654.321E-123", withEOL = False)) == [
            LexerToken(
                "654.321E-123",
                LexerTokenTypes.FLOAT,
                0
            )
        ], "Lexer did not find a FLOAT using scientific notation (upper E with minus)"
        
        # PAREN_OPEN/PAREN_CLOSE
        assert list(lexer.findTokens("(", withEOL = False)) == [
            LexerToken(
                "(",
                LexerTokenTypes.PAREN_OPEN,
                0
            )
        ], "Lexer did not find a PAREN_OPEN"
        assert list(lexer.findTokens(")", withEOL = False)) == [
            LexerToken(
                ")",
                LexerTokenTypes.PAREN_CLOSE,
                0
            )
        ], "Lexer did not find a PAREN_CLOSE"
        
        # EQUALS/PLUS/MINUS/STAR/DASH/CARROT
        assert list(lexer.findTokens("=", withEOL = False)) == [
            LexerToken(
                "=",
                LexerTokenTypes.EQUALS,
                0
            )
        ], "Lexer did not find an EQUALS"
        assert list(lexer.findTokens("+", withEOL = False)) == [
            LexerToken(
                "+",
                LexerTokenTypes.PLUS,
                0
            )
        ], "Lexer did not find a PLUS"
        assert list(lexer.findTokens("-", withEOL = False)) == [
            LexerToken(
                "-",
                LexerTokenTypes.DASH,
                0
            )
        ], "Lexer did not find a DASH"
        assert list(lexer.findTokens("*", withEOL = False)) == [
            LexerToken(
                "*",
                LexerTokenTypes.STAR,
                0
            )
        ], "Lexer did not find a STAR"
        assert list(lexer.findTokens("/", withEOL = False)) == [
            LexerToken(
                "/",
                LexerTokenTypes.SLASH,
                0
            )
        ], "Lexer did not find a SLASH"
        assert list(lexer.findTokens("^", withEOL = False)) == [
            LexerToken(
                "^",
                LexerTokenTypes.CARROT,
                0
            )
        ], "Lexer did not find a CARROT"
        
        # INVALID
        assert list(lexer.findTokens("‡", withEOL = False)) == [
            LexerToken(
                "‡",
                LexerTokenTypes.INVALID,
                0
            )
        ], "Lexer did not correctly detect an INVALID token"

    def testLexerHandlesWhitespace(self):
        lexer = CommandLexer()

        # skipped whitespace
        assert list(lexer.findTokens(" ", withEOL = False)) == [], \
            "Lexer found tokens in a single space"
        assert list(lexer.findTokens("\t", withEOL = False)) == [], \
            "Lexer found tokens in a single tab"
        assert list(lexer.findTokens("   \t\t  \t\t  \t", withEOL = False)) == [], \
            "Lexer found tokens in a combination of whitespace"
        
        # newlines/multi-EOLs
        assert list(lexer.findTokens("\n", withEOL = False)) == [], \
            "Lexer found tokens in a single newline"
        assert list(lexer.findTokens("\n", withEOL = True)) == [
            LexerToken("", LexerTokenTypes.EOL, 0),
            LexerToken("", LexerTokenTypes.EOL, 1)
        ], "Lexer did not correctly process EOLs with a single newline"
        assert list(lexer.findTokens("\n\n\n", withEOL = True)) == [
            LexerToken("", LexerTokenTypes.EOL, 0),
            LexerToken("", LexerTokenTypes.EOL, 1),
            LexerToken("", LexerTokenTypes.EOL, 2),
            LexerToken("", LexerTokenTypes.EOL, 3)
        ], "Lexer did not correctly process EOLs with multiple newlines"

    def testLexerDetectionForMultipleTokens(self):
        lexer = CommandLexer()

        assert list(lexer.findTokens("a b", withEOL = False)) == [
            LexerToken("a", LexerTokenTypes.IDENTIFIER, 0),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 2)
        ], "Lexer did not find correct tokens with two IDENTIFIERS"
        
        assert list(lexer.findTokens("2 + b-5e12*f", withEOL = False)) == [
            LexerToken("2", LexerTokenTypes.INT, 0),
            LexerToken("+", LexerTokenTypes.PLUS, 2),
            LexerToken("b", LexerTokenTypes.IDENTIFIER, 4),
            LexerToken("-", LexerTokenTypes.DASH, 5),
            LexerToken("5e12", LexerTokenTypes.FLOAT, 6),
            LexerToken("*", LexerTokenTypes.STAR, 10),
            LexerToken("f", LexerTokenTypes.IDENTIFIER, 11)
        ], "Lexer did not correctly process expression with various operators/numerics"
