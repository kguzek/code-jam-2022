"""Module containing code pertaining to connecting with the server."""

import asyncio
import json
import threading
from typing import Callable, Coroutine
from websockets import client as ws_client

from modules import GameInfo, GameStage


class WebSocket:
    """Class that allows for transmitting data through the open websocket connection."""

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


session = WebSocket()


async def close():
    """Closes the websocket connection."""


def get_url(url: str, path: str, scheme: str = "ws") -> str:
    """Trims the URL, adds the given scheme as needed, and appends the given path.."""
    if not url:
        raise ValueError("Invalid URL.")
    # Append path
    url = f"{url.rstrip('/')}/{path}"
    # Add scheme if not present
    if "://" not in url:
        url = f"{scheme}://" + url.lstrip(":/")
    return url


def _on_websocket_handshake() -> None:
    """Called when the websocket connection is established."""
    GameInfo.current_stage = GameStage.JOIN_ROOM


async def make_websocket_connection(url):
    """Makes a blocking infinite connection to the server websocket."""
    url = get_url(url, "ws")
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
