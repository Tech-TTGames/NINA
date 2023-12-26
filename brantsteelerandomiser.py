"""Brent-Steele Cast Randomizer

This module contains the Brent-Steele Cast Randomizer, which is a
randomizer for shuffling the cast for the Brent-Steele Hunger Games
simulator. Created for the needs of the Project Neural Cloud Discord
server.

Typical usage example:
    > ./brantsteelerandomiser.py -i input_cast.txt
"""

import argparse
import colorsys
import random
import colorama
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
                file.write(self.cast[a].gender + '\n')
                file.write(self.cast[a].image + '\n')
                file.write(self.cast[a].dead_image)
                if a != len(self.cast) - 1:
                    file.write("\n")
            cast_index += cpd


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
        self.gender = file.readline().strip()
        self.image = file.readline().strip()
        self.dead_image = file.readline().strip()

    def __str__(self):
        """Return a string representation of the tribute."""
        return "Tribute: " + self.name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Brent-Steele Cast Randomizer by Tech~.',
        prog='brantsteelerandomiser.py',
    )
    # Input file
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        help='Input file.',
        required=True,
    )
    # Output file
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Output file.',
        required=False,
    )
    parser.add_argument(
        '-c',
        '--cast',
        action='store_true',
        help='Randomize cast.',
        default=False,
    )
    parser.add_argument(
        '-dc',
        '--district_colors',
        action='store_true',
        help='Randomize district colors.',
        default=False,
    )
    args = parser.parse_args()
    colorama.init()
    intake = Path(args.input)
    if args.output is None:
        output = Path(args.input[:-4] + '_randomized.txt')
    else:
        output = Path(args.output)
    if not intake.exists():
        print(colorama.Fore.RED + "Input file does not exist!" +
              colorama.Style.RESET_ALL)
        print("Exiting...")
        exit(1)
    if output.exists():
        print(colorama.Fore.RED + "Output file already exists!")
        print("Are you sure you want to overwrite it? (Y/N)" +
              colorama.Style.RESET_ALL)
        if input().upper() != 'Y':
            print("Exiting...")
            exit(0)
    print("Reading input...")
    try:
        sim = Simulation(intake)
    except Exception as e:
        print(colorama.Fore.RED + "Error reading input file!" +
              colorama.Style.RESET_ALL)
        print(e)
        print("Exiting...")
        exit(1)
    if args.cast:
        print("Randomizing cast...")
        random.shuffle(sim.cast)
    if args.district_colors:
        print("Assigning district colors...")
        max_hue = 360
        increment = max_hue // len(sim.districts)
        offset = random.randint(0, increment)
        for i, district in enumerate(sim.districts):
            rgb = colorsys.hsv_to_rgb((i * increment + offset) / 360, 1.0, 1.0)
            rgb = tuple([int(x * 255) for x in rgb])
            color = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])
            district['color'] = color + " 0 0"
    sim.write(output)
    print(colorama.Fore.CYAN + "Done! Results written to " + str(output) + ".")
