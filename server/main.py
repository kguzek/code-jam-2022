"""Entry point for the application websocket server."""

from asyncio import gather
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from fastapi.staticfiles import StaticFiles


def debug(*args):
    """Log the message if debug mode is enabled."""
    if DEBUG:
        print(*args)


DEBUG = True


app = FastAPI()

app.mount("/ui", StaticFiles(directory="../client",html = True), name="client")


class ConnectionManager:
    """Code relating to connecting to the websocket server."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connected_player = None

    async def connect(self, websocket: WebSocket):
        """Creates a new connection between the server and the client."""
        await websocket.accept()

        if len(self.active_connections) == 2:
            await websocket.close(4000)

            return False

        self.active_connections.append(websocket)

        if len(self.active_connections) == 1:
            await websocket.send_json({"type": "connection", "player": "x"})

            self.connected_player = "x"
        elif len(self.active_connections) == 2:
            await websocket.send_json({"type": "connection", "player": "o"})

            await self.active_connections[0].send_json({"type": "start"})

            self.connected_player = "o"
        return True

    async def disconnect(self, websocket: WebSocket):
        """Disposes the websocket connection."""
        self.active_connections.remove(websocket)

        if self.active_connections:
            await self.active_connections[0].send_json({"type": "disconnect"})

    async def broadcast(self, message: dict):
        """Sends the message to all active connections."""
        coroutine = (conn.send_json(message) for conn in self.active_connections)
        # Execute all coroutines in parallel
        gather(*coroutine)


class GameManager:
    """Code relating to the game logic."""

    def __init__(self):
        """Initialises all properties to None, then sets the starting values in `reset()`."""
        self.board = None
        self.players = None
        self.is_started = None
        self.current_player = None
        self.reset()

    def add_player(self, player: str, websocket: WebSocket):
        """Adds the websocket to the map of connected players."""
        self.players[player] = websocket

    def start(self):
        """Starts the game, with player 'x' having the first move."""
        self.is_started = True
        self.current_player = "x"

    async def process_turn(self, turn: dict):
        """Handles the incoming turns and sends the corresponding messages to players."""

        debug(turn)

        player = turn["player"]
        cell = turn["cell"]

        if self.current_player != player:
            await manager.broadcast(
                {"type": "denied", "player": player, "message": "Wait for your turn"}
            )
            return

        cell_row, cell_col = divmod(cell, 3)

        if self.board[cell_row][cell_col] != "*":
            await manager.broadcast(
                {
                    "type": "denied",
                    "player": player,
                    "message": "You can't move in this cell",
                }
            )
            return

        await manager.broadcast({"type": "turn", "player": player, "cell": cell})

        self.board[cell_row][cell_col] = player

        # Check if there is a player who won.
        win = self.check_win()
        if win:
            await manager.broadcast(
                {"type": "win", "winner": self.current_player, "cells": win}
            )

            self.reset()

            return

        self.toggle_current_player()

    def toggle_current_player(self):
        """Toggles the current player, which is asked to make a move."""

        if self.current_player == "x":
            self.current_player = "o"

        elif self.current_player == "o":
            self.current_player = "x"

    @property
    def is_ready(self):
        """Returns a boolean indicating if the number of players connected is 2."""
        return len(self.players) == 2

    def check_win(self):
        """Checks if the current player is won and, if so,
        returns cells that led to the win. Otherwise returns False."""

        # Check if current player won by filling one of the rows
        for row_i, row in enumerate(self.board):
            if row.count(self.current_player) == 3:
                return (row_i * 3, row_i * 3 + 1, row_i * 3 + 2)

        # Check if current player won by filling one of the columns
        columns = [[self.board[i][j] for i in range(3)] for j in range(3)]
        for col_i, col in enumerate(columns):
            if col.count(self.current_player) == 3:
                return (col_i, col_i + 3, col_i + 6)

        # Check if current player won by filling first diagonal
        if all(self.board[i][i] == self.current_player for i in range(3)):
            return (0, 4, 8)

        # Check if current player won by filling second diagonal
        if all(self.board[i][2 - i] == self.current_player for i in range(3)):
            return (0, 4, 6)

        # Otherwise, current player didn`t won, so return False
        return False

    def reset(self):
        """Resets the game to the defaults."""
        self.board = [["*"] * 3] * 3
        self.players = {}
        self.is_started = False
        self.current_player = ""


manager = ConnectionManager()
game = GameManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main websocket endpoint for the client connection to the server."""
    is_player_connected = await manager.connect(websocket)

    # If the game is already started, then exit
    if not is_player_connected:
        return

    game.add_player(manager.connected_player, websocket)

    if game.is_ready:
        game.start()

    try:
        while True:
            data = await websocket.receive_json()

            if game.is_started:
                await game.process_turn(data)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        game.reset()
