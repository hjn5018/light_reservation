import os
import sys
import json
import socket
import threading
import logging
from flask import Flask, jsonify, request

# 모듈 탐색 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pi_b_flask.config import SOCKET_HOST, SOCKET_PORT, FLASK_PORT, DEBUG_MODE
from pi_b_flask.hardware.led import LEDController
from pi_b_flask.hardware.lcd import LCDController
from pi_b_flask.hardware.buzzer import BuzzerController

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PiB_App")

app = Flask(__name__)

# 전역 상태 관리 및 하드웨어 인스턴스 초기화
current_state = 'idle'  # 기본 상태: 대기 (idle)
state_lock = threading.Lock()

led_ctrl = LEDController()
lcd_ctrl = LCDController()
buzzer_ctrl = BuzzerController()

# 초기 상태 하드웨어 반영
led_ctrl.set_state(current_state)
lcd_ctrl.display_status(current_state)

def change_system_state(new_state):
    """
    안전하게 상태를 전환하고 하드웨어를 제어합니다.
    """
    global current_state
    new_state = new_state.strip().lower()
    
    # 상태값 정규화 (대기/예약/사용 한글 처리 포함)
    state_mapping = {
        '대기': 'idle', 'idle': 'idle', 'available': 'idle',
        '예약': 'reserved', 'reserved': 'reserved',
        '사용': 'in_use', 'in_use': 'in_use', 'occupied': 'in_use'
    }
    
    normalized_state = state_mapping.get(new_state)
    if not normalized_state:
        logger.warning(f"잘못된 상태 값 무시됨: {new_state}")
        return False, current_state

    with state_lock:
        prev_state = current_state
        if prev_state == normalized_state:
            # 상태 변화가 없는 경우 제어 건너뜀
            return True, current_state

        logger.info(f"시스템 상태 전환 요청: {prev_state} ➔ {normalized_state}")
        
        # 1. 부저 멜로디 재생 (상태 전이 조건 검사)
        # 요구사항: 예약('reserved') -> 사용('in_use')
        if prev_state == 'reserved' and normalized_state == 'in_use':
            buzzer_ctrl.play_reserved_to_in_use()
        # 요구사항: 사용('in_use') -> 대기('idle')
        elif prev_state == 'in_use' and normalized_state == 'idle':
            buzzer_ctrl.play_in_use_to_idle()

        # 2. LED 갱신
        led_ctrl.set_state(normalized_state)
        
        # 3. LCD 갱신
        lcd_ctrl.display_status(normalized_state)
        
        current_state = normalized_state
        return True, current_state

# ================= Flask REST API Endpoints =================

@app.route('/api/status', methods=['GET'])
def get_status():
    """현재 시스템 상태 조회 API"""
    with state_lock:
        return jsonify({
            'status': 'success',
            'state': current_state
        }), 200

@app.route('/api/status', methods=['POST'])
def post_status():
    """HTTP POST를 이용한 상태 직접 변경 API (보완용)"""
    data = request.get_json() or {}
    new_state = data.get('state')
    
    if not new_state:
        return jsonify({'status': 'error', 'message': 'state 필드가 누락되었습니다.'}), 400
        
    success, current = change_system_state(new_state)
    if success:
        return jsonify({'status': 'success', 'current_state': current}), 200
    else:
        return jsonify({'status': 'error', 'message': '유효하지 않은 상태 값입니다.'}), 400

# ================= TCP Socket Server =================

def run_socket_server():
    """Pi A로부터 접속을 수락하는 TCP 소켓 서버 스레드 함수"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 포트 재사용 설정
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((SOCKET_HOST, SOCKET_PORT))
        server_socket.listen(5)
        logger.info(f"TCP 소켓 서버 가동 중 - 포트 {SOCKET_PORT}에서 연결 대기 중...")
        
        while True:
            client_conn, client_addr = server_socket.accept()
            logger.info(f"Pi A 소켓 연결 수락: {client_addr}")
            
            # 클라이언트 처리를 스레드로 분할해 소켓 수락 블로킹 최소화
            t = threading.Thread(target=handle_socket_client, args=(client_conn,))
            t.daemon = True
            t.start()
            
    except Exception as e:
        logger.critical(f"소켓 서버 오류 발생 및 스레드 종료: {e}")
    finally:
        server_socket.close()

def handle_socket_client(client_conn):
    """소켓으로 전송된 상태 패킷을 파싱하고 하드웨어를 제어합니다."""
    try:
        # 단일 메시지 크기는 크지 않으므로 1024바이트 수신
        data = client_conn.recv(1024)
        if not data:
            return
            
        # 디코딩 및 JSON 파싱
        try:
            message_str = data.decode('utf-8')
            logger.info(f"소켓 수신 데이터: {message_str}")
            message = json.loads(message_str)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            error_response = {'status': 'error', 'message': f'Invalid format: {e}'}
            client_conn.sendall(json.dumps(error_response).encode('utf-8'))
            return

        new_state = message.get('state')
        if not new_state:
            error_response = {'status': 'error', 'message': 'state parameter required'}
            client_conn.sendall(json.dumps(error_response).encode('utf-8'))
            return

        # 시스템 상태 반영
        success, final_state = change_system_state(new_state)
        
        if success:
            response = {'status': 'success', 'current_state': final_state}
        else:
            response = {'status': 'error', 'message': f'Failed to set state to {new_state}'}
            
        client_conn.sendall(json.dumps(response).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"소켓 클라이언트 통신 처리 에러: {e}")
    finally:
        client_conn.close()

# ================= 애플리케이션 시작 및 종료 정리 =================

def startup_setup():
    """앱 시작 시 소켓 서버 스레드를 구동합니다."""
    socket_thread = threading.Thread(target=run_socket_server)
    socket_thread.daemon = True
    socket_thread.start()
    logger.info("소켓 백그라운드 리스너 스레드 시작됨")

# Flask 기동 전에 소켓 서버 구동
startup_setup()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=DEBUG_MODE, use_reloader=False)
    finally:
        logger.info("애플리케이션 종료 중. GPIO 자원을 반환합니다.")
        led_ctrl.cleanup()
        lcd_ctrl.cleanup()
        buzzer_ctrl.cleanup()
