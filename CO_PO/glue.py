from dash import html, no_update, dcc, Input, State, Output, ClientsideFunction
import dash_mantine_components as dmc
from CO_PO.AppConfig import BaseApplication
from CO_PO.Components.card import Card
from CO_PO import __version__
from CO_PO.Components.notify import show_notifications, time_format
import dash_uploader as du
import pathlib


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
        self._settings = "__settings"
        self._s_check = "__last_status_check"
        self._ask_help = "__ask_help"

        self._modal_id = "_modal"

        super().__init__()

    def gen_tip(self, for_element, help_text, pos="right", place="start", width=None):
        return dmc.Tooltip(
            children=for_element,
            wrapLines=True,
            label=help_text,
            position=pos,
            color="blue",
            withArrow=True,
            placement=place,
            style={"width": "100%"},
            id=self._tool_tips(),
            width=width
        )

    def get_modal(self, title, children, button_id, centered=True, z_index=4):
        _modal_id = self._modal_id + button_id

        self.app.clientside_callback(
            ClientsideFunction(
                namespace="modal",
                function_name="decide_modal"
            ),
            Output(_modal_id, "opened"),
            Input(button_id, "n_clicks"),
            State(_modal_id, "opened")
        )

        return dmc.Modal(
            title=title,
            children=children,
            centered=centered,
            id=_modal_id, zIndex=z_index
        )

    def set_modal(self, button_id):
        _modal_id = self._modal_id + button_id

    def _header(self):
        return dmc.Header(dmc.Group(
            [
                self.gen_tip(
                    dcc.Link(
                        dmc.Title(
                            ["CO-PO Mapping", html.Sub(
                                __version__.lower()
                            )], order=3
                        ),
                        href=self.repo,
                        target='_blank',
                        id="__name",
                        title="Redirects to Related GitHub Repo."
                    ),
                    "Redirects to GitHub Repo., Place where you can file issues / errors / see the releases, etc...",
                    "bottom",
                    "start"
                ), dmc.Group([
                self.gen_tip(
                    dmc.ActionIcon(
                        children="⚙", id=self._settings
                    ),
                    "Settings, You can clear cache, set auto-update, etc...",
                    "bottom", "center"
                ),
                dmc.Menu(
                    [
                        dmc.MenuLabel("Help"),
                        dmc.MenuItem("Docs", color="teal"),
                        dmc.MenuItem("About", color="orange"),
                        dmc.MenuItem("ChangeLog", color="orange"),
                        dmc.Divider(),
                        dmc.MenuItem("Sample Input", color="yellow", id=self._sample_input_dropdown),
                        dmc.MenuItem("Sample Output", color="green", id=self._sample_output_dropdown)
                    ], withArrow=True, size="md", shadow="lg", trigger="hover"
                ),
                dmc.ActionIcon(
                    dmc.Image(
                        src="assets/shutdown.svg"
                    ), id=self._shutdown
                ),
                dmc.Switch(
                    label="Show Help",
                    onLabel="Yes",
                    offLabel="No",
                    color="orange",
                    size="sm",
                    checked=False,
                    id=self._ask_help
                )
            ], align="center")]
            , position="apart", align="center"))

    def _settings_modal(self):
        body = dmc.Group([
            dmc.Alert(
                [
                    dmc.Group(
                        [
                            dmc.Text(
                                "Engine's status can either be loading or free or processing.", size="sm"
                            ),
                            dmc.Button(
                                "Check Status", variant="outline", color="orange", id=self._check_input, size="xs",
                                radius="xs"),
                            dmc.Text(time_format("Last checked at: "), color="orange", size="xs", id=self._s_check)
                        ], align="flex-end"
                    )
                ], color="teal", title="Engine Status", variant="outline"
            ),
            dmc.Alert(
                dmc.Group(
                    [
                        dmc.Text(
                            "Uploaded files are stored in your hard disk. It is possible they are not cleared properly."
                            " By this option you can force clear those files.", size="sm"),
                        dmc.Button("Clear Cache", variant="outline", color="orange", id=self._clear_cache, size="xs"),
                    ], align="center", position="right"
                ), title="Clear Cache", color="violet", variant="outline"
            ),
            dmc.Switch(
                label="Auto Check Updates",
                onLabel="Yes",
                offLabel="No",
                color="orange",
                id=self.auto_update,
                checked=self.settings[self.auto_update]
            )
        ], spacing="sm", direction="column", align="stretch")

        return self.get_modal(
            "Settings ⚙",
            body,
            self._settings, z_index=2
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
        card = Card()
        card.header = "Upload the Date File"
        card.footer = [
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

        card.body = dmc.Group(
            [
                # max size: 1GB (default)
                self.gen_tip(
                    du.Upload(
                        id=self.upload_button,
                        filetypes=[
                            "xlsx"
                        ]
                    ),
                    "You can upload excel .xlsx file here. Make sure it follows the format."
                ),
                html.Em(
                    dmc.Highlight(
                        "Only .xlsx files are allowed",
                        highlight=[".xlsx", "allowed"],
                        highlightColor="orange", size="xs", align="right"
                    )
                ),
                dmc.TextInput(label="Uploaded File", required=True, disabled=True, id=self.uploaded),
                self.gen_tip(
                    dmc.NumberInput(
                        label="No. of Exams",
                        description="Enter the Number of Exams conducted",
                        required=True,
                        min=1,
                        max=100,
                        id=self.exams
                    ),
                    "This is where we give Number of Examinations", place="end"
                ),
                dmc.ActionIcon(
                    dmc.Image(src="/assets/help.svg", alt="Get Help"),
                    class_name="position-absolute top-0 start-100 translate-middle",
                    id=self._help_for_input
                )
            ], spacing="xs", direction="column", position="center", align="stretch")

        return html.Section(card(), className="actual-body")


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
            zIndex=4,
            position="bottom-right",
            limit=100
        )


class ModelsComponent(NotificationComponents):
    def __init__(self):
        # -> Modals
        self.final_step = "__modal_for_process"

        # --> Modals Components
        self._shutdown = "__shutdown"
        self._shutdown_close = "__close_modal"
        self.confirm_shutdown = self._shutdown + "confirm"
        self.confirm_process = "confirm_process"
        self.confirm_clear = "_confirm_clear"
        self._files = "__files_"
        self._total_size = "__total_size"

        super().__init__()

    def _for_shutdown(self):
        return self.get_modal(
            "Want to Shutdown ?",
            [
                dmc.Text("Closing this Application may stop all the running tasks!"),
                dmc.Space(h=20),
                dmc.Group(dmc.Button("Shutdown", id=self.confirm_shutdown, color="red"), position="right"),
            ],
            self._shutdown, False
        )

    def _help_for_input_modal(self):
        return self.get_modal(
            "Help for Upload", dcc.Markdown(
                (self.docs / "input.md").read_text()
            ), self._help_for_input
        )

    def _clear_cache_modal(self):
        return self.get_modal(
            "Clear Cache",
            [
                dmc.Alert(
                    "Make sure no processes are currently running. As this could clear the files that are currently "
                    "in use by the application.",
                    color="red",
                    title="Note Before",
                    variant="filled"
                ),
                dmc.Space(h=15),
                dmc.Group(
                    [
                        dmc.Badge(
                            "Files: 0",
                            color="violet", size="lg", id=self._files
                        ),
                        dmc.Badge(
                            "Total Size: 0MB",
                            color="violet", size="lg", id=self._total_size
                        ),
                        dmc.Button(
                            "Delete Cache",
                            class_name="custom-butt",
                            style={
                                "float": "right"
                            },
                            id=self.confirm_clear
                        )
                    ], spacing="md", align="center", position="right", noWrap=True
                )
            ],
            self._clear_cache
        )

    def _modals(self):
        return html.Div([
            self._for_shutdown(),
            self._help_for_input_modal(),
            self._clear_cache_modal(),
            self._settings_modal()
        ], id="modals")
