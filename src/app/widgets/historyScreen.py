from typing import Iterable
from threading import Timer

from textual import on
from textual.reactive import var, reactive
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal, HorizontalScroll
from textual.widget import Widget
from textual.widgets import Button, Input

from src.app.widgets.dynamicLabel import DynamicLabel
from src.algebrasolver.solver import Relation
from src.app.textRenderer import TextRenderer


def _lazyImportSolverProApp():
    from src.app.widgets.solverProApp import SolverProApp
    return SolverProApp


class HistoryScreen(Screen):
    DEFAULT_CSS = """
        HistoryScreen {
            align: center middle;
        }
        
        HistoryScreen #mainContainer {
            width: 100%;
            height: 100%;
            align: center top;
        }

        HistoryScreen #backButton {
            min-width: 8;
            width: 8%;
            height: 3;
            margin: 2 3;
            background: rgb(60, 60, 60);
        }
        HistoryScreen #backButton:hover {
            background: rgb(60, 60, 60) 50%;
        }

        HistoryScreen RelationEditRow {
            margin: 3;
        }

        HistoryScreen .spacer {
            width: 1fr;
            height: 5;
        }
    """

    relations: var[tuple[Relation] | None] = var(None)

    def __init__(self, relations: Iterable[Relation], *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.relations = tuple(relations)

    def compose(self):
        assert self.relations is not None
        with VerticalScroll(id = 'mainContainer'):
            yield Button("← Back", id = 'backButton')
            for relation in self.relations:
                yield RelationEditRow(relation)


    @on(Button.Pressed, '#backButton')
    def goBack(self):
        self.dismiss()


class RelationEditRow(Widget):
    DEFAULT_CSS = """
        RelationEditRow {
            width: 100%;
            height: 3;
        }

        RelationEditRow.hidden, RelationEditRow .hidden {
            display: none;
        }

        RelationEditRow HorizontalScroll {
            width: 1fr;
            height: 100%;
        }

        RelationEditRow #staticGroup HorizontalScroll {
            background: rgb(60, 60, 60);
        }

        RelationEditRow DynamicLabel {
            height: 1;
            margin: 1 3;
            content-align: left middle;
        }

        RelationEditRow Input {
            width: 100%;
            height: 1fr;
            background: rgb(40, 50, 75);
        }
        RelationEditRow Input:focus {
            background: rgb(55, 65, 90);
        }

        RelationEditRow Input.errorFlash {
            border: tall rgb(200, 75, 85);
            color: rgb(200, 75, 85);
            background: rgb(100, 55, 65);
        }

        RelationEditRow Button {
            width: 10;
            height: 100%;
            content-align: center middle;
            margin: 0 3;
        }

        RelationEditRow #edit {
            background: rgb(55, 65, 90);
        }
        RelationEditRow #edit:hover {
            background: rgb(55, 65, 90) 50%;
        }

        RelationEditRow #delete {
            background: rgb(100, 55, 65);
        }
        RelationEditRow #delete:hover {
            background: rgb(100, 55, 65) 50%;
        }

        RelationEditRow #cancel {
            background: rgb(50, 50, 50);
        }
        RelationEditRow #cancel:hover {
            background: rgb(50, 50, 50) 50%;
        }

        RelationEditRow #save {
            background: rgb(55, 90, 65);
        }
        RelationEditRow #save:hover {
            background: rgb(55, 90, 65) 50%;
        }
    """

    relation: var[Relation | None] = var(None)
    flashTimer: var[Timer | None] = var(None)

    def __init__(self, relation: Relation, *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.relation = relation

    def compose(self):
        with Horizontal(id = 'staticGroup'):
            with HorizontalScroll():
                yield DynamicLabel(self.relationStr)
            yield Button("Edit", id = 'edit')
            yield Button("Delete", id = 'delete')
        with Horizontal(id = 'editGroup', classes = 'hidden'):
            with HorizontalScroll():
                yield Input()
            yield Button("Cancel", id = 'cancel')
            yield Button("Save", id = 'save')

    @property
    def relationStr(self):
        assert self.relation is not None
        # TODO: refactor text renderer to distinguish between "formatting" and "rendering"
        #       so the line below can be reused
        return TextRenderer()._correctSyntaxes(f"{self.relation.leftExpr} = {self.relation.rightExpr}")
    
    @on(Button.Pressed, '#edit')
    def enterEditMode(self):
        self.query_one('#staticGroup').add_class('hidden')
        self.query_one('#editGroup').remove_class('hidden')
        input = self.query_one(Input)
        input.value = self.relationStr
        input.focus()

    @on(Button.Pressed, '#delete')
    def deleteOwnRelation(self):
        assert self.relation is not None
        assert type(self.app) is _lazyImportSolverProApp()
        
        self.app.deleteRelation(self.relation)
        self.add_class('hidden')
    
    @on(Button.Pressed, '#cancel')
    def exitEditMode(self):
        self.query_one('#staticGroup').remove_class('hidden')
        self.query_one('#editGroup').add_class('hidden')

    @on(Input.Submitted)
    @on(Button.Pressed, '#save')
    def saveChanges(self):
        assert self.relation is not None
        assert type(self.app) is _lazyImportSolverProApp()
        
        input = self.query_one(Input)
        label = self.query_one(DynamicLabel)
        newRelation = self.app.replaceRelation(self.relation, input.value)
        noErrorsHappened = newRelation is not None
        if noErrorsHappened:
            self.relation = newRelation
            label.data = self.relationStr
            self.exitEditMode()
        else:
            input.focus()
            self.flashError()

    def flashError(self):
        self._clearFlash()

        input = self.query_one(Input)
        input.add_class('errorFlash')

        self.flashTimer = Timer(0.7, self._clearFlash)
        self.flashTimer.start()
    
    def _clearFlash(self):
        input = self.query_one(Input)
        input.remove_class('errorFlash')
        if self.flashTimer is not None:
            self.flashTimer.cancel()
            self.flashTimer = None
