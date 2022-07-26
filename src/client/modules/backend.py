"""Module containing code pertaining to connecting with the server."""

import aiohttp


session = aiohttp.ClientSession()


async def test_connection(url: str):
    """Tests if the request returns an OK response."""
    url = url.rstrip("/") + "/test-connection"
    # Add HTTP scheme if not present
    if "://" not in url:
        url = "http://" + url.lstrip(":/")
    print("GET", url)
    try:
        async with session.get(url) as resp:
            print(resp)
            return resp.ok
    except aiohttp.ClientConnectionError:
        return False
