import sympy

from src.parsing.parser import freeSymbolsOf
from src.algebrasolver.symbolsDatabase import SymbolsDatabase
from src.algebrasolver.relationSymbolTable import RelationSymbolTable
from src.algebrasolver.types import *


class InferenceOrderSolver:
    """
    In order for the solver to "solve for variables", it needs to know a list of
    ordered "instructions" to perform. Each "instruction" should contain a
    symbol to solve for and a relation containing that symbol to solve with.
    No symbol or relation should appear more than once in this list of
    instructions, and the instructions given should provide a concrete set
    of values for the last symbol when completed (which can then be used
    to substitute backwards for the rest of the variables).
    
    This task is what this class is meant to perform. It does so as a
    disposable, single-use object. Create it with some relations and known
    symbols, and it will attempt to find this list of valid instructions,
    without actually "solving" for any variable.

    This is all done based on the one-symbol-per-relation principle. That is,
    if you want to solve for N different symbols, you need N different
    relations that interrelate those symbols. If this is true, you can forward
    solve the relations and back substitute the symbols to generate concrete
    numeric values for each variable.

    For example, given the relations

    ```raw
    a + b = 6
    a = 2*b
    ```

    one could easily conclude that values for both `a` and `b` can be found,
    without the need for actually solving for either of them. On the contrary,

    ```raw
    c * d = 12
    ```

    and

    ```raw
    4*x*y = z - 1
    z - x = 22
    ```

    do not provide enough information to find numeric values for their
    variables, which (again) can be inferred without solving for any variables.

    (For those who just *must know*: `c = 3`, `d = 4`, `x = 3`, `y = 2`, and
    `z = 25`.)
    """
    
    def __init__(self, relations: list[Relation], knownSymbols: SymbolsDatabase):
        self._relations = relations
        self._knownSymbols = knownSymbols
        self._potentialInferencesTable = RelationSymbolTable()

    def findSolveOrder(self):
        """
        This is the main algorithm for this "solver". Simply put, it iterates
        through each relation it is given, pairs it with "the right symbol",
        and, if "the right symbol" was the last unknown one in the
        relation *and* the current list of symbol-relation pairs forms a
        "solid inference family", it returns the symbol-relation pairs in that
        "inference family".

        Now, first let's describe what it means to pair with "the right symbol".
        A symbol is determined to be "the right one" if it
            - hasn't been paired with previous relations
            - is present in the current relation being iterated
            - is the least likely to appear in future relations
            - doesn't cause a future relation to "become obsolete" (aka "trapping"
              the variable -- more on that in a little bit)
        
        To detect which variable in a relation is "least likely to appear in
        future relations", a simple calculation is made beforehand that counts
        each symbol in each relation. When it comes time to select a symbol from
        a relation, the symbol with the lowest count (that also hasn't been
        paired yet) is used.
              
        However, this does assume that the variable won't cause a future
        relation to "become obsolete". Because symbols won't be selected if they
        are already paired with some previous relation, the entire list of
        relations must be sorted according to the number of unknown variables
        they have. This is assumed about the list of relations given in the
        first place. This assumption is made to prevent "trapping" variables
        from being known from relations that are more descriptive about them.
        If the symbols and relations

        ```raw
        c (lowest count)  --  a + b + c + d = 123
        a (lowest count)  --  a + b + d = 234
        b (lowest count)  --  a + b - d = 432
        ? c already used! --  c = 8
        ```

        were checked in the order they are listed in, `c` would be "trapped"
        as it wouldn't be paired with the relation that contains more accurate
        information on what `c` actually is. If instead the relations were
        sorted by the number of unknown variables they contain

        ```raw
        c (lowest count) --  c = 8
        a (lowest count) --  a + b + d = 234
        b (lowest count) --  a + b - d = 432
        d (lowest count) --  a + b + c + d = 123
        ```

        the issue disappears completely. Making the assumption that the
        relations are sorted is crucial for this algorithm to work correctly
        (and is objectively better than not making the assumption and iterating
        through the relations again every time a "trapped variable" is
        detected).

        Lastly, this algorithm depends on detecting a "solid inference family".
        This process is described fully in the documentation for
        `_testSolidInferenceFamily()` (in terms of musical chairs, which is
        fun). But in short, an "inference family" is a collection of all
        relations that share any of their variables with each other (just one
        relation in the family needs to share just one symbol with a second
        relation for the second relation to be a part of the family). A "solid"
        inference family is one that has the same number of relations as there
        are symbols that describe them (aka it could follow the
        one-symbol-per-relation principle for back substitution), "solid"
        referring to the family not having any "holes", where a "hole" is any
        extra symbol that cannot possibly be inferred by back substitution
        (because there aren't enough relations to satisfy the
        one-symbol-per-relation principle).
        """
        
        symbolCounts = self._countSymbols()
        # relations must be sorted to prevent "trapping" a variable from being known:
        # a + b + c + d = 123
        # a + b + d = 234
        # a + b - d = 432
        # c = 8
        # in the above, `c` is chosen for the first relation (since it has the
        # lowest count), however this "traps" it since it won't be chosen for the
        # last relation, which actually provides its value
        assert self._testRelationsSorted(), "Relations for inference solver must be sorted!"
        for relation in self._relations:
            unknownSymbolsInRelation: list[tuple[sympy.Symbol, int]] = [
                (symbol, symbolCounts[symbol])
                for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False)
                if symbol not in self._knownSymbols and symbol not in self._potentialInferencesTable
            ]

            (symbolToSolve, symbolCount) = min(
                unknownSymbolsInRelation,
                key = lambda symbolAndCount: symbolAndCount[1],
                default = (None, None)
            )
            if symbolToSolve is not None:
                self._potentialInferencesTable[symbolToSolve] = relation

                # optimization: inference family cannot be solid unless this relation
                # has potential inferences for all of its symbols
                wasLastUnknownSymbol = len(unknownSymbolsInRelation) == 1
                if wasLastUnknownSymbol:
                    (canBackSubstitute, symbolsInFamily) = self._testSolidInferenceFamily(relation)
                    if canBackSubstitute:
                        return sorted(
                            [
                                (symbolToInfer, relationToInferFrom)
                                for symbolToInfer in symbolsInFamily
                                for relationToInferFrom in [self._potentialInferencesTable[symbolToInfer]]
                            ],
                            key = lambda data: len(freeSymbolsOf(data[1].asExprEqToZero, includeExpressionLists = False))
                        )
        return None
    
    def _testSolidInferenceFamily(self, baseRelation: Relation, relationsChecked: set[Relation] | None = None, symbolsInFamily: set[sympy.Symbol] | None = None):
        """
        This function has but one task: Is the inference family given by
        `baseRelation` "solid"?

        Asking this question is not quite trivial, however, and can loosely be
        equated to the problem of managing children playing musical chairs.
        Except the number of chairs is completely variable, the goal is actually
        to have the same number of chairs as there are children (in one game),
        each child is highly selective and will only sit on certain chairs,
        and you are managing multiple games of musical chairs that could or
        could not actually just be a part of the same game.

        The solution is to first turn the annoying music off -- it makes it hard
        to think. Then, simply assume all the chairs are filled. Starting with a
        given "current chair", check if there's a child in each chair, moving to
        the next chair after checking. If there ever is an empty chair, you know
        the chairs in that game aren't filled! Otherwise, after traversing all
        the chairs, you can decide they are all filled.

        This is pretty much the algorithm used below, which recursively checks
        if every unknown symbol (aka the chair) is paired with a relation
        (aka the child). If it finds an unpaired, unknown symbol, it returns
        `False`. Otherwise, after checking all the symbols (in just one family,
        not all the families), it can confidently return `True`. Notice that it
        is possible for other relations in `_relations` to be present that
        aren't a part of the same inference family is the given `baseRelation`.
        This is why multiple inference families (aka the games) must somehow be
        tracked at the same time.
        """

        if relationsChecked is None:
            relationsChecked = {baseRelation}
        if symbolsInFamily is None:
            symbolsInFamily = set()

        # TODO: (optimization?) not every symbol needs to be checked;
        #       just count symbols/relations to check pairity
        #       (could also build and keep track of inference families and then
        #       return a list of "instructions" instead of just one)
        for symbol in freeSymbolsOf(baseRelation.asExprEqToZero, includeExpressionLists = False):
            symbolIsPaired = symbol in self._potentialInferencesTable
            symbolNotKnown = symbol not in self._knownSymbols
            if symbolIsPaired:
                symbolsInFamily.add(symbol)
                relation = self._potentialInferencesTable[symbol]
                if relation not in relationsChecked:
                    relationsChecked.add(relation)
                    (isSolid, symbolsInFamily_extraRef) = self._testSolidInferenceFamily(relation, relationsChecked, symbolsInFamily)
                    holeExists = not isSolid
                    if holeExists:
                        return (False, symbolsInFamily)
            elif symbolNotKnown:
                return (False, symbolsInFamily)
        return (True, symbolsInFamily)

    def _countSymbols(self):
        """
        Generates a dictionary that indicates the number of relations a given
        symbol is in.
        """
        
        unknownSymbolCounts: dict[sympy.Symbol, int] = dict()
        for relation in self._relations:
            for symbol in freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False):
                if symbol in unknownSymbolCounts:
                    unknownSymbolCounts[symbol] += 1
                elif symbol not in self._knownSymbols:
                    unknownSymbolCounts[symbol] = 1
        return unknownSymbolCounts
    
    def _testRelationsSorted(self):
        lastNumUnknowns = -1
        for relation in self._relations:
            numUnknowns = len(freeSymbolsOf(relation.asExprEqToZero, includeExpressionLists = False))
            if numUnknowns < lastNumUnknowns:
                return False
            lastNumUnknowns = numUnknowns
        return True


