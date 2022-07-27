"""Module containing code pertaining to connecting with the server."""

import aiohttp
from websockets import client as ws_client

session = aiohttp.ClientSession()


def get_url(url: str, path: str, scheme: str = "http") -> str:
    """Trims the URL, adds the given scheme as needed, and appends the given path."""
    url = f"{url.rstrip('/')}/{path}"
    # Add HTTP scheme if not present
    if "://" not in url:
        url = f"{scheme}://" + url.lstrip(":/")
    return url


async def test_connection(url: str):
    """Tests if the request to the server returns the appropriate response."""
    url = get_url(url, "test-connection")
    print("GET", url)
    try:
        async with session.get(url) as resp:
            json = await resp.json()
            return json.get("server-running")
    except aiohttp.ClientConnectionError:
        return False


async def connect_to_websocket(url) -> None:
    """Connects to the server websocket."""
    if not url:
        raise ValueError("Invalid URL.")
    url = get_url(url, "ws", scheme="ws")
    async with ws_client.connect(url) as websocket:
        print("Connected!")
        func = websocket.data_received

        def callback(data: bytes):
            print(data)
            func(data)

        websocket.data_received = callback
