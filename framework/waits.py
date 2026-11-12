"""Polling helper: wait for a condition instead of sleeping for a fixed time."""

from __future__ import annotations

import time
from collections.abc import Callable


def wait_until[T](
    condition: Callable[[], T],
    *,
    timeout: float,
    interval: float = 1.0,
    description: str = "condition",
) -> T:
    """Call `condition` until it returns a truthy value. Return that value.

    Raise TimeoutError if the condition is still false after `timeout` seconds.
    The check stops as soon as the condition is true, so a fast system is not
    slowed down, and a slow one gets enough time.
    """
    deadline = time.monotonic() + timeout
    while True:
        result = condition()
        if result:
            return result
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Waited {timeout:.0f}s, but {description} is still false")
        time.sleep(interval)
