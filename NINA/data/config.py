"""Configuration for the bot.

This file contains the configuration for the bot.
It loads from a TOML file, and provides a class to access the config.

Typical usage example:
    ```py
    from NINA.data import config
    cnfg = config.Config()
    print(cnfg["guild"])
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import tomllib
from typing import overload

import discord

from NINA.data import const

BURNABLE = False


class Config(dict):
    """Configuration class for the bot.

    This class is used to access the configuration for the bot.
    It loads from a TOML file, and provides a dictionary-like interface.

    Attributes:
       All attributes are inherited from the superclass.
    """

    def __init__(self):
        """Initializes the config.

        We just init the superclass, and load the config from the TOML file into it.
        """
        super().__init__()
        with open(const.PROG_DIR.joinpath("config.toml"), "rb") as f:
            self.update(tomllib.load(f))

    @overload
    async def guild(self, instance: discord.Client) -> discord.Guild:
        ...

    @overload
    async def guild(self, instance: None) -> int:
        ...

    async def guild(self, instance: discord.Client | None = None) -> int | discord.Guild:
        """Returns the dev guild ID, or object.

        This is a function to allow for the Client object to be passed.
        If the Client object is passed, it returns the guild object.
        Otherwise, it returns the guild ID.
        """
        gld = self["guild_id"]
        if instance is not None:
            gld = await instance.fetch_guild(gld)
        return gld


class Secret:
    """Class for sensitive data.

    This class is used to access sensitive data.
    It loads from a TOML file, and provides a throwaway access key. After
    the key is used, the data in this class is deleted.

    Attributes:
        token: The bot token.
    """

    def __init__(self):
        """Initializes the secret.

        We just load the secret from the TOML file.
        And then set the BURNABLE flag to True.
        """
        global BURNABLE
        if BURNABLE:
            raise RuntimeError("Secret already burnt!")
        with open(const.PROG_DIR.joinpath("secret.toml"), "rb") as f:
            self.secrets = tomllib.load(f)
        BURNABLE = True

    def token(self) -> str:
        """Returns the bot token.

        Fetches the bot token from the secrets, and then deletes the secrets.
        """
        token = self.secrets["token"]
        del self.secrets
        return token
