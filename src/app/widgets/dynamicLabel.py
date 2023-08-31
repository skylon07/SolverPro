from typing import TypeVar

from textual.reactive import reactive
from textual.widgets import Label
from rich.console import RenderableType


class DynamicLabel(Label):
    DEFAULT_CSS = """
        DynamicLabel {
            width: auto;
            height: auto;
        }
    """
    
    data: reactive[RenderableType | None] = reactive(None)

    def __init__(self, initData: RenderableType | None, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.data = initData

    def render(self):
        return self.data
