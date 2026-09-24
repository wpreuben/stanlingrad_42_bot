# Stalingrad ’42 게임 엔진

영문 규칙서 v2.1(2025년 4월)을 기준으로 게임 규칙을 구현하는 Python 프로젝트입니다. 전략 판단과 AI는 엔진 범위에 포함하지 않습니다.

## 개발 명령

Python 3.11 이상과 `uv`가 필요합니다.

```bash
uv sync --locked
uv run --locked python -m unittest discover -s tests -t . -v
```

현재 구현된 부분은 불변 게임 상태, 판본별 자료 검증, §3 페이즈 순서, 명시적인 미구현 규칙 오류, 재현 가능한 주사위, 상태·행동 JSON입니다. 새 게임의 난수 시드는 `new_game("fall_blau", seed=428193)`처럼 지정할 수 있습니다. Map A 전체 지형·헥스변 자료와 S1 시작 유닛 자료는 전사 중입니다. 기본 `new_game("fall_blau")`는 자료가 완성될 때까지 `CatalogError`를 발생시킵니다.

설계와 남은 작업은 [설계 명세](docs/superpowers/specs/2026-09-24-stalingrad42-engine-foundation-design.md)와 [구현 계획](docs/superpowers/plans/2026-09-24-stalingrad42-engine-foundation.md)에 기록했습니다. 자료 확인 사항은 [규칙·자료 확인 사항](docs/rule_issues.md)을 참고하세요.
