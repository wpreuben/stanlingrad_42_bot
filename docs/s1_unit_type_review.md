# S1 시작 카운터 병과 검수

[`s1_unit_type_review.csv`](s1_unit_type_review.csv)는 이름 붙은 171개 시작 카운터를 엔진의 `term_id`와 기계화/비기계화 분류로 옮기기 위한 **임시 대조표**다. 분류 기준은 영문 규칙서 v2.1 §2.3.3의 병과표이며, 각 행은 `images_high/`의 시작 면 이미지 파일을 출처로 가리킨다. 이 CSV는 실행용 `units_s1.json`이 아니다.

파일명으로 유형이 명확한 카운터는 `filename_inference_pending_symbol_review`로 표시했다. 카운터 기호를 확대해 확인한 일부는 `symbol_sample_checked`로 구분했다. `SO-81&304MotCav-Div`는 이름에 `MotCav`가 있어도 인쇄 기호가 보병형이고 이동력이 3이라 `infantry`로 기록했다. 소련군 `1 TD`와 `2 TD`는 삼각형 기호의 정확한 규칙상 병과 판독을 완료하지 못했으므로 `tank_destroyer` 후보와 `symbol_interpretation_pending`을 함께 남겼다. 엔진 자료에 넣기 전 해당 두 행을 반드시 재확인해야 한다.

현재 집계는 보병 97, 기갑 28, 기병 11, 포병 지원 사령부 9 등 총 171개다. `bicycle_infantry`, `nkvd_infantry`, `panzergrenadier`, `sturmgeschutz` 용어는 §2.3.3에 실제로 열거돼 있어 용어집에 추가했다. `supply_point`는 기존 §18.6 용어를 사용한다. 이 분류만으로 인쇄 능력, 국적 제한, 3단계 잔존 병력 연결을 확정하지 않는다.
