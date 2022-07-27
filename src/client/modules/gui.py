"""Module containing UI elements to be used in the game menus."""

from time import time
from typing import Callable, Coroutine, Literal, Text
from numpy import isin
import pygame
from modules import Colour, Axis, SCREEN_DIMS, event_loop

DEFAULT_DIMS = (300, 50)


def call_callbacks(callbacks: list[Callable[[], Coroutine | None]]):
    """Calls each callback in the list, scheduling any returned coroutines as tasks
    to be awaited in the running game event loop.
    """
    for callback in callbacks:
        coro = callback()
        if not isinstance(coro, Coroutine):
            continue
        event_loop.create_task(coro)


class BaseElement:
    DEFAULT_FONT: pygame.font.Font = None

    def __init__(
        self,
        label: str,
        pos: tuple[float, float],
        font: pygame.font.Font = None,
        font_colour: Colour = Colour.WHITE,
        dims: tuple[int, int] = DEFAULT_DIMS,
        container: list = None,
        disabled: bool = False,
    ) -> None:
        self.label = label
        if font is None:
            font = self.DEFAULT_FONT
        self.font = font
        self.font_colour: tuple[int, int, int] = font_colour.value
        self.render_text()

        self.dimensions = dims
        self.pos = tuple(self.get_coordinate(Axis(i), pos[i]) for i in range(2))

        self.is_hovered = False
        self.is_pressed = False
        self.disabled = disabled

        self._click_callbacks: dict[str, list[Callable[[], Coroutine | None]]] = {
            "down": [],
            "up": [],
        }

        if container is None:
            raise ValueError("No element container specified.")
        container.append(self)
        Menu.all_elements.append(self)

    def render_text(self) -> None:
        self.text = self.font.render(self.label, True, self.font_colour)
        self.text_width = self.text.get_width()
        self.text_height = self.text.get_height()

    def blit_text(self, screen: pygame.Surface, width_offset: int = 0) -> None:
        """Blits the element's label to the centre of its area."""
        self.render_text()
        x_pos, y_pos, width, height = self.pos + self.dimensions
        text_pos = (
            x_pos + (width - self.text_width + width_offset) // 2,
            y_pos + (height - self.text_height) // 2,
        )
        screen.blit(self.text, text_pos)

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
        is_hovered = self.check_collision(mouse_pos)
        if is_hovered != self.is_hovered:
            self.on_hover_change(is_hovered)
        is_pressed = self.is_hovered and mouse_btns[0]
        if is_pressed != self.is_pressed:
            # The state was changed
            if is_pressed:
                # User just clicked mouse button
                self._on_mouse_down()
            else:
                # User just released mouse button
                self._on_mouse_up()
        self.is_pressed = is_pressed

    def on_hover_change(self, is_hovered: bool) -> None:
        """Called once when the user cursor either enters or leaves the element boundaries."""
        cursor = (
            pygame.SYSTEM_CURSOR_NO
            if is_hovered and self.disabled
            else pygame.SYSTEM_CURSOR_ARROW
        )
        pygame.mouse.set_cursor(*pygame.Cursor(cursor))
        self.is_hovered = is_hovered

    def toggle_disabled_state(self) -> None:
        self.disabled = not self.disabled
        cursor = (
            pygame.SYSTEM_CURSOR_NO
            if self.is_hovered and self.disabled
            else pygame.SYSTEM_CURSOR_ARROW
        )
        pygame.mouse.set_cursor(*pygame.Cursor(cursor))

    def _on_mouse_down(self) -> None:
        """Called once when the user clicks the element."""
        self._call_callbacks("down")

    def _on_mouse_up(self) -> None:
        """Called once when the user releases the element."""
        self._call_callbacks("up")

    def _call_callbacks(self, callback_type) -> None:
        """Calls all the given callbacks, even if they are coroutines."""
        if self.disabled:
            # Don't fire click events if the button is disabled
            return
        call_callbacks(self._click_callbacks[callback_type])

    def on_mouse(self, action: Literal["down", "up"]):
        """Can be used to decorate functions that will be called when the element is clicked."""

        def wrapper(callback: Callable[[], Coroutine | None]):
            self._click_callbacks[action].append(callback)

        return wrapper


class Button(BaseElement):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, container=Menu.buttons, **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the button to the game window."""
        dimensions = self.pos + self.dimensions
        # Element background
        bg_colour = (
            Colour.GREY2
            if self.disabled
            else Colour.GREY5
            if self.is_hovered
            else Colour.GREY4
        )
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        self.blit_text(screen)
        super().draw(screen)


class SelectableElement(BaseElement):
    def __init__(self, *args, **kwargs) -> None:
        self.selected = False
        self._on_select_callbacks: list[Callable[[], Coroutine | None]] = []
        super().__init__(*args, **kwargs)

    def blit_detail(
        self,
        dest: pygame.Surface,
        src: pygame.Surface,
        colour: Colour | None = None,
        outline_colour: Colour | None = None,
    ) -> None:
        dims = (self.dimensions[1],) * 2
        surf = pygame.Surface(dims, pygame.SRCALPHA, 32)
        if colour:
            surf.fill(colour.value)
        if outline_colour:
            pygame.draw.rect(surf, outline_colour.value, (0, 0) + dims, 2)
        surf.blit(
            src,
            (
                (dims[0] - src.get_width()) // 2,
                (dims[1] - src.get_height()) // 2 + 1,
            ),
        )
        dest.blit(
            surf,
            (self.pos[0] + self.dimensions[0] - self.dimensions[1], self.pos[1]),
        )

    def check_click(
        self, mouse_pos: tuple[int, int], mouse_btns: tuple[bool, bool, bool]
    ):
        super().check_click(mouse_pos, mouse_btns)
        if mouse_btns[0] and not self.is_hovered and self.selected:
            self._set_selected(False)

    def _set_selected(self, selected: bool) -> None:
        self.selected = selected
        call_callbacks(self._on_select_callbacks)

    def _on_mouse_down(self) -> None:
        if not self.disabled and not self.selected:
            self._set_selected(True)
        return super()._on_mouse_down()

    def on_select_change(self, callback: Callable[[], Coroutine | None]):
        """Can be used to decorate functions that will be called on select or deselect."""
        self._on_select_callbacks.append(callback)


class TextInput(SelectableElement):
    CURSOR_WIDTH = 3  # px

    def __init__(
        self,
        label: str,
        placeholder: str,
        pos: tuple[float, float],
        font: pygame.font.Font,
        label_font: pygame.font.Font,
        detail_font: pygame.font.Font,
        **kwargs
    ) -> None:
        self.value = ""
        self.placeholder = placeholder
        self.last_blink = time()
        self.text_font = font
        self.show_cursor = False

        self.success = None

        self.check = detail_font.render("✓", True, Colour.GREEN.value)
        self.exclamation = detail_font.render("!", True, Colour.RED.value)
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
            Colour.GREY5
            if self.disabled
            else Colour.WHITE
            if self.selected
            else Colour.GREY7
        )
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        screen.blit(self.text, tuple(dim + 5 for dim in self.pos))
        text, colour = (
            (self.value, Colour.BLACK)
            if self.value or self.selected
            else (self.placeholder, Colour.GREY5)
        )
        value_text = self.text_font.render(text, True, colour.value)

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

        if self.success is not None:
            self.blit_detail(screen, self.check if self.success else self.exclamation)
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

    def _on_mouse_down(self) -> None:
        self.last_blink = time()
        self.show_cursor = True
        self.success = None
        return super()._on_mouse_down()

    def keydown(self, event: pygame.event.Event) -> None:
        if event.key == 8:
            # Backspace
            if event.mod & pygame.KMOD_LCTRL:
                # Ctrl+Backspace: remove last word
                self.value = " ".join(self.value.rstrip().split(" ")[:-1])
                return
            self.value = self.value[:-1]
            return
        if event.key in (pygame.key.key_code(key) for key in ("return", "escape")):
            # Return or escape
            self._set_selected(False)
            return
        self.value += event.unicode

    def on_hover_change(self, is_hovered: bool) -> None:
        super().on_hover_change(is_hovered)
        if not is_hovered or self.disabled:
            return
        pygame.mouse.set_cursor(*pygame.Cursor(pygame.SYSTEM_CURSOR_IBEAM))


class Dropdown(SelectableElement):
    def __init__(self, *args, icon_font: pygame.font.Font, options=[], **kwargs):
        self.selected_option = None
        self.options = options
        self.icon = icon_font.render("V", True, Colour.WHITE.value)
        super().__init__(
            *args,
            font_colour=Colour.BLACK,
            dims=(DEFAULT_DIMS[0], DEFAULT_DIMS[1] * 2 // 3),
            container=Menu.dropdowns,
            **kwargs
        )

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the dropdown box to the game window."""
        dimensions = self.pos + self.dimensions
        # Element background
        bg_colour = Colour.LIGHTBLUE if self.is_hovered else Colour.GREY7
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        self.blit_text(screen, -self.dimensions[1])
        self.blit_detail(
            screen,
            self.icon,
            Colour.GREY3 if self.is_hovered else Colour.GREY4,
            Colour.BLACK,
        )
        super().draw(screen)


class Option(BaseElement):
    def __init__(self, parent: Dropdown, value: str, *args, **kwargs):
        self.parent = parent
        self.value = value
        super().__init__(*args, container=[], **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the dropdown option to the game window."""
        super().draw(screen)

    def _on_mouse_down(self) -> None:
        self.parent.selected_option = self.value
        return super()._on_mouse_down()


class Menu:
    """Container class that holds all UI elements."""

    all_elements: list[BaseElement] = []
    buttons: list[Button] = []
    text_inputs: list[TextInput] = []
    dropdowns: list[Dropdown] = []
