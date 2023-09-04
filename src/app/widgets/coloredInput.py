from typing import Iterable

from textual.widgets import Input
from rich.console import Console, ConsoleOptions, RenderableType
from rich.segment import Segment

from src.app.textRenderer import TextRenderer
from src.common.functions import lazyImportSolverProApp


class _ColoredInputRenderable:
    def __init__(self, superRenderable: RenderableType, passThru: bool, renderer: TextRenderer):
        self.superRenderable = superRenderable
        self.passThru = passThru
        self.renderer = renderer

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        items = self.superRenderable.__rich_console__(console, options) # type: ignore
        if self.passThru:
            yield from items
        
        yield from self._formatSegments(tuple(items), console)

    def _formatSegments(self, renderItems: Iterable, console: Console):
        for renderItem in renderItems:
            if type(renderItem) is Segment and not self._isCursorSegment(renderItem):
                formattedText = self.renderer.render(
                    self.renderer.formatLexerSyntax(renderItem.text)
                )
                yield from formattedText.render(console)
            else:
                yield renderItem

    def _isCursorSegment(self, segment: Segment):
        return segment.style is not None and segment.style.bgcolor is not None


class ColoredInput(Input):
    def render(self):
        # ie not placeholder or something else
        isActualText = self.value != ""
        assert type(self.app) is lazyImportSolverProApp()
        return _ColoredInputRenderable(
            super().render(),
            not isActualText,
            self.app.textRenderer
        )

