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
FRAMERATE = 30  # FPS

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

    def render_fps():
        """Blit the current FPS to the screen."""
        fps = min(CLOCK.get_fps(), FRAMERATE)
        message = f"{fps:.1f} FPS"
        fps_percentage = fps / FRAMERATE
        amount_green = round(fps_percentage * 255)
        fps_colour = (255 - amount_green, amount_green, 0)
        fps_surface = FONT.nimbus_sans.render(message, True, fps_colour)
        SCREEN.blit(fps_surface, (0, 0))

    render_fps()
    pygame.display.update()


def run_once(loop):
    """Executes one task in the event loop's coroutine stack."""
    loop.call_soon(loop.stop)
    loop.run_forever()


while running:
    run_once(event_loop)
    CLOCK.tick(FRAMERATE)

    # Handle Pygame events
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
                break
    render()

event_loop.close()
