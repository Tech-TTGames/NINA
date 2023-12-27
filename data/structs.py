"""Data structures for the project.

This is the module with the data structures for the TechSim.
"""
import tomllib
from pathlib import Path
from string import Template
from typing import Optional


class Simulation:
    """A class representing a TechSim simulation.

    Attributes:
        name: The name of the simulation.
        logo: The logo of the simulation.
        districts: The districts of the simulation.
        cast: The cast of the simulation.
    """

    def __init__(self, cast_file: Path, events_file: Path):
        """Initialize the Simulation object."""
        file = open(cast_file, "rb")
        data = tomllib.load(file)
        file.close()
        self.name: str = data['name']
        self.logo: str = data['logo']
        self.cast = [Tribute(tribute) for tribute in data['cast']]
        self.districts = [District(district) for district in data['districts']]
        file = open(events_file, "rb")
        data = tomllib.load(file)
        self.cycles = [Cycle(cycle) for cycle in data['cycles']]
        self.items = [Item(item, self.cycles) for item in data['items']]
        file.close()


class District:
    """The class representing a district.

    Attributes:
        name: The name of the district.
        color: The color of the district.
        members: The members of the district.
    """
    members: list["Tribute"] = []

    def __init__(self, data: dict):
        """Initialize the District object.

        Args:
            data: tomli interpreted data.
                Example: { name = "Eosphorous Faction", color = "#FF0400" }
        """
        self.name: str = data['name']
        self.color: str = data['color']


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
    status: int = 0
    power: int = 500
    district: District | None = None
    allies: list["Tribute"] = []
    enemies: list["Tribute"] = []
    items: list["Item"] = []
    kills: int = 0
    log: list[str] = []

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
        self.name: str = data['name']
        self.gender: int = data['gender']
        self.image: str = data['image']
        self.dead_image: str = data['dead_image']


class Cycle:
    """The class representing a cycle type.

    Attributes:
        name: The name of the cycle.
        text: The text of the cycle.
            Displayed at the start of the cycle. Optional.
        allow_item_events: Whether item events are allowed.
            This is specifically for the extra events that happen when a tribute has an item.
            Not to be confused with the base events of items, which are always imported if the cycle matches.
            0: Do not allow, 1: Allow, 2: Only allow items which can be gathered in the cycle.
        weight: The weight of the cycle.
            Influences the probability of the cycle happening. For hardcoded cycles, keep at None.
            A weight signifies a random cycle with a chance of happening.
        max_use: The maximum amount the cycle can happen. -1 for infinite.
        events: The events of the cycle.
    """
    name: str
    text: str | None = None
    allow_item_events: int = 0
    weight: int | None = None
    max_use: int = -1
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
        self.name: str = data['name']
        self.allow_item_events: int = data['allow_item_events']
        self.events = [Event(event, self) for event in data['events']]


class Event:
    """The class representing an event.

    Attributes:
        text: The text of the event.
        cycle: The cycle the event belongs to.
        weight: The weight of the event.
            Influences the probability of the event happening.
        max_use: The maximum amount the event can happen. -1 for infinite.
        max_cycle: The maximum amount the event can happen in a cycle. -1 for infinite.
        item: The item the event is attached to.
            Defaults to None, which means the event is not attached to an item.
            In ItemL and ItemG, the item is the specific item to lose or gain.
        tribute_changes: The changes in the tributes after the event.
            Write as a list with the tribute position as the index.
            Valid keys:
            Power - A change in power. Can be positive or negative.
            PowerN - A change in power, but not above or below base power. It Can be positive or negative.
            Status - 0 for alive, 1 for dead. It Can be theoretically used to revive tributes.
            ItemU - Item use. Use a specified number of charges from the event item.
            ItemL - Item loss. Either the event item (0) or a number of items to from the Tribute's item pool, randomly
            ItemG - Item gain. Either the event item (0) or a number of items to gain from this event's loss pool.
            Kills - A change in kill count. Positive.
            Allies - A change in allies. List of (tribute_id, change) where change is 0 for remove, 1 for adding.
            Enemies - A change in enemies. List of (tribute_id, change) where change is 0 for remove, 1 for adding.
            Example: [ { "power": 100 } ]
        tribute_requirements: The requirements for the tributes in the event.
            Write as a list with the tribute position as the index.
            Valid keys:
            Status - Default is 0, override to 1 for a dead tribute.
            Power - Requre a specific power, so a list of (operation, power).
                Operation is 0 for equal, 1 for greater than, 2 for less than. Power is the power to compare to.
            ItemStatus - Requre a specific item usage status, so a list of (operation, status).
                See `Power` parameter for operations. The item is the event item.
            Allies - Default not required, override to require alliance with specified tributes.
            NotAllies - Default not required, override to require no alliance with specified tributes.
            Enemies - Default not required, override to require enmity with specified tributes.
            NotEnemies - Default not required, override to require no enmity with specified tributes.
            Neutral - Default not required, override to require neutrality with specified tributes.
            Example: [ { "allies": [1] }, { "allies": [0] } ]
        """
    text: Template
    cycle: Cycle | list[Cycle]
    weight: int = 1
    max_use: int = -1
    max_cycle: int = -1
    item: Optional["Item"] = None
    tribute_changes: list[dict]
    tribute_requirements: list[dict] = []

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
        self.weight = data['weight'] or 1
        self.max_use = data['max_use'] or -1
        self.max_cycle = data['max_cycle'] or -1
        self.item = item
        self.tribute_changes: list[dict] = data['tribute_changes']
        self.tribute_requirements: list[dict] = data['tribute_requirements'] or []


class Item:
    """The class representing an item.

    Attributes:
        name: The name of the item.
        power: The power of the item.
        cycles: The cycles the item can be found in.
        use_count: The amount of times the item can be used. -1 for infinite.
        base_event: The base event of the item, so the event that causes the item to be found.
        events: The events that can happen with this item.
    """
    name: str
    power: int = 0
    cycles: list[Cycle]
    use_count: int = -1
    base_event: Event
    events: list[Event] = []

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
        self.name: str = data['name']
        self.power: int = data['power'] or 0
        self.cycles = [cycle for cycle in cycles if cycle.name in data['cycles']]
        self.use_count: int = data['use_count'] or -1
        self.base_event = Event(data['base_event'], self.cycles)
        self.events = [Event(event, self.cycles) for event in data['events']]
