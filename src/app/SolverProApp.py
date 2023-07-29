from textual import events, on
from textual.app import App
from textual.screen import Screen
from textual.widgets import Label, Header, TextLog, Input


class MainScreen(Screen):
    def compose(self):
        yield TextLog()
        yield Input(placeholder = " < Command >")
        
    def on_mount(self):
        self.focus_next(Input)

    @on(Input.Submitted)
    def processCommand(self, event: Input.Submitted):
        textLog = self.query_one(TextLog)
        textLog.write(event.value)

        input = self.query_one(Input)
        input.value = ""


class SolverProApp(App):
    SCREENS = {"main": MainScreen()}

    def on_mount(self):
        self.push_screen("main")


if __name__ == "__main__":
    app = SolverProApp()
    app.run()
