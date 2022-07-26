"""The entry point for the client-side application."""

import asyncio
import pygame
import websockets

from modules import Colour, Font

pygame.init()
FONT = Font(pygame.font.SysFont)

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

CLOCK = pygame.time.Clock()


running = True
try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


def render():
    """Rerenders the game window."""
    # Fill with white
    SCREEN.fill(Colour.NEAR_BLACK.value)
    # Blit the current FPS to the screen
    fps = CLOCK.get_fps()
    message = f"{fps:.1f} FPS"
    fps_surface = FONT.nimbus_sans.render(message, True, Colour.WHITE.value)
    SCREEN.blit(fps_surface, (0, 0))

    pygame.display.update()


def run_once(loop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


while running:
    run_once(event_loop)
    CLOCK.tick(30)  # FPS

    # Handle Pygame events
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
                break
    render()

event_loop.close()
