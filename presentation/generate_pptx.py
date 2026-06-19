import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(filename="presentation.pptx"):
    prs = Presentation()
    
    # 16:9 Widescreen slide dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # Color Palette (Dark Theme)
    BG_COLOR = RGBColor(15, 23, 42)        # #0F172A Slate 900 (Very Dark slate)
    PANEL_COLOR = RGBColor(30, 41, 59)     # #1E293B Slate 800 (Card backgrounds)
    TEXT_WHITE = RGBColor(248, 250, 252)   # #F8FAFC White/Gray
    TEXT_MUTED = RGBColor(148, 163, 184)   # #94A3B8 Cool Gray for captions
    COLOR_EMERALD = RGBColor(16, 185, 129) # #10B981 Emerald 500 (Primary accent)
    COLOR_AMBER = RGBColor(245, 158, 11)   # #F59E0B Amber 500 (Secondary accent)
    COLOR_RED = RGBColor(239, 68, 68)      # #EF4444 Red 500 (Alert/Warning)
    
    FONT_TITLE = "Malgun Gothic"
    FONT_BODY = "Malgun Gothic"

    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BG_COLOR

    def add_slide_header(slide, title_text, category_text="Smart Multi-Resource Reservation IoT System"):
        # Top-left small category tracker
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = FONT_BODY
        p_cat.font.size = Pt(10)
        p_cat.font.color.rgb = COLOR_EMERALD
        p_cat.font.bold = True
        
        # Main Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(10), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = FONT_TITLE
        p_title.font.size = Pt(26)
        p_title.font.color.rgb = TEXT_WHITE
        p_title.font.bold = True
        
        # Bottom footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.3))
        tf_foot = footer_box.text_frame
        tf_foot.margin_left = tf_foot.margin_right = tf_foot.margin_top = tf_foot.margin_bottom = 0
        p_foot = tf_foot.paragraphs[0]
        p_foot.text = "IoT 제어 실습  |  2-Pi 스마트 자원 예약 시스템 발표자료"
        p_foot.font.name = FONT_BODY
        p_foot.font.size = Pt(9)
        p_foot.font.color.rgb = TEXT_MUTED

    slide_layout = prs.slide_layouts[6]  # Blank Layout

    # ----------------------------------------------------
    # SLIDE 1: Title Slide (Cover)
    # ----------------------------------------------------
    slide1 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide1)
    
    # Accent Bar
    accent_bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.1), Inches(3.5), Inches(0.08))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = COLOR_EMERALD
    accent_bar.line.fill.background()
    
    # Main Title Text
    title_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(11.7), Inches(2.0))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "IoT 기반 스마트 통합 자원 예약 시스템"
    p1.font.name = FONT_TITLE
    p1.font.size = Pt(38)
    p1.font.color.rgb = TEXT_WHITE
    p1.font.bold = True
    
    p2 = tf1.add_paragraph()
    p2.text = "Smart Multi-Resource Reservation IoT System"
    p2.font.name = FONT_TITLE
    p2.font.size = Pt(18)
    p2.font.color.rgb = COLOR_AMBER
    p2.font.bold = True
    p2.space_before = Pt(6)

    # Subtitle / Meta info
    sub_box = slide1.shapes.add_textbox(Inches(0.8), Inches(4.3), Inches(11.7), Inches(1.5))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p_sub1 = tf_sub.paragraphs[0]
    p_sub1.text = "2대 라즈베리 파이 네트워크 연동 및 3대 하드웨어 피드백 기반 공용 자원 관리 솔루션"
    p_sub1.font.name = FONT_BODY
    p_sub1.font.size = Pt(14)
    p_sub1.font.color.rgb = TEXT_MUTED
    
    p_sub2 = tf_sub.add_paragraph()
    p_sub2.text = "과목: IoT 제어 실습  |  발표자: 홍길동 (편집 가능)"
    p_sub2.font.name = FONT_BODY
    p_sub2.font.size = Pt(13)
    p_sub2.font.color.rgb = COLOR_EMERALD
    p_sub2.space_before = Pt(20)

    # ----------------------------------------------------
    # SLIDE 2: Table of Contents (목차) - [NEW]
    # ----------------------------------------------------
    slide2 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide2)
    add_slide_header(slide2, "발표 목차 (Contents)")
    
    # 5 sections in 5 rounded panels
    start_top = Inches(1.6)
    panel_h = Inches(0.85)
    gap = Inches(0.2)
    
    toc_items = [
        ("01", "📋 프로젝트 개요 및 배경", "공용 자원 무단 점유와 예약 No-Show 분쟁의 원인과 시스템적 대안"),
        ("02", "🛠️ 사용 장비 및 시스템 구성", "2대 라즈베리 파이 및 3대 물리 액추에이터 하드웨어/네트워크 연동"),
        ("03", "📅 개발 일정 및 전체 흐름도", "3주 개발 주기 타임라인 및 클라이언트-서버 간 제어 순서도"),
        ("04", "🔒 핵심 소프트웨어 기술 설명", "CGI 게이트웨이, TCP 소켓 통신, 멀티스레딩, Mutex 데이터 잠금"),
        ("05", "📷 작동 시연 및 기대효과", "실제 시스템 구동 화면 구성, 기대효과 및 향후 발전 가능성")
    ]
    
    for i, (num, title, desc) in enumerate(toc_items):
        t_top = start_top + i * (panel_h + gap)
        
        # Round panel
        panel = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), t_top, Inches(11.733), panel_h)
        panel.fill.solid()
        panel.fill.fore_color.rgb = PANEL_COLOR
        panel.line.color.rgb = COLOR_EMERALD if i%2==0 else COLOR_AMBER
        panel.line.width = Pt(1.5)
        
        tf_panel = panel.text_frame
        tf_panel.word_wrap = True
        tf_panel.margin_left = Inches(0.3)
        tf_panel.margin_top = Inches(0.12)
        
        p = tf_panel.paragraphs[0]
        # Slide number badge
        r_num = p.add_run()
        r_num.text = f"{num}  "
        r_num.font.name = FONT_TITLE
        r_num.font.size = Pt(18)
        r_num.font.bold = True
        r_num.font.color.rgb = COLOR_EMERALD if i%2==0 else COLOR_AMBER
        
        # Title
        r_title = p.add_run()
        r_title.text = f"{title}   |   "
        r_title.font.name = FONT_TITLE
        r_title.font.size = Pt(16)
        r_title.font.bold = True
        r_title.font.color.rgb = TEXT_WHITE
        
        # Description
        r_desc = p.add_run()
        r_desc.text = desc
        r_desc.font.name = FONT_BODY
        r_desc.font.size = Pt(12)
        r_desc.font.color.rgb = TEXT_MUTED

    # ----------------------------------------------------
    # SLIDE 3: Development Background & Problems
    # ----------------------------------------------------
    slide3 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide3)
    add_slide_header(slide3, "1. 개발 배경 및 필요성")
    
    callout = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.7))
    callout.fill.solid()
    callout.fill.fore_color.rgb = PANEL_COLOR
    callout.line.color.rgb = COLOR_AMBER
    tf_call = callout.text_frame
    tf_call.word_wrap = True
    tf_call.margin_left = Inches(0.2)
    p_call = tf_call.paragraphs[0]
    p_call.text = "💡 공용 자원 관리의 고질적인 무단 점유와 예약 방치(No-Show)를 시스템 제어로 해결"
    p_call.font.name = FONT_TITLE
    p_call.font.size = Pt(14)
    p_call.font.color.rgb = TEXT_WHITE
    p_call.font.bold = True
    
    # 2 columns
    col_w = Inches(5.6)
    left_c = slide3.shapes.add_textbox(Inches(0.8), Inches(2.4), col_w, Inches(4.2))
    tf_l = left_c.text_frame
    tf_l.word_wrap = True
    p_lh = tf_l.paragraphs[0]
    p_lh.text = "🚨 기존 공용 자원의 관리 한계"
    p_lh.font.name = FONT_TITLE
    p_lh.font.size = Pt(18)
    p_lh.font.color.rgb = COLOR_AMBER
    p_lh.font.bold = True
    p_lh.space_after = Pt(12)
    
    probs = [
        "비인가 무단 점유: 실시간 예약 및 점유 상태가 불투명하여 발생하는 자원 가로채기와 마찰",
        "자원 독점과 노쇼: 예약 후 방치해 두어 다른 사용자들의 자원 접근 기회를 일방적으로 박탈",
        "물리 피드백 부재: 화면을 모니터링하기 전까지는 기기 상태나 반납 시간을 직관적으로 알기 어려움"
    ]
    for text in probs:
        p = tf_l.add_paragraph()
        p.text = "• " + text
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)
        
    right_c = slide3.shapes.add_textbox(Inches(6.9), Inches(2.4), col_w, Inches(4.2))
    tf_r = right_c.text_frame
    tf_r.word_wrap = True
    p_rh = tf_r.paragraphs[0]
    p_rh.text = "✅ 스마트 예약 시스템의 해결 대안"
    p_rh.font.name = FONT_TITLE
    p_rh.font.size = Pt(18)
    p_rh.font.color.rgb = COLOR_EMERALD
    p_rh.font.bold = True
    p_rh.space_after = Pt(12)
    
    sols = [
        "웹 실시간 대시보드: 5초 주기로 모든 공용 물품/공간의 예약 상태를 한눈에 비동기 모니터링",
        "4자리 PIN 본인 식별: 복잡한 가입 없이 예약 시 PIN 번호를 활용해 타인의 오용 및 해제 원천 차단",
        "자동 만료 스케줄러: 지정 대기 시간 내 미사용 시 노쇼 취소 처리, 최대 사용시간 경과 시 자동 반납"
    ]
    for text in sols:
        p = tf_r.add_paragraph()
        p.text = "• " + text
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)

    # ----------------------------------------------------
    # SLIDE 4: Equipment Used (사용 장비 및 부품) - [NEW]
    # ----------------------------------------------------
    slide4 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide4)
    add_slide_header(slide4, "2. 사용 장비 및 부품 사양")
    
    # 4 column blocks (Grid layout)
    grid_w = Inches(2.7)
    grid_h = Inches(4.5)
    grid_top = Inches(1.8)
    grid_gap = Inches(0.3)
    
    equipments = [
        ("🖥️", "라즈베리 파이 4 (2대)", "시스템 연동 제어 코어", 
         ["Pi A: Apache 웹 서버 호스팅 및 웹-서버 CGI 소켓 게이트웨이 역할", 
          "Pi B: Flask REST API 처리, 백그라운드 소켓 수신 및 하드웨어 액추에이터 제어"]),
        ("🚨", "삼색 LED (3개)", "직관적인 시각 피드백", 
         ["자원의 상태 변화를 신호등 개념으로 가시화", 
          "초록 LED: 대기 상태(Available)", 
          "노란 LED: 예약 상태(Reserved)", 
          "빨간 LED: 사용 상태(In Use)"]),
        ("📟", "16x2 Character LCD", "포커스 자원 문자 출력", 
         ["선택된 기기의 영문 자원명 실시간 렌더링", 
          "기기의 현재 세부 동작 상태 문자 표현", 
          "가변저항(Potentiometer) 회로 연동을 통해 전압 대비(Contrast) 미세 튜닝"]),
        ("🔊", "피에조 패시브 부저", "상태 전이 청각 피드백", 
         ["주파수 PWM 변조를 활용한 상태 변경 음계 연주", 
          "사용 시작 시: 상승음 (도-미-솔) 멜로디 알림", 
          "자동 만료/반납 시: 하강음 (솔-미-도) 멜로디 경보"])
    ]
    
    for idx, (icon, name, caption, specs) in enumerate(equipments):
        left_pos = Inches(0.8) + idx * (grid_w + grid_gap)
        
        # Grid box
        box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, grid_top, grid_w, grid_h)
        box.fill.solid()
        box.fill.fore_color.rgb = PANEL_COLOR
        box.line.color.rgb = COLOR_EMERALD if idx%2==0 else COLOR_AMBER
        box.line.width = Pt(1.5)
        
        tf_box = box.text_frame
        tf_box.word_wrap = True
        tf_box.margin_left = Inches(0.2)
        tf_box.margin_right = Inches(0.2)
        tf_box.margin_top = Inches(0.2)
        
        # Icon
        p_icon = tf_box.paragraphs[0]
        p_icon.text = icon
        p_icon.alignment = PP_ALIGN.CENTER
        p_icon.font.size = Pt(28)
        p_icon.space_after = Pt(6)
        
        # Name
        p_name = tf_box.add_paragraph()
        p_name.text = name
        p_name.alignment = PP_ALIGN.CENTER
        p_name.font.name = FONT_TITLE
        p_name.font.size = Pt(14)
        p_name.font.bold = True
        p_name.font.color.rgb = TEXT_WHITE
        
        # Caption
        p_cap = tf_box.add_paragraph()
        p_cap.text = caption
        p_cap.alignment = PP_ALIGN.CENTER
        p_cap.font.name = FONT_BODY
        p_cap.font.size = Pt(11)
        p_cap.font.color.rgb = COLOR_AMBER if idx%2==1 else COLOR_EMERALD
        p_cap.space_after = Pt(12)
        
        # Bullet Specs
        for spec in specs:
            p_spec = tf_box.add_paragraph()
            p_spec.text = "- " + spec
            p_spec.font.name = FONT_BODY
            p_spec.font.size = Pt(9.5)
            p_spec.font.color.rgb = TEXT_WHITE
            p_spec.space_after = Pt(4)

    # ----------------------------------------------------
    # SLIDE 5: Development Schedule (개발 일정) - [NEW]
    # ----------------------------------------------------
    slide5 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide5)
    add_slide_header(slide5, "3. 개발 일정 및 수행 내역")
    
    # Timeline Layout (3 Columns side-by-side representing 3 weeks)
    col_w = Inches(3.6)
    col_h = Inches(4.3)
    col_top = Inches(2.0)
    col_gap = Inches(0.4)
    
    schedule_steps = [
        ("📅 1주차: 기획 & 설계", "2026.06.04 ~ 2026.06.10", COLOR_EMERALD,
         ["• 요구사항 분석 및 관리 자원(공간/기기)의 명세 구체화",
          "• Pi A 및 Pi B 간의 이원화 네트워크 통신 방식 아키텍처 수립",
          "• 라즈베리 파이 GPIO 회로도 설계 (LED, LCD, 부저 핀 맵 매핑)"]),
        ("📅 2주차: 구현 & 프로그래밍", "2026.06.11 ~ 2026.06.17", COLOR_AMBER,
         ["• Pi A Apache 호스팅 환경 구축 및 CGI 게이트웨이 파이썬 구현",
          "• Pi B Flask REST API 엔드포인트 및 다중 스레드 소켓 서버 코어 개발",
          "• GPIO 드라이버 모듈(LCD, LED, 패시브 부저 PWM) 작성 및 더미 모드 연동"]),
        ("📅 3주차: 검증 & 최적화", "2026.06.18 ~ 2026.06.25", COLOR_EMERALD,
         ["• 전체 네트워크 연동 및 예외 시나리오 통합 테스트(PIN 검증, 마스터 PIN)",
          "• 백그라운드 만료 스케줄러 스레드의 타이머 연산 디버깅 및 안전 잠금 확인",
          "• setup.sh 설치 자동화 쉘 스크립트 작성 및 시스템 서비스 데몬 등록 검수"])
    ]
    
    # Progress indicators / arrows
    for idx, (title, date, accent_color, tasks) in enumerate(schedule_steps):
        left_pos = Inches(0.8) + idx * (col_w + col_gap)
        
        # Panel
        card = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, col_top, col_w, col_h)
        card.fill.solid()
        card.fill.fore_color.rgb = PANEL_COLOR
        card.line.color.rgb = accent_color
        card.line.width = Pt(2.0)
        
        tf_card = card.text_frame
        tf_card.word_wrap = True
        tf_card.margin_left = tf_card.margin_right = Inches(0.25)
        tf_card.margin_top = Inches(0.2)
        
        p_title = tf_card.paragraphs[0]
        p_title.text = title
        p_title.font.name = FONT_TITLE
        p_title.font.size = Pt(16)
        p_title.font.bold = True
        p_title.font.color.rgb = accent_color
        p_title.space_after = Pt(4)
        
        p_date = tf_card.add_paragraph()
        p_date.text = date
        p_date.font.name = FONT_BODY
        p_date.font.size = Pt(12)
        p_date.font.color.rgb = TEXT_MUTED
        p_date.space_after = Pt(18)
        
        for task in tasks:
            p_task = tf_card.add_paragraph()
            p_task.text = task
            p_task.font.name = FONT_BODY
            p_task.font.size = Pt(11.5)
            p_task.font.color.rgb = TEXT_WHITE
            p_task.space_after = Pt(10)
            
        # Draw small arrow between columns (except last)
        if idx < 2:
            arrow = slide5.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, 
                Inches(0.8) + col_w + idx * (col_w + col_gap) + Inches(0.1), 
                col_top + col_h/2 - Inches(0.2), 
                Inches(0.2), 
                Inches(0.4)
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = COLOR_AMBER
            arrow.line.fill.background()

    # ----------------------------------------------------
    # SLIDE 6: Overall System Structure (전체 시스템 구성) - [NEW]
    # ----------------------------------------------------
    slide6 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide6)
    add_slide_header(slide6, "4. 전체 시스템 구성도")
    
    # 3 Column architecture layout (Similar to Slide 3 of previous version)
    col_width = Inches(3.6)
    col_height = Inches(4.5)
    top_pos = Inches(1.8)
    
    # Pi A Block
    pi_a_panel = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_pos, col_width, col_height)
    pi_a_panel.fill.solid()
    pi_a_panel.fill.fore_color.rgb = PANEL_COLOR
    pi_a_panel.line.color.rgb = COLOR_EMERALD
    pi_a_panel.line.width = Pt(1.5)
    tf_a = pi_a_panel.text_frame
    tf_a.word_wrap = True
    tf_a.margin_left = tf_a.margin_right = Inches(0.2)
    tf_a.margin_top = Inches(0.25)
    
    p = tf_a.paragraphs[0]
    p.text = "📟 Pi A : 웹 게이트웨이"
    p.font.name = FONT_TITLE
    p.font.size = Pt(18)
    p.font.color.rgb = COLOR_EMERALD
    p.font.bold = True
    p.space_after = Pt(14)
    
    items_a = [
        "Apache Web Server: 포트 80 호스팅, 정적 웹 리소스 제공 (HTML, JS)",
        "ExecCGI 모듈: 비동기 데이터 통신을 위한 Python CGI 핸들러 연동",
        "CGI Script (update_status.py): 웹 브라우저의 제어 패킷을 해석하고 Pi B로 TCP 소켓 릴레이 송신"
    ]
    for item in items_a:
        p = tf_a.add_paragraph()
        p.text = "- " + item
        p.font.name = FONT_BODY
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)

    # Communications Block
    net_panel = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.8), top_pos, col_width, col_height)
    net_panel.fill.solid()
    net_panel.fill.fore_color.rgb = PANEL_COLOR
    net_panel.line.color.rgb = COLOR_AMBER
    net_panel.line.width = Pt(1.5)
    tf_net = net_panel.text_frame
    tf_net.word_wrap = True
    tf_net.margin_left = tf_net.margin_right = Inches(0.2)
    tf_net.margin_top = Inches(0.25)
    
    p = tf_net.paragraphs[0]
    p.text = "🔌 이원화 통신 파이프라인"
    p.font.name = FONT_TITLE
    p.font.size = Pt(18)
    p.font.color.rgb = COLOR_AMBER
    p.font.bold = True
    p.space_after = Pt(14)
    
    items_net = [
        "제어 명령 (저지연): 사용자 상태 전환 시 Pi A CGI 스크립트와 Pi B 소켓 리스너 스레드 간의 1:1 TCP Raw Socket 통신 (포트 50007)",
        "상태 조회 (REST API): 웹 대시보드에서 예약 현황 및 잔여 시간 동기화를 위해 5초 단위로 Pi B Flask API를 비동기 호출 (포트 5000)"
    ]
    for item in items_net:
        p = tf_net.add_paragraph()
        p.text = "- " + item
        p.font.name = FONT_BODY
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)

    # Pi B Block
    pi_b_panel = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.8), top_pos, col_width, col_height)
    pi_b_panel.fill.solid()
    pi_b_panel.fill.fore_color.rgb = PANEL_COLOR
    pi_b_panel.line.color.rgb = COLOR_EMERALD
    pi_b_panel.line.width = Pt(1.5)
    tf_b = pi_b_panel.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_right = Inches(0.2)
    tf_b.margin_top = Inches(0.25)
    
    p = tf_b.paragraphs[0]
    p.text = "⚙️ Pi B : 하드웨어 코어"
    p.font.name = FONT_TITLE
    p.font.size = Pt(18)
    p.font.color.rgb = COLOR_EMERALD
    p.font.bold = True
    p.space_after = Pt(14)
    
    items_b = [
        "Flask API Server: 전역 예약 상태 조회 및 실시간 잔여시간 계산 제공",
        "Socket Listener: 백그라운드 소켓 스레드가 상시 대기하여 Pi A CGI 제어 패킷 수신",
        "액추에이터 제어 모듈: LED 갱신(led.py), 부저 PWM 변조(buzzer.py), 한글 매핑 LCD 제어(lcd.py) 구동",
        "JSON DB: data.json 로컬 영속 저장 및 정전 시 직전 상태 백업 복구"
    ]
    for item in items_b:
        p = tf_b.add_paragraph()
        p.text = "- " + item
        p.font.name = FONT_BODY
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)

    # ----------------------------------------------------
    # SLIDE 7: Overall System Flowchart (전체 시스템 흐름도) - [NEW]
    # ----------------------------------------------------
    slide7 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide7)
    add_slide_header(slide7, "5. 전체 시스템 연동 흐름도")
    
    # Visual sequential flow description
    flow_steps = [
        ("1. 예약 / 제어 요청", "사용자가 웹 대시보드(index.html)에서 특정 기기 예약 버튼 클릭 후 본인 확인을 위한 4자리 비밀번호(PIN) 입력"),
        ("2. CGI 및 TCP 소켓 송신", "브라우저 요청을 접수한 Pi A의 Apache CGI(update_status.py)가 저지연 TCP 소켓 연결을 맺고 제어 패킷을 Pi B로 전송"),
        ("3. 소켓 수신 및 뮤텍스 락", "Pi B 백그라운드 소켓 리스너 스레드가 이를 수신하고, Flask API 조회와의 충돌을 막기 위해 Mutex Lock을 획득 후 data.json 갱신"),
        ("4. 하드웨어 물리 피드백", "상태 전이에 상응하는 물리 액추에이터 제어 수행 (LED 색상 변경, 피에조 부저 멜로디 출력, Character LCD 텍스트 갱신)"),
        ("5. 백그라운드 스케줄러", "Pi B의 데몬 스레드가 1초 주기로 돌며 노쇼 시간 만료(1분) 및 사용 한도(3분) 초과를 체크하고, 초과 시 즉각 대기(Idle) 상태로 강제 전환"),
        ("6. 실시간 브라우저 동기화", "사용자 브라우저가 Flask API(/api/status)를 5초마다 주기적으로 비동기 폴링하여, 갱신된 전역 예약 상태와 카운트다운 초 단위를 화면에 갱신")
    ]
    
    s_top = Inches(1.5)
    f_height = Inches(0.8)
    f_gap = Inches(0.1)
    
    for idx, (title, desc) in enumerate(flow_steps):
        left_pos = Inches(0.8)
        top_pos = s_top + idx * (f_height + f_gap)
        
        # Step panel
        flow_panel = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, top_pos, Inches(11.733), f_height)
        flow_panel.fill.solid()
        flow_panel.fill.fore_color.rgb = PANEL_COLOR
        flow_panel.line.color.rgb = COLOR_AMBER if idx%2==1 else COLOR_EMERALD
        flow_panel.line.width = Pt(1.5)
        
        tf_flow = flow_panel.text_frame
        tf_flow.word_wrap = True
        tf_flow.margin_left = Inches(0.25)
        tf_flow.margin_top = Inches(0.12)
        
        p = tf_flow.paragraphs[0]
        # Step Title
        r_title = p.add_run()
        r_title.text = f"{title}   |   "
        r_title.font.name = FONT_TITLE
        r_title.font.size = Pt(13)
        r_title.font.bold = True
        r_title.font.color.rgb = COLOR_AMBER if idx%2==1 else COLOR_EMERALD
        
        # Step Description
        r_desc = p.add_run()
        r_desc.text = desc
        r_desc.font.name = FONT_BODY
        r_desc.font.size = Pt(11)
        r_desc.font.color.rgb = TEXT_WHITE

    # ----------------------------------------------------
    # SLIDE 8: Detailed Technology Explanations (CGI, Socket, Thread, Mutex) - [NEW]
    # ----------------------------------------------------
    slide8 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide8)
    add_slide_header(slide8, "6. 주요 기술 명세 및 동기화 구현")
    
    # 4 column technologies
    techs = [
        ("📡 CGI (Common Gateway Interface)", "웹 서버와 백엔드 통신 매개", 
         ["• Apache Web Server 포트 80과 외부 브라우저 단말과의 동적 게이트웨이",
          "• 사용자의 POST/GET 비동기 신호를 파이썬 환경 변수로 매핑 해석",
          "• 소켓 인스턴스를 동적 생성하여 서버 내부 백엔드로 연결 송신"]),
        ("🔌 저지연 TCP 소켓 통신", "초고속 1:1 양방향 네트워킹", 
         ["• 포트 50007번에서 Pi A CGI 클라이언트와 Pi B 소켓 리스너 스레드 연동",
          "• HTTP 오버헤드가 배제된 원시 TCP 세션 데이터 전송으로 패킷 지연 최소화",
          "• JSON 기반 상태 제어 명령어 전송"]),
        ("🧵 멀티스레드 (Daemon Threads)", "백그라운드 다중 업무 병렬 처리", 
         ["• 소켓 리스너 스레드: 클라이언트의 갑작스러운 접속과 제어 명령 상시 대기",
          "• 타이머 스케줄러 스레드: 1초 간격 상태 및 만료 시간 연산 백그라운드 구동",
          "• daemon=True 설정으로 웹 해제 시 동시 정지"]),
        ("🔒 뮤텍스 락 (Mutex Lock)", "경쟁 상태 차단 및 데이터 보호", 
         ["• state_lock = threading.Lock()",
          "• 다수의 스레드(Flask/Socket/Scheduler)가 전역 객체 및 파일 DB에 동시 접근 차단",
          "• with state_lock: 구문을 사용해 데이터 무결성(Data Integrity) 확보"])
    ]
    
    grid_w = Inches(2.7)
    grid_h = Inches(4.5)
    grid_top = Inches(1.8)
    grid_gap = Inches(0.3)
    
    for idx, (title, caption, specs) in enumerate(techs):
        left_pos = Inches(0.8) + idx * (grid_w + grid_gap)
        
        # Grid box
        box = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, grid_top, grid_w, grid_h)
        box.fill.solid()
        box.fill.fore_color.rgb = PANEL_COLOR
        box.line.color.rgb = COLOR_EMERALD if idx%2==0 else COLOR_AMBER
        box.line.width = Pt(1.5)
        
        tf_box = box.text_frame
        tf_box.word_wrap = True
        tf_box.margin_left = Inches(0.2)
        tf_box.margin_right = Inches(0.2)
        tf_box.margin_top = Inches(0.2)
        
        # Title
        p_name = tf_box.paragraphs[0]
        p_name.text = title
        p_name.font.name = FONT_TITLE
        p_name.font.size = Pt(13)
        p_name.font.bold = True
        p_name.font.color.rgb = COLOR_EMERALD if idx%2==0 else COLOR_AMBER
        p_name.space_after = Pt(4)
        
        # Caption
        p_cap = tf_box.add_paragraph()
        p_cap.text = caption
        p_cap.font.name = FONT_BODY
        p_cap.font.size = Pt(11)
        p_cap.font.color.rgb = TEXT_MUTED
        p_cap.space_after = Pt(12)
        
        # Bullet Specs
        for spec in specs:
            p_spec = tf_box.add_paragraph()
            p_spec.text = spec
            p_spec.font.name = FONT_BODY
            p_spec.font.size = Pt(9.5)
            p_spec.font.color.rgb = TEXT_WHITE
            p_spec.space_after = Pt(6)

    # ----------------------------------------------------
    # SLIDE 9: Actual Operating Image (실제 작동 이미지 - Placeholder) - [NEW]
    # ----------------------------------------------------
    slide9 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide9)
    add_slide_header(slide9, "7. 실제 시스템 작동 시연 화면")
    
    # Large dotted/dashed placeholder area in the center
    # python-pptx doesn't easily set line styles to dash, but we can draw a beautiful box with guidance text
    placeholder = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.5))
    placeholder.fill.solid()
    placeholder.fill.fore_color.rgb = PANEL_COLOR
    placeholder.line.color.rgb = TEXT_MUTED
    placeholder.line.width = Pt(2.0)
    
    tf_place = placeholder.text_frame
    tf_place.word_wrap = True
    tf_place.margin_left = Inches(0.5)
    tf_place.margin_right = Inches(0.5)
    tf_place.margin_top = Inches(1.2)
    
    p_cam = tf_place.paragraphs[0]
    p_cam.text = "📷"
    p_cam.alignment = PP_ALIGN.CENTER
    p_cam.font.size = Pt(36)
    p_cam.space_after = Pt(10)
    
    p_msg1 = tf_place.add_paragraph()
    p_msg1.text = "[ 실제 작동 이미지 영역 ]"
    p_msg1.alignment = PP_ALIGN.CENTER
    p_msg1.font.name = FONT_TITLE
    p_msg1.font.size = Pt(18)
    p_msg1.font.bold = True
    p_msg1.font.color.rgb = COLOR_AMBER
    p_msg1.space_after = Pt(10)
    
    p_msg2 = tf_place.add_paragraph()
    p_msg2.text = "추후 제공해주실 실제 동작 화면 및 연동 회로 하드웨어 실물 이미지를 배치할 공간입니다.\n\n" \
                  "예시: 웹 대시보드(index.html) 예약 상태 카드 화면,\n" \
                  "라즈베리 파이 B 하드웨어(LED 신호등, 16x2 LCD 문자 출력, 부저) 조립 및 실습 장치 사진"
    p_msg2.alignment = PP_ALIGN.CENTER
    p_msg2.font.name = FONT_BODY
    p_msg2.font.size = Pt(13)
    p_msg2.font.color.rgb = TEXT_WHITE

    # ----------------------------------------------------
    # SLIDE 10: Future Potential (향후 발전 가능성) - [NEW]
    # ----------------------------------------------------
    slide10 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide10)
    add_slide_header(slide10, "8. 향후 시스템 발전 가능성")
    
    # 4 horizontal card bands describing enhancements
    potentials = [
        ("🌐 클라우드 데이터베이스 연동 확장", "현재는 로컬 data.json 데이터 저장소를 사용하여 동네 또는 단일 실습실 제어에 한정되어 있습니다. 향후 Firebase나 AWS 클라우드 RDB 및 NoSQL 연동을 적용하여, 전국에 분산된 공유회의실이나 스마트 물품 보관 지점들의 상태를 통합 제어하고 동기화할 수 있도록 대규모 분산 구조로 확장 가능합니다."),
        ("📱 전용 모바일 앱 및 하이브리드 PWA 연동", "사용자 접근성을 극대화하기 위해 반응형 웹을 넘어 전용 하이브리드 앱 또는 Progressive Web App(PWA)을 배포합니다. 실시간 잔여시간 만료 1분 전 및 노쇼 경고 시 모바일 푸시 알림(FCM Push Notification) 서비스를 연동하여 이용 회전 효과를 극대화합니다."),
        ("🔑 생체 정보 및 NFC 카드 본인인증 접목", "4자리 숫자를 입력하는 수동 PIN 번호 방식 외에, 라즈베리 파이에 NFC 리더기를 연동하여 학생증 카드나 사원증 태그를 접목하거나 지문 인식 모듈을 통해 보안성과 현장 사용 인증 편의성을 한 단계 업그레이드합니다."),
        ("📈 빅데이터 기반 자원 사용 분석 대시보드", "데이터베이스에 누적되는 예약 시간대, 기기별 가동률, 주로 취소/노쇼가 발생하는 원인을 인공지능 알고리즘과 BI 툴을 결합하여 분석합니다. 이를 통해 수요가 쏠리는 시간대의 예약 가중치 설정 및 공용 공간 자재 재배치 최적화 의사결정을 지원합니다.")
    ]
    
    col_w2 = Inches(5.6)
    col_h2 = Inches(2.1)
    
    for idx, (title, desc) in enumerate(potentials):
        col_idx = idx % 2
        row_idx = idx // 2
        
        left_pos = Inches(0.8) if col_idx == 0 else Inches(6.9)
        top_pos = Inches(1.8) if row_idx == 0 else Inches(4.3)
        
        card = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, top_pos, col_w2, col_h2)
        card.fill.solid()
        card.fill.fore_color.rgb = PANEL_COLOR
        card.line.color.rgb = COLOR_EMERALD if idx%2==0 else COLOR_AMBER
        card.line.width = Pt(1.5)
        
        tf_card = card.text_frame
        tf_card.word_wrap = True
        tf_card.margin_left = Inches(0.2)
        tf_card.margin_right = Inches(0.2)
        tf_card.margin_top = Inches(0.15)
        
        p = tf_card.paragraphs[0]
        p.text = title
        p.font.name = FONT_TITLE
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_EMERALD if idx%2==0 else COLOR_AMBER
        p.space_after = Pt(6)
        
        p_desc = tf_card.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = FONT_BODY
        p_desc.font.size = Pt(10.5)
        p_desc.font.color.rgb = TEXT_WHITE
        p_desc.space_after = Pt(4)

    # ----------------------------------------------------
    # SLIDE 11: Conclusions & Q&A
    # ----------------------------------------------------
    slide11 = prs.slides.add_slide(slide_layout)
    set_slide_background(slide11)
    add_slide_header(slide11, "9. 결론 및 기대효과")
    
    concl_panel = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.5))
    concl_panel.fill.solid()
    concl_panel.fill.fore_color.rgb = PANEL_COLOR
    concl_panel.line.color.rgb = COLOR_EMERALD
    concl_panel.line.width = Pt(1.5)
    
    tf_con = concl_panel.text_frame
    tf_con.word_wrap = True
    tf_con.margin_left = Inches(0.3)
    tf_con.margin_top = Inches(0.25)
    
    p = tf_con.paragraphs[0]
    p.text = "🌟 공유 자원의 효율적 운영과 질서 있는 공동체 문화 확립"
    p.font.name = FONT_TITLE
    p.font.size = Pt(20)
    p.font.color.rgb = COLOR_EMERALD
    p.font.bold = True
    p.space_after = Pt(16)
    
    conclusions = [
        "무단 점유 및 오용 방지: 4자리 PIN 기반 자율 인증 체계로 무단 상태 해제 및 점유 가로채기 갈등 해결",
        "자원 회전 효율의 공정 분배: 1초 주기 타이머 스케줄러가 노쇼 기기를 감지해 즉시 회수하고 사용 한도 강제 해제",
        "공용 물품 관리의 범위 대중화: 회의실 뿐만 아니라 PC, 학과 공유기, 소형 키트류 등 미세 공용물도 대시보드 연동",
        "감성적 피드백을 통한 사용 의식 개선: 시인성 높은 삼색 LED 신호등 및 기분 좋은 부저 음계가 규칙 준수 유도"
    ]
    for con_text in conclusions:
        p = tf_con.add_paragraph()
        p.text = "✔ " + con_text
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(6)
        p.space_after = Pt(8)

    # Save
    try:
        prs.save(filename)
        print(f"Presentation saved successfully as '{filename}'.")
    except PermissionError:
        base, ext = os.path.splitext(filename)
        fallback = f"{base}_new{ext}"
        prs.save(fallback)
        print(f"Permission denied for '{filename}' (likely open in PowerPoint). Saved as '{fallback}' instead.")

if __name__ == "__main__":
    out_file = "presentation.pptx"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    create_presentation(out_file)
