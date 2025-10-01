"""Lists all failed images."""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import time
import tomllib

import requests

cast_file = input()

with open(cast_file, "rb") as file:
    data = tomllib.load(file)

for tribute in data["cast"]:
    for pre in ["", "dead_"]:
        ok = False
        im = tribute[pre+"image"]
        if im == "BW":
            continue
        try:
            r = requests.get(im, headers = {"User-agent": "NINABot 0.1.0a"}, timeout=10)
            ok = r.status_code == requests.codes.ok
            if r.status_code != requests.codes.ok:
                time.sleep(int(r.headers["Retry-After"]))
            else:
                time.sleep(2)
        finally:
            if not ok:
                print(f"Fail: {tribute["name"]}: {pre}")
