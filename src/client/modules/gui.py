"""Module containing UI elements to be used in the game menus."""

from time import time
import pygame
from modules import Colour, Axis, SCREEN_DIMS

DEFAULT_DIMS = (200, 50)


class BaseElement:
    def __init__(
        self,
        label: str,
        pos: tuple[float, float],
        font: pygame.font.Font = None,
        font_colour: Colour = Colour.WHITE,
        dims: tuple[int, int] = DEFAULT_DIMS,
        container: list = None,
    ) -> None:
        self.label = label
        if font is None:
            font = self.DEFAULT_FONT
        self.text = font.render(label, True, font_colour.value)
        self.text_width = self.text.get_width()
        self.text_height = self.text.get_height()

        self.dimensions = dims
        self.pos = tuple(self.get_coordinate(Axis(i), pos[i]) for i in range(2))

        self.is_hovered = False
        self.is_pressed = False
        if container is None:
            raise ValueError("No element container specified.")
        container.append(self)
        Menu.all_elements.append(self)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the element to the game window."""
        # Element outline
        pygame.draw.rect(screen, Colour.BLACK.value, self.pos + self.dimensions, 2)

    def get_coordinate(self, axis: Axis, fraction: float):
        """Gets the coordinate if we want the element to be the given fraction away from the
        screen's edge.
        """
        return round((SCREEN_DIMS[axis.value] - self.dimensions[axis.value]) * fraction)

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

    def check_click(
        self, mouse_pos: tuple[int, int], mouse_btns: tuple[bool, bool, bool]
    ):
        self.is_hovered = self.check_collision(mouse_pos)
        is_pressed = self.is_hovered and mouse_btns[0]
        if is_pressed != self.is_pressed:
            # The state was changed
            if is_pressed:
                # User just clicked mouse button
                self.on_mouse_down()
            else:
                # User just released mouse button
                self.on_mouse_up()
        self.is_pressed = is_pressed

    def on_mouse_down(self) -> None:
        """Called once when the user clicks the element."""

    def on_mouse_up(self) -> None:
        """Called once when the user releases the element."""


class Button(BaseElement):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, container=Menu.buttons, **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the button to the game window."""
        dimensions = self.pos + self.dimensions
        # Element background
        bg_colour = Colour.GREY5 if self.is_hovered else Colour.GREY4
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        self.blit_text(screen)
        super().draw(screen)

    def blit_text(self, screen: pygame.Surface) -> None:
        """Blits the element's label to the centre of its area."""
        x_pos, y_pos, width, height = self.pos + self.dimensions
        text_pos = (
            x_pos + (width - self.text_width) // 2,
            y_pos + (height - self.text_height) // 2,
        )
        screen.blit(self.text, text_pos)


class SelectableElement(BaseElement):
    def __init__(self, *args, **kwargs) -> None:
        self.selected = False
        super().__init__(*args, **kwargs)

    def check_click(
        self, mouse_pos: tuple[int, int], mouse_btns: tuple[bool, bool, bool]
    ):
        is_hovered = self.check_collision(mouse_pos)
        if mouse_btns[0] and not is_hovered:
            self.selected = False
        if is_hovered != self.is_hovered:
            self.on_hover_change(is_hovered)
        super().check_click(mouse_pos, mouse_btns)

    def on_mouse_down(self) -> None:
        self.selected = True

    def on_hover_change(self) -> None:
        """Called once when the selection state changes."""


class TextInput(SelectableElement):
    CURSOR_WIDTH = 3  # px

    def __init__(
        self, label, pos, font: pygame.font.Font, label_font: pygame.font.Font, **kwargs
    ) -> None:
        self.value = ""
        self.last_blink = time()
        self.text_font = font
        self.show_cursor = False

        super().__init__(
            label,
            pos,
            font=label_font,
            font_colour=Colour.GREY2,
            container=Menu.text_inputs,
            **kwargs
        )

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the input box to the game window."""
        dimensions = self.pos + self.dimensions
        # Element background
        bg_colour = (
            Colour.WHITE
            if self.selected
            else Colour.LIGHTBLUE
            if self.is_hovered
            else Colour.GREY7
        )
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        screen.blit(self.text, tuple(dim + 5 for dim in self.pos))
        value_text = self.text_font.render(self.value, True, Colour.BLACK.value)

        # Initialise text surface container
        text_width = value_text.get_width()
        text_height = value_text.get_height()
        text_surf_dims = (text_width + self.CURSOR_WIDTH, text_height)
        # Blit inputted text onto `text_surf`
        text_surf = pygame.Surface(text_surf_dims, pygame.SRCALPHA, 32)
        text_surf.blit(value_text, (0, 0))
        # Blit cursor onto `text_surf`
        if self.selected:
            self.draw_cursor(text_surf, text_width, text_height)

        # Blit `text_surf` onto visible text area
        text_area_dims = (self.dimensions[0] - 10, self.dimensions[1] - 30)
        text_area = pygame.Surface(text_area_dims, pygame.SRCALPHA, 32)
        if text_surf_dims[0] >= text_area_dims[0] and self.selected:
            # Need to crop from left side since there is text overflow
            crop_area = (
                text_surf_dims[0] - text_area_dims[0],
                0,
                text_area_dims[0],
                text_area_dims[1],
            )
        else:
            # Don't crop the text since it fits in the text area
            crop_area = None
        text_area.blit(text_surf, (0, 0), crop_area)

        screen.blit(text_area, (self.pos[0] + 5, self.pos[1] + 25))
        super().draw(screen)

    def draw_cursor(self, surface: pygame.Surface, txt_wdth: int, txt_hgt: int) -> None:
        """Draws the blinking cursor."""
        now = time()
        blink_diff = now - self.last_blink
        if blink_diff > 1:
            self.last_blink = now
            self.show_cursor = True
        elif blink_diff > 0.5:
            self.show_cursor = False
        if not self.show_cursor:
            return
        cursor_dims = (txt_wdth, 0, self.CURSOR_WIDTH, txt_hgt)
        pygame.draw.rect(surface, Colour.BLACK.value, cursor_dims)

    def keydown(self, event: pygame.event.Event) -> None:
        print(event)
        if event.key == 8:
            # Backspace
            if event.mod & pygame.KMOD_LCTRL:
                print("here")
                # Ctrl+Backspace: remove last word
                self.value = " ".join(self.value.rstrip().split(" ")[:-1])
                return
            self.value = self.value[:-1]
            return
        if event.key in (pygame.key.key_code(key) for key in ("return", "escape")):
            # Return or escape
            self.selected = False
            return
        self.value += event.unicode

    def on_hover_change(self, is_hovered: bool) -> None:
        cursor = (
            pygame.SYSTEM_CURSOR_IBEAM if is_hovered else pygame.SYSTEM_CURSOR_ARROW
        )
        pygame.mouse.set_cursor(*pygame.Cursor(cursor))


class Dropdown(SelectableElement):
    def __init__(self, *args, options=[], **kwargs):
        self.selected_option = None
        self.options = options
        super().__init__(*args, container=Menu.dropdowns, **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the dropdown box to the game window."""
        dimensions = self.pos + self.dimensions
        # Element background
        bg_colour = (
            Colour.WHITE
            if self.selected
            else Colour.LIGHTBLUE
            if self.is_hovered
            else Colour.GREY7
        )
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        super().draw(screen)


class Option(BaseElement):
    def __init__(self, parent: Dropdown, value: str, *args, **kwargs):
        self.parent = parent
        self.value = value
        super().__init__(*args, container=[], **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the dropdown option to the game window."""
        super().draw(screen)

    def on_mouse_down(self) -> None:
        self.parent.selected_option = self.value


class Menu:
    """Container class that holds all UI elements."""

    all_elements: list[BaseElement] = []
    buttons: list[Button] = []
    text_inputs: list[TextInput] = []
    dropdowns: list[Dropdown] = []
