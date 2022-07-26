"""The entry point for the client-side application."""

import asyncio
import pygame
import websockets

from modules import Colour, Font, GameStage, SCREEN_DIMS
from modules.gui import Button, Menu

pygame.init()
FONT = Font(pygame.font.SysFont)

SCREEN = pygame.display.set_mode(SCREEN_DIMS)

CLOCK = pygame.time.Clock()
FRAMERATE = 30  # FPS

game_stage: GameStage = GameStage.CONNECT_TO_SERVER

try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


btn = Button("First button", FONT.nimbus_sans, (0.5, 0.5))
btn2 = Button("Second button", FONT.nimbus_sans, (0.5, 5 / 8))


def render():
    """Rerenders the game window."""
    # Fill with white
    SCREEN.fill(Colour.DARK0.value)

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
        for button in Menu.buttons:
            button.draw(SCREEN)

    render_fps()

    match game_stage:
        case GameStage.CONNECT_TO_SERVER:
            render_server_connector()

    pygame.display.update()


def run_once(loop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


def connect_to_server():
    pass


connect_to_server()

while game_stage != GameStage.ABORTED:
    run_once(event_loop)
    CLOCK.tick(FRAMERATE)

    # Handle Pygame events
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                game_stage = GameStage.ABORTED
    mouse_pos = pygame.mouse.get_pos()
    # Determine which buttons were pressed
    clicked = pygame.mouse.get_pressed(num_buttons=3)
    for button in Menu.buttons:
        button.check_click(mouse_pos, clicked)
    render()

event_loop.close()
