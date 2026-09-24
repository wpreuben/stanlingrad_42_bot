"""Public API for the Stalingrad '42 rules engine foundation."""

from pathlib import Path

from .actions import EndPhaseAction, deserialize_action, serialize_action
from .catalog import load_catalog
from .codec import deserialize_state as _deserialize_state
from .codec import hash_state, serialize_state
from .engine import Engine
from .types import GameResult, GameState


_DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "engine" / "v2025_04"


def _default_engine() -> Engine:
    return Engine(load_catalog(_DATA_ROOT))


def new_game(scenario_id: str, seed: int = 0) -> GameState:
    return _default_engine().new_game(scenario_id, seed=seed)


def get_legal_actions(state: GameState) -> list[EndPhaseAction]:
    return _default_engine().get_legal_actions(state)


def apply_action(state: GameState, action: EndPhaseAction) -> GameState:
    return _default_engine().apply_action(state, action)


def is_terminal(state: GameState) -> bool:
    return False


def get_result(state: GameState) -> GameResult:
    return GameResult.ONGOING


def deserialize_state(data: dict) -> GameState:
    return _deserialize_state(data, _default_engine().catalog)


__all__ = ["new_game", "get_legal_actions", "apply_action", "is_terminal",
           "get_result", "serialize_state", "deserialize_state", "hash_state",
           "serialize_action", "deserialize_action", "Engine", "EndPhaseAction"]
