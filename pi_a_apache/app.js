// API 엔드포인트 설정 (동일 도메인의 CGI 경로)
const API_URL = 'api/update_status.py';

// DOM 요소 획득
const statusCard = document.getElementById('statusCard');
const statusBadge = document.getElementById('statusBadge');
const statusIcon = document.getElementById('statusIcon');
const statusTitle = document.getElementById('statusTitle');
const statusValue = document.getElementById('statusValue');
const statusFocusedItem = document.getElementById('statusFocusedItem');
const buzzerAlert = document.getElementById('buzzerAlert');
const buzzerText = document.getElementById('buzzerText');
const resourceGrid = document.getElementById('resourceGrid');

// PIN 모달 관련 DOM 요소
const pinModal = document.getElementById('pinModal');
const modalTitle = document.getElementById('modalTitle');
const modalDesc = document.getElementById('modalDesc');
const modalIcon = document.getElementById('modalIcon');
const pinInput = document.getElementById('pinInput');
const modalConfirmBtn = document.getElementById('modalConfirmBtn');

// 상태 데이터 캐시 변수
let localStateData = {
    active_monitor_item: '',
    items: {}
};
let prevFocusedState = ''; // 모니터링 대상 기기의 이전 상태 기억 (부저 시각 효과용)

// 상태별 스타일 정의
const statusConfig = {
    idle: {
        title: 'AVAILABLE',
        text: '대기 (Available)',
        icon: 'fa-solid fa-circle-check',
        color: '#10b981',
        glow: '0 8px 32px rgba(16, 185, 129, 0.15)',
        badgeClass: 'badge-idle'
    },
    reserved: {
        title: 'RESERVED',
        text: '예약 (Reserved)',
        icon: 'fa-solid fa-hourglass-half',
        color: '#f59e0b',
        glow: '0 8px 32px rgba(245, 158, 11, 0.15)',
        badgeClass: 'badge-reserved'
    },
    in_use: {
        title: 'IN USE',
        text: '사용 (In Use)',
        icon: 'fa-solid fa-user-lock',
        color: '#ef4444',
        glow: '0 8px 32px rgba(239, 68, 68, 0.15)',
        badgeClass: 'badge-in_use'
    }
};

/**
 * 초 단위 숫자를 HH:MM:SS 또는 MM:SS 문자열로 변환합니다.
 */
function formatTime(seconds) {
    if (seconds <= 0) return '00:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    
    const mm = m.toString().padStart(2, '0');
    const ss = s.toString().padStart(2, '0');
    
    if (h > 0) {
        const hh = h.toString().padStart(2, '0');
        return `${hh}:${mm}:${ss}`;
    }
    return `${mm}:${ss}`;
}

/**
 * 상단 메인 하드웨어 모니터링 카드 UI 갱신
 */
function updateMainFocusCard(activeItemId, itemData) {
    if (!itemData) {
        statusValue.textContent = '정보 없음';
        statusFocusedItem.textContent = '모니터링 대상: -';
        return;
    }
    
    const state = itemData.state;
    const config = statusConfig[state] || statusConfig['idle'];
    
    statusTitle.textContent = config.title;
    statusTitle.style.color = config.color;
    statusValue.textContent = config.text;
    statusFocusedItem.textContent = `모니터링 기기: ${itemData.name}`;
    
    statusIcon.className = `${config.icon} status-icon`;
    statusIcon.style.color = config.color;
    statusIcon.style.filter = `drop-shadow(0 0 12px ${config.color})`;
    
    statusCard.style.boxShadow = config.glow;
    statusCard.style.borderTop = `4px solid ${config.color}`;
    
    // 부저 멜로디 시각 애니메이션 제어
    if (prevFocusedState === 'reserved' && state === 'in_use') {
        triggerBuzzerAnimation('reserved_to_in_use');
    } else if (prevFocusedState === 'in_use' && state === 'idle') {
        triggerBuzzerAnimation('in_use_to_idle');
    }
    prevFocusedState = state;
}

/**
 * 부저 작동 알림 애니메이션 표시
 */
function triggerBuzzerAnimation(transitionType) {
    if (transitionType === 'reserved_to_in_use') {
        buzzerText.textContent = "물리 부저: 예약 ➔ 사용 (상승음 ♪ 도-미-솔)";
        buzzerAlert.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        buzzerAlert.className = "buzzer-alert show";
    } else if (transitionType === 'in_use_to_idle') {
        buzzerText.textContent = "물리 부저: 사용 ➔ 대기 (하강음 ♬ 솔-미-도)";
        buzzerAlert.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        buzzerAlert.className = "buzzer-alert show";
    }

    // 3.5초 후 자동 숨김
    setTimeout(() => {
        buzzerAlert.className = "buzzer-alert";
    }, 3500);
}

/**
 * 전체 자원 대시보드 그리드 렌더링
 */
function renderResourceDashboard() {
    const items = localStateData.items;
    const activeMonitorId = localStateData.active_monitor_item;
    
    resourceGrid.innerHTML = '';
    
    Object.keys(items).forEach(itemId => {
        const item = items[itemId];
        const state = item.state;
        const config = statusConfig[state] || statusConfig['idle'];
        const isFocused = itemId === activeMonitorId;
        
        // 카드 엘리먼트 생성
        const card = document.createElement('div');
        card.className = `resource-card ${isFocused ? 'focused' : ''}`;
        card.id = `card_${itemId}`;
        
        // 타이머 및 정보 표시 구성
        let timerLabel = '이용 시간 완료';
        let timerValue = '00:00';
        let isTimerActive = false;
        
        if (state === 'reserved') {
            timerLabel = '예약 자동 취소 대기';
            timerValue = formatTime(item.remaining_seconds);
            isTimerActive = true;
        } else if (state === 'in_use') {
            timerLabel = '최대 잔여 이용 시간';
            timerValue = formatTime(item.remaining_seconds);
            isTimerActive = true;
        } else {
            timerLabel = '사용 즉시 가능';
            timerValue = '--:--';
        }
        
        card.innerHTML = `
            <div class="card-header">
                <span class="card-title">${item.name}</span>
                <span class="badge ${config.badgeClass}">${config.text}</span>
            </div>
            
            <div class="card-time-info">
                <span style="font-size: 0.75rem; opacity: 0.7;">${timerLabel}</span>
                <span class="timer-value ${isTimerActive ? 'active' : ''}" id="timer_${itemId}">
                    ${timerValue}
                </span>
            </div>
            
            <div class="card-controls">
                <button class="card-btn card-btn-idle ${state === 'idle' ? 'active-state' : ''}" 
                    onclick="handleStateRequest('${itemId}', 'idle')" ${state === 'idle' ? 'disabled' : ''}>
                    <i class="fa-solid fa-circle-stop"></i>
                    <span>대기/반납</span>
                </button>
                <button class="card-btn card-btn-reserved ${state === 'reserved' ? 'active-state' : ''}" 
                    onclick="handleStateRequest('${itemId}', 'reserved')" ${state === 'reserved' ? 'disabled' : ''}>
                    <i class="fa-solid fa-hourglass-half"></i>
                    <span>공간예약</span>
                </button>
                <button class="card-btn card-btn-in_use ${state === 'in_use' ? 'active-state' : ''}" 
                    onclick="handleStateRequest('${itemId}', 'in_use')" ${state === 'in_use' ? 'disabled' : ''}>
                    <i class="fa-solid fa-user-lock"></i>
                    <span>사용시작</span>
                </button>
                
                <button class="focus-action-btn ${isFocused ? 'active-focus' : ''}" 
                    onclick="setHardwareFocus('${itemId}')" ${isFocused ? 'disabled' : ''}>
                    <i class="fa-solid ${isFocused ? 'fa-circle-dot' : 'fa-microchip'}"></i>
                    <span>${isFocused ? '하드웨어 연동 중' : '기기 모니터링 연동'}</span>
                </button>
            </div>
        `;
        
        resourceGrid.appendChild(card);
    });
}

/**
 * 상태 변경 요청 핸들러
 */
function handleStateRequest(itemId, targetState) {
    const item = localStateData.items[itemId];
    if (!item) return;
    
    const currentState = item.state;
    
    // 상태 변이별 핀 모달 오픈 분기
    if (currentState === 'idle' && targetState === 'reserved') {
        // 대기 -> 예약: 신규 4자리 PIN 입력 받음
        openPinModal(itemId, targetState, '신규 예약 등록', '이 예약을 선점 및 제어하기 위한 4자리 비밀번호(PIN)를 설정해 주세요.', 'fa-solid fa-lock');
    } else if (currentState === 'reserved' && targetState === 'in_use') {
        // 예약 -> 사용: 본인 확인용 PIN 입력
        openPinModal(itemId, targetState, '사용 인증 요함', '예약 시 설정했던 4자리 비밀번호(PIN)를 입력해 주세요.', 'fa-solid fa-key');
    } else if (targetState === 'idle') {
        // 예약 취소 또는 사용 반납: PIN 입력
        const labelText = currentState === 'reserved' ? '예약 취소 확인' : '사용 반납 확인';
        openPinModal(itemId, targetState, labelText, '제어권을 인증하기 위해 예약 시 설정했던 4자리 비밀번호(PIN)를 입력해 주세요.', 'fa-solid fa-unlock-keyhole');
    } else {
        // 허용되지 않은 변이
        alert('올바르지 않은 상태 변경 접근입니다.');
    }
}

/**
 * PIN 모달 열기 및 확인 버튼 콜백 등록
 */
function openPinModal(itemId, targetState, title, desc, iconClass) {
    modalTitle.textContent = title;
    modalDesc.textContent = desc;
    modalIcon.className = `${iconClass} modal-icon`;
    
    if (iconClass.includes('unlock') || iconClass.includes('key')) {
        modalIcon.style.color = '#ef4444'; // 위험/해제 경고색
    } else {
        modalIcon.style.color = '#fbbf24'; // 대기/예약
    }
    
    pinInput.value = '';
    pinModal.classList.add('show');
    
    // 입력창 포커스
    setTimeout(() => pinInput.focus(), 150);
    
    // 확인 버튼에 이벤트 핸들러 바인딩 (이전 리스너 소거 위해 복사 방식 채택)
    const newConfirmBtn = modalConfirmBtn.cloneNode(true);
    modalConfirmBtn.parentNode.replaceChild(newConfirmBtn, modalConfirmBtn);
    
    // 전역 변수 참조 변경
    document.getElementById('modalConfirmBtn').addEventListener('click', () => {
        const pin = pinInput.value;
        if (!pin || pin.length !== 4) {
            alert('4자리 숫자로 구성된 PIN 번호를 입력해 주세요.');
            pinInput.focus();
            return;
        }
        submitStateChange(itemId, targetState, pin);
    });
    
    // 엔터키 입력 지원
    pinInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
            document.getElementById('modalConfirmBtn').click();
        }
    };
}

function closePinModal() {
    pinModal.classList.remove('show');
    pinInput.value = '';
}

/**
 * 상태 변경 API 호출 전송
 */
async function submitStateChange(itemId, state, pin) {
    try {
        console.log(`기기 [${itemId}] -> 상태 [${state}] 변경 요청 전송 중...`);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'change_state',
                item_id: itemId,
                state: state,
                pin: pin
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP 통신 에러 발생 (Status: ${response.status})`);
        }

        const data = await response.json();
        
        if (data.status === 'success') {
            closePinModal();
            // 즉시 상태 동기화
            await fetchCurrentStatus();
        } else {
            alert(`인증 실패: ${data.message || '상태 변경 권한이 없습니다.'}`);
            pinInput.value = '';
            pinInput.focus();
        }
    } catch (error) {
        console.error('상태 변경 실패:', error);
        alert(`네트워크 통신 오류가 발생했습니다.\n\n[상세 정보]\n${error.message}`);
    }
}

/**
 * 하드웨어 모니터링 포커스 기기 지정 API 호출
 */
async function setHardwareFocus(itemId) {
    try {
        console.log(`기기 [${itemId}] -> 하드웨어 모니터링 포커스 전환 요청 중...`);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'set_focus',
                item_id: itemId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP 통신 에러 (Status: ${response.status})`);
        }

        const data = await response.json();
        
        if (data.status === 'success') {
            // 즉시 상태 동기화
            await fetchCurrentStatus();
        } else {
            alert(`포커스 전환 실패: ${data.message}`);
        }
    } catch (error) {
        console.error('포커스 변경 실패:', error);
        alert(`네트워크 오류가 발생했습니다: ${error.message}`);
    }
}

/**
 * 서버 상태를 조회하여 동기화 (Polling)
 */
async function fetchCurrentStatus() {
    try {
        const response = await fetch(API_URL);
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success' && data.items) {
                localStateData = data;
                
                // 메인 카드 갱신 (선택된 아이템 상태 매핑)
                const activeId = data.active_monitor_item;
                const activeItem = data.items[activeId];
                updateMainFocusCard(activeId, activeItem);
                
                // 전체 목록 카드 갱신
                renderResourceDashboard();
            }
        }
    } catch (error) {
        console.warn('서버 상태 동기화 실패:', error);
    }
}

/**
 * 클라이언트 1초 주기 타이머 카운트다운 루프
 */
function runCountdownTimers() {
    const items = localStateData.items;
    let anyExpired = false;
    
    Object.keys(items).forEach(itemId => {
        const item = items[itemId];
        if (item.state !== 'idle' && item.remaining_seconds > 0) {
            item.remaining_seconds -= 1;
            
            // 화면의 타이머 값만 신속 업데이트 (리렌더링 부하 최소화)
            const timerEl = document.getElementById(`timer_${itemId}`);
            if (timerEl) {
                timerEl.textContent = formatTime(item.remaining_seconds);
                
                // 긴급 시각 경보 (남은 시간이 30초 이내인 경우 빨간색 깜빡임)
                if (item.remaining_seconds <= 30) {
                    timerEl.classList.add('active');
                } else {
                    timerEl.classList.remove('active');
                }
            }
            
            // 타이머 만료 도달
            if (item.remaining_seconds <= 0) {
                anyExpired = true;
            }
        }
    });
    
    // 만약 클라이언트에서 만료된 자원이 발생했다면, 즉시 서버에 최신 상태를 요청해 강제 싱크
    if (anyExpired) {
        fetchCurrentStatus();
    }
}

// 최초 로딩 시 초기 실행 및 주기 루프 설정
window.addEventListener('DOMContentLoaded', () => {
    fetchCurrentStatus();
    
    // 5초 간격 API 폴링
    setInterval(fetchCurrentStatus, 5000);
    
    // 1초 간격 클라이언트 초 카운트다운 타이머 구동
    setInterval(runCountdownTimers, 1000);
});
