from typing import Collection

from textual import on
from textual.reactive import var
from textual.screen import ModalScreen
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Label, Button
from textual.widgets import Footer
from rich.console import RenderableType

from src.app.widgets.colors import Colors


class TermTipModal(ModalScreen):
    DEFAULT_CSS = f"""
        TermTipModal {{
            align: center middle;
        }}
        
        TermTipModal #content {{
            width: 60%;
            max-width: 60;
            height: 40%;
            max-height: 14;
            background: {Colors.fillPlain.hex};
        }}
        
        TermTipModal #title {{
            width: 100%;
            padding: 1 0 1 0;
            content-align: center middle;
        }}

        TermTipModal .bodyItem {{
            width: 100%;
            padding: 0 1;
        }}

        TermTipModal #buttonbar {{
            width: 60%;
            max-width: 60;
            height: auto;
            align: right bottom;
            background: {Colors.fillPlain.hex};
        }}

        TermTipModal #close {{
            color: {Colors.textPlain.hex};
            border: none;
            background: {Colors.fillRed.hex};
        }}
        TermTipModal #close:hover {{
            color: {Colors.textPlain.hex};
            background: {Colors.textRed.hex};
        }}
    """

    BINDINGS = [
        ('escape', 'closeEscape', 'Close'),
        ('enter', 'closeEnter', 'Close'),
    ]

    title: var[str] = var("")
    bodyItems: var[Collection[RenderableType]] = var(tuple())

    def __init__(self, term: str = "", bodyItems: Collection[RenderableType] = tuple(), *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.title = f"[{Colors.textMuted.hex}]--=[/]  {term}  [{Colors.textMuted.hex}]=--[/]"
        self.bodyItems = bodyItems

    def compose(self):
        with VerticalScroll(id = 'content'):
            yield Label(self.title, id = 'title')
            for bodyItem in self.bodyItems:
                yield Label(bodyItem, classes = 'bodyItem')
                yield Label("", classes = 'bodyItem')
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
