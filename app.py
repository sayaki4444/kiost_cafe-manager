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

# 기본 테마: 라이트 모드
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# 활성화된 팝업 상태 (None, 'work', 'res', 'diet')
if "active_modal" not in st.session_state:
    st.session_state.active_modal = None

# -------------------------------------------------------------------
# 2. 다크 / 라이트 모드별 KIOST 컬러셋 및 CSS
# -------------------------------------------------------------------
if st.session_state.dark_mode:
    # 🌙 KIOST 다크 모드 팔레트
    theme = {
        "bg_gradient": "linear-gradient(180deg, #071526 0%, #0F2338 100%)",
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "card_bg": "#132A42",
        "border": "rgba(56, 189, 248, 0.2)",
        "accent": "#38BDF8",
        "button_bg": "#1A3654",
        "button_hover": "#234970",
        "sub_box": "#18324F",
        "modal_bg": "#0D1F33",
        "mug_stroke": "#38BDF8",
        "tray_border": "#38BDF8",
    }
else:
    # ☀️ KIOST 라이트 모드 팔레트
    theme = {
        "bg_gradient": "linear-gradient(180deg, #E8F1FA 0%, #F5F9FC 100%)",
        "text_primary": "#0A1C30",
        "text_secondary": "#334E68",
        "card_bg": "#FFFFFF",
        "border": "rgba(0, 56, 118, 0.16)",
        "accent": "#003876",
        "button_bg": "#FFFFFF",
        "button_hover": "#EFF6FF",
        "sub_box": "#F1F5F9",
        "modal_bg": "#FFFFFF",
        "mug_stroke": "#003876",
        "tray_border": "#CBD5E1",
    }

kiost_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

    .stApp {{
        background: {theme['bg_gradient']} !important;
        color: {theme['text_primary']} !important;
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

    /* 텍스트 가독성 */
    p, span, label, div, h1, h2, h3, h4, h5, h6 {{
        color: {theme['text_primary']};
    }}

    /* 커피 시그니처 카드 */
    .cup-card {{
        border-radius: 24px;
        padding: 20px 16px 14px;
        margin: 10px auto;
        max-width: 300px;
        text-align: center;
        background: {theme['card_bg']};
        border: 1.5px solid {theme['border']};
        box-shadow: 0 8px 24px rgba(0, 56, 118, 0.08);
    }}
    .cup-illustration {{
        width: 105px;
        height: auto;
        display: block;
        margin: 0 auto;
    }}
    .cup-title {{
        font-family: 'Gaegu', cursive;
        font-size: 28px;
        font-weight: 700;
        color: {theme['accent']} !important;
        margin-top: 4px;
    }}
    .cup-hours {{
        font-size: 12px;
        font-weight: 600;
        color: {theme['text_secondary']} !important;
        margin-bottom: 8px;
    }}
    .cup-badge {{
        display: inline-block;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 12px;
        border: 1.5px solid;
    }}

    /* 📱 3개 퀵메뉴 버튼 */
    div[data-testid="column"] .quick-box button {{
        background-color: {theme['button_bg']} !important;
        border: 1.5px solid {theme['border']} !important;
        border-radius: 18px !important;
        padding: 10px 4px !important;
        min-height: 84px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
    }}
    div[data-testid="column"] .quick-box button p {{
        color: {theme['accent']} !important;
        font-weight: 800 !important;
        font-size: 13px !important;
        margin: 0 !important;
        line-height: 1.3 !important;
    }}
    div[data-testid="column"] .quick-box button:hover {{
        background-color: {theme['button_hover']} !important;
        transform: translateY(-2px);
    }}

    /* 헤더 테마 토글 버튼 스타일 */
    .theme-toggle-box button {{
        background-color: {theme['card_bg']} !important;
        border: 1.5px solid {theme['border']} !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 18px !important;
    }}

    /* 팝업 레이어 스타일 */
    .modal-overlay {{
        background: {theme['modal_bg']};
        border: 2px solid {theme['border']};
        border-radius: 20px;
        padding: 20px 16px;
        margin-top: 15px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    }}

    /* 입력 폼 컨트롤 */
    .stTextInput input, .stNumberInput input, .stTimeInput input {{
        background-color: {theme['card_bg']} !important;
        color: {theme['text_primary']} !important;
        border: 1.5px solid {theme['border']} !important;
    }}
</style>
"""
st.markdown(kiost_css, unsafe_allow_html=True)

def safe_int(val, default=0):
    try:
        return int(float(str(val).strip())) if val is not None else default
    except (ValueError, TypeError):
        return default

# -------------------------------------------------------------------
# 3. 구글 시트 데이터 연동
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
    badge_bg, badge_color = ("#064E3B", "#34D399") if st.session_state.dark_mode else ("#DCFCE7", "#15803D")
    cup_fill_y = 55
elif current_stock > 0:
    status_label = "🟡 소진임박"
    badge_bg, badge_color = ("#78350F", "#FBBF24") if st.session_state.dark_mode else ("#FEF9C3", "#A16207")
    cup_fill_y = 100
else:
    status_label = "🔴 카페마감"
    badge_bg, badge_color = ("#7F1D1D", "#F87171") if st.session_state.dark_mode else ("#FEE2E2", "#B91C1C")
    cup_fill_y = 140

_coffee_height = 140 - cup_fill_y
coffee_fill_svg = f'<rect x="20" y="{cup_fill_y}" width="120" height="{_coffee_height}" fill="#0072CE" clip-path="url(#mugClip)" />' if _coffee_height > 0 else ""
mug_svg = (
    f'<svg class="cup-illustration" viewBox="0 0 160 170" xmlns="http://www.w3.org/2000/svg">'
    f'<defs><clipPath id="mugClip"><path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" /></clipPath></defs>'
    f'{coffee_fill_svg}'
    f'<path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" fill="none" stroke="{theme["mug_stroke"]}" stroke-width="4" stroke-linejoin="round" />'
    f'<path d="M135,55 C165,55 165,105 135,105" fill="none" stroke="{theme["mug_stroke"]}" stroke-width="6" stroke-linecap="round" />'
    f'</svg>'
)

# -------------------------------------------------------------------
# 4. 상단 헤더 (다크모드 스위치 + 텔레그램 버튼)
# -------------------------------------------------------------------
h_col1, h_col2, h_col3 = st.columns([7, 1.5, 1.5])

with h_col1:
    st.markdown(
        f"""
        <div style="font-size:11px; font-weight:800; color:{theme['accent']}; letter-spacing:0.5px;">KIOST 사내 카페</div>
        <div style="font-family:'Gaegu', cursive; font-size:26px; font-weight:700; color:{theme['text_primary']}; margin-top:-3px;">소담터 알리미 ☕</div>
        """,
        unsafe_allow_html=True,
    )

with h_col2:
    st.markdown('<div class="theme-toggle-box">', unsafe_allow_html=True)
    toggle_icon = "☀️" if st.session_state.dark_mode else "🌙"
    if st.button(toggle_icon, key="theme_toggle_btn", help="다크/라이트 모드 전환"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with h_col3:
    st.markdown(
        f"""
        <a href="https://t.me/+n5J-xg8BI4tkYmE1" target="_blank" style="text-decoration:none; display:flex; flex-direction:column; align-items:center;">
            <div style="width:38px; height:38px; border-radius:50%; background:{theme['card_bg']}; display:flex; align-items:center; justify-content:center; border:1.5px solid {theme['border']}; font-size:18px;">
                ✈️
            </div>
            <div style="font-size:9.5px; color:{theme['text_secondary']}; margin-top:2px; font-weight:700;">알람</div>
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
    f'<div class="cup-badge" style="color:{badge_color}; background:{badge_bg}; border-color:{badge_color};">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# 6. 하단 편의 서비스 (원클릭 팝업 트리거)
# -------------------------------------------------------------------
st.markdown(f"<p style='margin-top:16px; margin-bottom:8px; font-size:13px; font-weight:800; color:{theme['text_secondary']};'>KIOST 편의 서비스</p>", unsafe_allow_html=True)

b_col1, b_col2, b_col3 = st.columns(3)

with b_col1:
    st.markdown('<div class="quick-box">', unsafe_allow_html=True)
    if st.button("⏰\n근무 계산기", key="btn_work", use_container_width=True):
        st.session_state.active_modal = "work" if st.session_state.active_modal != "work" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with b_col2:
    st.markdown('<div class="quick-box">', unsafe_allow_html=True)
    if st.button("🍽️\n근처 맛집", key="btn_res", use_container_width=True):
        st.session_state.active_modal = "res" if st.session_state.active_modal != "res" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with b_col3:
    st.markdown('<div class="quick-box">', unsafe_allow_html=True)
    if st.button("🍱\n구내식당", key="btn_diet", use_container_width=True):
        st.session_state.active_modal = "diet" if st.session_state.active_modal != "diet" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# 7. 인-페이지 오버레이 모달 팝업 레이어 (새 창 전환 방지)
# -------------------------------------------------------------------
if st.session_state.active_modal:
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    top_col, close_col = st.columns([8.5, 1.5])
    with close_col:
        if st.button("✕", key="close_modal_btn", help="닫기"):
            st.session_state.active_modal = None
            st.rerun()

    # 1) 근무시간 계산기 팝업
    if st.session_state.active_modal == "work":
        with top_col:
            st.markdown(f"<h4 style='margin:0; color:{theme['text_primary']};'>⏰ 주 40시간 칼퇴 계산기</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12.5px; color:{theme['text_secondary']};'>목요일 누적 근무시간을 입력하면 금요일 퇴근 시간을 계산합니다.</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            prev_hours = st.number_input("목요일까지 누적(시간)", min_value=0, max_value=40, value=32, step=1)
        with c2:
            prev_minutes = st.number_input("누적(분)", min_value=0, max_value=59, value=0, step=5)

        fri_start = st.time_input("금요일 출근 시각", value=time(9, 0))
        deduct_lunch = st.checkbox("점심시간 1시간 제외", value=True)

        if st.button("계산하기", key="calc_run_btn", use_container_width=True):
            done_minutes = (prev_hours * 60) + prev_minutes
            remain_work_minutes = max(0, (40 * 60) - done_minutes)
            fri_start_dt = datetime.combine(datetime.today(), fri_start)
            lunch_offset = 60 if deduct_lunch else 0
            leave_dt = fri_start_dt + timedelta(minutes=remain_work_minutes + lunch_offset)

            if remain_work_minutes == 0:
                st.success("🎉 이미 주 40시간을 채우셨습니다! 바로 퇴근 가능합니다.")
            else:
                remain_h, remain_m = divmod(remain_work_minutes, 60)
                st.info(f"오늘 채워야 할 순 근무시간: **{remain_h}시간 {remain_m}분**")
                st.markdown(
                    f"<div style='text-align:center; padding:12px; background:{theme['sub_box']}; border-radius:12px; border:1.5px solid {theme['accent']}; margin-top:8px;'>"
                    f"<span style='font-size:12px; color:{theme['text_secondary']};'>금요일 퇴근 가능 시간</span><br>"
                    f"<b style='font-size:26px; color:{theme['accent']};'>{leave_dt.strftime('%H:%M')}</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # 2) 근처 맛집 팝업
    elif st.session_state.active_modal == "res":
        with top_col:
            st.markdown(f"<h4 style='margin:0; color:{theme['text_primary']};'>🍽️ KIOST 근처 맛집</h4>", unsafe_allow_html=True)
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
                <div style="background:{theme['sub_box']}; padding:10px 12px; border-radius:12px; border:1px solid {theme['border']}; margin-top:6px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:14px; color:{theme['text_primary']};">{item['name']}</b>
                        <span style="font-size:12px; color:#0284C7; font-weight:800;">{item['rating']}</span>
                    </div>
                    <div style="font-size:12px; color:{theme['text_secondary']}; margin-top:2px;">
                        {item['dist']} · 대표메뉴: {item['menu']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 3) 구내식당 식판 팝업
    elif st.session_state.active_modal == "diet":
        weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
        today_idx = now_kst.weekday()
        today_day_str = weekdays_kr[today_idx]
        today_date_str = now_kst.strftime("%Y/%m/%d")

        with top_col:
            st.markdown(f"<h4 style='margin:0; color:{theme['text_primary']};'>🍱 오늘 구내식당 점심</h4>", unsafe_allow_html=True)
        st.caption(f"📅 {now_kst.strftime('%m월 %d일')} ({today_day_str}요일) 중식 11:30 ~ 13:00")

        diet_list = fetch_diet_data()

        if today_idx >= 5:
            st.info("🌿 주말에는 구내식당을 운영하지 않습니다.")
        else:
            today_menus = [
                row for row in diet_list
                if str(row.get("날짜", "")).strip().replace("-", "/") == today_date_str
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
                        <div style="background:{theme['sub_box']}; border:1.5px solid {theme['tray_border']}; border-radius:16px; padding:14px; margin-top:8px;">
                            <div style="background:{theme['card_bg']}; border:1.5px solid {theme['accent']}; border-radius:10px; padding:10px; text-align:center; font-weight:800; color:{theme['accent']}; font-size:14px; margin-bottom:8px;">
                                🍲 {main_dish}
                            </div>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px;">
                        """
                        for dish in sub_dishes:
                            grid_html += f"""<div style="background:{theme['card_bg']}; border-radius:8px; padding:8px; text-align:center; font-size:12px; color:{theme['text_primary']}; border:1px solid {theme['border']}; font-weight:600;">🥢 {dish}</div>"""
                        if dessert and dessert not in ["-", "nan"]:
                            grid_html += f"""<div style="grid-column: span 2; background:#FFF7ED; border-radius:8px; padding:8px; text-align:center; font-size:12px; color:#C2410C; border:1px solid #FDBA74; font-weight:800;">🍦 후식: {dessert}</div>"""
                        grid_html += "</div></div>"
                        st.markdown(grid_html, unsafe_allow_html=True)

        with st.expander("📅 이번 주 전체 식단표 펼쳐보기"):
            if diet_list:
                df = pd.DataFrame(diet_list)
                cols = [c for c in ["날짜", "요일", "메뉴구분", "메뉴", "후식"] if c in df.columns]
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
