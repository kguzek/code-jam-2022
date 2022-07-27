"""The entry point for the client-side application."""

import asyncio
import aiohttp
import pygame

from modules import backend, SCREEN_DIMS, event_loop, Colour, Font, GameStage, GameInfo
from modules.gui import BaseElement, Button, Menu, TextInput, Dropdown

pygame.init()
pygame.key.set_repeat(500, 30)
FONT = Font(pygame.font.SysFont, pygame.font.Font)
BaseElement.DEFAULT_FONT = FONT.nimbus_sans

SCREEN = pygame.display.set_mode(SCREEN_DIMS)

CLOCK = pygame.time.Clock()
FRAMERATE = 60  # FPS


# REGION Register menu elements
dropdown = Dropdown(
    "Select server",
    (0.5, 3 / 14),
    icon_font=FONT.reemkufiregular,
    options=["Remote server", "Locally-hosted server"],
)
ipt_server_url = TextInput(
    "Server URL",
    "E.g. localhost:8000",
    (0.5, 5 / 14),
    FONT.consolas,
    FONT.nimbus_sans_sm,
    FONT.seguisym,
)
btn_test_connection = Button("Test connection", (0.5, 7 / 14))
btn_confirm = Button("Confirm settings", (0.5, 9 / 14), disabled=True)
# ENDREGION

# REGION Register element events
@btn_test_connection.on_mouse("down")
async def make_test_connection():
    old_label = btn_test_connection.label
    btn_test_connection.label = "Testing..."
    btn_test_connection.toggle_disabled_state()
    ipt_server_url.toggle_disabled_state()
    try:
        success = await backend.test_connection(ipt_server_url.value)
    except aiohttp.InvalidURL:
        ipt_server_url.success = False
        return
    else:
        ipt_server_url.success = success
        if not success:
            return
        GameInfo.last_valid_server = ipt_server_url.value
        if btn_confirm.disabled:
            btn_confirm.toggle_disabled_state()
    finally:
        btn_test_connection.label = old_label
        ipt_server_url.toggle_disabled_state()


@btn_confirm.on_mouse("down")
async def confirm_settings():
    old_label = btn_confirm.label
    btn_confirm.toggle_disabled_state()
    btn_confirm.label = "Connecting to the server..."
    await backend.connect_to_websocket(GameInfo.last_valid_server)
    GameInfo.current_stage = GameStage.GAME_IN_PROGRESS
    btn_confirm.toggle_disabled_state()
    btn_confirm.label = old_label


@ipt_server_url.on_select_change
def handle_value_change():
    if ipt_server_url.selected:
        if btn_test_connection.disabled:
            btn_test_connection.toggle_disabled_state()
        return
    if ipt_server_url.value == GameInfo.last_valid_server:
        return
    GameInfo.last_valid_server = None
    if not btn_confirm.disabled:
        btn_confirm.toggle_disabled_state()


# ENDREGION


def tick():
    """Performs logic on the game window."""

    mouse_pos = pygame.mouse.get_pos()
    # Determine which buttons were pressed
    clicked = pygame.mouse.get_pressed(num_buttons=3)
    for elem in Menu.all_elements:
        elem.check_click(mouse_pos, clicked)


def render():
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

    def render_server_connector():
        for elem in Menu.all_elements:
            elem.draw(SCREEN)

    render_fps()

    match GameInfo.current_stage:
        case GameStage.CONNECT_TO_SERVER:
            render_server_connector()

    pygame.display.update()


def run_once(loop: asyncio.AbstractEventLoop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


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
        tick()
        render()
except KeyboardInterrupt:
    pass

# Clean up event loop and close HTTP session
event_loop.run_until_complete(backend.session.close())
event_loop.close()
