import time
import unittest
import socket
import json
import threading
import sys
import os
import urllib.request

# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pi_b_flask.config import SOCKET_PORT, FLASK_PORT
from pi_b_flask.app import app

class TestSystemIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n=== [통합 테스트] Flask 및 소켓 백엔드 가동 시작 ===")
        # Flask 앱을 백그라운드 스레드에서 구동 (use_reloader=False 필수)
        cls.flask_thread = threading.Thread(
            target=lambda: app.run(host='127.0.0.1', port=FLASK_PORT, debug=False, use_reloader=False)
        )
        cls.flask_thread.daemon = True
        cls.flask_thread.start()
        
        # 서버 소켓 바인딩 및 구동 대기를 위해 잠시 대기
        time.sleep(2.0)

    def send_socket_command(self, item_id, state_val, pin=None, action='change_state'):
        """Pi B의 TCP 소켓 포트로 제어 패킷을 전송하는 헬퍼 메서드"""
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2.0)
        try:
            client.connect(('127.0.0.1', SOCKET_PORT))
            payload = {
                'action': action,
                'item_id': item_id,
                'state': state_val,
                'pin': pin
            }
            client.sendall(json.dumps(payload).encode('utf-8'))
            
            response = client.recv(4096)
            return json.loads(response.decode('utf-8'))
        finally:
            client.close()

    def get_current_http_status(self, item_id):
        """Flask HTTP GET API를 통해 현재 상태 확인"""
        url = f"http://127.0.0.1:{FLASK_PORT}/api/status"
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('items', {})
                item_data = items.get(item_id, {})
                return item_data.get('state')
        except Exception as e:
            self.fail(f"HTTP GET /api/status 실패: {e}")

    def test_full_scenario(self):
        """전체 예약 프로세스 통합 시나리오 테스트 (다중 자원 & PIN 검증)"""
        target_item = 'meeting_room'
        
        # 1. 초기 상태 확인 (기본값: idle)
        initial_state = self.get_current_http_status(target_item)
        print(f"\n[초기 검증] 현재 HTTP API 상태: {initial_state}")
        self.assertEqual(initial_state, 'idle')

        # 2. 대기 -> 예약 상태로 변경 요청 (PIN 누락 시 오류 검증)
        print("\n[단계 2] 소켓 전송: PIN 누락 예약 시도 -> 실패 예상")
        res = self.send_socket_command(target_item, 'reserved', pin=None)
        self.assertEqual(res['status'], 'error')
        self.assertIn("PIN is required", res['message'])

        # 3. 대기 -> 예약 상태로 변경 요청 (성공 시나리오)
        print("\n[단계 3] 소켓 전송: PIN '1234'로 예약 시도 -> 성공 예상")
        res = self.send_socket_command(target_item, 'reserved', pin='1234')
        self.assertEqual(res['status'], 'success')
        
        time.sleep(0.5)
        self.assertEqual(self.get_current_http_status(target_item), 'reserved')

        # 4. 예약 -> 사용 상태로 변경 요청 (잘못된 PIN 검증)
        print("\n[단계 4] 소켓 전송: 잘못된 PIN '9999'로 사용 시도 -> 실패 예상")
        res = self.send_socket_command(target_item, 'in_use', pin='9999')
        self.assertEqual(res['status'], 'error')
        self.assertIn("Incorrect PIN number", res['message'])

        # 5. 예약 -> 사용 상태로 변경 요청 (성공 시나리오)
        print("\n[단계 5] 소켓 전송: 올바른 PIN '1234'로 사용 시도 -> 성공 예상")
        res = self.send_socket_command(target_item, 'in_use', pin='1234')
        self.assertEqual(res['status'], 'success')
        
        time.sleep(0.5)
        self.assertEqual(self.get_current_http_status(target_item), 'in_use')

        # 6. 사용 -> 대기 상태로 반납 요청 (성공 시나리오)
        print("\n[단계 6] 소켓 전송: 올바른 PIN '1234'로 반납(idle) 시도 -> 성공 예상")
        res = self.send_socket_command(target_item, 'idle', pin='1234')
        self.assertEqual(res['status'], 'success')
        
        time.sleep(0.5)
        self.assertEqual(self.get_current_http_status(target_item), 'idle')

    def test_focus_scenario(self):
        """하드웨어 모니터링 포커스 기기 지정 시나리오 테스트"""
        print("\n[포커스 테스트] 소켓 전송: 모니터링 대상 기기를 'stapler'로 변경")
        res = self.send_socket_command('stapler', None, action='set_focus')
        self.assertEqual(res['status'], 'success')
        
        # HTTP GET API를 통해 활성화된 포커스 아이템 정보가 변경되었는지 확인
        url = f"http://127.0.0.1:{FLASK_PORT}/api/status"
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.assertEqual(data.get('active_monitor_item'), 'stapler')
        except Exception as e:
            self.fail(f"HTTP GET /api/status 실패: {e}")

if __name__ == '__main__':
    unittest.main()
