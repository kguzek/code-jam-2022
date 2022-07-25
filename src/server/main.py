"""Entry point for the websocket server."""

from classes import ConnectionManager
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

app = FastAPI()
conn_manager = ConnectionManager()

app.mount("/", StaticFiles(directory="../client", html=True), name="root")


@app.route("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main endpoint for the websocket."""
    conn_manager.connect(websocket)
