"""This file contains definition of GameManager class."""


from fastapi import WebSocket


class GameManager:
    """This class handles games."""

    def __init__(self):
        # List of all games.
        self.games = {}

    async def start_game(self, room_id: int, player_x: WebSocket, player_o: WebSocket):
        self.games[room_id] = {
            "x": player_x,
            "o": player_o,
            "board": [
                ["*", "*", "*"],
                ["*", "*", "*"],
                ["*", "*", "*"],
            ],
        }

        await player_x.send_json(
            {
                "type": "start_game",
            }
        )

        await player_o.send_json(
            {
                "type": "start_game",
            }
        )

    async def move(self, room_id: int, sign: str, cell: int):
        """This function updates the board and sends
        message with type 'update_board' to both players."""

        game = self.games[room_id]
        board = game["board"]

        # Update board.
        cell_row = cell // 3
        cell_col = cell % 3
        board[cell_row][cell_col] = sign

        # Send "update_board" message.
        for player in (game["x"], game["o"]):
            await player.send_json(
                {
                    "type": "update_board",
                    "board": board,
                }
            )

        # Check for win.
        win = self.check_win(board)

        if win:
            for player in (game["x"], game["o"]):
                await player.send_json(
                    {
                        "type": "win",
                        "sign": win[0],
                        "cells": win[1],
                    }
                )

        # Check for draw.

    def check_win(self, board: list):
        """This methon checks if the current player is won."""
        print(board)

        # Check if current player filled one of the rows
        for row_i, row in enumerate(board):
            if len(set(row)) == 1 and "*" not in row:
                print(f"{row[0]} won:", (row_i * 3, row_i * 3 + 1, row_i * 3 + 2))
                return row[0], (row_i * 3, row_i * 3 + 1, row_i * 3 + 2)

        # Check if current player filled one of the columns
        columns = [[board[i][j] for i in range(3)] for j in range(3)]
        for col_i, col in enumerate(columns):
            if len(set(col)) == 1 and "*" not in col:
                print(f"{col[0]} won:", (col_i, col_i + 3, col_i + 6))
                return col[0], (col_i, col_i + 3, col_i + 6)

        # Check if current player filled first diagonal
        d_1 = [board[i][i] for i in range(3)]
        if len(set(d_1)) == 1 and "*" not in d_1:
            print(f"{d_1[0]} won:", (0, 4, 8))
            return d_1[0], (0, 4, 8)

        d_2 = [board[i][2 - i] for i in range(3)]
        if len(set(d_2)) == 1 and "*" not in d_2:
            print(f"{d_2[0]} won:", (0, 4, 6))
            return d_2[0], (0, 4, 6)

        # Otherwise, return False
        return False
