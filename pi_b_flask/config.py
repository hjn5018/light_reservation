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

# 3. I2C LCD 설정 (보통 I2C 주소는 0x27 또는 0x3f)
LCD_I2C_ADDRESS = 0x27
LCD_WIDTH = 16  # 한 줄당 글자 수

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
