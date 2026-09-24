# Stalingrad ’42 Engine Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, serializable rules-engine foundation that loads the complete playable Map A and the Fall Blau (S1) starting position while explicitly refusing rules that are not implemented yet.

**Architecture:** Versioned JSON reference data describes the map, units, and scenario; immutable game state contains only changing facts. A small engine API validates actions, advances the §3 phase graph where supported, and records seeded dice and events. Later plans add movement, combat, logistics, advanced rules, and full S1–S4 play without replacing these contracts.

**Tech Stack:** Python 3.11 or newer, standard library (`dataclasses`, `enum`, `json`, `hashlib`, `unittest`); no runtime dependency.

**Spec:** `docs/superpowers/specs/2026-09-24-stalingrad42-engine-foundation-design.md`

## Global Constraints

- Rules source: `Stal42_RULES-2025-Final_LoRes.pdf`, v2.1, April 2025. The 2019 component images are secondary evidence where they disagree with this rules version.
- Preserve confirmed IDs from `data/glossary.csv` where they name rules concepts; compare IDs in logic, never Korean or English display text.
- Keep AI evaluation, search, strategy, and UI outside the engine.
- S1 initialization in this plan is not a claim of full playability. Unsupported mandatory rules raise `UnsupportedRuleError`; they are never skipped or treated as no-ops.
- Record uncertain source readings in `docs/rule_issues.md` with `TODO_RULE_REVIEW`; reject data depending on unresolved readings.
- Do not import the Little Saturn/Winter Storm expansion.
- The shared source directory has an empty, read-only `.git` placeholder. Execute implementation in an isolated clone or worktree of `git@github.com:wpreuben/stanlingrad_42_bot.git`; copy approved project inputs into it before the relevant task. Do not copy `*:Zone.Identifier` files.

## Review Focus

1. A corrupt or future state schema must fail on load before any partial state is returned — Task 7 tests this.
2. A map edge present on only one hex, or an edge pointing outside Map A, must fail catalog validation — Tasks 2 and 3 test this.
3. A setup card entry with a missing unit or hex ID must fail S1 initialization — Task 4 tests this.
4. An end-phase request while a mandatory rule is unavailable must raise `UnsupportedRuleError` without changing state — Task 5 tests this.
5. Saving after one die roll and resuming must produce the same next roll and event as uninterrupted play — Tasks 6 and 7 test this.

## File Map

| Path | Responsibility |
|---|---|
| `src/engine/types.py` | Frozen dynamic state, enums, result and event types. |
| `src/engine/errors.py` | Stable error categories for invalid actions, data, state format, unsupported rules. |
| `src/engine/catalog.py` | Immutable definitions, versioned data loader, reference and graph validation. |
| `src/engine/phase.py` | Pure §3 phase and turn successor function. |
| `src/engine/rng.py` | Version-stable seeded d6 sequence and roll events. |
| `src/engine/actions.py` | Tagged action types and action JSON codec. |
| `src/engine/engine.py` | `Engine` methods and thin public API functions. |
| `src/engine/codec.py` | Canonical state JSON, validated restore, rule-state hash. |
| `data/engine/v2025_04/map_a.json` | Every playable Map A hex, explicit six-direction neighbors, terrain and hexside features. |
| `data/engine/v2025_04/units_s1.json` | Counter definitions used by S1 at start; counter faces and stable IDs. |
| `data/engine/v2025_04/fall_blau.json` | S1 starting positions, markers, scope, source references. |
| `data/engine/v2025_04/sources.json` | Filenames, edition, and image regions for each transcribed data set. |
| `docs/rule_issues.md` | Source ambiguity and conflict log. |
| `tests/engine/test_*.py` | Rule-number tests, data integrity, round-trip and failure tests. |

The JSON files are deliberately separate: a reviewer can reject the map, counter inventory, or scenario setup without rejecting their neighbors. Every data object records its `source_ref` as a path and printed rule, card title, or image region.

---

### Task 1: State and error contract

**Files:** Create `src/engine/__init__.py`, `src/engine/types.py`, `src/engine/errors.py`, `tests/engine/test_state.py`.

**Interfaces:** Produces `Side`, `Phase`, `UnitState`, `RngState`, `Event`, `GameState`, `GameResult`; produces `CatalogError`, `InvalidActionError`, `UnsupportedRuleError`, `StateFormatError`. Later tasks import these exact names.

- [ ] **Step 1: Write the failing immutability test.**

```python
# tests/engine/test_state.py
import unittest
from engine.types import GameState, Phase, RngState, Side, UnitState

class StateTests(unittest.TestCase):
    def test_external_unit_mapping_change_does_not_change_state(self):
        units = {"axis-2a-hq": UnitState("axis-2a-hq", "1300", 1, ())}
        state = GameState("v2025_04", "fall_blau", 1, Phase.INITIAL,
                          Side.AXIS, "clear_weather", units, {}, RngState(7, 0), None, ())
        units.clear()
        self.assertIn("axis-2a-hq", state.units)
        with self.assertRaises(TypeError):
            state.units["axis-2a-hq"] = UnitState("axis-2a-hq", "1301", 1, ())
```

- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_state -v`; expect `ModuleNotFoundError` for `engine.types`.
- [ ] **Step 3: Implement the types.** `Phase` values are `weather`, `initial`, `movement`, `combat`, `recovery`, `supply`, `victory`; `Side` values are `axis`, `soviet`, `none`. Make all state members frozen. The mapping copy is essential:

```python
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

    def __post_init__(self):
        for name in ("units", "markers", "control", "supply", "resources",
                     "reinforcements", "victory_points", "private_state"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

class GameResult(str, Enum):
    ONGOING = "ongoing"
    AXIS_VICTORY = "axis_victory"
    SOVIET_VICTORY = "soviet_victory"
```

`errors.py` contains four `class Name(ValueError): pass` declarations using the names in the interface block. The first task defines every dynamic state area required by the spec; later rules refine the values without moving them outside `GameState`.

- [ ] **Step 4: Re-run** the test and add a frozen `UnitState` mutation assertion; expect all tests in this file to pass.
- [ ] **Step 5: Commit** `src/engine/` and `tests/engine/test_state.py` with message `feat: define immutable engine state contract`.

### Task 2: Catalog loader and reference validation

**Files:** Create `src/engine/catalog.py`, `tests/engine/test_catalog.py`, `data/engine/v2025_04/sources.json`.

**Interfaces:** `load_catalog(root: Path) -> Catalog`; `validate_catalog(catalog: Catalog) -> None`. `Catalog` exposes `ruleset_id`, `hexes`, `units`, `scenarios`. Each `HexDef` exposes `id`, `terrain`, `neighbors`, `features`, `source_ref`; each `UnitDef` exposes `id`, `side`, `term_id`, `faces`, `source_ref`; each `ScenarioDef` exposes `id`, `map_ids`, `start_turn`, `start_phase`, `start_side`, `end_turn`, `placements`.

- [ ] **Step 1: Write tests** using `tempfile.TemporaryDirectory` with three small JSON files. One fixture has `1300` east of `1400` and `1400` west of `1300`; the negative fixture removes the reciprocal west edge and must raise `CatalogError`. Add a missing `source_ref` case.

```python
def test_nonreciprocal_neighbor_rejected(self):
    catalog = Catalog("v2025_04", {
        "a": HexDef("a", "clear", {"e": "b"}, (), {}, "fixture:a"),
        "b": HexDef("b", "clear", {}, (), {}, "fixture:b"),
    }, {}, {})
    with self.assertRaises(CatalogError):
        validate_catalog(catalog)
```

- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_catalog -v`; expect import failure.
- [ ] **Step 3: Implement strict loading and validation.** Define `HexDef(id: str, terrain: str, neighbors: Mapping[str, str], features: tuple[str, ...], edge_features: Mapping[str, tuple[str, ...]], source_ref: str)`, `UnitFace(steps: int, attack: int | None, defense: int | None, movement: int | None, abilities: tuple[str, ...])`, `UnitDef(id: str, side: Side, term_id: str, printed_label: str, faces: tuple[UnitFace, ...], source_ref: str)`, `Placement(unit_id: str, location: str, steps: int, source_ref: str)`, `ScenarioDef(id: str, map_ids: tuple[str, ...], start_turn: int, start_phase: Phase, start_side: Side, end_turn: int, placements: tuple[Placement, ...])`, and `Catalog(ruleset_id: str, hexes: Mapping[str, HexDef], units: Mapping[str, UnitDef], scenarios: Mapping[str, ScenarioDef])`. Use frozen dataclasses and copy mappings into read-only views. Optional numeric face fields cover non-combat counters; encode their special abilities as IDs rather than printed symbols. Load JSON with `object_pairs_hook` that rejects duplicate keys; require exact `schema_version == 1`, `ruleset_id == "v2025_04"`, nonempty `source_ref`; reject unknown terrain IDs. Start the fixed allowed terrain set with `clear`, `desert`, `rough`, `woods`, `wooded_rough`, `mountain`, `minor_city`, `major_city`, `marsh`, `seasonal_marsh`; add a term only when it appears on the supplied TEC/map and record its source. Use direction opposites `{e:w, se:nw, sw:ne, w:e, nw:se, ne:sw}`. A neighbor must exist and point back through the opposite direction. Every unit and placement reference must be unique and point to an existing definition. Reject invalid data before constructing `Catalog`.

```python
OPPOSITE = {"e": "w", "se": "nw", "sw": "ne",
            "w": "e", "nw": "se", "ne": "sw"}
for h in catalog.hexes.values():
    for direction, neighbor_id in h.neighbors.items():
        neighbor = catalog.hexes.get(neighbor_id)
        if neighbor is None or neighbor.neighbors.get(OPPOSITE[direction]) != h.id:
            raise CatalogError(f"nonreciprocal edge {h.id}:{direction}->{neighbor_id}")
```

- [ ] **Step 4: Add a test for an outside-map neighbor, duplicate JSON key, unknown term ID, and missing setup unit ID; run the file and expect all to pass.** Read `data/glossary.csv` with `encoding="utf-8-sig"`; preserve its `term_id` values rather than display strings.
- [ ] **Step 5: Create `sources.json`** with schema/ruleset IDs and these concrete source paths: local English PDF; `Images/httpssteamusercontentaakamaihdnetugc17884687792252896570A62D23C2FCE91331EED1641567952E124BC8AF7.jpg` (map); `Images/httpssteamusercontentaakamaihdnetugc17884688380553658153FC9D37838E1E7AE747007396036D0CAE7AF8A0C.jpg` (Axis start); `Images/httpssteamusercontentaakamaihdnetugc1788468838055329033A93814D55EA6FBC4805AE36AD0C6339D5A88391A.jpg` (Soviet start).
- [ ] **Step 6: Commit** catalog code, source manifest, and tests as `feat: validate versioned game reference data`.

### Task 3: Complete Map A graph and feature data

**Files:** Create `data/engine/v2025_04/map_a.json`, `tests/engine/test_map_a.py`, `docs/rule_issues.md`.

**Interfaces:** Supplies every playable Map A hex to `load_catalog`; direction labels and feature IDs follow Task 2. A JSON hex has `id`, `terrain`, `neighbors`, `features`, `source_ref`; `features` lists hex properties, while `edge_features` maps each direction to road, railroad, river, bridge, ferry, or impassable IDs.

- [ ] **Step 1: Add a failing test** that loads the full catalog, checks known S1 hexes `1300`, `1600`, `3806`, `4100`, `4111`, and checks that every edge feature has the same value from both neighboring hexes. Include a coast/map-edge case where a missing neighbor is valid but an outgoing feature claiming a road connection is rejected.
- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_map_a -v`; expect missing `map_a.json`.
- [ ] **Step 3: Transcribe the Map A hex list and six neighbors** from the 6519×7186 map source named in Task 2. Store one JSON object per printed playable hex ID. Use `source_ref` values like `map-a:1300`; do not infer a neighbor from the four-digit ID alone. For each source image row, verify printed ID, six sides, and whether a partial edge hex is playable before moving to the next row. Validate the complete graph after each image region and commit only after all regions are covered.

```json
{"id":"fixture-a","terrain":"clear","neighbors":{"e":"fixture-b"},"features":[],"edge_features":{},"source_ref":"fixture:a"}
```

The line above is a complete synthetic two-hex fixture record shape; real Map A records use printed hex IDs and all visible sides. The `source_ref` is a coordinate locator, not evidence that data has been audited.

- [ ] **Step 4: Transcribe terrain and each hexside feature** from the same source image, including major/minor rivers, road/rail crossings, bridges, impassable/coast sides, cities, victory values, and entry boundaries. Use the 2019 TEC image `Images/httpssteamusercontentaakamaihdnetugc1788468838055324885C6C8FFAB6D5B1E880B63E27895D8291F069A9C64.jpg` only to identify printed symbols; apply 2025 rule effects later. Place ambiguous image readings in `docs/rule_issues.md` with `TODO_RULE_REVIEW` and leave their data unaccepted until resolved against the English rulebook and image.
- [ ] **Step 5: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_map_a tests.engine.test_catalog -v` after each map region and at the end. Visually audit all map regions once more, checking the independent source image against each recorded row; record audited image regions and counts in `sources.json`.
- [ ] **Step 6: Commit** complete Map A data, source-region audit, tests, and any issue entries as `data: transcribe and validate Map A`.

### Task 4: Fall Blau unit definitions and starting position

**Files:** Create `data/engine/v2025_04/units_s1.json`, `data/engine/v2025_04/fall_blau.json`, `tests/engine/test_fall_blau_data.py`.

**Interfaces:** `Catalog.scenarios["fall_blau"]` loads S1.1–S1.2, Map A only, turn 1–8, Axis Initial Phase start, and the complete Map A at-start units from both campaign setup cards. `ScenarioDef.placements` entries carry `unit_id`, `location`, `steps`, and `source_ref`.

- [ ] **Step 1: Write the failing tests.** Check that `axis-2a-hq` begins in `1300`, that a Soviet setup entry exists at `1600`, and that `fall_blau` starts at turn 1, Axis Initial Phase, ends after turn 8, and uses only Map A. A fixture with placement `missing-unit` or `9999` must raise `CatalogError`.
- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_fall_blau_data -v`; expect missing data.
- [ ] **Step 3: Transcribe the Axis start card** from `Images/httpssteamusercontentaakamaihdnetugc17884688380553658153FC9D37838E1E7AE747007396036D0CAE7AF8A0C.jpg`, then the Soviet start card from `Images/httpssteamusercontentaakamaihdnetugc1788468838055329033A93814D55EA6FBC4805AE36AD0C6339D5A88391A.jpg`. Include only units on S1 Map A and setup areas named by S1.1–S1.2. Give every physical counter a stable ID; keep its printed label separately. Record starting reduced faces, markers, and holding/entry locations rather than forcing every piece onto a hex. Use counter-sheet fronts and backs in `Images/` to record each included counter's printed step faces.

```json
{"id":"fixture-infantry","side":"axis","term_id":"infantry","printed_label":"T","faces":[{"steps":1,"attack":3,"defense":5,"movement":3,"abilities":[]}],"source_ref":"fixture:counter"}
```

The line above is a synthetic fixture record. Actual units use counter-sheet values. A real S1 placement of `axis-2a-hq` uses `{"unit_id":"axis-2a-hq","location":"1300","steps":1,"source_ref":"axis-at-start:1300"}` after validating its counter face.

- [ ] **Step 4: Encode S1-specific starting constraints** as scenario facts: Turn 1 Axis combat units' tactical movement limit; frozen Soviet units per §20.6; and the 14Pz, 22Pz, 60PzG restrictions from S1.2. These facts are data now and become enforced actions in later plans. Keep their source reference `rule:S1.2`.
- [ ] **Step 5: Run** the data tests and a catalog-wide uniqueness/reference check. Visually compare each setup-card group against the JSON, including multi-unit bracketed positions and units outside Map A that must be excluded. Record unresolved counter identity in `docs/rule_issues.md` and reject the affected scenario data until resolved.
- [ ] **Step 6: Commit** the two data files and tests as `data: encode Fall Blau initial position`.

### Task 5: §3 phase graph and guarded actions

**Files:** Create `src/engine/phase.py`, `src/engine/actions.py`, `src/engine/engine.py`, `tests/engine/test_phase.py`, `tests/engine/test_actions.py`.

**Interfaces:** `next_phase(turn: int, phase: Phase, side: Side) -> tuple[int, Phase, Side]`; `EndPhaseAction(side: Side)`; `Engine(catalog: Catalog).new_game(scenario_id: str) -> GameState`; `get_legal_actions(state: GameState) -> list[EndPhaseAction]`; `apply_action(state: GameState, action: EndPhaseAction) -> GameState`.

- [ ] **Step 1: Write failing §3 tests** for the exact sequence: weather → Axis initial → movement → combat → recovery → supply → Soviet initial → movement → combat → recovery → supply → victory → next turn weather. Check S1 starts directly at Axis initial and that `EndPhaseAction(Side.SOVIET)` during Axis phase is invalid.
- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_phase tests.engine.test_actions -v`; expect import failure.
- [ ] **Step 3: Implement the pure phase successor and S1 initializer.** `new_game("fall_blau")` loads placement states without executing missing rules; initial weather is `clear_weather` because S1 uses turns 1–8 (§3, §23). Unrecognized scenario IDs raise `CatalogError`.

```python
ORDER = (Phase.INITIAL, Phase.MOVEMENT, Phase.COMBAT,
         Phase.RECOVERY, Phase.SUPPLY)
if phase is Phase.WEATHER:
    return turn, Phase.INITIAL, Side.AXIS
if phase in ORDER[:-1]:
    return turn, ORDER[ORDER.index(phase) + 1], side
if phase is Phase.SUPPLY and side is Side.AXIS:
    return turn, Phase.INITIAL, Side.SOVIET
if phase is Phase.SUPPLY and side is Side.SOVIET:
    return turn, Phase.VICTORY, Side.NONE
if phase is Phase.VICTORY:
    return turn + 1, Phase.WEATHER, Side.NONE
raise InvalidActionError(f"invalid phase/side: {phase}/{side}")
```

- [ ] **Step 4: Guard public actions.** For S1's Axis Initial Phase and every later phase whose mandatory rules are absent, `get_legal_actions` and `apply_action` raise `UnsupportedRuleError`. For a test-only state at Weather Phase in turns 1–16, allow the deterministic clear-weather `EndPhaseAction(Side.NONE)`; do not allow EndPhase when `pending_decision` is set. Reject wrong-side actions before transition. `apply_action` uses `dataclasses.replace`, appends an `Event("phase_ended", ...)`, and leaves the input state unchanged.
- [ ] **Step 5: Add tests** that S1 Initial cannot be skipped, unknown action tags fail deserialization, wrong-side actions fail, and a pending decision blocks phase end. Run both test files and expect pass.
- [ ] **Step 6: Commit** phase and action code plus tests as `feat: model rulebook phase sequence and guarded actions`.

### Task 6: Seeded d6 and structured events

**Files:** Create `src/engine/rng.py`, `tests/engine/test_rng.py`.

**Interfaces:** `roll_d6(state: RngState, reason: str) -> tuple[int, RngState, Event]`. The function is pure; callers choose when a rule consumes a die.

- [ ] **Step 1: Write a failing test** asserting equal `(seed, draw_count, reason)` produces the same die and event, sequential draws increment `draw_count`, and the result is always 1–6. Check that changing `reason` does not change the die sequence; reason is log metadata, not entropy.
- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_rng -v`; expect import failure.
- [ ] **Step 3: Implement a version-stable byte encoding and rejection sampling** rather than Python's process-dependent `hash()` or a global random generator. Use SHA-256 of `f"st42-v1:{seed}:{draw_count}:{attempt}".encode("ascii")`; consume the first byte only when it is below 252; return `(byte % 6) + 1`, `RngState(seed, draw_count + 1)`, and `Event("die_roll", (("reason", reason), ("value", str(value))))`.
- [ ] **Step 4: Add a fixed golden vector test** for seed `428193`, draws 0–9: `[3, 3, 6, 1, 2, 3, 4, 1, 6, 4]`. Verify after a new process start. Run the RNG tests twice; both runs must match.
- [ ] **Step 5: Commit** RNG and tests as `feat: make die rolls reproducible across processes`.

### Task 7: Versioned state and action serialization

**Files:** Create `src/engine/codec.py`, extend `src/engine/actions.py`, `tests/engine/test_codec.py`.

**Interfaces:** `serialize_state(state: GameState) -> dict`; `deserialize_state(data: dict, catalog: Catalog) -> GameState`; `hash_state(state: GameState) -> str`; `serialize_action(action: EndPhaseAction) -> dict`; `deserialize_action(data: dict) -> EndPhaseAction`.

- [ ] **Step 1: Write failing tests** for state/action round-trip, deterministic JSON key order, hash equality when event history differs, and hash inequality when a unit location or RNG `draw_count` differs. A future schema version, unknown unit ID, absent `ruleset_id`, and malformed RNG counter must raise `StateFormatError`.
- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_codec -v`; expect import failure.
- [ ] **Step 3: Write explicit encoders** for enums, frozen dataclasses and mappings. Emit `schema_version: 1`; sort keys for units, markers, control, supply, resources, reinforcements, victory points, and private state; store every dynamic field, including pending decision and RNG seed/counter. Do not rely on `dataclasses.asdict` for `MappingProxyType`. Encode actions with `{"schema_version":1,"type":"end_phase","side":"axis"}` shape.
- [ ] **Step 4: Decode with strict checks.** Reject unknown keys, absent fields, invalid enum values, bools where integers are required, unknown unit references, duplicate unit IDs, and a `ruleset_id` that differs from the catalog. Construct a complete validated `GameState` only after all checks pass. Compute the state hash from canonical JSON after removing `events` only; keep the RNG state because it affects future outcomes.
- [ ] **Step 5: Add the Review Focus resume test:** roll once, serialize, deserialize, roll again from each resulting RNG state, and compare the second die and event. Run `PYTHONPATH=src python3 -m unittest tests.engine.test_codec tests.engine.test_rng -v` and expect pass.
- [ ] **Step 6: Commit** codecs and tests as `feat: save restore and hash engine states`.

### Task 8: Public API and foundation acceptance

**Files:** Extend `src/engine/__init__.py`, `src/engine/engine.py`, create `tests/engine/test_foundation_acceptance.py`, update `docs/rule_issues.md`.

**Interfaces:** Export `new_game`, `get_legal_actions`, `apply_action`, `is_terminal`, `get_result`, `serialize_state`, `deserialize_state`. Expose `Engine(catalog)` for isolated fixture tests. The public functions load the packaged v2025_04 catalog; `is_terminal` is `False` and `get_result` is `GameResult.ONGOING` for every reachable foundation state.

- [ ] **Step 1: Write the failing acceptance test.** Load the actual S1 data; assert starting turn 1, Axis Initial Phase, Map A placements, and `get_legal_actions` raising `UnsupportedRuleError` because S1 Initial rules are not implemented in this plan. Verify a complete state/action JSON round-trip. Test a synthetic clear-weather phase transition and original-state immutability.
- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.engine.test_foundation_acceptance -v`; expect missing exports.
- [ ] **Step 3: Add the thin public functions** and exact exports in `__init__.py`. `Engine` owns a validated immutable catalog; it does not own mutable game state. `new_game` calls catalog validation before returning. The public functions may construct a read-only default `Engine` from the packaged data; do not store a current game in a global variable.
- [ ] **Step 4: Run the full suite** with `PYTHONPATH=src python3 -m unittest discover -s tests -v`. Check every `TODO_RULE_REVIEW` entry against the accepted data: any unresolved item referenced by S1 initialization fails acceptance. Verify no test claims S1 can complete a full turn.
- [ ] **Step 5: Commit** exports, acceptance tests and issue log as `feat: expose validated S1 engine foundation`.

## Plan Self-Review and Execution Gate

- Check the spec against Tasks 1–8: state and action contracts, data provenance, Map A, S1 setup, phase graph, RNG, JSON, explicit unsupported-rule behavior, and tests each have an owning task.
- Check that every path and interface named by a later task is produced by an earlier task. Search for unfinished markers, vague steps, and dangling method names; revise before execution.
- This plan is complete only after the human reviewer accepts it. Then choose the execution method. A separate spec and plan are needed for each subsequent rules unit; full S1 play is reached after the logistics/victory unit, and S4 after the campaign unit.
