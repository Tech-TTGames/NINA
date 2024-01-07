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
import random
import shutil

import discord
from discord import app_commands
from discord.ext import commands

from techsim import bot
from techsim.data import const
from techsim.ext import checks
from techsim.ext import exceptions
from techsim.ext import thing

logger = logging.getLogger("techsim.core")


async def tribute_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Suggests completions for tribute names.

    Args:
        interaction: The interaction requesting autocompletion.
        current: The current input in the field.
    """
    return [
        app_commands.Choice(name=tribute.name, value=tribute.name)
        for tribute in interaction.client.sim.cast
        if current.lower() in tribute.name.lower()
    ]


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
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 255),
                              title=f"Simulation primary ready up protocol complete.",
                              description="Fetching images...")
        embed.set_author(name=self.sim.name, icon_url=self.sim.logo)
        embed.set_footer(text=f"Random seed: {self.sim.seed}")
        await ctx.followup.send(embed=embed)
        cast_fdir = self._dir.joinpath("cast")
        location = self._dir.joinpath("status")
        cycles = self._dir.joinpath("cycles")
        if cycles.exists():
            shutil.rmtree(cycles)
        if location.exists():
            shutil.rmtree(location)
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
        os.makedirs(location, exist_ok=True)
        # This is a directory as the districts split the status images.
        emd = discord.Embed(title="Current Simulation Status",)
        emd.set_author(name=f"{self.sim.name}", icon_url=self.sim.logo)
        for district in self.sim.districts:
            image = await district.get_render(self.sim)
            op_image = discord.File(image, filename=image.name)
            emd.description = f"Status for {district.name}"
            emd.set_image(url=f"attachment://{image.name}")
            emd.colour = discord.Color.from_str(district.color)
            await ctx.followup.send(embed=emd, file=op_image)

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
        await ctx.response.defer(thinking=True)
        ctx.extras["location"] = self._dir.joinpath("cycles", f"{self.sim.cycle}")
        os.makedirs(ctx.extras["location"], exist_ok=True)
        # This is a directory as a cycle consists of multiple event images.
        await self.sim.computecycle(ctx)
        await ctx.followup.send(f"Cycle {self.sim.cycle - 1} complete!")

    @app_commands.command(
        name="tributestatus",
        description="Displays the status of a tribute.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(tribute="The tribute to display.",)
    @checks.sim_ready_check()
    @app_commands.autocomplete(tribute=tribute_autocomplete)
    async def tributestatus(self, ctx: discord.Interaction, tribute: str) -> None:
        """Displays the status of a tribute.

        This command is used to display the status of a tribute.
        It takes the tribute as an argument.
        Displays the text-based log of the tribute.

        Args:
            ctx: The interaction context.
            tribute: The tribute to display.
        """
        for possibly_correct in self.sim.cast:
            if possibly_correct.name == tribute:
                tribute = possibly_correct
                break
        if isinstance(tribute, str):
            raise exceptions.UsageError("Invalid Tribute provided.")
        emd = discord.Embed(
            color=discord.Colour.from_str(tribute.district.color),
            title=f"Status of {tribute.name}",
            description=f"**Status:** {['Alive', 'Dead'][tribute.status]}\n"
            f"**District:** {tribute.district.name}\n"
            f"**Kills:** {tribute.kills}\n"
            f"**Power:** {tribute.effectivepower()}",
        )
        file = discord.utils.MISSING
        if tribute.status and tribute.dead_image == "BW":
            place = self._dir.joinpath("cast", f"{self.sim.cast.index(tribute)}")
            fil = await tribute.fetch_image("dead", place)
            file = discord.File(fil)
            emd.set_image(url=f"attachment://{file.filename}")
        else:
            emd.set_thumbnail(url=[tribute.image, tribute.dead_image][tribute.status])
        emd.set_author(name=f"{self.sim.name}", icon_url=self.sim.logo)
        emd.add_field(name="Items", value="\n".join([f"{item.name} - {uses}" for item, uses in tribute.items.items()]))
        emd.add_field(name="Allies", value="\n".join([ally.name for ally in tribute.allies]))
        emd.add_field(name="Enemies", value="\n".join([enemy.name for enemy in tribute.enemies]))
        emd.add_field(name="Events", value="\n".join(tribute.log))
        await ctx.response.send_message(embed=emd, file=file)


async def setup(bot_instance: bot.TechSimBot) -> None:
    """Set up the core cog.

    The bot calls this function when loading the cog.
    It is used to add the cog to the bot.

    Args:
        bot_instance: The bot instance.
    """
    await bot_instance.add_cog(Core(bot_instance))
