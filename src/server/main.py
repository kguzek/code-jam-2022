"""Websocket definitions."""

from pydoc import cli
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from server.wsserver import ConnectionManager, EventType, Message

app = FastAPI()
conn_manager = ConnectionManager()

app.mount("/client", StaticFiles(directory="client", html=True), name="client")


@app.get("/")
async def root():
    """Redirects to the `/client` subpath containing the client static page content."""
    return RedirectResponse(url="/client")


@app.get("/test-connection")
async def test():
    """Endpoint to validate if the server is running."""
    return JSONResponse({"server-running": True})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main endpoint for the websocket."""

    # Client() object representing the connected client.
    client = await conn_manager.connect(websocket)

    async def transfer_client(room_id):
        room = conn_manager.get_room(room_id)

        await room.broadcast(Message(EventType.CONNECT, client=client.serialised))
        await conn_manager.transfer_client(client, room)

        return room

    try:
        while True:
            request = await client.recieve_data()

            match request["type"]:
                case "create_room":
                    # Create a room and then connect to it.

                    await client.debug("create_room")

                    # Create the room
                    room_id = len(conn_manager.rooms)

                    # Connect to the created room.
                    room = await transfer_client(room_id)
                    await client.debug(
                        f"Room created. len(room.clients): {len(room.clients)}"
                    )

                    # Send room_id to the client.
                    await client.socket.send_json(
                        {
                            "type": "create_room",
                            "room_id": room_id,
                        }
                    )
                case "transfer":
                    await transfer_client(request)

                case "get_rooms":
                    # Get all rooms that have only one connected player.
                    rooms = conn_manager.get_rooms()

                    data = Message(EventType.GET_ROOMS, rooms=rooms)

                    await client.send_message(data)

                case _:
                    pass

    except WebSocketDisconnect:
        # If player disconnects:

        # Disconnect client from the room.
        await conn_manager.disconnect(client)
