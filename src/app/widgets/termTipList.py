from typing import Collection

from textual import on
from textual.reactive import var
from textual.screen import Screen
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Label, Button
from textual.widgets import Footer
from rich.console import RenderableType

from src.app.termTips import TermTips, TermTip

def _lazyImportSolverProApp():
    from src.app.widgets.solverProApp import SolverProApp
    return SolverProApp


class TermTipListScreen(Screen):
    DEFAULT_CSS = """
        TermTipListScreen {
            align: center middle;
        }
        
        
    """

    def compose(self):
        termsAndTips = tuple(TermTips().getTermTips())
        sortedTermTips = sorted(termsAndTips, key = self._termTipSorter)
        for (term, termTip) in sortedTermTips:
            yield Button(termTip.term, id = term)
    
    @on(Button.Pressed)
    def termClicked(self, event: Button.Pressed):
        term = event.button.id
        assert term is not None
        assert type(self.app) is _lazyImportSolverProApp()
        self.app.action_showTermTip(term)

    def _termTipSorter(self, termTipData: tuple[str, TermTip]):
        (term, termTip) = termTipData
        return termTip.term
