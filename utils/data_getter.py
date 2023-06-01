import json
import os
import re

import requests

from typing import Union, Dict, List

from .pathutils import from_root
from .basiclogger import log, log_success, log_failure, log_info, log_error, log_warning, is_debug, LOGLEVEL


def load_ignored_games():
    ignore_path = from_root(os.path.join("cache", "ignored_game_ids.json"))
    try:
        with open(ignore_path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError as e:
        log_failure(LOGLEVEL.DEBUG, "Ignored games cache file doesn't exist")
    except (IOError, json.JSONDecodeError) as e:
        log_failure(LOGLEVEL.DEBUG, "Couldn't parse ignored games cache, clearing it")
        os.remove(ignore_path)

    return set()


def get_game_id_info():
    log_info(LOGLEVEL.DEBUG, "Loading all game names")

    req = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

    result = requests.get(
        url=req
    )

    if result.status_code == 200:
        try:
            return json.loads(result.content)["applist"]["apps"]
        except json.JSONDecodeError as e:
            log_error(LOGLEVEL.INFO, "Couldn't parse result of Steam games query for cache")
            return None
    else:
        log_error(LOGLEVEL.INFO, "Failed to get list of Steam games for cache")
        return None


def steam_ids_to_names(games: List[int]) -> Union[None, Dict[int, str]]:
    log_info(LOGLEVEL.DEBUG, "Getting steam game IDs -> names")

    cache_path = from_root(os.path.join("cache", "steam_game_names.json"))
    ignore_ids = load_ignored_games()

    cached_info = {}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_info = json.load(f)

        log_info(LOGLEVEL.DEBUG, "id->name cache is valid")
    except FileNotFoundError as e:
        log_failure(LOGLEVEL.DEBUG, "id->name cache file doesn't exist")
    except (IOError, json.JSONDecodeError) as e:
        log_failure(LOGLEVEL.DEBUG, "Couldn't parse id->name cache, clearing it")
        os.remove(cache_path)

    ids_to_names = {
        **{int(gameid): cached_info[str(gameid)] for gameid in games if str(gameid) in cached_info and gameid not in ignore_ids}
    }

    if any(game not in ids_to_names and game not in ignore_ids for game in games):
        log_info(LOGLEVEL.DEBUG, "Some games not in id->name cache, recaching")
        load_result = get_game_id_info()

        new_cache = {}
        for entry in load_result:
            appid = str(entry["appid"])
            name = str(entry["name"])

            new_cache[appid] = name
            if int(appid) not in ids_to_names and int(appid) in games and int(appid) not in ignore_ids:
                ids_to_names[int(appid)] = name

        log_info(LOGLEVEL.DEBUG, "Writing new id->name cache")

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(new_cache, f)
    else:
        log_info(LOGLEVEL.DEBUG, "No id->name cache misses")

    # If there are still some games left we haven't got, we need to ignore them because they aren't in the full list
    for game in games:
        if game not in ids_to_names:
            ignore_ids.add(game)

    ignore_path = from_root(os.path.join("cache", "ignored_game_ids.json"))
    with open(ignore_path, "w", encoding="utf-8") as f:
        json.dump(list(ignore_ids), f)

    return ids_to_names


def get_steam_playtimes(apikey, steamid) -> Union[None, Dict[int, int]]:
    log_info(LOGLEVEL.DEBUG, "Loading steam playtimes")

    ignore_ids = load_ignored_games()

    req = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?" \
          "key={apikey}&steamid={steamid}&include_played_free_games=true&format=json".format(
        apikey=apikey, steamid=steamid
    )

    result = requests.get(
        url=req
    )

    if result.status_code == 200:
        try:
            data = json.loads(result.content)
            playtimes = {
                d["appid"]: d["playtime_forever"] for d in data["response"]["games"] if d["appid"] not in ignore_ids
            }

            return playtimes
        except json.JSONDecodeError as e:
            log_error(LOGLEVEL.CRITICAL, "Couldn't parse result of playtimes query (check Steam ID and API key)")
            return None
    else:
        print(steamid)
        log_error(LOGLEVEL.CRITICAL, "Failed to get playtimes for {} (check Steam ID and API key)".format(
            steamid
        ))

        return None


def get_game_filesizes(steamlibs, games) -> Dict[int, int]:
    log_info(LOGLEVEL.DEBUG, "Getting steam game sizes")

    cache_path = from_root(os.path.join("cache", "game_filesize_cache.json"))
    ignore_ids = load_ignored_games()

    cached_info = {}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_info = json.load(f)

        log_info(LOGLEVEL.DEBUG, "size cache is valid")
    except FileNotFoundError as e:
        log_failure(LOGLEVEL.DEBUG, "size cache file doesn't exist")
    except (IOError, json.JSONDecodeError) as e:
        log_failure(LOGLEVEL.DEBUG, "Couldn't parse size cache, clearing it")
        os.remove(cache_path)

    ids_to_sizes = {
        **{gameid: int(cached_info[str(gameid)]) for gameid in games if str(gameid) in cached_info and gameid not in ignore_ids}
    }

    cache_misses = list(filter(
        lambda game: int(game) not in ids_to_sizes and int(game) not in ignore_ids,
        games
    ))

    if len(cache_misses) > 0:
        log_info(LOGLEVEL.DEBUG, "Some games not in size cache, recaching")

        new_cache = {
            **ids_to_sizes
        }

        for gameid in cache_misses:
            manifest_filename = "appmanifest_{}.acf".format(gameid)
            location = None
            for steamlib in steamlibs:
                p = os.path.join(steamlib, manifest_filename)
                if os.path.isfile(p):
                    location = p
                    break

            if location:
                with open(location, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r'^.*"SizeOnDisk".*"(.*)".*$', content, flags=re.M)
                    if match:
                        sizeondisk = int(match.group(1))
                        log_info(LOGLEVEL.DEBUG, "game ID {}: caching size {}".format(
                            gameid, sizeondisk
                        ))

                        ids_to_sizes[int(gameid)] = sizeondisk
                        new_cache[gameid] = sizeondisk
                    else:
                        log_failure(LOGLEVEL.INFO,
                                    "Game ID {} has a corrupted manifest. Will ignore in future.".format(
                                        gameid
                                    ))
            else:
                log_failure(LOGLEVEL.DEBUG, "Couldn't find game ID {} in any library. Will ignore in future.".format(
                    gameid
                ))

        log_info(LOGLEVEL.DEBUG, "Writing new size cache")

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(new_cache, f)
    else:
        log_info(LOGLEVEL.DEBUG, "No size cache misses")

    # If there are still some games left we haven't got, we need to ignore them because they aren't in the full list
    for game in games:
        if game not in ids_to_sizes:
            ignore_ids.add(game)

    ignore_path = from_root(os.path.join("cache", "ignored_game_ids.json"))
    with open(ignore_path, "w", encoding="utf-8") as f:
        json.dump(list(ignore_ids), f)

    return ids_to_sizes
