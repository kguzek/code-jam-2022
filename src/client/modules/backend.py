"""Module containing code pertaining to connecting with the server."""

import aiohttp
from websockets import client as ws_client, uri as ws_uri


class WebSession(aiohttp.ClientSession):
    """Child class of `aiohttp.ClientSession` that additionally defines a global storage for
    a websocket connection."""

    def __init__(self):
        self.socket_connection: ws_client.ClientConnection = None
        super().__init__()

    def set_socket_connection(self, connection: ws_client.ClientConnection) -> None:
        """Initialises the websocket connection."""
        self.socket_connection = connection


session = WebSession()


async def close():
    """Closes the web session."""
    await session.close()


def get_url(url: str, path: str, scheme: str = "http") -> str | ws_uri.WebSocketURI:
    """Trims the URL, adds the given scheme as needed, and appends the given path. If the
    URL scheme is `ws`, returns a `WebSocketURI` object."""
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


# def connect_to_websocket(url) -> None:
#     """Connects to the server websocket."""
#     if not url:
#         raise ValueError("Invalid URL.")
#     url = uri.parse_uri(get_url(url, "ws", scheme="ws"))
#     session.set_socket_connection(ws_client.ClientConnection(url))
#     connection_request = session.socket_connection.connect()
#     session.socket_connection.send_request(connection_request)
#     print(url)


async def connect_to_websocket(url):
    """Connects to the server websocket."""
    if not url:
        raise ValueError("Invalid URL.")
    url: ws_uri.WebSocketURI = get_url(url, "ws", scheme="ws")
    async with ws_client.connect(url) as websocket:
        await websocket.recv()
