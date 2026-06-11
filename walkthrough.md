# 스마트 예약 시스템 구현 결과 보고서 (Walkthrough)

라즈베리 파이 2대 간의 소켓 및 Flask 연동 예약 시스템의 핵심 설계 요구사항을 바탕으로 모든 소프트웨어 및 하드웨어 모듈 구현을 완료하였습니다.

---

## 1. 구현 완료 코드 구조

프로젝트 루트 디렉토리 아래에 아래와 같이 Pi A(Apache)와 Pi B(Flask)로 디렉토리를 분리하여 작업 공간을 구성했습니다.

### 1.1 Pi B (Flask & Hardware Control)
- [config.py]: GPIO 및 LCD 핀 정보, 소켓 포트 설정 및 플랫폼 감지(더미 폴백 작동용) 파일입니다.
- [hardware/led.py]: 초록/노랑/빨강 LED 3개 점등을 상태별로 맵핑 제어합니다.
- [hardware/lcd.py]: RPLCD 라이브러리 기반 16x2 LCD 드라이버 모듈(I2C 및 GPIO 듀얼 모드 지원)로 터미널 가상 화면 렌더링 기능을 포함합니다.
- [hardware/buzzer.py]: 패시브 부저 PWM을 이용한 상승(도-미-솔) / 하강(솔-미-도) 3음계 연주 클래스입니다.
- [app.py]: 백그라운드 TCP 소켓 리스너 스레드와 모니터링용 Flask REST API를 동시에 구동하는 메인 스크립트입니다.
- [requirements.txt]: 필요한 파이썬 라이브러리(Flask, RPLCD, smbus2 등) 의존성 파일입니다.

### 1.2 Pi A (Apache Web Client)
- [index.html]: 글래스모피즘 테마의 반응형 제어 센터 대시보드 웹 페이지입니다.
- [app.js]: CGI 호출, 실시간 상태 폴링(5초 주기) 및 화면 상의 부저 작동 인터랙션을 담당하는 JavaScript 모듈입니다.
- [api/update_status.py]: CGI-BIN 규격의 게이트웨이 스크립트로, 웹 브라우저로부터 요청을 받아 Pi B로 소켓 패킷을 생성해 던집니다. state 인자 누락 시 Flask HTTP API를 통해 상태를 동기화합니다.

---

## 2. 테스트 및 검증 결과

### 2.1 하드웨어 단독 시나리오 테스트
[test_hardware.py]를 실행하여 4가지 상태 전환(`대기 ➔ 예약 ➔ 사용 ➔ 대기`) 시 LED, LCD, Buzzer 드라이버가 정상 작동함을 검증하였습니다.
- **결과**: `OK` (5.21s)

### 2.2 시스템 통신 통합 테스트
[test_integration.py]를 실행하여 백그라운드에 실제 Flask 및 TCP Socket 서버를 구동시킨 후, 가상 소켓 클라이언트를 통한 제어 패킷 전송과 Flask HTTP API 교차 조회가 오차 없이 정합성을 유지하는지 검증하였습니다.
- **결과**: `OK` (4.88s)
  - `idle ➔ reserved`: 부저 없음, 노랑 LED, LCD Reserved 표시
  - `reserved ➔ in_use`: 부저 3가지 상승음 (도-미-솔), 빨강 LED, LCD In Use 표시
  - `in_use ➔ idle`: 부저 3가지 하강음 (솔-미-도), 초록 LED, LCD Available 표시

---

## 3. 실제 라즈베리 파이 배포 가이드

실제 기기 배포 및 상호 연동을 추진하기 위해 하드웨어를 결선한 뒤, `setup.sh` 자동 설치 스크립트를 사용하여 간편하게 배포할 수 있습니다.

### STEP 1: 하드웨어 결선 (Pi B 공통)
- **LED (단색 LED 3개) 연결**:
  - 초록 LED ➔ GPIO 17 (220Ω 저항 직렬 연결)
  - 노랑 LED ➔ GPIO 27 (220Ω 저항 직렬 연결)
  - 빨강 LED ➔ GPIO 22 (220Ω 저항 직렬 연결)
- **부저 (패시브 부저) 연결**:
  - PWM I/O 핀 ➔ GPIO 18 (GND 및 VCC는 부저 모듈 전원부 연결)
- **LCD 연결**:
  - **방법 A: I2C 백팩 모듈 사용 시** (기본값):
    - SDA ➔ GPIO 2 (SDA)
    - SCL ➔ GPIO 3 (SCL)
    - VCC ➔ 5V 단자, GND ➔ GND 단자
  - **방법 B: GPIO 직접 연결 시** (I2C 백팩이 없을 때):
    - LCD VSS ➔ GND 단자
    - LCD VDD ➔ 5V 단자
    - LCD VO (Contrast 제어) ➔ 가변 저항의 가운데 핀 (또는 약 1kΩ~2kΩ 저항을 거쳐 GND로 연결)
    - LCD RS ➔ GPIO 26
    - LCD RW ➔ GND 단자 (쓰기 고정)
    - LCD E ➔ GPIO 19
    - LCD D4 ➔ GPIO 13
    - LCD D5 ➔ GPIO 6
    - LCD D6 ➔ GPIO 5
    - LCD D7 ➔ GPIO 11
    - LCD A (백라이트 Anode) ➔ 5V 단자 (또는 220Ω 저항 직렬 연결 후 5V)
    - LCD K (백라이트 Cathode) ➔ GND 단자

### STEP 2: 자동 원스톱 배포 (setup.sh 사용)

각 라즈베리 파이에 접속한 후, 터미널에서 다음 명령어를 실행하여 원클릭으로 구성을 마칠 수 있습니다.

```bash
# 1. 깃 클론으로 소스 받기
git clone https://github.com/hjn5018/light_reservation.git
cd light_reservation

# 2. 자동 빌드/배포 스크립트 실행
sudo bash setup.sh
```

- **Pi A (Apache + CGI) 설정 시**: 
  - 선택 메뉴에서 `1`번을 선택합니다.
  - 연동할 **Pi B의 IP 주소**를 입력하면 CGI 스크립트 내부에 자동 반영되고, 웹 리소스 복사 및 CGI 실행 권한 설정이 한번에 완료됩니다.
- **Pi B (Flask + 소켓 + 하드웨어) 설정 시**: 
  - 선택 메뉴에서 `2`번을 선택합니다.
  - 필수 하드웨어 라이브러리(RPi.GPIO, RPLCD, smbus2)가 자동 설치되며, 백그라운드 구동을 위한 **systemd 백그라운드 서비스(`reservation_pib.service`)**로 등록 및 즉시 가동됩니다.

---

## 4. 수동 배포 가이드 (참고용)
(자동 스크립트를 사용하지 않고 배포하려면 아래 절차를 직접 실행해 주세요.)

### Pi B (Flask + Socket 서버) 수동 구성
1. Pi B 터미널에서 라이브러리 설치:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-rpi.gpio python3-smbus python3-smbus2
   pip3 install -r pi_b_flask/requirements.txt
   ```
2. I2C 인터페이스 활성화:
   ```bash
   sudo raspi-config # Interface Options -> I2C 활성화
   ```
3. 백그라운드로 애플리케이션 구동:
   ```bash
   python3 pi_b_flask/app.py
   ```

### Pi A (Apache + CGI) 수동 구성
1. Apache2 설치 및 CGI 모듈 활성화:
   ```bash
   sudo apt-get install apache2 && sudo a2enmod cgi && sudo systemctl restart apache2
   ```
2. 파일 배치:
   - `pi_a_apache/index.html` 및 `app.js` ➔ `/var/www/html/` 경로 복사
   - `pi_a_apache/api/update_status.py` ➔ `/usr/lib/cgi-bin/` 또는 `/var/www/html/api/` 경로 복사 및 실행 권한 인가 (`chmod +x`)

