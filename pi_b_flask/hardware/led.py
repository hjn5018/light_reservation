import time
import logging
from pi_b_flask.config import IS_RASPBERRY_PI, LED_GREEN_PIN, LED_YELLOW_PIN, LED_RED_PIN

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LEDController")

if IS_RASPBERRY_PI:
    import RPi.GPIO as GPIO
else:
    GPIO = None

class LEDController:
    def __init__(self):
        self.is_pi = IS_RASPBERRY_PI
        self.pins = {
            'green': LED_GREEN_PIN,
            'yellow': LED_YELLOW_PIN,
            'red': LED_RED_PIN
        }
        self._setup()

    def _setup(self):
        if self.is_pi:
            # GPIO 경고 비활성화 및 모드 설정
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for pin in self.pins.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            logger.info("GPIO LED 핀 설정 완료 (BCM 모드)")
        else:
            logger.info("[Dummy Mode] LED 제어기 초기화 (비-라즈베리파이 환경)")

    def set_state(self, state):
        """
        상태에 따라 LED를 제어합니다.
        state: '대기' (또는 'idle'), '예약' (또는 'reserved'), '사용' (또는 'in_use')
        """
        # 영문/한글 상태 매핑 처리
        state = state.strip().lower()
        
        if state in ['대기', 'idle', 'available']:
            self._turn_on_only('green')
        elif state in ['예약', 'reserved']:
            self._turn_on_only('yellow')
        elif state in ['사용', 'in_use', 'occupied']:
            self._turn_on_only('red')
        else:
            logger.warning(f"알 수 없는 상태 전달됨: {state}. 모든 LED를 소등합니다.")
            self.all_off()

    def _turn_on_only(self, color):
        """지정된 색상의 LED만 켜고 나머지는 끕니다."""
        if color not in self.pins:
            return

        if self.is_pi:
            for c, pin in self.pins.items():
                if c == color:
                    GPIO.output(pin, GPIO.HIGH)
                else:
                    GPIO.output(pin, GPIO.LOW)
        
        # 동작 로깅 (Dummy 및 실기기 공통 표시)
        status_msg = ", ".join([f"{c.upper()}: {'ON' if c == color else 'OFF'}" for c in self.pins.keys()])
        logger.info(f"[LED 상태 변경] -> {status_msg}")

    def all_off(self):
        """모든 LED를 끕니다."""
        if self.is_pi:
            for pin in self.pins.values():
                GPIO.output(pin, GPIO.LOW)
        logger.info("[LED 상태 변경] -> 모든 LED OFF")

    def cleanup(self):
        """프로그램 종료 시 호출하여 모든 LED를 끄고 리소스를 정리합니다."""
        self.all_off()
        if self.is_pi:
            # LED 관련 핀만 정리
            for pin in self.pins.values():
                try:
                    GPIO.cleanup(pin)
                except Exception as e:
                    logger.debug(f"GPIO LED 핀 정리 중 오류: {e}")
            logger.info("GPIO LED 리소스 정리 완료")
