"""Entry point for the server application."""

from asyncio import gather
import re
from enum import Enum
from uuid import uuid4

from fastapi import WebSocket


class EventType(Enum):
    """Enum containing all message event types."""

    CONNECT = "new_connection"
    TRANSFER = "transferred"
    DISCONNECT = "client_disconnected"


class Message:  # pylint:disable=too-few-public-methods
    """Message class to be used for server-client communication."""

    def __init__(self, msg_type: EventType, **kwargs):
        self.type = msg_type.value
        self.options = kwargs

    @property
    def serialised(self) -> dict:
        """Gets the message instance serialised as a dictionary."""
        return {"type": self.type, **self.options}


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
        self.uuid = str(uuid4())

        if self.name:
            # Checks to make sure the name is only using
            # alphanumeric characters and is 3 to 20 characters long
            if re.match(r"^[a-zA-Z0-9]{3,20}$", self.name):
                self.name = self.name
            else:
                self.name = "Anonymous"
        else:
            self.name = "Anonymous"

    async def send_message(self, message: Message):
        """
        Sends a message to the client.

        Args:
            message: The Message object to send.
        """
        await self.socket.send_json(message.serialised)

    async def close(self) -> None:
        """Closes the conection to the server."""
        print("Closed client", self.serialised)

    @property
    def serialised(self) -> dict:
        """Gets a serialised version of the client instance."""
        return {"uuid": self.uuid, "name": self.name}


class Room:
    """
    Main class for a game room.

    Each room has a list of clients (up to 2 unless we do spectators).
    Also has an id which will probably be a uuid.
    """

    def __init__(self, room_id: int) -> None:
        self.room_id = room_id
        self.clients: list[Client] = []

    def add_client(self, client: Client):
        """Adds the client to the room."""
        self.clients.append(client)

    async def remove_client(self, client: Client):
        """Removes the client from the room."""
        self.clients.remove(client)
        await self.broadcast(Message(EventType.DISCONNECT, uuid=client.uuid))

    async def broadcast(self, message: Message):
        """Sends the message to all connected clients."""
        # Send all messages concurrently
        coroutines = (client.send_message(message) for client in self.clients)
        await gather(*coroutines)


class ConnectionManager:
    """
    The main connection manager for the server

    Keeps track of connections in self.connections and rooms in self.rooms
    """

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []
        self.rooms: list[Room] = []

    async def connect(self, websocket: WebSocket) -> Client:
        """Connects the websocket to the server."""
        client = Client(websocket, None)
        print(websocket.query_params)
        await client.socket.accept()
        self.connections.append(client)
        return client

    async def remove_client_from_room(self, client) -> None:
        """Removes the client from its current room."""
        if not client.room_id:
            return
        room = self.get_room(client.room_id)
        await room.remove_client(client)

        if len(room.clients) == 0:
            self.rooms.remove(room)

    async def disconnect(self, client: Client):
        """Disconnects the client from the server."""
        await client.close()

        self.connections.remove(client)
        await self.remove_client_from_room(client)

    async def transfer_client(self, client: Client, room: Room):
        """Transfers the client to the room."""
        await self.remove_client_from_room(client)

        if room not in self.rooms:
            self.rooms.append(room)

        room.add_client(client)
        client.room_id = room.room_id

        clients = [client.serialised for client in room.clients]
        await client.send_message(
            Message(EventType.TRANSFER, roomid=room.room_id, clients=clients)
        )

    def get_room(self, room_id: int) -> Room:
        """Gets the room with the id or creates one."""
        for room in self.rooms:
            if room.room_id == room_id:
                return room
        return Room(room_id)

    def __str__(self) -> str:
        output = "Rooms:\n"
        for room in self.rooms:
            output += f"{room.room_id}: {', '.join(i.name for i in room.clients)}\n"

        return output
