"""The actual simulation infrastructure for TechSim.

This is the main module for the simulation infrastructure.
It contains the classes for the simulation, districts, tributes, cycles, events and items.
It's placed in the ext folder because it's not a cog, and the core cog will import it.

Typical usage example:
    ```py
    from techsim.ext import simulation
    # Set up the log handler of choice.
    sim = simulation.Simulation("cast.toml", "events.toml")
    await sim.ready()
    await sim.computecycle()
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import asyncio
import colorsys
import io
import itertools
import logging
import os
import pathlib
import random
import string
import tomllib
from typing import Any, Literal, Optional, Union

import aiohttp
import discord
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageSequence

from techsim import bot
from techsim.data import const
from techsim.ext import imgops

logger = logging.getLogger("techsim.simulation")

BASE_POWER = 500
MAX_LINEBREAKS = 5
FONT = "consola.ttf"
DRAW_ARGS = {
    "fill": (255, 255, 255, 255),
    "stroke_fill": (0, 0, 0, 255),
    "stroke_width": 2,
    "align": "center",
}

# 0: Female, 1: Male, 2: Neuter, 3: Pair, 4: Non-binary
SPronouns = ["she", "he", "it", "they", "they"]
OPronouns = ["her", "him", "it", "them", "them"]
PPronouns = ["hers", "his", "its", "theirs", "theirs"]
RPronouns = ["herself", "himself", "itself", "themself", "themself"]
PAdjectives = ["her", "his", "its", "their", "their"]


def getsize(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """Get the size of the text.

    Args:
        draw: The draw object to use.
        Shouldn't change anything.
        text: The text to measure.
        font: The font to use for measurement.
    """
    bbox = draw.textbbox((0, 0), text, font, stroke_width=DRAW_ARGS['stroke_width'], align=DRAW_ARGS['align'])
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_max_text(
    im: Image.Image,
    text: str,
    max_sizes: tuple[int, int],
    anchor: str,
    location: tuple[int, int],
) -> ImageDraw.ImageDraw:
    """Draws a text on top of the image, taking up as much space as possible.

    Attempts to provide the biggest possible fontsize for the best readability.

    Args:
        im: The image to draw on
        text: The text to draw
        max_sizes: The maximum size that the text can take up
        anchor: The to use for the drawing.
        location: The location to use for drawing.

    Returns:
        The draw object used.
    """
    draw = ImageDraw.Draw(im)
    size = 1
    last_viable_set = None
    while True:
        proposed_text = text
        font = ImageFont.truetype(FONT, size)
        current_size = getsize(draw, proposed_text, font)
        if current_size[0] > max_sizes[0]:
            cropped_frags = []
            linebreaks = 0
            while True:
                current_size = getsize(draw, proposed_text, font)
                if current_size[0] <= max_sizes[0]:
                    break
                split_text = proposed_text.split(" ")
                for word_n in range(len(split_text), 0, -1):
                    sequence = " ".join(split_text[:word_n])
                    sequence_size = getsize(draw, sequence, font)
                    if sequence_size[0] < max_sizes[0]:
                        cropped_frags.append(sequence + "\n")
                        proposed_text = " ".join(split_text[word_n:])
                        break
                linebreaks += 1
                if linebreaks > MAX_LINEBREAKS:
                    break
            proposed_text = "".join(cropped_frags) + proposed_text
            current_size = getsize(draw, proposed_text, font)
        if current_size[1] > max_sizes[1] or current_size[0] > max_sizes[0]:
            break
        last_viable_set = (font, proposed_text)
        size += 1
    if not last_viable_set:
        raise ValueError("Text too long for image.")
    font, new_text = last_viable_set
    if anchor[1] in ["a", "d"]:
        sizey = draw.textbbox(location,
                              new_text,
                              font,
                              anchor,
                              stroke_width=DRAW_ARGS['stroke_width'],
                              align=DRAW_ARGS['align'])
        if anchor[1] == "a":
            location = (location[0], location[1] + (location[1] - sizey[1]))
        else:
            location = (location[0], location[1] + (location[1] - sizey[3]))
    draw.text(location, new_text, font=font, anchor=anchor, **DRAW_ARGS)
    return draw


def truncatelast(text: str, length: int) -> str:
    """Truncate a string to fit the provided length.

    Args:
        text: The string to truncate
        length: The length to achieve
    """
    return "..." + text[-1 * (length - 3):] if len(text) > length else text


async def generate_endcycle(
    cycle_no: int,
    involved: list["Tribute"],
    sim: "Simulation",
    request: int,
) -> pathlib.Path:
    """Generate a mortem report image for the given deaths.

    Args:
        cycle_no: The number of the cycle requesting the mortem report
        involved: A list of tributes involved in this endofcycle.
        sim: The current simulation status.
        request: 0 for mortem request, 1 for victory screen.
    """
    tribute_place = const.PROG_DIR.joinpath("data", "cast")
    image_paths = await asyncio.gather(*[
        tribute.fetch_image(["alive", "dead"][tribute.status], tribute_place.joinpath(f"{sim.cast.index(tribute)}"))
        for tribute in involved
    ])
    images = [(Image.open(pth), (dead.name, dead.district.name)) for pth, dead in zip(image_paths, involved)]
    place = const.PROG_DIR.joinpath("data", "cycles", f"{cycle_no}")
    if cycle_no == -1:
        place = const.PROG_DIR.joinpath("data")
    base_image = Image.new(
        "RGBA",
        (min(4, len(involved)) * 576 + 64, (len(involved) // 4 + 1 - bool(len(involved) % 4 == 0)) * 576 + 128),
        (0, 0, 0, 0),
    )
    text = f"Fallen Tribute{'s' if len(involved) > 1 else ''} for Day {cycle_no // 2 + 1}"
    if request:
        text = f"Winner{'s' if len(involved) > 1 else ''} of {sim.name}!"
    draw = draw_max_text(base_image, text, (base_image.width, 128), "md", (base_image.width // 2, 128))
    # Size is
    # Width: number between 1-4 * 576 + 64
    # Height: 640 for each row of images,
    font = ImageFont.truetype(FONT, size=32)
    gifs_pending = []
    for row, batch in enumerate(itertools.batched(images, 4)):
        offset = 64 + ((4 - len(batch)) * 288) * bool(len(involved) > 4)
        for col, img in enumerate(batch):
            paste = (offset + col * 576, 128 + row * 576)
            if img[0].format == "GIF":
                gifs_pending.append((img[0], paste))
            else:
                base_image.paste(img[0], paste)
            draw.text((paste[0] + 256, paste[1] + 512),
                      text=f"{img[1][0]}\n{img[1][1]}",
                      font=font,
                      anchor="ma",
                      **DRAW_ARGS)
    if not gifs_pending:
        place = place.joinpath(f"{['mortem', 'victors'][request]}.png")
        base_image.save(place, optimize=True)
    else:
        place = place.joinpath(f"{['mortem', 'victors'][request]}.gif")
        max_frames = max([gif[1].n_frames for gif in gifs_pending])
        status_img = [base_image.copy() for _ in range(max_frames)]
        for gif, location in gifs_pending:
            for result_frame, gif_frame in zip(status_img, itertools.cycle(ImageSequence.all_frames(gif))):
                result_frame.paste(gif_frame, location)
        durs = imgops.average_gif_durations([gif[1].info.get("duration", 50) for gif in gifs_to_process], max_frames)
        status_img[0].save(
            place,
            save_all=True,
            append_images=status_img[1:],
            loop=0,
            duration=durs,
            optimize=True,
            disposal=2,
        )
    return place


class Simulation:
    """A class representing a TechSim simulation.

    Attributes:
        cycle: The current cycle/status of the simulation.
            -2: Not ready, -1: Complete, 0+: Cycle number.
        name: The name of the simulation.
        logo: The logo of the simulation (link).
        districts: The districts of the simulation.
            See District class for more information.
        cast: The cast of the simulation.
            See Tribute class for more information.
        cycles: The cycles of the simulation.
            See Cycle class for more information.
        items: The items of the simulation.
            See Item class for more information.
        alive: The living tributes of the simulation.
        dead: The dead tributes of the simulation.
    """
    seed: Any
    cycle: int
    alive: list["Tribute"]
    dead: list["Tribute"]
    cycle_deaths: list["Tribute"]

    def __init__(self, cast_file: pathlib.Path, events_file: pathlib.Path, bot_instance: bot.TechSimBot | None) -> None:
        """Initialize the Simulation object."""
        with open(cast_file, "rb") as file:
            data = tomllib.load(file)
        self.cycle = -2
        self.name: str = data['name']
        self.logo: str = data['logo']
        self.cast = [Tribute(tribute) for tribute in data['cast']]
        self.districts = [District(district) for district in data['districts']]
        with open(events_file, "rb") as file:
            data = tomllib.load(file)
        self.cycles = [Cycle(cycle) for cycle in data['cycles']]
        self.items = [Item(item, self.cycles) for item in data['items']]
        if not self.cycles:
            raise ValueError("No cycles found.")
        self._bt = bot_instance

    def __str__(self):
        """Text representation of the simulation."""
        return f"TechSim Simulation: {self.name}"

    async def ready(
        self,
        seed: str | None,
        districtrand: bool = False,
        recolor: bool = False,
        interaction: discord.Interaction | None = None,
    ):
        """Ready up!

        This is the method that prepares the simulation for running.

        Args:
            seed: The seed for the simulation
                None for random.
            districtrand: Whether to randomize the district members.
            recolor: Whether to recolor the districts to the standard HUE rotation.
            interaction: The interaction to send some log-like messages to.
        """
        logger.info("Beginning simulation '%s' ready up procedure.", self.name)
        if interaction:
            await interaction.followup.send(f"Beginning simulation `{self.name}` ready up procedure.")
        if not seed:
            seed = os.urandom(16)
            self.seed = int.from_bytes(seed)
        else:
            if seed.isnumeric():
                self.seed = int(seed)
                try:
                    seed = int(seed).to_bytes(16)
                except ArithmeticError:
                    seed = str(seed)
                    self.seed = seed
            else:
                self.seed = seed
        random.seed(seed)
        if districtrand:
            logger.info("Randomizing district members.")
            if interaction:
                await interaction.followup.send("Randomizing district members.")
            random.shuffle(self.cast)
        if recolor:
            logger.info("Recoloring districts.")
            if interaction:
                await interaction.followup.send("Recoloring districts.")
            max_hue = 360
            increment = max_hue // len(self.districts)
            offset = random.randint(0, increment)
            for i, district in enumerate(self.districts):
                rgb = [int(x * 255) for x in colorsys.hsv_to_rgb((i * increment + offset) / 360, 1.0, 1.0)]
                color = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])
                district.color = color
        logger.info("Assigning districts.")
        if interaction:
            await interaction.followup.send("Assigning districts.")
        tid = 0
        mpd = len(self.cast) // len(self.districts)
        for district in self.districts:
            for tribute in range(tid, tid + mpd):
                self.cast[tribute].district = district
                district.members.append(self.cast[tribute])
            district.apply_allies()
            tid += mpd
        self.cycle = 0
        self.alive = self.cast.copy()
        self.dead = []
        self.cycle_deaths = []
        logger.info("Simulation '%s' ready.", self.name)

    def getcycle(self) -> Optional["Cycle"]:
        """Fetch the cycle object for the current cycle.

        Returns:
            The cycle object for the current cycle.
        """
        if self.cycle == [-2, -1]:
            logger.warning("Simulation '%s' is not ready.", self.name)
            return None
        night = self.cycle % 2 == 0
        randomevents = []
        resolved_cycle: Cycle | None = None
        for cycle in self.cycles:
            if isinstance(cycle.weight, str):
                if int(cycle.weight) == self.cycle:
                    resolved_cycle = cycle
                    break
                continue
            if cycle.weight > 0 and not night and cycle.max_use != 0:
                randomevents.append(cycle)
                continue
            if cycle.weight < 0 and night and cycle.max_use != 0:
                randomevents.append(cycle)
        if randomevents and not resolved_cycle:
            resolved_cycle = random.choices(randomevents, weights=[abs(cycle.weight) for cycle in randomevents])[0]
        return resolved_cycle

    async def computecycle(self, interaction: discord.Interaction | None = None) -> None:
        """Compute the next cycle.

        This is the method that computes the next cycle.
        So the whole day/night/special event cycle.

        Args:
            interaction: The interaction to send some log-like messages to.
        """
        if self.cycle in [-2, -1]:
            logger.warning("Simulation '%s' is not ready.", self.name)
            return
        cycle = self.getcycle()
        if interaction:
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 255),
                                  title=f"Beginning simulation of Cycle {self.cycle}",
                                  description=f"Cycle type: {cycle.name}\n"
                                  f"Remaining tribute count: {len(self.alive)}")
            embed.set_author(name=self.name, icon_url=self.logo)
            attach = discord.File(await cycle.render_start(self.cycle))
            embed.set_image(url="attachment://start.png")
            await interaction.followup.send(embed=embed, file=attach)
        logger.info("Beginning cycle %s.", cycle.name)
        if cycle.text:
            logger.info("Displaying cycle text.")
            logger.info(cycle.text)
        logger.info("Computing events.")
        # Parse to bot here.
        active_tributes = self.alive.copy()
        cycle_events = cycle.events
        event_no = 0
        for item in self.items:
            if cycle in item.cycles:
                cycle_events.append(item.base_event)
        while active_tributes:
            possible_events = []
            wg = [tribute.effectivepower() for tribute in active_tributes]
            tribute: "Tribute" = random.choices(active_tributes, weights=wg)[0]
            for item, _ in tribute.items.items():
                if (cycle in item.cycles and cycle.allow_item_events == "cycle") or cycle.allow_item_events == "all":
                    possible_events.extend(item.events)
            for event in cycle_events:
                if event.check_requirements(tribute, 0):
                    logger.debug("Adding event to pool %s for tribute %s", event.text.template, tribute.name)
                    possible_events.append(event)
                else:
                    logger.debug("Discarded event %s for tribute %s", event.text.template, tribute.name)
            if not possible_events:
                logger.warning("Could not find event for tribute '%s'.", tribute.name)
                continue
            event = random.choices(possible_events, weights=[event.weight for event in possible_events])[0]
            logger.debug("Resolving event '%s'.", event.text.template)
            tributes_involved = await event.affiliationresolution(tribute, active_tributes, self)
            if not tributes_involved:
                continue  # Already logged in affiliationresolution
            event_no += 1
            if interaction:
                pack = (interaction.extras["location"], event_no)
                resolution_text, image = await event.rendered_resolve(tributes_involved, self, pack)
                attach = discord.File(image, description=f"{resolution_text}")
                embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 255),
                                      title=f"Event {event_no} for Cycle {self.cycle}",
                                      description=f"Active tributes remaining: {len(active_tributes)}\n"
                                      f"Event result:\n{truncatelast(resolution_text, 5900)}")
                embed.set_author(name=self.name, icon_url=self.logo)
                embed.set_image(url=f"attachment://{attach.filename}")
                await interaction.followup.send(embed=embed, file=attach)
            else:
                resolution_text = await event.resolve(tributes_involved, self)
            for tribute in tributes_involved:
                if tribute in active_tributes:
                    active_tributes.remove(tribute)
            logger.info("Resolution text: %s", resolution_text)
        logger.info("Cycle %s-%i complete.", cycle.name, self.cycle)
        if self.cycle_deaths and self.cycle % 2 == 1 and self.cycle != 0:
            logger.info("You hear %i cannon shot%s in the distance.", len(self.cycle_deaths),
                        "s" if len(self.cycle_deaths) > 1 else "")
            logger.info("The fallen tributes are: %s", ", ".join([tribute.name for tribute in self.cycle_deaths]))
            if interaction:
                image = await generate_endcycle(self.cycle, self.cycle_deaths, self, 0)
                attach = discord.File(image)
                embed = discord.Embed(
                    title=f"Fallen Tributes for Day {self.cycle // 2 + 1}",
                    color=discord.Color.from_rgb(255, 255, 255),
                    description=
                    f"You hear {len(self.cycle_deaths)} cannon shot{'s' if len(self.cycle_deaths) > 1 else ''}"
                    " in the distance.\nThe fallen tributes are:\n" + truncatelast(
                        "\n".join([f"{tribute.name} - {tribute.district.name}" for tribute in self.cycle_deaths]),
                        5900),
                )
                embed.set_author(name=self.name, icon_url=self.logo)
                embed.set_image(url=f"attachment://{attach.filename}")
                await interaction.followup.send(embed=embed, file=attach)
            self.cycle_deaths = []
        self.cycle += 1
        if cycle.max_use > 0:
            cycle.max_use -= 1
        if cycle.max_use == 0:
            logger.info("Cycle %s-%i reached max use.", cycle.name, self.cycle)
            self.cycles.remove(cycle)
        else:
            # Reset the cycle use for all events in the cycle.
            for event in cycle.events:
                event.cycle_use = event.max_cycle
        # Also reset the cycle use for all items.
        for item in self.items:
            item.base_event.cycle_use = item.base_event.max_cycle
            for event in item.events:
                event.cycle_use = event.max_cycle
        # Check if the simulation is over, so if there are only tributes from one district left.
        districts = []
        for tribute in self.alive:
            if tribute.district not in districts:
                districts.append(tribute.district)
        if len(districts) == 1:
            logger.info("Simulation %s complete.", self.name)
            self.cycle = -1
            if interaction:
                image = await generate_endcycle(self.cycle, self.alive, self, 1)
                attach = discord.File(image)
                embed = discord.Embed(color=discord.Color.gold(),
                                      title="Simulation Complete",
                                      description="Winners:\n" + "\n".join([tribute.name for tribute in self.alive]))
                embed.set_author(name=self.name, icon_url=self.logo)
                embed.set_image(url=f"attachment://{attach.filename}")
                await interaction.followup.send(embed=embed, file=attach)
            logger.info("Winner: %s", districts[0].name)
            logger.info("Alive tributes: %s", ", ".join([tribute.name for tribute in self.alive]))


class District:
    """The class representing a district.

    Attributes:
        name: The name of the district.
        color: The color of the district.
        members: The members of the district.
    """
    name: str
    color: str
    members: list["Tribute"]
    render: tuple[pathlib.Path, list[list[int]]] | None

    def __init__(self, data: dict):
        """Initialize the District object.

        Args:
            data: tomli interpreted data.
                Example: { name = "Eosphorous Faction", color = "#FF0400" }
        """
        self.name = data['name']
        self.color = data['color']
        self.members = []
        self.render = None

    def __str__(self):
        """Text representation of the district."""
        return f"TechSim District: {self.name}"

    def apply_allies(self):
        """Mark all members of the district as allies to each other."""
        for member in self.members:
            member.allies.update(set(self.members))
            member.allies.remove(member)  # Remove self from allies

    async def get_render(self, sim: Simulation) -> pathlib.Path:
        """Get an image representing the district

        Merges the status images of the tributes and places a name above them.

        Args:
            sim: The simulation that the district is part of

        """
        status = [[tribute.status, tribute.kills, tribute.effectivepower()] for tribute in self.members]
        if self.render and self.render[1] == status:
            return self.render[0]

        data_dir = const.PROG_DIR.joinpath("data")
        place = data_dir.joinpath("cast")
        landing = data_dir.joinpath("status")
        tribute_status_gets = [
            tribute.get_status_render(place.joinpath(f"{sim.cast.index(tribute)}")) for tribute in self.members
        ]
        tribute_status = await asyncio.gather(*tribute_status_gets)
        tribute_status = [Image.open(stat_img) for stat_img in tribute_status]
        member_c = len(self.members)

        base_image = Image.new("RGBA", (512 * member_c + 64 * (member_c + 1), 768), (0, 0, 0, 0))
        # The width is 512 for each member + 64 for each offset + 128 for sides
        draw = ImageDraw.Draw(base_image)
        font = ImageFont.truetype(FONT, size=128)
        draw.text(
            (base_image.width // 2, 0),
            self.name,
            font=font,
            anchor="ma",
            fill=self.color,
            stroke_fill=DRAW_ARGS["stroke_fill"],
            stroke_width=DRAW_ARGS["stroke_width"],
            align=DRAW_ARGS["align"],
        )
        gifs_to_process = []
        for i, tribute_status_image in enumerate(tribute_status):
            if tribute_status_image.format == "GIF":
                gifs_to_process.append((i, tribute_status_image))
                continue
            base_image.paste(tribute_status_image, (64 + i * 576, 128))
        if not gifs_to_process:
            landing = landing.joinpath(f"{sim.districts.index(self)}.png")
            base_image.save(landing, optimize=True)
        else:
            landing = landing.joinpath(f"{sim.districts.index(self)}.gif")
            max_frames = max([gif[1].n_frames for gif in gifs_to_process])
            status_img = [base_image.copy() for _ in range(max_frames)]
            for i, gif in gifs_to_process:
                for result_frame, gif_frame in zip(status_img, itertools.cycle(ImageSequence.all_frames(gif))):
                    result_frame.paste(gif_frame, (64 + i * 576, 128))
            durs = imgops.average_gif_durations([gif[1].info.get("duration", 50) for gif in gifs_to_process],
                                                max_frames)
            status_img[0].save(
                landing,
                save_all=True,
                append_images=status_img[1:],
                loop=0,
                duration=durs,
                optimize=True,
                disposal=2,
            )
        self.render = (landing, status)
        return landing


class Tribute:
    """The class representing a tribute.

    Attributes:
        name: The name of the tribute.
        status: The status of the tribute.
            0: Alive, 1: Dead
        power: The power of the tribute.
            Influences the probability of both being killed and committing murder.
        gender: The gender of the tribute.
            0: Female, 1: Male, 2: Neuter, 3: Pair, 4: Non-binary
        image: The image of the tribute (link)
        dead_image: The image of the tribute after death (link)
        allies: Tributes considered allies by this tribute.
        enemies: Tribute considered enemies by this tribute.
        items: Items held by the tribute
        kills: Kill count of the tribute.
        log: Log of all events this tribute has been a part of.
    """
    name: str
    gender: int
    image: str
    dead_image: str
    status: int
    power: int
    district: District | None
    allies: set["Tribute"]
    enemies: set["Tribute"]
    items: dict["Item", int]
    kills: int
    log: list[str]
    render: tuple[pathlib.Path, list[int]] | None

    def __init__(self, data: dict):
        """Initialize the Tribute object.

        Args:
            data: tomli interpreted data.
                Example:
                ```toml
                [[cast]]
                name = "Nina"
                gender = 0
                image = "https://i.imgur.com/X3BM59z.png"
                dead_image = "https://cdn.discordapp.com/attachments/718338933880258601/1187782049633935433/image.png"
                ```
        """
        self.name = data['name']
        self.gender = data['gender']
        self.image = data['image']
        self.dead_image = data['dead_image']
        self.status = 0
        self.power = BASE_POWER
        self.district = None
        self.allies = set()
        self.enemies = set()
        self.items = {}
        self.kills = 0
        self.log = []
        self.render = None

    def __str__(self):
        """Text representation of the tribute."""
        return f"TechSim Tribute: {self.name}"

    def effectivepower(self) -> int:
        """Resolve the effective power of the tribute.

        This is the power of the tribute, plus the power of all items the tribute has.
        If the power is 0 or less, it is set to 1.
        """
        power = self.power
        power += sum([item.power for item, count in self.items.items()])
        if power <= 0:
            power = 1
        return power

    def handle_relationships(
        self,
        tributes: list[list[int, int]],
        involved: list["Tribute"],
        relationship: Literal["allies", "enemies"],
    ):
        """Handle the relationship changes for the tribute.

        Args:
            tributes: The tributes to change the relationship with.
                The key is the tribute index (moved by 1), the value is the change.
            involved: The tributes involved in the event.
            relationship: The relationship to change.
                Relationships: enemies, allies
        """
        for tribt_id, modif in tributes:
            tribt_idr = tribt_id - 1
            if not modif and involved[tribt_idr] in getattr(self, relationship):
                getattr(self, relationship).remove(involved[tribt_idr])
            elif modif and involved[tribt_idr] not in getattr(self, relationship):
                getattr(self, relationship).add(involved[tribt_idr])
                if relationship == "allies" and involved[tribt_idr] in self.enemies:
                    self.enemies.remove(involved[tribt_idr])
                if relationship == "enemies" and involved[tribt_idr] in self.allies:
                    self.allies.remove(involved[tribt_idr])

    def relationshipchck(self, tributes: Union["Tribute", list["Tribute"]], relationship: str) -> bool:
        """Check whether the tribute has the requested relationship with any of the tributes.

        Args:
            tributes: The tributes to check.
            relationship: The relationship to check for.
                Relationships: enemies, notallies, neutral, notenemies, allies
        """
        if isinstance(tributes, Tribute):
            tributes = [tributes]
        match relationship:
            case "enemies":
                return any([tribute in self.enemies for tribute in tributes])
            case "notallies":
                return any([tribute not in self.allies for tribute in tributes])
            case "neutral":
                return any([tribute not in self.enemies.union(self.allies) for tribute in tributes])
            case "notenemies":
                return any([tribute not in self.enemies for tribute in tributes])
            case "allies":
                return any([tribute in self.allies for tribute in tributes])
            case _:
                raise ValueError("Invalid relationship.")

    async def fetch_image(
        self,
        itype: Literal["alive", "dead"] | str,
        place: pathlib.Path,
        session: aiohttp.ClientSession | None = None,
    ) -> pathlib.Path:
        """Fetch the image of the tribute.

        Args:
            itype: The type of image to fetch.
                Valid values: alive, dead
            place: The place to save the image to.
                The directory for the tribute.
            session: The aiohttp session to use for the request.
        """
        match itype:
            case "dead":
                image = self.dead_image
            case _:
                image = self.image

        if image == "BW" and itype == "dead":
            placepth = place.joinpath(f"{itype}.png")
        else:
            frmt = image.split(".")[-1]
            if frmt in ["jpg", "jpeg"]:
                frmt = "png"
            if frmt == "webp":
                frmt = "gif"  # Sadly, Discord doesn't support webp.
            if frmt not in ["png", "gif"]:
                raise ValueError(f"Invalid image format {frmt} for tribute {self.name}.")
            placepth = place.joinpath(f"{itype}.{frmt}")

        if placepth.exists():
            return placepth

        if not session:
            raise ValueError(f"No session and image not found for {placepth}.")

        if image == "BW" and itype == "dead":
            img = Image.open(await self.fetch_image("alive", place, session))
            img = img.convert("LA")
            img = imgops.resize(img, border_c=self.district.color)
            img.save(placepth, optimize=True)
            return placepth

        try:
            async with session.get(image) as response:
                if not response.ok:
                    raise ValueError(f"Could not fetch image for tribute {self.name}.")
                img = Image.open(io.BytesIO(await response.read()))
        except aiohttp.ClientError:
            await asyncio.sleep(10)  # Retries the download if a ClientError happened
            async with session.get(image) as response:
                if not response.ok:
                    raise ValueError(f"Could not fetch image for tribute {self.name}.")
                img = Image.open(io.BytesIO(await response.read()))

        img = imgops.resize(img, border_c=self.district.color)
        if isinstance(img, tuple):
            img[0][0].save(placepth, save_all=True, append_images=img[0][1:], **img[1], optimize=True, disposal=2)
        else:
            img.save(placepth, optimize=True)
        return placepth

    async def get_status_render(self, place: pathlib.Path | None) -> pathlib.Path:
        """Get an assembled image representing the tribute.

        With the status, kills and effective power.

        Args:
            place: The place to save the image to.
                The directory for the tribute.
        """
        status = [self.status, self.kills, self.effectivepower()]
        if self.render and self.render[1] == status:
            return self.render[0]
        if not place:
            if self.render:
                place = self.render[0].parent
            else:
                raise ValueError(f"Neither place nor old render provided for tribute {self}")
        if self.status:
            user_image = Image.open(await self.fetch_image("dead", place))
        else:
            user_image = Image.open(await self.fetch_image("alive", place))

        base_image = Image.new("RGBA", (512, 640), (0, 0, 0, 0))
        font = ImageFont.truetype(FONT, size=32)
        text = (f"{self.name}\n"
                f"Status: {['Alive', 'Dead'][self.status]}\n"
                f"Kills: {self.kills}\n"
                f"Power: {self.effectivepower()}\n")
        draw = ImageDraw.Draw(base_image)
        draw.text((256, 670), text, font=font, anchor="md", **DRAW_ARGS)
        if user_image.format == "PNG":
            status_img = base_image
            status_img.paste(user_image)
            landing = place.joinpath("status.png")
            status_img.save(landing, optimize=True)
        else:
            status_img = [base_image.copy() for _ in range(user_image.n_frames)]
            for sts_frame, usr_frame in zip(status_img, ImageSequence.Iterator(user_image)):
                sts_frame.paste(usr_frame)
            landing = place.joinpath("status.gif")
            status_img[0].save(
                landing,
                save_all=True,
                append_images=status_img[1:],
                **user_image.info,
                optimize=True,
                disposal=2,
            )
        self.render = (landing, status)
        return landing


class Cycle:
    """The class representing a cycle type.

    Attributes:
        name: The name of the cycle.
        text: The text of the cycle.
            Displayed at the start of the cycle. Optional.
        allow_item_events: Whether item events are allowed.
            This is specifically for the extra events that happen when a tribute has an item.
            Not to be confused with the base events of items, which are always imported if the cycle matches.
            TOML value: "all" for all items, "cycle" for items that are in the cycle, "none" for no items.
        weight: The weight of the cycle.
            Influences the probability of the cycle happening. For hardcoded cycle enter cycle number in quotes.
            Positive numbers are weights for the day period (not divisible by 2), negative numbers are weights for the
            night period (divisible by 2). For standard day/night cycles enter big positive and negative numbers.
            Example: 1000 for day, -1000 for night, "0" for bloodbath and 1 for a feast event.
        max_use: The maximum amount of times the cycle can happen. -1 for infinite.
        events: The events of the cycle.
    """
    name: str
    text: str | None
    allow_item_events: str
    weight: int | str
    max_use: int
    events: list["Event"]

    def __init__(self, data: dict):
        """Initialize the Cycle object.

        Args:
            data: tomli interpreted data.
                Example:
                ```toml
                [[cycles]]
                name = "Day"
                allow_item_events = 1
                [[cycles.events]]
                /// REMOVED FOR BREVITY, REFER EVENT OBJECT ///
                ```
        """
        self.name = data['name']
        self.text = data.get('text', None)
        self.allow_item_events = data.get('allow_item_events', "none")
        self.weight = data.get('weight', 1)
        self.max_use = data.get('max_use', -1)
        self.events = [Event(event, self) for event in data['events']]

    def __str__(self):
        """Text representation of the cycle."""
        return f"TechSim Cycle: {self.name}"

    async def render_start(self, current_cycle: int) -> pathlib.Path:
        """Get an image representing the start of the cycle."""
        place = const.PROG_DIR.joinpath("data", "cycles", f"{current_cycle}", f"start.png")
        image = Image.new("RGBA", (512, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(FONT, size=64)
        y_print = 64 // 2
        anchor = "mm"
        if self.text:
            y_print = 0
            anchor = "ma"
            font = ImageFont.truetype(FONT, size=16)
            draw_max_text(image, self.text, (512, 32), "md", (256, 64))
        draw.text((256, y_print), f"Cycle {current_cycle}: {self.name}", anchor=anchor, font=font, **DRAW_ARGS)
        image.save(place, optimize=True)
        return place


class Event:
    """The class representing an event.

    Attributes:
        text: The text of the event.
            Placeholders:
            $TributeX - The name of the tribute in the Xth position.
            $DistrictX - The name of the district the tribute in the Xth position belongs to.
            $PowerX - The power of the tribute in the Xth position.
            $SPX - The subjective pronoun of the tribute in the Xth position.
            $OPX - The objective pronoun of the tribute in the Xth position.
            $PPX - The possessive pronoun of the tribute in the Xth position.
            $RPX - The reflexive pronoun of the tribute in the Xth position.
            $PAX - The possessive adjective of the tribute in the Xth position.
            $ItemLX_Y - The name of the Yth item lost by the tribute in the Xth position.
            $ItemGX_Y - The name of the Yth item gained by the tribute in the Xth position.
        cycle: The cycle the event belongs to.
        weight: The weight of the event.
            Influences the probability of the event happening.
        max_use: The maximum amount the event can happen. -1 for infinite.
        max_cycle: The maximum amount the event can happen in a cycle. -1 for infinite.
        cycle_use: The number of times the event can happen in the current cycle.
        item: The item the event is attached to.
            Defaults to None, which means the event is not attached to an item.
            In ItemL and ItemG, the item is the specific item to lose or gain.
        tribute_changes: The changes in the tributes after the event.
            Write as a list with each tribute's changes as a dictionary.
            Valid keys:
            Power - A change in power. Can be positive or negative.
                TOML key: power
            PowerN - A change in power, but not above or below base power (BASE_POWER). It Can be positive or negative.
                TOML key: powern
            Status - 0 for alive, 1 for dead. It Can be theoretically used to revive tributes.
                TOML key: status
            ItemU - Item use. Use a specified number of charges from the event item.
                Please make sure that the tribute has enough charges, using ItemStatus in tribute_requirements.
                Not checking can cause the item to gain infinite charges.
                TOML key: itemu
            ItemL - Item loss. Either the event item (0) or a number of items for the tribute to lose.
                Processed with Priority, before any other changes.
                TOML key: iteml
            ItemG - Item gain. Either the event item (0) or a number of items to gain from this event's loss pool.
                TOML key: itemg
            Kills - A change in kill count. Positive.
                TOML key: kills
            Allies - A change in allies. List of [tribute_id, change] where change is 0 for remove, 1 for adding.
                Effectively a list of lists [tribute_id, change].
                TOML key: allies
            Enemies - A change in enemies. List of [tribute_id, change] where change is 0 for remove, 1 for adding.
                Effectively a list of lists [tribute_id, change].
                TOML key: enemies
            Example: [ { power = 100 } ]
        tribute_requirements: The requirements for the tributes in the event.
            Write as a list with each tribute's requirements as a dictionary.
            Valid keys:
            Status - Default is 0, override to 1 for a dead tribute.
                You *cannot* require the first tribute to be dead, but you can require so for any other tribute.
                TOML key: status
            Power - Requre a specific power, so a list of [operation, power].
                Allowed operations "=" for equal, "<" for less than, ">" for greater than.
                Power is the value to compare to.
                TOML key: power
            ItemStatus - Requre a specific item usage status, so a list of [operation, status].
                See `Power` parameter for operations. The item is the event item.
                TOML key: item_status
            Relationship - Default not required, override to require a specific relationship with specified tributes.
                Relationship is a list of array/dictionary { tribute_id = relationship } where relationship is
                Relationships: enemies, notallies, neutral, notenemies, allies
                TOML key: relationship
            Example: [ { relationship = { 2 = "notallies" } }, { relationship = { 1 = "allies" } } ]
                Tribute 1 does not consider Tribute 2 an ally, Tribute 2 considers Tribute 1 an ally.
        """
    text: string.Template
    cycle: Cycle | list[Cycle]
    weight: int
    max_use: int
    max_cycle: int
    cycle_use: int
    item: Optional["Item"]
    tribute_changes: list[dict]
    tribute_requirements: list[dict]

    def __init__(self, data: dict, cycle: Cycle | list[Cycle], item: Optional["Item"] = None):
        """Initialize the Event object.

        Args:
            data: tomli interpreted data.
                Example:
                ```toml
                [[cycles.events]] # or [[items.events]], or [items.base_event]
                text = "$Tribute1 yeeted $Tribute2 into the void."
                weight = 1
                max_use = -1
                max_cycle = -1
                tribute_changes = [
                    { "kills": 1 },
                    { "status": 1 }
                ]
                tribute_requirements = [
                    { "enemies": [1] },
                    { }
                ]
                ```
            cycle: The cycle the event belongs to.
            item: The item the event is attached to.
        """
        self.text = string.Template(data['text'])
        self.cycle = cycle
        self.weight = data.get('weight', 1)
        self.max_use = data.get('max_use', -1)
        self.max_cycle = data.get('max_cycle', -1)
        self.cycle_use = self.max_cycle
        self.item = item
        self.tribute_changes: list[dict] = data['tribute_changes']
        self.tribute_requirements: list[dict] = data.get('tribute_requirements', [])

    def __str__(self):
        """Return the text representation of the event."""
        return f"TechSim Event: {self.text.template}"

    def check_requirements(self, tribute: Tribute, placement: int) -> bool:
        """Check whether the tribute can meet the requirements for the event/placement.

        Args:
            tribute: The tribute to check.
            placement: The placement of the tribute.
                Using the python list index system, so 0 is the first tribute, 1 the second, etc.
        """
        if self.max_use == 0 or self.cycle_use == 0:
            return False
        if not self.tribute_requirements:
            if tribute.status:
                return False
            return True
        # If tribute_requirements exist, they have to have as many entries as there are tributes involved.
        requirements = self.tribute_requirements[placement]
        if requirements.get('status', 0) != tribute.status:
            return False
        if requirements.get('power', 'MISSING') != 'MISSING':
            operation, power = requirements['power']
            if operation == "=" and tribute.effectivepower() != power:
                return False
            if operation == ">" and tribute.effectivepower() <= power:
                return False
            if operation == "<" and tribute.effectivepower() >= power:
                return False
        if requirements.get('item_status', 'MISSING') != 'MISSING':
            if not self.item:
                raise ValueError("Event has item requirements but is not attached to an item.")
            # Assuming the Tribute has the item, otherwise the event would not be in the pool.
            operation, status = requirements['item_status']
            if operation == "=" and tribute.items[self.item] != status:
                return False
            if operation == ">" and tribute.items[self.item] <= status:
                return False
            if operation == "<" and tribute.items[self.item] >= status:
                return False
        # Relationship requirements are a tad too complicated, so we handle them during event resolution.
        return True

    async def affiliationresolution(self, tribute: Tribute, active: list[Tribute],
                                    simstate: Simulation) -> list[Tribute]:
        """Resolve the affiliation requirements for the event.

        Args:
            tribute: The tribute to resolve the event for.
            active: List of tributes not yet involved in any event during the current cycle.
            simstate: The simulation state.

        Returns:
            The chosen tributes.
        """
        if len(self.tribute_changes) == 1:
            # If there is only one tribute involved, we return the tribute.
            return [tribute]
        relationship_reqs: list[dict[str, str]] = []
        empty_relationship = 0
        for reqs in self.tribute_requirements:
            if reqs.get('relationship', 'MISSING') != 'MISSING':
                relationship_reqs.append(reqs['relationship'])
                continue
            relationship_reqs.append({})
            empty_relationship += 1

        if not self.tribute_requirements or empty_relationship == len(self.tribute_requirements):
            # If there are no relationship requirements, we return the tribute + random required active tributes.
            tributes = [tribute]
            active_copy = active.copy()
            active_copy.remove(tribute)
            pos = 1
            if empty_relationship:
                active_copy += simstate.dead
            positional_active = active_copy.copy()
            while len(tributes) < len(self.tribute_changes):
                if not active_copy or not positional_active:
                    logger.warning("Could not resolve tributes for event %s.", self.text.template)
                    return []
                mpower = max([tribute.effectivepower() for tribute in positional_active]) + 1
                wg = [mpower - tribute.effectivepower() for tribute in positional_active]
                fit = random.choices(positional_active, weights=wg)[0]
                if self.check_requirements(fit, pos):
                    tributes.append(fit)
                    active_copy.remove(fit)
                    positional_active = active_copy.copy()
                    pos += 1
                else:
                    positional_active.remove(fit)
                    # Remove the tribute from the positional active list, so it can't be chosen again.
                    # But don't remove it from the active list, so it can be chosen again for other positions.
            return tributes

        # We start operating mostly on sets below this point.

        activep = set(active + simstate.dead)
        activep.remove(tribute)
        # We have the relationship_reqs already extracted, so we can use them, and make sure to use
        # self.check_requirements(tribute, placement) to check the other requirements.
        # To be considered a tribute has to be in activep, se we can consider that all the possible tributes are there.

        possible_resolutions: list[set[Tribute]] = [set() for _ in range(len(self.tribute_changes))]
        possible_resolutions[0].add(tribute)
        for tribute_pos in range(2, len(self.tribute_requirements) + 1):
            match relationship_reqs[0].get(str(tribute_pos), "any"):
                case "enemies":
                    possible_resolutions[tribute_pos - 1] = activep.intersection(tribute.enemies)
                case "notallies":
                    possible_resolutions[tribute_pos - 1] = activep.difference(tribute.allies)
                case "neutral":
                    possible_resolutions[tribute_pos - 1] = activep.difference(tribute.enemies.union(tribute.allies))
                case "notenemies":
                    possible_resolutions[tribute_pos - 1] = activep.difference(tribute.enemies)
                case "allies":
                    possible_resolutions[tribute_pos - 1] = activep.intersection(tribute.allies)
                case _:
                    possible_resolutions[tribute_pos - 1] = activep.copy()
            # Remove tributes that don't meet the requirements.
        for i in range(len(possible_resolutions)):
            possible_resolutions[i] = {
                tribute for tribute in possible_resolutions[i] if self.check_requirements(tribute, i)
            }
            if not possible_resolutions[i]:
                logger.debug("Could not resolve tributes for event %s.", self.text.template)
                return []

        async def sub_resolve(
            sub_pos: int,
            possibilities: list[set[Tribute]],
            trail: list[Tribute],
        ) -> Optional[list[Tribute]]:
            """Recursive resolution helper function.

            Args:
                sub_pos: The position we are resolving. Python index.
                possibilities: The possible tributes for each position.
                trail: The trail of tributes we have already chosen.
            """
            sub_mpower = max([trbt.effectivepower() for trbt in possibilities[sub_pos]]) + 1
            sub_wg = []
            listed_possibilities = []
            for possibility in possibilities[sub_pos]:
                # In one loop, so we don't mess up the weight-tribute correspondence.
                sub_wg.append(sub_mpower - possibility.effectivepower())
                listed_possibilities.append(possibility)
            while listed_possibilities:
                g_breaker = False
                sub_choice = random.choices(listed_possibilities, weights=sub_wg)[0]
                # First, we check if the choice's requirements for previous tributes are met,
                # i.e., if the choice has a relationship requirement regarding the previous tribute.
                for j in range(sub_pos):
                    relationship = relationship_reqs[j].get(str(sub_pos + 1), "any")
                    match relationship:
                        case "enemies":
                            if trail[j] not in sub_choice.enemies:
                                g_breaker = True
                                break
                        case "notallies":
                            if trail[j] in sub_choice.allies:
                                g_breaker = True
                                break
                        case "neutral":
                            if trail[j] in sub_choice.enemies.union(sub_choice.allies):
                                g_breaker = True
                                break
                        case "notenemies":
                            if trail[j] in sub_choice.enemies:
                                g_breaker = True
                                break
                        case "allies":
                            if trail[j] not in sub_choice.allies:
                                g_breaker = True
                                break
                        case _:
                            continue
                if g_breaker or sub_choice in trail:
                    # If the choice's requirements for previous tributes are not met, we remove it from the pool.
                    sub_wg.remove(sub_wg[listed_possibilities.index(sub_choice)])
                    listed_possibilities.remove(sub_choice)
                    continue
                # If the choice's requirements for previous tributes are met, we intersect the possibilities
                # with the choice's requirements for the current tribute.
                if sub_pos == len(possibilities) - 1:
                    # If we are at the last position, we can just return the trail + the choice.
                    # We don't need to check the requirements for the next tribute because there is none.
                    return trail + [sub_choice]
                sub_possibilities = possibilities.copy()
                sub_possibilities[sub_pos] = {sub_choice}
                for j in range(sub_pos + 1, len(possibilities)):
                    match relationship_reqs[sub_pos].get(str(j + 1), "any"):
                        case "enemies":
                            sub_possibilities[j] = sub_possibilities[j].intersection(sub_choice.enemies)
                        case "notallies":
                            sub_possibilities[j] = sub_possibilities[j].difference(sub_choice.allies)
                        case "neutral":
                            sub_possibilities[j] = sub_possibilities[j].difference(
                                sub_choice.enemies.union(sub_choice.allies))

                        case "notenemies":
                            sub_possibilities[j] = sub_possibilities[j].difference(sub_choice.enemies)
                        case "allies":
                            sub_possibilities[j] = sub_possibilities[j].intersection(sub_choice.allies)
                        case _:
                            continue
                    if sub_choice in sub_possibilities[j]:
                        sub_possibilities[j].remove(sub_choice)
                    if not sub_possibilities[j]:
                        g_breaker = True
                        break
                if g_breaker:
                    # If the choice's requirements for the next tributes are not met, we remove it from the pool.
                    sub_wg.remove(sub_wg[listed_possibilities.index(sub_choice)])
                    listed_possibilities.remove(sub_choice)
                    continue
                # If the intersection is not empty, we add the choice to the trail and continue resolving.
                trail.append(sub_choice)
                result = await sub_resolve(sub_pos + 1, sub_possibilities, trail)
                if result:
                    return result
                trail.pop()
                sub_wg.remove(sub_wg[listed_possibilities.index(sub_choice)])
                listed_possibilities.remove(sub_choice)
            return None

        resolved_tributes = await sub_resolve(1, possible_resolutions, [tribute])
        if resolved_tributes is None:
            logger.debug("Could not resolve tributes for event %s.", self.text.template)
            return []
        return resolved_tributes

    async def resolve(self, tributes: list[Tribute], simstate: Simulation) -> str:
        """Resolve the event for the given tributes.

        Resolves the tribute changes and returns the resolution text.

        Args:
            tributes: The tributes to resolve the event for.
            simstate: The simulation state.
        """
        itempool = []
        item_loses = {}
        item_gains = {}
        resolutuion_strings = []
        # Priority processing loop
        for tribute_id, changes in enumerate(self.tribute_changes):
            for change, value in changes.items():
                affected = tributes[tribute_id]
                match change:
                    case "iteml":
                        val = value
                        if val == 0:
                            if not self.item:
                                raise ValueError("Event has event item changes but is not attached to an item.")
                            itempool.append((self.item, affected.items.pop(self.item)))
                            item_loses[affected] = [self.item]
                            continue
                        while affected.items and val > 0:
                            item = random.choice(list(affected.items.keys()))
                            itempool.append((item, affected.items.pop(item)))
                            if affected in item_loses:
                                item_loses[affected].append(item)
                            else:
                                item_loses[affected] = [item]
                            val -= 1
                        continue
                    case _:
                        continue
        # Normal processing loop
        for tribute_id, changes in enumerate(self.tribute_changes):
            for change, value in changes.items():
                affected = tributes[tribute_id]
                match change:
                    case "power":
                        affected.power += value
                        continue
                    case "powern":
                        if value > 0:
                            # If the power is positive, we want to add it with a ceiling of BASE_POWER.
                            affected.power += min(affected.power + value, BASE_POWER)
                        elif value < 0:
                            # If the power is negative, we want to subtract it with a floor of BASE_POWER.
                            affected.power += max(affected.power + value, BASE_POWER)
                        continue
                    case "status":
                        affected.status = value
                        if value:
                            simstate.alive.remove(affected)
                            simstate.dead.append(affected)
                            simstate.cycle_deaths.append(affected)
                        else:
                            simstate.alive.append(affected)
                            simstate.dead.remove(affected)
                        continue
                    case "itemu":
                        if not self.item:
                            raise ValueError("Event has event item changes but is not attached to an item.")
                        affected.items[self.item] -= value
                        if affected.items[self.item] == 0:
                            affected.items.pop(self.item)
                            destruction = self.item.textl.safe_substitute(Tribute1=affected.name)
                            resolutuion_strings.append(destruction)
                            affected.log.append(destruction)
                        continue
                    case "itemg":
                        if value == 0:
                            if not self.item:
                                raise ValueError("Event has event item changes but is not attached to an item.")
                            items = [(self.item, self.item.use_count)]
                            item_gains[affected] = [self.item]
                        else:
                            items = []
                            random.shuffle(itempool)
                            while value > 0 and itempool:
                                items.append(itempool.pop(0))
                                value -= 1
                        for item, count in items:
                            if item in affected.items:
                                affected.items[item] += count
                            else:
                                affected.items[item] = count
                            if affected in item_gains:
                                item_gains[affected].append(item)
                            else:
                                item_gains[affected] = [item]
                        continue
                    case "kills":
                        affected.kills += value
                        continue
                    case "allies":
                        affected.handle_relationships(value, tributes, "allies")
                    case "enemies":
                        affected.handle_relationships(value, tributes, "enemies")
                    case _:
                        continue
        resolution_dict = {}
        for tribute_id, tribute in enumerate(tributes):
            # Generate all the Placeholders
            resolution_dict[f"Tribute{tribute_id + 1}"] = tribute.name
            resolution_dict[f"District{tribute_id + 1}"] = tribute.district.name
            resolution_dict[f"Power{tribute_id + 1}"] = str(tribute.power)
            resolution_dict[f"SP{tribute_id + 1}"] = SPronouns[tribute.gender]
            resolution_dict[f"OP{tribute_id + 1}"] = OPronouns[tribute.gender]
            resolution_dict[f"PP{tribute_id + 1}"] = PPronouns[tribute.gender]
            resolution_dict[f"RP{tribute_id + 1}"] = RPronouns[tribute.gender]
            resolution_dict[f"PA{tribute_id + 1}"] = PAdjectives[tribute.gender]
            for i, item in enumerate(item_loses.get(tribute, [])):
                resolution_dict[f"ItemL{tribute_id + 1}_{i + 1}"] = item.name
            for i, item in enumerate(item_gains.get(tribute, [])):
                resolution_dict[f"ItemG{tribute_id + 1}_{i + 1}"] = item.name
        resolutuion_strings.insert(0, self.text.safe_substitute(**resolution_dict))
        for tribute in tributes:
            tribute.log.append(resolutuion_strings[0])
        self.max_use -= 1
        self.cycle_use -= 1
        return "\n".join(resolutuion_strings)

    async def rendered_resolve(self, tributes: list[Tribute], simstate: Simulation,
                               pack: tuple[pathlib.Path, int]) -> tuple[str, pathlib.Path]:
        """Resolve the event with a rendered image.

        Resolves the tribute changes and returns the resolution text and the rendered image.

        Args:
            tributes: The tributes to resolve the event for.
            simstate: The simulation state.
            pack: Tuple of cycle directory and event number
        """
        tribute_c = len(tributes)
        base_image = Image.new("RGBA", (512 * tribute_c + 64 * (tribute_c + 1), 640), (0, 0, 0, 0))
        tribute_place = const.PROG_DIR.joinpath("data", "cast")
        tribute_images = await asyncio.gather(*[
            tribute.fetch_image(
                ["alive", "dead"][tribute.status],
                tribute_place.joinpath(f"{simstate.cast.index(tribute)}"),
            ) for tribute in tributes
        ])
        tribute_images = [Image.open(im) for im in tribute_images]
        text = await self.resolve(tributes, simstate)
        draw_max_text(base_image, text, (base_image.width, 128), "md", (base_image.width // 2, 640))
        gifs_to_process = []
        for i, tribute_image in enumerate(tribute_images):
            if tribute_image.format == "GIF":
                gifs_to_process.append((i, tribute_image))
                continue
            base_image.paste(tribute_image, (64 + i * 576, 0))
        if not gifs_to_process:
            landing = pack[0].joinpath(f"{pack[1]}.png")
            base_image.save(landing, optimize=True)
        else:
            landing = pack[0].joinpath(f"{pack[1]}.gif")
            max_frames = max([gif[1].n_frames for gif in gifs_to_process])
            status_img = [base_image.copy() for _ in range(max_frames)]
            for i, gif in gifs_to_process:
                for result_frame, gif_frame in zip(status_img, itertools.cycle(ImageSequence.all_frames(gif))):
                    result_frame.paste(gif_frame, (64 + i * 576, 0))
            durs = imgops.average_gif_durations([gif[1].info.get("duration", 50) for gif in gifs_to_process],
                                                max_frames)
            status_img[0].save(
                landing,
                save_all=True,
                append_images=status_img[1:],
                loop=0,
                duration=durs,
                optimize=True,
                disposal=2,
            )
        return text, landing


class Item:
    """The class representing an item.

    Attributes:
        name: The name of the item.
        textL: The text of the item when lost.
            The only placeholder here is $Tribute1.
        power: The power of the item.
        cycles: The cycles the item can be found in.
        use_count: The amount of times the item can be used. -1 for infinite.
        base_event: The base event of the item, so the event that causes the item to be found.
        events: The events that can happen with this item.
    """
    name: str
    textl: string.Template
    power: int
    cycles: list[Cycle]
    use_count: int
    base_event: Event
    events: list[Event]

    def __init__(self, data: dict, cycles: list[Cycle]):
        """Initialize the Item object.

        Args:
            data: tomli interpreted data.
                Example:
                ```toml
                [[items]]
                name = "Sword"
                power = 100
                cycles = ["Day", "Bloodbath"]
                use_count = -1
                # The cycle is a special attribute attached to the base_event.
                [items.base_event]
                text = "$Tribute1 found a sword."
                /// REMOVED FOR BREVITY, REFER EVENT OBJECT ///
                [[items.events]]
                /// REMOVED FOR BREVITY, REFER EVENT OBJECT ///
                ```
            cycles: The cycle library for the simulation.
        """
        self.name = data['name']
        self.textl = string.Template(data.get('text', f"$Tribute1's {self.name} broke."))
        self.power = data.get('power', 0)
        self.cycles = [cycle for cycle in cycles if cycle.name in data['cycles']]
        self.use_count = data.get('use_count', -1)
        self.base_event = Event(data['base_event'], self.cycles, self)
        event_cycles: list[Cycle] = []
        for cycle in cycles:
            if cycle.allow_item_events == "all" or (cycle.allow_item_events == "cycle" and
                                                    cycle.name in data['cycles']):
                event_cycles.append(cycle)
        self.events = [Event(event, event_cycles, self) for event in data['events']]

    def __str__(self):
        """Return the name of the item."""
        return f"TechSim Item: {self.name}"


async def main():
    """Testing loop."""
    sim = Simulation(
        const.PROG_DIR.joinpath("data", "cast.toml"),
        const.PROG_DIR.joinpath("data", "events.toml"),
        None,
    )
    await sim.ready(None)
    # Place for testing code


if __name__ == "__main__":
    asyncio.run(main())
