import time
import logging
from pi_b_flask.config import IS_RASPBERRY_PI, BUZZER_PIN

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BuzzerController")

if IS_RASPBERRY_PI:
    import RPi.GPIO as GPIO
else:
    GPIO = None

# 대표 주파수 정의 (4옥타브 기준)
NOTE_C4 = 261.63  # 도
NOTE_E4 = 329.63  # 미
NOTE_G4 = 392.00  # 솔

class BuzzerController:
    def __init__(self):
        self.is_pi = IS_RASPBERRY_PI
        self.pin = BUZZER_PIN
        self._setup()

    def _setup(self):
        if self.is_pi:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            logger.info("GPIO 부저 핀 설정 완료 (BCM 모드)")
        else:
            logger.info("[Dummy Mode] 부저 제어기 초기화 (비-라즈베리파이 환경)")

    def _play_tone(self, frequency, duration):
        """특정 주파수의 음을 정해진 시간(초) 동안 출력합니다."""
        if self.is_pi:
            try:
                # PWM 시작 (Duty Cycle 50%로 설정하여 맑은 사각파 소리 출력)
                pwm = GPIO.PWM(self.pin, frequency)
                pwm.start(50)
                time.sleep(duration)
                pwm.stop()
            except Exception as e:
                logger.error(f"부저 재생 중 오류 발생: {e}")
        else:
            # Dummy 모드 시 터미널 로그로 연주 음계를 안내
            freq_map = {
                NOTE_C4: "도 (261.63Hz)",
                NOTE_E4: "미 (329.63Hz)",
                NOTE_G4: "솔 (392.00Hz)"
            }
            note_name = freq_map.get(frequency, f"{frequency}Hz")
            logger.info(f"[Buzzer 연주] {note_name} - {duration}초 간 재생")
            time.sleep(duration)

    def play_reserved_to_in_use(self):
        """'예약'에서 '사용'으로 상태 변경 시: 3가지 상승음 (도 -> 미 -> 솔)"""
        logger.info("[Buzzer 멜로디] 예약 ➔ 사용 (상승음 재생)")
        melody = [NOTE_C4, NOTE_E4, NOTE_G4]
        for note in melody:
            self._play_tone(note, 0.15)
            time.sleep(0.05)  # 음 간의 아주 짧은 공백

    def play_in_use_to_idle(self):
        """'사용'에서 '대기'로 상태 변경 시: 다른 3가지 하강음 (솔 -> 미 -> 도)"""
        logger.info("[Buzzer 멜로디] 사용 ➔ 대기 (하강음 재생)")
        melody = [NOTE_G4, NOTE_E4, NOTE_C4]
        for note in melody:
            self._play_tone(note, 0.15)
            time.sleep(0.05)

    def cleanup(self):
        """GPIO 리소스 정리"""
        if self.is_pi:
            try:
                GPIO.cleanup(self.pin)
            except Exception as e:
                logger.debug(f"GPIO 부저 핀 정리 중 오류: {e}")
            logger.info("GPIO 부저 리소스 정리 완료")
