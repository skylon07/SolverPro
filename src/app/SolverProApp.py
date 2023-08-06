from textual import events, on
from textual.app import App
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Label, Header, TextLog, Input

from src.common.functions import first
from src.app.appDriver import AppDriver, ProcessResult, Command


class MainScreen(Screen):
    def compose(self):
        yield TextLog()
        yield Input(placeholder = " < Command >")
        
    def on_mount(self):
        self.focus_next(Input)

    @on(Input.Submitted)
    def runCommand(self, event: Input.Submitted):
        commandStr = event.value
        
        textLog = self.query_one(TextLog)
        textLog.write(commandStr)

        input = self.query_one(Input)
        input.value = ""

        # TODO: why does tagging `driver: AppDriver` cause pylance to break?
        driver = self.app.driver
        result: ProcessResult = first(driver.processCommandLines(commandStr))
        if result.type is Command.EMPTY:
            pass

        elif result.type is Command.RECORD_RELATION:
            pass

        elif result.type is Command.EVALUATE_EXPRESSION:
            for expr in result.data:
                # TODO: standardize the tabbing here
                textLog.write(f"    {expr}")

        else:
            raise NotImplementedError(f"Command result of type {result.type} not implemented")


class SolverProApp(App):
    SCREENS = {"main": MainScreen()}

    driver: var[AppDriver] = var(lambda: AppDriver())

    def on_mount(self):
        self.push_screen("main")


if __name__ == "__main__":
    app = SolverProApp()
    app.run()
