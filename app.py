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

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "☀️ 라이트"

if "active_modal" not in st.session_state:
    st.session_state.active_modal = None

is_dark = (st.session_state.theme_mode == "🌙 다크")

# -------------------------------------------------------------------
# 2. 고대비 테마 팔레트 (선명한 명도 대비)
# -------------------------------------------------------------------
if is_dark:
    c = {
        "bg_app": "#0A1128",
        "card_bg": "#1C2541",
        "card_sub": "#263554",
        "border": "#3A506B",
        "border_bold": "#48CAE4",
        "text_main": "#FFFFFF",
        "text_sub": "#CBD5E1",
        "accent": "#48CAE4",
        "badge_bg": "#1E3A8A",
        "badge_border": "#60A5FA",
        "badge_text": "#93C5FD",
        "shadow": "0 4px 16px rgba(0, 0, 0, 0.4)",
        "mug_line": "#48CAE4",
        "mug_fill": "#0096C7",
    }
else:
    c = {
        "bg_app": "#F1F5F9",
        "card_bg": "#FFFFFF",
        "card_sub": "#F8FAFC",
        "border": "#94A3B8",
        "border_bold": "#003876",
        "text_main": "#0F172A",
        "text_sub": "#334155",
        "accent": "#003876",
        "badge_bg": "#DCFCE7",
        "badge_border": "#15803D",
        "badge_text": "#15803D",
        "shadow": "0 4px 14px rgba(0, 0, 0, 0.08)",
        "mug_line": "#003876",
        "mug_fill": "#0072CE",
    }

mobile_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&family=Noto+Sans+KR:wght@500;700;900&display=swap');

    /* 모바일 기본 폰트 스케일 및 배경 고정 */
    html, body, .stApp {{
        background-color: {c['bg_app']} !important;
        color: {c['text_main']} !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        font-size: 16px !important;
        -webkit-text-size-adjust: 100% !important;
        overflow-x: hidden !important;
    }}
    
    .main .block-container {{
        max-width: 430px !important;
        width: 100% !important;
        padding-top: 0.8rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 14px !important;
        padding-right: 14px !important;
        margin: 0 auto;
        box-sizing: border-box !important;
    }}
    footer {{ visibility: hidden !important; height: 0px !important; }}

    /* 라디오 버튼 텍스트 가독성 */
    div[data-testid="stRadio"] label p {{
        color: {c['text_main']} !important;
        font-weight: 800 !important;
        font-size: 13px !important;
    }}

    /* 커피 시그니처 카드 */
    .cup-card {{
        background: {c['card_bg']} !important;
        border: 2px solid {c['border']} !important;
        border-radius: 22px;
        padding: 18px 14px;
        margin: 10px auto;
        width: 100%;
        box-sizing: border-box;
        text-align: center;
        box-shadow: {c['shadow']};
    }}
    .cup-illustration {{
        width: 105px;
        height: auto;
        display: block;
        margin: 0 auto;
    }}
    .cup-title {{
        font-family: 'Gaegu', cursive !important;
        font-size: 30px !important;
        font-weight: 700 !important;
        color: {c['accent']} !important;
        margin-top: 4px;
    }}
    .cup-hours {{
        font-size: 13px !important;
        font-weight: 700 !important;
        color: {c['text_sub']} !important;
        margin-bottom: 8px;
    }}
    .cup-badge {{
        display: inline-block;
        font-size: 13px !important;
        font-weight: 800 !important;
        padding: 5px 16px;
        border-radius: 12px;
        border: 2px solid;
    }}

    /* 📱 모바일 1행 3열 그리드 강제 (가로 밀림 완전 방지) */
    div[data-testid="stHorizontalBlock"] {{
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 10px !important;
        width: 100% !important;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
        width: 100% !important;
        min-width: 0 !important;
        padding: 0 !important;
    }}

    /* 📱 정사각형(1:1) 버튼 & 큼직한 텍스트 */
    .square-btn {{
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
    }}
    .square-btn .stButton {{
        width: 100% !important;
        height: 100% !important;
    }}
    .square-btn .stButton > button {{
        width: 100% !important;
        height: 100% !important;
        aspect-ratio: 1 / 1 !important;
        background-color: {c['card_bg']} !important;
        border: 2px solid {c['border']} !important;
        border-radius: 18px !important;
        padding: 6px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: {c['shadow']} !important;
        transition: transform 0.1s ease !important;
    }}
    .square-btn .stButton > button:active {{
        transform: scale(0.95);
    }}
    .square-btn .stButton > button p {{
        color: {c['accent']} !important;
        font-weight: 900 !important;
        font-size: 14px !important;       /* 글자 크기 시원하게 확대 */
        line-height: 1.3 !important;
        margin: 0 !important;
        text-align: center !important;
        white-space: pre-line !important;
    }}

    /* 팝업 레이어 */
    .popup-box {{
        background: {c['card_bg']} !important;
        border: 2px solid {c['border_bold']} !important;
        border-radius: 20px;
        padding: 18px 14px;
        margin-top: 14px;
        box-shadow: {c['shadow']};
    }}

    .stTextInput input, .stNumberInput input, .stTimeInput input {{
        background-color: {c['card_sub']} !important;
        color: {c['text_main']} !important;
        border: 2px solid {c['border']} !important;
        font-size: 15px !important;
        font-weight: 700 !important;
    }}
    div[data-testid="stCheckbox"] label span {{
        color: {c['text_main']} !important;
        font-size: 14px !important;
        font-weight: 700 !important;
    }}
    .stTabs [data-baseweb="tab"] div {{
        color: {c['text_main']} !important;
        font-size: 14px !important;
        font-weight: 800 !important;
    }}
</style>
"""
st.markdown(mobile_css, unsafe_allow_html=True)

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
# 4. 상단 모바일 헤더
# -------------------------------------------------------------------
h_col1, h_col2, h_col3 = st.columns([5.2, 3.8, 1.0])

with h_col1:
    st.markdown(
        f"""
        <div style="font-size:11px; font-weight:800; color:{c['accent']}; letter-spacing:0.3px;">KIOST 사내 카페</div>
        <div style="font-family:'Gaegu', cursive; font-size:25px; font-weight:700; color:{c['text_main']}; margin-top:-3px;">소담터 알리미 ☕</div>
        """,
        unsafe_allow_html=True,
    )

with h_col2:
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

with h_col3:
    st.markdown(
        f"""
        <a href="https://t.me/+n5J-xg8BI4tkYmE1" target="_blank" style="text-decoration:none; display:flex; flex-direction:column; align-items:center;">
            <div style="width:34px; height:34px; border-radius:50%; background:{c['card_bg']}; display:flex; align-items:center; justify-content:center; border:1.5px solid {c['border']}; font-size:16px;">
                ✈️
            </div>
            <div style="font-size:9.5px; color:{c['text_sub']}; margin-top:2px; font-weight:800;">알람</div>
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
    f'<div class="cup-badge" style="color:{badge_color} !important; background:{badge_bg}; border-color:{badge_border};">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# 6. 하단 편의 서비스 (정사각형 1:1 버튼 & 선명한 글씨)
# -------------------------------------------------------------------
st.markdown(f"<div style='margin-top:16px; margin-bottom:8px; font-size:14px; font-weight:800; color:{c['text_sub']};'>KIOST 편의 서비스</div>", unsafe_allow_html=True)

btn_c1, btn_c2, btn_c3 = st.columns(3)

with btn_c1:
    st.markdown('<div class="square-btn">', unsafe_allow_html=True)
    if st.button("⏰\n근무 계산", key="btn_work", use_container_width=True):
        st.session_state.active_modal = "work" if st.session_state.active_modal != "work" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with btn_c2:
    st.markdown('<div class="square-btn">', unsafe_allow_html=True)
    if st.button("🍽️\n근처 맛집", key="btn_res", use_container_width=True):
        st.session_state.active_modal = "res" if st.session_state.active_modal != "res" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with btn_c3:
    st.markdown('<div class="square-btn">', unsafe_allow_html=True)
    if st.button("🍱\n구내 식당", key="btn_diet", use_container_width=True):
        st.session_state.active_modal = "diet" if st.session_state.active_modal != "diet" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# 7. 팝업 레이어 (오버레이 컨테이너)
# -------------------------------------------------------------------
if st.session_state.active_modal:
    st.markdown('<div class="popup-box">', unsafe_allow_html=True)
    t_col, close_c = st.columns([8.2, 1.8])
    with close_c:
        if st.button("✕", key="close_modal_btn", help="닫기"):
            st.session_state.active_modal = None
            st.rerun()

    # 1) 근무 계산기
    if st.session_state.active_modal == "work":
        with t_col:
            st.markdown(f"<div style='font-size:16px; font-weight:800; color:{c['text_main']};'>⏰ 주 40시간 칼퇴 계산기</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; color:{c['text_sub']}; font-weight:600; margin-bottom:8px;'>목요일까지 누적 시간을 입력하면 금요일 퇴근 시각을 계산합니다.</div>", unsafe_allow_html=True)
        
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
                st.info(f"오늘 채울 순 근무시간: **{remain_h}시간 {remain_m}분**")
                st.markdown(
                    f"<div style='text-align:center; padding:12px; background:{c['card_sub']}; border-radius:14px; border:2px solid {c['accent']}; margin-top:8px;'>"
                    f"<span style='font-size:13px; color:{c['text_sub']}; font-weight:800;'>금요일 퇴근 가능 시간</span><br>"
                    f"<b style='font-size:28px; color:{c['accent']}; font-weight:900;'>{leave_dt.strftime('%H:%M')}</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # 2) 맛집 리스트
    elif st.session_state.active_modal == "res":
        with t_col:
            st.markdown(f"<div style='font-size:16px; font-weight:800; color:{c['text_main']};'>🍽️ KIOST 근처 맛집</div>", unsafe_allow_html=True)
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
                <div style="background:{c['card_sub']}; padding:10px 12px; border-radius:12px; border:1px solid {c['border']}; margin-top:6px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:14.5px; color:{c['text_main']}; font-weight:800;">{item['name']}</b>
                        <span style="font-size:13px; color:{c['accent']}; font-weight:800;">{item['rating']}</span>
                    </div>
                    <div style="font-size:12.5px; color:{c['text_sub']}; margin-top:3px; font-weight:600;">
                        {item['dist']} · {item['menu']}
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
            st.markdown(f"<div style='font-size:16px; font-weight:800; color:{c['text_main']};'>🍱 오늘 구내식당 점심</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; color:{c['text_sub']}; font-weight:800; margin-bottom:8px;'>📅 {now_kst.strftime('%m월 %d일')} ({today_day_str}) 11:30~13:00</div>", unsafe_allow_html=True)

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
                        <div style="background:{c['card_sub']}; border:1.5px solid {c['border']}; border-radius:16px; padding:12px; margin-top:8px;">
                            <div style="background:{c['card_bg']}; border:1.5px solid {c['accent']}; border-radius:10px; padding:10px; text-align:center; font-weight:800; color:{c['accent']}; font-size:15px; margin-bottom:8px;">
                                🍲 {main_dish}
                            </div>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px;">
                        """
                        for dish in sub_dishes:
                            grid_html += f"""<div style="background:{c['card_bg']}; border-radius:8px; padding:8px; text-align:center; font-size:13px; color:{c['text_main']}; border:1px solid {c['border']}; font-weight:700;">🥢 {dish}</div>"""
                        if dessert and dessert not in ["-", "nan"]:
                            grid_html += f"""<div style="grid-column: span 2; background:#FFF7ED; border-radius:8px; padding:8px; text-align:center; font-size:13px; color:#C2410C; border:1.5px solid #FDBA74; font-weight:800;">🍦 후식: {dessert}</div>"""
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
