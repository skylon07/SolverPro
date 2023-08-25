from threading import Timer

from textual import on
from textual.app import App
from textual.reactive import var
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import TextLog, Input, Button, Label

from src.common.functions import first, getVersion
from src.app.appDriver import AppDriver, Command
from src.app.widgets.appHeader import AppHeader
from src.app.widgets.termTipModal import TermTipModal
from src.app.widgets.termTipList import TermTipListScreen
from src.app.termTips import TermTips
from src.app.textRenderer import TextRenderer


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

        MainScreen #historyButton {
            background: rgb(55, 75, 50);
        }

        MainScreen #tutorialButton {
            background: rgb(85, 50, 60);
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
                # TODO: history screen
                yield Button("History (WIP)", id = 'historyButton', classes = 'managerButton')
                yield Label(classes = 'spacer')
                # TODO: tutorial screen(s)
                yield Button("Tutorial (WIP)", id = 'tutorialButton', classes = 'managerButton')
                yield Label(classes = 'spacer')

    def on_mount(self):
        self.app.title = f"--- Solver Pro {getVersion()} ---"

    @on(Input.Submitted)
    def runCommand(self, event: Input.Submitted):
        commandStr = event.value

        textLog = self.query_one(TextLog)

        input = self.query_one(Input)
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
                pass

            elif result.type is Command.RECORD_RELATION:
                (relation, isRedundant) = result.data
                textLog.write(renderer.renderInputLog(commandStr, True))
                textLog.write(renderer.renderRelation(relation, isRedundant))

            elif result.type is Command.EVALUATE_EXPRESSION:
                exprs = result.data
                textLog.write(renderer.renderInputLog(commandStr, True))
                textLog.write(renderer.renderExpressions(exprs))

            else:
                raise NotImplementedError(f"Command result of type {result.type} not implemented")
        
        except Exception as error:
            textLog.write(renderer.renderInputLog(commandStr, False))
            textLog.write(renderer.renderException(error))
        
        textLog.write(" ") # empty line to space for next command
        self.inputTimer = Timer(0.1, lambda: input.remove_class('highlighted'))
        self.inputTimer.start()

    @on(Button.Pressed)
    def openMenuItem(self, event: Button.Pressed):
        assert type(self.app) is SolverProApp
        menuItem = str(event.button.label).lower()
        if menuItem == 'dictionary':
            self.app.push_screen('termTipList')
        else:
            error = ValueError(f"Invalid menu item [magenta]{menuItem}[/magenta]")
            renderer = self.app.textRenderer
            self.query_one(TextLog).write(renderer.renderException(error))


class SolverProApp(App):
    SCREENS = {
        'main': MainScreen(),
        'termTipList': TermTipListScreen(),
    }
    driver: var[AppDriver] = var(lambda: AppDriver())
    textRenderer: var[TextRenderer] = var(lambda: TextRenderer())
    termTips: var[TermTips] = var(lambda: TermTips())

    def on_mount(self):
        self.push_screen('main')

    def action_showTermTip(self, term: str):
        tip = self.termTips.lookupTerm(term)
        self.push_screen(TermTipModal(
            tip.term,
            tip.definitionLines,
        ))
