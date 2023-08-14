from time import sleep
from threading import Timer

from textual import on
from textual.app import App
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import TextLog, Input, Label
from textual.widget import Widget
from rich.text import Text

from src.common.functions import first, getVersion
from src.app.appDriver import AppDriver, ProcessResult, Command
from src.app.textRenderer import TextRenderer


class AppHeader(Widget):
    title: var[str] = var("")

    def __init__(self, title: str, *, name: str = None, id: str = None, classes: str = None):
        super().__init__(name = name, id = id, classes = classes)
        self.title = title

    def compose(self):
        yield Label(self.title)


class MainScreen(Screen):
    inputTimer: var[Timer] = var(None)

    def compose(self):
        yield AppHeader(f"--- Solver Pro {getVersion()} ---")
        yield TextLog()
        yield Input(placeholder = " < Command >")

    @on(Input.Submitted)
    def runCommand(self, event: Input.Submitted):
        commandStr = event.value

        textLog = self.query_one(TextLog)

        input = self.query_one(Input)
        input.value = ""
        input.add_class("darkPlaceholder")
        if self.inputTimer is not None:
            self.inputTimer.cancel()

        driver: AppDriver = self.app.driver
        renderer: TextRenderer = self.app.textRenderer
        try:
            # only single lines are accepted for now;
            # `renderer` (for exceptions) can't handle multiple lines yet,
            # and the driver does not behave transactionally (an error on the
            # third of four lines still actually executes the first two)
            driver.validateSingleLine(commandStr)
            result: ProcessResult = first(driver.processCommandLines(commandStr))
            if result.type is Command.EMPTY:
                pass

            elif result.type is Command.RECORD_RELATION:
                (relation, isRedundant) = result.data
                textLog.write(self._renderCommand(commandStr, True))
                textLog.write(renderer.renderRelation(relation, isRedundant))

            elif result.type is Command.EVALUATE_EXPRESSION:
                exprs = result.data
                textLog.write(self._renderCommand(commandStr, True))
                textLog.write(renderer.renderExpressions(exprs))

            else:
                raise NotImplementedError(f"Command result of type {result.type} not implemented")
        
        except Exception as error:
            textLog.write(self._renderCommand(commandStr, False))
            textLog.write(renderer.renderException(error))
        
        textLog.write(" ") # empty line to space for next command
        self.inputTimer = Timer(0.1, lambda: input.remove_class("darkPlaceholder"))
        self.inputTimer.start()

    def _renderCommand(self, commandStr: str, succeeded: bool):
        marker = self.app.console.render_str("[green]✓[/green]") if succeeded \
            else self.app.console.render_str("[red]✕[/red]")
        return marker + f" {commandStr}"


class SolverProApp(App):
    SCREENS = {"main": MainScreen()}

    CSS_PATH = "mainApp.tcss"

    driver: var[AppDriver] = var(lambda: AppDriver())
    textRenderer: var[TextRenderer] = var(lambda: TextRenderer())

    def on_mount(self):
        self.push_screen("main")


if __name__ == "__main__":
    app = SolverProApp()
    app.run()
