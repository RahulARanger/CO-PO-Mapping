import dash_mantine_components as dmc
from dash import html


class Card:
    def __init__(self):
        self._header = None
        self._footer = None
        self._body = None
        self._ends = "__card_ends"
        self._card_body = "card"

    @property
    def header(self):
        return dmc.Header(
            self._header, class_name=self._ends
        )

    @property
    def footer(self):
        return html.Footer(
            dmc.Group(
                self._footer, align="center", position="apart"
            ), className=self._ends + "-footer"
        )

    @property
    def body(self):
        return self._body

    @header.setter
    def header(self, children):
        self._header = children

    @footer.setter
    def footer(self, children):
        self._footer = children

    @body.setter
    def body(self, children):
        self._body = children

    def __call__(self):
        return dmc.Paper(dmc.Group(
            [
                self.header, self.body, self.footer
            ], direction="column",
            position="center", align="stretch", spacing="xs"
        ), class_name=self._card_body,)
