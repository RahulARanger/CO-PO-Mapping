import sys

print(sys.path)
sys.path = sys.path[: 2] + sys.path[5: ]
print(sys.path)

import urllib.error
from typing import Union, List
from CO_PO.misc import get_free_port, open_local_url, auto_update
from CO_PO.main import Server, app
from waitress import serve
from CO_PO import __version__
from urllib.request import urlopen
import json
import subprocess
import pathlib


def get_version():
    with urlopen("https://api.github.com/repos/Tangellapalli-Srinivas/CO-PO-Mapping/releases/latest") as response:
        parsed = json.loads(response.read())
        return parsed["tag_name"]


def call_shell(mode, get_args=False, *arg) -> Union[subprocess.Popen, List]:
    args = ["powershell.exe", "-file", str(pathlib.Path(__file__).parent.parent / "gate.ps1"), "-mode", str(mode)]

    if arg:
        args.append("-arguments")
        args.extend(arg)

    args.insert(3, "-WindowStyle")
    args.insert(4, "Hidden")

    if get_args:
        return args
    return subprocess.Popen(
        args,
        close_fds=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )


def call_shell_wait(message):
    args = call_shell(4, True, message)
    return subprocess.run(args, close_fds=True)


stop = True
try:
    assert get_version().startswith("v0.0")
    stop = False
except AssertionError as error:
    call_shell_wait("Trial Version Expired!, Uninstalling Files...")
except urllib.error.HTTPError as _:
    call_shell_wait(str(_.reason) + "\nPlease check your internet connection.")
except urllib.error.URLError as _:
    call_shell_wait(str(_.reason) + "\nPlease check your internet connection.")
except Exception as _:
    call_shell_wait(str(_))

if stop:
    exit(0)

if __name__ == "__main__":
    server = Server(get_free_port())

    open_local_url(server.port)

    app.add_url_rule("/", view_func=server.main_route)

    app.add_url_rule("/close-session", view_func=server.close_session)
    app.add_url_rule("/submit-input", view_func=server.submit_input, methods=["POST"])
    app.add_url_rule("/get-status", view_func=server.get_status)
    app.add_url_rule("/restart", view_func=server.force_restart)
    app.add_url_rule("/start-engine", view_func=server.start_engine)
    app.add_url_rule("/wait-for-processing", view_func=server.wait_for_processing)

    serve(app, port=server.port)
    call_shell(2, False, __version__) if auto_update(True).get("auto_update", False) else ...
