"""State transitions for the currently supported rules subset."""

from dataclasses import replace

from .actions import EndPhaseAction
from .catalog import Catalog, validate_catalog
from .errors import CatalogError, InvalidActionError, UnsupportedRuleError
from .phase import next_phase
from .types import Event, GameState, Phase, RngState, Side, UnitState


class Engine:
    def __init__(self, catalog: Catalog) -> None:
        validate_catalog(catalog)
        self.catalog = catalog

    def new_game(self, scenario_id: str) -> GameState:
        scenario = self.catalog.scenarios.get(scenario_id)
        if scenario is None:
            raise CatalogError(f"unknown scenario: {scenario_id}")
        validate_catalog(self.catalog)
        units = {p.unit_id: UnitState(p.unit_id, p.location, p.steps, ())
                 for p in scenario.placements}
        return GameState(self.catalog.ruleset_id, scenario.id, scenario.start_turn,
                         scenario.start_phase, scenario.start_side, "clear_weather",
                         units, {}, RngState(0, 0), None, ())

    def get_legal_actions(self, state: GameState) -> list[EndPhaseAction]:
        self._check_state_catalog(state)
        if state.pending_decision is not None:
            return []
        if state.phase is Phase.WEATHER and state.active_side is Side.NONE:
            if 1 <= state.turn <= 16 and state.weather == "clear_weather":
                return [EndPhaseAction(Side.NONE)]
        raise UnsupportedRuleError(f"phase rule not implemented: {state.phase.value}")

    def apply_action(self, state: GameState, action: EndPhaseAction) -> GameState:
        self._check_state_catalog(state)
        if not isinstance(action, EndPhaseAction):
            raise InvalidActionError("unknown action type")
        if action.side is not state.active_side:
            raise InvalidActionError("wrong acting side")
        if state.pending_decision is not None:
            raise InvalidActionError("pending decision must be resolved")
        if action not in self.get_legal_actions(state):
            raise InvalidActionError("action is not legal")
        turn, phase, side = next_phase(state.turn, state.phase, state.active_side)
        event = Event("phase_ended", (("phase", state.phase.value),
                                      ("side", state.active_side.value),
                                      ("turn", str(state.turn))))
        return replace(state, turn=turn, phase=phase, active_side=side,
                       events=state.events + (event,))

    def _check_state_catalog(self, state: GameState) -> None:
        if state.ruleset_id != self.catalog.ruleset_id or state.scenario_id not in self.catalog.scenarios:
            raise CatalogError("state does not match engine catalog")
