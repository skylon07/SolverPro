from typing import Collection

from textual import on
from textual.reactive import var
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Button, Label

from src.app.termTips import TermTips, TermTip

def _lazyImportSolverProApp():
    from src.app.widgets.solverProApp import SolverProApp
    return SolverProApp


class DictionaryScreen(Screen):
    DEFAULT_CSS = """
        DictionaryScreen {
            align: center middle;
        }
        
        DictionaryScreen #mainContainer {
            width: 100%;
            height: 100%;
        }

        DictionaryScreen #backButton {
            min-width: 8;
            width: 8%;
            height: 3;
            margin: 2 3;
            background: rgb(60, 60, 60);
        }
        DictionaryScreen #backButton:hover {
            background: rgb(60, 60, 60) 50%;
        }

        DictionaryScreen Horizontal {
            height: 8;
            align: center middle;
        }

        DictionaryScreen .spacer {
            width: 1fr;
            height: 5;
        }

        DictionaryScreen .termButton, DictionaryScreen .buttonBlank {
            min-width: 3;
            width: 6fr;
            max-width: 26;
            height: 7;
            padding: 1 2;
            text-align: center;
        }
        
        DictionaryScreen .termButton {
            background: rgb(55, 65, 90);
        }
        DictionaryScreen .termButton:hover {
            background: rgb(55, 65, 90) 50%;
        }
    """

    def compose(self):
        termsAndTips = tuple(TermTips().getTermTips())
        sortedTermTips = sorted(termsAndTips, key = self._termTipSorter)
        with VerticalScroll(id = 'mainContainer'):
            yield Button("← Back", id = 'backButton')
            while len(sortedTermTips) > 0:
                with Horizontal():
                    yield Label(classes = 'spacer')
                    for (term, termTip) in sortedTermTips[:5]:
                        yield Button(termTip.term, id = term, classes = 'termButton')
                        yield Label(classes = 'spacer')
                    if len(sortedTermTips) < 5:
                        for extraBlankIdx in range(5 - len(sortedTermTips)):
                            yield Label(classes = 'buttonBlank')
                            yield Label(classes = 'spacer')
                    sortedTermTips = sortedTermTips[5:]
            yield Label(classes = 'spacer')
                
    
    @on(Button.Pressed)
    def termClicked(self, event: Button.Pressed):
        if event.button.id == 'backButton':
            self.dismiss()
            return
        
        term = event.button.id
        assert term is not None
        assert type(self.app) is _lazyImportSolverProApp()
        self.app.action_showTermTip(term)

    def _termTipSorter(self, termTipData: tuple[str, TermTip]):
        (term, termTip) = termTipData
        return termTip.term
