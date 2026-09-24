# 래스터 지도 구조화 프로젝트 산출물 계약

## 목적

이 문서는 별도 도구·세션에서 Stalingrad ’42 Map A 래스터 이미지를 구조화할 때, 결과를 현재 엔진 저장소에서 바로 검증하고 사용할 수 있도록 정한 산출물 계약이다. 지도 분석 도구의 내부 구현은 자유롭게 선택하되, 최종 데이터 형식과 검수 근거는 아래 계약을 따른다.

## 엔진에 바로 넣을 최종 결과

완성된 결과의 기준 파일은 다음 경로다.

```text
data/engine/v2025_04/map_a.json
```

인코딩은 UTF-8, 형식은 JSON이다. 최상위 키와 레코드는 현재 `src/engine/catalog.py`의 `load_catalog()`가 읽는 형식 그대로 작성한다.

```json
{
  "schema_version": 1,
  "ruleset_id": "v2025_04",
  "hexes": [
    {
      "id": "1300",
      "terrain": "clear",
      "neighbors": {"s": "1301"},
      "features": [],
      "edge_features": {"s": []},
      "source_ref": "map_a:hex:1300",
      "victory_points": 0
    }
  ]
}
```

위 한 헥스 예시는 형식을 보여주는 축약 예일 뿐이다. 실제 맵에서는 각 헥스의 모든 실제 이웃과 변 정보를 기록한다. `neighbors`와 `edge_features`의 방향은 `n`, `ne`, `se`, `s`, `sw`, `nw` 중 하나다. 이웃 관계는 양쪽에 서로 반대 방향으로 기록한다. 예를 들어 `1300.s = 1301`이면 `1301.n = 1300`이어야 한다. 지도 바깥, 바다, 엔트리 구역 등과 실제 헥스 이웃 관계가 없는 경계는 이웃으로 만들지 않는다.

### 허용 값

- `terrain`: `clear`, `desert`, `rough`, `woods`, `wooded_rough`, `mountain`, `minor_city`, `major_city`, `marsh`, `seasonal_marsh`
- 헥스 `features`: `town`, `landmark`, `port`, `fortification`, `entry_area`, `supply_source` 중 필요한 값
- 변 `edge_features`: `primary_road`, `secondary_road`, `railroad`, `minor_river`, `major_river`, `volga_river`, `bridge`, `road_bridge`, `railroad_bridge`, `ferry`, `lake_hexside`, `alpine_hexside`, `impassable_hexside` 중 필요한 값
- `victory_points`: 0 이상의 정수. 승점이 없는 헥스는 생략하거나 0으로 둔다.
- `source_ref`: 비어 있지 않은 문자열. 세부 출처는 `sources.json`의 출처 항목과 검수표에서 찾을 수 있어야 한다.

엔진의 허용 값은 현재 구현과 일치시킨 것이다. 프로젝트 도중 새 terrain·feature 값이 필요해지면 임의 문자열을 산출하지 말고 별도 목록으로 제안해 엔진 계약과 함께 갱신한다.

## 지도 전체 완성 전 중간 결과

부분 작업은 기존 전사 조각과 호환되는 다음 CSV 형식으로 전달한다. 이 파일들은 검수·병합 자료이며 그 자체로 완성된 엔진 맵이라고 간주하지 않는다.

`map_a_<영역>_hexes.csv`

```csv
hex_id,terrain,source_ref,other_features,victory_points
1300,clear,map_a:hex:1300,none,0
```

`map_a_<영역>_edges.csv`

```csv
hex_id,direction,neighbor_id,source_ref,crossing_features
1300,s,1301,map_a:edge:1300-s,none
```

`other_features`와 `crossing_features`에는 여러 값이 있을 때 `|`로 구분한 glossary ID를 쓰고, 값이 없으면 `none`을 쓴다. 이웃 헥스 한 쌍은 변 CSV에 한 번만 기록해도 되지만, 변 속성이 양쪽 헥스에서 같아야 한다. 최종 JSON을 생성할 때는 변 정보를 양쪽 방향에 대칭으로 펼친다.

## 검수 근거 파일

최종 또는 중간 데이터와 함께 `map_a_review.csv`를 제공한다. 이미지에서 추출한 각 헥스·변마다 적어도 다음 정보를 남긴다.

```csv
record_type,hex_id,direction,neighbor_id,attribute,value,status,source_ref,source_region,confidence,note
hex,1300,,,terrain,clear,reviewed,map_a:hex:1300,region-name,high,인쇄 지형표식 확인
edge,1300,s,1301,feature,secondary_road,reviewed,map_a:edge:1300-s,region-name,high,공유 변을 가로지르는 도로 확인
```

- `status`는 최소한 `reviewed`, `needs_review`, `excluded` 중 하나다.
- `confidence`는 `high`, `medium`, `low` 중 하나다. 자동 점수나 색상 분류는 사람이 확인하기 전까지 `reviewed`가 될 수 없다.
- `source_ref`는 원본 이미지/자료와 위치를 역추적할 수 있어야 한다. 픽셀 좌표를 계산할 수 있다면 `note` 또는 추가 열에 이미지 파일·좌표·영역을 남긴다.
- 번호가 보이는 것만으로 플레이 가능 헥스라고 판정하지 않는다. 바다색·잘림·회색 X 엔트리 구역과 같은 제외 후보도 기록한다.
- `needs_review` 항목이 남아 있으면 이를 숨기거나 임의로 평지/무특성으로 채우지 않는다.

## 출처와 파일 묶음

결과 묶음에는 다음이 들어 있어야 한다.

1. `data/engine/v2025_04/map_a.json` — 모든 플레이 가능 헥스의 검수 완료 엔진 데이터
2. `data/engine/v2025_04/sources.json` 갱신분 — 사용한 지도·지형표·룰북의 파일명, 판본, 역할
3. `docs/map_a_review.csv` 또는 영역별 검수 CSV — 항목별 근거와 검수 상태
4. `docs/map_a_coverage.md` — 입력 이미지 해시/크기, 전체·검수·미해결·제외 개수, 알려진 한계, 재생성 방법

큰 이미지나 중간 산출물은 별도 프로젝트 저장소에 둘 수 있지만, 엔진에 병합할 때 위 최종 파일과 검수 근거 파일은 이 저장소로 복사 가능해야 한다. 입력 이미지는 원본을 보존하고, 자르기·회전·리사이즈를 했다면 변환 방법과 좌표 변환을 기록한다.

## 엔진이 바로 사용할 수 있는 완료 조건

- 모든 포함 헥스 ID가 고유한 4자리 좌표다.
- 모든 이웃이 데이터에 존재하고, 좌표 기반 이웃이면 현재 격자 방향 계산과 일치한다.
- 이웃 링크와 변 속성이 반대편에서 정확히 대칭이다.
- terrain·feature 값이 엔진 허용 목록 및 glossary에 있다.
- 지도 경계·바다·비플레이 영역을 플레이 가능 헥스로 오인하지 않았으며, 제외 판단은 검수표에서 추적할 수 있다.
- 자동 추출 후보와 사람의 확인 결과가 구별된다. 완성 `map_a.json`에는 미검수 후보를 넣지 않는다.
- 저장소의 카탈로그 로더·지도 감사 명령으로 검증할 수 있고, 이미지에서 JSON과 검수표를 다시 만드는 명령이 문서에 있다.

## 새 프로젝트의 첫 전달물

도구 구현을 시작하기 전에, 새 프로젝트는 다음 세 가지를 먼저 제시한다.

1. 위 최종 JSON 및 검수 CSV를 생성하는 최소 실행 예시
2. 원본 Map A 이미지와 VASSAL 격자 정보를 좌표·ID로 연결하는 방법
3. 자동 추출 결과의 확정/미확정 경계를 보존하고, 검수자가 대량으로 수정·승인하는 방식

이 계약에 맞는 `map_a.json`과 검수 근거를 받으면 엔진 저장소에서 직접 로드·감사한 뒤 통합할 수 있다. 후보 점수표나 스크린샷만 전달된 경우에는 엔진 지형·변 데이터로 바로 가져오지 않고 검수 근거로 사용한다.
