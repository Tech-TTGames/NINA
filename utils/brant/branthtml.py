"""Handling of Brant-Stelle HTML files."""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import os
import re
import typing
from warnings import warn

import bs4
from selenium import webdriver
import tomli_w

driver = webdriver.Firefox()


def convert_to_toml(soup: bs4.BeautifulSoup):
    """
    Converts event data from HTML to TOML format.

    Args:
        soup: The more limited pre-parsed BeautifulSoup object.

    Returns:
        A list of dictionaries containing the converted event data in TOML format.
    """
    data = soup.find_all("strong")  # Find events separated by double <br>

    converted_events = []
    template = {
        "weight": 20,
        "max_use": -1,
        "max_cycle": -1,
    }
    current_data: dict[str, typing.Any] = template.copy()
    event_running = False
    for bag_of_soup in data:
        if "#" in bag_of_soup.string:
            if event_running:
                converted_events.append(current_data)
                current_data = template.copy()
            event_running = True
            text = str(bag_of_soup.next_sibling[2:].strip())
            current_data["refstring"] = text[:]
            for matchfound in re.finditer(r"\((.*?)\)", text):
                if "/" in matchfound.group(1):
                    text = text.replace(matchfound.group(), matchfound.group(1).split("/")[0])
                else:
                    plr_id = re.split(r"[+\-!:]", matchfound.group(1).replace("Player", ""))[0]
                    text = text.replace(matchfound.group(), f"$Tribute{plr_id}")
            for matchfound in re.finditer(r"\[(.*?)]", text):
                plchldr_type = matchfound.group(1)[:5]
                translation = {"typea": "SP", "typeb": "OP", "typec": "PA", "typed": "RP"}
                replacement = "$" + translation[plchldr_type.casefold()] + matchfound.group(1)[5:]
                if plchldr_type[0] == "T":
                    replacement += "_C"  # Respect capitalization settings
                text = text.replace(matchfound.group(), replacement)

            current_data["text"] = text
            # Also try and generate tribute_requirements based on string, but that probably in a second loop.
        elif "Tributes" in bag_of_soup.string:
            current_data["tribute_changes"] = [{} for _ in range(int(bag_of_soup.next_sibling.strip()))]
        elif "Killed (By)" in bag_of_soup.string:
            sets = bag_of_soup.next_sibling.string.strip().split("|")
            for dataset in sets:
                killed, by = dataset.split(" (")
                killed = int(killed.strip()[6:]) - 1
                by = [int(a[6:]) - 1 for a in by.strip()[:-1].split(", ")]
                current_data["tribute_changes"][killed]["status"] = 1
                for killer in by:
                    if killer == -1:
                        continue
                    current_killtotal = current_data["tribute_changes"][killer].get("kills", 0) + 1
                    current_data["tribute_changes"][killer]["kills"] = current_killtotal

    return converted_events


def process_html_file(fname):
    """
    DEPRECATED!
    Mostly due to the manual-intensive process it uses. The new function will be much more automated.
    Reads HTML data from a file, converts it to TOML, and saves it to a corresponding TOML file.

    Args:
        fname: The name of the HTML file to process.
    """
    warn("This function is deprecated. It will continue to function but will not be maintained!")
    with open(fname, encoding="utf-8") as f:
        html_data = f.read()

    soup = bs4.BeautifulSoup(html_data, "lxml")
    toml_data = convert_to_toml(soup)
    toml_data = {"cycles": {"events": toml_data}}

    # Create the output filename by replacing the extension with .toml
    output_filename = os.path.splitext(fname)[0] + ".toml"

    with open(output_filename, "wb") as f:
        tomli_w.dump(toml_data, f)


def scrape_events(entry_url: str):
    """
    Fully automatically scrapes all the events from the URL-provided brent simulator link.

    Args:
        entry_url: The URL of the brent simulator save to scrape.
    """
    driver.get(entry_url)
    driver.implicitly_wait(5)
    base_event_url = "https://brantsteele.com/hungergames/classic/ManageEvents.php?type="
    e_types = [
        "bloodbath",
        "day",
        "night",
        "feast",
        "bloodbathfatal",
        "dayfatal",
        "nightfatal",
        "feastfatal",
    ]  # TODO: ARENA and ENDGAME need special handling
    for event_type in e_types:
        driver.get(base_event_url + event_type)
        driver.implicitly_wait(5)
        soup = bs4.BeautifulSoup(driver.page_source, "lxml")
        soup = soup.find(class_="left")
        tomled_data = {"cycles": {"events": convert_to_toml(soup)}}
        with open(event_type + ".toml", "wb") as f:
            tomli_w.dump(tomled_data, f)


if __name__ == "__main__":
    imput = input("Paste the BrantSteele Save link here or just press enter to use legacy mode!\n")
    if not imput:
        # Get all HTML files in the current directory
        html_files = [f for f in os.listdir() if f.endswith(".html")]

        # Process each HTML file
        for filename in html_files:
            process_html_file(filename)

        print("Converted all HTML files to TOML successfully!")
    else:
        scrape_events(imput)

