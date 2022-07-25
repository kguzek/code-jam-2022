import wsserver as s
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()
conn_manager = s.ConnectionManager()

@app.get("/")
async def root():
    with open("../client/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main endpoint for the websocket."""
    client = await conn_manager.connect(websocket)
    while True:
        data = await client.recieve_data()
        print(data)

        match data["type"]:
            case "transfer":
                if data.get("roomid"):
                    try: id = int(data.get("roomid"))
                    except ValueError: continue

                    room = conn_manager.get_room(data.get("roomid"))
                    await conn_manager.transfer_client(client, room)
                    await client.send_data({
                        "type": "transferred",
                        "roomid": room.id
                    })

            case _:
                pass

        print(conn_manager)