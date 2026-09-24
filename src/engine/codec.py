"""Versioned JSON values and deterministic hashes for game states."""

import hashlib
import json
from typing import Any

from .catalog import Catalog, validate_catalog
from .errors import StateFormatError
from .types import Event, GameState, Phase, RngState, Side, UnitState


SCHEMA_VERSION = 1
STATE_KEYS = frozenset({
    "schema_version", "ruleset_id", "scenario_id", "turn", "phase", "active_side",
    "weather", "units", "markers", "rng", "pending_decision", "events", "control",
    "supply", "resources", "reinforcements", "victory_points", "private_state",
})


def serialize_state(state: GameState) -> dict[str, Any]:
    """Convert a state into stable, JSON-compatible values."""
    return {
        "schema_version": SCHEMA_VERSION,
        "ruleset_id": state.ruleset_id,
        "scenario_id": state.scenario_id,
        "turn": state.turn,
        "phase": state.phase.value,
        "active_side": state.active_side.value,
        "weather": state.weather,
        "units": {key: {"unit_id": unit.unit_id, "location": unit.location,
                         "steps": unit.steps, "statuses": list(unit.statuses)}
                  for key, unit in sorted(state.units.items())},
        "markers": dict(sorted(state.markers.items())),
        "rng": {"seed": state.rng.seed, "draw_count": state.rng.draw_count},
        "pending_decision": state.pending_decision,
        "events": [{"kind": event.kind, "params": [list(pair) for pair in event.params]}
                   for event in state.events],
        "control": dict(sorted(state.control.items())),
        "supply": dict(sorted(state.supply.items())),
        "resources": dict(sorted(state.resources.items())),
        "reinforcements": {key: list(value) for key, value in sorted(state.reinforcements.items())},
        "victory_points": dict(sorted(state.victory_points.items())),
        "private_state": dict(sorted(state.private_state.items())),
    }


def _object(value: object, keys: frozenset[str], label: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise StateFormatError(f"invalid {label} fields")
    return value


def _string(value: object, label: str) -> str:
    if type(value) is not str:
        raise StateFormatError(f"invalid {label}")
    return value


def _integer(value: object, label: str, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise StateFormatError(f"invalid {label}")
    return value


def _string_map(value: object, label: str) -> dict[str, str]:
    if type(value) is not dict:
        raise StateFormatError(f"invalid {label}")
    return {_string(k, label): _string(v, label) for k, v in value.items()}


def _integer_map(value: object, label: str) -> dict[str, int]:
    if type(value) is not dict:
        raise StateFormatError(f"invalid {label}")
    return {_string(k, label): _integer(v, label) for k, v in value.items()}


def deserialize_state(data: dict, catalog: Catalog) -> GameState:
    """Validate the whole saved value before constructing a GameState."""
    data = _object(data, STATE_KEYS, "state")
    if _integer(data["schema_version"], "schema_version") != SCHEMA_VERSION:
        raise StateFormatError("unsupported state schema")
    validate_catalog(catalog)
    if _string(data["ruleset_id"], "ruleset_id") != catalog.ruleset_id:
        raise StateFormatError("ruleset mismatch")
    scenario_id = _string(data["scenario_id"], "scenario_id")
    if scenario_id not in catalog.scenarios:
        raise StateFormatError(f"unknown scenario: {scenario_id}")
    turn = _integer(data["turn"], "turn", 1)
    try:
        phase = Phase(_string(data["phase"], "phase"))
        side = Side(_string(data["active_side"], "active_side"))
    except ValueError as exc:
        raise StateFormatError("invalid phase or side") from exc
    weather = _string(data["weather"], "weather")
    if type(data["units"]) is not dict:
        raise StateFormatError("invalid units")
    units = {}
    seen_ids = set()
    for key, raw in data["units"].items():
        _string(key, "unit key")
        raw = _object(raw, frozenset({"unit_id", "location", "steps", "statuses"}), "unit")
        unit_id = _string(raw["unit_id"], "unit_id")
        if unit_id != key or unit_id in seen_ids or unit_id not in catalog.units:
            raise StateFormatError(f"unknown or duplicate unit: {unit_id}")
        seen_ids.add(unit_id)
        location = _string(raw["location"], "unit location")
        if location not in catalog.hexes and not location.startswith("zone:"):
            raise StateFormatError(f"unknown unit location: {location}")
        steps = _integer(raw["steps"], "unit steps", 1)
        if steps not in {face.steps for face in catalog.units[unit_id].faces}:
            raise StateFormatError(f"invalid unit steps: {unit_id}")
        if type(raw["statuses"]) is not list:
            raise StateFormatError("invalid unit statuses")
        statuses = tuple(_string(x, "unit status") for x in raw["statuses"])
        units[key] = UnitState(unit_id, location, steps, statuses)
    markers = _string_map(data["markers"], "markers")
    raw_rng = _object(data["rng"], frozenset({"seed", "draw_count"}), "rng")
    rng = RngState(_integer(raw_rng["seed"], "rng seed"),
                   _integer(raw_rng["draw_count"], "rng draw_count", 0))
    pending = data["pending_decision"]
    if pending is not None:
        pending = _string(pending, "pending_decision")
    if type(data["events"]) is not list:
        raise StateFormatError("invalid events")
    events = []
    for raw in data["events"]:
        raw = _object(raw, frozenset({"kind", "params"}), "event")
        if type(raw["params"]) is not list:
            raise StateFormatError("invalid event params")
        pairs = []
        for pair in raw["params"]:
            if type(pair) is not list or len(pair) != 2:
                raise StateFormatError("invalid event parameter")
            pairs.append((_string(pair[0], "event key"), _string(pair[1], "event value")))
        events.append(Event(_string(raw["kind"], "event kind"), tuple(pairs)))
    control = _string_map(data["control"], "control")
    supply = _string_map(data["supply"], "supply")
    if set(control) - catalog.hexes.keys():
        raise StateFormatError("unknown control hex")
    if set(supply) - catalog.units.keys():
        raise StateFormatError("unknown supply unit")
    resources = _integer_map(data["resources"], "resources")
    if type(data["reinforcements"]) is not dict:
        raise StateFormatError("invalid reinforcements")
    reinforcements = {}
    for key, value in data["reinforcements"].items():
        if type(value) is not list:
            raise StateFormatError("invalid reinforcement list")
        reinforcements[_string(key, "reinforcement key")] = tuple(
            _string(item, "reinforcement unit") for item in value)
        if set(reinforcements[key]) - catalog.units.keys():
            raise StateFormatError("unknown reinforcement unit")
    victory_points = _integer_map(data["victory_points"], "victory_points")
    private_state = _string_map(data["private_state"], "private_state")
    return GameState(catalog.ruleset_id, scenario_id, turn, phase, side, weather,
                     units, markers, rng, pending, tuple(events), control, supply,
                     resources, reinforcements, victory_points, private_state)


def hash_state(state: GameState) -> str:
    """Hash all future-relevant state, excluding the descriptive event log."""
    data = serialize_state(state)
    del data["events"]
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
