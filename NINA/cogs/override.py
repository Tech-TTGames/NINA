"""General powertools for the bot owner.

Tech's standardized bot override cogs.
This cog contains commands that are only available to the bot owner.
These commands are used to reload cogs, restart the bot, and pull from git.
The commands are only available in the development guild, as specified in
the config.

Typical usage example:
    ```py
    from NINA import bot
    bot_instance = bot.NINABot(...)
    await bot_instance.load_extension("NINA.cogs.override")
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from NINA import bot
from NINA import cogs
from NINA.data import config
from NINA.data import const
from NINA.ext import checks
from NINA.ext import views

_CNFG = config.Config()
"""Submodule private global constant for the config."""
logger = logging.getLogger("NINA.override")


@app_commands.guilds(_CNFG["guild_id"])
class Overrides(commands.GroupCog, name="override", description="Owner override commands."):
    """Owner override commands.

    This class contains commands that are only available to the bot owner.
    These commands are used to reload cogs, restart the bot, and pull from git.
    The commands are only available in the development guild, as specified in
    the config.
    """

    def __init__(self, bot_instance: bot.NINABot):
        """Initializes the cog.

        This method initializes the cog.
        It also sets the bot instance as a private attribute.
        And finally initializes the superclass.

        Args:
            bot_instance: The bot instance.
        """
        self._bt = bot_instance
        super().__init__()
        logger.info("Loaded %s", self.__class__.__name__)

    @app_commands.command(name="reload", description="Reloads the bot's cogs.")
    @checks.is_owner_check()
    @app_commands.describe(sync="Syncs the tree after reloading cogs.")
    async def reload(self, ctx: discord.Interaction, sync: bool = False) -> None:
        """Reloads the bot's cogs.

        This command reloads all cogs in the EXTENSIONS list.
        Reloads are atomic, so if one fails, it rolls back.
        We can just import this submodule and iterate over the EXTENSIONS list.
        You can also sync the tree after reloading cogs. Though this is not
        to be used very often, as it has low rate limits.

        Args:
            ctx: The interaction context.
            sync: Whether to sync the tree after reloading cogs.
        """
        await ctx.response.send_message("Reloading cogs...")
        logger.info("Reloading cogs...")
        for extension in cogs.EXTENSIONS:
            if extension in self._bt.extensions:
                await self._bt.reload_extension(extension)
            else:
                await self._bt.load_extension(extension)
        await ctx.followup.send("Reloaded cogs.")
        logger.info("Finished reloading cogs.")
        if sync:
            self._bt.full_tree = await self._bt.tree.sync()
            guild = self._bt.get_guild(_CNFG["guild_id"])
            await self._bt.tree.sync(guild=guild)
            logger.info("Finished syncing tree.")

    @app_commands.command(name="close", description="Closes the bot.")
    @checks.is_owner_check()
    async def close(self, ctx: discord.Interaction) -> None:
        """Closes the bot.

        If used with a process manager, this will restart the bot.
        If used without a process manager, this will stop the bot.

        Args:
            ctx: The interaction context.
        """
        await ctx.response.send_message("Closing...")
        logger.info("Closing...")
        await self._bt.close()

    @app_commands.command(name="pull", description="Pulls the latest changes from the git repo. DANGEROUS!")
    @checks.is_owner_check()
    async def pull(self, ctx: discord.Interaction) -> None:
        """Pulls the latest changes from the git repo.

        This is a dangerous command, as it can break the bot.
        If you are not sure what you are doing, don't use this command.

        Args:
            ctx: The interaction context.
        """
        confr = views.Confirm(ctx.user)
        emd = discord.Embed(
            title="Pull from git",
            description=("Are you sure you want to pull from git?\n"
                         "This is a dangerous command, as it can break the bot.\n"
                         "If you are not sure what you are doing, abort now."),
            color=discord.Color.red(),
        )
        await ctx.response.send_message(embed=emd, view=confr)
        mgs = await ctx.original_response()
        if not await confr.resolve(
                ctx,
                mgs,
                emd,
                "Confirmed.\nPulling latest changes...",
                "Please stand by...",
        ):
            return
        logger.info("Pulling latest changes...")
        pull = await asyncio.create_subprocess_shell(
            "git pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=const.PROG_DIR,
        )
        stdo, stdr = await pull.communicate()
        if stdo:
            await ctx.followup.send(f"[stdout]\n{stdo.decode()}")
            logger.info("[stdout]\n%s", stdo.decode())

        if stdr:
            await ctx.followup.send(f"[stderr]\n{stdr.decode()}")
            logger.info("[stderr]\n%s", stdr.decode())

        await ctx.followup.send("Finished pulling latest changes.\n"
                                "Restart bot or reload cogs to apply changes.")

    @app_commands.command(name="logs", description="Sends the logs.")
    @checks.is_owner_check()
    @app_commands.describe(id_no="Log ID (0 for latest log)")
    async def logs(self, ctx: discord.Interaction, id_no: int = 0) -> None:
        """Sends the logs.

        This command sends the logs to the user who invoked the command.
        The logs are sent as a file attachment.
        It is possible to specify a log ID, which will send a specific log.
        If no log ID is specified, the latest log will be sent.

        Args:
            ctx: The interaction context.
            id_no: The log ID.
        """
        await ctx.response.defer(thinking=True)
        logger.info("Sending logs to %s...", str(ctx.user))
        filename = f"bot.log{'.'+str(id_no) if id_no else ''}"
        file_path = os.path.join(const.PROG_DIR, "log", filename)
        try:
            await ctx.user.send(file=discord.File(fp=file_path))
        except FileNotFoundError:
            await ctx.followup.send("Specified log not found.")
            logger.info("Specified log not found.")
            return
        await ctx.followup.send("Sent logs.")
        logger.info("Logs sent.")

    @app_commands.command(name="exec", description="Initiate an exec request.")
    @checks.is_owner_check()
    async def exec(self, ctx: discord.Interaction) -> None:
        """Initiates an exec request.

        This command starts listening in the DMs from the user for the code to execute.
        """
        await ctx.response.send_message("Waiting for code in DMs. Edit response to return something.", ephemeral=True)

        owner = ctx.user
        channel = owner.dm_channel
        if channel is None:
            channel = await owner.create_dm()

        def dm_from_user(msg):
            """Check if the message is from the user in DMs."""
            return msg.channel == channel and msg.author == owner

        response = None
        code = await ctx.client.wait_for("message", check=dm_from_user)
        await asyncio.to_thread(exec, code.content, globals(), locals())
        await channel.send("Executed.")

    @commands.command(name="sync", description="Syncs the tree.")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context) -> None:
        """Syncs the command tree.

        The command tree is what the bot uses to register slash commands.
        It is not recommended to use this command often, as it has low rate
        limits. It is the only non-slash command in this bot.

        Args:
            ctx: The command context.
        """
        await ctx.send("Syncing...")
        logger.info("Syncing...")
        self._bt.full_tree = await self._bt.tree.sync()
        guild = self._bt.get_guild(_CNFG["guild_id"])
        await self._bt.tree.sync(guild=guild)
        await ctx.send("Synced.")
        logger.info("Synced.")


async def setup(bot_instance: bot.NINABot):
    """Sets up the overrides.

    We add the override cog to the bot.

    Args:
        bot_instance: The bot.
    """
    await bot_instance.add_cog(Overrides(bot_instance))
