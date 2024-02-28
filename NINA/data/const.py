"""Constants for the bot.

This module contains constants for the bot. These constants are used
throughout the bot and are not meant to be changed by the user.

Typical usage example:
    ```py
    from NINA.data import const
    print(const.VERSION)
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import logging.handlers
import pathlib

import colorama
import discord

VERSION = "v0.1.0a"
"""The current version of the bot as a string.

FORMAT:
v[major].[minor].[release][build (optional letter)]

MAJOR and MINOR version changes can be compatibility-breaking.
Compatibility-breaking changes are changes that require manual intervention
by the USER to update the bot. Internal changes that do not require
manual intervention by the USER are not considered compability-breaking.
"""
PROG_DIR = pathlib.Path(__file__).parent.parent.parent.absolute()
"""The absolute path to the root directory of the bot."""
INTENTS = discord.Intents.default()
"""The discord gateway intents that the bot uses."""
HANDLER = logging.handlers.RotatingFileHandler(
    filename=pathlib.Path(PROG_DIR, "log", "bot.log"),
    encoding="utf-8",
    mode="w",
    backupCount=10,
    maxBytes=100000,
)
"""The default logging handler for the bot."""
OK = colorama.Fore.GREEN + "OK" + colorama.Fore.RESET
"""The string to print when something is OK."""
FAILED = colorama.Fore.RED + colorama.Style.BRIGHT + "FAILED" + colorama.Style.RESET_ALL
"""The string to print when something fails."""
ALL_OK = colorama.Fore.GREEN + colorama.Style.BRIGHT + "ALL OK" + colorama.Style.RESET_ALL
"""The string to print when everything is OK."""
