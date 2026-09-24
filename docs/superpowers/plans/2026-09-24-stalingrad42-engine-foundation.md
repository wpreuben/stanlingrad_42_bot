# Stalingrad ’42 게임 엔진 기반 구현 계획

> **구현 담당자:** 작업별로 이 계획의 체크박스를 진행한다. 실행 방식에 따라 `superpowers:subagent-driven-development` 또는 `superpowers:executing-plans` 스킬을 사용한다.

**목표:** 플레이 가능한 Map A 전체와 Fall Blau(S1) 시작 상태를 읽어들이는 결정론적 게임 엔진의 기반을 만든다. 아직 구현하지 않은 규칙은 명확하게 거부한다.

**구조:** 판본이 고정된 JSON 자료에 지도·유닛·시나리오의 변하지 않는 사실을 보관하고, 불변 `GameState`에는 게임 중 바뀌는 정보만 둔다. 엔진 API는 행동을 검증하고, 지원되는 범위에서 룰북 §3의 페이즈를 진행하며, 시드가 있는 주사위와 사건을 기록한다. 이후 계획은 이 계약을 유지하면서 이동·전투·보급·고급 규칙과 S1~S4의 완전한 플레이를 추가한다.

**기술 선택:** Python 3.11 이상, 패키지 관리는 `uv`. `pyproject.toml`에 설치 가능한 `src/engine` 패키지를 정의하고 `uv.lock`을 커밋한다. `.venv/`는 Git에서 제외한다. 표준 라이브러리의 `dataclasses`, `enum`, `json`, `hashlib`, `unittest`를 사용하며 실행 의존성은 추가하지 않는다. 테스트와 개발 명령은 `uv run --locked`로 실행한다.

**설계 명세:** `docs/superpowers/specs/2026-09-24-stalingrad42-engine-foundation-design.md`

## 공통 제약

- 규칙 판정의 기준은 `Stal42_RULES-2025-Final_LoRes.pdf` 영문 v2.1(2025년 4월)이다. 2019년 구성품 이미지는 이 판본과 충돌하면 보조 자료로만 사용한다.
- 규칙 개념에는 가능한 한 `data/glossary.csv`의 `term_id`를 쓴다. 한글·영문 표시 문자열로 규칙을 분기하지 않는다.
- AI 평가, 탐색, 전략 판단, UI는 엔진에 넣지 않는다.
- 이 계획의 S1 초기화는 S1을 끝까지 플레이할 수 있다는 뜻이 아니다. 필수 규칙이 아직 없으면 `UnsupportedRuleError`를 발생시키며 건너뛰거나 아무 효과 없는 행동으로 처리하지 않는다.
- 출처 판독이나 규칙 해석이 불확실하면 `docs/rule_issues.md`에 `TODO_RULE_REVIEW`로 기록한다. 미해결 자료에 의존하는 초기화는 거부한다.
- Little Saturn/Winter Storm 확장판은 포함하지 않는다.
- 현재 공유 작업 폴더의 `.git`은 비어 있고 쓰기 제한이 있다. 구현할 때는 `git@github.com:wpreuben/stanlingrad_42_bot.git`의 별도 복제본 또는 worktree에서 작업한다. 필요한 프로젝트 원본을 해당 작업 공간으로 옮기되 `*:Zone.Identifier` 파일은 제외한다.

## 검토 시 특히 확인할 사례

1. 손상됐거나 미래 버전인 상태 JSON은 일부만 복원하지 않고 즉시 실패해야 한다. → 작업 7의 테스트.
2. 한쪽에만 기록된 헥스 연결이나 Map A 밖을 가리키는 연결은 자료 검증에서 실패해야 한다. → 작업 2·3의 테스트.
3. 시작 배치가 존재하지 않는 유닛 또는 헥스를 가리키면 S1 초기화가 실패해야 한다. → 작업 4의 테스트.
4. 필수 규칙이 미구현인 페이즈를 종료하려 하면 원본 상태를 바꾸지 않고 `UnsupportedRuleError`가 발생해야 한다. → 작업 5의 테스트.
5. 주사위를 한 번 굴린 뒤 저장·복원해도 다음 주사위와 사건 기록이 중단 없이 진행한 경우와 같아야 한다. → 작업 6·7의 테스트.

## 파일별 책임

| 파일 | 책임 |
|---|---|
| `pyproject.toml`, `uv.lock`, `.gitignore` | Python 패키지 정의, 재현 가능한 의존성 잠금, 로컬 가상 환경 제외 |
| `src/engine/types.py` | 불변 게임 상태, enum, 결과·사건 타입 |
| `src/engine/errors.py` | 불법 행동·자료·저장 형식·미구현 규칙의 오류 타입 |
| `src/engine/catalog.py` | 불변 지도·유닛·시나리오 정의, 판본별 자료 로더, 참조와 그래프 검증 |
| `src/engine/phase.py` | 룰북 §3의 순수 페이즈·턴 전이 함수 |
| `src/engine/rng.py` | 시드 기반 6면체 주사위와 사건 기록 |
| `src/engine/actions.py` | 행동 타입과 행동 JSON 변환 |
| `src/engine/engine.py` | `Engine` 메서드와 공개 API 함수 |
| `src/engine/codec.py` | 정규화된 상태 JSON, 검증된 복원, 규칙 상태 해시 |
| `data/engine/v2025_04/map_a.json` | Map A의 모든 플레이 가능 헥스, 여섯 방향 인접 관계, 지형·헥스변 정보 |
| `data/engine/v2025_04/units_s1.json` | S1 시작 시 사용하는 카운터의 정의·면별 수치·고정 ID |
| `data/engine/v2025_04/fall_blau.json` | S1 시작 배치, 마커, 적용 범위, 출처 |
| `data/engine/v2025_04/sources.json` | 전사한 자료의 파일명·판본·이미지 영역 |
| `docs/rule_issues.md` | 판독 불가 항목과 자료 충돌 기록 |
| `tests/engine/test_*.py` | 규칙 번호, 자료 무결성, 저장·복원, 실패 상황 테스트 |

JSON 자료를 지도·카운터·시나리오별로 분리한다. 검토자가 한 자료 묶음의 문제를 다른 묶음과 독립적으로 판단할 수 있어야 한다. 각 자료 객체의 `source_ref`에는 원본 파일과 인쇄된 규칙 번호, 카드 제목 또는 이미지 영역을 기록한다.

---

### Task 1: 작업 1 — 게임 상태와 오류 계약

**파일:** `pyproject.toml`, `uv.lock`, `.gitignore`, `src/engine/__init__.py`, `src/engine/types.py`, `src/engine/errors.py`, `tests/__init__.py`, `tests/engine/__init__.py`, `tests/engine/test_state.py` 생성.

**인터페이스:** `Side`, `Phase`, `UnitState`, `RngState`, `Event`, `GameState`, `GameResult`를 제공한다. 오류 타입은 `CatalogError`, `InvalidActionError`, `UnsupportedRuleError`, `StateFormatError`다. 뒤 작업에서는 이 이름을 그대로 사용한다.

- [ ] **1단계: 불변성 테스트를 먼저 작성한다.**

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

- [ ] **2단계: `uv` 프로젝트를 설정하고 실패하는 테스트를 확인한다.** `src/engine/__init__.py`와 두 테스트 패키지의 `__init__.py`를 빈 파일로 만든다. 아래 설정을 `pyproject.toml`에 기록하고 `.gitignore`에 `.venv/`, `__pycache__/`, `dist/`를 추가한다. `uv lock`으로 `uv.lock`을 생성하고 `uv sync --locked`를 실행한다. 이후 `uv run --locked python -m unittest tests.engine.test_state -v`를 실행한다. `engine.types`가 없어 실패해야 한다.

```toml
[project]
name = "stalingrad42-engine"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.12,<0.13"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "engine"
```
- [ ] **3단계: 타입을 구현한다.** `Phase` 값은 용어집의 `weather_phase`, `initial_phase`, `movement_phase`, `combat_phase`, `recovery_phase`, `supply_phase`, `victory_determination_phase`를 사용한다. `Side` 값은 `axis`, `soviet`, `none`이다. 입력 매핑을 복사해 읽기 전용으로 만드는 부분이 핵심이다.

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

`errors.py`에는 인터페이스에 적은 네 오류 클래스를 `ValueError`의 하위 클래스로 둔다. 이 단계에서 설계 명세의 동적 상태 영역을 모두 정의한다. 후속 규칙은 필요한 값 타입을 구체화한다.

- [ ] **4단계:** 테스트를 다시 실행하고 `UnitState` 필드 변경도 금지되는지 검사한다. 파일의 모든 테스트가 통과해야 한다.
- [ ] **5단계:** `src/engine/`, `tests/engine/test_state.py`를 `feat: define immutable engine state contract`로 커밋한다.

### Task 2: 작업 2 — 규칙 자료 로더와 참조 검증

**파일:** `src/engine/catalog.py`, `tests/engine/test_catalog.py`, `data/engine/v2025_04/sources.json` 생성.

**인터페이스:** `load_catalog(root: Path) -> Catalog`, `validate_catalog(catalog: Catalog) -> None`. `Catalog`는 `ruleset_id`, `hexes`, `units`, `scenarios`를 제공한다. `HexDef`에는 `id`, `terrain`, `neighbors`, `features`, `edge_features`, `source_ref`가 있다. `UnitDef`에는 `id`, `side`, `term_id`, `printed_label`, `faces`, `source_ref`가 있다. `ScenarioDef`에는 `id`, `map_ids`, `start_turn`, `start_phase`, `start_side`, `end_turn`, `placements`가 있다.

- [ ] **1단계: 작은 JSON 임시 자료로 실패 테스트를 작성한다.** `a`의 동쪽이 `b`라면 `b`의 서쪽이 `a`여야 한다. 역방향이 빠진 자료와 `source_ref`가 빠진 자료는 `CatalogError`가 나야 한다.

```python
def test_nonreciprocal_neighbor_rejected(self):
    catalog = Catalog("v2025_04", {
        "a": HexDef("a", "clear", {"e": "b"}, (), {}, "fixture:a"),
        "b": HexDef("b", "clear", {}, (), {}, "fixture:b"),
    }, {}, {})
    with self.assertRaises(CatalogError):
        validate_catalog(catalog)
```

- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_catalog -v`를 실행한다. import 실패가 예상된다.
- [ ] **3단계: 엄격한 로더와 검증기를 구현한다.** 불변 데이터 클래스 `HexDef(id: str, terrain: str, neighbors: Mapping[str, str], features: tuple[str, ...], edge_features: Mapping[str, tuple[str, ...]], source_ref: str)`, `UnitFace(steps: int, attack: int | None, defense: int | None, movement: int | None, abilities: tuple[str, ...])`, `UnitDef(id: str, side: Side, term_id: str, printed_label: str, faces: tuple[UnitFace, ...], source_ref: str)`, `Placement(unit_id: str, location: str, steps: int, source_ref: str)`, `ScenarioDef(id: str, map_ids: tuple[str, ...], start_turn: int, start_phase: Phase, start_side: Side, end_turn: int, placements: tuple[Placement, ...])`, `Catalog(ruleset_id: str, hexes: Mapping[str, HexDef], units: Mapping[str, UnitDef], scenarios: Mapping[str, ScenarioDef])`를 만든다. 각 매핑은 복사해 읽기 전용으로 보관한다. 전투 수치가 없는 비전투 유닛은 선택적 숫자 필드를 사용하고 특수 능력은 인쇄 기호 대신 ID로 기록한다. JSON 중복 키를 거부하는 `object_pairs_hook`을 사용한다. `schema_version == 1`, `ruleset_id == "v2025_04"`, 비어 있지 않은 `source_ref`를 요구한다. 지형 ID의 시작 집합은 `clear`, `desert`, `rough`, `woods`, `wooded_rough`, `mountain`, `minor_city`, `major_city`, `marsh`, `seasonal_marsh`다. 추가 ID는 제공된 TEC/지도에 실제로 있을 때만 출처와 함께 정의한다. 유효하지 않은 자료는 `Catalog`를 반환하기 전에 거부한다.

```python
OPPOSITE = {"e": "w", "se": "nw", "sw": "ne",
            "w": "e", "nw": "se", "ne": "sw"}
for h in catalog.hexes.values():
    for direction, neighbor_id in h.neighbors.items():
        neighbor = catalog.hexes.get(neighbor_id)
        if neighbor is None or neighbor.neighbors.get(OPPOSITE[direction]) != h.id:
            raise CatalogError(f"nonreciprocal edge {h.id}:{direction}->{neighbor_id}")
```

- [ ] **4단계:** 지도 밖 인접 헥스, JSON 중복 키, 모르는 용어 ID, 없는 배치 유닛 ID의 실패 테스트를 추가한다. `data/glossary.csv`는 `encoding="utf-8-sig"`로 읽고 표시어가 아닌 `term_id`를 보존한다. 테스트 파일 전체가 통과해야 한다.
- [ ] **5단계:** `sources.json`에 스키마·룰셋 ID와 다음 실제 파일 경로를 기록한다: 로컬 영문 규칙서; `Stal42_Map_west-FINAL-150 Q12.jpg`(Map A); `Images/httpssteamusercontentaakamaihdnetugc17884688380553658153FC9D37838E1E7AE747007396036D0CAE7AF8A0C.jpg`(추축군 시작 배치); `Images/httpssteamusercontentaakamaihdnetugc1788468838055329033A93814D55EA6FBC4805AE36AD0C6339D5A88391A.jpg`(소련군 시작 배치).
- [ ] **6단계:** 자료 로더, 출처 목록, 테스트를 `feat: validate versioned game reference data`로 커밋한다.

### Task 3: 작업 3 — Map A의 전체 헥스 그래프와 지형 자료

**파일:** `data/engine/v2025_04/map_a.json`, `tests/engine/test_map_a.py`, `docs/rule_issues.md` 생성.

**인터페이스:** `load_catalog`에 Map A의 모든 플레이 가능 헥스를 제공한다. 작업 2의 방향·지형 ID를 사용한다. 각 헥스 JSON에는 `id`, `terrain`, `neighbors`, `features`, `edge_features`, `source_ref`가 있다. `features`는 헥스의 속성, `edge_features`는 방향별 도로·철도·강·교량·나루터·통행 불가 속성이다.

- [ ] **1단계: 전체 자료가 필요한 실패 테스트를 만든다.** 실제 자료를 읽어 S1에서 쓰는 `1300`, `1600`, `3806`, `4100`, `4111`의 존재를 확인한다. 모든 헥스변 속성이 이웃의 반대쪽에도 같은 값으로 기록됐는지 검사한다. 이웃이 없는 해안·지도 끝은 허용하지만, 이웃 없이 연결 도로가 있다고 적힌 자료는 거부한다.
- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_map_a -v`를 실행한다. `map_a.json`이 없어서 실패해야 한다.
- [ ] **3단계: 지도 원본에서 Map A의 인쇄된 헥스 ID와 여섯 방향 이웃을 전사한다.** 새로 제공된 `Stal42_Map_west-FINAL-150 Q12.jpg`(3300×5100) 원본을 사용한다. 인쇄된 플레이 가능 헥스마다 JSON 객체 하나를 작성한다. 각 이미지 행을 끝낼 때 ID, 여섯 변, 가장자리 부분 헥스의 플레이 가능 여부를 원본과 확인한다. 네 자리 숫자만 계산해서 이웃을 추정하지 않는다. 이미지 영역마다 전체 그래프 검증을 실행하고, 모든 영역의 전사가 끝나야 이 작업을 커밋한다.

```json
{"id":"fixture-a","terrain":"clear","neighbors":{"e":"fixture-b"},"features":[],"edge_features":{},"source_ref":"fixture:a"}
```

위 줄은 **실제 지도 자료가 아닌**, 두 헥스 테스트용 레코드의 형태다. Map A 레코드에는 인쇄된 헥스 ID와 눈으로 확인한 모든 연결을 넣는다. `source_ref`는 이미지 위치를 찾기 위한 값이며 검수 완료 표시가 아니다.

- [ ] **4단계: 헥스 지형과 헥스변 속성을 옮긴다.** 대·소하천, 도로·철도 교차, 교량, 통행 불가 경계, 도시, 승리 점수, 진입 경계를 포함한다. 2019년 TEC 이미지 `Images/httpssteamusercontentaakamaihdnetugc1788468838055324885C6C8FFAB6D5B1E880B63E27895D8291F069A9C64.jpg`는 기호 판독에만 사용하고 실제 효과는 이후 2025년 규칙으로 구현한다. 판독이 어려운 항목은 `docs/rule_issues.md`에 `TODO_RULE_REVIEW`로 적고 확정 전에는 자료 검증을 통과시키지 않는다.
- [ ] **5단계:** 이미지 영역을 완료할 때마다, 마지막에는 전체에 대해 `uv run --locked python -m unittest tests.engine.test_map_a tests.engine.test_catalog -v`를 실행한다. 원본 그림의 각 영역을 다시 보고 JSON의 헥스 행과 대조한다. 검토한 영역과 개수는 `sources.json`에 기록한다.
- [ ] **6단계:** 완성된 Map A 자료, 영역별 대조 기록, 테스트, 규칙 쟁점 기록을 `data: transcribe and validate Map A`로 커밋한다.

### Task 4: 작업 4 — Fall Blau 유닛 정의와 시작 배치

**파일:** `data/engine/v2025_04/units_s1.json`, `data/engine/v2025_04/fall_blau.json`, `tests/engine/test_fall_blau_data.py` 생성.

**인터페이스:** `Catalog.scenarios["fall_blau"]`는 S1.1~S1.2에 따라 Map A만 사용하고, 1턴에 시작하여 8턴에 종료하며, 추축군 초기 페이즈에서 시작한다. 양측 시작 카드에 있는 Map A 시작 유닛 전체를 읽는다. `ScenarioDef.placements`에는 `unit_id`, `location`, `steps`, `source_ref`가 있다.

- [ ] **1단계: 실패 테스트를 작성한다.** `axis-2a-hq`가 `1300`에서 시작하는지, `1600`에 소련군 시작 배치가 있는지 확인한다. `fall_blau`의 시작 턴·진영·페이즈, 마지막 턴, 사용 지도도 검사한다. `missing-unit` 또는 `9999`를 배치한 자료는 `CatalogError`가 나야 한다.
- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_fall_blau_data -v`를 실행한다. 자료가 없어서 실패해야 한다.
- [ ] **3단계: 양측 시작 카드와 카운터를 전사한다.** 추축군 카드는 `Images/httpssteamusercontentaakamaihdnetugc17884688380553658153FC9D37838E1E7AE747007396036D0CAE7AF8A0C.jpg`, 소련군 카드는 `Images/httpssteamusercontentaakamaihdnetugc1788468838055329033A93814D55EA6FBC4805AE36AD0C6339D5A88391A.jpg`다. S1 Map A 또는 S1.1~S1.2의 배치 구역에 해당하는 유닛만 포함한다. 물리적 카운터마다 안정적인 ID를 주고 인쇄된 이름은 별도 필드로 둔다. 감소 면, 마커, 수용 상자·진입 구역은 억지로 지도 헥스에 놓지 않고 위치 종류를 기록한다. `Images/`의 카운터 앞뒷면으로 포함된 유닛의 면별 수치를 확인한다.

```json
{"id":"fixture-infantry","side":"axis","term_id":"infantry","printed_label":"T","faces":[{"steps":1,"attack":3,"defense":5,"movement":3,"abilities":[]}],"source_ref":"fixture:counter"}
```

위 줄은 테스트용 가상 유닛이다. 실제 유닛에는 카운터에 인쇄된 값을 사용한다. 실제 `axis-2a-hq` 배치는 카운터 면을 검증한 뒤 `{"unit_id":"axis-2a-hq","location":"1300","steps":1,"source_ref":"axis-at-start:1300"}`로 기록한다.

- [ ] **4단계:** S1.2의 시작 제약을 시나리오 자료로 기록한다. 1턴 추축군 전투 유닛의 전술 이동 제한, §20.6에 따른 소련군 이동 제한, 14Pz·22PzG·60PzG가 1턴에 이동·공격하지 못하는 조건을 `rule:S1.2` 출처로 둔다. 실제 행동 제한 적용은 해당 규칙 구현 단계에서 한다.
- [ ] **5단계:** 자료 테스트와 전체 고유 ID·참조 검증을 실행한다. 시작 카드의 괄호로 묶인 여러 유닛·배치 위치를 이미지와 대조하고, Map A 밖이라 제외해야 할 유닛도 확인한다. 정체가 불분명한 카운터는 `docs/rule_issues.md`에 기록하며 해결 전에는 영향을 받는 시나리오 자료를 통과시키지 않는다.
- [ ] **6단계:** 자료 파일과 테스트를 `data: encode Fall Blau initial position`으로 커밋한다.

### Task 5: 작업 5 — 룰북 §3 페이즈 그래프와 행동 차단

**파일:** `src/engine/phase.py`, `src/engine/actions.py`, `src/engine/engine.py`, `tests/engine/test_phase.py`, `tests/engine/test_actions.py` 생성.

**인터페이스:** `next_phase(turn: int, phase: Phase, side: Side) -> tuple[int, Phase, Side]`, `EndPhaseAction(side: Side)`, `Engine(catalog: Catalog).new_game(scenario_id: str) -> GameState`, `get_legal_actions(state: GameState) -> list[EndPhaseAction]`, `apply_action(state: GameState, action: EndPhaseAction) -> GameState`.

- [ ] **1단계: §3 순서의 실패 테스트를 작성한다.** 날씨 → 추축군 초기·이동·전투·회복·보급 → 소련군 초기·이동·전투·회복·보급 → 승리 판정 → 다음 턴 날씨를 확인한다. S1이 곧바로 추축군 초기 페이즈에서 시작하는지, 추축군 페이즈에 소련군의 `EndPhaseAction`이 불법인지 확인한다.
- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_phase tests.engine.test_actions -v`를 실행한다. import 실패가 예상된다.
- [ ] **3단계: 순수 페이즈 전이 함수와 S1 초기화 함수를 구현한다.** `new_game("fall_blau")`는 배치 상태를 읽되 아직 없는 규칙은 실행하지 않는다. S1은 1~8턴이므로 §3·§23에 따라 초기 날씨를 `clear_weather`로 설정한다. 모르는 시나리오 ID는 `CatalogError`다.

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

- [ ] **4단계: 공개 행동을 제한한다.** S1의 추축군 초기 페이즈와 아직 필수 규칙이 없는 모든 페이즈에서 `get_legal_actions`, `apply_action`은 `UnsupportedRuleError`를 발생시킨다. 테스트 전용으로 만든 1~16턴 날씨 페이즈 상태에서만 맑은 날씨의 결정론적 `EndPhaseAction(Side.NONE)`을 허용한다. `pending_decision`이 있으면 종료를 허용하지 않는다. 잘못된 진영의 행동은 전이 전에 거부한다. `apply_action`은 `dataclasses.replace`로 새 상태를 만들고 `Event("phase_ended", ...)`를 추가하며 입력 상태는 보존한다.
- [ ] **5단계:** S1 초기 페이즈를 건너뛸 수 없음, 알 수 없는 행동 태그의 역직렬화 실패, 잘못된 진영의 행동 실패, 대기 중인 결정이 페이즈 종료를 막음에 대한 테스트를 추가한다. 두 테스트 파일이 모두 통과해야 한다.
- [ ] **6단계:** 페이즈·행동 코드와 테스트를 `feat: model rulebook phase sequence and guarded actions`로 커밋한다.

### Task 6: 작업 6 — 시드 기반 주사위와 구조화 사건

**파일:** `src/engine/rng.py`, `tests/engine/test_rng.py` 생성.

**인터페이스:** `roll_d6(state: RngState, reason: str) -> tuple[int, RngState, Event]`. 순수 함수이며 규칙을 호출하는 쪽에서 주사위 소비 시점을 결정한다.

- [ ] **1단계: 실패 테스트를 작성한다.** 같은 `(seed, draw_count, reason)`에서 같은 주사위와 사건이 나오는지, 연속 호출에서 `draw_count`가 증가하는지, 값이 항상 1~6인지 확인한다. `reason`을 바꿔도 주사위 숫자는 같아야 한다. `reason`은 기록 정보이지 난수 입력이 아니다.
- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_rng -v`를 실행한다. import 실패가 예상된다.
- [ ] **3단계: 버전별로 결과가 일정한 바이트 인코딩과 거부 표본 추출을 구현한다.** Python의 프로세스마다 달라질 수 있는 `hash()`나 전역 난수는 사용하지 않는다. `f"st42-v1:{seed}:{draw_count}:{attempt}".encode("ascii")`의 SHA-256 첫 바이트가 252보다 작을 때만 `(byte % 6) + 1`을 반환한다. 새 상태는 `RngState(seed, draw_count + 1)`, 사건은 `Event("die_roll", (("reason", reason), ("value", str(value))))`다.
- [ ] **4단계:** 시드 `428193`, 0~9번째 추출의 고정 기대값 `[3, 3, 6, 1, 2, 3, 4, 1, 6, 4]`를 테스트한다. 새 프로세스에서 다시 실행해도 같아야 한다. RNG 테스트를 두 번 실행한다.
- [ ] **5단계:** RNG 코드와 테스트를 `feat: make die rolls reproducible across processes`로 커밋한다.

### Task 7: 작업 7 — 판본이 있는 상태·행동 저장 형식

**파일:** `src/engine/codec.py`, `src/engine/actions.py` 수정, `tests/engine/test_codec.py` 생성.

**인터페이스:** `serialize_state(state: GameState) -> dict`, `deserialize_state(data: dict, catalog: Catalog) -> GameState`, `hash_state(state: GameState) -> str`, `serialize_action(action: EndPhaseAction) -> dict`, `deserialize_action(data: dict) -> EndPhaseAction`.

- [ ] **1단계: 실패 테스트를 작성한다.** 상태·행동의 저장 후 복원, JSON 키 순서의 안정성, 사건 기록만 다를 때 같은 상태 해시, 유닛 위치 또는 RNG `draw_count`가 다를 때 다른 해시를 확인한다. 미래 스키마 판본, 모르는 유닛 ID, 빠진 `ruleset_id`, 손상된 RNG 카운터는 `StateFormatError`가 나야 한다.
- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_codec -v`를 실행한다. import 실패가 예상된다.
- [ ] **3단계: 명시적인 인코더를 작성한다.** enum·불변 데이터 클래스·매핑을 JSON 값으로 바꾼다. `schema_version: 1`을 기록하고 유닛·마커·통제·보급·자원·증원·승리 점수·비공개 상태의 키를 정렬한다. 대기 중인 결정과 RNG 시드·카운터를 포함해 모든 동적 필드를 저장한다. `MappingProxyType`에 `dataclasses.asdict`를 바로 사용하지 않는다. 행동 JSON의 형태는 `{"schema_version":1,"type":"end_phase","side":"axis"}`다.
- [ ] **4단계: 복원 시 엄격히 검사한다.** 모르는 키, 누락 필드, 잘못된 enum 값, 정수 자리에 들어온 bool, 모르는 유닛 참조, 중복 유닛 ID, 카탈로그와 다른 `ruleset_id`를 거부한다. 모든 검사 후 완전한 `GameState`를 생성한다. 상태 해시는 `events`만 제외한 정규 JSON으로 계산한다. RNG 상태는 이후 결과에 영향을 주므로 해시에 포함한다.
- [ ] **5단계: 저장 후 재개 사례를 추가한다.** 한 번 굴리고 저장·복원한 다음 양쪽 상태에서 두 번째 주사위와 사건이 같은지 검사한다. `uv run --locked python -m unittest tests.engine.test_codec tests.engine.test_rng -v`가 통과해야 한다.
- [ ] **6단계:** 저장 형식과 테스트를 `feat: save restore and hash engine states`로 커밋한다.

### Task 8: 작업 8 — 공개 API와 기반 단계 인수 검사

**파일:** `src/engine/__init__.py`, `src/engine/engine.py` 수정, `tests/engine/test_foundation_acceptance.py` 생성, `docs/rule_issues.md` 갱신.

**인터페이스:** `new_game`, `get_legal_actions`, `apply_action`, `is_terminal`, `get_result`, `serialize_state`, `deserialize_state`를 내보낸다. 격리된 테스트에는 `Engine(catalog)`를 제공한다. 공개 함수는 기본 `v2025_04` 카탈로그를 읽는다. 기반 단계에서 실제로 도달 가능한 상태의 `is_terminal`은 `False`, `get_result`는 `GameResult.ONGOING`이다.

- [ ] **1단계: 실패하는 인수 테스트를 작성한다.** 실제 S1 자료를 읽어 1턴·추축군 초기 페이즈·Map A 시작 배치를 확인한다. 초기 페이즈 규칙이 이 계획에서 미구현이므로 `get_legal_actions`가 `UnsupportedRuleError`를 내야 한다. 상태·행동 JSON을 저장·복원하고, 테스트용 맑은 날씨 상태에서는 페이즈가 전이되면서 원본이 바뀌지 않는지 확인한다.
- [ ] **2단계:** `uv run --locked python -m unittest tests.engine.test_foundation_acceptance -v`를 실행한다. 공개 함수가 없어 실패해야 한다.
- [ ] **3단계:** `__init__.py`에 정확한 공개 함수를 내보내고 얇은 위임 함수를 만든다. `Engine`은 검증된 불변 카탈로그만 소유하고 변경 중인 게임 상태는 소유하지 않는다. `new_game`은 반환 전에 자료를 검증한다. 공개 함수는 기본 자료에서 읽기 전용 `Engine`을 구성할 수 있으나 현재 게임을 전역 변수에 보관하지 않는다.
- [ ] **4단계:** `uv run --locked python -m unittest discover -s tests -t . -v`로 전체 테스트를 실행한다. `TODO_RULE_REVIEW` 항목이 S1 초기화 자료와 관계있다면 해결 전에는 인수 검사를 실패시킨다. S1을 한 턴 끝까지 플레이할 수 있다고 주장하는 테스트가 없는지도 확인한다.
- [ ] **5단계:** 공개 함수, 인수 테스트, 쟁점 기록을 `feat: expose validated S1 engine foundation`으로 커밋한다.

## 자체 검토와 구현 전 확인

- 명세와 작업 1~8을 대조한다. 상태·행동 계약, 자료 출처, Map A, S1 시작 상태, 페이즈, RNG, JSON, 미구현 규칙 오류, 테스트 모두 담당 작업이 있어야 한다.
- 뒤 작업이 사용하는 파일·함수·타입이 앞 작업에 정의돼 있는지 확인한다. 미완성 표시, 모호한 단계, 정의되지 않은 메서드 이름을 찾아 수정한다.
- 이 계획은 사용자가 내용을 검토하고 승인한 뒤에만 실행한다. 이후 규칙 단위마다 별도 설계와 계획이 필요하다. S1 전체 플레이는 보급·승리조건 단위 완료 후, S4 전체 플레이는 캠페인 단위 완료 후 달성한다.
