"""TechSim decorators for use with discord.py app commands.

A set of decorators for use with discord.py application commands.
These are generally TechSim Bot specific, but some may be more general.
They require the client to be a `techsim.bot.TechSimBot` instance.
Though some may work with any `discord.ext.commands.Bot` instance.

Typical usage example:
    ```py
    from discord import app_commands
    from techsim.ext import checks

    @app_commands.command()
    @checks.is_owner_check()
    async def command(interaction: discord.Interaction):
        ...
    ```
"""
# License: UNLICENSED
# SPDX-License-Identifier: UNLICENSED
# Copyright (c) 2023-present Tech. TTGames

import discord
from discord import app_commands

from techsim.ext import exceptions


def is_owner_check():
    """A check for owner only commands.

    We need to create our own check because the default one doesn't work with
    application commands.

    Returns:
        `discord.app_commands.check`: The check.
            It's a decorator, so you can use it like this:
            ```py
            @app_commands.command()
            @is_owner_check()
            async def command(interaction: discord.Interaction):
                ...
            ```
    """

    async def is_owner(interaction: discord.Interaction) -> bool:
        """Checks if interaction user is an owner.

        The actual check. It's a coroutine, so it can be awaited.

        Args:
            interaction: The interaction to check.

        Returns:
            `bool`: Whether the user is an owner or not.
                Doesn't return if the user is not an owner.

        Raises:
            `techsim.exceptions.DCheckFailure`: Requirements not met.
                Raised if the user is not an owner. This is according to the
                discord.py convention.
        """
        app = await interaction.client.application_info()
        if app.team:
            # Split to avoid errors ie AttributeError
            if interaction.user in app.team.members:
                return True
        if interaction.user == app.owner:
            return True
        raise exceptions.DCheckFailure("You do not have permission to do this.")

    return app_commands.check(is_owner)
