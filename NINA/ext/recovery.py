"""A fallback and recovery method for any object.

This module provides a with ... as ... option to wrap an object around for emergency recover should an error occur.

Typical usage example:
    ```py
    from NINA.ext import recovery
    a = "Unsafe String!"
    with recovery.Safe(a) as safe_string:
        ...
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

from copy import deepcopy


class Safe(object):
    """A 'Safe' object that applies changes to objects only if executed safely.

    Think SQL transactions. If we get an error, we issue a ROLLBACK.
    This prevents an error from causing a total loss of data.
    """

    def __init__(self, obj: object) -> None:
        """Creates a new Safe object.

        Attributes:
            obj: The object to safeguard.
        """
        self.original = obj
        self.exposed = deepcopy(obj)

    def __repr__(self):
        return f"<Safe(value={repr(self.value)})>"

    def __enter__(self):
        return self.exposed

    def __exit__(self, exc_type, exc_value, traceback):
        if not any([exc_type, exc_value, traceback]):
            self.original.__dict__ = self.exposed.__dict__
