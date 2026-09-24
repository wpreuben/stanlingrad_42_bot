"""Typed actions accepted by the foundation engine."""

from dataclasses import dataclass

from .errors import InvalidActionError
from .types import Side


@dataclass(frozen=True)
class EndPhaseAction:
    side: Side


def serialize_action(action: EndPhaseAction) -> dict[str, object]:
    if not isinstance(action, EndPhaseAction) or not isinstance(action.side, Side):
        raise InvalidActionError("unknown action")
    return {"schema_version": 1, "type": "end_phase", "side": action.side.value}


def deserialize_action(data: dict) -> EndPhaseAction:
    if (type(data) is not dict or set(data) != {"schema_version", "type", "side"}
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["type"] != "end_phase"):
        raise InvalidActionError("invalid action data")
    try:
        return EndPhaseAction(Side(data["side"]))
    except (TypeError, ValueError) as exc:
        raise InvalidActionError("invalid action side") from exc
