# 스마트 예약 시스템 개선 작업 목록

- `[x]` **Phase 1: Pi B 공통 설정 및 JSON DB 도입**
  - `[x]` `pi_b_flask/config.py` 파일에 아이템 속성 정의 및 파일 경로 추가
  - `[x]` `pi_b_flask/data.json` 데이터 저장 파일 작성
- `[x]` **Phase 2: Pi B 백엔드 및 자동 만료 타이머 스케줄러 구현**
  - `[x]` `pi_b_flask/app.py`에 파일 DB 로드/세이브 및 검증 로직 구현
  - `[x]` 백그라운드 스케줄러 스레드 탑재하여 예약/사용 만료 관리
  - `[x]` 소켓 서버 및 Flask API 응답 구조를 확장 데이터에 맞춤
- `[x]` **Phase 3: Pi B 하드웨어 출력 모듈 수정**
  - `[x]` `pi_b_flask/hardware/lcd.py`에서 아이템 이름과 상태를 LCD에 동시 표기하도록 변경
  - `[x]` `pi_b_flask/hardware/led.py` 및 `buzzer.py`에서 모니터링 지정 대상 아이템만 제어하도록 수정
- `[x]` **Phase 4: Pi A CGI 게이트웨이 파라미터 연동**
  - `[x]` `pi_a_apache/api/update_status.py`에서 전달받은 파라미터를 그대로 소켓으로 포워딩하도록 변경
- `[x]` **Phase 5: Pi A 프론트엔드 다중 자원 및 타이머 UI/UX 고도화**
  - `[x]` `pi_a_apache/index.html`에 다중 자원 카드 뷰 및 PIN 입력 팝업(모달) 추가
  - `[x]` `pi_a_apache/app.js`에 실시간 초 단위 카운트다운 타이머 연동 및 PIN 검증 API 연동
- `[x]` **Phase 6: 테스트 및 기능 검증**
  - `[x]` 더미 환경에서의 시나리오 통합 테스트 수행 및 버그 수정
