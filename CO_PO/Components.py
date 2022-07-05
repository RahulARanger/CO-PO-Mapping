import string
import random
import typing
from dash import html, no_update, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from CO_PO.AppConfig import BaseApplication, time_format
from CO_PO import __version__
import dash_uploader as du
import pathlib


def get_header():
    html.Thead(
        [
            html.Tr(_)
            for _ in ("File Name", "File Size", "Created Date")
        ]
    )


def set_timestamp(title):
    return title, dmc.Text(time_format(), size="xs")


def show_notifications(title, *message, auto_close: typing.Union[bool, int] = False, color="red"):
    return dmc.Notification(
        title=set_timestamp(title),
        color=color,
        autoClose=auto_close,
        disallowClose=False,
        message=message,
        action="show",
        id="".join(random.choices(string.ascii_letters, k=10))
    )


def set_file_path(new_path, old_path):
    if not new_path or new_path == old_path:
        return no_update

    old = pathlib.Path(old_path) if old_path else None

    if old and old.exists():
        note = show_notifications(
            "File uploaded Successfully",
            "Replaced old Uploaded File with new one, by Clicking on \"Process\", Old results will be replaced",
            auto_close=6000,
            color="orange"
        )

        old.unlink()
        parent = old.parent

        if not list(parent.iterdir()):
            parent.rmdir()

    else:
        note = show_notifications(
            "File Uploaded Successfully",
            "You can use this file for processing. ",
            dmc.Code("Note: only checked for extension .xlsx. not its internal contents"),
            color="green",
            auto_close=3000
        )

    return new_path, note


class HeaderComponent(BaseApplication):
    def __init__(self):
        # DropDown
        self._sample_input_dropdown = "__dropdown_sample_input"
        self._sample_output_dropdown = "__dropdown_sample_output"

        # DropDownMenuItem
        self._check_input = "__check_input"
        self._help_for_input = "help_input"
        self._clear_cache = "_clear_cache"
        self.auto_update = "auto_update"
        self._fetch = "__fetch_status"
        self._shutdown = "__shutdown"

        super().__init__()

    def _header(self):
        return dbc.NavbarSimple(
            [
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            "Help 👋", header=True
                        ),
                        dbc.DropdownMenuItem(
                            "About", n_clicks=0
                        ),
                        dbc.DropdownMenuItem(
                            "Documentation"
                        ),
                        dbc.DropdownMenuItem(
                            "Sample Input", n_clicks=0, id=self._sample_input_dropdown
                        ),
                        dbc.DropdownMenuItem(
                            "Sample Output", n_clicks=0, id=self._sample_output_dropdown
                        )
                    ],
                    menu_variant="dark",
                    nav=True,
                    in_navbar=True,
                    color="info",
                    align_end=True,
                    label="Help 👋"
                ),
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            "Engine ⚙", header=True
                        ),
                        dbc.DropdownMenuItem(
                            "Check Status", n_clicks=0, id=self._check_input
                        ),
                        dbc.DropdownMenuItem(
                            "Clear Cache", n_clicks=0, id=self._clear_cache
                        ),
                        dbc.DropdownMenuItem(
                            "Shutdown", n_clicks=0, id=self._shutdown
                        )
                    ],
                    menu_variant="dark",
                    nav=True,
                    in_navbar=True,
                    color="info",
                    align_end=True,
                    label="Engine ⚙"
                ),
                dmc.Switch(
                    label="Auto Check Updates",
                    onLabel="Yes",
                    offLabel="No",
                    color="orange",
                    size="md",
                    id=self.auto_update,
                    checked=self.settings[self.auto_update]
                )
            ],
            brand="CO-PO Mapping",
            brand_href=self.repo,
            light=False,
            dark=True
        )


class FormComponent(HeaderComponent):
    def __init__(self):
        # -> Input
        self.exams = "__exams"
        self.uploaded = "__uploaded"

        self._result = "__result"
        self.upload_button = "__upload"
        self.confirm_process = "confirm_process"

        super().__init__()

    def _body(self):
        return html.Section(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Upload the Data File"
                        ),
                        dbc.CardBody(
                            [
                                # max size: 1GB (default)
                                du.Upload(
                                    id=self.upload_button,
                                    filetypes=[
                                        "xlsx"
                                    ]
                                ),
                                dmc.Space(h="xs"),
                                html.Em(
                                    dmc.Highlight(
                                        "Only .xlsx files are allowed to be uploaded",
                                        highlight=[".xlsx", "allowed"],
                                        highlightColor="orange", size="xs", align="right"
                                    )
                                ),
                                dmc.Space(h=10),
                                dmc.TextInput(label="Uploaded File", required=True, disabled=True, id=self.uploaded),
                                dmc.Space(h=10),
                                dmc.NumberInput(
                                    label="No. of Exams",
                                    description="Enter the Number of Exams conducted",
                                    required=True,
                                    min=1,
                                    max=100,
                                    id=self.exams
                                ),
                                dmc.ActionIcon(
                                    dmc.Image(src="/assets/help.svg", alt="Get Help"),
                                    class_name="position-absolute top-0 start-100 translate-middle",
                                    id=self._help_for_input
                                )
                            ],
                            style={
                                "width": "100%"
                            }
                        ),
                        dbc.CardFooter(
                            [
                                dmc.Button(
                                    "Process",
                                    class_name="custom-butt",
                                    style={
                                        "float": "right"
                                    },
                                    id=self.confirm_process
                                ),
                                dmc.Button(
                                    "Results ⭐",
                                    class_name="custom-butt",
                                    style={
                                        "float": "left"
                                    },
                                    id=self._result
                                )
                            ]
                        )
                    ]
                )
            ], className="actual-body"
        )


class NotificationComponents(FormComponent):
    def __init__(self):
        # -> Notifications
        self.for_file_upload = "__for_file_upload"
        self.for_shutdown = "__for_shutdown"
        self.for_process = "__for_process"

        super().__init__()

    def _notifications(self):
        return dmc.NotificationsProvider(
            [
                *(
                    html.Div(
                        id=_
                    )
                    for _ in (self.for_file_upload, self.for_shutdown, self.for_process)
                )
            ],
            zIndex=2,
            position="bottom-right",
            limit=100
        )


class ModelsComponent(NotificationComponents):
    def __init__(self):
        # -> Modals
        self._modal_for_shutdown = "__modal_for_shutdown"
        self.final_step = "__modal_for_process"
        self._modal_for_clear_cache = "__modal_for_clear_cache"

        # --> Modals Components
        self._shutdown = "__shutdown"
        self._shutdown_close = "__close_modal"
        self.confirm_shutdown = self._shutdown + "confirm"
        self.confirm_process = "confirm_process"

        super().__init__()

    def _for_shutdown(self):
        return dmc.Modal(
            title="Want to Shutdown ?",
            id=self._modal_for_shutdown,
            children=[
                dmc.Text("Closing this Application may stop all the running tasks!"),
                dmc.Space(h=20),
                dmc.Group(
                    [
                        dmc.Button("Shutdown", id=self.confirm_shutdown, color="red"),
                        dmc.Button(
                            "Cancel",
                            color="green",
                            variant="outline",
                            id=self._shutdown_close
                        ),
                    ],
                    position="right",
                ),
            ],
        )

    def _help_for_input_modal(self):
        return dmc.Modal(
            title="Help for Upload",
            centered=True,
            id=self.final_step,
            children=dcc.Markdown(
                (self.docs / "input.md").read_text()
            )
        )

    def _clear_cache_modal(self):
        return dmc.Modal(
            title="Clear Cache",
            centered=True,
            id=self._modal_for_clear_cache,
            children=[
                dmc.Alert(
                    "Whenever files are uploaded, they are stored in the local folder as a temp files."
                    "It normally deletes all the files, when application was gracefully closed "
                    "(through \"Shutdown\" Button). But it is possible to miss some files. "
                    "So clearing those can save some space on your disk.",
                    title="Why?",
                    color="violet",
                    variant="filled"
                ),
                dmc.Alert(
                    "Deleting the temp files would also delete the "
                    "files that you might have uploaded now or used in the existing process. Make sure no processes"
                    " are running, by \"Check Status\"",
                    color="red",
                    title="Note Before",
                    variant="filled"
                ),
                dmc.Space(h=30),
                dmc.Space(h=20),
                dmc.Button(
                    "Delete Cache",
                    class_name="custom-butt",
                    style={
                        "float": "right"
                    }
                )
            ]
        )

    def _modals(self):
        return html.Div([
            self._for_shutdown(),
            self._help_for_input_modal(),
            self._clear_cache_modal()
        ], id="modals")
