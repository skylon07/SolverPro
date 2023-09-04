from typing import Iterable
from threading import Timer

from textual import on
from textual.reactive import var
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal, HorizontalScroll
from textual.widget import Widget
from textual.widgets import Button, Label

from src.algebrasolver.solver import Relation
from src.app.textRenderer import TextRenderer
from src.app.widgets.colors import Colors
from src.app.widgets.coloredInput import ColoredInput
from src.common.functions import lazyImportSolverProApp


class HistoryScreen(Screen):
    DEFAULT_CSS = f"""
        HistoryScreen {{
            align: center middle;
        }}
        
        HistoryScreen #mainContainer {{
            width: 100%;
            height: 100%;
            align: center top;
        }}

        HistoryScreen #backButton {{
            min-width: 8;
            width: 8%;
            height: 3;
            margin: 2 3;
            background: {Colors.fillPlain.hex};
        }}

        HistoryScreen .emptyState {{
            color: {Colors.textMuted.hex};
            height: 9;
        }}

        HistoryScreen RelationEditRow {{
            margin: 3;
        }}
    """

    relations: var[tuple[Relation] | None] = var(None)

    def __init__(self, relations: Iterable[Relation], *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.relations = tuple(relations)

    def compose(self):
        assert self.relations is not None
        with VerticalScroll(id = 'mainContainer'):
            yield Button("← Back", id = 'backButton')
            anyRelations = False
            for relation in self.relations:
                anyRelations = True
                yield RelationEditRow(relation)
            if not anyRelations:
                yield Label("(No relations recorded)", classes = 'emptyState')


    @on(Button.Pressed, '#backButton')
    def goBack(self):
        self.dismiss()


class RelationEditRow(Widget):
    DEFAULT_CSS = f"""
        RelationEditRow {{
            width: 100%;
            height: 3;
        }}

        RelationEditRow.hidden, RelationEditRow .hidden {{
            display: none;
        }}

        RelationEditRow HorizontalScroll {{
            width: 1fr;
            height: 100%;
        }}

        RelationEditRow #staticGroup HorizontalScroll {{
            background: {Colors.fillPlain.hex};
        }}

        RelationEditRow Label {{
            height: 1;
            margin: 1 3;
            content-align: left middle;
        }}

        RelationEditRow Input {{
            width: 100%;
            height: 1fr;
            background: {Colors.fillBlue.hex} 50%;
        }}
        RelationEditRow Input:focus {{
            background: {Colors.fillBlue.hex} 50%;
        }}

        RelationEditRow Input.errorFlash {{
            border: tall {Colors.textRed.hex};
            color: {Colors.textRed.hex};
            background: {Colors.fillRed.hex};
        }}

        RelationEditRow Button {{
            width: 10;
            height: 100%;
            content-align: center middle;
            margin: 0 3;
        }}

        RelationEditRow #edit {{
            background: {Colors.fillBlue.hex};
        }}

        RelationEditRow #delete {{
            background: {Colors.fillRed.hex};
        }}

        RelationEditRow #cancel {{
            background: {Colors.fillPlain.hex};
        }}

        RelationEditRow #save {{
            background: {Colors.fillGreen.hex};
        }}
    """

    relation: var[Relation | None] = var(None)
    flashTimer: var[Timer | None] = var(None)

    def __init__(self, relation: Relation, *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.relation = relation

    def compose(self):
        assert type(self.app) is lazyImportSolverProApp()
        renderer = self.app.textRenderer

        with Horizontal(id = 'staticGroup'):
            with HorizontalScroll():
                yield Label(self.relationStr(True))
            yield Button("Edit", id = 'edit')
            yield Button("Delete", id = 'delete')
        with Horizontal(id = 'editGroup', classes = 'hidden'):
            with HorizontalScroll():
                yield ColoredInput()
            yield Button("Cancel", id = 'cancel')
            yield Button("Save", id = 'save')

    def relationStr(self, highlightSyntax: bool):
        assert self.relation is not None
        assert type(self.app) is lazyImportSolverProApp()
        renderer = self.app.textRenderer
        return renderer.formatRelation(self.relation, highlightSyntax = highlightSyntax)
    
    @on(Button.Pressed, '#edit')
    def enterEditMode(self):
        self.query_one('#staticGroup').add_class('hidden')
        self.query_one('#editGroup').remove_class('hidden')
        input = self.query_one(ColoredInput)
        input.value = self.relationStr(False)
        input.focus()

    @on(Button.Pressed, '#delete')
    def deleteOwnRelation(self):
        assert self.relation is not None
        assert type(self.app) is lazyImportSolverProApp()
        
        self.app.deleteRelation(self.relation)
        self.add_class('hidden')
    
    @on(Button.Pressed, '#cancel')
    def exitEditMode(self):
        self.query_one('#staticGroup').remove_class('hidden')
        self.query_one('#editGroup').add_class('hidden')

    @on(ColoredInput.Submitted)
    @on(Button.Pressed, '#save')
    def saveChanges(self):
        assert self.relation is not None
        assert type(self.app) is lazyImportSolverProApp()
        
        input = self.query_one(ColoredInput)
        label = self.query_one(Label)
        newRelation = self.app.replaceRelation(self.relation, input.value)
        noErrorsHappened = newRelation is not None
        if noErrorsHappened:
            self.relation = newRelation
            label.update(self.relationStr(True))
            self.exitEditMode()
        else:
            input.focus()
            self.flashError()

    def flashError(self):
        self._clearFlash()

        input = self.query_one(ColoredInput)
        input.add_class('errorFlash')
        input.highlightSyntax = False

        self.flashTimer = Timer(0.7, self._clearFlash)
        self.flashTimer.start()
    
    def _clearFlash(self):
        input = self.query_one(ColoredInput)
        input.remove_class('errorFlash')
        input.highlightSyntax = True
        if self.flashTimer is not None:
            self.flashTimer.cancel()
            self.flashTimer = None
