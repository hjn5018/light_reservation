# 스마트 예약 시스템 구현 결과 보고서 (Walkthrough)

라즈베리 파이 2대 간의 소켓 및 Flask 연동 예약 시스템의 핵심 설계 요구사항을 바탕으로 모든 소프트웨어 및 하드웨어 모듈 구현을 완료하였습니다.

---

## 1. 구현 완료 코드 구조

프로젝트 루트 디렉토리 아래에 아래와 같이 Pi A(Apache)와 Pi B(Flask)로 디렉토리를 분리하여 작업 공간을 구성했습니다.

### 1.1 Pi B (Flask & Hardware Control)
- [config.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/config.py): GPIO 핀 정보, 소켓 포트 설정 및 플랫폼 감지(더미 폴백 작동용) 파일입니다.
- [hardware/led.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/hardware/led.py): 초록/노랑/빨강 LED 3개 점등을 상태별로 맵핑 제어합니다.
- [hardware/lcd.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/hardware/lcd.py): I2C 16x2 LCD 드라이버 모듈로 터미널 가상 화면 렌더링 기능을 포함합니다.
- [hardware/buzzer.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/hardware/buzzer.py): 패시브 부저 PWM을 이용한 상승(도-미-솔) / 하강(솔-미-도) 3음계 연주 클래스입니다.
- [app.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/app.py): 백그라운드 TCP 소켓 리스너 스레드와 모니터링용 Flask REST API를 동시에 구동하는 메인 스크립트입니다.
- [requirements.txt](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/requirements.txt): 필요한 파이썬 라이브러리 의존성 파일입니다.

### 1.2 Pi A (Apache Web Client)
- [index.html](file:///c:/Users/USER/Desktop/light_reservation/pi_a_apache/index.html): 글래스모피즘 테마의 반응형 제어 센터 대시보드 웹 페이지입니다.
- [app.js](file:///c:/Users/USER/Desktop/light_reservation/pi_a_apache/app.js): CGI 호출, 실시간 상태 폴링(5초 주기) 및 화면 상의 부저 작동 인터랙션을 담당하는 JavaScript 모듈입니다.
- [api/update_status.py](file:///c:/Users/USER/Desktop/light_reservation/pi_a_apache/api/update_status.py): CGI-BIN 규격의 게이트웨이 스크립트로, 웹 브라우저로부터 요청을 받아 Pi B로 소켓 패킷을 생성해 던집니다. state 인자 누락 시 Flask HTTP API를 통해 상태를 동기화합니다.

---

## 2. 테스트 및 검증 결과

### 2.1 하드웨어 단독 시나리오 테스트
[test_hardware.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/tests/test_hardware.py)를 실행하여 4가지 상태 전환(`대기 ➔ 예약 ➔ 사용 ➔ 대기`) 시 LED, LCD, Buzzer 드라이버가 정상 작동함을 검증하였습니다.
- **결과**: `OK` (5.21s)

### 2.2 시스템 통신 통합 테스트
[test_integration.py](file:///c:/Users/USER/Desktop/light_reservation/pi_b_flask/tests/test_integration.py)를 실행하여 백그라운드에 실제 Flask 및 TCP Socket 서버를 구동시킨 후, 가상 소켓 클라이언트를 통한 제어 패킷 전송과 Flask HTTP API 교차 조회가 오차 없이 정합성을 유지하는지 검증하였습니다.
- **결과**: `OK` (4.88s)
  - `idle ➔ reserved`: 부저 없음, 노랑 LED, LCD Reserved 표시
  - `reserved ➔ in_use`: 부저 3가지 상승음 (도-미-솔), 빨강 LED, LCD In Use 표시
  - `in_use ➔ idle`: 부저 3가지 하강음 (솔-미-도), 초록 LED, LCD Available 표시

---

## 3. 실제 라즈베리 파이 배포 가이드

실제 기기 배포 및 상호 연동을 추진하기 위해 아래 단계를 따르십시오.

### STEP 1: 하드웨어 결선
- **LED (단색 LED 3개) 연결**:
  - 초록 LED ➔ GPIO 17 (220Ω 저항 직렬 연결)
  - 노랑 LED ➔ GPIO 27 (220Ω 저항 직렬 연결)
  - 빨강 LED ➔ GPIO 22 (220Ω 저항 직렬 연결)
- **부저 (패시브 부저) 연결**:
  - PWM I/O 핀 ➔ GPIO 18 (GND 및 VCC는 부저 모듈 전원부 연결)
- **I2C 16x2 LCD 연결**:
  - SDA ➔ GPIO 2 (SDA)
  - SCL ➔ GPIO 3 (SCL)
  - VCC ➔ 5V 단자, GND ➔ GND 단자

### STEP 2: Pi B (Flask + Socket 서버) 구성
1. Pi B 터미널에서 라이브러리 설치:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-rpi.gpio python3-smbus
   pip3 install -r requirements.txt
   ```
2. I2C 인터페이스 활성화:
   ```bash
   sudo raspi-config
   # Interface Options -> I2C -> Enable 활성화 후 재부팅
   ```
3. 백그라운드로 애플리케이션 시작:
   ```bash
   python3 pi_b_flask/app.py
   ```

### STEP 3: Pi A (Apache + CGI) 구성
1. Apache2 설치 및 CGI 모듈 활성화:
   ```bash
   sudo apt-get install apache2
   sudo a2enmod cgi
   sudo systemctl restart apache2
   ```
2. 파일 배치:
   - `pi_a_apache/index.html` 및 `app.js` ➔ `/var/www/html/` 경로 복사
   - `pi_a_apache/api/update_status.py` ➔ `/usr/lib/cgi-bin/` (또는 CGI 실행 권한이 인가된 `/var/www/html/api/` 경로) 복사 후 실행 권한 부여 (`chmod +x update_status.py`)
3. Pi B의 IP 주소 설정:
   - `pi_a_apache/api/update_status.py` 파일 내의 `PI_B_IP = '127.0.0.1'` 부분을 실제 Pi B의 IP 주소(예: `'192.168.0.x'`)로 수정하거나 환경변수 `PI_B_IP`를 설정하십시오.
