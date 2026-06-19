# 스마트 통합 자원 예약 시스템 다이어그램 명세 (Diagram Specs)

이 문서는 시스템 구성도와 시스템 연동 흐름도를 마크다운 내 Mermaid 코드 형태로 제공합니다. 
VS Code, GitHub 등 마크다운 내 Mermaid 렌더링이 가능한 환경에서 이 문서를 열어 렌더링된 다이어그램을 캡처한 후, **`images` 폴더** 아래에 다음 파일명으로 저장해주세요.

1. **전체 시스템 구성도 (UML Component Diagram)**
   - 캡처 파일명: `system_architecture.png`
   - 저장 경로: `images/system_architecture.png`
2. **전체 시스템 연동 흐름도 (Flow Chart)**
   - 캡처 파일명: `system_flowchart.png`
   - 저장 경로: `images/system_flowchart.png`

---

## 1. 전체 시스템 구성도 (UML Component Diagram)

```mermaid
graph TD
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef pia fill:#eff6ff,stroke:#10b981,stroke-width:2px;
    classDef pib fill:#fffbeb,stroke:#f59e0b,stroke-width:2px;
    classDef hw fill:#f0fdf4,stroke:#16a34a,stroke-width:2px;

    User("🧑‍💻 User Browser<br>(Dashboard)"):::user
    
    subgraph PiA ["📟 Raspberry Pi A (Gateway)"]
        Apache["Apache Web Server<br>(Port 80)"]:::pia
        CGI["CGI Script<br>(update_status.py)"]:::pia
    end
    
    subgraph PiB ["⚙️ Raspberry Pi B (Hardware Core)"]
        Flask["Flask Server<br>(Port 5000)"]:::pib
        Socket["Socket Listener Thread<br>(Port 50007)"]:::pib
        Mutex["Mutex Lock & data.json"]:::pib
        Scheduler["Background Scheduler Thread<br>(1s loop daemon)"]:::pib
    end
    
    subgraph HW ["🚨 Hardware Actuators"]
        LED["LEDs (3-color)"]:::hw
        LCD["16x2 Character LCD"]:::hw
        Buzzer["Piezo Buzzer"]:::hw
    end
    
    User -->|HTTP Request / static files| Apache
    Apache -->|Execute| CGI
    CGI -->|TCP Socket Command (Port 50007)| Socket
    User -.->|HTTP REST API Polling (Port 5000)| Flask
    Socket -->|Write State (Mutex)| Mutex
    Flask -->|Read State (Mutex)| Mutex
    Scheduler -->|Read/Write State (Mutex)| Mutex
    
    Socket -->|GPIO Control| HW
    Scheduler -->|Auto Expiration / GPIO Control| HW
```

---

## 2. 전체 시스템 연동 흐름도 (Flow Chart)

```mermaid
flowchart TD
    classDef start fill:#fef2f2,stroke:#b91c1c,stroke-width:2px,color:#b91c1c;
    classDef init fill:#fef2f2,stroke:#b91c1c,stroke-width:2px,color:#0f172a;
    classDef rect fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#0f172a;
    classDef decision fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#0f172a;
    classDef circle fill:#ffffff,stroke:#b91c1c,stroke-width:2px,color:#b91c1c;
    classDef hwBox fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef ndkBox fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;

    subgraph Process1 ["PROCESS 1 (웹 클라이언트 및 CGI)"]
        P1_Start("START<br>Web Portal"):::start
        P1_Init("Apache Web &<br>CGI Script Init<br>(update_status.py)"):::init
        P1_Wait("웹 제어 대기"):::rect
        P1_Dec{"예약/반납<br>클릭?"}:::decision
        P1_PIN("4자리 PIN<br>본인 확인 입력"):::rect
        P1_Send("CGI 소켓 전송<br>(Port 50007)"):::rect
        P1_Sensing1("(SENSING)"):::circle
        
        P1_Start --> P1_Init
        P1_Init --> P1_Wait
        P1_Wait --> P1_Dec
        P1_Dec -->|YES| P1_PIN
        P1_Dec -->|NO| P1_Wait
        P1_PIN --> P1_Send
        P1_Send --> P1_Sensing1
    end

    subgraph Sensing ["SENSING (상태 조회 및 갱신)"]
        S_Sensing2("(SENSING)"):::circle
        S_Poll("5초 주기 REST API<br>조회 (/api/status)"):::rect
        S_Dec{"자원 상태<br>변경 감지?"}:::decision
        S_Render("웹 UI 예약 카드<br>비동기 화면 갱신"):::rect
        S_Wait5("5초 후<br>비동기 재폴링"):::rect
        
        S_Sensing2 --> S_Poll
        S_Poll --> S_Dec
        S_Dec -->|YES| S_Render
        S_Dec -->|NO| S_Poll
        S_Render --> S_Wait5
        S_Wait5 --> S_Poll
    end

    subgraph Process2 ["PROCESS 2 (Pi B 하드웨어 코어)"]
        P2_Start("START<br>Socket Daemon"):::start
        P2_WaitSock("TCP 소켓 수신 대기<br>(Port 50007)"):::rect
        P2_Dec{"패킷 수신 및<br>PIN 검증?"}:::decision
        P2_DB("Mutex Lock 획득 후<br>data.json DB 갱신"):::rect
        
        subgraph HWBox ["물리 피드백 및 액추에이터 제어"]
            LEDs("삼색 LED 상태별 점등<br>(초록/노랑/빨강)"):::rect
            LCDText("16x2 LCD 자원 상태 영문 출력"):::rect
            BuzzerMelody("피에조 부저 멜로디 연주<br>(상승/하강음)"):::rect
        end
        
        Scheduler("자동 회수 스케줄러 (1초 데몬 스레드)<br>(노쇼 1분 폭파 / 사용한도 3분 회수)"):::ndkBox
        
        P2_Start --> P2_WaitSock
        P2_WaitSock --> P2_Dec
        P2_Dec -->|YES| P2_DB
        P2_Dec -->|NO| P2_WaitSock
        P2_DB --> HWBox
        HWBox -.-> Scheduler
        Scheduler -.->|상태 초기화| P2_WaitSock
    end

    P1_Send ==>|TCP Packet| P2_WaitSock
    Scheduler ==>|비상 회수 상태 전달| P1_Wait
```
