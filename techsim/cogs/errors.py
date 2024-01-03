"""A cog that handles errors from app commands globally.

We use this cog to handle errors from app commands globally.
This is to actually handle and respond to errors.
It's nice to not leave the user confused.

Typical usage example:
    ```py
    from techsim import bot
    bot_instance = bot.TechSimBot(...)
    await bot_instance.load_extension("techsim.cogs.errors")
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import logging

import discord
from discord import app_commands, utils
from discord.ext import commands

from techsim import bot
from techsim.ext import exceptions

logger = logging.getLogger("techsim.commanderrorhandler")


class ErrorHandling(commands.Cog, name="AppCommandErrorHandler"):
    """Error handling for TechSimBot.

    This cog is used to handle errors from app commands globally.
    This is to actually handle and respond to errors.

    Attributes:
        old_error_handler: The old error handler.
            This is used to restore the old error handler.
    """

    def __init__(self, bot_instance: bot.TechSimBot) -> None:
        """Initialises the cog instance.

        We store some attributes here for later use.

        Args:
            bot_instance: The bot instance.
        """
        self._bt = bot_instance
        self.old_error_handler = None
        logger.info("Loaded %s", self.__class__.__name__)

    async def cog_load(self) -> None:
        """Adds the error handler to the bot.

        Should not be called manually.
        """
        tree = self._bt.tree
        self.old_error_handler = tree.on_error
        tree.on_error = self.on_app_command_error
        logger.info("Error handling ready.")

    async def cog_unload(self) -> None:
        """Removes the error handler from the bot.

        Should not be called manually.
        """
        tree = self._bt.tree
        tree.on_error = self.old_error_handler
        logger.info("Error handling unloaded.")

    async def on_app_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Handles errors from app commands globally.

        This function is automatically called when an error is raised from an app command.
        This is used to handle and respond to errors.
        To not leave the user confused.

        Args:
            ctx: The interaction that raised the error.
            error: The error that was raised.
        """
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)
        if isinstance(ctx.command, app_commands.Command):
            # Splitting because we don't want AttributeError
            if hasattr(ctx.command, "on_error"):
                # Same as above
                if ctx.command.on_error is not None:
                    return

        emd = discord.Embed(
            title="TechSimBot Error: 500 - Internal Server Error",
            description=("An unexpected internal error occurred.\n"
                         "Please report this error to the server staff."),
            color=discord.Color.red(),
            timestamp=utils.utcnow(),
        )

        if isinstance(error, app_commands.CommandNotFound):
            emd.title = "TechSimBot Error: 404 - Command Not Found"
            emd.description = "The command you tried to use does not exist."
            emd.set_footer(text="If this error persists, please report it.")
            await ctx.followup.send(embed=emd, ephemeral=True)
            return

        if isinstance(error, app_commands.CheckFailure):
            if isinstance(error, app_commands.BotMissingPermissions):
                emd.title = "TechSimBot Error: 503 - Bot Missing Permissions"
                emd.description = ("The bot is missing permissions required"
                                   " to run this command.\n"
                                   "Please ask a server administrator to grant the bot the "
                                   "following permissions:\n"
                                   f"{chr(92).join(error.missing_permissions)}")
                emd.set_footer(text="If you are sure the bot has the "
                               "required permissions, please report this.")
                await ctx.followup.send(embed=emd, ephemeral=True)
                return

            if isinstance(error, app_commands.NoPrivateMessage):
                emd.title = "TechSimBot Error: 405 - DMs Not Allowed"
                emd.description = "This command cannot be used in DMs."
                emd.set_footer(text="Please use this command in a server.")
                await ctx.followup.send(embed=emd, ephemeral=True)
                return

            if isinstance(error, app_commands.CommandOnCooldown):
                emd.title = "TechSimBot Error: 429 - Command On Cooldown"
                emd.description = ("This command is on cooldown.\n"
                                   f"Please try again in {error.retry_after} seconds.")
                emd.set_footer(text="Thank you for using TechSim!")
                await ctx.followup.send(embed=emd, ephemeral=True)
                return

            emd.title = "TechSimBot Error: 403 - Forbidden"
            emd.description = "You do not have permission to use this command."
            emd.set_footer(text=f"Error type: {type(error).__name__}")
            await ctx.followup.send(embed=emd, ephemeral=True)
            return

        if isinstance(error, exceptions.TechSimBotError):
            emd.title = "TechSimBot Error: 400 - Bad Request"
            emd.description = str(error)
            emd.set_footer(text=f"Error type: {type(error).__name__}")
            await ctx.followup.send(embed=emd, ephemeral=True)
            return  # We don't want to log this error.

        if isinstance(error, app_commands.CommandInvokeError):
            error_invk = error.original
        else:
            error_invk = error

        logger.error("An unhandled error occurred while executing a command:", exc_info=error_invk)
        emd.set_footer(text=f"Error type: {type(error_invk).__name__}")
        await ctx.followup.send(embed=emd, ephemeral=True)


async def setup(bot_instance: bot.TechSimBot) -> None:
    """Sets up the error handler.

    This function is called when the cog is loaded.
    It is used to add the cog to the bot.

    Args:
        bot_instance: The bot instance.
    """
    await bot_instance.add_cog(ErrorHandling(bot_instance))
