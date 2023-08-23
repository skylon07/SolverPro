from textual.reactive import reactive
from textual.widget import Widget


class _AppHeaderTitle(Widget):
    DEFAULT_CSS = """
        _AppHeaderTitle {
            width: 100%;
            height: 100%;
            content-align: center middle;
        }
    """

    title: reactive[str] = reactive("")

    def __init__(self, title: str = "", *, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name = name, id = id, classes = classes)
        self.title = title

    def render(self):
        return self.title


class AppHeader(Widget):
    DEFAULT_CSS = """
        AppHeader {
            dock: top;
            width: 100%;
            height: 3;
            background: $foreground 5%;
            color: $text;
        }
    """

    def compose(self):
        yield _AppHeaderTitle()

    def on_mount(self):
        headerTitle = self.query_one(_AppHeaderTitle)
        def setTitle(newTitle: str):
            headerTitle.title = newTitle
        self.watch(self.app, "title", setTitle)