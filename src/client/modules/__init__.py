"""Package containing all client modules as well as miscellaneous constant definitions."""

import asyncio
from enum import Enum
from typing import Callable
from pygame.font import Font

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_DIMS = (SCREEN_WIDTH, SCREEN_HEIGHT)


try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


class Colour(Enum):
    """Custom colours used in the client application."""

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

    def __init__(self, font_init: Callable[[str, int], Font]):
        self.nimbus_sans = font_init("Nimbus Sans L", 24)
        self.nimbus_sans_sm = font_init("Nimbus Sans L", 21)
        self.consolas = font_init("Consolas", 17)
        self.reemkufiregular = font_init("reemkufiregular", 13)


class GameStage(Enum):
    """Custom game stages."""

    ABORTED = 0
    CONNECT_TO_SERVER = 1
    WAITING_FOR_PLAYER = 2
    GAME_IN_PROGRESS = 3


class Axis(Enum):
    """Enum containing the X-axis, Y-axis, and both axes."""

    HORIZONTAL = 0
    VERTICAL = 1
    BOTH = 2
