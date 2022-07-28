"""Module containing code pertaining to connecting with the server."""

import asyncio
import json
import threading
from typing import Callable, Coroutine
from websockets import client as ws_client, uri as ws_uri

import aiohttp

from modules import GameInfo, GameStage


class WebSession(aiohttp.ClientSession):
    """Child class of `aiohttp.ClientSession` that additionally defines a global storage for
    a websocket connection."""

    def __init__(self):
        self._data_to_send: list[dict] = []
        self._message_handler: Callable[[str | bytes], None] = None
        super().__init__()

    def send_message(self, message: dict) -> None:
        """Sends the message object to the server through the active websocket connection."""
        self._data_to_send.append(message)

    async def send_all_data(self, websocket: ws_client.WebSocketClientProtocol) -> None:
        """Sends all the data in the message stack."""
        while self._data_to_send:
            data = self._data_to_send.pop(0)
            if data == "ping":
                future = await websocket.ping()
                print("Ping...")
                await future
                print("Pong!")
                continue
            stringified = json.dumps(data)
            await websocket.send(stringified)

    def on_server_message(self, handler: Callable[[str | bytes], None]) -> None:
        """Used to decorate functions that will handle all server messages."""
        self._message_handler = handler

    async def receive_message(self, data: str | bytes) -> None:
        """Called whenever the server sends a message over the websocket connection."""
        if self._message_handler is None:
            return
        coro = self._message_handler(data)
        if isinstance(coro, Coroutine):
            await coro


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


async def test_connection(base_url: str):
    """Tests if the request to the server returns the appropriate response."""
    base_url = get_url(base_url, "test-connection")
    print("GET", base_url)
    try:
        async with session.get(base_url) as resp:
            data = await resp.json()
            return data.get("server-running")
    except aiohttp.ClientConnectionError:
        return False


def _on_websocket_handshake() -> None:
    """Called when the websocket connection is established."""
    GameInfo.current_stage = GameStage.WAITING_FOR_PLAYER


async def make_websocket_connection(url):
    """Makes a blocking infinite connection to the server websocket."""
    if not url:
        raise ValueError("Invalid URL.")
    url: ws_uri.WebSocketURI = get_url(url, "ws", scheme="ws")
    async with ws_client.connect(url) as websocket:
        _on_websocket_handshake()
        while GameInfo.current_stage != GameStage.ABORTED:
            try:
                # Only wait a small amount of time for message from server
                data = await asyncio.wait_for(websocket.recv(), 0.25)
            except asyncio.TimeoutError:
                pass
            else:
                # Handle the received message
                await session.receive_message(data)
            await session.send_all_data(websocket)


def connect_to_websocket(url):
    """Creates a thread to connect to the server websocket."""
    coroutine: Coroutine[any, any, None] = make_websocket_connection(url)
    thread = threading.Thread(target=asyncio.run, args=(coroutine,))
    thread.start()
