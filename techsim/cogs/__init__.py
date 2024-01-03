"""An import utility for loading all cogs in this submodule.

This file just makes it easier to load all cogs in this submodule.
We can just import this submodule and iterate over the `EXTENSIONS` list.

Typical usage example:
    ```py
    from techsim import bot
    from techsim import cogs
    bot_instance = bot.TechSimBot(...)
    for extension in cogs.EXTENSIONS:
        await bot_instance.load_extension(extension)
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import pkgutil

EXTENSIONS = [module.name for module in pkgutil.iter_modules(__path__, f"{__package__}.")]
"""A list of all cogs in this submodule. This is the list of cogs to load."""
