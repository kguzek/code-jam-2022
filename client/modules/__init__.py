"""Package containing all client modules as well as miscellaneous constant definitions."""

from enum import Enum
from typing import Callable
from pygame.font import Font


class Colour(Enum):
    """Custom colours used in the client application."""

    NEAR_BLACK = (50,) * 3
    WHITE = (255,) * 3


class Font:  # pylint:disable=too-few-public-methods
    """Custom fonts used in the client application."""

    def __init__(self, font_initialiser: Callable[[str, int], Font]):
        self.nimbus_sans = font_initialiser("Nimbus Sans L", 24)
