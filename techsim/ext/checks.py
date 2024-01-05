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
        raise exceptions.TechCheckFailure("You do not have permission to do this.")

    return app_commands.check(is_owner)


def sim_setup_check():
    """A check to ensure that data has been loaded into the simulation.

    Returns:
        `discord.app_commands.check`: The check.
            This time it requires a cog so use it with
            command.sim_setup_check(sim_setup(self))
    """

    async def sim_setup(interaction: discord.Interaction):
        """This check to ensure that data has been loaded into the simulation

        Args:
            interaction: The interaction to handle.

        Returns:
            `bool`: Whether the data is loaded into the simulation
        """
        direct = interaction.client.basp
        castdir, eventsdir = direct.joinpath("cast.toml"), direct.joinpath("events.toml")
        if not castdir.exists() or not eventsdir.exists():
            setup_id = 0
            for command in interaction.client.full_tree:
                if command.name == "setup":
                    setup_id = command.id
                    break
            await interaction.response.send_message(
                f"Simulation not set up. Please use </setup:{setup_id}> first.",
                ephemeral=True,
            )
            return False
        return True

    return app_commands.check(sim_setup)


def sim_ready_check():
    """A check to ensure that the simulation is ready.

    Returns:
        `discord.app_commands.check`: The check.
            This time it requires a cog so use it with
            command.add_check(sim_ready_check(self))
    """

    async def sim_ready(interaction: discord.Interaction):
        """This check to ensure that sim ready before running commands

        Args:
            interaction: The interaction to handle.

        Returns:
            `bool`: Whether the data is loaded into the simulation
        """
        bt = interaction.client
        if bt.sim.cycle == -2:
            ready_id = 0
            for command in bt.full_tree:
                if command.name == "ready":
                    ready_id = command.id
                    break
            await interaction.response.send_message(
                f"Simulation not readied up!. Please use </ready:{ready_id}> first.",
                ephemeral=True,
            )
            return False
        return True

    return app_commands.check(sim_ready)
