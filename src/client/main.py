"""The entry point for the client-side application."""

import asyncio
import pygame
import websockets

from modules import Colour, Font, GameStage, SCREEN_DIMS, event_loop, backend
from modules.gui import BaseElement, Button, Menu, TextInput, Dropdown

pygame.init()
pygame.key.set_repeat(500, 30)
FONT = Font(pygame.font.SysFont)
BaseElement.DEFAULT_FONT = FONT.nimbus_sans

SCREEN = pygame.display.set_mode(SCREEN_DIMS)

CLOCK = pygame.time.Clock()
FRAMERATE = 30  # FPS

game_stage: GameStage = GameStage.CONNECT_TO_SERVER


dropdown = Dropdown(
    "Select server",
    (0.5, 3 / 14),
    icon_font=FONT.reemkufiregular,
    options=["Remote server", "Locally-hosted server"],
)
txtbox = TextInput(
    "Server URL",
    "E.g. localhost:8000",
    (0.5, 5 / 14),
    FONT.consolas,
    FONT.nimbus_sans_sm,
)
btn_test_connection = Button("Test connection", (0.5, 7 / 14))
btn_confirm = Button("Confirm settings", (0.5, 9 / 14))


@btn_test_connection.on_mouse_down
async def make_test_connection():
    success = await backend.test_connection("https://localhost:8000")
    print("Connection success:", success)


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

    match game_stage:
        case GameStage.CONNECT_TO_SERVER:
            render_server_connector()

    pygame.display.update()


def run_once(loop: asyncio.AbstractEventLoop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


def connect_to_server():
    pass


connect_to_server()

try:
    while game_stage != GameStage.ABORTED:
        run_once(event_loop)
        CLOCK.tick(FRAMERATE)

        # Handle Pygame events
        events = pygame.event.get()
        for event in events:
            match event.type:
                case pygame.QUIT:
                    game_stage = GameStage.ABORTED
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
event_loop.create_task(backend.session.close())
event_loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(event_loop)))
event_loop.close()
