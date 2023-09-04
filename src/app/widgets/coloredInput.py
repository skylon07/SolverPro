from textual.widgets import Input
from rich.console import Console, ConsoleOptions, RenderableType
from rich.segment import Segment

from src.app.textRenderer import TextRenderer


def _lazyImportSolverProApp():
    from src.app.widgets.solverProApp import SolverProApp
    return SolverProApp


class _ColoredInputRenderable:
    def __init__(self, superRenderable: RenderableType, passThru: bool, renderer: TextRenderer):
        self.superRenderable = superRenderable
        self.passThru = passThru
        self.renderer = renderer

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        items = self.superRenderable.__rich_console__(console, options) # type: ignore
        if self.passThru:
            yield from items
        
        items = list(items)
        try:
            assert type(items[0]) is Segment
            inputText = items[0].text
            items = [
                *self.renderer.render(
                    self.renderer.formatInputSyntax(inputText)
                ).render(console),
                *items[1:]
            ]
            yield from items
        except AssertionError:
            yield from items


class ColoredInput(Input):
    def render(self):
        # ie not placeholder or something else
        isActualText = self.value != ""
        assert type(self.app) is _lazyImportSolverProApp()
        return _ColoredInputRenderable(
            super().render(),
            not isActualText,
            self.app.textRenderer
        )

