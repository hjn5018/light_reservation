#!/usr/bin/env bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    Smart Reservation System 자동 설치/설정 도구   ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Root 권한 체크
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}오류: 이 스크립트는 sudo 권한(root)으로 실행해야 합니다.${NC}"
  echo -e "예: sudo bash setup.sh"
  exit 1
fi

# 프로젝트 루트 경로 확보
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

show_menu() {
  echo -e "이 라즈베리 파이의 역할을 선택해 주세요:"
  echo -e "  ${GREEN}1)${NC} Pi A (Apache 웹 서버 + CGI 소켓 클라이언트)"
  echo -e "  ${GREEN}2)${NC} Pi B (Flask API + 하드웨어 제어 소켓 서버)"
  echo -e "  ${GREEN}3)${NC} 종료"
  read -p "선택 (1-3): " CHOICE
}

setup_pi_a() {
  echo -e "\n${YELLOW}[Pi A] 설정을 시작합니다...${NC}"
  
  # 1. 아파치 및 파이썬 관련 패키지 설치
  echo -e "${BLUE}1/4. 시스템 패키지 설치 중 (Apache2, Python3)...${NC}"
  apt-get update
  apt-get install -y apache2 python3
  
  # 2. CGI 모듈 활성화
  echo -e "${BLUE}2/4. Apache CGI 모듈 활성화...${NC}"
  a2enmod cgi
  systemctl restart apache2
  
  # 3. Pi B의 IP 주소 설정 입력
  echo -e "${BLUE}3/4. Pi B(소켓 서버) 연동 설정...${NC}"
  read -p "연동할 Pi B의 IP 주소를 입력하세요 (기본값: 127.0.0.1): " PIB_IP
  if [ -z "$PIB_IP" ]; then
    PIB_IP="127.0.0.1"
  fi
  
  # update_status.py 파일에 IP 주소 주입
  CGI_SOURCE="${PROJECT_DIR}/pi_a_apache/api/update_status.py"
  if [ -f "$CGI_SOURCE" ]; then
    sed -i "s/PI_B_IP = os.environ.get('PI_B_IP', '127.0.0.1')/PI_B_IP = os.environ.get('PI_B_IP', '${PIB_IP}')/g" "$CGI_SOURCE"
    echo -e "-> Pi B 연동 IP를 ${GREEN}${PIB_IP}${NC}로 설정 완료했습니다."
  else
    echo -e "${RED}경고: update_status.py 파일을 찾을 수 없습니다.${NC}"
  fi
  
  # 4. 웹 파일 및 CGI 파일 복사 및 권한 부여
  echo -e "${BLUE}4/4. 웹 리소스 배포 중...${NC}"
  
  # 웹 루트 디렉토리로 HTML/JS 파일 복사
  cp "${PROJECT_DIR}/pi_a_apache/index.html" /var/www/html/
  cp "${PROJECT_DIR}/pi_a_apache/app.js" /var/www/html/
  
  # CGI 디렉토리 생성 및 CGI 복사
  mkdir -p /var/www/html/api
  cp "$CGI_SOURCE" /var/www/html/api/
  chmod +x /var/www/html/api/update_status.py
  
  # CGI가 작동할 수 있도록 Apache configuration에 ExecCGI 추가 권한 부여
  # (기본적으로 /var/www/html/api 내에서 .py 확장자의 CGI 실행을 활성화하는 임시 설정 추가)
  APACHE_CONF="/etc/apache2/conf-available/reservation-cgi.conf"
  cat <<EOF > "$APACHE_CONF"
<Directory "/var/www/html/api">
    Options +ExecCGI
    AddHandler cgi-script .py
    Require all granted
</Directory>
EOF
  a2enconf reservation-cgi
  systemctl reload apache2
  
  echo -e "${GREEN}✔ Pi A (Apache) 설정 완료!${NC}"
  echo -e "브라우저에서 ${BLUE}http://$(hostname -I | awk '{print $1}')${NC} 로 접속하여 시스템을 테스트해 보세요."
}

setup_pi_b() {
  echo -e "\n${YELLOW}[Pi B] 설정을 시작합니다...${NC}"
  
  # 1. 하드웨어 관련 라이브러리 및 PIP 설치
  echo -e "${BLUE}1/3. 필수 시스템 라이브러리 설치 중 (GPIO, I2C)...${NC}"
  apt-get update
  apt-get install -y python3-pip python3-rpi.gpio python3-smbus i2c-tools
  
  # 2. 파이썬 의존성 패키지 설치
  echo -e "${BLUE}2/3. Python 의존성 라이브러리 설치 (Flask)...${NC}"
  pip3 install -r "${PROJECT_DIR}/pi_b_flask/requirements.txt" --break-system-packages 2>/dev/null || pip3 install -r "${PROJECT_DIR}/pi_b_flask/requirements.txt"
  
  # 3. Systemd 서비스 등록 (백그라운드 자동 실행용)
  echo -e "${BLUE}3/3. Flask & Socket 서버 백그라운드 서비스 등록...${NC}"
  
  SERVICE_FILE="/etc/systemd/system/reservation_pib.service"
  cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Pi B Reservation Flask and Socket Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/pi_b_flask/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable reservation_pib.service
  systemctl start reservation_pib.service
  
  echo -e "${GREEN}✔ Pi B (Flask & Hardware) 설정 완료 및 백그라운드 서비스 구동 성공!${NC}"
  echo -e "서비스 로그는 다음 명령어로 확인할 수 있습니다: ${BLUE}sudo journalctl -u reservation_pib.service -f${NC}"
}

# 메인 실행 흐름
show_menu

case $CHOICE in
  1)
    setup_pi_a
    ;;
  2)
    setup_pi_b
    ;;
  3)
    echo -e "${YELLOW}설치를 취소했습니다.${NC}"
    exit 0
    ;;
  *)
    echo -e "${RED}잘못된 입력입니다.${NC}"
    exit 1
    ;;
esac
