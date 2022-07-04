import json
import os
import threading
import traceback
import dash_uploader as du
import pathlib
import string
import datetime
import random
from dash import Dash, html, Input, Output, ctx, no_update, State, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import typing
from CO_PO.parse_excel_file import Engine
import tempfile
from _thread import interrupt_main
import socket
import logging
import webbrowser
from waitress import serve
import subprocess
from CO_PO import __version__

logging.basicConfig(
    level=logging.INFO
)


class CoreApplication:
    def handle_settings(self, save=None):
        if not save:
            return json.loads(self.settings_path.read_text())

        self.settings.update(save)
        self.settings_path.write_text(json.dumps(self.settings))
        return self.settings

    def __init__(self):
        self.settings_path = pathlib.Path(__file__).parent / "settings.json"
        self.settings = self.handle_settings()
        self.docs = self.settings_path.parent / "docs"
        # All Constants
        # Samples

        self.assets = self.settings_path.parent / "assets"
        self._sample_input = str(self.assets / "Sample Input.xlsx")
        self._sample_output = str(self.assets / "Sample Output.txt")

        self._sample_input_dropdown = "__dropdown_sample_input"
        self._sample_output_dropdown = "__dropdown_sample_output"
        self._download_feed = "__download_feed"

        # -> Slider
        self.auto_update = "auto_update"

        # -> Loading Overlay
        self.loading_overlay = "__loading_overlay"

        # -> Button Constants
        self._fetch = "__fetch_status"
        self._shutdown = "__shutdown"

        # --> Upload Button Constant
        self.upload_button = "__upload"

        # -> Notifications
        self.for_file_upload = "__for_file_upload"
        self.for_shutdown = "__for_shutdown"
        self.for_process = "__for_process"

        # -> Modals
        self._modal_for_shutdown = "__modal_for_shutdown"
        self.final_step = "__modal_for_process"
        # --> Modals Components
        self._shutdown_close = "__close_modal"
        self.confirm_shutdown = self._shutdown + "confirm"
        self.confirm_process = "confirm_process"

        # -> DropDownMenu
        self._result = "__result"

        # -> Input
        self.exams = "__exams"
        self.uploaded = "__uploaded"

        self._check_input = "__check_input"

        # -> Repo URL
        self.repo = "https://github.com/RahulARanger/CO-PO-Mapping"

        # -> Output
        self.result_for_process = "result_memory"

        self.temp = pathlib.Path(__file__).parent / "temp"

        # Help Components
        self._help_for_input = "help_input"

        self.app = Dash(__name__)
        self.engine = Engine()

        self.set_layout()
        self.set_callbacks()
        self.configure_upload()

        if not self.engine.loading.locked():
            threading.Thread(
                target=self.engine.load,
                name="Loading Engine"
            ).start()

    def set_callbacks(self):
        self.app.callback(
            Output(self._modal_for_shutdown, "opened"),
            Output(self.for_shutdown, "children"),
            [
                Input(self._shutdown, "n_clicks"),
                Input(self._shutdown_close, "n_clicks"),
                Input(self.confirm_shutdown, "n_clicks")
            ],
            [
                State(self._modal_for_shutdown, "opened")
            ]
        )(self._shutdown_this)

        self.app.callback(
            [
                Output(self.uploaded, "value"),
                Output(self.for_file_upload, "children")
            ],
            [
                Input(self.uploaded, "placeholder")
            ],
            [
                State(self.uploaded, "value")
            ]
        )(set_file_path)

        self.app.callback(
            [
                Output(self.for_process, "children"),
                Output(self.result_for_process, "data")
            ],
            [
                Input(self.confirm_process, "n_clicks"),
                Input(self._check_input, "n_clicks")
            ],
            [
                State(self.uploaded, "value"),
                State(self.exams, "value")
            ]
        )(
            self._process_input
        )

        self.app.callback(
            Output(self._download_feed, "data"),
            [
                Input(self._sample_input_dropdown, "n_clicks"),
                Input(self._sample_output_dropdown, "n_clicks"),
                Input(self._result, "n_clicks")
            ],
            State(self.result_for_process, "data")
        )(self._download_feeder)

        self.app.callback(
            Output(self.auto_update, "id"),
            Input(self.auto_update, "checked")
        )(self._set_settings)

        self.app.callback(
            Output(self.final_step, "opened"),
            Input(self._help_for_input, "n_clicks"),
            State(self.final_step, "opened")
        )(
            lambda _, opened: not opened if _ else no_update
        )

    def configure_upload(self):
        self.temp.mkdir(exist_ok=True)
        du.configure_upload(self.app, str(self.temp))

    def set_layout(self):
        self.app.layout = dmc.MantineProvider(dmc.LoadingOverlay(
            [
                self._header(),
                self.body(),
                self.notifications(),
                self._modals(),
                dcc.Store(id=self.result_for_process),
                dcc.Download(id=self._download_feed)
            ],
            id=self.loading_overlay,
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
                            "Engine ⚙", header=True
                        ),
                        dbc.DropdownMenuItem(
                            "Check Status", n_clicks=0, id=self._check_input
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

    def body(self):
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

    def notifications(self):
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

    def _modals(self):
        return html.Div([
            dmc.Modal(
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
            ),
            dmc.Modal(
                title="Help for Upload",
                centered=True,
                id=self.final_step,
                children=dcc.Markdown(
                    (self.docs / "input.md").read_text()
                )
            )
        ], id="modals")

    def _download_feeder(self, _, __, ___, data):
        if not any((_, __, ___)):
            return no_update

        if ctx.triggered_id == self._sample_input_dropdown:
            return dcc.send_file(self.assets / "Sample Input.xlsx", filename="Sample Input.xlsx")

        if ctx.triggered_id == self._sample_output_dropdown:
            return dcc.send_file(self.assets / "Sample Output.txt", filename="Sample Output.txt")

        raw = json.loads(data if data else "{}")

        handler, path = tempfile.mkstemp(suffix=".txt")
        os.close(handler)

        name = "Error" if raw.get("is_error", True) else "Results"
        pathlib.Path(path).write_text(raw.get("results", ""))

        threading.Timer(6000, lambda p=path: pathlib.Path(p).unlink() if pathlib.Path(p.exists()) else None).start()

        return dcc.send_file(path, filename=name + ".txt")

    def _shutdown_this(self, _, __, ___, opened):
        if not any((_, __, ___)):
            return False, no_update

        so = not opened

        if ctx.triggered_id != self.confirm_shutdown:
            return so, no_update

        self.engine.stop_engine()
        close_main_thread_in_good_way()
        return so, show_notifications(
            "Server was closed",
            "You can close this tab and any other tabs that was open with this url.",
            color="orange"
        )

    def _set_settings(self, auto_update):
        if auto_update is None:
            return no_update

        self.handle_settings({
            self.auto_update: bool(auto_update)
        })

        return no_update

    def _process_input(self, _, __, file_path, exams):
        if not (_ or __):
            return no_update, no_update

        if ctx.triggered_id == self._check_input:
            if self.engine.loading.locked():
                note = "Engine is currently loading"
            elif self.engine.processing.locked():
                note = "Engine is currently processing"
            else:
                note = "Engine is free for future use"

            return show_notifications(
                "Engine status",
                note,
                auto_close=6000,
                color="pink"
            ), no_update

        uploaded = pathlib.Path(file_path) if file_path else None

        if not (uploaded and uploaded.exists()):
            return show_notifications(
                "File not uploaded",
                "Please try again after uploading a file."
            ), no_update

        if not exams:
            return show_notifications(
                "Invalid value for exams",
                "Please provide valid number for number of examinations"
            ), no_update

        if self.engine.processing.locked():
            return show_notifications(
                "Please try again later!",
                "Engine is already processing previous request. ",
                dmc.Code("Please start a new process or wait for results."),
                color="red"
            ), no_update

        self.engine.load()

        try:

            results = self.engine.parse(uploaded, exams)
            is_error = bool(results[-1])

        except ValueError as error:
            return show_notifications(
                "Wrong Input",
                dmc.Text(
                    [
                        "It seems Input was not correct, Please refer to this ",
                        html.A("docs", href=self.repo, target="_blank"),
                        ". Meanwhile please download the results to get more idea on error"
                    ],
                )
            ), json.dumps({
                "is_error": True,
                "results": str(error),
            })

        except Exception as error:
            # RARE CASES
            is_error = True
            results = str(error), traceback.format_exc()

        if is_error:
            note = show_notifications(
                "Failed to Process your request",
                "Please refer the Results button to download the results"
            )
        else:
            note = show_notifications(
                "Results are generated successfully",
                "Please refer the Results button to download the results",
                color="green",
                auto_close=4000
            )

        return note, json.dumps({
            "is_error": is_error,
            "results": output_format(*results) if is_error else results[0],
        })


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
        p = old.parent

        if not list(p.iterdir()):
            p.rmdir()

    else:
        note = show_notifications(
            "File Uploaded Successfully",
            "You can use this file for processing. ",
            dmc.Code("Note: only checked for extension .xlsx. not its internal contents"),
            color="green",
            auto_close=3000
        )

    return new_path, note


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
    output=Output(core.uploaded, "placeholder"),
    id=core.upload_button
)
def upload_status(status):
    if not status:
        return ""
    return status[0]


def close_main_thread_in_good_way(wait=0.9):
    logging.warning("Shutting down....")
    threading.Timer(wait, lambda: interrupt_main()).start()


def open_local_url(port_, wait=1, postfix=""):
    logging.info("Requested to open %s", f"http://localhost:{port_}/" + postfix)
    return threading.Timer(wait, lambda: webbrowser.open(f"http://localhost:{port_}/" + postfix)).start()


def get_free_port():
    logging.info("Getting a free port")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        port_ = sock.getsockname()[1]
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return port_


def output_format(stderr="", stdout=""):
    return f"""
STDERR [From Error PIPE]
------------------------
{stderr}

STDOUT [From Output PIPE]
------------------------
{stdout}
"""


def shell_exc(mode, *args):
    arg_s = ["setup", "-mode", mode]

    if args:
        arg_s.extend(["-arguments", *args])

        return subprocess.Popen(
            arg_s,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=core.settings_path.parent.parent,
            start_new_session=True
        )


if __name__ == "__main__":
    port = get_free_port()
    open_local_url(port)
    serve(core.app.server, port=port, host="localhost")

    shell_exc("3")  # to clear cache, if no applications are running
    shell_exc("2", __version__) if core.handle_settings()[core.auto_update] else ...

# if __name__ == "__main__":
#     core.app.run_server(debug=True)
