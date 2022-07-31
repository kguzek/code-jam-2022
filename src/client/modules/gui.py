"""Module containing UI elements to be used in the game menus."""

from time import time
from typing import Callable, Coroutine, Literal, Sequence
import pygame
from modules import Colour, Axis, SCREEN_DIMS, util, GameInfo, backend
from modules.util import debug

DEFAULT_DIMENSIONS = (300, 50)


class BaseElement:
    """Base UI element abstract class for specific elements to inherit from."""

    DEFAULT_FONT: pygame.font.Font = None

    def __init__(
        self,
        label: str,
        pos: tuple[float, float],
        /,
        *,
        font: pygame.font.Font = None,
        font_colour: Colour = Colour.WHITE,
        dims: tuple[int, int] = DEFAULT_DIMENSIONS,
        container: Sequence = None,
        menu: Sequence = None,
        menus: Sequence[Sequence] = None,
        disabled: bool = False,
    ) -> None:
        self.label = label
        if font is None:
            font = self.DEFAULT_FONT
        self.font = font
        self.font_colour = font_colour
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
            raise ValueError(
                "No element container specified. This is likely a development error, "
                "and @kguzek simply forgot to add the appropriate line "
                "when inheriting from `gui.BaseElement`."
            )
        container.append(self)
        if menu is not None:
            menu.append(self)
        if menus is not None:
            for m in menus:
                m.append(self)
        Menu.all_elements.append(self)

    def render_text(self) -> None:
        self.text = self.font.render(self.label, True, self.font_colour.value)
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

    def draw(
        self, screen: pygame.Surface, exclude_top: bool = False, width: int = 2
    ) -> None:
        """Blits the element to the game window. For `BaseElement`, this means blitting a black
        rectangular outline. This method is meant to be overriden by subclasses, but calls to the
        it may still be made."""
        # Element outline
        if exclude_top:
            top_left = self.pos
            bottom_left = (self.pos[0], self.pos[1] + self.dimensions[1])
            bottom_right = tuple(self.pos[i] + self.dimensions[i] for i in range(2))
            top_right = (self.pos[0] + self.dimensions[0], self.pos[1])

            pygame.draw.lines(
                screen,
                Colour.BLACK.value,
                closed=True,
                points=(top_left, bottom_left, bottom_right, top_right),
                width=width,
            )
        else:
            pygame.draw.rect(
                screen, Colour.BLACK.value, self.pos + self.dimensions, width
            )

    def get_coordinate(self, axis: Axis, fraction: float):
        """Gets the coordinate if we want the element to be the given fraction away from the
        screen's edge.
        """
        if not 0 <= fraction <= 1:
            raise ValueError(
                f"Invalid fraction provided for element position: {fraction}"
            )
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
    ) -> bool:
        """Checks if the mouse position impedes on the element boundaries.
        Returns a boolean indicating if the mouse is currently hovering over the element.
        Responsible for emitting the `on_hover_change()` and `on_mouse()` listener events."""
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
        return is_hovered

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
        # debug("Set", self.label, "to", "disabled" if self.disabled else "enabled")
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
        util.call_callbacks(self._click_callbacks[callback_type])

    def on_mouse(self, action: Literal["down", "up"]):
        """Can be used to decorate functions that will be called when the element is clicked."""

        def wrapper(callback: Callable[[], Coroutine | None]):
            self._click_callbacks[action].append(callback)
            return callback

        return wrapper


class SelectableElement(BaseElement):
    """Abstract element for selectable elements to inherit from."""

    def __init__(
        self, *args, inverse_selection_on_click: bool = False, **kwargs
    ) -> None:
        self.selected = False
        self.inverse_selection_on_click = inverse_selection_on_click
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
    ) -> bool:
        super().check_click(mouse_pos, mouse_btns)
        # Deselect if clicked out of region
        if mouse_btns[0] and not self.is_hovered and self.selected:
            self._set_selected(False)
        return self.is_hovered

    def _set_selected(self, selected: bool) -> None:
        self.selected = selected
        util.call_callbacks(self._on_select_callbacks)

    def _on_mouse_down(self) -> None:
        if not self.disabled:
            selected = not self.selected
            if self.inverse_selection_on_click:
                self._set_selected(selected)
            elif selected:
                self._set_selected(True)

        return super()._on_mouse_down()

    def on_select_change(self, callback: Callable[[], Coroutine | None]):
        """Can be used to decorate functions that will be called on select or deselect."""
        self._on_select_callbacks.append(callback)


class Label(BaseElement):
    """Basic element that blits text to the screen."""

    def __init__(self, label: str, pos: tuple[float, float], **kwargs) -> None:
        super().__init__(label, pos, container=Menu.labels, **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the label to the game window."""
        self.blit_text(screen)

    def assert_properties(self, **values):
        """Sets all the given properties to the specified values, if they are not already so.
        Returns the object again, allowing for method chaining."""
        for key, value in values.items():
            if self.__getattribute__(key) == value:
                continue
            self.__setattr__(key, value)
        return self


class Button(BaseElement):
    """Button element that listens for hover and click events."""

    def __init__(self, label: str, pos: tuple[float, float], **kwargs) -> None:
        super().__init__(label, pos, container=Menu.buttons, **kwargs)

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


class TextInput(SelectableElement):
    """Text box element that accepts user-inputted text."""

    CURSOR_WIDTH = 3  # px

    def __init__(
        self,
        label: str,
        pos: tuple[float, float],
        /,
        *,
        placeholder: str,
        font: pygame.font.Font,
        label_font: pygame.font.Font,
        detail_font: pygame.font.Font,
        **kwargs,
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
            **kwargs,
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
            self._draw_cursor(text_surf, text_width, text_height)

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

    def _draw_cursor(
        self, surface: pygame.Surface, txt_wdth: int, txt_hgt: int
    ) -> None:
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


class Option(BaseElement):
    """Child element that is displayed for each possible option of a `Dropdown` element."""

    def __init__(
        self,
        label: str,
        pos: tuple[float, float],
        value: str,
        *args,
        **kwargs,
    ):
        self.value = value
        super().__init__(label, (0, 0), *args, container=[], **kwargs)
        self.pos = pos

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the dropdown option to the game window."""
        colour = Colour.LIGHTBLUE if self.is_hovered else Colour.GREY7
        pygame.draw.rect(screen, colour.value, self.pos + self.dimensions)
        self.blit_text(screen)
        super().draw(screen, exclude_top=True)


class Dropdown(SelectableElement):
    """Dropdown box that reveals an arbitrary number of selectable `Option` elements."""

    def __init__(
        self,
        label: str,
        pos: tuple[float, float],
        /,
        *,
        icon_font: pygame.font.Font,
        options: Sequence[tuple[int, str]] = [],
        **kwargs,
    ):
        self.placeholder_label = label
        self.selected_option = None
        self.icon = icon_font.render("V", True, Colour.WHITE.value)
        self._selection_callbacks: list[Callable[[], Coroutine | None]] = []
        super().__init__(
            label,
            pos,
            inverse_selection_on_click=True,
            font_colour=Colour.BLACK,
            dims=(DEFAULT_DIMENSIONS[0], DEFAULT_DIMENSIONS[1] * 2 // 3),
            container=Menu.dropdowns,
            **kwargs,
        )
        self.set_options(options)

    def _create_option(self, index: int, option: tuple[int, str]) -> Option:
        """Creates a child option element."""
        # Calculate absolute Y position using the index of the element and its dimensions
        elem_y = self.pos[1] + self.dimensions[1] - 2 + DEFAULT_DIMENSIONS[1] * index
        option_key, option_desc = option
        elem = Option(
            option_desc,
            (self.pos[0], elem_y),
            dims=(DEFAULT_DIMENSIONS[0] - self.dimensions[1], DEFAULT_DIMENSIONS[1]),
            font_colour=Colour.BLACK,
            value=option_key,
        )

        def select_option():
            """Event handler for when a dropdown option is selected."""
            self.selected_option, self.label = option
            # Collapse the dropdown menu
            self._set_selected(False)
            util.call_callbacks(self._selection_callbacks)

        elem.on_mouse("down")(select_option)

        return elem

    def draw(self, screen: pygame.Surface) -> None:
        """Blits the dropdown box to the game window."""
        dimensions = self.pos + self.dimensions
        # Element background
        bg_colour = (
            Colour.LIGHTBLUE
            if self.is_hovered and not self.selected and not self.disabled
            else Colour.GREY7
        )
        pygame.draw.rect(screen, bg_colour.value, dimensions)
        self.blit_text(screen, -self.dimensions[1])
        self.blit_detail(
            screen,
            self.icon,
            Colour.GREY3 if self.is_hovered and not self.disabled else Colour.GREY4,
            Colour.BLACK,
        )
        super().draw(screen)
        if self.selected:
            for elem in self.option_elems:
                elem.draw(screen)

    def set_options(self, options: Sequence[tuple[int, str]]) -> None:
        """Updates the dropdown element's options."""
        # debug("dropdown:", len(options), self.disabled)
        # Toggle the disabled state if it is incorrect
        if (len(options) > 0) == self.disabled:
            self.toggle_disabled_state()
        if self.selected_option not in options:
            self.label = self.placeholder_label
        self.options = tuple(options)
        self.option_elems = [
            self._create_option(*option) for option in enumerate(self.options)
        ]

    def on_selection_change(
        self, callback: Callable[[], Coroutine | None]
    ) -> Callable[[], Coroutine | None]:
        """Can be used to decorate functions that will be called when an option is selected."""
        self._selection_callbacks.append(callback)
        return callback


class Grid(BaseElement):
    """Base class for the Tic-Tac-Toe 3x3 grid."""

    CELL_SIZE = 90  # width/height, px

    def __init__(self, label: str, pos: tuple[float, float], **kwargs) -> None:
        dims = (self.CELL_SIZE * 3,) * 2
        super().__init__(label, pos, dims=dims, container=[], **kwargs)
        self.reset()

    def reset(self):
        """Called whenever the board has to be cleared."""

        GameInfo.board = [["*"] * 3] * 3
        self.child_cells = list(self._create_cell_elements())

    def draw(self, screen: pygame.Surface) -> None:
        for elem in self.child_cells:
            elem.draw(screen)
        return super().draw(screen)

    def toggle_disabled_state(self) -> None:
        super().toggle_disabled_state()
        for elem in self.child_cells:
            elem.toggle_disabled_state()
            elem.font_colour = Colour.WHITE if elem.disabled else Colour.BLACK

    def _create_cell_elements(self):
        for row in range(3):
            for col in range(3):
                coords = (col, row)
                cell_pos = tuple(
                    pos + coords[i] * self.CELL_SIZE for i, pos in enumerate(self.pos)
                )
                # cell_x = self.pos[0] + col * self.CELL_SIZE
                # cell_y = self.pos[1] + row * self.CELL_SIZE
                cell = GridCell(
                    (0, 0), dims=(self.CELL_SIZE,) * 2, disabled=True, row=row, col=col
                )
                cell.pos = cell_pos

                yield cell


class GridCell(BaseElement):
    """Class for each cell of the `Grid` element."""

    def __init__(
        self,
        pos: tuple[float, float],
        /,
        *,
        dims: tuple[int, int],
        row: int,
        col: int,
        **kwargs,
    ) -> None:
        self.row = row
        self.col = col
        super().__init__("*", pos, container=[], dims=dims, **kwargs)

    def draw(self, screen: pygame.Surface) -> None:
        colour = (
            Colour.GREY3
            if self.disabled
            else Colour.GREY7
            if self.is_hovered and self.label == "*"
            else Colour.WHITE
        )
        pygame.draw.rect(screen, colour.value, self.pos + self.dimensions)
        self.blit_text(screen)
        return super().draw(screen, width=1)

    def _on_mouse_down(self) -> None:
        """Called whenever the user clicks a cell."""
        super()._on_mouse_down()
        if self.disabled:
            return
        debug(f"Clicked cell ({self.col}, {self.row})")
        if self.label != "*":
            return
        self.label = GameInfo.player_sign
        backend.session.send_message(
            {
                "type": "move",
                "room_id": GameInfo.connected_room,
                "cell": self.row * 3 + self.col,
                "sign": GameInfo.player_sign,
            }
        )


class Menu:
    """Container class that holds all UI elements."""

    all_elements: list[BaseElement] = []
    settings: list[BaseElement] = []
    game: list[BaseElement] = []

    labels: list[Label] = []
    buttons: list[Button] = []
    text_inputs: list[TextInput] = []
    dropdowns: list[Dropdown] = []
