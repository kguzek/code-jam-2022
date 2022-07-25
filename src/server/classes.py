"""Class definitions."""

import re
from typing import List

from fastapi import WebSocket


class Client(WebSocket):
    """The main class for the client.

    Gives the client a name and handles sending of data.
    Name defaults to "Anonymous" if not provided.

    Args:
        WebSocket: The WebSocket object for the client.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.query_params.get("name")

        if name:
            # Checks to make sure the name is only using
            # alphanumeric characters and is 3 to 20 characters long
            if re.match(r"^[a-zA-Z0-9]{3,20}$", name):
                self.name = name
            else:
                self.name = "Anonymous"
        else:
            self.name = "Anonymous"

        self.accept()

    async def send(self, message: dict):
        """
        Sends json data to the client.

        Args:
            message: The data to send to the client. Should be a dictionary
        """
        self.send_json(message)


class Room:
    """
    Will be written

    Made to shut flake8 up
    """

    def __init__(self, room_id: int) -> None:
        self.room_id = room_id
        self.clients: List[Client] = []

    def add_client(self, client: Client):
        """Adds the client to the room"""
        self.clients.append(client)


class ConnectionManager:
    """
    Will be written

    Made to shut flake8 up
    """

    def __init__(self) -> None:
        self.connections: List[WebSocket] = []
        self.rooms: List[Room] = []

    async def connect(self, websocket: WebSocket):
        """Connects the websocket to the server."""
        self.connections.append(websocket)
