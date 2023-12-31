"""Data structures for the project.

This is the module with the data structures for the TechSim.
"""
import random
import colorsys
import tomllib
import logging
import sys  # Temporary logging thingie
from pathlib import Path
from string import Template
from typing import Optional, Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_POWER = 500

# 0: Female, 1: Male, 2: Neuter, 3: Pair, 4: Non-binary
SPronouns = ["she", "he", "it", "they", "they"]
OPronouns = ["her", "him", "it", "them", "them"]
PPronouns = ["hers", "his", "its", "theirs", "theirs"]
RPronouns = ["herself", "himself", "itself", "themself", "themself"]
PAdjectives = ["her", "his", "its", "their", "their"]


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
    cycle: int
    alive: list["Tribute"]
    dead: list["Tribute"]
    cycle_deaths: list["Tribute"]

    def __init__(self, cast_file: Path, events_file: Path):
        """Initialize the Simulation object."""
        file = open(cast_file, "rb")
        data = tomllib.load(file)
        file.close()
        self.cycle = -2
        self.name: str = data['name']
        self.logo: str = data['logo']
        self.cast = [Tribute(tribute) for tribute in data['cast']]
        self.districts = [District(district) for district in data['districts']]
        file = open(events_file, "rb")
        data = tomllib.load(file)
        self.cycles = [Cycle(cycle) for cycle in data['cycles']]
        self.items = [Item(item, self.cycles) for item in data['items']]
        file.close()

    def __str__(self):
        """Text representation of the simulation."""
        return f"TechSim Simulation: {self.name}"

    def ready(self, seed: str | None, districtrand: bool = False, recolor: bool = False):
        """Ready up!

        This is the method that prepares the simulation for running.

        Args:
            seed: The seed for the simulation
                None for random.
            districtrand: Whether to randomize the district members.
            recolor: Whether to recolor the districts to the standard HUE rotation.
        """
        logger.info("Beginning simulation '%s' ready up procedure.", self.name)
        random.seed(seed)
        if districtrand:
            logger.info("Randomizing district members.")
            random.shuffle(self.cast)
        if recolor:
            logger.info("Recoloring districts.")
            max_hue = 360
            increment = max_hue // len(self.districts)
            offset = random.randint(0, increment)
            for i, district in enumerate(self.districts):
                rgb = [int(x * 255) for x in colorsys.hsv_to_rgb((i * increment + offset) / 360, 1.0, 1.0)]
                color = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])
                district.color = color
        logger.info("Assigning districts.")
        tid = 0
        mpd = len(self.cast) // len(self.districts)
        for district in self.districts:
            for tribute in range(tid, tid + mpd):
                self.cast[tribute].district = district
                district.members.add(self.cast[tribute])
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
            return
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
        if not randomevents and not resolved_cycle:
            raise ValueError("Configuration error: No cycles available.")
        return resolved_cycle or random.choices(randomevents, weights=[abs(cycle.weight) for cycle in randomevents])[0]

    def computecycle(self):
        """Compute the next cycle.

        This is the method that computes the next cycle.
        So the whole day/night/special event cycle.
        """
        if self.cycle in [-2, -1]:
            logger.warning("Simulation '%s' is not ready.", self.name)
            return
        cycle = self.getcycle()
        logger.info("Beginning cycle %s.", cycle.name)
        if cycle.text is not None:
            logger.info("Displaying cycle text.")
            # TODO: Actually displaying anything.
        logger.info("Computing events.")
        active_tributes = self.alive.copy()
        cycle_events = cycle.events
        for item in self.items:
            if cycle in item.cycles:
                cycle_events.append(item.base_event)
        while active_tributes:
            possible_events = []
            wg = [tribute.effectivepower() for tribute in active_tributes]
            tribute: "Tribute" = random.choices(active_tributes, weights=wg)[0]
            for item, _ in tribute.items.items():
                if (cycle in item.cycles and cycle.allow_item_events == "special") or cycle.allow_item_events == "all":
                    possible_events.extend(item.events)
            for event in cycle_events:
                if event.check_requirements(tribute, 0):
                    possible_events.append(event)
            if not possible_events:
                logger.warning("Could not find event for tribute '%s'.", tribute.name)
                continue
            event = random.choices(possible_events, weights=[event.weight for event in possible_events])[0]
            logger.debug("Resolving event '%s'.", event.text.template)
            tributes_involved = event.affiliationresolution(tribute, active_tributes, self)
            if not tributes_involved:
                continue  # Already logged in affiliationresolution
            resolution_text = event.resolve(tributes_involved, self)
            for tribute in tributes_involved:
                if tribute in active_tributes:
                    active_tributes.remove(tribute)
            # TODO: Actually displaying anything.
            logger.info("Resolution text: %s", resolution_text)
        logger.info("Cycle %s-%i complete.", cycle.name, self.cycle)
        if self.cycle_deaths and int(cycle.weight) % 2 == 0 and int(cycle.weight) != 0:
            logger.info("You hear %i cannon shot%s in the distance.", len(self.cycle_deaths),
                        "s" if len(self.cycle_deaths) > 1 else "")
            logger.info("The fallen tributes are: %s", ", ".join([tribute.name for tribute in self.cycle_deaths]))
            # TODO: Display this.
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
        # Also rest the cycle use for all items.
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
    members: set["Tribute"]

    def __init__(self, data: dict):
        """Initialize the District object.

        Args:
            data: tomli interpreted data.
                Example: { name = "Eosphorous Faction", color = "#FF0400" }
        """
        self.name = data['name']
        self.color = data['color']
        self.members = set()

    def __str__(self):
        """Text representation of the district."""
        return f"TechSim District: {self.name}"

    def apply_allies(self):
        """Mark all members of the district as allies to each other."""
        for member in self.members:
            member.allies.update(self.members)
            member.allies.remove(member)  # Remove self from allies


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

    def handle_relationships(self, tributes: list[list[int, int]], involved: list["Tribute"], relationship: str):
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
    text: Template
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
        self.text = Template(data['text'])
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
            if operation == "=" and tribute.power != power:
                return False
            if operation == ">" and tribute.power <= power:
                return False
            if operation == "<" and tribute.power >= power:
                return False
        if requirements.get('item_status', 'MISSING') != 'MISSING':
            if self.item is None:
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

    def affiliationresolution(self, tribute: Tribute, active: list[Tribute], simstate: Simulation) -> list[Tribute]:
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

        def sub_resolve(sub_pos: int, possibilities: list[set[Tribute]],
                        trail: list[Tribute]) -> Optional[list[Tribute]]:
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
                glblbrkr = False
                sub_choice = random.choices(listed_possibilities, weights=sub_wg)[0]
                # First, we check if the choice's requirements for previous tributes are met,
                # i.e., if the choice has a relationship requirement regarding the previous tribute.
                for j in range(sub_pos):
                    relationship = relationship_reqs[j].get(str(sub_pos + 1), "any")
                    match relationship:
                        case "enemies":
                            if trail[j] not in sub_choice.enemies:
                                glblbrkr = True
                                break
                        case "notallies":
                            if trail[j] in sub_choice.allies:
                                glblbrkr = True
                                break
                        case "neutral":
                            if trail[j] in sub_choice.enemies.union(sub_choice.allies):
                                glblbrkr = True
                                break
                        case "notenemies":
                            if trail[j] in sub_choice.enemies:
                                glblbrkr = True
                                break
                        case "allies":
                            if trail[j] not in sub_choice.allies:
                                glblbrkr = True
                                break
                        case _:
                            continue
                if glblbrkr:
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
                        glblbrkr = True
                        break
                if glblbrkr:
                    # If the choice's requirements for the next tributes are not met, we remove it from the pool.
                    sub_wg.remove(sub_wg[listed_possibilities.index(sub_choice)])
                    listed_possibilities.remove(sub_choice)
                    continue
                # If the intersection is not empty, we add the choice to the trail and continue resolving.
                trail.append(sub_choice)
                result = sub_resolve(sub_pos + 1, sub_possibilities, trail)
                if result is not None:
                    return result
                trail.pop()
                sub_wg.remove(sub_wg[listed_possibilities.index(sub_choice)])
                listed_possibilities.remove(sub_choice)
            return None

        resolved_tributes = sub_resolve(1, possible_resolutions, [tribute])
        if resolved_tributes is None:
            logger.debug("Could not resolve tributes for event %s.", self.text.template)
            return []
        return resolved_tributes

    def resolve(self, tributes: list[Tribute], simstate: Simulation) -> str:
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
                        if self.item is None:
                            raise ValueError("Event has item requirements but is not attached to an item.")
                        val = value
                        if val == 0:
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
                        affected.items[self.item] -= value
                        if affected.items[self.item] == 0:
                            affected.items.pop(self.item)
                            destruction = self.item.textl.safe_substitute(Tribute1=affected.name)
                            resolutuion_strings.append(destruction)
                            affected.log.append(destruction)
                        continue
                    case "itemg":
                        if value == 0:
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
    textl: Template
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
        self.textl = Template(data.get('text', f"$Tribute1's {self.name} broke."))
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
