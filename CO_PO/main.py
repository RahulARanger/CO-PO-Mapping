import json
import os
from threading import Timer
import dash_uploader as du
import pathlib
import string
import datetime
import random
import diskcache
from dash import Dash, html, Input, Output, ctx, no_update, State, dcc
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import typing
from CO_PO.parse_excel_file import Engine
import tempfile
from _thread import interrupt_main
import socket
import logging
import webbrowser


class CoreApplication:
    def __init__(self):
        # All Constants
        # Samples

        self._sample_input = "assets/Sample Input.xlsx"
        self._sample_output = "assets/Sample Output.txt"
        self._sample_input_dropdown = "__dropdown_sample_input"
        self._sample_output_dropdown = "__dropdown_sample_output"
        self._download_feed = "__download_feed"

        # -> Loading Overlay
        self.loading_overlay = "__loading_overlay"

        # -> Button Constants
        self._fetch = "__fetch_status"
        self._shutdown = "__shutdown"

        # --> Upload Button Constant
        self.upload_button = "__upload"

        # -> Card Header
        self.upload_header = "__upload_header"

        # -> Notifications
        self.for_file_upload = "__for_file_upload"
        self.for_process = "__for_process"

        # -> Modals
        self._modal_for_shutdown = "__modal_for_shutdown"
        self.final_step = "__modal_for_process"
        # --> Modals Components
        self._shutdown_close = "__close_modal"
        self.confirm_shutdown = self._shutdown + "confirm"
        self.confirm_process = "confirm_process"
        self.cancel_final_step = "__cancel_upload"

        self.alert_for_start = "alert_for_start"

        # -> DropDownMenu
        self._result = "__result"

        # -> Input
        self.exams = "__exams"

        # -> Repo URL
        self.repo = ""

        # -> Output
        self.result_for_process = "result_memory"

        self.temp = pathlib.Path(__file__).parent / "temp"

        self.__cache_disk = diskcache.Cache(str(self.temp))
        self.manager = DiskcacheLongCallbackManager(self.__cache_disk)

        self.app = Dash(__name__, long_callback_manager=self.manager, external_stylesheets=[
            "assets/index.css", "assets/bootstrap.min.css"
        ])
        self.set_layout()
        self.set_callbacks()
        self.configure_upload()

    def set_callbacks(self):
        self.app.callback(
            Output(self._modal_for_shutdown, "opened"),
            [
                Input(self._shutdown, "n_clicks"),
                Input(self._shutdown_close, "n_clicks")
            ],
            [
                State(self._modal_for_shutdown, "opened")
            ]
        )(lambda _, __, opened: False if not (_ or __) else not opened)

        self.app.callback(
            [
                Output(self.final_step, "opened"),
                Output(self.for_file_upload, "children")
            ],
            [
                Input(self.upload_header, "title"),
                Input(self.cancel_final_step, "n_clicks")
            ],
            State(self.final_step, "opened")
        )(self._handle_final_step)

        self.app.callback(
            Output(self.exams, "value"),
            Input(self.final_step, "opened")
        )(lambda _: None)  # FIXME: without this long_callback was called again

        self.app.callback(
            Output(self.alert_for_start, "children"),
            Input(self.result_for_process, "data")
        )(self._process_results)

        self.app.callback(
            Output(self._download_feed, "data"),
            [
                Input(self._sample_input_dropdown, "n_clicks"),
                Input(self._sample_output_dropdown, "n_clicks"),
                Input(self._result, "n_clicks")
            ],
            State(self.result_for_process, "data")
        )(self._download_feeder)

    def configure_upload(self):
        self.temp.mkdir(exist_ok=True)
        du.configure_upload(self.app, str(self.temp))

    def set_layout(self):
        self.app.layout = dmc.MantineProvider(html.Article(
            [
                self._header(),
                self.body(),
                self.notifications(),
                self._modals(),
                dcc.Store(id=self.result_for_process),
                dcc.Download(id=self._download_feed)
            ],
            id=self.loading_overlay
        ), theme={"colorScheme": "dark"})

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
                            "Results ⭐", header=True
                        ),
                        dbc.DropdownMenuItem(
                            "Fetch Results", n_clicks=0, id=self._result
                        ),
                        dbc.DropdownMenuItem(
                            "Shutdown", n_clicks=0, id=self._shutdown
                        ),
                    ],
                    menu_variant="dark",
                    nav=True,
                    in_navbar=True,
                    color="info",
                    align_end=True,
                    label="Results ⭐"
                ),
                dmc.Switch(
                    label="Auto Check Updates",
                    onLabel="Yes",
                    offLabel="No",
                    color="orange",
                    size="md"
                )
            ],
            brand="CO-PO Mapping",
            brand_href="https://github.com/Tangellapalli-Srinivas/CO-PO-Mapping",
            light=False,
            dark=True
        )

    def body(self):
        return html.Section(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.Label("Upload the Data File", id=self.upload_header),
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
                                )
                            ],
                            style={
                                "width": "100%"
                            }
                        )
                    ]
                )
            ], className="actual-body"
        )

    def notifications(self):
        return dmc.NotificationsProvider(
            [
                *(
                    html.Div(
                        id=_
                    )
                    for _ in (self.for_file_upload, self.for_process)
                )
            ],
            zIndex=2,
            position="bottom-right",
            limit=100
        )

    def _modals(self):
        return html.Div([
            dmc.Modal(
                title="Want to Shutdown ?",
                id=self._modal_for_shutdown,
                children=[
                    dmc.Text("Closing Engine may stop all the running tasks!"),
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
            ),
            dmc.Modal(
                title="Uploaded",
                centered=True,
                closeOnClickOutside=False,
                withCloseButton=False,
                closeOnEscape=False,
                id=self.final_step,
                children=[
                    dmc.NumberInput(
                        label="No. of Exams",
                        description="Enter the Number of Exams conducted",
                        required=True,
                        min=1,
                        max=100,
                        id=self.exams
                    ),
                    dmc.Space(h=20),
                    dmc.Alert(
                        "Submitting now, will start a process where your results are processed",
                        title="Note", color="violet", variant="filled"
                    ),
                    dmc.Space(h=10),
                    dmc.Alert(
                        "Closing now, will delete the file uploaded."
                        " And if the process is started it will also be cancelled",
                        title="Note", color="red", variant="filled"
                    ),
                    dmc.Space(h=20),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Submit",
                                class_name="custom-butt",
                                id=self.confirm_process
                            ),
                            dmc.Button(
                                "Close",
                                color="red",
                                variant="outline",
                                id=self.cancel_final_step
                            )
                        ],
                        position="right"
                    ),
                    dmc.Space(h=20),
                    html.Section(
                        id=self.alert_for_start
                    )
                ]
            )
        ], id="modals")

    def _handle_final_step(self, title, _, opened):
        if not title:
            return no_update, no_update

        if ctx.triggered_id == self.cancel_final_step:
            note = pathlib.Path(title)
            note.unlink() if note.exists() else ...
            parent = note.parent

            if parent.exists() and not list(parent.iterdir()):
                parent.rmdir()

            return False, show_notifications(
                "Cancelled Final Step",
                "File was deleted, if the process was started, is cancelled.",
                color="orange",
                auto_close=6000
            )

        return not opened, no_update

    def _process_results(self, raw):
        loaded = json.loads(raw)

        result_type = loaded.get("type", 0)

        if result_type == 4:
            return dmc.Alert(
                "Regarding your recent process, You can view the results in the NavBar",
                title="Results ⭐",
                color="orange",
                duration=6900,
                variant="outline"
            )

        elif result_type == 1:
            return dmc.Alert(
                "Please Enter the Number of Exams Conducted",
                title=set_timestamp("Missing Number of Exams"),
                duration=4000,
                color="red",
                variant="outline"
            )

        elif result_type == 2:
            return dmc.Alert(
                dmc.Text([
                    "It seems we are missing the file that was uploaded before."
                    "This could be due to 2 reasons:",
                    dmc.List([
                        dmc.ListItem(
                            "After Processing, File will be deleted as the last step (in order to delete unused files)"
                        ),
                        dmc.ListItem(
                            [
                                "Maybe file was not uploaded onto server, if this issue persists,"
                                " Please raise the issue in the ", html.A("Repo.", href=self.repo)
                            ]
                        )
                    ], type="ordered"),
                ]),
                title=set_timestamp("File Not Found"),
                withCloseButton=True,
                color="red",
                variant="outline"
            )

        elif result_type == 3:
            return dmc.Alert(
                "Please Download the raw file from the NavBar in Home page",
                title=set_timestamp("Error in Processing the request"),
                withCloseButton=True,
                color="red",
                variant="outline"
            )

        return dmc.Alert(
            "Invalid Response, Please try uploading file again!, if this issue persists, please raise an issue",
            title=set_timestamp("Rare Issue found 😲"),
            color="red",
            withCloseButton=True,
            variant="outline"
        )

    def _download_feeder(self, _, __, ___, data):
        if not any((_, __, ___)):
            return no_update

        if ctx.triggered_id == self._sample_input_dropdown:
            return dcc.send_file("assets/Sample Input.xlsx", filename="Sample Input.xlsx")

        if ctx.triggered_id == self._sample_output_dropdown:
            return dcc.send_file("assets/Sample Output.txt", filename="Sample Output.txt")

        raw = json.loads(data if data else "{}")

        handler, path = tempfile.mkstemp(suffix=".txt")
        os.close(handler)

        name = "Results" if raw.get("type", 3) == 4 else "Error"
        pathlib.Path(path).write_text(raw.get("results", ""))

        Timer(6000, lambda p=path: pathlib.Path(p).unlink() if pathlib.Path(p.exists()) else None).start()
        return dcc.send_file(path, filename=name + ".txt")


def set_timestamp(title):
    return title, dmc.Text(time_format(), size="xs")


def time_format():
    return datetime.datetime.now().strftime("%H:%M:%S")


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


core = CoreApplication()


@du.callback(
    output=Output(core.upload_header, "title"),
    id=core.upload_button
)
def upload_status(status):
    if not status:
        return ""
    return status[0]


@core.app.long_callback(
    output=Output(
        core.result_for_process, "data"
    ),
    inputs=[
        Input(core.confirm_process, "n_clicks")
    ],
    state=[
        State(core.exams, "value"),
        State(core.upload_header, "title")
    ],
    running=[
        (Output(core.confirm_process, "disabled"), True, False),
        (Output(core.confirm_process, "children"), "Processing...", "Process")
    ],
    cancel=[Input(core.cancel_final_step, "n_clicks")],
    prevent_initial_call=False
)
def process_input(_, exams, path):
    print("called", _, exams, path)

    if not _:
        return no_update

    if not exams:
        return json.dumps({"type": 1})

    uploaded = pathlib.Path(path)

    if not uploaded.exists():
        return json.dumps({"type": 2})

    try:
        parser = Engine()
        results = parser.actual_parse(uploaded, exams)
    except Exception as error:
        results = "", error

    r_type = 4

    if results[-1]:
        r_type = 3
        results = f"""
Results from STDOUT:
--------------------

{results[0]}

Results from STDERR:
--------------------

{results[-1]}
"""

    else:
        results = results[0]

    return json.dumps({"type": r_type, "results": results})


def close_main_thread_in_good_way(wait=0.9):
    logging.warning("Shutting down....")
    return Timer(wait, lambda: interrupt_main()).start()


def open_local_url(port_, wait=1, postfix=""):
    logging.info("Requested to open %s", f"http://localhost:{port_}/" + postfix)
    return Timer(wait, lambda: webbrowser.open(f"http://localhost:{port_}/" + postfix)).start()


def get_free_port():
    logging.info("Getting a free port")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        port_ = sock.getsockname()[1]
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return port_


if __name__ == "__main__":
    port = get_free_port()
    open_local_url(port)
    core.app.run_server(port=port, debug=True, host="localhost")
