import time
import unittest
import sys
import os

# 부모 디렉토리를 sys.path에 추가하여 pi_b_flask 모듈을 찾을 수 있도록 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pi_b_flask.hardware.led import LEDController
from pi_b_flask.hardware.lcd import LCDController
from pi_b_flask.hardware.buzzer import BuzzerController

class TestHardwareIntegration(unittest.TestCase):
    def setUp(self):
        print("\n=== 하드웨어 테스트 설정 시작 ===")
        self.led = LEDController()
        self.lcd = LCDController()
        self.buzzer = BuzzerController()
        print("================================")

    def tearDown(self):
        print("\n=== 하드웨어 리소스 정리 ===")
        self.led.cleanup()
        self.lcd.cleanup()
        self.buzzer.cleanup()
        print("==========================")

    def test_state_transitions(self):
        """대기 -> 예약 -> 사용 -> 대기 상태 전환 흐름을 순차적으로 테스트합니다."""
        
        # 1. 초기 상태: 대기 (Idle)
        print("\n--- [시나리오 1] 초기 상태: 대기 (LED: 초록, LCD: Available) ---")
        self.led.set_state('대기')
        self.lcd.display_status('대기')
        time.sleep(1)

        # 2. 대기 -> 예약 (Reserved)
        print("\n--- [시나리오 2] 대기 -> 예약 (LED: 노랑, LCD: Reserved) ---")
        self.led.set_state('예약')
        self.lcd.display_status('예약')
        time.sleep(1)

        # 3. 예약 -> 사용 (In Use)
        # 요구사항: 예약 -> 사용 상태로 변경될 때 부저 3가지 상승음 출력
        print("\n--- [시나리오 3] 예약 -> 사용 (부저: 상승음, LED: 빨강, LCD: In Use) ---")
        self.buzzer.play_reserved_to_in_use()
        self.led.set_state('사용')
        self.lcd.display_status('사용')
        time.sleep(1)

        # 4. 사용 -> 대기 (Idle)
        # 요구사항: 사용 -> 대기로 상태 변경될 때 부저 다른 3가지 하강음 출력
        print("\n--- [시나리오 4] 사용 -> 대기 (부저: 하강음, LED: 초록, LCD: Available) ---")
        self.buzzer.play_in_use_to_idle()
        self.led.set_state('대기')
        self.lcd.display_status('대기')
        time.sleep(1)

if __name__ == '__main__':
    unittest.main()
