from datetime import datetime, timezone, timedelta, time
import json
import gspread
import requests
import streamlit as st

# -------------------------------------------------------------------
# 1. 페이지 기본 설정 및 세션 상태 초기화
# -------------------------------------------------------------------
st.set_page_config(
    page_title="소담터 - 사내 카페",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "app_theme" not in st.session_state:
    st.session_state["app_theme"] = "☕ 오리지널 커피 다크"

# -------------------------------------------------------------------
# 2. 테마 설정 및 커스텀 CSS
# -------------------------------------------------------------------
themes_config = {
    "☕ 오리지널 커피 다크": {
        "bg-base": "#120d0a",
        "bg-gradient-end": "#1a120d",
        "bg-elevated": "#1c140f",
        "bg-card": "#1f1712",
        "accent": "#c17a3d",
        "accent-light": "#e0a458",
        "text-primary": "#f5ece0",
        "text-secondary": "#b3a08c",
        "border-soft": "rgba(245, 236, 224, 0.08)",
        "card-radius": "28px",
        "button-radius": "14px",
        "shadow": "0 10px 34px rgba(193, 122, 61, 0.12)",
        "mug-stroke": "#e8dcc8",
        "glow-effect": "none",
    },
    "🌿 성수동 세이지 그린": {
        "bg-base": "#F4F6F4",
        "bg-gradient-end": "#EAEEEC",
        "bg-elevated": "#EAECEB",
        "bg-card": "#FFFFFF",
        "accent": "#4E8A6C",
        "accent-light": "#2D5A43",
        "text-primary": "#1C2E24",
        "text-secondary": "#6B7F74",
        "border-soft": "rgba(78, 138, 108, 0.15)",
        "card-radius": "16px",
        "button-radius": "8px",
        "shadow": "0 8px 24px rgba(78, 138, 108, 0.06)",
        "mug-stroke": "#2D5A43",
        "glow-effect": "none",
    },
    "☀️ 포근한 카라멜 우드": {
        "bg-base": "#FAF6F0",
        "bg-gradient-end": "#F5EDE4",
        "bg-elevated": "#F3EBE1",
        "bg-card": "#FFFFFF",
        "accent": "#D4A373",
        "accent-light": "#6C584C",
        "text-primary": "#3D342E",
        "text-secondary": "#8C7D73",
        "border-soft": "rgba(212, 163, 115, 0.18)",
        "card-radius": "24px",
        "button-radius": "18px",
        "shadow": "0 10px 30px rgba(212, 163, 115, 0.08)",
        "mug-stroke": "#6C584C",
        "glow-effect": "none",
    },
    "🎆 을지로 힙스토 네온": {
        "bg-base": "#0D0E15",
        "bg-gradient-end": "#05060A",
        "bg-elevated": "#161722",
        "bg-card": "#1A1B2A",
        "accent": "#FF7A00",
        "accent-light": "#00F0FF",
        "text-primary": "#FFFFFF",
        "text-secondary": "#8C8EAD",
        "border-soft": "rgba(0, 240, 255, 0.15)",
        "card-radius": "20px",
        "button-radius": "12px",
        "shadow": "0 10px 30px rgba(0, 240, 255, 0.15)",
        "mug-stroke": "#00F0FF",
        "glow-effect": "0 0 25px rgba(0, 240, 255, 0.25)",
    },
}

selected_theme = st.session_state["app_theme"]
t = themes_config[selected_theme]

custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

    :root {{
        --bg-base: {t['bg-base']};
        --bg-elevated: {t['bg-elevated']};
        --bg-card: {t['bg-card']};
        --accent: {t['accent']};
        --accent-light: {t['accent-light']};
        --text-primary: {t['text-primary']};
        --text-secondary: {t['text-secondary']};
        --border-soft: {t['border-soft']};
        --card-radius: {t['card-radius']};
        --button-radius: {t['button-radius']};
        --mug-stroke: {t['mug-stroke']};
    }}

    .stApp {{
        background: linear-gradient(160deg, var(--bg-base) 0%, {t['bg-gradient-end']} 100%);
        color: var(--text-primary);
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .main .block-container {{
        max-width: 430px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto;
    }}
    footer {{ visibility: hidden !important; height: 0px !important; }}

    /* 버튼 기본 스타일 */
    .stButton > button {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-radius: var(--button-radius) !important;
        border: 1px solid var(--border-soft) !important;
        padding: 8px 16px !important;
        width: 100%;
        font-weight: 600;
        transition: all 0.2s ease;
    }}
    .stButton > button:hover {{
        background-color: var(--accent) !important;
        border-color: var(--accent-light) !important;
        color: {("#1a120d" if "다크" in selected_theme or "네온" in selected_theme else "#ffffff")} !important;
    }}

    /* 커피 시그니처 카드 */
    .cup-card {{
        border-radius: var(--card-radius);
        padding: 24px 20px 18px;
        margin: 15px auto;
        max-width: 300px;
        text-align: center;
        background: {t['bg-card']};
        box-shadow: {t['shadow']};
    }}
    .cup-illustration {{
        width: 120px;
        height: auto;
        display: block;
        margin: 0 auto;
    }}
    .cup-title {{
        font-family: 'Gaegu', cursive;
        font-size: 30px;
        font-weight: 700;
        color: var(--text-primary);
        margin-top: 4px;
    }}
    .cup-hours {{
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 10px;
    }}
    .cup-badge {{
        display: inline-block;
        font-size: 13px;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 12px;
        border: 1px solid;
    }}

    /* 📱 퀵메뉴 앱 그리드 아이콘 버튼 스타일 */
    .quick-btn-box {{
        position: relative;
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 22px;
        aspect-ratio: 1 / 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        transition: transform 0.15s ease;
    }}
    .quick-btn-box:active {{
        transform: scale(0.95);
    }}
    .quick-badge {{
        position: absolute;
        top: -6px;
        right: -4px;
        font-size: 9px;
        font-weight: 800;
        color: #ffffff;
        padding: 2px 7px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .quick-icon {{
        font-size: 32px;
        line-height: 1;
        margin-bottom: 4px;
    }}
    .quick-label {{
        font-size: 12px;
        font-weight: 600;
        color: var(--text-primary);
        text-align: center;
        margin-top: 6px;
        white-space: nowrap;
    }}

    /* 배민 스타일 가로 스크롤 태그 */
    .filter-scroll-wrapper {{
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 10px;
        margin-bottom: 15px;
        -webkit-overflow-scrolling: touch;
    }}
    .filter-scroll-wrapper::-webkit-scrollbar {{
        display: none;
    }}

    /* 구내식당 식판 카드 */
    .diet-tray {{
        background: var(--bg-card);
        border: 1.5px solid var(--border-soft);
        border-radius: 20px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    }}
    .diet-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 12px;
    }}
    .diet-cell {{
        background: var(--bg-elevated);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        font-size: 13px;
        border: 1px solid var(--border-soft);
    }}
    .diet-main {{
        grid-column: span 2;
        background: rgba(193, 122, 61, 0.12);
        border: 1px solid var(--accent);
        font-weight: 700;
        color: var(--accent);
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

def safe_int(val, default=0):
    try:
        return int(float(str(val).strip())) if val is not None else default
    except (ValueError, TypeError):
        return default

# -------------------------------------------------------------------
# 3. 구글 시트 연동 & 기본 상태 계산
# -------------------------------------------------------------------
KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)

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
        return None
    try:
        doc = _gc.open("kiost_sodam")
        return doc.worksheet("재고")
    except Exception:
        return None

sheet_stock = get_sheets(gc)

@st.cache_data(ttl=10)
def fetch_stock_data():
    if not sheet_stock:
        return 0
    return sheet_stock.acell("B1").value

try:
    current_stock = safe_int(fetch_stock_data(), 0)
except Exception:
    current_stock = 0

if current_stock > 30:
    status_label = "🟢 이용가능"
    badge_bg, badge_color = "rgba(34, 197, 94, 0.15)", "#22c55e"
    cup_fill_y, theme_shadow, theme_border = 55, "0 10px 34px rgba(34, 197, 94, 0.12)", "rgba(34, 197, 94, 0.35)"
elif current_stock > 0:
    status_label = "🟡 소진임박"
    badge_bg, badge_color = "rgba(234, 179, 8, 0.15)", "#eab308"
    cup_fill_y, theme_shadow, theme_border = 100, "0 10px 34px rgba(234, 179, 8, 0.12)", "rgba(234, 179, 8, 0.35)"
else:
    status_label = "🔴 카페마감"
    badge_bg, badge_color = "rgba(239, 68, 68, 0.15)", "#ef4444"
    cup_fill_y, theme_shadow, theme_border = 140, "0 10px 34px rgba(239, 68, 68, 0.12)", "rgba(239, 68, 68, 0.35)"

# 커피잔 SVG 조립
_coffee_height = 140 - cup_fill_y
coffee_fill_svg = f'<rect x="20" y="{cup_fill_y}" width="120" height="{_coffee_height}" fill="var(--accent)" clip-path="url(#mugClip)" />' if _coffee_height > 0 else ""
mug_svg = (
    '<svg class="cup-illustration" viewBox="0 0 160 170" xmlns="http://www.w3.org/2000/svg">'
    '<defs><clipPath id="mugClip"><path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" /></clipPath></defs>'
    + coffee_fill_svg
    + '<path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" fill="none" stroke="var(--mug-stroke)" stroke-width="4" stroke-linejoin="round" />'
    '<path d="M135,55 C165,55 165,105 135,105" fill="none" stroke="var(--mug-stroke)" stroke-width="6" stroke-linecap="round" />'
    '</svg>'
)

# -------------------------------------------------------------------
# 4. 기능 대화상자 (Dialog Modal) 정의
# -------------------------------------------------------------------

# 1번: 금요일 퇴근시간 계산기
@st.dialog("⏰ 주 40시간 칼퇴 계산기")
def show_worktime_modal():
    st.write("목표 40시간 채우고 금요일에 바로 퇴근하세요!")
    col1, col2 = st.columns(2)
    with col1:
        prev_hours = st.number_input("목요일까지 누적(시간)", min_value=0, max_value=40, value=32, step=1)
    with col2:
        prev_minutes = st.number_input("누적(분)", min_value=0, max_value=59, value=0, step=5)

    fri_start = st.time_input("금요일 출근 시간", value=time(9, 0))
    deduct_lunch = st.checkbox("점심시간 1시간 제외", value=True)

    if st.button("퇴근 시간 계산하기", use_container_width=True):
        done_minutes = (prev_hours * 60) + prev_minutes
        remain_work_minutes = max(0, (40 * 60) - done_minutes)

        fri_start_dt = datetime.combine(datetime.today(), fri_start)
        lunch_offset = 60 if deduct_lunch else 0
        total_offset = remain_work_minutes + lunch_offset
        leave_dt = fri_start_dt + timedelta(minutes=total_offset)

        st.divider()
        if remain_work_minutes == 0:
            st.success("🎉 이미 주 40시간을 달성하셨습니다! 바로 퇴근 가능합니다.")
        else:
            remain_h, remain_m = divmod(remain_work_minutes, 60)
            st.info(f"오늘 채워야 할 순 근무시간: **{remain_h}시간 {remain_m}분**")
            st.markdown(
                f"<div style='text-align:center; padding:15px; background:rgba(34,197,94,0.12); border-radius:14px; border:1px solid #22c55e;'>"
                f"<span style='font-size:14px;'>금요일 퇴근 가능 시간</span><br>"
                f"<b style='font-size:26px; color:#22c55e;'>{leave_dt.strftime('%H:%M')}</b>"
                f"</div>",
                unsafe_allow_html=True
            )

# 2번: 주변 점심 맛집 리스트 (배민 스타일 필터)
@st.dialog("🍽️ 회사 근처 점심 맛집")
def show_restaurants_modal():
    restaurants = [
        {"name": "소담 한식뷔페", "category": "한식", "rating": "⭐ 4.8", "dist": "도보 3분", "menu": "제육볶음, 된장찌개"},
        {"name": "동화루 중화요리", "category": "중식", "rating": "⭐ 4.5", "dist": "도보 5분", "menu": "짬뽕, 간짜장, 탕수육"},
        {"name": "스시도담", "category": "일식", "rating": "⭐ 4.7", "dist": "도보 7분", "menu": "모듬초밥, 히레카츠"},
        {"name": "우리동네 떡볶이", "category": "분식", "rating": "⭐ 4.6", "dist": "도보 4분", "menu": "가래떡떡볶이, 모둠튀김"},
        {"name": "그린샐러드랩", "category": "샐러드", "rating": "⭐ 4.9", "dist": "도보 2분", "menu": "우삼겹 보울, 연어 샐러드"},
    ]

    categories = ["전체", "한식", "중식", "일식", "분식", "샐러드"]
    selected_cat = st.radio("카테고리 선택", categories, horizontal=True, label_visibility="collapsed")

    st.write("")
    filtered = [r for r in restaurants if selected_cat == "전체" or r["category"] == selected_cat]

    for item in filtered:
        st.markdown(
            f"""
            <div style="background:var(--bg-elevated); padding:12px 14px; border-radius:14px; border:1px solid var(--border-soft); margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:15px;">{item['name']}</b>
                    <span style="font-size:12px; color:var(--accent); font-weight:600;">{item['rating']}</span>
                </div>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">
                    {item['dist']} · 대표메뉴: {item['menu']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# 3번: 구내식당 식판 카드
@st.dialog("🍱 오늘 구내식당 점심 메뉴")
def show_cafeteria_modal():
    today_str = now_kst.strftime("%m월 %d일 (%a)")
    st.caption(f"📅 {today_str} 중식 (11:30 ~ 13:00)")

    st.markdown(
        """
        <div class="diet-tray">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; font-size:15px;">A코너: 든든한 정식</span>
                <span style="font-size:12px; background:rgba(34,197,94,0.15); color:#22c55e; padding:2px 8px; border-radius:8px; font-weight:bold;">운영중</span>
            </div>
            <div class="diet-grid">
                <div class="diet-cell diet-main">🥩 매콤 돼지갈비찜</div>
                <div class="diet-cell">🍚 흑미밥</div>
                <div class="diet-cell">🍲 소고기 미역국</div>
                <div class="diet-cell">🥗 해물잡채</div>
                <div class="diet-cell">🥬 겉절이 김치</div>
            </div>
            <div style="margin-top:12px; text-align:right; font-size:11px; color:var(--text-secondary);">
                열량: 820 kcal · 샐러드바 자율이용
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")
    with st.expander("🥗 B코너: 라이트/간편식 보기"):
        st.write("• 닭가슴살 아보카도 샐러드팩")
        st.write("• 착즙 감귤 주스")
        st.write("• 삶은 달걀 & 단호박")

# -------------------------------------------------------------------
# 5. 상단 헤더 & 커피잔 카드
# -------------------------------------------------------------------
st.markdown(
    f"""
<div class="top-header" style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;">
    <div>
        <div class="header-title" style="margin:0;">Good day ☕</div>
        <div class="header-sub" style="margin-top:2px;">Sodam-teo Cafe</div>
    </div>
    <a href="https://t.me/+n5J-xg8BI4tkYmE1" target="_blank" style="text-decoration:none; display:flex; flex-direction:column; align-items:center;">
        <div style="width:38px; height:38px; border-radius:50%; background:rgba(42, 171, 238, 0.15); display:flex; align-items:center; justify-content:center; border:1px solid rgba(42, 171, 238, 0.4); font-size:18px;">
            ✈️
        </div>
        <div style="font-size:10px; color:#2AAAEE; margin-top:3px; font-weight:600;">알람받기</div>
    </a>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="cup-card" style="box-shadow: {theme_shadow}; border: 1px solid {theme_border};">'
    f'{mug_svg}'
    f'<div class="cup-title">소담터</div>'
    f'<div class="cup-hours">운영시간 10:00 - 16:00</div>'
    f'<div class="cup-badge" style="color: {badge_color}; background: {badge_bg}; border-color: {badge_color}40;">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# 6. 하단 이미지 스타일 퀵메뉴 (스퀏클 디자인 그리드)
# -------------------------------------------------------------------
st.markdown("<div style='margin-top: 25px; margin-bottom: 12px; font-size: 14px; font-weight: 700; color: var(--text-secondary);'>사내 편의 서비스</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="quick-btn-box">
            <div class="quick-badge" style="background: #ef4444;">칼퇴</div>
            <div class="quick-icon">⏰</div>
        </div>
        <div class="quick-label">근무 계산기</div>
        """,
        unsafe_allow_html=True
    )
    if st.button("열기", key="btn_work", use_container_width=True):
        show_worktime_modal()

with col2:
    st.markdown(
        """
        <div class="quick-btn-box">
            <div class="quick-badge" style="background: #22c55e;">PICK</div>
            <div class="quick-icon">🍕</div>
        </div>
        <div class="quick-label">근처 맛집</div>
        """,
        unsafe_allow_html=True
    )
    if st.button("보기", key="btn_res", use_container_width=True):
        show_restaurants_modal()

with col3:
    st.markdown(
        """
        <div class="quick-btn-box">
            <div class="quick-badge" style="background: #0284c7;">오늘</div>
            <div class="quick-icon">🍱</div>
        </div>
        <div class="quick-label">구내식당</div>
        """,
        unsafe_allow_html=True
    )
    if st.button("조회", key="btn_diet", use_container_width=True):
        show_cafeteria_modal()

# -------------------------------------------------------------------
# 7. 사이드바 (테마 & 관리자)
# -------------------------------------------------------------------
st.sidebar.title("🎨 테마 설정")
st.sidebar.selectbox(
    "디자인 모드",
    list(themes_config.keys()),
    key="app_theme"
)

st.sidebar.divider()
st.sidebar.title("🔐 관리자 메뉴")
if "is_admin_logged_in" not in st.session_state:
    st.session_state.is_admin_logged_in = False

if not st.session_state.is_admin_logged_in:
    admin_pw = st.sidebar.text_input("비밀번호", type="password", key="admin_pw")
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
