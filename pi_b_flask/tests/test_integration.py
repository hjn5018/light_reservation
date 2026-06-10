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
from pi_b_flask.app import app, change_system_state

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

    def send_socket_command(self, state_val):
        """Pi B의 TCP 소켓 포트로 상태 변경 패킷을 전송하는 헬퍼 메서드"""
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2.0)
        try:
            client.connect(('127.0.0.1', SOCKET_PORT))
            payload = {'state': state_val}
            client.sendall(json.dumps(payload).encode('utf-8'))
            
            response = client.recv(1024)
            return json.loads(response.decode('utf-8'))
        finally:
            client.close()

    def get_current_http_status(self):
        """Flask HTTP GET API를 통해 현재 상태 확인"""
        url = f"http://127.0.0.1:{FLASK_PORT}/api/status"
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('state')
        except Exception as e:
            self.fail(f"HTTP GET /api/status 실패: {e}")

    def test_full_scenario(self):
        """전체 예약 프로세스 통합 시나리오 테스트"""
        
        # 1. 초기 상태 확인 (기본값: idle)
        initial_state = self.get_current_http_status()
        print(f"\n[초기 검증] 현재 HTTP API 상태: {initial_state}")
        self.assertEqual(initial_state, 'idle')

        # 2. 대기 -> 예약 상태로 변경 요청 (소켓 통신 전송)
        print("\n[단계 2] 소켓 전송: state = reserved (예약)")
        res = self.send_socket_command('reserved')
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['current_state'], 'reserved')
        
        # HTTP API로 잘 동기화되었는지 교차 검증
        time.sleep(0.5)
        self.assertEqual(self.get_current_http_status(), 'reserved')

        # 3. 예약 -> 사용 상태로 변경 요청 (소켓 전송 ➔ 부저 상승음 트리거 검증 대상)
        print("\n[단계 3] 소켓 전송: state = in_use (사용 시작, 부저 상승음 작동)")
        res = self.send_socket_command('in_use')
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['current_state'], 'in_use')
        
        time.sleep(0.5)
        self.assertEqual(self.get_current_http_status(), 'in_use')

        # 4. 사용 -> 대기 상태로 변경 요청 (소켓 전송 ➔ 부저 하강음 트리거 검증 대상)
        print("\n[단계 4] 소켓 전송: state = idle (반납/대기 전환, 부저 하강음 작동)")
        res = self.send_socket_command('idle')
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['current_state'], 'idle')
        
        time.sleep(0.5)
        self.assertEqual(self.get_current_http_status(), 'idle')

if __name__ == '__main__':
    unittest.main()
