"""Websocket definitions."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from server.wsserver import ConnectionManager

app = FastAPI()
conn_manager = ConnectionManager()


@app.get("/")
async def root():
    """Returns static file web client."""
    with open("./client/index.html", "r", encoding="UTF-8") as file:
        return HTMLResponse(file.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main endpoint for the websocket."""
    client = await conn_manager.connect(websocket)

    async def transfer_client(data):
        try:
            room_id = int(data.get("roomid"))
        except (TypeError, ValueError):
            # TypeError if data.get() evaluates to None; ValueError if it cannot be cast to int
            return

        room = conn_manager.get_room(room_id)

        await room.broadcast({"type": "new_connection", "name": client.name})

        await conn_manager.transfer_client(client, room)
        await client.send_data(
            {
                "type": "transferred",
                "roomid": room.room_id,
                "clients": [i.name for i in room.clients],
            }
        )

    try:
        while True:
            data = await client.recieve_data()
            print(data)

            match data["type"]:
                case "transfer":
                    await transfer_client(data)

                case _:
                    pass

            print(conn_manager)

    except WebSocketDisconnect:
        await conn_manager.disconnect(client)
        # TODO: alert other clients in the room that the client has disconnected
