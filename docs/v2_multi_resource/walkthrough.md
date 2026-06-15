# 스마트 예약 시스템 개선 완료 보고서 (Walkthrough)

본 문서는 다중 공용 공간/물품 관리, PIN 기반 간편 본인 인증, 자동 예약 만료(No-show 방지) 및 사용 만료 기능을 유기적으로 연동하여 시스템을 개선하고 테스트 검증을 마친 최종 결과에 대해 설명합니다.

---

## 1. 구현 완료된 변경 사항

### 1.1 Pi B 백엔드 및 하드웨어 제어부
- **다중 자원 모델 도입 & 데이터 영속화**: [config.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_b_flask/config.py)에 회의실, 학과 PC, 공용 스테이플러, 테스트용 라즈베리파이를 정의하고, 서버 재기동 시에도 상태를 유지하도록 [data.json](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_b_flask/data.json) 파일 DB 구조를 설계하였습니다.
- **백그라운드 자동 만료 타이머 스케줄러**: [app.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_b_flask/app.py#L182)에 데몬 스레드 스케줄러를 탑재하여, 1초마다 모든 자원을 스캔하고 예약 대기 시간 만료 또는 이용 한계 시간 완료 시 자동으로 상태를 `idle`로 복귀시킵니다.
- **PIN 비밀번호 검증**: 자원 점유(`idle ➔ reserved`), 사용 시작(`reserved ➔ in_use`), 반납/취소(`➔ idle`) 시 4자리 PIN 코드 일치 여부를 검사하며, 비상 반납을 위해 `config.py`에 선언된 `MASTER_PIN`("0000") 마스터 해제 기능도 지원합니다.
- **물리 하드웨어 모니터링 포커스**: 웹에서 특정 기기를 "물리 연동 대상"으로 포커스 전환 시, [lcd.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_b_flask/hardware/lcd.py#L96)가 한글 깨짐 방지용 영문 매핑을 거쳐 첫째 줄에 `Item: [이름]`, 둘째 줄에 `Status: [상태]`를 출력하고 삼색 LED를 동기화합니다.

### 1.2 Pi A CGI 및 웹 프론트엔드
- **CGI 파라미터 포워딩 확장**: [update_status.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_a_apache/api/update_status.py)가 웹 클라이언트로부터 전달받은 `item_id`, `state`, `pin`, `action` 등의 제어 파라미터를 그대로 TCP 소켓 패킷으로 가공해 Pi B로 포워딩하고 API 조회를 중계합니다.
- **다중 자원 그리드 UI**: [index.html](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_a_apache/index.html)에서 모든 아이템의 상태 배지, 활성/비활성 제어 버튼, 물리 하드웨어 연동 전용 버튼을 슬릭한 글래스모피즘 카드로 표현합니다.
- **간편 PIN 입력 모달**: 예약을 등록하고, 사용/반납 상태를 전환할 때 자동으로 모달창이 팝업되어 보안 PIN 번호를 편리하게 제출하도록 설계했습니다.
- **초 단위 실시간 카운트다운 타이머**: [app.js](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_a_apache/app.js)에 1초 단위 타이머 스레드를 연동하여 남은 예약/이용 시간을 카운트다운하고, 30초 이하 도달 시 빨간색 긴급 경보(Blinking) 스타일로 사용자 피드백을 전달합니다.

---

## 2. 테스트 및 기능 검증 결과

### 2.1 하드웨어 단독 테스트
[test_hardware.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_b_flask/tests/test_hardware.py)를 실행하여 16x2 LCD 영문 표시 기능 및 상태 전이에 따른 부저 상승음/하강음 재생 동작을 더미 환경에서 검증 완료했습니다.
```bash
python pi_b_flask/tests/test_hardware.py
```
> **결과: OK** (5.211초 소요)
> - LED 초록/노랑/빨강 및 LCD 문구(`Item: Meeting Room`, `Status: Available / Reserved / In Use`)의 정상 순환 출력 확인.
> - 예약 ➔ 사용 시 `NOTE_C4 ➔ NOTE_E4 ➔ NOTE_G4` 상승음 및 사용 ➔ 대기 시 `NOTE_G4 ➔ NOTE_E4 ➔ NOTE_C4` 하강음의 로깅 출력 확인.

### 2.2 시스템 백엔드 통합 시나리오 테스트
[test_integration.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_projects/light_reservation/pi_b_flask/tests/test_integration.py)를 실행하여 소켓 통신을 통한 PIN 검증 규칙의 엄격성 및 기기 포커스 변경에 따른 연동 상태 변화를 검증했습니다.
```bash
python -m unittest pi_b_flask/tests/test_integration.py
```
> **결과: OK** (3.674초 소요, 2개 케이스 모두 통과)
> - PIN 정보가 유입되지 않을 때 예약 차단 검증.
> - 올바른 PIN(`1234`)으로 예약 성공 확인.
> - 다른 기기에서 잘못된 PIN(`9999`)으로 사용 전환 시도 시 차단 검증.
> - 올바른 PIN(`1234`)으로 사용 전환 및 대기 반납 성공 확인.
> - 모니터링 대상 기기를 'stapler'로 변경하는 API 요청 시 서버 내부 액티브 포커스 변수의 즉시 연동 확인.
