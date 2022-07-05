import logging
import threading
import webbrowser
from _thread import interrupt_main
import socket
import subprocess
import datetime
import pathlib
import json
from dash import Dash


class BaseApplication:
    def __init__(self):
        self.__app = Dash(__name__)
        self.repo = "https://github.com/RahulARanger/CO-PO-Mapping"

        # Important Folders
        self.settings_path = pathlib.Path(__file__).parent / "settings.json"
        self.settings = self.handle_settings()

        self.docs = self.settings_path.parent / "docs"

        # Some Files
        self.assets = self.settings_path.parent / "assets"
        self._sample_input = str(self.assets / "Sample Input.xlsx")
        self._sample_output = str(self.assets / "Sample Output.txt")

        self.set_layout()
        self.set_callbacks()

    @property
    def app(self):
        return self.__app

    def set_layout(self):
        ...

    def set_callbacks(self):
        ...

    def handle_settings(self, save=None):
        if not save:
            return json.loads(self.settings_path.read_text())

        self.settings.update(save)
        self.settings_path.write_text(json.dumps(self.settings))
        return self.settings


def time_format():
    return datetime.datetime.now().strftime("%H:%M:%S")


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
            cwd=pathlib.Path(__file__).parent.parent,
            start_new_session=True
        )
