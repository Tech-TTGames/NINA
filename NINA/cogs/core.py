"""Simulation bot user interface cog.

This cog contains the commands that are used to interact with the simulation
via the Discord bot. This includes commands to import data, ready up, run a cycle,
check the status, and more.

Typical usage example:
    ```py
    from NINA import bot
    bot_instance = bot.NINABot(...)
    await bot_instance.load_extension("NINA.cogs.core")
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
import owo
from discord import app_commands
from discord.ext import commands

from NINA import bot
from NINA.data import const
from NINA.ext import NINA
from NINA.ext import checks
from NINA.ext import exceptions

logger = logging.getLogger("NINA.core")


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

    def __init__(self, bot_instance: bot.NINABot) -> None:
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
        self.owo_toggwe = False
        cast_dir, events_dir = self._dir.joinpath("cast.toml"), self._dir.joinpath("events.toml")
        if cast_dir.exists() and events_dir.exists():
            try:
                self.sim = NINA.Simulation(cast_dir, events_dir, self.owo_toggwe)
                logger.info("Loaded last simulation data.")
            except (ValueError, KeyError):
                self.sim = None
                os.remove(cast_dir)
                os.remove(events_dir)
                logger.info("Local files invalid/corrupt. Purged from system.")
        self._bt.basp = self._dir
        self._bt.sim = self.sim
        self.lock = False
        logger.info("Loaded %s", self.__class__.__name__)

    def t(self, string: str) -> str:
        """Adjusts text according to the current owo_toggwe mode."""
        if self.owo_toggwe:
            return owo.owo(string)
        return string

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
        if self.lock:
            raise exceptions.UsageError("Bot cog lock active.")
        self.lock = True
        t = self.t
        logger.info(f"Setting up simulation for {ctx.user}.")
        await ctx.response.defer(thinking=True, ephemeral=True)
        cast_dir, events_dir = self._dir.joinpath("cast.toml"), self._dir.joinpath("events.toml")
        async with ctx.channel.typing():
            with open(cast_dir, "wb") as f:
                f.write(await cast.read())
            with open(events_dir, "wb") as f:
                f.write(await events.read())
        self.lock = False
        await ctx.followup.send(t("Configuration loaded."), ephemeral=True)
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
        owo_toggwe="Manually toggle OwO mode for the simulation.",
    )
    @checks.sim_setup_check()
    async def ready(
        self,
        ctx: discord.Interaction,
        seed: str | None = None,
        randomize_dc: bool = False,
        recolor_dc: bool = False,
        owo_toggwe: bool = False,
    ) -> None:
        """Readies the simulation.

        This command is used to ready the simulation.
        It takes a seed and two booleans to randomize and recolor the data collection.

        Args:
            ctx: The interaction context.
            seed: The seed to use for the simulation.
            randomize_dc: Whether to shuffle district assignments.
            recolor_dc: Whether to recolor the districts.
            owo_toggwe: Whether to owo_toggwe everything.
        """
        if self.lock:
            raise exceptions.UsageError("Bot simulation lock active.")
        self.lock = True
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
        self.owo_toggwe = owo_toggwe
        if not self.owo_toggwe:
            a = random.randint(0, 7911979)
            self.owo_toggwe = a == 0
        t = self.t
        self.sim = NINA.Simulation(cast_dir, events_dir, self.owo_toggwe)
        self._bt.sim = self.sim
        # Reset the sim just in case.
        logger.info(f"Readying simulation for {ctx.user}.")
        await ctx.response.defer(thinking=True)
        await self.sim.ready(seed, randomize_dc, recolor_dc, ctx)
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 255),
                              title=t(f"Simulation primary ready up protocol complete."),
                              description=t("Fetching images..."))
        embed.set_author(name=t(self.sim.name), icon_url=self.sim.logo)
        embed.set_footer(text=t("Random seed:") + f"{self.sim.seed}")
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
        await ctx.followup.send(t("Images fetched. Simulation ready."))
        logger.info(f"Simulation readied for {ctx.user}.")
        self.lock = False

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
        t = self.t
        location = self._dir.joinpath("status")
        os.makedirs(location, exist_ok=True)
        # This is a directory as the districts split the status images.
        emd = discord.Embed(title=t("Current Simulation Status"))
        emd.set_author(name=t(f"{self.sim.name}"), icon_url=self.sim.logo)
        for district in self.sim.districts:
            image = await district.get_render(self.sim)
            op_image = discord.File(image, filename=image.name)
            emd.description = t(f"Status for {district.name}")
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
        if self.lock:
            raise exceptions.UsageError("Bot simulation lock active.")
        self.lock = True
        t = self.t
        sim = self.sim
        # recovery.Safe doesn't seem to be working at the moment. Bypassed
        # with recovery.Safe(self.sim) as sim:
        await ctx.response.defer(thinking=True)
        ctx.extras["location"] = self._dir.joinpath("cycles", f"{sim.cycle}")
        os.makedirs(ctx.extras["location"], exist_ok=True)
        # This is a directory as a cycle consists of multiple event images.
        await sim.computecycle(ctx)
        await ctx.followup.send(t(f"Cycle {sim.cycle - 1} complete!"))
        self.lock = False

    @app_commands.command(
        name="tributestatus",
        description="Displays the status of a tribute.",
    )
    @app_commands.guild_only()
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
        t = self.t
        emd = discord.Embed(
            color=discord.Colour.from_str(tribute.district.color),
            title=t(f"Status of {tribute.name}"),
            description=t(f"**Status:** {['Alive', 'Dead'][tribute.status]}\n") +
            t(f"**District:** {tribute.district.name}\n") + t(f"**Kills:** {tribute.kills}\n") +
            t(f"**Power:** {tribute.effectivepower()}"),
        )
        file = discord.utils.MISSING
        if tribute.status and tribute.dead_image == "BW":
            place = self._dir.joinpath("cast", f"{self.sim.cast.index(tribute)}")
            fil = await tribute.fetch_image("dead", place)
            file = discord.File(fil)
            emd.set_image(url=f"attachment://{file.filename}")
        else:
            emd.set_thumbnail(url=[tribute.image, tribute.dead_image][tribute.status])
        emd.set_author(name=t(f"{self.sim.name}"), icon_url=self.sim.logo)
        emd.add_field(name=t("Items"),
                      value=NINA.truncatelast(
                          t("\n".join([f"{item.name} - {uses}" for item, uses in tribute.items.items()])), 1024))
        emd.add_field(name=t("Allies"),
                      value=NINA.truncatelast(t("\n".join([ally.name for ally in tribute.allies])), 1024))
        emd.add_field(name=t("Enemies"),
                      value=NINA.truncatelast(t("\n".join([enemy.name for enemy in tribute.enemies])), 1024))
        emd.add_field(name=t("Events"), value=NINA.truncatelast("\n".join(tribute.log), 1024))
        await ctx.response.send_message(embed=emd, file=file)

    @app_commands.command(
        name="tweakfont",
        description="Tweaks the font for the simulation.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        fill="The fill color for the font. Hexcode.",
        stroke="The stroke color for the font. Hexcode.",
        width="The width of the stroke.",
    )
    async def tweakfont(self, ctx: discord.Interaction, fill: str = "", stroke: str = "", width: int = -1) -> None:
        """Tweaks the font for the simulation.

        This command is used to tweak the font for the simulation.
        It takes the stroke, fill, and width as arguments.

        Args:
            ctx: The interaction context.
            stroke: The stroke color for the font. Hexcode.
            fill: The fill color for the font. Hexcode.
            width: The width of the stroke.
        """
        if self.lock:
            raise exceptions.UsageError("Bot simulation lock active.")
        self.lock = True
        if width < 0:
            width = None
        await ctx.response.defer(thinking=True)
        NINA.DRAW_ARGS["fill"] = fill or NINA.DRAW_ARGS["fill"]
        NINA.DRAW_ARGS["stroke_fill"] = stroke or NINA.DRAW_ARGS["stroke_fill"]
        NINA.DRAW_ARGS["stroke_width"] = width or NINA.DRAW_ARGS["stroke_width"]
        await ctx.followup.send("Font tweaked.")
        self.lock = False


async def setup(bot_instance: bot.NINABot) -> None:
    """Set up the core cog.

    The bot calls this function when loading the cog.
    It is used to add the cog to the bot.

    Args:
        bot_instance: The bot instance.
    """
    await bot_instance.add_cog(Core(bot_instance))
