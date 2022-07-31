"""Main program of the server."""

from random import randint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles


DEBUG = True


async def debug(websocket: WebSocket, message):
    """This function prints the debug message if DEBUG is set to True."""

    if not DEBUG:
        return
    await websocket.send_json({"type": "log", "body": message})


class ConnectionManager:
    """This class handles connection to the rooms."""

    def __init__(self):
        """This function initializes the class."""

        self.rooms = {}
        self.clients = []

    async def add_client(self, client: WebSocket):
        """Adds the client to the list of connected clients."""
        self.clients.append(client)

    async def get_open_rooms(self, websocket: WebSocket):
        """Gets the rooms that are not full."""
        open_rooms = []
        room_descriptions = ["Rooms:"]
        for room_id, room in self.rooms.items():
            x_vacant = room["x"] is None
            o_vacant = room["o"] is None
            if x_vacant or o_vacant:
                if x_vacant and o_vacant:
                    self.rooms.pop(room_id)
                else:
                    open_rooms.append(room_id)
            room_descriptions.append(
                f"  {room_id}: {sum(map(bool, room.values())) } players"
            )

        await debug(websocket, "\n".join(room_descriptions))

        return open_rooms

    async def update_open_rooms(self, websocket: WebSocket):
        """This function sends information about new rooms to clients
        that are not connected to room."""

        open_rooms = await self.get_open_rooms(websocket)

        for client in self.clients:
            await client.send_json(
                {
                    "type": "update_open_rooms",
                    "open_rooms": open_rooms,
                }
            )


app = FastAPI()
app.mount("/client", StaticFiles(directory="client", html=True), name="client")

conn_manager = ConnectionManager()


@app.get("/")
async def root():
    """This function redirects to the `/client` subpath containing the client page content."""
    return RedirectResponse(url="/client")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main endpoint for websocket connection."""

    # Accept websocket connection.
    await websocket.accept()

    await conn_manager.add_client(websocket)

    # Listens to all messages from the connected client.
    try:
        while True:
            message = await websocket.receive_json()
            await debug(websocket, f"Received message '{message}'")

            match message["type"]:
                # If client wants to connect to the room:
                case "connect":
                    # Add client to the room.
                    room_id = message["room_id"]
                    room = conn_manager.rooms[room_id]
                    room["o"] = websocket

                    # Send message with type "connected" to the client.
                    await websocket.send_json(
                        {
                            "type": "connected",
                            "room_id": room_id,
                            "sign": "o",
                        }
                    )

                case "disconnect":
                    room_id = message["room_id"]
                    sign = message["sign"]

                    conn_manager.rooms[room_id][sign] = None

                    if sign == "x":
                        del conn_manager.rooms[room_id]

                    await conn_manager.add_client(websocket)

                    await conn_manager.update_open_rooms(websocket)

                    conn_manager.clients.remove(websocket)

                # If message type is "get_open_rooms":
                case "get_open_rooms":
                    open_rooms = await conn_manager.get_open_rooms(websocket)

                    await websocket.send_json(
                        {
                            "type": "update_open_rooms",
                            "open_rooms": open_rooms,
                        }
                    )

                # If message type is "create_room":
                case "create_room":
                    # Create room with client that created it.
                    room_id = randint(0, 10**5)
                    conn_manager.rooms[room_id] = {
                        "x": websocket,
                        "o": None,
                    }

                    # Send room_id to client.
                    await websocket.send_json(
                        {
                            "type": "connected",
                            "room_id": room_id,
                            "sign": "x",
                        }
                    )

                    await conn_manager.update_open_rooms(websocket)

                case "get_playercount":
                    # Send the number of connected players
                    num_players = len(conn_manager.clients)
                    await websocket.send_json(
                        {"type": "playercount", "playercount": num_players}
                    )
                case _:
                    await debug(websocket, "Invalid message type: " + message["type"])

    # If client has disconnected:
    except WebSocketDisconnect:
        conn_manager.clients.remove(websocket)
