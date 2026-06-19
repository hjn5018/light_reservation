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

    User("🧑‍💻 User Browser<br>(Dashboard UI)"):::user
    PiA["📟 Raspberry Pi A<br>(Web Gateway & CGI)"]:::pia
    PiB["⚙️ Raspberry Pi B<br>(Flask, Socket & JSON DB)"]:::pib
    HW["🚨 Hardware Actuators<br>(LEDs, LCD & Buzzer)"]:::hw

    User -->|"1. HTTP Control Request (Port 80)"| PiA
    PiA -->|"2. TCP Socket Command (Port 50007)"| PiB
    User -.->|"3. HTTP REST API Polling (Port 5000)"| PiB
    PiB -->|"4. GPIO Hardware Control"| HW
```

---

## 2. 전체 시스템 연동 흐름도 (Flow Chart)

```mermaid
flowchart TD
    classDef step fill:#eff6ff,stroke:#1e40af,stroke-width:2px,color:#0f172a;
    classDef highlight fill:#fffbeb,stroke:#ca8a04,stroke-width:2px,color:#0f172a;

    subgraph P1 ["1단계: 사용자 제어 요청 (Web & Pi A)"]
        A["1. 웹 UI 예약/반납 버튼 클릭"]:::step --> B["2. 4자리 PIN 입력 및 전송"]:::step
        B --> C["3. Apache CGI 실행 및 TCP 소켓 전송"]:::step
    end
    
    subgraph P2 ["2단계: 제어 실행 및 물리 피드백 (Pi B)"]
        D["4. Pi B 소켓 수신 및 PIN 검증"]:::step --> E["5. Mutex Lock 획득 후 data.json DB 갱신"]:::step
        E --> F["6. GPIO 제어 (LED/LCD/부저 피드백)"]:::step
    end
    
    subgraph P3 ["3단계: 백그라운드 관리 및 상태 갱신 (Pi B & Web)"]
        G["7. 1초 주기 만료 스케줄러 (노쇼/한도초과 회수)"]:::highlight
        H["8. 웹 브라우저 5초 주기 REST API 폴링 조회"]:::step
        I["9. 웹 대시보드 상태 실시간 갱신"]:::step
    end
    
    C ==>|"TCP Port 50007"| D
    F -.->|"상태 변화"| G
    G -.->|"DB 상태 반영"| H
    H --> I
```
