from textual import events, on
from textual.app import App
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Header, TextLog, Input

from src.common.functions import first, getVersion
from src.app.appDriver import AppDriver, ProcessResult, Command
from src.app.textRenderer import TextRenderer


class MainScreen(Screen):
    def compose(self):
        yield Header(show_clock = True)
        yield TextLog()
        yield Input(placeholder = " < Command >")
        
    def on_mount(self):
        self.focus_next(Input)
        self.app.title = f"--- Solver Pro {getVersion()} ---"
        self.query_one(Header).tall = True

    @on(Input.Submitted)
    def runCommand(self, event: Input.Submitted):
        commandStr = event.value

        textLog = self.query_one(TextLog)
        textLog.write(commandStr)

        input = self.query_one(Input)
        input.value = ""

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
                relation = result.data
                textLog.write(renderer.renderRelation(relation))

            elif result.type is Command.EVALUATE_EXPRESSION:
                exprs = result.data
                textLog.write(renderer.renderExpressions(exprs))

            else:
                raise NotImplementedError(f"Command result of type {result.type} not implemented")
        
        except Exception as error:
            textLog.write(renderer.renderException(error))


class SolverProApp(App):
    SCREENS = {"main": MainScreen()}

    driver: var[AppDriver] = var(lambda: AppDriver())
    textRenderer: var[TextRenderer] = var(lambda: TextRenderer())

    def on_mount(self):
        self.push_screen("main")


if __name__ == "__main__":
    app = SolverProApp()
    app.run()
