import time
import logging
from pi_b_flask.config import IS_RASPBERRY_PI, LCD_I2C_ADDRESS, LCD_WIDTH

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LCDController")

# 라즈베리 파이 환경에서 I2C 통신용 smbus 라이브러리 임포트 시도
try:
    if IS_RASPBERRY_PI:
        import smbus
    else:
        smbus = None
except ImportError:
    smbus = None
    logger.warning("smbus 라이브러리를 찾을 수 없습니다. Dummy LCD 모드로 작동합니다.")

# LCD I2C 제어를 위한 상수 정의 (HD44780 기반 I2C 백팩 스펙)
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LINE_1 = 0x80 # LCD RAM address for the 1st line
LINE_2 = 0xC0 # LCD RAM address for the 2nd line

LCD_BACKLIGHT  = 0x08  # On
# LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_DELAY = 0.0005
E_PULSE = 0.0005

class LCDController:
    def __init__(self):
        self.is_pi = IS_RASPBERRY_PI and (smbus is not None)
        self.addr = LCD_I2C_ADDRESS
        self.bus = None
        self._setup()

    def _setup(self):
        if self.is_pi:
            try:
                # 보통 라즈베리파이 2, 3, 4 등은 I2C 버스 1번을 사용
                self.bus = smbus.SMBus(1)
                self._lcd_byte(0x33, LCD_CMD) # 110011 Initialize
                self._lcd_byte(0x32, LCD_CMD) # 110010 Initialize
                self._lcd_byte(0x06, LCD_CMD) # 000110 Cursor move direction
                self._lcd_byte(0x0C, LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
                self._lcd_byte(0x28, LCD_CMD) # 001010 Data length, number of lines, font size
                self._lcd_byte(0x01, LCD_CMD) # 000001 Clear display
                time.sleep(E_DELAY)
                logger.info(f"I2C LCD 초기화 성공 (Address: {hex(self.addr)})")
            except Exception as e:
                logger.error(f"LCD 하드웨어 초기화 실패: {e}. Dummy 모드로 폴백합니다.")
                self.is_pi = False
        else:
            logger.info("[Dummy Mode] LCD 제어기 초기화 (비-라즈베리파이 환경)")

    def _lcd_byte(self, bits, mode):
        # 8비트 데이터를 4비트씩 쪼개서 I2C 백팩 칩셋(PCF8574) 형식으로 보냄
        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        # High bits
        self.bus.write_byte(self.addr, bits_high)
        self._lcd_toggle_enable(bits_high)

        # Low bits
        self.bus.write_byte(self.addr, bits_low)
        self._lcd_toggle_enable(bits_low)

    def _lcd_toggle_enable(self, bits):
        time.sleep(E_DELAY)
        self.bus.write_byte(self.addr, (bits | ENABLE))
        time.sleep(E_PULSE)
        self.bus.write_byte(self.addr, (bits & ~ENABLE))
        time.sleep(E_DELAY)

    def display_message(self, line1, line2=""):
        """LCD 화면에 텍스트를 출력합니다."""
        # 16자 보정
        line1 = line1.ljust(LCD_WIDTH, " ")[:LCD_WIDTH]
        line2 = line2.ljust(LCD_WIDTH, " ")[:LCD_WIDTH]

        if self.is_pi:
            try:
                self._lcd_byte(LINE_1, LCD_CMD)
                for char in line1:
                    self._lcd_byte(ord(char), LCD_CHR)

                self._lcd_byte(LINE_2, LCD_CMD)
                for char in line2:
                    self._lcd_byte(ord(char), LCD_CHR)
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
        if self.is_pi:
            try:
                self._lcd_byte(0x01, LCD_CMD)
                time.sleep(E_DELAY)
            except Exception as e:
                logger.error(f"LCD Clear 중 오류 발생: {e}")
        logger.info("[LCD 화면 Clear]")

    def cleanup(self):
        """종료 시 LCD 화면을 지웁니다."""
        self.clear()
