from fastapi import WebSocket
from random import randint
from starlette.websockets import WebSocketState


class ConnectionManager:
    """This class handles connection to the rooms."""

    def __init__(self):
        """This function sets variables of ConnectionManager object to default values."""

        # List of all existing rooms.
        self.rooms = {}

        # List of all clients that are not connected to room.
        self.open_clients = []

    async def connect(self, client: WebSocket):
        """This function accepts websocket connection and adds connected client to list of open clients."""

        await client.accept()

        self.open_clients.append(client)

        print(f"client {client} added to open_clients")
        print(f"open_clients: {self.open_clients}")

    async def create_room(self, client: WebSocket):
        """This function creates room with one connected player and sends message
        with type "connected" to client that created it."""

        # Create room with one player.
        room_id = randint(0, 10**5)
        self.rooms[room_id] = {
            "x": client,
            "o": None,
        }

        # Send message to client.
        await client.send_json(
            {
                "type": "create_room",
                "room_id": room_id,
                "sign": "x",
            }
        )

    async def join_room(self, client: WebSocket, room_id: int):
        """This function connects client to room and removes it from list of open clients.
        Then, starts game and sends message with type "update_open_rooms" to all open clients."""

        if room_id not in self.rooms.keys():
            await client.send_json(
                {
                    "type": "join_room_error",
                    "message": f"Room {room_id} does not exist.",
                }
            )
            return (None, None)

        room = self.rooms[room_id]

        if None not in [room["x"], room["o"]]:
            await client.send_json(
                {
                    "type": "join_room_error",
                    "message": f"Room {room_id} is full.",
                }
            )
            return (None, None)

        # Connect client to the room.
        if room["x"]:
            sign = "o"
        else:
            sign = "x"

        room[sign] = client

        # Send message to connected client.
        await client.send_json(
            {
                "type": "join_room",
                "room_id": room_id,
                "sign": sign,
            }
        )

        return (room["x"], room["o"])

    async def leave_room(self, client: WebSocket):
        """This function removes the player from the room."""

        # Find room_id and sign of the player.
        for room_id, room in self.rooms.items():
            if room["x"] == client:
                room_id = room_id
                sign = "x"
                break
            elif room["o"] == client:
                room_id = room_id
                sign = "o"
                break
        else:
            return

        # Remove the player from the room.
        self.rooms[room_id][sign] = None

        # Delete the room if it is empty and update open rooms.
        room = self.rooms[room_id]
        if room["x"] is None and room["o"] is None:
            del self.rooms[room_id]
        else:
            if sign == "x":
                player = room["o"]
            else:
                player = room["x"]

            await player.send_json(
                {
                    "type": "player_disconnected",
                }
            )

        if client.client_state == WebSocketState.DISCONNECTED:
            return

        self.open_clients.append(client)

        await client.send_json(
            {
                "type": "leave_room",
            }
        )

        await self.update_open_rooms()

    async def get_open_rooms(self):
        """This function returns list of all rooms that have only one connected player."""

        print("get_open_rooms called")
        print(f"all rooms: {self.rooms}")

        open_rooms = [
            room_id
            for room_id, room in self.rooms.items()
            if None in [room["x"], room["o"]]
        ]

        return open_rooms

    async def update_open_rooms(self):
        """This function sends information about new rooms to clients
        that are not connected to room."""

        open_rooms = await self.get_open_rooms()

        print(f"update_open_rooms called")
        print(f"open_rooms: {open_rooms}")
        print(f"open_clients: {self.open_clients}")

        for client in self.open_clients:
            await client.send_json(
                {
                    "type": "update_open_rooms",
                    "open_rooms": open_rooms,
                }
            )
