import time
import logging
from pi_b_flask.config import IS_RASPBERRY_PI, LCD_MODE, LCD_I2C_ADDRESS, LCD_WIDTH, LCD_PINS

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LCDController")

# RPi.GPIO 및 RPLCD 임포트 시도
try:
    if IS_RASPBERRY_PI:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
    else:
        GPIO_AVAILABLE = False
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False

try:
    if IS_RASPBERRY_PI:
        from RPLCD.i2c import CharLCD as I2cCharLCD
        from RPLCD.gpio import CharLCD as GpioCharLCD
        RPLCD_AVAILABLE = True
    else:
        RPLCD_AVAILABLE = False
except (ImportError, RuntimeError):
    RPLCD_AVAILABLE = False


class LCDController:
    def __init__(self):
        self.is_pi = IS_RASPBERRY_PI and GPIO_AVAILABLE and RPLCD_AVAILABLE
        self.lcd = None
        self._setup()

    def _setup(self):
        if self.is_pi:
            try:
                mode = LCD_MODE.upper()
                if mode == "I2C":
                    self.lcd = I2cCharLCD(
                        i2c_expander='PCF8574',
                        address=LCD_I2C_ADDRESS,
                        port=1,
                        cols=LCD_WIDTH,
                        rows=2,
                        dotsize=8
                    )
                    logger.info(f"I2C LCD 초기화 성공 (Address: {hex(LCD_I2C_ADDRESS)})")
                elif mode == "GPIO":
                    # BCM 핀 매핑
                    pin_rs = LCD_PINS.get("rs", 26)
                    pin_e = LCD_PINS.get("e", 19)
                    pin_d4 = LCD_PINS.get("d4", 13)
                    pin_d5 = LCD_PINS.get("d5", 6)
                    pin_d6 = LCD_PINS.get("d6", 5)
                    pin_d7 = LCD_PINS.get("d7", 11)
                    
                    self.lcd = GpioCharLCD(
                        pin_rs=pin_rs,
                        pin_rw=None,
                        pin_e=pin_e,
                        pins_data=[pin_d4, pin_d5, pin_d6, pin_d7],
                        numbering_mode=GPIO.BCM,
                        cols=LCD_WIDTH,
                        rows=2,
                        dotsize=8
                    )
                    logger.info("GPIO Direct LCD 초기화 성공")
            except Exception as e:
                logger.error(f"LCD 하드웨어 초기화 실패: {e}. Dummy 모드로 폴백합니다.")
                self.is_pi = False
                self.lcd = None
        else:
            logger.info("[Dummy Mode] LCD 제어기 초기화 (비-라즈베리파이 환경)")

    def display_message(self, line1, line2=""):
        """LCD 화면에 텍스트를 출력합니다."""
        # 16자 보정
        line1 = line1.ljust(LCD_WIDTH, " ")[:LCD_WIDTH]
        line2 = line2.ljust(LCD_WIDTH, " ")[:LCD_WIDTH]

        if self.is_pi and self.lcd:
            try:
                self.lcd.clear()
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string(line1)
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(line2)
            except Exception as e:
                logger.error(f"LCD 쓰기 중 오류 발생: {e}")
        
        # 동작 콘솔 출력 (Dummy 및 실기기 공통)
        logger.info(f"[LCD 화면 갱신]\n┌────────────────┐\n│{line1}│\n│{line2}│\n└────────────────┘")

    def display_status(self, state):
        """예약 상태에 맞는 LCD 문구를 보여줍니다."""
        state = state.strip().lower()
        
        # 한글 상태명과 깔끔한 영문 상태명을 혼용하여 LCD에 표기
        if state in ['대기', 'idle', 'available']:
            self.display_message("Status: Available", "   - READY -   ")
        elif state in ['예약', 'reserved']:
            self.display_message("Status: Reserved", "   - HOLDING - ")
        elif state in ['사용', 'in_use', 'occupied']:
            self.display_message("Status: In Use", "  - OCCUPIED - ")
        else:
            self.display_message("Status: Unknown", f"State: {state[:10]}")

    def clear(self):
        """LCD 화면을 지웁니다."""
        if self.is_pi and self.lcd:
            try:
                self.lcd.clear()
            except Exception as e:
                logger.error(f"LCD Clear 중 오류 발생: {e}")
        logger.info("[LCD 화면 Clear]")

    def cleanup(self):
        """종료 시 LCD 화면을 정리합니다."""
        if self.is_pi and self.lcd:
            try:
                self.lcd.clear()
                self.lcd.close()
            except Exception as e:
                logger.error(f"LCD 자원 해제 중 오류 발생: {e}")
        logger.info("[LCD 리소스 정리 완료]")
