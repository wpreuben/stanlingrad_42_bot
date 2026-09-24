# 작업 재개 메모

이 문서는 작업이 중단됐을 때 다음 세션에서 바로 이어가기 위한 기록이다. 먼저 `git status --short`와 `git log -1 --oneline`을 확인한다.

## 목표와 제약

- 2025년 영문 Stalingrad ’42 v2.1 기본 룰북의 S1–S4 전체를 결정론적 게임 엔진으로 구현한다. Little Saturn/Winter Storm 확장판은 제외한다.
- AI 판단·탐색은 엔진 완성 뒤로 미룬다. §34도 엔진 내부 규칙으로 구현한다.
- 패키지 관리는 `uv`로 한다. 게임 엔진 실행 의존성은 없으며 지도 이미지 보조 도구만 `map-tools` 그룹의 Pillow를 사용한다.
- 설계·진행 문서는 한국어로 작성한다. 사용자가 `git@github.com:wpreuben/stanlingrad_42_bot.git`에 작업 브랜치를 커밋·푸시하도록 승인했다.

## 저장소와 현재 상태

- 작업 위치: `/home/pc/project/Stalingrad42_bot/.worktrees/engine-foundation`, 브랜치 `feat/engine-foundation`.
- 이 작업 위치는 자체 `.git`을 갖는다. 이전 임시 Git 디렉터리가 시스템 재시작으로 삭제된 뒤 원격 브랜치에서 복구했다. 다시 `/tmp`에 Git 관리 디렉터리를 만들지 않는다.
- 게임 엔진의 상태·행동·페이즈·카탈로그 계약과 일부 규칙 보조 함수가 있다. 전체 `map_a.json`, `units_s1.json`, `fall_blau.json`은 아직 없으므로 S1 플레이는 불가능하다. 검수하지 않은 자료를 완성 지도나 초기화 가능 시나리오로 만들지 않는다.
- [지도 전사 기록](map_a_transcription_progress.md)에 확인한 인쇄 ID 1,042개, 지형·변까지 검수한 헥스 80개와 변 178개를 구분해 적었다.
- [이웃 후보](map_a_edge_candidates.csv)는 2,947개 중 178개만 `reviewed`이며 나머지는 단순 기하 후보이다. [강변 검토 대기열](map_a_river_review_queue.csv)은 99픽셀 가로 간격으로 보정한 이미지 신호를 사용한다. 두 파일 모두 실행용 지도 자료가 아니다.
- 사용자 제공 `Stalingrad42_v203/` 조사 결과는 [VASSAL 모듈 자료 조사](vassal_module_inventory.md)에 기록했다. 격자·카운터·시나리오 배치는 구조화되어 있으나 헥스별 지형·변 자료는 확인되지 않았다. Map A 이미지는 기존 `images_high` 파일과 해시가 같다.
- [일괄 판독 시험](map_a_automation_spike.md)에서 단순 색 신호의 한계를 측정했다. 강 28변 중 25개를 오탐 없이 찾았으나 보조도로·철도 신호는 오탐이 많다. 검수된 헥스 80개가 모두 `clear`라 다른 지형의 정확도를 평가할 수 없다. 다음에는 선 연결성 분석과 다양한 지형 표본 검수를 우선한다.
- [변 픽셀 후보](map_a_edge_pixel_candidates.csv)는 `tools.map_edge_pixel_candidates`로 확인된 인쇄 ID 사이의 기하학적 변 2,947개를 일괄 점수화한 자료다. 51×51픽셀 영역의 색 신호가 거의 없고 통과선이 없는 미검수 변 1,116개는 `no_feature_candidate`, 그중 공유 변의 양 끝까지 조용한 972개는 `strong_no_feature_candidate`로 표시된다. 변을 가로질러 양쪽으로 이어지는 선은 `route_crossing_candidate`로 표시된다. 후보 신호는 실행용 지도 속성이 아니다.
- 지형 표본 탐색: 기존 검수 헥스 80개는 전부 `clear`다. VASSAL 지형표와 지도 확대 대조에서 `3905`·`4010`·`2122`·`3805`는 수목, `3534`는 습지, `2029`·`2503`·`3134`는 대도시, `1824`는 소도시의 후보로 확인했다. 아직 부분 CSV의 정식 검수 자료는 아니다. 이 표본으로 비평지 분류 가능성을 시험한다.
- [헥스 색상 후보](map_a_hex_pixel_candidates.csv)는 `tools.map_hex_pixel_candidates`로 확인된 ID 1,042개를 일괄 점수화한 자료다. 평지 967, 수목 32, 습지 2, 대도시 3, 미해결 38개로 분류됐다. [일괄 판독 시험](map_a_automation_spike.md)에 표본 검사와 규칙상 한계를 적었다. 모두 실행용 지형이 아닌 후보이다.

## 재현 명령

작업 위치에서 실행한다. 원본 이미지 `../../images_high/Stal42_Map_west-FINAL-150 Q12.jpg`는 저장소 밖의 제공 자료다.

```bash
uv run --locked python -m tools.map_fragment_audit docs
uv run --locked python -m tools.map_edge_candidates --output docs/map_a_edge_candidates.csv
uv run --locked --group map-tools python -m tools.map_image_evidence \
  '../../images_high/Stal42_Map_west-FINAL-150 Q12.jpg' \
  --output docs/map_a_river_review_queue.csv
uv run --locked --group map-tools python -m tools.map_edge_review_sheet \
  '../../images_high/Stal42_Map_west-FINAL-150 Q12.jpg' \
  --columns 29 31 --rows 3 4 --output /tmp/map_a_edge_review_29_31.png
uv run --locked --group map-tools python -m unittest discover -s tests -t . -q
```

네트워크 없이 실행할 때는 기존 세션과 같이 `UV_CACHE_DIR=/tmp/stalingrad42-uv-cache`를 명령 앞에 붙인다. 시스템 재시작 후 이 임시 캐시가 사라질 수 있으므로 그 경우 `uv`가 잠금 파일에 따라 다시 다운로드하게 한다.

## 바로 이어 할 일

1. 지도 전체의 토큰 비용을 줄이기 위해 [일괄 판독 시험](map_a_automation_spike.md)의 다음 단계인 선 연결성 분석과 지형 표본 검수를 진행한다. 지도 수동 검수로 돌아가면 검토 시트로 `3103`·`3104`를 판독한다. `2903`–`3004`의 4헥스·8변은 이미 검수했다. 각 헥스의 지형·표식·승점과 **모든 이미 검수된 인접 헥스와의 변**을 부분 CSV에 함께 기록한다. 불확실한 속성은 확정하지 않는다.
2. [규칙·자료 확인 사항](rule_issues.md)의 Savala `3600→3701`과 Anna의 도로·강 교차에서 `bridge`/`road_bridge` 속성을 어떻게 적는지 2025년 규칙과 TEC로 확인한다.
3. 부분 CSV를 고칠 때마다 후보 CSV와 강변 대기열을 재생성하고, 감사 도구·전체 테스트를 실행한다. 현재의 99픽셀 이미지 좌표 보정은 검수된 강 변 28개 중 25개를 표시했고 강이 아닌 150개 중 0개를 표시했다. 누락 3개가 있으므로 파란색 신호가 없어도 검수한다.
4. 지도 전체가 완성되기 전에는 `map_a.json`을 완성 자료로 만들지 않는다. 지도 작업 뒤에는 S1 유닛·시나리오 자료와 미구현 규칙으로 돌아간다.

주간 사용량은 `python3 /home/pc/.codex/skills/codex-usage/scripts/usage.py`로 확인한다. 2026-09-24 조사 시점에는 잔여 15%였다. 3% 이하가 되면 안전한 지점에서 이 문서를 갱신하고 작업을 멈춘다.
