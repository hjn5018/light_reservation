# 🚀 Smart Multi-Resource Reservation IoT System (스마트 통합 자원 예약 시스템)

본 프로젝트는 두 대의 라즈베리 파이(**Pi A**와 **Pi B**)를 유기적으로 네트워크 연동하여, 다양한 공용 공간이나 기자재(회의실, 학과 PC, 공유기, 공유 물품 등)의 예약 현황을 실시간 관리하고, 물리적인 하드웨어 피드백(LED, LCD, 부저)을 제공하는 IoT 자원 관리 솔루션입니다.

---

## 🌟 주요 특징 (Core Features)

*   **다중 자원 동시 관리**: 단일 공간 제어에서 벗어나 여러 개의 자원을 독립된 스펙(이용 시간, 예약 유효 시간)으로 동시 관리합니다.
*   **PIN 번호 기반 간편 보안**: 로그인 없이 예약 시 사용자가 설정한 4자리 숫자(PIN)를 사용해 본인 확인을 거칩니다. 타인의 오용이나 강탈을 완벽 방지하며, 비상시를 위해 마스터 해제 PIN(`0000`)을 지원합니다.
*   **자동 예약 취소 & 사용 만료 스케줄러**: 백그라운드 데몬 스레드가 1초 주기로 시간 경과를 감시하여 노쇼(No-show) 시 예약을 자동 취소하고, 최대 사용 시간에 도달한 기기를 자동으로 대기(`idle`) 상태로 복구 및 반납 처리합니다.
*   **실시간 카운트다운 타이머**: 브라우저 UI에서 잔여 이용 시간 및 예약 취소 대기 시간을 1초 간격으로 카운트다운하며, 만료 30초 전부터 긴급 시각 경보(Blinking red) 효과를 제공합니다.
*   **물리 하드웨어 모니터링 연동 (Focusing Mode)**: 웹 대시보드에서 특정 자원을 '하드웨어 연동 대상'으로 지정하면, Pi B 장치의 LCD 디스플레이에 자원 명칭과 상태가 실시간 출력되고, 삼색 LED 및 상태 전이 멜로디(부저 상승/하강음)가 해당 기기에 동기화되어 작동합니다.

---

## 🔌 하드웨어 회로 구성 (Pi B 기준)

*   **삼색 LED / 단색 LED 3개**:
    *   초록 LED (대기): BCM 17
    *   노란 LED (예약): BCM 27
    *   빨간 LED (사용): BCM 22
*   **피에조 패시브 부저 (Passive Buzzer)**:
    *   PWM 신호 핀: BCM 18
*   **LCD 디스플레이 (16x2 문자형)**:
    *   **I2C 백팩 모듈 모드 (기본)**: SDA: BCM 2 / SCL: BCM 3
    *   **GPIO 직결 모드**: RS: BCM 26, E: BCM 19, D4: BCM 13, D5: BCM 6, D6: BCM 5, D7: BCM 11

---

## 🛠️ 설치 및 설정 가이드 (Deployment Guide)

라즈베리 파이 A 및 B에 접속한 뒤, 프로젝트를 복제하고 루트 디렉토리에서 자동화 쉘 스크립트인 `setup.sh`를 구동합니다.

```bash
# 리포지토리 복제
git clone https://github.com/hjn5018/light_reservation.git
cd light_reservation

# 설정 스크립트 실행 (Root 권한 필수)
sudo bash setup.sh
```

### 1) Pi A (Apache Web Server & CGI Gateway) 설치 시
1. 메뉴에서 `1) Pi A` 선택.
2. 시스템 패키지(`apache2`, `python3`) 자동 설치 및 CGI 모듈이 활성화됩니다.
3. 연동할 대상 기기인 **Pi B의 IP 주소**를 입력합니다.
4. 웹 리소스(`index.html`, `app.js`)가 `/var/www/html/`로 복사되고, CGI 게이트웨이 스크립트(`update_status.py`)가 내부적으로 Pi B의 IP 주소를 주입받아 설정 및 배포가 완료됩니다.

### 2) Pi B (Flask REST API & Socket Hardware Server) 설치 시
1. 메뉴에서 `2) Pi B` 선택.
2. GPIO 및 I2C 통신을 위한 필수 패키지와 Python 의존 라이브러리(`Flask`, `RPLCD`, `smbus2` 등)가 설치됩니다.
3. LCD 하드웨어 연결 방식(I2C vs GPIO 핀 직결)을 묻는 질문에 알맞게 선택하면 `config.py` 기본값이 자동 갱신됩니다.
4. JSON 데이터 파일(`data.json`)에 대한 읽기/쓰기 권한이 갱신되며, 시스템 부팅 시 백그라운드에서 자동 구동되고 예외 발생 시 자동 복구되는 **systemd 데몬 서비스(`reservation_pib.service`)**가 등록 및 기동됩니다.

---

## 📂 프로젝트 파일 구조

```
light_reservation/
├── docs/                     # 시스템 설계 및 태스크 히스토리 아카이브
│   ├── v1_single_resource/   # 단일 자원 관리 시절의 구버전 문서 보관소
│   └── v2_multi_resource/    # 다중 자원 및 PIN 본인 인증 관련 최신 문서 보관소
│
├── pi_a_apache/              # Pi A (Apache 웹 서버 배포 영역)
│   ├── index.html            # 웹 통합 대시보드 프론트엔드 HTML
│   ├── app.js                # 타이머, 폴링 및 모달 팝업 컨트롤러 JS
│   └── api/                  # 아파치 CGI 디렉토리
│       └── update_status.py  # 소켓 및 Flask API 중계 CGI 스크립트
│
├── pi_b_flask/               # Pi B (Flask API 및 물리 장치 제어 소켓 서버 영역)
│   ├── app.py                # Flask 엔드포인트 및 데몬 스레드 구동 코어
│   ├── config.py             # GPIO 핀 맵핑 및 자원 스펙 상수 설정
│   ├── data.json             # 예약 현황 및 영속적 상태 저장 JSON DB
│   ├── requirements.txt      # 파이썬 라이브러리 의존 파일
│   ├── hardware/             # 액추에이터 제어 모듈 디렉토리
│   │   ├── led.py            # LED 제어부 (더미 모드 지원)
│   │   ├── lcd.py            # LCD 제어부 (한글 영문 자동 매핑)
│   │   └── buzzer.py         # 부저 멜로디 제어부 (주파수 PWM 변조)
│   └── tests/                # 테스트 스크립트 디렉토리
│       ├── test_hardware.py     # 하드웨어 동작 단독 검증 유닛 테스트
│       └── test_integration.py  # 소켓 통신 및 시나리오 통합 테스트
│
├── setup.sh                  # Pi A/B 대화형 배포 자동화 쉘 스크립트
└── README.md                 # 프로젝트 통합 매뉴얼 (본 문서)
```

---

## 🧪 테스트 가이드 (Test Run)

라즈베리 파이 기기가 아니거나 개발 PC(Windows, macOS) 환경인 경우, 드라이버를 로드하지 않는 **Dummy Mode(더미 모드)**로 전환되어 로깅 출력을 통해 안전하게 가상 모니터링 테스트를 진행할 수 있습니다.

### [하드웨어 기능 검증]
```bash
python pi_b_flask/tests/test_hardware.py
```
*   LCD 영문 매핑과 LED 상태 갱신이 콘솔 가상 박스로 출력되며, 상태 전환에 맞춰 부저 멜로디가 연주되는 로그가 작동합니다.

### [전체 소켓 통신 및 PIN 보안 시나리오 통합 테스트]
```bash
python -m unittest pi_b_flask/tests/test_integration.py
```
*   배지 조회 검증, PIN 누락 시 차단 검증, 올바르지 않은 PIN 검증, 마스터 PIN 검증, 기기 모니터링 포커스 이동 검증 등 백엔드 소켓 및 HTTP 파이프라인의 모든 예외 처리를 자동 확인합니다.
