"""Module containing code pertaining to connecting with the server."""

# Built-in library imports
import asyncio
import json
import threading
from time import time
from typing import Callable, Coroutine, Literal
from websockets import client as ws_client, exceptions as ws_exceptions

# Local application imports
from modules import GameInfo, GameStage, Message, FRAMERATE


# Message timeout is half the frametime to allow for other
# game process functions in the space of one game tick
MESSAGE_TIMEOUT = 1 / FRAMERATE / 2


async def send_json(websocket: ws_client.WebSocketClientProtocol, data: dict):
    """Stringifies the JSON data and sends it to the server."""
    stringified = json.dumps(data)
    await websocket.send(stringified)


class WebSocket:
    """Class that allows for transmitting data through the open websocket connection."""

    def __init__(self):
        self._data_to_send: list[dict] = []
        self._message_handler: Callable[[str | bytes], None] = None
        super().__init__()

    def send_message(self, message: dict | Literal["PING"]) -> None:
        """Sends the message object to the server through the active websocket connection."""
        self._data_to_send.append(message)

    async def send_all_data(self, websocket: ws_client.WebSocketClientProtocol) -> None:
        """Sends all the data in the message stack."""
        while self._data_to_send:
            data = self._data_to_send.pop(0)
            if not (isinstance(data, str) and data.upper() == "PING"):
                # Handle regular message
                send_json(websocket, data)
                continue
            # Handle pinging the server
            start_time = time()
            await (await websocket.ping())
            GameInfo.ping = round((time() - start_time) * 1000)  # Convert diff to ms

    def on_server_message(self, handler: Callable[[str | bytes], None]) -> None:
        """Used to decorate functions that will handle all server messages."""
        self._message_handler = handler

    async def receive_message(self, data: str | bytes) -> None:
        """Called whenever the server sends a message over the websocket connection."""
        if self._message_handler is None:
            print("ERROR: No server message handler set.")
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


async def _on_websocket_handshake(websocket: ws_client.WebSocketClientProtocol) -> None:
    """Called when the websocket connection is established."""
    GameInfo.current_stage = GameStage.JOIN_ROOM
    await send_json(websocket, {"type": "get_open_rooms"})


def _on_websocket_error(connection_dropped: bool):
    """Called if there is an error connecting to the websocket."""
    GameInfo.current_stage = GameStage.WEBSOCKET_ERROR
    Message.SERVER_ERROR = (
        Message.CONNECTION_DROPPED if connection_dropped else Message.CONNECTION_FAILED
    )


async def make_websocket_connection(url: str):
    """Makes a blocking infinite connection to the server websocket."""
    url = get_url(url, "ws")

    try:
        async with ws_client.connect(url) as websocket:
            await _on_websocket_handshake(websocket)
            while GameInfo.current_stage != GameStage.ABORTED:
                await session.send_all_data(websocket)
                try:
                    # Only wait a small amount of time for message from server
                    data = await asyncio.wait_for(websocket.recv(), MESSAGE_TIMEOUT)
                except asyncio.TimeoutError:
                    pass
                else:
                    # Handle the received message
                    await session.receive_message(data)
    except ConnectionRefusedError:
        _on_websocket_error(False)
    except ws_exceptions.ConnectionClosedError:
        _on_websocket_error(True)


def connect_to_websocket(url: str):
    """Creates a thread to connect to the server websocket."""
    coroutine: Coroutine[any, any, None] = make_websocket_connection(url)
    thread = threading.Thread(target=asyncio.run, args=(coroutine,))
    thread.start()
