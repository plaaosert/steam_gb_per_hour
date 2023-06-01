#!/usr/bin/env python3

import os.path
import sys

from utils import arg_parser, constants, data_getter, pathutils
from utils.basiclogger import log, log_success, log_failure, log_info, log_error, log_warning, is_debug, LOGLEVEL


def print_and_write(fp, *st, end="\n"):
    fp.write(" ".join(s for s in st) + end)
    print(*st, end=end)


variables = arg_parser.parse_args()

apikey = constants.APIKEY
steamid = variables["steamid"]
steamlibs = variables["steamlibs"]

if variables["help"]:
    arg_parser.show_help()
    exit(0)

if not steamlibs:
    log_warning(
        LOGLEVEL.INFO,
        "Didn't find any Steam libraries in {} and none were provided with -p. This won't work.".format(
            constants.STEAMLIBS_PATH
        )
    )

playtimes = data_getter.get_steam_playtimes(apikey, steamid)

if not playtimes:
    log_error(LOGLEVEL.CRITICAL, "Couldn't find any games because the Steam API returned no data. "
                                 "Check your api_key and steam_id files.")
    exit(1)

game_ids = [gameid for gameid in playtimes.keys()]

name_lookups = data_getter.steam_ids_to_names(game_ids)

sorted_playtimes = sorted(playtimes, key=lambda t: -playtimes[t])

game_filesizes = data_getter.get_game_filesizes(steamlibs, game_ids)

sorted_playtimes = list(filter(
    lambda pt: pt in game_filesizes and game_filesizes[pt] > 0 and pt in playtimes and playtimes[pt] > 0,
    sorted_playtimes
))

filesize_values = {
    gameid: (game_filesizes[gameid] / (1000 * 1000 * 1000)) / (playtimes[gameid] / 60) for gameid in sorted_playtimes
}

sorted_sizevalues = sorted(sorted_playtimes, key=lambda t: -filesize_values[t])

if len(sorted_sizevalues) > 0:
    with open("results.log", "w", encoding="utf-8") as f:
        print_and_write(f, "{} games installed and played:\n".format(len(sorted_playtimes)))
        print_and_write(f, "\n".join(
            "{:60}| {:12} | {:40} | {} GB/hr".format(
                name_lookups[gameid],
                "{}h {}m".format(
                    playtimes[gameid] // 60,
                    playtimes[gameid] % 60
                ),
                "{} GB ({} B)".format(round(game_filesizes[gameid] / (1000 * 1000 * 1000), 2), game_filesizes[gameid]),
                round(filesize_values[gameid], 4)
            ) for gameid in sorted_sizevalues
        ))

        avg_value = sum(game_filesizes[gameid] / 1000 / 1000 / 1000 for gameid in sorted_sizevalues) / \
                    sum(playtimes[gameid] / 60 for gameid in sorted_sizevalues)

        print_and_write(f, "\nThe average game size in GB for one hour of your time is {} GB.\n".format(
            round(avg_value, 4)
        ))

        print_and_write(f, "The best value (least GB) per hour played of your games is {} ({} GB/hr).".format(
            name_lookups[sorted_sizevalues[-1]], round(filesize_values[sorted_sizevalues[-1]], 4)
        ))

        print_and_write(f, "The worst value (most GB) per hour played of your games is {} ({} GB/hr).".format(
            name_lookups[sorted_sizevalues[0]], round(filesize_values[sorted_sizevalues[0]], 4)
        ))

        print("The above output has also been written to {}.".format(
            os.path.abspath("results.log")
        ))
else:
    log_error(LOGLEVEL.CRITICAL, "No installed games were found. "
                                 "Check your api_key, steam_id and steam_libraries.json files.")
    log_error(LOGLEVEL.CRITICAL, "Use -h ({} -h) for help.".format(sys.argv[0]))
