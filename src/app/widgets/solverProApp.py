from threading import Timer

import sympy
from textual import on
from textual.events import Key
from textual.app import App
from textual.reactive import var
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import RichLog, Button, Label

from src.common.functions import first, getVersion
from src.app.appDriver import AppDriver, Command
from src.app.widgets.appHeader import AppHeader
from src.app.widgets.coloredInput import ColoredInput
from src.app.widgets.termTipModal import TermTipModal
from src.app.widgets.dictionaryScreen import DictionaryScreen
from src.app.widgets.historyScreen import HistoryScreen
from src.app.widgets.colors import Colors
from src.app.termTips import TermTips
from src.app.textRenderer import TextRenderer
from src.parsing.parser import AliasTemplate
from src.algebrasolver.solver import Relation


class MainScreen(Screen):
    DEFAULT_CSS = f"""
        MainScreen Input {{
            border: tall {Colors.borderPlain.hex};

        }}
        MainScreen Input:focus {{
            border: tall {Colors.borderFocus.hex};
        }}
        MainScreen Input .input--placeholder {{
            color: {Colors.textPlain.hex} 50%;
        }}
        MainScreen Input.highlighted .input--placeholder {{
            background: {Colors.fillBright.hex};
        }}

        MainScreen #rightSection {{
            min-width: 16;
            width: 20%;
            max-width: 32;
            height: 100%;
            padding: 0 5;
            align: center middle;
        }}

        MainScreen .managerButton {{
            width: 100%;
            height: 5;
        }}

        MainScreen #dictionaryButton {{
            background: {Colors.fillBlue.hex};
        }}

        MainScreen #historyButton {{
            background: {Colors.fillGreen.hex};
        }}

        MainScreen #tutorialButton {{
            background: {Colors.fillRed.hex};
        }}

        MainScreen .spacer {{
            width: 100%;
            height: 1fr;
        }}
    """

    inputTimer: var[Timer | None] = var(None)

    def compose(self):
        yield AppHeader()
        with Horizontal(id = 'sectionsContainer'):
            with Vertical(id = 'leftSection'):
                yield RichLog()
                yield MainInput(placeholder = " < Command >")
            with Vertical(id = 'rightSection'):
                yield Label(classes = 'spacer')
                yield Button("Dictionary", id = 'dictionaryButton', classes = 'managerButton')
                yield Label(classes = 'spacer')
                yield Button("History", id = 'historyButton', classes = 'managerButton')
                yield Label(classes = 'spacer')
                # TODO: tutorial screen(s)
                yield Button("Tutorial (WIP)", id = 'tutorialButton', classes = 'managerButton')
                yield Label(classes = 'spacer')

    def on_mount(self):
        self.app.title = f"--- Solver Pro {getVersion()} ---"

    @on(ColoredInput.Submitted)
    def runCommand(self, event: ColoredInput.Submitted):
        input = event.input
        commandStr = input.value.strip()
        input.value = ""
        input.add_class('highlighted')
        if self.inputTimer is not None:
            self.inputTimer.cancel()

        assert type(self.app) is SolverProApp
        driver = self.app.driver
        renderer = self.app.textRenderer
        try:
            # only single lines are accepted for now;
            # `renderer` (for exceptions) can't handle multiple lines yet,
            # and the driver does not behave transactionally (an error on the
            # third of four lines still actually executes the first two)
            driver.validateSingleLine(commandStr)
            result = first(tuple(driver.processCommandLines(commandStr)))
            if result.type is Command.EMPTY:
                self.writeSpacerToLogger()

            elif result.type is Command.RECORD_RELATIONS:
                relationsData: list[tuple[Relation, bool]] = result.data
                self.writeToLogger(
                    commandStr,
                    True,
                    renderer.formatRelationsRecorded(relationsData, highlightSyntax = True)
                )

            elif result.type is Command.EVALUATE_EXPRESSION:
                exprs: set[sympy.Expr] = result.data
                assert isinstance(exprs, set)
                self.writeToLogger(
                    commandStr,
                    True,
                    renderer.formatExpressions(exprs, highlightSyntax = True)
                )

            elif result.type is Command.RECORD_ALIAS:
                aliasTemplate = result.data
                assert type(aliasTemplate) is AliasTemplate
                self.writeToLogger(
                    commandStr,
                    True,
                    renderer.formatAliasTemplate(aliasTemplate, highlightSyntax = True)
                )

            else:
                raise NotImplementedError(f"Command result of type {result.type} not implemented")
        
        except Exception as error:
            self.writeToLogger(commandStr, False, renderer.formatException(error, withErrorHeader = True))
        
        self.inputTimer = Timer(0.1, lambda: input.remove_class('highlighted'))
        self.inputTimer.start()

    def writeToLogger(self, commandStr: str, commandSucceeded: bool, formattedStr: str, *, highlightSyntax: bool = True):
        assert type(self.app) is SolverProApp
        renderer = self.app.textRenderer

        richLog = self.query_one(RichLog)
        if commandStr != "":
            richLog.write(renderer.render(
                renderer.formatInputLog(
                    commandStr,
                    commandSucceeded,
                    highlightSyntax = highlightSyntax,
                ),
            ))
        richLog.write(renderer.render(formattedStr, indent = True))
        self.writeSpacerToLogger()

    def writeSpacerToLogger(self):
        richLog = self.query_one(RichLog)
        spaceForNextCommand = " "
        richLog.write(spaceForNextCommand)

    @on(Button.Pressed, '#dictionaryButton')
    def openDictionaryScreen(self):
        assert type(self.app) is SolverProApp
        self.app.push_screen(DictionaryScreen(self.app.termTips.getTermTips()))
    
    @on(Button.Pressed, '#historyButton')
    def openHistoryScreen(self):
        assert type(self.app) is SolverProApp
        relations_newestFirst = reversed(self.app.driver.getRelations())
        self.app.push_screen(HistoryScreen(relations_newestFirst))


class SolverProApp(App):
    DEFAULT_CSS = f"""
        SolverProApp * {{
            color: {Colors.textPlain.hex};
            link-hover-style: underline;
            link-hover-color: {Colors.textBlue.hex};
            link-hover-background: {Colors.fillBlue.hex} 70%;
        }}
        
        SolverProApp Button:hover {{
            opacity: 80%;
        }}
    """

    driver: var[AppDriver] = var(lambda: AppDriver())
    textRenderer: var[TextRenderer] = var(lambda: TextRenderer())
    termTips: var[TermTips] = var(lambda: TermTips())

    mainScreen: var[MainScreen] = var(lambda: MainScreen())

    def on_mount(self):
        self.textRenderer.useAliasProvider(self.driver)
        self.push_screen(self.mainScreen)

    # defined as an action for term tip links
    def action_showTermTip(self, term: str):
        tip = self.termTips.lookupTerm(term)
        self.push_screen(TermTipModal(
            tip.term,
            tuple(self.textRenderer.render(line) for line in tip.definitionLines),
        ))

    def replaceRelation(self, oldRelation: Relation, newRelationCommand: str):
        modifiedRelationStr = f"[{Colors.textMuted.hex}]<[/]replace {self.textRenderer.formatRelation(oldRelation, highlightSyntax = True)}[{Colors.textMuted.hex}]>[/]"
        try:
            result = self.driver.replaceRelation(oldRelation, newRelationCommand)
            (relation, isRedundant) = result.data[0]
            self.mainScreen.writeToLogger(
                modifiedRelationStr,
                True,
                self.textRenderer.formatRelationReplaced(oldRelation, relation, warnRedundant = isRedundant, highlightSyntax = True),
                highlightSyntax = False,
            )
            assert type(relation) is Relation
            return relation
        except Exception as exception:
            self.mainScreen.writeToLogger(
                modifiedRelationStr,
                False,
                self.textRenderer.formatException(exception, withErrorHeader = True),
                highlightSyntax = False,
            )
            return None

    def deleteRelation(self, relation: Relation):
        deletedRelationStr = f"[{Colors.textMuted.hex}]<[/]delete {self.textRenderer.formatLexerSyntax(self.textRenderer.formatRelation(relation))}[{Colors.textMuted.hex}]>[/]"
        try:
            self.driver.deleteRelation(relation)
            self.mainScreen.writeToLogger(
                deletedRelationStr, 
                True, 
                self.textRenderer.formatRelationDeleted(relation),
                highlightSyntax = False,
            )
        except Exception as exception:
            self.mainScreen.writeToLogger(
                deletedRelationStr,
                False,
                self.textRenderer.formatException(exception, withErrorHeader = True),
                highlightSyntax = False,
            )
            return None
        

class MainInput(ColoredInput):
    isLoadingHistory: var[bool] = var(False)

    def handle_key(self, event: Key):
        if event.key == "up":
            self.loadPreviousHistory()
        elif event.key == "down":
            self.loadNextHistory()
        return super().handle_key(event)
    
    @on(ColoredInput.Changed)
    def recordHistorySearchTerm(self):
        if not self.isLoadingHistory:
            assert type(self.app) is SolverProApp
            self.app.driver.recordHistorySearchTerm(self.value)
        else:
            self.isLoadingHistory = False
    
    def loadPreviousHistory(self):
        assert type(self.app) is SolverProApp
        prevHistory = self.app.driver.loadPreviousHistory()
        if prevHistory is not None:
            self.isLoadingHistory = True
            self.value = prevHistory
            self.cursor_position = len(prevHistory)

    def loadNextHistory(self):
        assert type(self.app) is SolverProApp
        nextHistory = self.app.driver.loadNextHistory()
        if nextHistory is not None:
            self.isLoadingHistory = True
            self.value = nextHistory
            self.cursor_position = len(nextHistory)

    def getInputHistory(self):
        assert type(self.app) is SolverProApp
        return self.app.driver.getInputHistory()
