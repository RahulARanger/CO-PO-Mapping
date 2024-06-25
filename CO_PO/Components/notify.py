import dash_mantine_components as dmc
import typing
import string
import random
import datetime


def time_format(prefix=""):
    return prefix + datetime.datetime.now().strftime("%H:%M:%S")


def set_timestamp(title):
    return title, dmc.Text(time_format(), size="xs")


def show_notifications(title, *message, auto_close: typing.Union[bool, int] = False, color="red", disallow=False):
    return dmc.Notification(
        title=set_timestamp(title),
        color=color,
        autoClose=not disallow and auto_close,
        disallowClose=disallow,
        message=message,
        action="show",
        id="".join(random.choices(string.ascii_letters, k=10))
    )
