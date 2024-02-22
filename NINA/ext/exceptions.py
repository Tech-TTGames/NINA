"""General exceptions that we can use in the application.

This module contains general exceptions that we can use in the application.
These exceptions are used to handle errors in a more elegant way. Most of these
exceptions are a subclass of `discord.app_commands.AppCommandError`.

Typical usage example:
    ```py
    from NINA.ext import exceptions
    try:
        ...
    except exceptions.ReferenceNotFound:
        ...
    ```
"""
# License: UNLICENSED
# SPDX-License-Identifier: UNLICENSED
# Copyright (c) 2023-present Tech. TTGames

from discord import app_commands


class NINABotError(app_commands.AppCommandError):
    """Base class for Project: NINA exceptions.

    This is the base class for all Project: NINA exceptions.
    Avoid using this exception, use a subclass of this exception instead.
    If you are using this exception, please consider creating a subclass of
    for your use case.
    This is a subclass of `discord.app_commands.AppCommandError` to use
    the library's app command handling functions.
    """


class NINACheckFailure(app_commands.CheckFailure):
    """Command failed simulation checks.

    An app command failed the checks.
    This is usually used when a user tries to execute a command
     not allowed in the current simulation state.
    """


class ReferenceNotFound(NINABotError):
    """Command executed with invalid reference.

    A previously valid reference no longer resolves successfully.
    Mostly caused by manual deletion of the referenced object,
    by the user.
    """


class UsageError(NINABotError):
    """Command executed with invalid usage.

    An app command was executed with invalid usage.
    A broad Project: NINA exception that is used when a command is executed
    in an invalid way.
    """


class InvalidLocation(UsageError):
    """Command executed in an invalid location.

    An app command was executed in an invalid location.
    This is usually used when a command is executed in a DM channel,
    or in general, a channel that is invalid for the command.
    """


class InvalidParameters(UsageError):
    """Command executed with invalid parameters.

    An app command was executed with invalid parameters.
    This is usually used when a user provides invalid parameters to a command.
    """
