"""This is the module with the data structures for the Brent-Steele Hunger Games simulator.

It is not representative of Project: NINA, but it is a good utility for
transferring data between the Project: NINA and the Brent-Steele simulator.
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import pathlib
from typing import TextIO

import tomllib
import tomli_w


class Simulation:
    """A class representing a Brent-Steele simulation.

    Attributes:
        name: The name of the simulation.
        logo: The logo of the simulation.
        districts: The districts of the simulation.
        cast: The cast of the simulation.
    """

    def __init__(self, filename: pathlib.Path):
        """Initialize the Simulation object.

        Args:
            filename: The file containing the cast.
        """
        if pathlib.Path(filename).suffix == ".txt":
            with open(filename, encoding="utf-8") as file:
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
                            "name": line.strip(),
                            "color": file.readline().strip(),
                        }
                        skipcount = 0
                if cur_district is not None:
                    self.districts.append(cur_district)
        else:
            with open(filename, "rb") as file:
                dts = tomllib.load(file)
                self.name: str = dts["name"]
                self.logo: str = dts["logo"]
                self.districts = dts["districts"]
                self.cast = [Tribute(tribute["name"], tribute) for tribute in dts["cast"]]


    def __dict__(self):
        """Return a dictionary representation of the simulation."""
        districts_clean = []
        for district in self.districts:
            districts_clean.append({
                "name": district["name"],
                "color": district["color"][:7],
            })
        resolve_cast = [castmember.__dict__ for castmember in self.cast]
        return {
            "name": self.name,
            "logo": self.logo,
            "districts": districts_clean,
            "cast": resolve_cast,
        }

    def write(
        self,
        filename: pathlib.Path,
    ):
        """Write the simulation to the specified file.

        Args:
            filename: The file to write the simulation to.
        """
        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.name + "\n")
            file.write(self.logo + "\n")
            cast_index = 0
            cpd = len(self.cast) // len(self.districts)
            for district in self.districts:
                file.write("\n")
                file.write("\n")
                file.write(district["name"] + "\n")
                file.write(district["color"] + "\n")
                for a in range(cast_index, cast_index + cpd):
                    file.write("\n")
                    file.write(self.cast[a].name + "\n")
                    file.write(self.cast[a].nickname + "\n")
                    file.write(f"{self.cast[a].gender}\n")
                    file.write(self.cast[a].image + "\n")
                    file.write(self.cast[a].dead_image)
                    if a != len(self.cast) - 1:
                        file.write("\n")
                cast_index += cpd

    def writet(self, filename: pathlib.Path):
        """Write the simulation to .toml.

        This not the default write method because it is not compatible
        with the Brent-Steele simulator.

        Args:
            filename: The file to write the simulation to.
        """
        file = open(filename, "wb")
        tomli_w.dump(self.__dict__(), file)
        file.close()


class Tribute:
    """A class representing a tribute.

    Attributes:
    """

    def __init__(self, name: str, file: TextIO | dict):
        """Take the provided file and read the tribute from it.

        We assume the cursor is at the end of the line containing the
        tribute's name.

        Args:
            file: The file or dict containing the tribute.
        """
        self.name = name
        if type(file) is TextIO:
            self.nickname = file.readline().strip()
            self.gender = int(file.readline().strip())
            self.image = file.readline().strip()
            self.dead_image = file.readline().strip()
        else:
            self.nickname = file["nickname"]
            self.gender = file["gender"]
            self.image = file["image"]
            self.dead_image = file["dead_image"]

    def __str__(self):
        """Return a string representation of the tribute."""
        return "Tribute: " + self.name
