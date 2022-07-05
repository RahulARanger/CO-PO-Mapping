import json
import os
import threading
import traceback
import dash_uploader as du
import pathlib
from dash import html, Input, Output, ctx, no_update, State, dcc
import dash_mantine_components as dmc
from CO_PO.parse_excel_file import Engine
import tempfile
import logging
from waitress import serve
from CO_PO.Components import ModelsComponent, show_notifications, set_file_path
from CO_PO.AppConfig import open_local_url, get_free_port, output_format, close_main_thread_in_good_way, shell_exc
from CO_PO import __version__

logging.basicConfig(
    level=logging.INFO
)


class CoreApplication(ModelsComponent):
    def __init__(self):
        # All Constants
        self._download_feed = "__download_feed"

        # -> Loading Overlay
        self.loading_overlay = "__loading_overlay"

        # -> Output
        self.result_for_process = "result_memory"

        self.temp = pathlib.Path(__file__).parent / "temp"

        super().__init__()
        self.engine = Engine()
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

        self.app.callback(
            Output(self._modal_for_clear_cache, "opened"),
            Input(self._clear_cache, "n_clicks"),
            State(self._modal_for_clear_cache, "opened")
        )(
            self._handle_clear_cache
        )

    def configure_upload(self):
        self.temp.mkdir(exist_ok=True)
        du.configure_upload(self.app, str(self.temp))

    def set_layout(self):
        self.app.layout = dmc.MantineProvider(dmc.LoadingOverlay(
            [
                self._header(),
                self._body(),
                self._notifications(),
                self._modals(),
                dcc.Store(id=self.result_for_process),
                dcc.Download(id=self._download_feed)
            ],
            id=self.loading_overlay,
        ), theme={"colorScheme": "dark"})

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

    def _handle_clear_cache(self, _, opened):
        if not _:
            return no_update

        return not opened


core = CoreApplication()


@du.callback(
    output=Output(core.uploaded, "placeholder"),
    id=core.upload_button
)
def upload_status(status):
    if not status:
        return ""
    return status[0]


if __name__ == "__main__":
    port = get_free_port()
    open_local_url(port)
    serve(core.app.server, port=port, host="localhost")

    shell_exc("3")  # to clear cache, if no applications are running
    shell_exc("2", __version__) if core.handle_settings()[core.auto_update] else ...

# if __name__ == "__main__":
#     core.app.run_server(debug=True)
