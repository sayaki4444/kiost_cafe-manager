from datetime import datetime, timezone, timedelta, time
import json
import gspread
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# 1. 페이지 기본 설정 및 상태 초기화
# -------------------------------------------------------------------
st.set_page_config(
    page_title="소담터 - KIOST 사내 카페",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)

# 기본 테마 상태 관리 ("라이트" or "다크")
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "☀️ 라이트"

if "active_modal" not in st.session_state:
    st.session_state.active_modal = None

is_dark = (st.session_state.theme_mode == "🌙 다크")

# -------------------------------------------------------------------
# 2. 확실한 명도 대비 KIOST 테마 팔레트 정의
# -------------------------------------------------------------------
if is_dark:
    # 🌙 다크 모드 (선명한 어둠 + 흰색/스카이블루 고대비)
    c = {
        "bg_app": "#0B132B",
        "card_bg": "#1C2541",
        "card_sub": "#263554",
        "border": "#3A506B",
        "border_bold": "#48CAE4",
        "text_main": "#FFFFFF",
        "text_sub": "#CBD5E1",
        "accent": "#48CAE4",           # 밝은 네온 스카이
        "accent_text": "#000000",
        "badge_bg": "#1E3A8A",
        "badge_border": "#60A5FA",
        "badge_text": "#93C5FD",
        "shadow": "0 8px 24px rgba(0, 0, 0, 0.4)",
        "mug_line": "#48CAE4",
        "mug_fill": "#0096C7",
    }
else:
    # ☀️ 라이트 모드 (깔끔한 화이트 + 딥 네이비 블랙 고대비)
    c = {
        "bg_app": "#F1F5F9",
        "card_bg": "#FFFFFF",
        "card_sub": "#F8FAFC",
        "border": "#CBD5E1",
        "border_bold": "#003876",
        "text_main": "#0F172A",       # 거의 검은색에 가까운 진한 네이비
        "text_sub": "#334155",
        "accent": "#003876",           # KIOST 딥오션 블루
        "accent_text": "#FFFFFF",
        "badge_bg": "#EFF6FF",
        "badge_border": "#003876",
        "badge_text": "#003876",
        "shadow": "0 8px 20px rgba(0, 56, 118, 0.08)",
        "mug_line": "#003876",
        "mug_fill": "#0072CE",
    }

custom_style = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap');

    /* 앱 전체 배경 및 기본 텍스트 강제 고대비 */
    .stApp {{
        background-color: {c['bg_app']} !important;
        color: {c['text_main']} !important;
        font-family: 'Noto Sans KR', sans-serif;
    }}
    .main .block-container {{
        max-width: 430px !important;
        padding-top: 1rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto;
    }}
    footer {{ visibility: hidden !important; height: 0px !important; }}

    /* 모든 기본 마크다운 글자색 고정 */
    p, span, label, div, h1, h2, h3, h4, h5, h6 {{
        color: {c['text_main']};
    }}

    /* 커피 시그니처 카드 */
    .cup-card {{
        background: {c['card_bg']} !important;
        border: 2px solid {c['border']} !important;
        border-radius: 24px;
        padding: 22px 16px 16px;
        margin: 12px auto;
        max-width: 310px;
        text-align: center;
        box-shadow: {c['shadow']};
    }}
    .cup-illustration {{
        width: 110px;
        height: auto;
        display: block;
        margin: 0 auto;
    }}
    .cup-title {{
        font-family: 'Gaegu', cursive;
        font-size: 30px;
        font-weight: 700;
        color: {c['accent']} !important;
        margin-top: 4px;
    }}
    .cup-hours {{
        font-size: 13px;
        font-weight: 600;
        color: {c['text_sub']} !important;
        margin-bottom: 8px;
    }}
    .cup-badge {{
        display: inline-block;
        font-size: 13px;
        font-weight: 800;
        padding: 5px 16px;
        border-radius: 12px;
        border: 1.5px solid;
    }}

    /* 📱 편의 서비스 3개 버튼 디자인 */
    div[data-testid="column"] .quick-service-btn button {{
        background-color: {c['card_bg']} !important;
        border: 2px solid {c['border']} !important;
        border-radius: 18px !important;
        padding: 12px 4px !important;
        min-height: 86px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: {c['shadow']} !important;
        transition: all 0.15s ease-in-out !important;
    }}
    div[data-testid="column"] .quick-service-btn button:hover {{
        border-color: {c['accent']} !important;
        background-color: {c['card_sub']} !important;
        transform: translateY(-2px);
    }}
    div[data-testid="column"] .quick-service-btn button p {{
        color: {c['accent']} !important;
        font-weight: 900 !important;
        font-size: 13.5px !important;
        line-height: 1.3 !important;
    }}

    /* 팝업 레이어 */
    .popup-box {{
        background: {c['card_bg']} !important;
        border: 2px solid {c['border_bold']} !important;
        border-radius: 20px;
        padding: 20px 16px;
        margin-top: 15px;
        box-shadow: {c['shadow']};
    }}

    /* 입력 폼 컨트롤 */
    .stTextInput input, .stNumberInput input, .stTimeInput input {{
        background-color: {c['card_sub']} !important;
        color: {c['text_main']} !important;
        border: 1.5px solid {c['border']} !important;
        font-weight: 600 !important;
    }}
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

def safe_int(val, default=0):
    try:
        return int(float(str(val).strip())) if val is not None else default
    except (ValueError, TypeError):
        return default

# -------------------------------------------------------------------
# 3. 구글 시트 연동
# -------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            secret_data = st.secrets["gcp_service_account"]
            creds_dict = json.loads(secret_data) if isinstance(secret_data, str) else dict(secret_data)
            return gspread.service_account_from_dict(creds_dict, scopes=SCOPES)
        return gspread.service_account(filename="service_account.json", scopes=SCOPES)
    except Exception:
        return None

gc = get_gspread_client()

@st.cache_resource
def get_sheets(_gc):
    if not _gc:
        return None, None, None
    try:
        doc = _gc.open("kiost_sodam")
        sheet_stock = doc.worksheet("재고")
        sheet_diet = doc.worksheet("식단")
        return doc, sheet_stock, sheet_diet
    except Exception:
        return None, None, None

doc, sheet_stock, sheet_diet = get_sheets(gc)

@st.cache_data(ttl=10)
def fetch_stock_data():
    if not sheet_stock:
        return 0
    try:
        return sheet_stock.acell("B1").value
    except Exception:
        return 0

@st.cache_data(ttl=60)
def fetch_diet_data():
    if not sheet_diet:
        return []
    try:
        return sheet_diet.get_all_records()
    except Exception:
        return []

current_stock = safe_int(fetch_stock_data(), 0)

# 카페 상태 색상 설정 (배경 대비 극대화)
if current_stock > 30:
    status_label = "🟢 이용가능"
    badge_bg, badge_border, badge_color = ("#064E3B", "#34D399", "#34D399") if is_dark else ("#DCFCE7", "#15803D", "#15803D")
    cup_fill_y = 55
elif current_stock > 0:
    status_label = "🟡 소진임박"
    badge_bg, badge_border, badge_color = ("#78350F", "#FBBF24", "#FBBF24") if is_dark else ("#FEF9C3", "#B45309", "#B45309")
    cup_fill_y = 100
else:
    status_label = "🔴 카페마감"
    badge_bg, badge_border, badge_color = ("#7F1D1D", "#F87171", "#F87171") if is_dark else ("#FEE2E2", "#B91C1C", "#B91C1C")
    cup_fill_y = 140

_coffee_height = 140 - cup_fill_y
coffee_fill_svg = f'<rect x="20" y="{cup_fill_y}" width="120" height="{_coffee_height}" fill="{c["mug_fill"]}" clip-path="url(#mugClip)" />' if _coffee_height > 0 else ""
mug_svg = (
    f'<svg class="cup-illustration" viewBox="0 0 160 170" xmlns="http://www.w3.org/2000/svg">'
    f'<defs><clipPath id="mugClip"><path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" /></clipPath></defs>'
    f'{coffee_fill_svg}'
    f'<path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" fill="none" stroke="{c["mug_line"]}" stroke-width="4" stroke-linejoin="round" />'
    f'<path d="M135,55 C165,55 165,105 135,105" fill="none" stroke="{c["mug_line"]}" stroke-width="6" stroke-linecap="round" />'
    f'</svg>'
)

# -------------------------------------------------------------------
# 4. 상단 헤더 (타이틀 + 명확한 라이트/다크 스위치 + 텔레그램)
# -------------------------------------------------------------------
header_col1, header_col2, header_col3 = st.columns([5, 3.8, 1.2])

with header_col1:
    st.markdown(
        f"""
        <div style="font-size:11px; font-weight:800; color:{c['accent']}; letter-spacing:0.5px;">KIOST 사내 카페</div>
        <div style="font-family:'Gaegu', cursive; font-size:26px; font-weight:700; color:{c['text_main']}; margin-top:-3px;">소담터 알리미 ☕</div>
        """,
        unsafe_allow_html=True,
    )

with header_col2:
    # ☀️ 라이트 < > 🌙 다크 직관적 세그먼트 스위치
    selected_theme = st.radio(
        "테마 모드",
        options=["☀️ 라이트", "🌙 다크"],
        index=1 if is_dark else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio_selector"
    )
    if selected_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = selected_theme
        st.rerun()

with header_col3:
    st.markdown(
        f"""
        <a href="https://t.me/+n5J-xg8BI4tkYmE1" target="_blank" style="text-decoration:none; display:flex; flex-direction:column; align-items:center;">
            <div style="width:36px; height:36px; border-radius:50%; background:{c['card_bg']}; display:flex; align-items:center; justify-content:center; border:2px solid {c['border']}; font-size:16px;">
                ✈️
            </div>
            <div style="font-size:9.5px; color:{c['text_sub']}; margin-top:2px; font-weight:700;">알람</div>
        </a>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------------------------
# 5. 커피잔 카드
# -------------------------------------------------------------------
st.markdown(
    f'<div class="cup-card">'
    f'{mug_svg}'
    f'<div class="cup-title">소담터</div>'
    f'<div class="cup-hours">운영시간 10:00 - 16:00</div>'
    f'<div class="cup-badge" style="color:{badge_color}; background:{badge_bg}; border-color:{badge_border};">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# 6. 하단 편의 서비스 (원클릭 팝업 트리거)
# -------------------------------------------------------------------
st.markdown(f"<p style='margin-top:16px; margin-bottom:8px; font-size:13px; font-weight:800; color:{c['text_sub']};'>KIOST 편의 서비스</p>", unsafe_allow_html=True)

btn_c1, btn_c2, btn_c3 = st.columns(3)

with btn_c1:
    st.markdown('<div class="quick-service-btn">', unsafe_allow_html=True)
    if st.button("⏰\n근무 계산기", key="btn_work", use_container_width=True):
        st.session_state.active_modal = "work" if st.session_state.active_modal != "work" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with btn_c2:
    st.markdown('<div class="quick-service-btn">', unsafe_allow_html=True)
    if st.button("🍽️\n근처 맛집", key="btn_res", use_container_width=True):
        st.session_state.active_modal = "res" if st.session_state.active_modal != "res" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with btn_c3:
    st.markdown('<div class="quick-service-btn">', unsafe_allow_html=True)
    if st.button("🍱\n구내식당", key="btn_diet", use_container_width=True):
        st.session_state.active_modal = "diet" if st.session_state.active_modal != "diet" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# 7. 간단한 팝업 레이어 (오버레이 컨테이너)
# -------------------------------------------------------------------
if st.session_state.active_modal:
    st.markdown('<div class="popup-box">', unsafe_allow_html=True)
    t_col, close_c = st.columns([8.5, 1.5])
    with close_c:
        if st.button("✕", key="close_modal_btn", help="닫기"):
            st.session_state.active_modal = None
            st.rerun()

    # 1) 근무 계산기
    if st.session_state.active_modal == "work":
        with t_col:
            st.markdown(f"<h4 style='margin:0; color:{c['text_main']};'>⏰ 주 40시간 칼퇴 계산기</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12.5px; color:{c['text_sub']}; font-weight:600;'>목요일까지 누적 시간을 입력하면 금요일 퇴근 시각을 계산합니다.</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            prev_hours = st.number_input("목요일까지 누적(시간)", min_value=0, max_value=40, value=32, step=1)
        with c2:
            prev_minutes = st.number_input("누적(분)", min_value=0, max_value=59, value=0, step=5)

        fri_start = st.time_input("금요일 출근 시각", value=time(9, 0))
        deduct_lunch = st.checkbox("점심시간 1시간 제외", value=True)

        if st.button("퇴근 시간 계산하기", key="btn_calc_run", use_container_width=True):
            done_minutes = (prev_hours * 60) + prev_minutes
            remain_work_minutes = max(0, (40 * 60) - done_minutes)
            fri_start_dt = datetime.combine(datetime.today(), fri_start)
            lunch_offset = 60 if deduct_lunch else 0
            leave_dt = fri_start_dt + timedelta(minutes=remain_work_minutes + lunch_offset)

            if remain_work_minutes == 0:
                st.success("🎉 이미 주 40시간을 달성하셨습니다! 바로 퇴근 가능합니다.")
            else:
                remain_h, remain_m = divmod(remain_work_minutes, 60)
                st.info(f"오늘 채워야 할 순 근무시간: **{remain_h}시간 {remain_m}분**")
                st.markdown(
                    f"<div style='text-align:center; padding:12px; background:{c['card_sub']}; border-radius:14px; border:2px solid {c['accent']}; margin-top:8px;'>"
                    f"<span style='font-size:12px; color:{c['text_sub']}; font-weight:700;'>금요일 퇴근 가능 시간</span><br>"
                    f"<b style='font-size:28px; color:{c['accent']}; font-weight:900;'>{leave_dt.strftime('%H:%M')}</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # 2) 맛집 리스트
    elif st.session_state.active_modal == "res":
        with t_col:
            st.markdown(f"<h4 style='margin:0; color:{c['text_main']};'>🍽️ KIOST 근처 맛집</h4>", unsafe_allow_html=True)
        restaurants = [
            {"name": "소담 한식뷔페", "category": "한식", "rating": "⭐ 4.8", "dist": "도보 3분", "menu": "제육볶음, 된장찌개"},
            {"name": "동화루 중화요리", "category": "중식", "rating": "⭐ 4.5", "dist": "도보 5분", "menu": "짬뽕, 간짜장, 탕수육"},
            {"name": "스시도담", "category": "일식", "rating": "⭐ 4.7", "dist": "도보 7분", "menu": "모듬초밥, 히레카츠"},
            {"name": "우리동네 떡볶이", "category": "분식", "rating": "⭐ 4.6", "dist": "도보 4분", "menu": "가래떡떡볶이, 모둠튀김"},
            {"name": "그린샐러드랩", "category": "샐러드", "rating": "⭐ 4.9", "dist": "도보 2분", "menu": "우삼겹 보울, 연어 샐러드"},
        ]
        categories = ["전체", "한식", "중식", "일식", "분식", "샐러드"]
        selected_cat = st.radio("카테고리 선택", categories, horizontal=True, label_visibility="collapsed")

        for item in [r for r in restaurants if selected_cat == "전체" or r["category"] == selected_cat]:
            st.markdown(
                f"""
                <div style="background:{c['card_sub']}; padding:10px 12px; border-radius:12px; border:1.5px solid {c['border']}; margin-top:6px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:14.5px; color:{c['text_main']};">{item['name']}</b>
                        <span style="font-size:12px; color:{c['accent']}; font-weight:800;">{item['rating']}</span>
                    </div>
                    <div style="font-size:12px; color:{c['text_sub']}; margin-top:2px; font-weight:600;">
                        {item['dist']} · 대표메뉴: {item['menu']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 3) 구내식당 식판
    elif st.session_state.active_modal == "diet":
        weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
        today_idx = now_kst.weekday()
        today_day_str = weekdays_kr[today_idx]
        today_date_slash = now_kst.strftime("%Y/%m/%d")

        with t_col:
            st.markdown(f"<h4 style='margin:0; color:{c['text_main']};'>🍱 오늘 구내식당 점심</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12.5px; color:{c['text_sub']}; font-weight:700;'>📅 {now_kst.strftime('%m월 %d일')} ({today_day_str}요일) 중식 11:30 ~ 13:00</p>", unsafe_allow_html=True)

        diet_list = fetch_diet_data()

        if today_idx >= 5:
            st.info("🌿 주말에는 구내식당을 운영하지 않습니다.")
        else:
            today_menus = [
                row for row in diet_list
                if str(row.get("날짜", "")).strip().replace("-", "/") == today_date_slash
                or str(row.get("요일", "")).strip() == today_day_str
            ]

            if not today_menus:
                st.warning("⚠️ 등록된 식단 정보가 없습니다.")
            else:
                tabs = st.tabs([f"📍 {m.get('메뉴구분', '중식')}" for m in today_menus]) if len(today_menus) > 1 else [st.container()]
                for idx, t_elem in enumerate(tabs):
                    with t_elem:
                        m_info = today_menus[idx]
                        dishes = [d.strip() for d in str(m_info.get("메뉴", "")).split(",") if d.strip()]
                        dessert = str(m_info.get("후식", "")).strip()
                        main_dish = dishes[0] if dishes else "메뉴 준비중"
                        sub_dishes = dishes[1:] if len(dishes) > 1 else []

                        grid_html = f"""
                        <div style="background:{c['card_sub']}; border:2px solid {c['border']}; border-radius:16px; padding:14px; margin-top:8px;">
                            <div style="background:{c['card_bg']}; border:2px solid {c['accent']}; border-radius:10px; padding:10px; text-align:center; font-weight:800; color:{c['accent']}; font-size:14.5px; margin-bottom:8px;">
                                🍲 {main_dish}
                            </div>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px;">
                        """
                        for dish in sub_dishes:
                            grid_html += f"""<div style="background:{c['card_bg']}; border-radius:8px; padding:8px; text-align:center; font-size:12.5px; color:{c['text_main']}; border:1.5px solid {c['border']}; font-weight:700;">🥢 {dish}</div>"""
                        if dessert and dessert not in ["-", "nan"]:
                            grid_html += f"""<div style="grid-column: span 2; background:#FFF7ED; border-radius:8px; padding:8px; text-align:center; font-size:12.5px; color:#C2410C; border:1.5px solid #FDBA74; font-weight:800;">🍦 후식: {dessert}</div>"""
                        grid_html += "</div></div>"
                        st.markdown(grid_html, unsafe_allow_html=True)

        with st.expander("📅 이번 주 전체 식단표 펼쳐보기"):
            if diet_list:
                df = pd.DataFrame(diet_list)
                cols = [col for col in ["날짜", "요일", "메뉴구분", "메뉴", "후식"] if col in df.columns]
                st.dataframe(df[cols] if cols else df, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# 8. 사이드바 (관리자 메뉴)
# -------------------------------------------------------------------
st.sidebar.title("🔐 관리자 메뉴")
if "is_admin_logged_in" not in st.session_state:
    st.session_state.is_admin_logged_in = False

if not st.session_state.is_admin_logged_in:
    admin_pw = st.sidebar.text_input("관리자 비밀번호", type="password", key="admin_pw")
    if st.sidebar.button("로그인", use_container_width=True):
        correct_pw = st.secrets.get("admin", {}).get("password", "1234")
        if admin_pw == correct_pw:
            st.session_state.is_admin_logged_in = True
            st.rerun()
        else:
            st.sidebar.error("비밀번호 오류")
else:
    st.sidebar.success("관리자 로그인 중")
    if st.sidebar.button("🟢 이용가능 (200잔)", use_container_width=True):
        if sheet_stock: sheet_stock.update_cell(1, 2, 200)
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("🟡 소진임박 (15잔)", use_container_width=True):
        if sheet_stock: sheet_stock.update_cell(1, 2, 15)
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("🔴 마감 (0잔)", use_container_width=True):
        if sheet_stock: sheet_stock.update_cell(1, 2, 0)
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.is_admin_logged_in = False
        st.rerun()
