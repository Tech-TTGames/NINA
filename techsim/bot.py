"""This main bot class module for the TechSim bot.

A module that contains purely the bot class - `TechSimBot`.
It's a subclass of `discord.ext.commands.Bot`.
It's not sharded, as it's not meant for use in more than one server.

Typical usage example:
    ```py
    from techsim import bot
    bot_instance = bot.TechSimBot(...)
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

from techsim import cogs
from techsim.data import config
from techsim.data import const

logger = logging.getLogger("techsim.botcore")


class TechSimBot(commands.Bot):
    """The main bot class for the TechSim bot.

    Subclassing `discord.ext.commands.Bot`, this is the main bot class.
    It's not sharded, as it's not meant for use in more than one server.
    It is used to share the database engine/pool, and the config.

    Attributes:
        stat_confg: The config for the bot.
    """
    stat_confg: config.Config
    sim: "Simulation"
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
        self.httpsession = aiohttp.ClientSession()

    async def setup_hook(self) -> None:
        """Runs just before the bot connects to Discord.

        Sets up the bot for actual use.
        This is used to load the cogs and sync the database.
        Generally, this function should not be called manually.
        """
        logger.info("TechSim version: %s", const.VERSION)
        logger.info("Discord.py version: %s", discord.__version__)
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
