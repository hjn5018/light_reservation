import os
import sys
import json
import time
import socket
import threading
import logging
from flask import Flask, jsonify, request

# 모듈 탐색 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pi_b_flask.config import (
    SOCKET_HOST, SOCKET_PORT, FLASK_PORT, DEBUG_MODE,
    JSON_DB_PATH, MASTER_PIN, RESERVATION_ITEMS
)
from pi_b_flask.hardware.led import LEDController
from pi_b_flask.hardware.lcd import LCDController
from pi_b_flask.hardware.buzzer import BuzzerController

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PiB_App")

app = Flask(__name__)

# 뮤텍스 락 설정
state_lock = threading.Lock()

# 하드웨어 인스턴스 초기화
led_ctrl = LEDController()
lcd_ctrl = LCDController()
buzzer_ctrl = BuzzerController()

# ================= JSON 파일 DB 관리 함수 =================

def load_db():
    """파일 DB에서 시스템 상태 데이터를 가져옵니다."""
    if not os.path.exists(JSON_DB_PATH):
        # 파일이 없을 시 기본값 구조 생성
        logger.info("JSON DB 파일이 존재하지 않아 초기화 중...")
        initial_data = {
            "active_monitor_item": "meeting_room",
            "items": {item_id: {"state": "idle", "pin": None, "status_changed_at": None} for item_id in RESERVATION_ITEMS}
        }
        save_db(initial_data)
        return initial_data
        
    try:
        with open(JSON_DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 설정(RESERVATION_ITEMS)에 있는 모든 아이템이 누락 없이 DB에 존재하도록 정합성 맞춤
            dirty = False
            if "active_monitor_item" not in data:
                data["active_monitor_item"] = list(RESERVATION_ITEMS.keys())[0]
                dirty = True
            if "items" not in data:
                data["items"] = {}
                dirty = True
            for item_id in RESERVATION_ITEMS:
                if item_id not in data["items"]:
                    data["items"][item_id] = {"state": "idle", "pin": None, "status_changed_at": None}
                    dirty = True
            if dirty:
                save_db(data)
            return data
    except Exception as e:
        logger.error(f"JSON DB 파일 로드 중 오류 발생: {e}")
        # 오류 발생 시 메모리상 복구용 기본값 반환
        return {
            "active_monitor_item": list(RESERVATION_ITEMS.keys())[0],
            "items": {item_id: {"state": "idle", "pin": None, "status_changed_at": None} for item_id in RESERVATION_ITEMS}
        }

def save_db(data):
    """파일 DB에 시스템 상태 데이터를 안전하게 기록합니다."""
    try:
        with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"JSON DB 파일 저장 중 오류 발생: {e}")
        raise e

# 초기 하드웨어 물리 상태 갱신
def sync_physical_hardware():
    """현재 DB 상태에 기하여 물리 하드웨어 지시값을 갱신합니다."""
    data = load_db()
    active_item_id = data.get("active_monitor_item")
    item_data = data["items"].get(active_item_id)
    if item_data:
        item_name = RESERVATION_ITEMS[active_item_id]["name"]
        led_ctrl.set_state(item_data["state"])
        lcd_ctrl.display_status(item_data["state"], item_name)

# 프로그램 시작 시 1회 싱크
sync_physical_hardware()

# ================= 핵심 비즈니스 로직 제어 함수 =================

def change_item_state(item_id, new_state, input_pin=None):
    """
    각 아이템의 상태 전이 유효성을 검사하고 안전하게 전환합니다.
    """
    if item_id not in RESERVATION_ITEMS:
        logger.warning(f"존재하지 않는 아이템 ID에 대한 제어 요청 거절: {item_id}")
        return False, "Invalid item_id"

    new_state = new_state.strip().lower()
    state_mapping = {
        '대기': 'idle', 'idle': 'idle', 'available': 'idle',
        '예약': 'reserved', 'reserved': 'reserved',
        '사용': 'in_use', 'in_use': 'in_use', 'occupied': 'in_use'
    }
    normalized_state = state_mapping.get(new_state)
    if not normalized_state:
        return False, f"Invalid state value: {new_state}"

    # PIN 검증 편의성을 위해 문자열로 통일
    if input_pin is not None:
        input_pin = str(input_pin).strip()

    with state_lock:
        db = load_db()
        item = db["items"][item_id]
        current_state = item["state"]
        saved_pin = item.get("pin")
        active_monitor_item = db.get("active_monitor_item")

        if current_state == normalized_state:
            return True, "No state change required"

        # 타입 불일치(정수 vs 문자열)로 인한 인증 오작동 방지를 위해 저장된 PIN을 문자열로 표준화
        saved_pin_str = str(saved_pin).strip() if saved_pin is not None else None
        
        logger.info(f"[PIN 인증 시도] 아이템: {item_id}, 입력 PIN: '{input_pin}', 저장 PIN: '{saved_pin_str}', 마스터 PIN: '{MASTER_PIN}'")

        # 상태 전환 조건 체크 및 PIN 확인
        # 1) 대기 -> 예약
        if current_state == 'idle' and normalized_state == 'reserved':
            if not input_pin:
                return False, "PIN is required for reservation"
            item["pin"] = input_pin
            
        # 2) 예약 -> 사용
        elif current_state == 'reserved' and normalized_state == 'in_use':
            if not input_pin:
                return False, "PIN is required to change to in_use"
            if input_pin != saved_pin_str and input_pin != MASTER_PIN:
                logger.warning(f"[인증 실패] 사용시작 거절 - 입력 PIN '{input_pin}'이 저장 PIN '{saved_pin_str}' 및 마스터 PIN '{MASTER_PIN}'과 일치하지 않습니다.")
                return False, "Incorrect PIN number"
            
        # 3) 사용 또는 예약 -> 대기 (반납/취소)
        elif normalized_state == 'idle':
            # 예약 취소 또는 사용 종료 시 PIN 확인 필요
            if not input_pin:
                return False, "PIN is required to release or cancel"
            if input_pin != saved_pin_str and input_pin != MASTER_PIN:
                logger.warning(f"[인증 실패] 반납/취소 거절 - 입력 PIN '{input_pin}'이 저장 PIN '{saved_pin_str}' 및 마스터 PIN '{MASTER_PIN}'과 일치하지 않습니다.")
                return False, "Incorrect PIN number"
            item["pin"] = None

        # 4) 예외적인 전이 시도 차단 (대기 -> 사용 바로 가기 등)
        else:
            return False, f"Invalid state transition from {current_state} to {normalized_state}"

        # 상태 전환 처리
        logger.info(f"[{RESERVATION_ITEMS[item_id]['name']}] 상태 전환: {current_state} ➔ {normalized_state}")
        item["state"] = normalized_state
        item["status_changed_at"] = time.time()
        try:
            save_db(db)
        except Exception as e:
            return False, f"Database write failed: {str(e)}"

        # 물리 하드웨어 연동 (현재 모니터링 지정 대상 아이템일 경우만 반응)
        if item_id == active_monitor_item:
            # 부저 멜로디 조건 검사
            if current_state == 'reserved' and normalized_state == 'in_use':
                buzzer_ctrl.play_reserved_to_in_use()
            elif current_state == 'in_use' and normalized_state == 'idle':
                buzzer_ctrl.play_in_use_to_idle()

            led_ctrl.set_state(normalized_state)
            item_name = RESERVATION_ITEMS[item_id]["name"]
            lcd_ctrl.display_status(normalized_state, item_name)

        return True, "Success"

def set_active_monitor_item(item_id):
    """물리 하드웨어 모니터링 지정 대상을 전환합니다."""
    if item_id not in RESERVATION_ITEMS:
        return False, "Invalid item_id"

    with state_lock:
        db = load_db()
        db["active_monitor_item"] = item_id
        save_db(db)
        
        # 즉시 하드웨어 출력 동기화
        item_data = db["items"][item_id]
        item_name = RESERVATION_ITEMS[item_id]["name"]
        led_ctrl.set_state(item_data["state"])
        lcd_ctrl.display_status(item_data["state"], item_name)
        
        logger.info(f"하드웨어 모니터링 대상 전환 완료: -> [{item_name}]")
        return True, "Success"

# ================= 백그라운드 자동 만료 타이머 스케줄러 =================

def auto_expiry_scheduler():
    """
    백그라운드에서 주기적으로(1초 간격) 상태 데이터를 검사하여
    고정 예약 유지 시간 초과 또는 고정 이용 시간 초과 시 자동으로 대기 상태로 전환합니다.
    """
    logger.info("자동 만료 타이머 스케줄러 스레드 구동 시작")
    while True:
        try:
            time.sleep(1.0)
            
            with state_lock:
                db = load_db()
                dirty = False
                active_monitor_item = db.get("active_monitor_item")
                
                for item_id, item_data in db["items"].items():
                    state = item_data["state"]
                    changed_at = item_data["status_changed_at"]
                    
                    if state == 'idle' or changed_at is None:
                        continue
                        
                    elapsed = time.time() - changed_at
                    
                    # 1) 예약 만료 처리 (No-show 방지)
                    if state == 'reserved':
                        limit = RESERVATION_ITEMS[item_id]["reservation_timeout"]
                        if elapsed >= limit:
                            logger.info(f"[{RESERVATION_ITEMS[item_id]['name']}] 예약 대기 시간 만료 (No-show) -> 자동 대기 전환")
                            item_data["state"] = 'idle'
                            item_data["pin"] = None
                            item_data["status_changed_at"] = time.time()
                            dirty = True
                            
                            # 만약 모니터링 대상 아이템이면 하드웨어 갱신
                            if item_id == active_monitor_item:
                                led_ctrl.set_state('idle')
                                lcd_ctrl.display_status('idle', RESERVATION_ITEMS[item_id]["name"])
                                
                    # 2) 사용 만료 처리 (자동 반납)
                    elif state == 'in_use':
                        limit = RESERVATION_ITEMS[item_id]["usage_duration"]
                        if elapsed >= limit:
                            logger.info(f"[{RESERVATION_ITEMS[item_id]['name']}] 최대 사용 시간 완료 -> 자동 대기 반납")
                            item_data["state"] = 'idle'
                            item_data["pin"] = None
                            item_data["status_changed_at"] = time.time()
                            dirty = True
                            
                            # 만약 모니터링 대상 아이템이면 하드웨어 갱신 및 반납 멜로디 재생
                            if item_id == active_monitor_item:
                                buzzer_ctrl.play_in_use_to_idle()
                                led_ctrl.set_state('idle')
                                lcd_ctrl.display_status('idle', RESERVATION_ITEMS[item_id]["name"])
                
                if dirty:
                    save_db(db)
                    
        except Exception as e:
            logger.error(f"스케줄러 스레드 루프 내 오류 발생: {e}")

# ================= Flask REST API 엔드포인트 구현 =================

@app.route('/api/status', methods=['GET'])
def get_status():
    """모든 예약 대상 아이템 목록 및 물리 모니터링 상태 조회 API"""
    with state_lock:
        db = load_db()
        response_items = {}
        now = time.time()
        
        for item_id, item_data in db["items"].items():
            state = item_data["state"]
            changed_at = item_data["status_changed_at"]
            
            # 남은 유효 시간 계산 (초 단위)
            remaining_seconds = 0
            if state == 'reserved' and changed_at:
                limit = RESERVATION_ITEMS[item_id]["reservation_timeout"]
                remaining_seconds = max(0, int(limit - (now - changed_at)))
            elif state == 'in_use' and changed_at:
                limit = RESERVATION_ITEMS[item_id]["usage_duration"]
                remaining_seconds = max(0, int(limit - (now - changed_at)))
                
            response_items[item_id] = {
                "name": RESERVATION_ITEMS[item_id]["name"],
                "state": state,
                "has_pin": item_data.get("pin") is not None,
                "usage_duration": RESERVATION_ITEMS[item_id]["usage_duration"],
                "reservation_timeout": RESERVATION_ITEMS[item_id]["reservation_timeout"],
                "remaining_seconds": remaining_seconds
            }
            
        return jsonify({
            'status': 'success',
            'active_monitor_item': db.get("active_monitor_item"),
            'items': response_items
        }), 200

@app.route('/api/status', methods=['POST'])
def post_status():
    """HTTP POST를 이용한 상태 직접 변경 및 모니터링 대상 변경 API"""
    data = request.get_json() or {}
    action = data.get('action', 'change_state')
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({'status': 'error', 'message': 'item_id 필드가 누락되었습니다.'}), 400
        
    if action == 'set_focus':
        success, msg = set_active_monitor_item(item_id)
        if success:
            return jsonify({'status': 'success', 'message': msg}), 200
        else:
            return jsonify({'status': 'error', 'message': msg}), 400
            
    elif action == 'change_state' or not action:
        new_state = data.get('state')
        pin = data.get('pin')
        
        if not new_state:
            return jsonify({'status': 'error', 'message': 'state 필드가 누락되었습니다.'}), 400
            
        success, msg = change_item_state(item_id, new_state, pin)
        if success:
            # 상태 변경 후 전체 갱신된 데이터를 응답하여 클라이언트 실시간 동기화 지원
            return jsonify({'status': 'success', 'message': '상태 변경 완료'}), 200
        else:
            return jsonify({'status': 'error', 'message': msg}), 400
            
    return jsonify({'status': 'error', 'message': '유효하지 않은 action입니다.'}), 400

# ================= TCP 소켓 서버 구현 =================

def run_socket_server():
    """Pi A로부터 접속을 수락하는 TCP 소켓 서버 스레드 함수"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((SOCKET_HOST, SOCKET_PORT))
        server_socket.listen(5)
        logger.info(f"TCP 소켓 서버 가동 중 - 포트 {SOCKET_PORT}에서 연결 대기 중...")
        
        while True:
            client_conn, client_addr = server_socket.accept()
            logger.info(f"Pi A 소켓 연결 수락: {client_addr}")
            
            # 클라이언트 처리를 독립 스레드로 위임
            t = threading.Thread(target=handle_socket_client, args=(client_conn,))
            t.daemon = True
            t.start()
            
    except Exception as e:
        logger.critical(f"소켓 서버 오류 발생 및 스레드 종료: {e}")
    finally:
        server_socket.close()

def handle_socket_client(client_conn):
    """소켓으로 수신된 상태 변경 및 모니터링 지정 요청을 파싱하고 로직을 수행합니다."""
    try:
        data = client_conn.recv(2048)  # 다중 정보 수신을 위해 수신 버퍼 넉넉히 설정
        if not data:
            return
            
        try:
            message_str = data.decode('utf-8')
            logger.info(f"소켓 수신 데이터: {message_str}")
            message = json.loads(message_str)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            error_response = {'status': 'error', 'message': f'Invalid format: {e}'}
            client_conn.sendall(json.dumps(error_response).encode('utf-8'))
            return

        action = message.get('action', 'change_state')
        item_id = message.get('item_id')
        
        if not item_id:
            error_response = {'status': 'error', 'message': 'item_id parameter required'}
            client_conn.sendall(json.dumps(error_response).encode('utf-8'))
            return

        if action == 'set_focus':
            success, msg = set_active_monitor_item(item_id)
            if success:
                response = {'status': 'success', 'message': msg}
            else:
                response = {'status': 'error', 'message': msg}
                
        elif action == 'change_state' or not action:
            new_state = message.get('state')
            pin = message.get('pin')
            
            if not new_state:
                error_response = {'status': 'error', 'message': 'state parameter required'}
                client_conn.sendall(json.dumps(error_response).encode('utf-8'))
                return
                
            success, msg = change_item_state(item_id, new_state, pin)
            if success:
                response = {'status': 'success', 'message': '상태 변경 완료'}
            else:
                response = {'status': 'error', 'message': msg}
        else:
            response = {'status': 'error', 'message': f'Unknown action: {action}'}
            
        client_conn.sendall(json.dumps(response).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"소켓 클라이언트 통신 처리 에러: {e}")
    finally:
        client_conn.close()

# ================= 애플리케이션 시작 및 종료 정리 =================

def startup_setup():
    """앱 시작 시 소켓 서버 및 자동 만료 타이머 스레드를 백그라운드 구동합니다."""
    # 1. 소켓 서버 스레드 시작
    socket_thread = threading.Thread(target=run_socket_server)
    socket_thread.daemon = True
    socket_thread.start()
    logger.info("소켓 백그라운드 리스너 스레드 시작됨")
    
    # 2. 자동 만료 스케줄러 스레드 시작
    scheduler_thread = threading.Thread(target=auto_expiry_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logger.info("만료 스케줄러 백그라운드 스레드 시작됨")

# Flask 기동 전에 데몬 스레드 구동
startup_setup()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=DEBUG_MODE, use_reloader=False)
    finally:
        logger.info("애플리케이션 종료 중. GPIO 자원을 반환합니다.")
        led_ctrl.cleanup()
        lcd_ctrl.cleanup()
        buzzer_ctrl.cleanup()
