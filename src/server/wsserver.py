"""Entry point for the server application."""

import re
from typing import List

from fastapi import WebSocket


class Client:
    """The main class for the client.

    Gives the client a name and handles sending of data.
    Name defaults to "Anonymous" if not provided.

    Args:
        WebSocket: The WebSocket object for the client.
        name: The name of the client. Alphanumeric 3-20 characters. Default: Anonymous
        room_id: ID of the client
    """

    def __init__(self, websocket: WebSocket, room_id: int = None):
        self.name = websocket.query_params.get("name")
        self.room_id = room_id
        self.socket = websocket

        if self.name:
            # Checks to make sure the name is only using
            # alphanumeric characters and is 3 to 20 characters long
            if re.match(r"^[a-zA-Z0-9]{3,20}$", self.name):
                self.name = self.name
            else:
                self.name = "Anonymous"
        else:
            self.name = "Anonymous"

    async def send_data(self, data: dict):
        """
        Sends json data to the client.

        Args:
            data: The data to send to the client. Should be a dictionary
        """
        await self.socket.send_json(data)

    async def accept(self) -> None:
        """Accepts the socket connection"""
        await self.socket.accept()

    async def recieve_data(self) -> dict:
        """Recieves data send by the client"""
        return await self.socket.receive_json()


class Room:
    """
    Main class for a game room.

    Each room has a list of clients (up to 2 unless we do spectators).
    Also has an id which will probably be a uuid.
    """

    def __init__(self, room_id: int) -> None:
        self.room_id = room_id
        self.clients: List[Client] = []

    def add_client(self, client: Client):
        """Adds the client to the room."""
        self.clients.append(client)

    def remove_client(self, client: Client):
        """Removes the client from the room."""
        self.clients.remove(client)

    async def broadcast(self, data: dict):
        """Sends the data to all connected clients."""
        for client in self.clients:
            await client.send_data(data)


class ConnectionManager:
    """
    The main connection manager for the server

    Keeps track of connections in self.connections and rooms in self.rooms
    """

    def __init__(self) -> None:
        self.connections: List[WebSocket] = []
        self.rooms: List[Room] = []

    async def connect(self, websocket: WebSocket) -> Client:
        """Connects the websocket to the server."""
        client = Client(websocket, None)
        print(websocket.query_params)
        await client.accept()
        self.connections.append(client)
        return client

    async def disconnect(self, client: Client):
        """Disconnects the client from the server."""
        try:
            await client.close()
        except AttributeError:
            pass

        if client.room_id:
            old_room = self.get_room(client.room_id)
            old_room.remove_client(client)

            if len(old_room.clients) == 0:
                self.rooms.remove(old_room)

        self.connections.remove(client)

    async def transfer_client(self, client: Client, room: Room):
        """
        Transfers the client to the room.
        """
        if client.room_id:
            old_room = self.get_room(client.room_id)
            old_room.remove_client(client)

            if len(old_room.clients) == 0:
                self.rooms.remove(old_room)

        if room not in self.rooms:
            self.rooms.append(room)

        room.add_client(client)
        client.room_id = room.room_id

    def get_room(self, room_id: int) -> Room:
        """Get's the room with the id or creates one."""
        for room in self.rooms:
            if room.room_id == room_id:
                return room
        return Room(room_id)

    def __str__(self) -> str:
        output = "Rooms:\n"
        for room in self.rooms:
            output += f"{room.room_id}: {', '.join(i.name for i in room.clients)}\n"

        return output
