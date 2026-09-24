"""Portable, reproducible six-sided die rolls."""

import hashlib

from .types import Event, RngState


def roll_d6(state: RngState, reason: str) -> tuple[int, RngState, Event]:
    """Consume one die draw; rejection sampling avoids modulo bias."""
    if type(state.seed) is not int or type(state.draw_count) is not int or state.draw_count < 0:
        raise ValueError("invalid RNG state")
    if not isinstance(reason, str) or not reason:
        raise ValueError("die roll requires a reason")
    attempt = 0
    while True:
        payload = f"st42-v1:{state.seed}:{state.draw_count}:{attempt}".encode("ascii")
        sample = hashlib.sha256(payload).digest()[0]
        if sample < 252:
            value = sample % 6 + 1
            break
        attempt += 1
    next_state = RngState(state.seed, state.draw_count + 1)
    event = Event("die_roll", (("reason", reason), ("value", str(value))))
    return value, next_state, event
