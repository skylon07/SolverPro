from typing import Collection

from textual import on
from textual.reactive import var
from textual.screen import ModalScreen
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Label, Button
from textual.widgets import Footer
from rich.console import RenderableType


class TermTipModal(ModalScreen):
    DEFAULT_CSS = """
        TermTipModal {
            align: center middle;
        }
        
        TermTipModal #content {
            width: 60%;
            max-width: 60;
            height: 40%;
            max-height: 14;
            background: $foreground 15%;
        }
        
        TermTipModal #title {
            width: 100%;
            padding: 1 0 1 0;
            content-align: center middle;
        }

        TermTipModal .bodyItem {
            width: 100%;
            padding: 0 1;
        }

        TermTipModal #buttonbar {
            width: 60%;
            max-width: 60;
            height: auto;
            align: right bottom;
            background: $foreground 15%;
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
    bodyItems: var[Collection[RenderableType]] = var(tuple())

    def __init__(self, term: str = "", bodyItems: Collection[RenderableType] = tuple(), *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.title = f"[#b0b0b0]--=[/#b0b0b0]  {term}  [#b0b0b0]=--[/#b0b0b0]"
        self.bodyItems = bodyItems

    def compose(self):
        with VerticalScroll(id = 'content'):
            yield Label(self.title, id = 'title')
            for bodyItem in self.bodyItems:
                yield Label(bodyItem, classes = "bodyItem")
                yield Label("", classes = "bodyItem")
        with Horizontal(id = "buttonbar"):
            yield Button("Close", id = 'close')
        yield Footer()
    
    def action_closeEscape(self):
        self.dismiss()

    def action_closeEnter(self):
        self.dismiss()

    @on(Button.Pressed)
    def onClose(self, event: Button.Pressed):
        self.dismiss()
