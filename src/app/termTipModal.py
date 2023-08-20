from textual.reactive import var
from textual.screen import ModalScreen
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Label, Button
from textual.widgets import Footer


class TermTipModal(ModalScreen):
    DEFAULT_CSS = """
        TermTipModal {
            align: center middle;
        }
        
        TermTipModal #dialog {
            width: 60%;
            height: 70%;
            background: $foreground 15%;
        }
        
        TermTipModal #title {
            width: 100%;
            padding: 1 0 1 0;
            content-align: center middle;
        }

        TermTipModal #body {
            width: 100%;
            padding: 0 1;
        }

        TermTipModal #buttonbar {
            height: auto;
            align: right bottom;
        }

        TermTipModal #close {
            color: white;
            border: none;
            background: red 15%;
        }
        TermTipModal #close:hover {
            color: white;
            background: red 30%;
        }
    """

    BINDINGS = [
        ('escape', 'closeEscape', 'Close'),
        ('enter', 'closeEnter', 'Close'),
    ]

    title: var[str] = var("")
    body: var[str] = var("")

    def __init__(self, title: str = "", body: str = "", *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.title = title
        self.body = body

    def compose(self):
        with Vertical(id = 'dialog'):
            with VerticalScroll():
                yield Label(self.title, id = 'title')
                yield Label(self.body, id = 'body')
            with Horizontal(id = "buttonbar"):
                yield Button("Close", id = 'close')
        yield Footer()
    
    def action_closeEscape(self):
        self.dismiss()

    def action_closeEnter(self):
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()
