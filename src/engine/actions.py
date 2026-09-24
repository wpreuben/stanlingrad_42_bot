"""Typed actions accepted by the foundation engine."""

from dataclasses import dataclass

from .types import Side


@dataclass(frozen=True)
class EndPhaseAction:
    side: Side
