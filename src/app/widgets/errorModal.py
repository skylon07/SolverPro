from typing import Collection

from textual import on
from textual.reactive import var
from textual.screen import ModalScreen
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Label, Button
from textual.widgets import Footer
from rich.console import RenderableType

from src.app.textRenderer import TextRenderer


class ErrorModal(ModalScreen):
    DEFAULT_CSS = """
        ErrorModal {
            align: center middle;
        }
        
        ErrorModal #content {
            width: 60%;
            max-width: 60;
            height: 40%;
            max-height: 14;
            background: $foreground 15%;
        }
        
        ErrorModal #title {
            width: 100%;
            padding: 1 0 1 0;
            content-align: center middle;
        }

        ErrorModal #body {
            width: 100%;
            padding: 0 1;
        }

        ErrorModal #buttonbar {
            width: 60%;
            max-width: 60;
            height: auto;
            align: right bottom;
            background: $foreground 15%;
        }

        ErrorModal #close {
            color: white;
            border: none;
            background: red 15%;
        }
        ErrorModal #close:hover {
            color: white;
            background: red 30%;
        }
    """

    BINDINGS = [
        ('escape', 'closeEscape', 'Close'),
        ('enter', 'closeEnter', 'Close'),
    ]

    error: var[Exception | None] = var(None)

    def __init__(self, error: Exception, *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.error = error

    def compose(self):
        assert self.error is not None
        renderedError = TextRenderer().renderException(self.error, withErrorHeader = False)
        with VerticalScroll(id = 'content'):
            yield Label("[red]Error![/red]", id = 'title')
            yield Label(renderedError, id = 'body')
        with Horizontal(id = 'buttonbar'):
            yield Button("Close", id = 'close')
        yield Footer()
    
    def action_closeEscape(self):
        self.dismiss()

    def action_closeEnter(self):
        self.dismiss()

    @on(Button.Pressed, '#close')
    def closeModal(self):
        self.dismiss()
