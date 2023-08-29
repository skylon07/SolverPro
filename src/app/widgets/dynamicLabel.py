from typing import TypeVar

from textual.reactive import reactive
from textual.widget import Widget
from rich.console import RenderableType


class DynamicLabel(Widget):
    data: reactive[RenderableType | None] = reactive(None)

    def __init__(self, initData: RenderableType | None, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.data = initData

    def render(self):
        return self.data
