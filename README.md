# Stalingrad ’42 게임 엔진

영문 규칙서 v2.1(2025년 4월)을 기준으로 게임 규칙을 구현하는 Python 프로젝트입니다. 전략 판단과 AI는 엔진 범위에 포함하지 않습니다.

## 개발 명령

Python 3.11 이상과 `uv`가 필요합니다.

```bash
uv sync --locked
uv run --locked python -m unittest discover -s tests -t . -v
```

현재 구현된 부분은 불변 게임 상태, 판본별 자료 검증, §3 페이즈 순서, 명시적인 미구현 규칙 오류, 재현 가능한 주사위, 상태·행동 JSON입니다. 새 게임의 난수 시드는 `new_game("fall_blau", seed=428193)`처럼 지정할 수 있습니다. Map A 전체 지형·헥스변 자료와 S1 시작 유닛 자료는 전사 중입니다. 기본 `new_game("fall_blau")`는 자료가 완성될 때까지 `CatalogError`를 발생시킵니다.

상태 JSON은 스키마 v2이며 카운터의 피해 단계와 준비/사용 면을 별도로 저장합니다. 행동과 정적 자료 JSON은 스키마 v1입니다. S1 카운터 단계 수의 임시 판독은 [검수 기록](docs/s1_step_face_review.md)에 있습니다.
S1 카운터 병과의 임시 분류는 [병과 검수표](docs/s1_unit_type_review.md)에 있으며, 기호 전수 검수 전에는 실행용 자료에 포함하지 않습니다.

설계와 남은 작업은 [설계 명세](docs/superpowers/specs/2026-09-24-stalingrad42-engine-foundation-design.md)와 [구현 계획](docs/superpowers/plans/2026-09-24-stalingrad42-engine-foundation.md)에 기록했습니다. 자료 확인 사항은 [규칙·자료 확인 사항](docs/rule_issues.md)을 참고하세요.
추가된 2019년 playbook의 규칙·기호 대조 결과는 [playbook 검수 기록](docs/playbook_source_review.md)에 있습니다.
