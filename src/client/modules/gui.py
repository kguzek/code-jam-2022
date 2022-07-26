"""Module containing UI elements to be used in the game menus."""

import pygame
from modules import Colour, Axis, SCREEN_DIMS

DEFAULT_DIMS = (200, 50)


class BaseElement:
    def __init__(
        self,
        pos: tuple[int, int],
        dims: tuple[int, int],
    ) -> None:
        self.pos = pos
        self.dimensions = dims
        self.pos = pos

    def get_coordinate(self, axis: Axis, fraction: float):
        """Gets the coordinate if we want the element to be the given fraction away from the
        screen's edge.
        """
        return round((SCREEN_DIMS[axis.value] - self.dimensions[axis.value]) * fraction)

    def get_pos(self, fractions: tuple[float, float]):
        """Gets the position in both axes according to `BaseElement.get_coordinate()`."""
        return tuple(self.get_coordinate(Axis(i), fractions[i]) for i in range(2))

    def centre(self, axis: Axis = Axis.BOTH) -> None:
        """Sets the element's position to the centre of the screen on the given axis."""
        pos_x, pos_y = self.pos
        if axis.value % 2 == 0:
            # need to centre horizontally
            pos_x = self.get_coordinate(Axis.HORIZONTAL, 0.5)
        if axis.value > 0:
            # need to centre vertically
            pos_y = self.get_coordinate(Axis.VERTICAL, 0.5)
        self.pos = pos_x, pos_y
        return self

    def check_collision(self, target_pos: tuple[int, int]) -> bool:
        """Determines if the target's coordinates are within the object's boundaries."""
        x_pos, y_pos = self.pos
        width, height = self.dimensions
        return (
            x_pos <= target_pos[0] <= x_pos + width
            and y_pos <= target_pos[1] <= y_pos + height
        )


class Button(BaseElement):
    def __init__(
        self,
        label: str,
        font: pygame.font.Font,
        pos_fractions: tuple[float, float],
        dims: tuple[int, int] = DEFAULT_DIMS,
    ) -> None:
        self.label = label
        self.text = font.render(label, True, Colour.WHITE.value)
        self.dimensions = dims
        self.text_width = self.text.get_width()
        self.text_height = self.text.get_height()
        self.active = False
        self.is_pressed = False
        Menu.buttons.append(self)
        pos = self.get_pos(pos_fractions)
        super().__init__(pos, dims)

    def draw(self, screen: pygame.Surface):
        """Blits the button to the game window."""
        dimensions = self.pos + self.dimensions
        # Button background
        bg_colour = Colour.DARK3 if self.active else Colour.DARK2
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        # Button outline
        pygame.draw.rect(screen, Colour.BLACK.value, dimensions, 2)
        x_pos, y_pos, width, height = dimensions
        text_pos = (
            x_pos + (width - self.text_width) // 2,
            y_pos + (height - self.text_height) // 2,
        )
        screen.blit(self.text, text_pos)

    def check_click(
        self, mouse_pos: tuple[int, int], clicked_buttons: tuple[bool, bool, bool]
    ) -> None:
        self.active = self.check_collision(mouse_pos)
        is_pressed = self.active and clicked_buttons[0]
        if is_pressed != self.is_pressed:
            # The state was changed
            if is_pressed:
                # User just clicked button
                self.on_mouse_down()
            else:
                # User just released mouse button
                self.on_mouse_up()
        self.is_pressed = is_pressed

    def on_mouse_down(self) -> None:
        """Called once when the user clicks the button."""
        # print("Clicked button", self.label)

    def on_mouse_up(self) -> None:
        """Called once when the user releases the button."""
        # print("Released button", self.label)


class Menu:
    """Container class that holds all UI elements."""

    buttons: list[Button] = []
