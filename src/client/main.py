"""The entry point for the client-side application."""

import asyncio
from typing import Sequence
import pygame

from modules import backend, SCREEN_DIMS, event_loop, Colour, Font, GameStage, GameInfo
from modules.gui import Label, BaseElement, Button, Menu, TextInput, Dropdown

pygame.init()
pygame.key.set_repeat(500, 30)
FONT = Font(pygame.font.SysFont, pygame.font.Font)
BaseElement.DEFAULT_FONT = FONT.nimbus_sans

SCREEN = pygame.display.set_mode(SCREEN_DIMS)

CLOCK = pygame.time.Clock()
FRAMERATE = 60  # FPS

LOADING_MSG = "Connecting to server..."
SERVER_CONNECTION_ERROR_MSG = "Error connecting to server!"


# REGION Register menu elements
dropdown = Dropdown(
    "Select room",
    (0.5, 1 / 4),
    icon_font=FONT.reemkufiregular,
    options=["Remote server", "Locally-hosted server"],
    menu=Menu.settings,
)
ipt_server_url = TextInput(
    "Server URL",
    (0.5, 5 / 14),
    placeholder="E.g. localhost:8000",
    font=FONT.consolas,
    label_font=FONT.nimbus_sans_sm,
    detail_font=FONT.seguisym,
    menu=Menu.settings,
)
btn_join_room = Button("Join room", (0.5, 1 / 2), disabled=True, menu=Menu.settings)
btn_test = Button("Test", (0.5, 0.5))
btn_retry_connection = Button("Retry connnection", (0.5, 3 / 4))
txt_current_info = Label("", (0.5, 0.5))
# ENDREGION

# REGION Register element events


@btn_join_room.on_mouse("down")
def join_room():
    old_label = btn_join_room.label
    btn_join_room.toggle_disabled_state()
    btn_join_room.label = "Connecting to room..."
    GameInfo.current_stage = GameStage.LOADING
    btn_join_room.toggle_disabled_state()
    btn_join_room.label = old_label


# TODO: implement textbox on_value_change hook
# @ipt_server_url.on_select_change
def handle_value_change():
    if ipt_server_url.value or btn_join_room.disabled:
        return
    btn_join_room.toggle_disabled_state()


@btn_test.on_mouse("down")
def test_websocket():
    print("Sending the message to the backend")
    backend.session.send_message({"type": "test", "message": "hello world"})
    # backend.session.send_message("ping")


# ENDREGION


# REGION Register websocket events
@backend.session.on_server_message
def on_server_message(data: str or bytes) -> None:
    if isinstance(data, bytes):
        data = bytes.decode()
    print("Received message from server:", data)


@btn_retry_connection.on_mouse("down")
def connect_to_server() -> None:
    backend.connect_to_websocket(GameInfo.WEBSOCKET_URL)


# ENDREGION


def tick():
    """Performs logic on the game window."""

    mouse_pos = pygame.mouse.get_pos()
    # Determine which buttons were pressed
    clicked = pygame.mouse.get_pressed(num_buttons=3)

    match GameInfo.current_stage:
        case GameStage.JOIN_ROOM:
            visible_elems = Menu.settings
        case GameStage.WAITING_FOR_PLAYER | GameStage.GAME_IN_PROGRESS:
            visible_elems = [btn_test]
        case GameStage.WEBSOCKET_ERROR:
            txt_current_info.assert_properties(
                label=SERVER_CONNECTION_ERROR_MSG, font_colour=Colour.RED
            )
            visible_elems = [txt_current_info, btn_retry_connection]
        case GameStage.LOADING:
            txt_current_info.assert_properties(
                label=LOADING_MSG, font_colour=Colour.WHITE
            )
            visible_elems = [txt_current_info]
        case _:
            visible_elems = []
    for elem in visible_elems:
        elem.check_click(mouse_pos, clicked)
    return visible_elems


def render(visible_elems: Sequence[BaseElement]):
    """Rerenders the game window."""
    # Fill with white
    SCREEN.fill(Colour.GREY2.value)

    def render_fps():
        """Blit the current FPS to the screen."""
        fps = min(CLOCK.get_fps(), FRAMERATE)
        message = f"{fps:.1f} FPS"
        fps_percentage = fps / FRAMERATE
        amount_green = round(fps_percentage * 255)
        fps_colour = (255 - amount_green, amount_green, 0)
        fps_surface = FONT.nimbus_sans.render(message, True, fps_colour)
        SCREEN.blit(fps_surface, (0, 0))

    for elem in visible_elems:
        elem.draw(SCREEN)
    render_fps()
    pygame.display.update()


def run_once(loop: asyncio.AbstractEventLoop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


# Connect to the websocket
connect_to_server()

# Main game loop
try:
    while GameInfo.current_stage != GameStage.ABORTED:
        run_once(event_loop)
        CLOCK.tick(FRAMERATE)

        # Handle Pygame events
        events = pygame.event.get()
        for event in events:
            match event.type:
                case pygame.QUIT:
                    GameInfo.current_stage = GameStage.ABORTED
                case pygame.KEYDOWN:
                    for text_input in Menu.text_inputs:
                        if not text_input.selected:
                            continue
                        text_input.keydown(event)
        render(tick())
except KeyboardInterrupt:
    pass

# Clean up event loop and close HTTP session
event_loop.run_until_complete(backend.close())
event_loop.close()
