"""Various aiohttp stuffs.

In practice mostly factory functions for middleware.
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames
import asyncio
from datetime import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime
import logging
from typing import Awaitable, Callable

import aiohttp

logger = logging.getLogger(__name__)
AIOHTTPMiddleware = Callable[[aiohttp.ClientRequest, Callable[..., Awaitable]], Awaitable]


def create_retry_middleware(attempts: int = 2, timecap: int = 30) -> AIOHTTPMiddleware:
    """Factory to create a middleware that handles retries for rate limiting.

    This middleware will retry a request if it receives a 429 or 503 status
    code, respecting the 'Retry-After' header.

    Args:
        attempts: The number of times to retry the request.
                  (e.g., attempts=3 means 1 initial try + up to 3 retries)
        timecap: The maximum number of seconds the request should wait before retrying.
    """

    async def retry_middleware(request: aiohttp.ClientRequest, handler: Callable[...,
                                                                                 Awaitable]) -> aiohttp.ClientResponse:
        response = None
        for _ in range(attempts + 1):
            response = await handler(request)
            if response.status in (429, 503) and "Retry-After" in response.headers:
                retry_after = response.headers["Retry-After"]
                try:
                    delay = int(retry_after)
                except ValueError:
                    retry_date = parsedate_to_datetime(retry_after)
                    delay = (retry_date - datetime.now(timezone.utc)).total_seconds()
                if delay >= timecap:
                    return response
                wait_time = max(0, delay)
                logger.warning(
                    "Request to %s failed with status %d. "
                    "Honoring Retry-After header. Waiting %.2f seconds.", request.url, response.status, wait_time)
                await response.release()
                await asyncio.sleep(wait_time)
                continue
            return response
        logger.error("Request to %s failed after %d attempts.", request.url, attempts + 1)
        return response

    return retry_middleware
