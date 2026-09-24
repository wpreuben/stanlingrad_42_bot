# S1 시작 카드의 헥스별 묶음 전사

[`s1_start_card_locations.csv`](s1_start_card_locations.csv)는 제공된 2019년 추축군·소련군 *Campaign Game and Fall Blau Scenario* 시작 카드에서 **지도 헥스에 적힌 카운터 묶음**을 옮긴 중간 검수 자료다. `card_row`는 카드에서 위에서 아래로 읽은 행 번호이며, `printed_labels`는 해당 헥스 아래 괄호로 묶인 카운터의 인쇄 표기를 카드의 왼쪽부터 `;`로 구분한 것이다. `+`가 든 표기는 카드에 그렇게 인쇄된 한 카운터다. 동일한 숫자가 여러 군·병과에 재사용되므로 이 표기는 아직 엔진의 고유 유닛 ID가 아니다.

원본: `Images/httpssteamusercontentaakamaihdnetugc17884688380553658153FC9D37838E1E7AE747007396036D0CAE7AF8A0C.jpg`(추축군), `Images/httpssteamusercontentaakamaihdnetugc1788468838055329033A93814D55EA6FBC4805AE36AD0C6339D5A88391A.jpg`(소련군). 이 CSV는 양 카드의 지도 시작 묶음 98개(추축군 50개, 소련군 48개)를 기록한다. 카드의 카운터 그림과 인쇄 수치·뒷면, Map A 헥스의 실제 존재 여부는 아직 대조 중이므로 `units_s1.json`이나 `fall_blau.json`로 사용하지 않는다.

카드의 초기 공중 유닛·Off Prep·Rail marker·Blücher/NCV 표시 상자, 소련군 Volga Flotilla·Eliminated Box·Trans-Caucasus 표시 상자, 5예비군의 Fall Blau 3턴 진입은 이 지도 헥스 CSV에 포함하지 않았다. 소련군 6예비군의 `3806` 묶음은 지도에 시작하지만 카드와 2025년 규칙 S1.2에 따라 **2턴에 정상 이동 가능**하다. 5예비군은 S1.2에 따라 **3턴 Entry Area M에서 `4100`~`4111` 사이로 진입**하므로 초기 지도 배치가 아니다. 2019년 카드의 `4210` 북쪽 가장자리 표기와 범위가 다르므로 2025년 규칙의 범위를 적용한다. 두 사건은 이후 시나리오의 해제·증원 일정 자료로 따로 모델링해야 한다.

지도 헥스 밖의 초기 상태도 카드에 명시돼 있다. 추축군은 Rail marker 5개가 `1303`, `1717`, `2126`, `2427`, `2431`에 있고, 공중 유닛 `VIII FK`, `IV FK`가 Available이다. Off Prep Ready 2개는 임의의 Army HQ와 함께 놓는다. Blücher Display와 North Caucasian Volunteer Units Display에는 별도 카운터가 있다. 소련군 Volga Flotilla는 Available, 일부 카운터는 Eliminated Box와 Trans-Caucasus Units Display에 있다. 이 항목은 유닛·마커의 종류와 카드 앞뒷면을 검수한 뒤 별도 초기 상태 자료로 전사한다.

다음 검수에서 각 `printed_labels`를 카운터 앞뒷면, 소속 군·병과와 대조해 고유 ID와 면별 수치를 확정한다. 카드의 그룹 괄호와 2025년 S1.1~S1.2의 예외도 확인한다.

[`s1_start_card_fronts.csv`](s1_start_card_fronts.csv)에는 양측 지도 시작 카운터 171개(추축군 78개, 소련군 93개)의 카드 앞면 수치 문자열을 같은 순서로 옮겼다. 묶음별 카운터 수와 라벨 순서는 위치 CSV와 모두 일치한다. 이 문자열은 수치의 위치만 보존한다. 탱크 점, 정예·낮은 질 표시, 검은 이동력 테두리, 단계 수, 국적·병과, 뒷면 수치는 아직 포함하지 않는다. `5[10]-5-4`는 카드에서 기본 공격 수치 `5` 위에 작은 `10`이 붙은 모습을 임시로 적은 것이며, 효과를 뜻하지 않는다. HQ의 `S(1)5`도 카드에 보이는 문자열로만 보관한다. 따라서 이 파일은 `UnitFace` 자료로 바로 변환할 수 없다.
