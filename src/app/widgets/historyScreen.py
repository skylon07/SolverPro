from typing import Iterable

from textual import on
from textual.reactive import var, reactive
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal, HorizontalScroll
from textual.widget import Widget
from textual.widgets import Button, Label, Input

from src.algebrasolver.solver import Relation


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


    @on(Button.Pressed)
    def handleClick(self, event: Button.Pressed):
        if event.button.id == 'backButton':
            self.dismiss()


class RelationEditRow(Widget):
    DEFAULT_CSS = """
        RelationEditRow {
            width: 100%;
            height: 3;
        }

        RelationEditRow .hidden {
            display: none;
        }

        RelationEditRow HorizontalScroll {
            width: 1fr;
            height: 100%;
        }

        RelationEditRow #staticGroup HorizontalScroll {
            background: rgb(60, 60, 60);
        }

        RelationEditRow Label {
            height: 1fr;
            margin-top: 1;
            margin-left: 3;
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
    _editMode: var[bool] = var(False)

    def __init__(self, relation: Relation, *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.relation = relation

    def compose(self):
        with Horizontal(id = 'staticGroup'):
            with HorizontalScroll():
                yield Label(self.relationStr)
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
        return f"{self.relation.leftExpr} = {self.relation.rightExpr}"
    
    @on(Button.Pressed)
    def handleClick(self, event: Button.Pressed):
        buttonId = event.button.id
        if buttonId == 'edit':
            self.editMode = True
        elif buttonId == 'delete':
            pass # TODO
        elif buttonId == 'cancel':
            self.editMode = False
        elif buttonId == 'save':
            self.save()

    @property
    def editMode(self):
        return self._editMode
    
    @editMode.setter
    def editMode(self, newMode: bool):
        self._editMode = newMode
        isEditing = newMode is True
        if isEditing:
            self.query_one('#staticGroup').add_class('hidden')
            self.query_one('#editGroup').remove_class('hidden')
            input = self.query_one(Input)
            input.value = self.relationStr
            input.focus()
        else:
            self.query_one('#staticGroup').remove_class('hidden')
            self.query_one('#editGroup').add_class('hidden')

    @on(Input.Submitted)
    def save(self):
        pass # TODO
        self.editMode = False
