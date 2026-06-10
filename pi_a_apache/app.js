// API 엔드포인트 설정 (동일 도메인 내의 CGI 스크립트 경로)
const API_URL = 'api/update_status.py';

// DOM 요소 획득
const statusCard = document.getElementById('statusCard');
const statusBadge = document.getElementById('statusBadge');
const statusIcon = document.getElementById('statusIcon');
const statusValue = document.getElementById('statusValue');
const buzzerAlert = document.getElementById('buzzerAlert');
const buzzerText = document.getElementById('buzzerText');

// 시스템 현재 상태 기록 변수
let localCurrentState = 'idle';

// 상태별 다이내믹 UI 설정 정보
const stateStyles = {
    idle: {
        text: '대기 (AVAILABLE)',
        iconClass: 'fa-solid fa-circle-check',
        color: '#10b981',
        glow: '0 8px 32px rgba(16, 185, 129, 0.15)',
        borderTop: '#10b981'
    },
    reserved: {
        text: '예약 (RESERVED)',
        iconClass: 'fa-solid fa-hourglass-half',
        color: '#f59e0b',
        glow: '0 8px 32px rgba(245, 158, 11, 0.15)',
        borderTop: '#f59e0b'
    },
    in_use: {
        text: '사용 (IN USE)',
        iconClass: 'fa-solid fa-user-lock',
        color: '#ef4444',
        glow: '0 8px 32px rgba(239, 68, 68, 0.15)',
        borderTop: '#ef4444'
    }
};

/**
 * 상태에 따라 메인 카드와 배경 스타일을 업데이트합니다.
 */
function updateUI(state) {
    const style = stateStyles[state];
    if (!style) return;

    // 텍스트 및 아이콘 갱신
    statusValue.textContent = style.text;
    statusIcon.className = style.iconClass;
    statusIcon.style.color = style.color;
    statusIcon.style.filter = `drop-shadow(0 0 12px ${style.color})`;

    // 카드 테두리 및 섀도우 연동
    statusCard.style.boxShadow = style.glow;
    statusCard.style.setProperty('--glow-color', style.color);
    
    // CSS 가상 요소를 흉내 내기 위해 카드 상단 테두리 스타일 직접 보정
    statusCard.style.borderTop = `4px solid ${style.color}`;

    // 버튼 상태 비활성화 제어 (필요시 활성화)
    resetButtonStates();
    highlightActiveButton(state);
}

function resetButtonStates() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.style.opacity = '0.7';
        btn.style.transform = 'scale(1)';
        btn.style.borderWidth = '1px';
    });
}

function highlightActiveButton(state) {
    let btnId = '';
    if (state === 'idle') btnId = 'btnIdle';
    else if (state === 'reserved') btnId = 'btnReserved';
    else if (state === 'in_use') btnId = 'btnInUse';

    const activeBtn = document.getElementById(btnId);
    if (activeBtn) {
        activeBtn.style.opacity = '1';
        activeBtn.style.transform = 'scale(1.04)';
        activeBtn.style.borderWidth = '2px';
    }
}

/**
 * 부저 작동 시각 알림 애니메이션을 표출합니다.
 */
function triggerBuzzerAnimation(transitionType) {
    if (transitionType === 'reserved_to_in_use') {
        buzzerText.textContent = "부저 작동: 예약 ➔ 사용 (상승음 ♪ 도-미-솔)";
        buzzerAlert.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        buzzerAlert.className = "buzzer-alert show";
    } else if (transitionType === 'in_use_to_idle') {
        buzzerText.textContent = "부저 작동: 사용 ➔ 대기 (하강음 ♬ 솔-미-도)";
        buzzerAlert.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        buzzerAlert.className = "buzzer-alert show";
    }

    // 3.5초 후 자동으로 알림 숨김 (재생 시간 고려)
    setTimeout(() => {
        buzzerAlert.className = "buzzer-alert";
    }, 3500);
}

/**
 * Pi B 상태 변경 요청 전송
 */
async function updateState(newState) {
    try {
        console.log(`상태 변경 요청 전송 중... [${newState}]`);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ state: newState })
        });

        if (!response.ok) {
            throw new Error(`HTTP 통신 에러 발생 (Status: ${response.status})`);
        }

        const data = await response.json();
        
        if (data.status === 'success') {
            const returnedState = data.current_state;
            
            // 부저 알림 조건 판별
            if (localCurrentState === 'reserved' && returnedState === 'in_use') {
                triggerBuzzerAnimation('reserved_to_in_use');
            } else if (localCurrentState === 'in_use' && returnedState === 'idle') {
                triggerBuzzerAnimation('in_use_to_idle');
            }

            localCurrentState = returnedState;
            updateUI(returnedState);
        } else {
            alert(`오류: ${data.message || '상태를 변경하지 못했습니다.'}`);
        }
    } catch (error) {
        console.error('상태 변경 실패:', error);
        // 사용자에게 다크 모드에 어울리는 세련된 경고 피드백 제공 가능
    }
}

/**
 * 서버 상태를 주기적으로 조회하여 연동 (Polling)
 */
async function fetchCurrentStatus() {
    try {
        // state 없이 GET으로 쿼리 시 현재 상태만 받아옴
        const response = await fetch(API_URL);
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success' && data.current_state) {
                const fetchedState = data.current_state;
                if (fetchedState !== localCurrentState) {
                    // 외부 변경 요인이나 초기 연동 시 멜로디 애니메이션 생략하고 단순 동기화
                    localCurrentState = fetchedState;
                    updateUI(fetchedState);
                }
            }
        }
    } catch (error) {
        console.warn('현재 상태 동기화 실패:', error);
    }
}

// 최초 페이지 로딩 시 상태 동기화 및 5초 주기 폴링 등록
window.addEventListener('DOMContentLoaded', () => {
    fetchCurrentStatus();
    // 5초 간격 실시간 동기화
    setInterval(fetchCurrentStatus, 5000);
});
