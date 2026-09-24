# S1 시작 카운터 병과 검수

[`s1_unit_type_review.csv`](s1_unit_type_review.csv)는 이름 붙은 171개 시작 카운터를 엔진의 `term_id`와 기계화/비기계화 분류로 옮기기 위한 **임시 대조표**다. 분류 기준은 영문 규칙서 v2.1 §2.3.3의 병과표이며, 각 행은 `images_high/`의 시작 면 이미지 파일을 출처로 가리킨다. 이 CSV는 실행용 `units_s1.json`이 아니다.

파일명으로 유형이 명확한 카운터는 `filename_inference_pending_symbol_review`로 표시했다. 이름 붙은 카운터 기호를 확대해 제공된 **2019년 playbook 24쪽**의 기호표와 대조한 9개는 `symbol_playbook_key_verified`로 구분했다. `SO-81&304MotCav-Div`는 이름에 `MotCav`가 있어도 시작 면의 인쇄 기호가 보병형이고 이동력이 3이라 `infantry`로 기록했다. 소련군 `1 TD`와 `2 TD`의 삼각형·점 기호는 playbook의 `Tank Destroyer` 기호와 일치하며, 2025년 영문 규칙서 §2.3.3과 §9.2.4에 해당 병과와 대전차 효과가 있다.

현재 집계는 보병 97, 기갑 28, 기병 11, 포병 지원 사령부 9 등 총 171개다. `bicycle_infantry`, `nkvd_infantry`, `panzergrenadier`, `sturmgeschutz` 용어는 §2.3.3에 실제로 열거돼 있어 용어집에 추가했다. `supply_point`는 기존 §18.6 용어를 사용한다. 이 분류만으로 인쇄 능력, 국적 제한, 3단계 잔존 병력 연결을 확정하지 않는다.

엔진 카탈로그는 병과 `term_id`가 용어집의 `unit` 범주 또는 실제 보급 포인트 용어인지 검사한다. 지형 용어를 유닛 병과로 잘못 입력하면 자료를 거부한다.
