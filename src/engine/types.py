"""Value objects for a deterministic Stalingrad '42 game state."""

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class Side(str, Enum):
    AXIS = "axis"
    SOVIET = "soviet"
    NONE = "none"


class Phase(str, Enum):
    WEATHER = "weather_phase"
    INITIAL = "initial_phase"
    MOVEMENT = "movement_phase"
    COMBAT = "combat_phase"
    RECOVERY = "recovery_phase"
    SUPPLY = "supply_phase"
    VICTORY = "victory_determination_phase"


@dataclass(frozen=True)
class UnitState:
    unit_id: str
    location: str
    steps: int
    statuses: tuple[str, ...]


@dataclass(frozen=True)
class RngState:
    seed: int
    draw_count: int


@dataclass(frozen=True)
class Event:
    kind: str
    params: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GameState:
    ruleset_id: str
    scenario_id: str
    turn: int
    phase: Phase
    active_side: Side
    weather: str
    units: Mapping[str, UnitState]
    markers: Mapping[str, str]
    rng: RngState
    pending_decision: str | None
    events: tuple[Event, ...]
    control: Mapping[str, str] = field(default_factory=dict)
    supply: Mapping[str, str] = field(default_factory=dict)
    resources: Mapping[str, int] = field(default_factory=dict)
    reinforcements: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    victory_points: Mapping[str, int] = field(default_factory=dict)
    private_state: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("units", "markers", "control", "supply", "resources",
                     "reinforcements", "victory_points", "private_state"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


class GameResult(str, Enum):
    ONGOING = "ongoing"
    AXIS_VICTORY = "axis_victory"
    SOVIET_VICTORY = "soviet_victory"
