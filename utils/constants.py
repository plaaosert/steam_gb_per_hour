import json
import os

from . import pathutils
from .basiclogger import log_failure, log_info, log_error, LOGLEVEL, log_warning

LASTUSE_PATH = pathutils.from_root(os.path.join("config", "last_use"))
LAST_KEY_AND_ID = ""
if os.path.exists(LASTUSE_PATH):
    with open(LASTUSE_PATH, "r") as f:
        LAST_KEY_AND_ID = f.read()

if not os.path.isdir(pathutils.from_root("config")):
    os.mkdir(pathutils.from_root("config"))

if not os.path.isdir(pathutils.from_root("cache")):
    os.mkdir(pathutils.from_root("cache"))

APIKEY_PATH = pathutils.from_root(os.path.join("config", "api_key"))
USERID_PATH = pathutils.from_root(os.path.join("config", "steam_id"))
STEAMLIBS_PATH = pathutils.from_root(os.path.join("config", "steam_libraries.json"))

APIKEY = None
USERID = None
STEAMLIBS = []

log_info(LOGLEVEL.DEBUG, "Loading API key from {}".format(os.path.abspath(APIKEY_PATH)))
if os.path.exists(APIKEY_PATH):
    with open(APIKEY_PATH, "r") as f:
        APIKEY = f.read().split("\n")[0]
else:
    log_error(
        LOGLEVEL.CRITICAL,
        "Tried to find file containing steam web API key (\"{}\") but it did not exist.".format(
            APIKEY_PATH
        )
    )
    exit(1)


log_info(LOGLEVEL.DEBUG, "Loading user ID from {}".format(os.path.abspath(USERID_PATH)))
if os.path.exists(USERID_PATH):
    with open(USERID_PATH, "r") as f:
        USERID = f.read().split("\n")[0]
else:
    log_warning(
        LOGLEVEL.INFO,
        "Didn't load a Steam user ID from {}. Place one there and the program will default to that user ID.".format(
            USERID_PATH
        )
    )


log_info(LOGLEVEL.DEBUG, "Loading steam libraries from {}".format(os.path.abspath(STEAMLIBS_PATH)))
try:
    with open(STEAMLIBS_PATH, "r") as f:
        STEAMLIBS = json.load(f)
except FileNotFoundError as e:
    log_failure(LOGLEVEL.DEBUG, "Steam libraries file doesn't exist")
except (IOError, json.JSONDecodeError) as e:
    log_failure(LOGLEVEL.DEBUG, "Couldn't parse steam libraries file")


if not STEAMLIBS:
    log_warning(
        LOGLEVEL.DEBUG,
        "Didn't load any Steam libraries from {}. "
        "Place one there and the program will default to those library paths.".format(
            STEAMLIBS_PATH
        )
    )
