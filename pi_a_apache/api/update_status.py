#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import socket
import cgi
import urllib.request

# ----------------- 설정 정보 -----------------
# Pi B (소켓 및 Flask 서버)의 IP 주소
PI_B_IP = os.environ.get('PI_B_IP', '127.0.0.1')
PI_B_PORT = 50007      # TCP 소켓 제어 포트
PI_B_FLASK_PORT = 5000 # Flask REST API 포트
SOCKET_TIMEOUT = 3.0   # 초 단위 타임아웃
# ---------------------------------------------

def send_socket_message(state_value):
    """
    Pi B의 TCP 소켓 서버로 상태 변경 정보를 JSON 형식으로 전송하고
    결과를 리턴받습니다.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(SOCKET_TIMEOUT)
    
    try:
        # Pi B로 소켓 연결 시도
        client_socket.connect((PI_B_IP, PI_B_PORT))
        
        # 보낼 메시지 가공
        payload = {'state': state_value}
        message = json.dumps(payload).encode('utf-8')
        
        # 전송
        client_socket.sendall(message)
        
        # 응답 수신
        response_data = client_socket.recv(1024)
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
    Pi B의 Flask REST API를 조회하여 현재 상태를 대행 조회합니다.
    """
    try:
        url = f"http://{PI_B_IP}:{PI_B_FLASK_PORT}/api/status"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=SOCKET_TIMEOUT) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode('utf-8'))
                return {'status': 'success', 'current_state': res_data.get('state')}
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
            form = cgi.FieldStorage()
            for key in form.keys():
                payload[key] = form.getvalue(key)
    except Exception as e:
        print(json.dumps({'status': 'error', 'message': f'Request parsing failed: {str(e)}'}))
        sys.exit(1)

    state_value = payload.get('state')
    
    # state가 주어지지 않은 경우: 현재 상태 조회 동작 수행
    if not state_value:
        result = get_current_state_from_flask()
    else:
        # state가 주어진 경우: 소켓을 통해 변경 지시
        result = send_socket_message(state_value)
    
    # 최종 결과 JSON 출력
    print(json.dumps(result))

if __name__ == '__main__':
    main()
