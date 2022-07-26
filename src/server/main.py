"""Websocket definitions."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse

from server.wsserver import ConnectionManager, Message, EventType

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
    client = await conn_manager.connect(websocket)

    async def transfer_client(data):
        try:
            room_id = int(data.get("roomid"))
        except (TypeError, ValueError):
            # TypeError if data.get() evaluates to None; ValueError if it cannot be cast to int
            return

        room = conn_manager.get_room(room_id)

        await room.broadcast(Message(EventType.CONNECT, client=client.serialised))
        await conn_manager.transfer_client(client, room)

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
