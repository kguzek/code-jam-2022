"""The entry point for the client-side application."""

import asyncio
import json
from time import time
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
from modules.util import debug

pygame.init()
pygame.key.set_repeat(500, 30)
FONT = Font(pygame.font.SysFont, pygame.font.Font)
BaseElement.DEFAULT_FONT = FONT.nimbus_sans

SCREEN = pygame.display.set_mode(SCREEN_DIMS)
pygame.display.set_caption("Tic-tac-toe")

CLOCK = pygame.time.Clock()


# REGION Register menu elements
lbl_room_info = Label("Open rooms: 0", (0.5, 1 / 224), menu=Menu.settings)
lbl_player_sign = Label("[SIGN]", (0.5, 2 / 28), font=FONT.nimbus_sans_sm)
btn_join_room = Button("Join room", (0.5, 11 / 28), disabled=True, menu=Menu.settings)
btn_create_room = Button("Create room", (0.5, 17 / 28), menu=Menu.settings)
btn_retry_connection = Button("Retry connnection", (0.5, 9 / 14))
btn_disconnect = Button("Disconnect", (0.5, 9 / 14))
lbl_current_info = Label("Connecting to server...", (0.5, 0.5))
dropdown_room = Dropdown(
    "Select room",
    (0.5, 2 / 7),
    icon_font=FONT.reemkufiregular,
    menu=Menu.settings,
)
# ENDREGION

# REGION Register element events
@btn_join_room.on_mouse("down")
def join_room():
    backend.session.send_message(
        {"type": "join_room", "room_id": dropdown_room.selected_option}
    )
    lbl_current_info.label = "Connecting to room..."
    GameInfo.current_stage = GameStage.LOADING


@btn_create_room.on_mouse("down")
def create_room():
    """Sends a message to the server instructing it to create a new room, and transfer the client
    to it."""
    backend.session.send_message({"type": "create_room"})


@btn_disconnect.on_mouse("down")
def disconnect_from_room():
    backend.session.send_message({"type": "leave_room"})
    btn_disconnect.toggle_disabled_state()
    GameInfo.current_stage = GameStage.JOIN_ROOM
    if not btn_join_room.disabled:
        btn_join_room.toggle_disabled_state()
    GameInfo.connected_room = None
    GameInfo.player_sign = None


# ENDREGION

# REGION Register websocket events
@backend.session.on_server_message
def on_server_message(data: str | bytes) -> None:
    if isinstance(data, bytes):
        data: str = bytes.decode()
    try:
        parsed = json.loads(data)
    except (TypeError, json.decoder.JSONDecodeError):
        debug("Invalid server message:", data)
        return
    else:
        data: dict = parsed
    data_type = data.get("type")
    if data_type != "log":
        debug(f"CLIENT: Received message '{data}'")
    match data_type:
        case "create_room" | "join_room":
            room_id = data.get("room_id")
            lbl_room_info.label = f"Connected to room #{room_id}"
            sign = data.get("sign")
            GameInfo.current_stage = (
                GameStage.GAME_IN_PROGRESS
                if data_type == "join_room"
                else GameStage.WAITING_FOR_PLAYER
            )
            GameInfo.player_sign = sign
            lbl_player_sign.label = f"Your sign: {sign}"
            GameInfo.connected_room = room_id
            if btn_disconnect.disabled:
                btn_disconnect.toggle_disabled_state()
        case "leave_room":
            pass
        case "start_game":
            GameInfo.current_stage = GameStage.GAME_IN_PROGRESS
        case "player_disconnected":
            GameInfo.current_stage = GameStage.WAITING_FOR_PLAYER
            pass
        case "update_open_rooms":
            open_rooms = data.get("open_rooms")
            options = tuple((room, f"Room {room}") for room in open_rooms)
            dropdown_room.set_options(options)
            if GameInfo.current_stage == GameStage.JOIN_ROOM:
                lbl_room_info.label = f"Open rooms: {len(open_rooms)}"
        case "playercount":
            GameInfo.playercount = data.get("playercount")
        case "log":
            debug("SERVER:", data.get("body"))
        case _:
            debug("Received unknown server message:", data)


@btn_retry_connection.on_mouse("down")
def connect_to_server() -> None:
    """Instructs the program to start a thread to create the websocket connection."""
    btn_retry_connection.toggle_disabled_state()

    backend.connect_to_websocket(
        GameInfo.WEBSOCKET_URL, btn_retry_connection.toggle_disabled_state
    )


@dropdown_room.on_selection_change
def select_room() -> None:
    if btn_join_room.disabled or dropdown_room.selected_option is None:
        btn_join_room.toggle_disabled_state()


# ENDREGION


def tick():
    """Performs logic on the game window. Returns a tuple containing a list of all visible elements
    and a boolean indicating if the left mouse button was clicked this frame."""
    mouse_pos = pygame.mouse.get_pos()
    # Determine which buttons were pressed
    mouse_btns = pygame.mouse.get_pressed(num_buttons=3)
    # Determine which buttons were pressed this frame
    new_mouse_btns = (False,) * 3 if currently_clicked else mouse_btns

    # Determine which UI elements to display
    match GameInfo.current_stage:
        case GameStage.JOIN_ROOM:
            visible_elems = [
                lbl_current_info.assert_properties(label="or", font_colour=Colour.WHITE)
            ] + Menu.settings
        case GameStage.WAITING_FOR_PLAYER:
            visible_elems = [
                lbl_room_info,
                btn_disconnect,
                lbl_player_sign,
                lbl_current_info.assert_properties(
                    label="Waiting for opponent...", font_colour=Colour.WHITE
                ),
            ]
        case GameStage.GAME_IN_PROGRESS:
            visible_elems = [lbl_room_info, btn_disconnect, lbl_player_sign]
        case GameStage.WEBSOCKET_ERROR:
            visible_elems = [
                lbl_current_info.assert_properties(
                    label=Message.SERVER_ERROR, font_colour=Colour.RED
                ),
                btn_retry_connection,
            ]
        case GameStage.LOADING:
            visible_elems = [
                lbl_current_info.assert_properties(font_colour=Colour.WHITE)
            ]
        case _:
            visible_elems = []
    # Add the child elems of all dropdown elements
    option_elems = []
    for elem in visible_elems:
        if isinstance(elem, Dropdown) and elem.selected:
            option_elems += elem.option_elems
    visible_elems += option_elems
    # Loop reversed list since last-most elements are rendered at the top of the screen
    for elem in visible_elems[::-1]:
        if elem.check_click(mouse_pos, new_mouse_btns):
            # Don't check other elements in case of overlap
            mouse_pos = (-1, -1)
    return visible_elems, mouse_btns[0]


def render(visible_elems: Sequence[BaseElement]):
    """Rerenders the game window."""
    # Fill with white
    SCREEN.fill(Colour.GREY2.value)

    padding = 2  # space between the text and the screen edge, px

    # Blit the current FPS to the screen
    fps = min(CLOCK.get_fps(), FRAMERATE)
    message = f"{fps:.1f} FPS"
    fps_percentage = fps / FRAMERATE
    amount_green = round(fps_percentage * 255)
    fps_colour = (255 - amount_green, amount_green, 0)
    fps_surface = FONT.nimbus_sans.render(message, True, fps_colour)
    SCREEN.blit(fps_surface, (padding,) * 2)

    # Blit the playercount to the screen
    # message = f"Connected players: {GameInfo.playercount}"
    # players_surface = FONT.nimbus_sans.render(message, True, Colour.GREY7.value)
    # x_pos = SCREEN_DIMS[0] - players_surface.get_width() - padding
    # SCREEN.blit(players_surface, (x_pos, padding))

    # Blit the server latency to the screen
    if GameInfo.ping == -1:
        message = "DISCONNECTED"
        ping_colour = Colour.YELLOW
    else:
        message = f"{GameInfo.ping} ms"
        ping_colour = Colour.CYAN
    ping_surface = FONT.nimbus_sans.render(message, True, ping_colour.value)
    # x_pos -= ping_surface.get_width() + 7
    x_pos = SCREEN_DIMS[0] - ping_surface.get_width() - padding
    SCREEN.blit(ping_surface, (x_pos, padding))

    for elem in visible_elems:
        elem.draw(SCREEN)
    pygame.display.update()


def run_once(loop: asyncio.AbstractEventLoop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


# Connect to the websocket
connect_to_server()

# Boolean to keep track of mouse click events
currently_clicked = False

# Main game loop
try:
    while GameInfo.current_stage != GameStage.ABORTED:
        run_once(event_loop)
        CLOCK.tick(FRAMERATE)

        # Ping the server
        if backend.session.connected and time() - GameInfo.last_ping_check > 0.25:
            GameInfo.last_ping_check = time()
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
        visible_elems, currently_clicked = tick()
        render(visible_elems)
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
