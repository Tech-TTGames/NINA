"""This main bot class module for the Project: NINA bot.

A module that contains purely the bot class - `NINABot`.
It's a subclass of `discord.ext.commands.Bot`.
It's not sharded, as it's not meant for use in more than one server.

Typical usage example:
    ```py
    from NINA import bot
    bot_instance = bot.NINABot(...)
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import logging
import pathlib

import aiohttp
import discord
from discord.ext import commands

from NINA import cogs
from NINA.data import config
from NINA.data import const
from NINA.ext import http
from NINA.ext.NINA import Simulation

logger = logging.getLogger("NINA.botcore")


class NINABot(commands.Bot):
    """The main bot class for the Project: NINA bot.

    Subclassing `discord.ext.commands.Bot`, this is the main bot class.F
    It's not sharded, as it's not meant for use in more than one server.
    It is used to share the database engine/pool, and the config.

    Attributes:
        stat_confg: The config for the bot.
    """
    stat_confg: config.Config
    sim: "Simulation | None"
    basp: pathlib.Path

    def __init__(self, *args, confg: config.Config | None, **kwargs) -> None:
        """Initialises the bot instance.

        We prep some stuff for the bot to use, like the config.

        Args:
            *args: The arguments to pass to the superclass.
            db_engine: The database engine.
            confg: The config for the bot.
            **kwargs: The keyword arguments to pass to the superclass.
        """
        if confg is None:
            confg = config.Config()
        super().__init__(*args, **kwargs)
        self.stat_confg = confg
        self.full_tree = None
        headers = {'User-agent': f"{type(self).__name__}/{const.VERSION[1:]}"}
        self.httpsession = aiohttp.ClientSession(headers=headers, middlewares=(http.create_retry_middleware(1),))

    async def setup_hook(self) -> None:
        """Runs just before the bot connects to Discord.

        Sets up the bot for actual use.
        This is used to load the cogs and sync the database.
        Generally, this function should not be called manually.
        """
        logger.info("Project: NINA version: %s", const.VERSION)
        logger.info("Discord.py version: %s", discord.__version__)
        logger.info("Discord username: %s", self.user.name)
        logger.info("Loading cogs...")
        for extension in cogs.EXTENSIONS:
            try:
                await self.load_extension(extension)
            except commands.ExtensionError as err:
                logger.error("Failed to load cog %s: %s", extension, err)
        self.full_tree = await self.tree.fetch_commands()
        logger.info("Finished loading cogs.")

    async def close(self) -> None:
        """Closes the bot.

        This function is used to stop the bot gracefully.
        We additionally clean up the database engine/pool.
        """
        logger.info("Closing bot...")
        await self.httpsession.close()
        return await super().close()
