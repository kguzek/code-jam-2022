"""Miscellaneous utility functions."""


from typing import Callable, Coroutine, Iterable

from modules import DEBUG_MODE, event_loop


def call_callbacks(
    callbacks: Callable[[], Coroutine | None] | list[Callable[[], Coroutine | None]]
):
    """
    Calls the callbacks.

    Calls each callback in the list, scheduling any returned coroutines as tasks
    to be awaited in the running game event loop.

    Arguments:
        `callbacks` -- Either a function that returns a `Coroutine` or `None`, or a list of them.
    """
    for callback in callbacks if isinstance(callbacks, Iterable) else (callbacks,):
        coro = callback()
        if not isinstance(coro, Coroutine):
            continue
        event_loop.create_task(coro)


def debug(*message) -> None:
    """Prints the message if `DEBUG_MODE` is set to `True`."""
    if DEBUG_MODE:
        print(*message)
