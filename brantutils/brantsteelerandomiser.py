"""Brent-Steele Cast Randomizer

This module contains the Brent-Steele Cast Randomizer, which is a
randomizer for shuffling the cast for the Brent-Steele Hunger Games
simulator. Created for the needs of the Project Neural Cloud Discord
server.

Typical usage example:
    > ./brantsteelerandomiser.py -i input_cast.txt
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import argparse
import colorsys
import pathlib
import random

import colorama

from brantutils.brantstructs import Simulation

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
    parser.add_argument(
        '-toml',
        '--output_toml',
        action='store_true',
        help='Output a toml file.',
        default=False,
    )
    parser.add_argument(
        '-r',
        '--repeat',
        type=int,
        help='Number of times to randomize cast. Conflicts with --output.',
        default=1,
    )
    args = parser.parse_args()
    colorama.init()
    intake = pathlib.Path(args.input)
    for i in range(args.repeat):
        if args.output is None:
            if args.output_toml:
                ext = '.toml'
            else:
                ext = '.txt'
            no = ""
            if i:
                no = f"_{i}"
            output = pathlib.Path(f'{args.input[:-4]}_randomized{no}{ext}')

        else:
            output = pathlib.Path(args.output)
        if not intake.exists():
            print(colorama.Fore.RED + "Input file does not exist!" + colorama.Style.RESET_ALL)
            print("Exiting...")
            exit(1)
        if output.exists():
            print(colorama.Fore.RED + "Output file already exists!")
            print("Are you sure you want to overwrite it? (Y/N)" + colorama.Style.RESET_ALL)
            if input().upper() != 'Y':
                print("Exiting...")
                exit(0)
        print("Reading input...")
        try:
            sim = Simulation(intake)
        except Exception as e:
            print(colorama.Fore.RED + "Error reading input file!" + colorama.Style.RESET_ALL)
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
            for y, district in enumerate(sim.districts):
                rgb = [int(x * 255) for x in colorsys.hsv_to_rgb((y * increment + offset) / 360, 1.0, 1.0)]
                color = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])
                district['color'] = color + " 0 0"
        if args.output_toml:
            sim.writet(output)
        else:
            sim.write(output)
        print(colorama.Fore.CYAN + "Done! Results written to " + str(output) + ".")
