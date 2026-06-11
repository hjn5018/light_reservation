# 파일 설명서 (File Explanations)

이 문서에서는 `light_reservation` 프로젝트의 주요 구성 파일인 `pi_b_flask/app.py`와 `setup.sh` 파일의 기능과 구조, 특히 스레드(Thread)의 동작 방식과 자동 설정 스크립트의 작동 단계를 상세히 설명합니다.

---

## 1. `pi_b_flask/app.py` 설명 및 스레드(Thread) 구조

`app.py`는 **Pi B (하드웨어 제어부)**에서 실행되는 핵심 애플리케이션으로, **Flask Web API** 서버와 **TCP 소켓 서버**를 동시에 구동하여 상태 제어 요청을 수신하고 LED, LCD, Buzzer 등의 하드웨어를 안전하게 제어합니다.

### 1.1. 스레드(Thread)와 소켓 서버 동작 방식
이 애플리케이션은 파이썬의 `threading` 모듈을 사용하여 멀티스레드로 동작합니다. 이는 Flask와 소켓 서버가 동시에 각각의 포트(Flask: REST API 포트, Socket: TCP 포트)에서 클라이언트 요청을 대기하고 처리할 수 있게 해줍니다.

1. **소켓 백그라운드 리스너 스레드 생성 (`startup_setup`)**
   - Flask 서버가 실행되기 직전, `startup_setup()` 함수가 실행됩니다.
   - 이 함수는 `run_socket_server()` 함수를 대상으로 하는 백그라운드 스레드(`socket_thread`)를 생성하고 시작합니다.
   - `daemon = True`로 설정되어 있어, 메인 프로세스(Flask 서버)가 종료될 때 이 백그라운드 스레드도 함께 자동으로 안전하게 종료됩니다.

2. **클라이언트 연결 스레드 분기 (`run_socket_server`)**
   - TCP 소켓 서버는 `while True:` 루프 안에서 Pi A(웹 서버) 등 외부 클라이언트의 접속을 기다립니다 (`server_socket.accept()`).
   - 연결이 수락되면(Accept), 주 스레드가 연결 처리로 인해 대기 상태(Blocking)에 빠지는 것을 방지하기 위해 새로운 스레드(`t = threading.Thread(target=handle_socket_client, args=(client_conn,))`)를 즉시 생성하여 연결 객체를 전달합니다.
   - 이 연결 전용 스레드 역시 `daemon = True`로 설정되어 신속하게 요청을 파싱하고 응답한 뒤 소멸합니다.

### 1.2. 스레드 안전성(Thread Safety)과 뮤텍스 락(Mutex Lock)
Flask API 스레드와 TCP 소켓 서버 스레드는 모두 하나의 전역 변수인 `current_state`(현재 예약 시스템 상태)와 물리 하드웨어 자원(LED, LCD, Buzzer)에 동시 접근하여 값을 읽거나 변경할 수 있습니다. 

여러 스레드가 동일한 자원에 동시에 접근하여 수정하려고 할 때 발생하는 충돌(Race Condition, 경쟁 상태)을 방지하기 위해 **뮤텍스 락(`threading.Lock`)**을 사용합니다.

- **`state_lock = threading.Lock()`**
  - 전역 임계 영역(Critical Section)을 보호하기 위한 상호 배제(Mutual Exclusion) 락 객체입니다.
- **`with state_lock:` 구문**
  - **상태 변경 시 (`change_system_state`)**: 새로운 상태로 변경하고 하드웨어(LED, LCD)를 갱신하며 이전 상태에 맞춰 부저 멜로디를 울리는 전 과정이 완료될 때까지 다른 스레드가 상태를 변경하거나 조회하지 못하도록 잠금(Lock)을 획득합니다. 작업이 완료되면 자동으로 잠금이 해제됩니다.
  - **상태 조회 시 (`get_status` - `/api/status`)**: Flask를 통해 사용자가 현재 상태를 조회할 때도, 상태가 변경 중인 불완전한 찰나의 순간을 읽지 않도록 락을 획득한 채 안전하게 `current_state` 값을 가져옵니다.

---

## 2. `setup.sh` 설명 (설정/설치 스크립트)

`setup.sh`는 라즈베리 파이 A(웹/CGI)와 라즈베리 파이 B(Flask/하드웨어)의 **초기 환경 설치 및 설정을 자동화**해 주는 Bash 쉘 스크립트입니다. 

### 2.1. 공통 처리 단계
1. **Root 권한 체크**: 패키지 설치 및 시스템 서비스 등록을 위해 스크립트가 `sudo` (root 권한)로 실행되었는지 검사합니다. (`$EUID`가 0인지 확인)
2. **역할 선택 메뉴 제공**: 실행 시 사용자에게 이 라즈베리 파이가 **Pi A**인지 **Pi B**인지 묻는 상호작용형 메뉴가 나타납니다.

### 2.2. [1] Pi A (Apache 웹 서버) 설정 단계 (`setup_pi_a`)
Pi A는 사용자가 브라우저로 접근하는 웹 프론트엔드와 예약 신호를 전달하는 CGI 클라이언트를 구성합니다.
1. **의존성 패키지 설치**: 시스템 패키지 매니저(`apt-get`)를 통해 `apache2` 웹 서버와 `python3`를 설치합니다.
2. **Apache CGI 모듈 활성화**: Python CGI 스크립트가 실행될 수 있도록 `a2enmod cgi` 명령어를 수행하고 Apache 서버를 재시작합니다.
3. **연동 IP 입력**: 연동할 대상인 Pi B의 IP 주소를 입력받습니다. (기본값: `127.0.0.1`)
4. **웹 리소스 배포 및 설정**:
   - `index.html`과 `app.js`를 Apache 기본 웹 디렉토리인 `/var/www/html/`로 복사합니다.
   - CGI 스크립트(`update_status.py`)를 `/var/www/html/api/` 폴더에 복사하고, 복사본 내부의 `PI_B_IP` 변수값에 앞서 입력받은 Pi B의 IP 주소를 주입(sed 치환)합니다.
   - CGI 디렉토리 및 실행 파일의 권한을 `755`로 설정하여 웹 서버가 실행할 수 있게 합니다.
   - `/etc/apache2/conf-available/reservation-cgi.conf` 설정 파일을 생성하여 해당 폴더 내의 Python 스크립트가 CGI로 처리되도록 권한을 부여하고 Apache 설정을 재로드합니다.

### 2.3. [2] Pi B (Flask & Hardware 서버) 설정 단계 (`setup_pi_b`)
Pi B는 Flask API와 TCP 소켓 서버를 통해 하드웨어(LED, LCD, 부저)를 실시간으로 제어합니다.
1. **시스템 필수 라이브러리 설치**: GPIO 제어, I2C 통신을 위해 `python3-pip`, `python3-rpi.gpio`, `python3-smbus`, `i2c-tools` 패키지를 설치합니다.
2. **Python 의존성 설치**: `pi_b_flask/requirements.txt`에 기록된 라이브러리(Flask, RPLCD 등)를 `pip3 install`로 설치합니다.
3. **LCD 연결 모드 설정**: LCD의 연결 유형(I2C 백팩 모듈 vs GPIO 핀 직접 연결)을 선택받고, 그 결과를 `pi_b_flask/config.py`의 `LCD_MODE` 설정값에 반영합니다.
4. **Systemd 백그라운드 서비스 등록**:
   - `/etc/systemd/system/reservation_pib.service` 파일에 서비스 설정 파일(유닛 파일)을 생성합니다.
   - 이 서비스는 Pi B 부팅 시 `/usr/bin/python3 pi_b_flask/app.py`를 자동으로 백그라운드에서 실행하고, 비정상 종료 시 재시작(`Restart=always`)하도록 설정합니다.
   - 서비스를 시스템에 등록(`enable`)하고 즉시 실행(`restart`)하여 백그라운드에서 상시 대기하도록 만듭니다.
