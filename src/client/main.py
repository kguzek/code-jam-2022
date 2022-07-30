"""The entry point for the client-side application."""

import asyncio
import json
from random import random
from typing import Sequence
import pygame

from modules import (
    backend,
    SCREEN_DIMS,
    FRAMERATE,
    event_loop,
    Colour,
    Font,
    GameStage,
    GameInfo,
    Message,
)
from modules.gui import Label, BaseElement, Button, Menu, Dropdown

pygame.init()
pygame.key.set_repeat(500, 30)
FONT = Font(pygame.font.SysFont, pygame.font.Font)
BaseElement.DEFAULT_FONT = FONT.nimbus_sans

SCREEN = pygame.display.set_mode(SCREEN_DIMS)
pygame.display.set_caption("Tic-tac-toe")

CLOCK = pygame.time.Clock()


# REGION Register menu elements
dropdown = Dropdown(
    "Select room",
    (0.5, 2 / 7),
    icon_font=FONT.reemkufiregular,
    options=["Remote server", "Locally-hosted server"],
    menu=Menu.settings,
)
btn_join_room = Button("Join room", (0.5, 11 / 28), disabled=True, menu=Menu.settings)
btn_create_room = Button("Create room", (0.5, 17 / 28), menu=Menu.settings)
btn_retry_connection = Button("Retry connnection", (0.5, 9 / 14))
lbl_current_info = Label("[ARBITRARY MESSAGE]", (0.5, 0.5))
# ipt_server_url = TextInput(
#     "Server URL",
#     (0.5, 5 / 14),
#     placeholder="E.g. localhost:8000",
#     font=FONT.consolas,
#     label_font=FONT.nimbus_sans_sm,
#     detail_font=FONT.seguisym,
# )
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


@btn_create_room.on_mouse("down")
def create_room():
    """Sends a message to the server instructing it to create a new room, and transfer the client
    to it."""
    backend.session.send_message({"type": "create_room"})


# TODO: implement textbox on_value_change hook
# @ipt_server_url.on_select_change
# def handle_value_change():
#     if ipt_server_url.value or btn_join_room.disabled:
#         return
#     btn_join_room.toggle_disabled_state()

# ENDREGION


# REGION Register websocket events
@backend.session.on_server_message
def on_server_message(data: str | bytes) -> None:
    if isinstance(data, bytes):
        data = bytes.decode()
    try:
        parsed = json.loads(data)
    except (TypeError, json.decoder.JSONDecodeError):
        print("Invalid server message:", data)
        return
    else:
        data = parsed
    match data.get("type"):
        case "update_open_rooms":
            open_rooms = data.get("open_rooms")
            print("Open rooms:", open_rooms)
        case "connected":
            room_id = data.get("room_id")
            sign = data.get("sign")
            print("YOU ARE:", sign, "in room", room_id)
        case "log":
            print("SERVER:", data)
        case _:
            print("Received unknown server message:", data)


@btn_retry_connection.on_mouse("down")
def connect_to_server() -> None:
    """Instructs the program to start a thread to create the websocket connection."""
    backend.connect_to_websocket(GameInfo.WEBSOCKET_URL)


# ENDREGION


def tick():
    """Performs logic on the game window."""
    mouse_pos = pygame.mouse.get_pos()
    # Determine which buttons were pressed
    clicked = pygame.mouse.get_pressed(num_buttons=3)

    match GameInfo.current_stage:
        case GameStage.JOIN_ROOM:
            visible_elems = Menu.settings + [
                lbl_current_info.assert_properties(label="or", font_colour=Colour.WHITE)
            ]
        case GameStage.WAITING_FOR_PLAYER | GameStage.GAME_IN_PROGRESS:
            visible_elems = []
        case GameStage.WEBSOCKET_ERROR:
            visible_elems = [
                lbl_current_info.assert_properties(
                    label=Message.SERVER_ERROR, font_colour=Colour.RED
                ),
                btn_retry_connection,
            ]
        case GameStage.LOADING:
            visible_elems = [
                lbl_current_info.assert_properties(
                    label=Message.LOADING, font_colour=Colour.WHITE
                )
            ]
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
        padding = 2  # space between the text and the screen edge, px
        SCREEN.blit(fps_surface, (padding,) * 2)

    def render_ping():
        """Blits the server latency to the screen."""
        if GameInfo.ping == -1:
            message = "DISCONNECTED"
            ping_colour = Colour.YELLOW
        else:
            message = f"{GameInfo.ping} ms"
            ping_colour = Colour.CYAN
        ping_surface = FONT.nimbus_sans.render(message, True, ping_colour.value)
        padding = 2  # space between the text and the screen edge, px
        x_pos = SCREEN_DIMS[0] - ping_surface.get_width() - padding
        SCREEN.blit(ping_surface, (x_pos, padding))

    for elem in visible_elems:
        elem.draw(SCREEN)
    render_fps()
    render_ping()
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

        # Ping the server
        backend.session.send_message("PING")

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

# Set the current info label text and render it while the program is exitting.
render(
    [
        lbl_current_info.assert_properties(
            label="Disconnecting from server...", font_colour=Colour.WHITE
        )
    ]
)

# Clean up event loop and close HTTP session
event_loop.run_until_complete(backend.close())
event_loop.close()
