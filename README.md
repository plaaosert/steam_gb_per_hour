# steam_gb_per_hour
The premier service to find out how many gigabytes those hours are really worth.

## Prerequisites
- You need a Steam Web API key. If you don't have one, get one here: https://steamcommunity.com/dev/apikey. You don't need a valid domain. Just put anything in there, it really doesn't matter.
  - I'm not responsible for the results if it does, at some point, matter. If you're worried, I'd recommend revoking the key right after using it.
  - Copy this into a file called `config/api_key`.

- You'll need the Steam ID of an account (probably yours). There are many ways to get yours, such as https://steamdb.info/calculator/
  - Copy this into a file called `config/steam_id`, or provide it as a command-line parameter (`-u STEAMID`)

- You need to know where your steam library or libraries are on your disk. Chances are you already know, but if you don't: 
  - Rightclick on a game, click **Browse local files...**
  - Move up directories to the `steamapps` folder (usually two directories up)
  - This is the directory you should use - for example, `D:\Steam\steamapps\`.
  - Copy all of these paths into the `config/steam_libraries.json` folder. It should contain paths like this:
```json
[
    "path/to/library",
    "path/to/other/library"
]
```

## Setup
- Get the repository (clone or otherwise).
- Complete the steps in Prerequisites.
- Install the `requests` library if you don't have it (`python -m pip install requests`)
- You're done. To run the program, run `main.py`.

## Compatibility
Probably works on all versions of Python 3.
Haven't tested on Linux, but should work fine.
Open an issue if it doesn't. Thanks.

## Command help output
```
> python main.py -h
                                              -|-
-h                      (--help, -?, ?)        | Show this help message.
                                              -|-
-n                      (--no-cache)           | Delete all caches before starting processing. Use if
                                               | something looks like it's going wrong.
                                              -|-
-p <steam_library_path> (--steam-library-path) | Add a Steam library to the list of Steam libraries used
                                               | to calculate file size. Placing a file called
                                               | "steam_libraries.json" in the "config" directory will
                                               | load those library paths automatically.
                                              -|-
-u <steam_id>           (--user-id)            | Set the Steam user ID used. Placing a file called
                                               | "steam_id" in the "config" directory will make the
                                               | program default to that user ID.
                                              -|-
-v <loglevel>           (--verbosity)          | Set the log level of the program:
                                               | CRITICAL       (0) - silent apart from error messages
                                               | INFO_QUIET     (1) - only important messages
                                               | INFO [default] (2) - relevant information only
                                               | DEBUG          (3) - maximum verbosity
                                              -|-
```
