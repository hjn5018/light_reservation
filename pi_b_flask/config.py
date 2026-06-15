import os
import sys

# 소켓 서버 및 Flask 설정
SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 50007
FLASK_PORT = 5000

# 하드웨어 GPIO 핀 맵핑 설정 (BCM 핀 번호 기준)
# 1. LED 핀 (개별 단색 LED 3개 구성)
LED_GREEN_PIN = 17
LED_YELLOW_PIN = 27
LED_RED_PIN = 22

# 2. 패시브 부저 (Passive Buzzer) 핀
BUZZER_PIN = 18

# 3. LCD 설정 (I2C 또는 GPIO 직결)
LCD_MODE = os.environ.get('LCD_MODE', 'I2C').upper()  # 'I2C' 또는 'GPIO'
LCD_I2C_ADDRESS = 0x27
LCD_WIDTH = 16  # 한 줄당 글자 수

# GPIO 직결 모드 시의 BCM 핀 정의
LCD_PINS = {
    "rs": 26,
    "e": 19,
    "d4": 13,
    "d5": 6,
    "d6": 5,
    "d7": 11
}

# 환경 감지 및 Dummy 모드 여부 설정
# RPi.GPIO 및 smbus(I2C LCD용) 라이브러리가 없거나, 리눅스(라즈베리파이)가 아닐 경우 자동으로 Dummy 드라이버 작동
IS_RASPBERRY_PI = False
try:
    import platform
    if platform.system() == 'Linux':
        # 실제 Raspberry Pi 인지 추가 확인 가능하지만, 여기서는 Linux 여부와 라이브러리 로드 성공 여부로 판단
        import RPi.GPIO
        IS_RASPBERRY_PI = True
except ImportError:
    IS_RASPBERRY_PI = False

# 디버그 콘솔 출력 여부
DEBUG_MODE = True

# JSON DB 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DB_PATH = os.path.join(BASE_DIR, 'data.json')

# 관리자 마스터 PIN
MASTER_PIN = "0000"

# 공간 및 물품 예약 기본 사양 정의 (이용 시간, 예약 대기 시간은 초 단위로 설정)
RESERVATION_ITEMS = {
    "meeting_room": {
        "name": "회의실",
        "usage_duration": 3600,        # 60분
        "reservation_timeout": 600     # 10분
    },
    "pc": {
        "name": "학과 PC",
        "usage_duration": 7200,        # 120분
        "reservation_timeout": 900     # 15분
    },
    "stapler": {
        "name": "공용 스테이플러",
        "usage_duration": 300,         # 5분
        "reservation_timeout": 120     # 2분
    },
    "raspberry_pi": {
        "name": "테스트용 라즈베리파이",
        "usage_duration": 10800,       # 180분
        "reservation_timeout": 1200    # 20분
    }
}

