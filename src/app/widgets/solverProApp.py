from threading import Timer

from textual import on
from textual.app import App
from textual.reactive import var
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import TextLog, Input, Button, Label
from rich.text import Text

from src.common.functions import first, getVersion
from src.app.appDriver import AppDriver, Command
from src.app.widgets.appHeader import AppHeader
from src.app.widgets.errorModal import ErrorModal
from src.app.widgets.termTipModal import TermTipModal
from src.app.widgets.dictionaryScreen import DictionaryScreen
from src.app.widgets.historyScreen import HistoryScreen
from src.app.termTips import TermTips
from src.app.textRenderer import TextRenderer
from src.algebrasolver.solver import Relation


class MainScreen(Screen):
    CSS = """
        MainScreen TextLog {
            link-hover-style: underline;
            link-hover-color: #0a1eff;
            link-hover-background: #3250f0 40%;
        }
        
        Input.highlighted .input--placeholder {
            background: #a0a0a0;
        }

        MainScreen #rightSection {
            min-width: 16;
            width: 20%;
            max-width: 32;
            height: 100%;
            padding: 0 5;
            align: center middle;
        }

        MainScreen .managerButton {
            width: 100%;
            height: 5;
        }

        MainScreen #dictionaryButton {
            background: rgb(55, 65, 90);
        }
        MainScreen #dictionaryButton:hover {
            background: rgb(55, 65, 90) 50%;
        }

        MainScreen #historyButton {
            background: rgb(55, 75, 50);
        }
        MainScreen #historyButton:hover {
            background: rgb(55, 75, 50) 50%;
        }

        MainScreen #tutorialButton {
            background: rgb(85, 50, 60);
        }
        MainScreen #tutorialButton:hover {
            background: rgb(85, 50, 60) 50%;
        }

        MainScreen .spacer {
            width: 100%;
            height: 1fr;
        }
    """

    inputTimer: var[Timer | None] = var(None)

    def compose(self):
        yield AppHeader()
        with Horizontal(id = 'sectionsContainer'):
            with Vertical(id = 'leftSection'):
                yield TextLog()
                yield Input(placeholder = " < Command >")
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

    @on(Input.Submitted)
    def runCommand(self, event: Input.Submitted):
        input = event.input
        commandStr = input.value
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
            result = first(driver.processCommandLines(commandStr), None)
            assert result is not None
            if result.type is Command.EMPTY:
                self.writeSpacerToLogger()

            elif result.type is Command.RECORD_RELATION:
                (relation, isRedundant) = result.data
                self.writeToLogger(commandStr, True, renderer.formatRelation(relation, warnRedundant = isRedundant))

            elif result.type is Command.EVALUATE_EXPRESSION:
                exprs = result.data
                self.writeToLogger(commandStr, True, renderer.formatExpressions(exprs))

            else:
                raise NotImplementedError(f"Command result of type {result.type} not implemented")
        
        except Exception as error:
            self.writeToLogger(commandStr, False, renderer.formatException(error, withErrorHeader = True))
        
        self.inputTimer = Timer(0.1, lambda: input.remove_class('highlighted'))
        self.inputTimer.start()

    def writeToLogger(self, commandStr: str, commandSucceeded: bool, formattedStr: str):
        assert type(self.app) is SolverProApp
        renderer = self.app.textRenderer

        textLog = self.query_one(TextLog)
        if commandStr != "":
            textLog.write(renderer.render(renderer.formatInputLog(commandStr, commandSucceeded)))
        textLog.write(renderer.render(formattedStr))
        self.writeSpacerToLogger()

    def writeSpacerToLogger(self):
        textLog = self.query_one(TextLog)
        spaceForNextCommand = " "
        textLog.write(spaceForNextCommand)

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
    driver: var[AppDriver] = var(lambda: AppDriver())
    textRenderer: var[TextRenderer] = var(lambda: TextRenderer())
    termTips: var[TermTips] = var(lambda: TermTips())

    mainScreen: var[MainScreen] = var(lambda: MainScreen())

    def on_mount(self):
        self.push_screen(self.mainScreen)
        # DEBUG
        first(self.driver.processCommandLines("a = 1")) # type: ignore
        first(self.driver.processCommandLines("b = 2")) # type: ignore
        first(self.driver.processCommandLines("c = 3")) # type: ignore
        first(self.driver.processCommandLines("d = 4")) # type: ignore
        first(self.driver.processCommandLines("e = 5")) # type: ignore
        first(self.driver.processCommandLines("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff = 6")) # type: ignore

    # defined as an action for term tip links
    def action_showTermTip(self, term: str):
        tip = self.termTips.lookupTerm(term)
        self.push_screen(TermTipModal(
            tip.term,
            tuple(self.textRenderer.render(line) for line in tip.definitionLines),
        ))

    def replaceRelation(self, oldRelation: Relation, newRelationCommand: str):
        modifiedRelationStr = f"<replace {self.textRenderer.formatRelation(oldRelation)}>"
        try:
            result = self.driver.replaceRelation(oldRelation, newRelationCommand)
            (relation, isRedundant) = result.data
            self.mainScreen.writeToLogger(modifiedRelationStr, True, self.textRenderer.formatRelationReplaced(oldRelation, relation, warnRedundant = isRedundant))
            assert type(relation) is Relation
            return relation
        except Exception as exception:
            self.mainScreen.writeToLogger(modifiedRelationStr, False, self.textRenderer.formatException(exception, withErrorHeader = True))
            return None

    def deleteRelation(self, relation: Relation):
        deletedRelationStr = f"<delete {self.textRenderer.formatRelation(relation)}>"
        try:
            self.driver.deleteRelation(relation)
            self.mainScreen.writeToLogger(deletedRelationStr, True, self.textRenderer.formatRelationDeleted(relation))
        except Exception as exception:
            self.mainScreen.writeToLogger(deletedRelationStr, False, self.textRenderer.formatException(exception, withErrorHeader = True))
            return None