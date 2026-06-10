# 예약 시스템 작업 목록 (Task List)

- [x] **Phase 1: 하드웨어 모듈 구현 (Pi B)**
  - [x] [led.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/hardware/led.py) 구현 (LED 제어 및 폴백 로직)
  - [x] [lcd.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/hardware/lcd.py) 구현 (LCD 제어 및 폴백 로직)
  - [x] [buzzer.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/hardware/buzzer.py) 구현 (Buzzer 3음계 알림 및 폴백 로직)
  - [x] [test_hardware.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/tests/test_hardware.py) 테스트 스크립트 작성 및 독립 테스트

- [x] **Phase 2: Pi B 백엔드 (Flask 및 소켓 서버) 구현**
  - [x] [config.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/config.py) 설정 파일 구현
  - [x] [app.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/app.py) 구현 (Flask 및 TCP 소켓 서버 스레드)

- [x] **Phase 3: Pi A 백엔드 (Apache 웹 서버 및 소켓 클라이언트) 구현**
  - [x] [index.html](file:///c:/Users/USER/Desktop/light_reservation/pi_a_apache/index.html) 및 [app.js](file:///c:/Users/USER/Desktop/light_reservation/pi_a_apache/app.js) 웹 UI 작성
  - [x] [update_status.py](file:///c:/Users/USER/Desktop/light_reservation/pi_a_apache/api/update_status.py) CGI/소켓 송신 스크립트 작성

- [x] **Phase 4: 통합 테스트 및 검증**
  - [x] 로컬 또는 가상 환경에서 소켓 연동 테스트 수행
  - [x] 전체 상태 전환 및 멜로디 연동 타이밍 최종 확인
