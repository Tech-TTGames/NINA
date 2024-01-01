"""This is the module with the data structures for the Brent-Steele Hunger Games simulator.

It is not representative of the TechSim, but it is a good utility for
transferring data between the TechSim and the Brent-Steele simulator.
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import tomli_w
from pathlib import Path
from typing import TextIO


class Simulation:
    """A class representing a Brent-Steele simulation.

    Attributes:
        name: The name of the simulation.
        logo: The logo of the simulation.
        districts: The districts of the simulation.
        cast: The cast of the simulation.
    """

    def __init__(self, filename: Path):
        """Initialize the Simulation object.

        Args:
            filename: The file containing the cast.
        """
        file = open(filename)
        self.name = file.readline().strip()
        self.logo = file.readline().strip()
        self.districts = []
        self.cast = []
        skipcount = 0
        cur_district = None
        while True:
            line = file.readline()
            if line == "":
                break
            if line == "\n":
                skipcount += 1
                continue
            if skipcount == 1:
                tribute = Tribute(line.strip(), file)
                self.cast.append(tribute)
                skipcount = 0
            if skipcount == 2:
                if cur_district is not None:
                    self.districts.append(cur_district)
                cur_district = {
                    'name': line.strip(),
                    'color': file.readline().strip(),
                }
                skipcount = 0
        if cur_district is not None:
            self.districts.append(cur_district)
        file.close()

    def __dict__(self):
        """Return a dictionary representation of the simulation."""
        districts_clean = []
        for district in self.districts:
            districts_clean.append({
                'name': district['name'],
                'color': district['color'][:7],
            })
        resolve_cast = [castmember.__dict__ for castmember in self.cast]
        return {
            'name': self.name,
            'logo': self.logo,
            'districts': districts_clean,
            'cast': resolve_cast,
        }

    def write(
        self,
        filename: Path,
    ):
        """Write the simulation to the specified file.

        Args:
            filename: The file to write the simulation to.
        """
        file = open(filename, 'w')
        file.write(self.name + '\n')
        file.write(self.logo + '\n')
        cast_index = 0
        cpd = len(self.cast) // len(self.districts)
        for district in self.districts:
            file.write("\n")
            file.write("\n")
            file.write(district['name'] + '\n')
            file.write(district['color'] + '\n')
            for a in range(cast_index, cast_index + cpd):
                file.write("\n")
                file.write(self.cast[a].name + '\n')
                file.write(self.cast[a].nickname + '\n')
                file.write(f"{self.cast[a].gender}\n")
                file.write(self.cast[a].image + '\n')
                file.write(self.cast[a].dead_image)
                if a != len(self.cast) - 1:
                    file.write("\n")
            cast_index += cpd
        file.close()

    def writet(self, filename: Path):
        """Write the simulation to .toml.

        This not the default write method because it is not compatible
        with the Brent-Steele simulator.

        Args:
            filename: The file to write the simulation to.
        """
        file = open(filename, 'wb')
        tomli_w.dump(self.__dict__(), file)
        file.close()


class Tribute:
    """A class representing a tribute.

    Attributes:
    """

    def __init__(self, name: str, file: TextIO):
        """Take the provided file and read the tribute from it.

        We assume the cursor is at the end of the line containing the
        tribute's name.

        Args:
            file: The file containing the tribute.
        """
        self.name = name
        self.nickname = file.readline().strip()
        self.gender = int(file.readline().strip())
        self.image = file.readline().strip()
        self.dead_image = file.readline().strip()

    def __str__(self):
        """Return a string representation of the tribute."""
        return "Tribute: " + self.name
