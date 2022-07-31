"""Package containing all client modules as well as miscellaneous constant definitions."""

import asyncio
from enum import Enum
from time import time
from typing import Callable

from pygame.font import Font

###################
# Change url here #
###################
SERVER_URL = "161.97.167.128:8123"

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_DIMS = (SCREEN_WIDTH, SCREEN_HEIGHT)

FRAMERATE = 60  # FPS

DEBUG_MODE = True

try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


class Colour(Enum):
    """Custom colours used in the client application."""

    RED = (255, 0, 0)
    GREEN = (0, 128, 0)
    BLUE = (0, 0, 255)
    CYAN = (0, 255, 255)
    PURPLE = (255, 0, 255)
    YELLOW = (255, 255, 0)
    BLACK = (0,) * 3
    GREY1 = (16,) * 3
    GREY2 = (32,) * 3
    GREY3 = (48,) * 3
    GREY4 = (64,) * 3
    GREY5 = (128,) * 3
    GREY6 = (192,) * 3
    GREY7 = (224,) * 3
    WHITE = (255,) * 3
    LIGHTBLUE = (204, 230, 255)


class Font:  # pylint:disable=too-few-public-methods
    """Custom fonts used in the client application."""

    def __init__(
        self,
        font_from_name: Callable[[str, int], Font],
        font_from_file: Callable[[str, int], Font],
    ):
        self.nimbus_sans_sm = font_from_name("Nimbus Sans L", 21)
        self.nimbus_sans = font_from_name("Nimbus Sans L", 24)
        self.nimbus_sans_xl = font_from_name("Nimbus Sans L", 34)
        self.consolas = font_from_name("Consolas", 17)
        self.reemkufiregular = font_from_name("reemkufiregular", 13)

        self.seguisym = font_from_file("src/client/data/seguisym.ttf", 23)


class GameStage(Enum):
    """Custom game stages."""

    ABORTED = 0
    LOADING = 1
    JOIN_ROOM = 2
    WAITING_FOR_PLAYER = 3
    GAME_IN_PROGRESS = 4
    GAME_FINISHED = 5
    WEBSOCKET_ERROR = 6


class Axis(Enum):
    """Enum containing the X-axis, Y-axis, and both axes."""

    HORIZONTAL = 0
    VERTICAL = 1
    BOTH = 2


class GameInfo:
    """Information pertaining to the current game process."""

    # WEBSOCKET_URL = "localhost:8000"
    WEBSOCKET_URL = SERVER_URL
    current_stage: GameStage = GameStage.LOADING
    ping = -1  # ms
    last_ping_check: float = time()
    playercount = 0
    connected_room = None
    player_sign = None
    game_started = False
    countdown_started: float = -1
    current_round: int = 0
    board: list[list[str]] = None


class Message(str):
    """Container for various messages that can be displayed to the client."""

    CONNECTION_FAILED = "Error connecting to server!"
    CONNECTION_DROPPED = "Connection to server lost!"
    SERVER_ERROR = CONNECTION_FAILED
