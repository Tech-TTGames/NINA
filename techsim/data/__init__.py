"""Various data interfaces and structures for the TechSim bot.

This package holds all the data interfaces and structures for the TechSim bot.
This is mostly constants, config interfaces, data structures, and database layers.

Typical usage example:
    ```py
    from techsim.data import config, layer
    cnfg = config.Config()
    print(cnfg["guild"])
    manager = layer.DatabaseLayer(bot, session)
    ...
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames
