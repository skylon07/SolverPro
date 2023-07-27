from textual.app import App
from textual.widgets import Footer, Header, Label, Button

class SolverProApp(App):
    def compose(self):
        yield Header()
        yield Label("Solver Pro!")
        yield Button("Useless button")
        yield Footer()

if __name__ == "__main__":
    SolverProApp().run()
