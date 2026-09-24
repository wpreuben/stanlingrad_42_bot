"""Rule §3 phase and turn sequence."""

from .errors import InvalidActionError
from .types import Phase, Side


ORDER = (Phase.INITIAL, Phase.MOVEMENT, Phase.COMBAT,
         Phase.RECOVERY, Phase.SUPPLY)


def next_phase(turn: int, phase: Phase, side: Side) -> tuple[int, Phase, Side]:
    if type(turn) is not int or turn < 1:
        raise InvalidActionError(f"invalid turn: {turn}")
    if phase is Phase.WEATHER and side is Side.NONE:
        return turn, Phase.INITIAL, Side.AXIS
    if phase in ORDER and side in (Side.AXIS, Side.SOVIET):
        if phase is not Phase.SUPPLY:
            return turn, ORDER[ORDER.index(phase) + 1], side
        if side is Side.AXIS:
            return turn, Phase.INITIAL, Side.SOVIET
        return turn, Phase.VICTORY, Side.NONE
    if phase is Phase.VICTORY and side is Side.NONE:
        return turn + 1, Phase.WEATHER, Side.NONE
    raise InvalidActionError(f"invalid phase/side: {phase}/{side}")
