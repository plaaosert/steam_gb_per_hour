import glob
import inspect
import os
import sys
import textwrap
from typing import Dict, Callable, Optional

from . import constants
from .basiclogger import log_error, LOGLEVEL, set_loglevel
from .pathutils import from_root


class ArgAction:
    def __init__(self, help_str, action):
        self.help_str: str = help_str
        self.action: Callable[[dict, ...], None] = action


def argact_do_nothing(variables):
    return


def argact_enable_help(variables):
    variables["help"] = True


def argact_set_loglevel(variables, loglevel):
    loglevels = (LOGLEVEL.CRITICAL, LOGLEVEL.INFO_QUIET, LOGLEVEL.INFO, LOGLEVEL.DEBUG)
    p_loglevel = None

    if loglevel.isdigit() and 0 <= int(loglevel) <= 3:
        p_loglevel = loglevels[int(loglevel)]
    elif any(loglevel.upper() == loglvl.name.upper() for loglvl in loglevels):
        p_loglevel = next(loglvl for loglvl in loglevels if loglevel.upper() == loglvl.name.upper())
    else:
        log_error(LOGLEVEL.CRITICAL, "Invalid log level provided ({}).".format(loglevel))
        variables["help"] = True

    variables["loglevel"] = p_loglevel


def argact_set_steamid(variables, steam_id):
    variables["steamid"] = steam_id


def argact_add_steamlib(variables, steam_library_path):
    variables["steamlibs"].append(steam_library_path)


def argact_nocache(variables):
    files = glob.glob(os.path.join(from_root("cache"), "*"))
    for f in files:
        os.remove(f)


default_arg_actions: Dict[str, ArgAction] = {
    "-v": ArgAction(
        "Set the log level of the program:\n"
        "CRITICAL       (0) - silent apart from error messages \n"
        "INFO_QUIET     (1) - only important messages \n"
        "INFO [default] (2) - relevant information only \n"
        "DEBUG          (3) - maximum verbosity",
        argact_set_loglevel
    ),

    "-h": ArgAction(
        "Show this help message.",
        argact_enable_help
    )
}

default_arg_aliases: Dict[str, str] = {
    "--verbosity": "-v",
    "--help": "-h",
    "-?": "-h",
    "?": "-h"
}


arg_actions: Dict[str, ArgAction] = {
    **default_arg_actions,
    "-u": ArgAction(
        "Set the Steam user ID used. Placing a file called \"steam_id\" in the \"config\" "
        "directory will make the program default to that user ID.",
        argact_set_steamid
    ),

    "-p": ArgAction(
        "Add a Steam library to the list of Steam libraries used to calculate file size. "
        "Placing a file called \"steam_libraries.json\" in the \"config\" directory will load those library paths "
        "automatically.",
        argact_add_steamlib
    ),

    "-n": ArgAction(
        "Delete all caches before starting processing. Use if something looks like it's going wrong.",
        argact_nocache
    ),
}

arg_aliases: Dict[str, str] = {
    **default_arg_aliases,
    "--user-id": "-u",
    "--steam-library-path": "-p",
    "--no-cache": "-n"
}


def split_preserving_newlines(st, width):
    lines = st.split("\n")
    lists = (textwrap.TextWrapper(width=width).wrap(s) for s in lines)
    body = "\n".join("\n".join(ls) for ls in lists)

    return body


def show_help():
    try:
        terminal_cols = os.get_terminal_size().columns
    except OSError:
        terminal_cols = 80

    sec1_p2_stringlength = len(max([
        "".join(" <{}>".format(arg) for arg in list(
            inspect.signature(arg_actions[act].action).parameters.keys()
        )[1:]) for act in sorted(arg_actions.keys())
    ]))

    sec1_strings = [
        ("{}{:" + str(sec1_p2_stringlength) + "} ({})").format(
            act,
            "".join(" <{}>".format(arg) for arg in list(
                inspect.signature(arg_actions[act].action).parameters.keys()
            )[1:]),
            ", ".join(alias for alias in [v[0] for v in arg_aliases.items() if v[1] == act]),
        ) for act in sorted(arg_actions.keys())
    ]

    sec1_length = len(max(
        sec1_strings, key=len
    ))

    length_left = min(80, terminal_cols - sec1_length - 8) if terminal_cols - sec1_length > 0 else 0
    sec2_strings = [
        split_preserving_newlines(arg_actions[act].help_str, length_left) for act in sorted(arg_actions.keys())
    ]

    final_str = ""
    final_str += "{}-|-\n".format("".ljust(sec1_length))
    for st1, st2 in zip(sec1_strings, sec2_strings):
        for idx, line in enumerate(st2.split("\n")):
            final_str += "{} | {}\n".format(
                (st1 if idx == 0 else "").ljust(sec1_length), line
            )

        final_str += "{}-|-\n".format("".ljust(sec1_length))

    print(final_str)


def parse_args():
    variables = {
        "loglevel": LOGLEVEL.INFO,
        "steamid": constants.USERID,
        "steamlibs": constants.STEAMLIBS,
        "apikey": constants.APIKEY,
        "help": False
    }

    loaded_action: Optional[Callable[[dict, ...], None]] = None
    action_params = []
    num_params = 0

    for arg in sys.argv[1:]:
        if loaded_action:
            if len(action_params) < num_params:
                action_params.append(arg)
            else:
                loaded_action(variables, *action_params)

                loaded_action = None
                action_params = []
                num_params = 0

        if not loaded_action:
            arg_aliased: str = arg
            if arg in arg_aliases:
                arg_aliased = arg_aliases[arg]

            if arg_aliased in arg_actions:
                loaded_action = arg_actions[arg_aliased].action
                action_params = []
                num_params = len(inspect.signature(loaded_action).parameters) - 1

    if loaded_action:
        if len(action_params) <= num_params:
            loaded_action(variables, *action_params)

    set_loglevel(variables["loglevel"])

    return variables
