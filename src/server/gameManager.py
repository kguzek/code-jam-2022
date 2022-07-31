"""This file contains definition of GameManager class."""


from fastapi import WebSocket


class GameManager:
    """This class handles games."""

    def __init__(self):
        # List of all games.
        self.games = {}

    async def send_both(self, game: dict, message: dict):
        for player in (game["player_x"], game["player_o"]):
            await player.send_json(message)

    async def start_round(self, game: dict, round: int):
        await self.send_both(
            game,
            {
                "type": "start_countdown",
                "round": round,
                "end_countdown_time": "",
            },
        )

    def reset_board(self, room_id: int):
        self.games[room_id]["board"] = [
            ["*", "*", "*"],
            ["*", "*", "*"],
            ["*", "*", "*"],
        ]

    async def start_game(self, room_id: int, player_x: WebSocket, player_o: WebSocket):
        # Create game.
        self.games[room_id] = {
            "player_x": player_x,
            "player_o": player_o,
            "board": [
                ["*", "*", "*"],
                ["*", "*", "*"],
                ["*", "*", "*"],
            ],
            "x_wins": 0,
            "o_wins": 0,
            "played_rounds": 1,
        }

        await self.start_round(self.games[room_id], 1)

    async def move(self, room_id: int, sign: str, cell: int):
        """This function updates the board and sends
        message with type 'update_board' to both players."""

        game = self.games[room_id]
        board = game["board"]

        # Update board dict.
        cell_row = cell // 3
        cell_col = cell % 3
        board[cell_row][cell_col] = sign

        # Send "update_board" message.
        await self.send_both(
            game,
            {
                "type": "update_board",
                "board": board,
            },
        )

        # Check win_board.
        winner, win_cells = self.check_win_round(board)

        if (winner, win_cells) != (None, None):
            # Update winner score.
            game[winner + "_wins"] += 1

            # Send "win_round" message.
            await self.send_both(
                game,
                {
                    "type": "win_round",
                    "sign": winner,
                    "cells": win_cells,
                    "x_wins": game["x_wins"],
                    "o_wins": game["o_wins"],
                },
            )

            game["played_rounds"] += 1
            await self.start_round(game, game["played_rounds"])
            self.reset_board(room_id)

        # Check for draw_round.
        if self.check_draw_round(board):
            game["x_wins"] += 1
            game["o_wins"] += 1
            await self.send_both(
                game,
                {
                    "type": "draw_round",
                    "x_wins": game["x_wins"],
                    "o_wins": game["o_wins"],
                },
            )

            game["played_rounds"] += 1
            await self.start_round(game, game["played_rounds"])
            self.reset_board(room_id)

        # Check is game is over

    def check_win_round(self, board: list):
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
            print(f"{d_2[0]} won:", (2, 4, 6))
            return d_2[0], (2, 4, 6)

        # Otherwise, return False
        return (None, None)

    def check_draw_round(self, board):
        print("draw", board)

        return all([row.count("*") == 3 for row in board])
