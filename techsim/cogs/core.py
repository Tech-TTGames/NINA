"""Simulation bot user interface cog.

This cog contains the commands that are used to interact with the simulation
via the Discord bot. This includes commands to import data, ready up, run a cycle,
check the status, and more.

Typical usage example:
    ```py
    from techsim import bot
    bot_instance = bot.TechSimBot(...)
    await bot_instance.load_extension("techsim.cogs.core")
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import asyncio
import logging
import os
import shutil

import discord
from discord import app_commands
from discord.ext import commands

from techsim import bot
from techsim.data import config, const
from techsim.ext import thing, checks

logger = logging.getLogger("techsim.core")


class Core(commands.Cog, name="SimCore"):
    """Simulation user interface cog.

    This cog contains the commands that are used to interact with the simulation
    via the Discord bot. This includes commands to import data, ready up, run a cycle,
    check the status, and more.
    """

    def __init__(self, bot_instance: bot.TechSimBot) -> None:
        """Initializes the cog.

        This method initializes the cog.
        It also sets the bot instance as a private attribute.
        And finally initializes the superclass.

        Args:
            bot_instance: The bot instance.
        """
        self._bt = bot_instance
        self._dir = const.PROG_DIR.joinpath("data")
        os.makedirs(self._dir, exist_ok=True)
        self.sim = None
        cast_dir, events_dir = self._dir.joinpath("cast.toml"), self._dir.joinpath("events.toml")
        if cast_dir.exists() and events_dir.exists():
            self.sim = thing.Simulation(cast_dir, events_dir, self._bt)
            logger.info("Loaded last simulation data.")
        self._bt.basp = self._dir
        self._bt.sim = self.sim
        logger.info("Loaded %s", self.__class__.__name__)

    @app_commands.command(
        name="setup",
        description="Sets up the simulation.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        cast="The cast for the simulation. A TOML file.",
        events="The events for the simulation. A TOML file.",
    )
    async def setup(self, ctx: discord.Interaction, cast: discord.Attachment, events: discord.Attachment) -> None:
        """Sets up the simulation.

        This command is used to set up the simulation.
        It takes two attachments, one for the cast and one for the events.
        The attachments must be in CSV format.

        Args:
            ctx: The interaction context.
            cast: The cast attachment.
            events: The events attachment.
        """
        logger.info(f"Setting up simulation for {ctx.user}.")
        await ctx.response.defer(thinking=True, ephemeral=True)
        cast_dir, events_dir = self._dir.joinpath("cast.toml"), self._dir.joinpath("events.toml")
        async with ctx.channel.typing():
            with open(cast_dir, "wb") as f:
                f.write(await cast.read())
            with open(events_dir, "wb") as f:
                f.write(await events.read())
        self.sim = thing.Simulation(cast_dir, events_dir, self._bt)
        await ctx.followup.send("Configuration loaded.", ephemeral=True)
        logger.info(f"Simulation set up for {ctx.user}.")

    @app_commands.command(
        name="ready",
        description="Readies the simulation.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        seed="The seed to use for the simulation.",
        randomize_dc="Whether to shuffle district assignments.",
        recolor_dc="Whether to recolor the districts.",
    )
    @checks.sim_setup_check()
    async def ready(
        self,
        ctx: discord.Interaction,
        seed: str | None = None,
        randomize_dc: bool = False,
        recolor_dc: bool = False,
    ) -> None:
        """Readies the simulation.

        This command is used to ready the simulation.
        It takes a seed and two booleans to randomize and recolor the data collection.

        Args:
            ctx: The interaction context.
            seed: The seed to use for the simulation.
            randomize_dc: Whether to shuffle district assignments.
            recolor_dc: Whether to recolor the districts.
        """
        cast_dir, events_dir = self._dir.joinpath("cast.toml"), self._dir.joinpath("events.toml")
        if not cast_dir.exists() or not events_dir.exists():
            setup_id = 0
            for command in self._bt.full_tree:
                if command.name == "setup":
                    setup_id = command.id
                    break
            await ctx.response.send_message(
                f"Simulation not set up. Please use </setup:{setup_id}> first.",
                ephemeral=True,
            )
            return
        self.sim = thing.Simulation(cast_dir, events_dir, self._bt)
        self._bt.sim = self.sim
        # Reset the sim just in case.
        logger.info(f"Readying simulation for {ctx.user}.")
        await ctx.response.defer(thinking=True)
        await self.sim.ready(seed, randomize_dc, recolor_dc, ctx)
        await ctx.followup.send(
            f"Simulation '{self.sim.name}' primary ready procedure complete.\n"
            f"Fetching images...",)
        cast_fdir = self._dir.joinpath("cast")
        if cast_fdir.exists():
            shutil.rmtree(cast_fdir)
        os.makedirs(cast_fdir)
        image_tasks = []
        sesh = self._bt.httpsession
        for tribute_id, tribute in enumerate(self.sim.cast):
            cwd = cast_fdir.joinpath(str(tribute_id))
            os.makedirs(cwd)
            image_tasks.append(tribute.fetch_image("alive", cwd, sesh))
        await asyncio.gather(*image_tasks)
        image_tasks = []
        # Separated to allow for PIL to be used for BW images.
        for tribute_id, tribute in enumerate(self.sim.cast):
            cwd = cast_fdir.joinpath(str(tribute_id))
            image_tasks.append(tribute.fetch_image("dead", cwd, sesh))
        await asyncio.gather(*image_tasks)
        await ctx.followup.send("Images fetched. Simulation ready.")
        logger.info(f"Simulation readied for {ctx.user}.")

    @app_commands.command(
        name="status",
        description="Display the current simulation status.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @checks.sim_ready_check()
    async def status(self, ctx: discord.Interaction) -> None:
        """Displays the current simulation status.

        This command is used to display the current simulation status.
        It displays every cast member of the district, their kill count, and their status.

        Args:
            ctx: The interaction context.
        """
        await ctx.response.defer(thinking=True)
        location = self._dir.joinpath("status")
        place = self._dir.joinpath("cast")
        os.makedirs(location, exist_ok=True)
        # This is a directory as the districts split the status images.
        # TODO: After implementing rendering stuff, use it here.
        # For testing stuff: Nuke after use, probably or actually use it.
        tasks = []
        for tribute_id, tribute in enumerate(self.sim.cast):
            cwd = place.joinpath(str(tribute_id))
            tasks.append(tribute.get_status_render(cwd))
        await asyncio.gather(*tasks)
        await ctx.followup.send("Test status generation done.")

    @app_commands.command(
        name="cycle",
        description="Runs a cycle of the simulation.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @checks.sim_ready_check()
    async def cycle(self, ctx: discord.Interaction) -> None:
        """Runs a cycle of the simulation.

        This command is used to run a cycle of the simulation.
        It takes no arguments.

        Args:
            ctx: The interaction context.
        """
        ctx.extras["location"] = self._dir.joinpath("cycles", f"cycle_{self.sim.cycle}")
        os.makedirs(ctx.extras["location"], exist_ok=True)
        # This is a directory as a cycle consists of multiple event images.
        # TODO: After implementing rendering stuff, use it here.

    @app_commands.command(
        name="tributestatus",
        description="Displays the status of a tribute.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(tribute="The tribute to display.",)
    # @app_commands.autocomplete(tribute="tribute")
    # TODO: Implement autocomplete.
    @checks.sim_ready_check()
    async def tributestatus(self, ctx: discord.Interaction, tribute: str) -> None:
        """Displays the status of a tribute.

        This command is used to display the status of a tribute.
        It takes the tribute as an argument.
        Displays the text-based log of the tribute.

        Args:
            ctx: The interaction context.
            tribute: The tribute to display.
        """
        pass
        # This one won't be rendering anything we just use the image/dead image and some data in an embed.
        # TODO: Implement this.


async def setup(bot_instance: bot.TechSimBot) -> None:
    """Set up the core cog.

    The bot calls this function when loading the cog.
    It is used to add the cog to the bot.

    Args:
        bot_instance: The bot instance.
    """
    await bot_instance.add_cog(Core(bot_instance))