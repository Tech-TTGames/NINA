import re

import tomli_w
from bs4 import BeautifulSoup


def convert_to_toml(html_data):
    """
    Converts event data from HTML to TOML format.

    Args:
        html_data: String containing the HTML content.

    Returns:
        A list of dictionaries containing the converted event data in TOML format.
    """
    soup = BeautifulSoup(html_data, 'html.parser')
    data = soup.find_all("br")  # Find events separated by double <br>

    converted_events = []
    template = {
        "weight": 20,
        "max_use": -1,
        "max_cycle": -1,
    }
    current_data = template.copy()
    for pouch in data:
        if pouch.next_sibling is None or pouch.next_element.name == 'br':
            converted_events.append(current_data)
            current_data = template.copy()
        elif pouch.previous_sibling.name == 'br':
            continue
        elif pouch.next_sibling.name == 'strong':
            text = str(pouch.previous_element[2:])
            current_data["refstring"] = text[:]
            for matchfound in re.finditer(r'\((.*?)\)', text):
                if '/' in matchfound.group(1):
                    text = text.replace(matchfound.group(), matchfound.group(1).split('/')[0])
                else:
                    plr_id = matchfound.group(1).replace('Player', "").split(":")[0]
                    text = text.replace(matchfound.group(), f"$Tribute{plr_id}")
            for matchfound in re.finditer(r'\[(.*?)\]', text):
                plchldr_type = matchfound.group(1)[:5]
                translation = {'typea': "SP", 'typeb': "OP", "typec": "PA", 'typed': "RP"}
                replacement = "$" + translation[plchldr_type.casefold()] + matchfound.group(1)[5:]
                if plchldr_type[0] == "T":
                    replacement += "_C"  # Respect capitalization settings
                text = text.replace(matchfound.group(), replacement)

            current_data['text'] = text
            # Also try and generate tribute_requirements based on string, but that probably in a second loop.
        elif pouch.next_sibling.name == 'a':
            current_data['tribute_changes'] = int(pouch.previous_element) * [{}]

    return converted_events


# Example usage
with open("events.html") as f:
    html_data = f.read()

toml_data = convert_to_toml(html_data)
toml_data = {"cycles": {"events": toml_data}}

with open("events.toml", "wb") as f:
    tomli_w.dump(toml_data, f)
