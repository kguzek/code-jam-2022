"""Module containing code pertaining to connecting with the server."""

import aiohttp


session = aiohttp.ClientSession()


async def test_connection(url: str):
    """Tests if the request returns an OK response."""
    try:
        async with session.get(url) as resp:
            return resp.ok
    except aiohttp.ClientConnectionError:
        return False
