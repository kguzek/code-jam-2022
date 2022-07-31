"""Main program of the server."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from server.gameManager import GameManager
from server.connectionManager import ConnectionManager


app = FastAPI()
app.mount("/client", StaticFiles(directory="client", html=True), name="client")

conn_manager = ConnectionManager()
game_manager = GameManager()


@app.get("/")
async def root():
    """This function redirects to the `/client` subpath containing the client page content."""
    return RedirectResponse(url="/client")


@app.websocket("/ws")
async def websocket_endpoint(client: WebSocket):
    """Main endpoint for websocket connection."""

    # Accept websocket connection and add connected client to list of open clients.
    await conn_manager.connect(client)

    # Listens to all messages from client.
    try:
        while True:
            message = await client.receive_json()
            print(f"Received message: {message}")

            match message["type"]:  # noqa: E999
                # If message type is "get_open_rooms":
                case "update_open_rooms":
                    open_rooms = await conn_manager.get_open_rooms()

                    print(f"Received update_open_rooms request")
                    print(f"open_rooms: {open_rooms}")
                    print(f"open_clients: {conn_manager.open_clients}")

                    await client.send_json(
                        {
                            "type": "update_open_rooms",
                            "open_rooms": open_rooms,
                        }
                    )

                # If client wants to connect to the open room:
                case "join_room":
                    player_x, player_o = await conn_manager.join_room(
                        client, message["room_id"]
                    )

                    if (player_x, player_o) == (None, None):
                        return

                    conn_manager.open_clients.remove(client)
                    print(f"Client {client} joined a room")
                    print(f"open_clients: {conn_manager.open_clients}")

                    # Update open rooms.
                    await conn_manager.update_open_rooms()

                    await game_manager.start_game(
                        message["room_id"], player_x, player_o
                    )

                # If the client left the room.
                case "leave_room":
                    await conn_manager.leave_room(client)

                # If message type is "create_room":
                case "create_room":
                    await conn_manager.create_room(client)

                    # Remove client from open clients.
                    conn_manager.open_clients.remove(client)

                    # Update open rooms
                    await conn_manager.update_open_rooms()

                case "move":
                    await game_manager.move(
                        message["room_id"],
                        message["sign"],
                        message["cell"],
                    )

    # If client has disconnected:
    except WebSocketDisconnect:
        print("Client disconnected")

        await conn_manager.leave_room(client)
