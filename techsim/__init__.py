"""TechSim - A discord pruning bot, for the KumoDesu discord server.

This is the main module for the bot. It contains the entry point for the bot.

Typical usage example:
    For a standard startup, use start_bot.
    For a custom startup, use the code in the example below.
    ```py
    #!/usr/bin/env python3
    import asyncio
    import techsim
    loop = asyncio.get_event_loop()
    loop.run_until_complete(techsim.start_bot(config))
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import logging
import signal
import sys

import colorama
import discord
from discord.ext import commands

from techsim import bot
from techsim.data import config
from techsim.data import const


# pylint: disable=unused-argument
def sigint_handler(sign, frame):
    """Handles SIGINT (Ctrl+C)"""
    logging.info("SIGINT received. Exiting.")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)
logger = logging.getLogger("techsim.launchpad")


async def start_bot(conf: config.Config, debug: bool = False) -> None:
    """Starts the bot.

    Also sets up logging.
    Also handles neat shutdown.
    """
    colorama.just_fix_windows_console()
    print("Beginning setup...")
    if debug:
        print(colorama.Fore.RED + colorama.Style.BRIGHT + "DEBUG MODE ACTIVE!" + colorama.Style.RESET_ALL)
    try:
        # Set up logging
        dt_fmr = "%Y-%m-%d %H:%M:%S"
        const.HANDLER.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s", dt_fmr))

        # Set up setup logging
        logger.setLevel(logging.INFO)
        logger.addHandler(const.HANDLER)

        # Set up asyncio logging
        async_logger = logging.getLogger("asyncio")
        async_logger.setLevel(logging.INFO)
        async_logger.addHandler(const.HANDLER)

        # Set up botcore logging
        core_logger = logging.getLogger("techsim.botcore")
        core_logger.setLevel(logging.INFO)
        core_logger.addHandler(const.HANDLER)

        # Set up error handling logging
        err_logger = logging.getLogger("techsim.commanderrorhandler")
        err_logger.setLevel(logging.INFO)
        err_logger.addHandler(const.HANDLER)

        # Set up override logging
        ovrd_logger = logging.getLogger("techsim.override")
        ovrd_logger.setLevel(logging.INFO)
        ovrd_logger.addHandler(const.HANDLER)

        # Set up core command logging
        corecmd_logger = logging.getLogger("techsim.core")
        corecmd_logger.setLevel(logging.INFO)
        corecmd_logger.addHandler(const.HANDLER)

        # Set up simulation logging
        sim_logger = logging.getLogger("techsim.simulation")
        sim_logger.setLevel(logging.INFO)
        sim_logger.addHandler(const.HANDLER)

        # Set up discord.py logging
        dscrd_logger = logging.getLogger("discord")
        dscrd_logger.setLevel(logging.INFO)
        dscrd_logger.addHandler(const.HANDLER)

        logger.info("Logging set up.")

        if debug:
            logger.setLevel(logging.DEBUG)
            async_logger.setLevel(logging.DEBUG)
            corecmd_logger.setLevel(logging.DEBUG)
            err_logger.setLevel(logging.DEBUG)
            ovrd_logger.setLevel(logging.DEBUG)
            corecmd_logger.setLevel(logging.DEBUG)
            sim_logger.setLevel(logging.DEBUG)
            dscrd_logger.setLevel(logging.DEBUG)
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception("Failed to set up logging.")
        print(f"LOGGING: {const.FAILED}")
        print(f"ERROR: {e}")
        print("Aborting...")
        return
    print(f"LOGGING: {const.OK}")

    # Create bot instance
    try:
        bot_instance = bot.TechSimBot(
            confg=conf,
            intents=const.INTENTS,
            command_prefix=commands.when_mentioned,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="over the simulation.",
            ),
        )
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception("Failed to create bot instance.")
        print(f"BOT INITIALIZATION: {const.FAILED}")
        print(f"ERROR: {e}")
        print("Aborting...")
        return
    print(f"BOT INITIALIZATION: {const.OK}")

    print(const.ALL_OK)
    print("Starting bot...")
    try:
        scrt = config.Secret()
        await bot_instance.start(scrt.token())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Shutting down...")
        print("Keyboard interrupt detected. Shutting down...")
        await bot_instance.close()
    except SystemExit as exc:
        logger.info("System exit code: %s detected. Closing bot...", exc.code)
        print(f"System exit code: {exc.code} detected. Closing bot...")
        await bot_instance.close()
    else:
        print("Internal bot shutdown. (/close was used.)")
        logger.info("Bot shutdown gracefully.")
    logger.info("Bot shutdown complete.")
    print("Thanks for using TechSim!")
