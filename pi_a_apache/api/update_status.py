#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import socket
import urllib.request
import urllib.parse

# ----------------- 설정 정보 -----------------
# Pi B (소켓 및 Flask 서버)의 IP 주소
PI_B_IP = os.environ.get('PI_B_IP', '127.0.0.1')
PI_B_PORT = 50007      # TCP 소켓 제어 포트
PI_B_FLASK_PORT = 5000 # Flask REST API 포트
SOCKET_TIMEOUT = 3.0   # 초 단위 타임아웃
# ---------------------------------------------

def send_socket_message(payload):
    """
    Pi B의 TCP 소켓 서버로 제어 요청 페이로드를 JSON 형식으로 전송하고
    결과를 리턴받습니다.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(SOCKET_TIMEOUT)
    
    try:
        # Pi B로 소켓 연결 시도
        client_socket.connect((PI_B_IP, PI_B_PORT))
        
        # 보낼 메시지 가공
        message = json.dumps(payload).encode('utf-8')
        
        # 전송
        client_socket.sendall(message)
        
        # 응답 수신
        response_data = client_socket.recv(4096)  # 넉넉하게 수신 버퍼 설정
        if response_data:
            return json.loads(response_data.decode('utf-8'))
        else:
            return {'status': 'error', 'message': 'No response received from Pi B.'}
            
    except socket.timeout:
        return {'status': 'error', 'message': f'Connection timeout to Pi B ({PI_B_IP}:{PI_B_PORT})'}
    except ConnectionRefusedError:
        return {'status': 'error', 'message': f'Connection refused by Pi B. Is the socket server running?'}
    except Exception as e:
        return {'status': 'error', 'message': f'Socket communication error: {str(e)}'}
    finally:
        client_socket.close()

def get_current_state_from_flask():
    """
    Pi B의 Flask REST API를 조회하여 모든 기기의 현재 상태를 대행 조회합니다.
    """
    try:
        url = f"http://{PI_B_IP}:{PI_B_FLASK_PORT}/api/status"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=SOCKET_TIMEOUT) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data
            else:
                return {'status': 'error', 'message': f'HTTP status error: {response.status}'}
    except Exception as e:
        return {'status': 'error', 'message': f'HTTP request failed: {str(e)}'}

def main():
    # CGI 응답용 HTTP Header 출력
    print("Content-Type: application/json; charset=utf-8")
    print("Access-Control-Allow-Origin: *")  # CORS 허용
    print("Access-Control-Allow-Headers: Content-Type")
    print("Access-Control-Allow-Methods: POST, GET, OPTIONS")
    print("")  # 헤더와 바디 경계선

    # Preflight OPTIONS 요청 대응
    if os.environ.get('REQUEST_METHOD') == 'OPTIONS':
        sys.exit(0)

    # 데이터 파싱
    payload = {}
    method = os.environ.get('REQUEST_METHOD', 'GET')
    
    try:
        if method == 'POST':
            content_length = int(os.environ.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                post_data = sys.stdin.read(content_length)
                payload = json.loads(post_data)
        else:
            # GET 요청 시 쿼리 스트링 파싱
            query_string = os.environ.get('QUERY_STRING', '')
            parsed = urllib.parse.parse_qs(query_string)
            for key, val in parsed.items():
                if val:
                    payload[key] = val[0]
    except Exception as e:
        print(json.dumps({'status': 'error', 'message': f'Request parsing failed: {str(e)}'}))
        sys.exit(1)

    state_value = payload.get('state')
    action_value = payload.get('action')
    item_id = payload.get('item_id')
    
    # 상태 변경(state 제공) 또는 모니터링 지정(action=set_focus)이 아닌 경우 ➔ 조회 수행
    # 단, item_id만 주어지고 아무런 state나 action이 없어도 단순 조회를 수행합니다.
    if not state_value and action_value != 'set_focus':
        result = get_current_state_from_flask()
    else:
        # 변경 지시 ➔ 소켓을 통해 변경 패킷 전달
        # 소켓 통신용 파라미터 빌드
        socket_payload = {
            'item_id': item_id,
            'state': state_value,
            'pin': payload.get('pin'),
            'action': action_value or 'change_state'
        }
        result = send_socket_message(socket_payload)
    
    # 최종 결과 JSON 출력
    print(json.dumps(result))

if __name__ == '__main__':
    main()
