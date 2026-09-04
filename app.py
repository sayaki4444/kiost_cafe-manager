from datetime import datetime, timezone, timedelta, time
import json
import gspread
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# 1. 페이지 기본 설정
# -------------------------------------------------------------------
st.set_page_config(
    page_title="소담터 - KIOST 사내 카페",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------------
# 2. KIOST 블루톤 테마 & 일체형 퀵버튼 커스텀 CSS
# -------------------------------------------------------------------
kiost_blue_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

    :root {
        --kiost-primary: #003876;       /* 딥 오션 블루 */
        --kiost-secondary: #0072CE;     /* 마린 블루 */
        --kiost-light: #E8F1F8;         /* 연한 블루 배경 */
        --kiost-teal: #00838F;
        --bg-gradient-start: #EBF3FA;
        --bg-gradient-end: #F4F8FC;
        --card-bg: #FFFFFF;
        --text-main: #0B2545;
        --text-sub: #5C768D;
        --border-color: rgba(0, 56, 118, 0.12);
    }

    .stApp {
        background: linear-gradient(180deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
        color: var(--text-main);
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main .block-container {
        max-width: 430px !important;
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto;
    }
    footer { visibility: hidden !important; height: 0px !important; }

    /* 커피 시그니처 카드 */
    .cup-card {
        border-radius: 24px;
        padding: 22px 18px 16px;
        margin: 12px auto;
        max-width: 300px;
        text-align: center;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 24px rgba(0, 56, 118, 0.08);
    }
    .cup-illustration {
        width: 110px;
        height: auto;
        display: block;
        margin: 0 auto;
    }
    .cup-title {
        font-family: 'Gaegu', cursive;
        font-size: 28px;
        font-weight: 700;
        color: var(--kiost-primary);
        margin-top: 4px;
    }
    .cup-hours {
        font-size: 12px;
        color: var(--text-sub);
        margin-bottom: 8px;
    }
    .cup-badge {
        display: inline-block;
        font-size: 12.5px;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 12px;
        border: 1px solid;
    }

    /* 📱 일체형 컴팩트 퀵버튼 컨테이너 */
    div[data-testid="column"] .stButton > button {
        background-color: var(--card-bg) !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 18px !important;
        padding: 12px 6px 10px 6px !important;
        height: auto !important;
        min-height: 86px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 12px rgba(0, 56, 118, 0.05) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        border-color: var(--kiost-secondary) !important;
        background-color: #F0F6FC !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 114, 206, 0.15) !important;
    }
    div[data-testid="column"] .stButton > button:active {
        transform: scale(0.96);
    }

    /* 버튼 내부 텍스트 및 이모지 스타일 커스텀 */
    div[data-testid="column"] .stButton > button p {
        margin: 0 !important;
        line-height: 1.3 !important;
        white-space: pre-line !important;
    }

    /* 다이얼로그 모달 내부 탭/버튼 스타일 */
    .stDialog .stButton > button {
        background-color: var(--kiost-primary) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }
</style>
"""
st.markdown(kiost_blue_css, unsafe_allow_html=True)

def safe_int(val, default=0):
    try:
        return int(float(str(val).strip())) if val is not None else default
    except (ValueError, TypeError):
        return default

# -------------------------------------------------------------------
# 3. 구글 시트 연동 ('식단' 탭 자동 생성 및 읽기)
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
        return None, None, None
    try:
        doc = _gc.open("kiost_sodam")
        sheet_stock = doc.worksheet("재고")

        try:
            sheet_diet = doc.worksheet("식단")
        except gspread.WorksheetNotFound:
            sheet_diet = doc.add_worksheet(title="식단", rows=20, cols=6)
            default_headers = ["요일", "메인메뉴", "밥/국", "반찬1", "반찬2", "김치/기타"]
            sample_diet = [
                default_headers,
                ["월", "제육볶음", "흑미밥 / 콩나물국", "계란찜", "청경채나물", "깍두기"],
                ["화", "닭볶음탕", "기장밥 / 된장찌개", "해물파전", "도토리묵", "배추김치"],
                ["수", "등심돈까스", "쌀밥 / 크림스프", "마카로니샐러드", "모닝빵/딸기잼", "피클/깍두기"],
                ["목", "소불고기", "현미밥 / 소고기뭇국", "잡채", "시금치무침", "열무김치"],
                ["금", "돼지갈비찜", "흑미밥 / 미역국", "동그랑땡", "콩자반", "겉절이"]
            ]
            sheet_diet.update("A1:F6", sample_diet)

        return doc, sheet_stock, sheet_diet
    except Exception:
        return None, None, None

doc, sheet_stock, sheet_diet = get_sheets(gc)

@st.cache_data(ttl=10)
def fetch_stock_data():
    if not sheet_stock:
        return 0
    return sheet_stock.acell("B1").value

@st.cache_data(ttl=300)
def fetch_diet_data():
    if not sheet_diet:
        return []
    try:
        return sheet_diet.get_all_records()
    except Exception:
        return []

try:
    current_stock = safe_int(fetch_stock_data(), 0)
except Exception:
    current_stock = 0

if current_stock > 30:
    status_label = "🟢 이용가능"
    badge_bg, badge_color = "rgba(16, 185, 129, 0.12)", "#059669"
    cup_fill_y = 55
elif current_stock > 0:
    status_label = "🟡 소진임박"
    badge_bg, badge_color = "rgba(245, 158, 11, 0.12)", "#d97706"
    cup_fill_y = 100
else:
    status_label = "🔴 카페마감"
    badge_bg, badge_color = "rgba(239, 68, 68, 0.12)", "#dc2626"
    cup_fill_y = 140

_coffee_height = 140 - cup_fill_y
coffee_fill_svg = f'<rect x="20" y="{cup_fill_y}" width="120" height="{_coffee_height}" fill="#0072CE" clip-path="url(#mugClip)" />' if _coffee_height > 0 else ""
mug_svg = (
    '<svg class="cup-illustration" viewBox="0 0 160 170" xmlns="http://www.w3.org/2000/svg">'
    '<defs><clipPath id="mugClip"><path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" /></clipPath></defs>'
    + coffee_fill_svg
    + '<path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" fill="none" stroke="#003876" stroke-width="4" stroke-linejoin="round" />'
    '<path d="M135,55 C165,55 165,105 135,105" fill="none" stroke="#003876" stroke-width="6" stroke-linecap="round" />'
    '</svg>'
)

# -------------------------------------------------------------------
# 4. 기능 팝업 모달
# -------------------------------------------------------------------

# 1번: 퇴근 계산기
@st.dialog("⏰ 주 40시간 칼퇴 계산기")
def show_worktime_modal():
    st.write("목표 40시간 달성 후 금요일 조기/정시 퇴근 시각 계산")
    col1, col2 = st.columns(2)
    with col1:
        prev_hours = st.number_input("목요일까지 누적(시간)", min_value=0, max_value=40, value=32, step=1)
    with col2:
        prev_minutes = st.number_input("누적(분)", min_value=0, max_value=59, value=0, step=5)

    fri_start = st.time_input("금요일 출근 시각", value=time(9, 0))
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
            st.info(f"오늘 필요한 순 근무시간: **{remain_h}시간 {remain_m}분**")
            st.markdown(
                f"<div style='text-align:center; padding:15px; background:rgba(0,56,118,0.06); border-radius:14px; border:1.5px solid #003876;'>"
                f"<span style='font-size:13px; color:#5C768D; font-weight:600;'>금요일 퇴근 가능 시간</span><br>"
                f"<b style='font-size:26px; color:#003876;'>{leave_dt.strftime('%H:%M')}</b>"
                f"</div>",
                unsafe_allow_html=True
            )

# 2번: 주변 맛집
@st.dialog("🍽️ KIOST 근처 점심 맛집")
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

    filtered = [r for r in restaurants if selected_cat == "전체" or r["category"] == selected_cat]

    for item in filtered:
        st.markdown(
            f"""
            <div style="background:#EBF3FA; padding:12px 14px; border-radius:14px; border:1px solid rgba(0,56,118,0.1); margin-top:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:15px; color:#003876;">{item['name']}</b>
                    <span style="font-size:12px; color:#0072CE; font-weight:700;">{item['rating']}</span>
                </div>
                <div style="font-size:12px; color:#5C768D; margin-top:2px;">
                    {item['dist']} · 대표메뉴: {item['menu']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# 3번: 구내식당 식판 모달
@st.dialog("🍱 오늘 구내식당 점심 메뉴")
def show_cafeteria_modal():
    weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today_weekday_idx = now_kst.weekday()
    today_weekday_str = weekdays_kr[today_weekday_idx]
    today_str = now_kst.strftime("%m월 %d일")

    st.caption(f"📅 {today_str} ({today_weekday_str}요일) 중식 11:30 ~ 13:00")

    diet_list = fetch_diet_data()
    today_menu = None
    if diet_list:
        for row in diet_list:
            if str(row.get("요일", "")).strip() == today_weekday_str:
                today_menu = row
                break

    if today_weekday_idx >= 5:
        st.info("🌿 주말에는 구내식당을 운영하지 않습니다.")
    elif today_menu:
        main_dish = today_menu.get("메인메뉴", "식단 정보 없음")
        rice_soup = today_menu.get("밥/국", "밥 / 국")
        side1 = today_menu.get("반찬1", "-")
        side2 = today_menu.get("반찬2", "-")
        kimchi = today_menu.get("김치/기타", "김치")

        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1.5px solid rgba(0,56,118,0.12); border-radius:18px; padding:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:800; font-size:15px; color:#003876;">KIOST 오늘의 중식</span>
                    <span style="font-size:12px; background:rgba(0,114,206,0.12); color:#0072CE; padding:3px 8px; border-radius:8px; font-weight:bold;">운영중</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:12px;">
                    <div style="grid-column: span 2; background:rgba(0,56,118,0.06); border:1.5px solid #003876; border-radius:10px; padding:10px; text-align:center; font-weight:800; color:#003876;">🥩 {main_dish}</div>
                    <div style="background:#F4F8FC; border-radius:10px; padding:8px; text-align:center; font-size:13px; border:1px solid rgba(0,56,118,0.08);">🍚 {rice_soup}</div>
                    <div style="background:#F4F8FC; border-radius:10px; padding:8px; text-align:center; font-size:13px; border:1px solid rgba(0,56,118,0.08);">🥗 {side1}</div>
                    <div style="background:#F4F8FC; border-radius:10px; padding:8px; text-align:center; font-size:13px; border:1px solid rgba(0,56,118,0.08);">🍳 {side2}</div>
                    <div style="background:#F4F8FC; border-radius:10px; padding:8px; text-align:center; font-size:13px; border:1px solid rgba(0,56,118,0.08);">🥬 {kimchi}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ 이번 주 식단 데이터가 등록되지 않았습니다.")

    st.write("")
    with st.expander("📅 이번 주 전체 식단표 펼쳐보기"):
        if diet_list:
            df = pd.DataFrame(diet_list)
            st.dataframe(df, use_container_width=True, hide_index=True)

# -------------------------------------------------------------------
# 5. 상단 헤더 & 커피잔 카드
# -------------------------------------------------------------------
st.markdown(
    """
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
    <div>
        <div style="font-size:11px; font-weight:800; color:#0072CE; letter-spacing:0.5px;">KIOST 사내 카페</div>
        <div style="font-family:'Gaegu', cursive; font-size:26px; font-weight:700; color:#003876; margin-top:-2px;">소담터 알리미 ☕</div>
    </div>
    <a href="https://t.me/+n5J-xg8BI4tkYmE1" target="_blank" style="text-decoration:none; display:flex; flex-direction:column; align-items:center;">
        <div style="width:36px; height:36px; border-radius:50%; background:rgba(0,114,206,0.12); display:flex; align-items:center; justify-content:center; border:1.5px solid rgba(0,114,206,0.3); font-size:17px;">
            ✈️
        </div>
        <div style="font-size:10px; color:#0072CE; margin-top:2px; font-weight:700;">알람받기</div>
    </a>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="cup-card">'
    f'{mug_svg}'
    f'<div class="cup-title">소담터</div>'
    f'<div class="cup-hours">운영시간 10:00 - 16:00</div>'
    f'<div class="cup-badge" style="color:{badge_color}; background:{badge_bg}; border-color:{badge_color}40;">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# 6. 하단 편의 서비스 (일체형 원클릭 컴팩트 버튼)
# -------------------------------------------------------------------
st.markdown("<div style='margin-top:20px; margin-bottom:10px; font-size:13px; font-weight:800; color:#5C768D;'>KIOST 편의 서비스</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    # 버튼 하나로 아이콘과 텍스트가 모두 렌더링되며, 클릭 시 바로 모달 오픈
    if st.button("⏰\n**근무 계산기**", key="btn_work", use_container_width=True):
        show_worktime_modal()

with col2:
    if st.button("🍽️\n**근처 맛집**", key="btn_res", use_container_width=True):
        show_restaurants_modal()

with col3:
    if st.button("🍱\n**구내식당**", key="btn_diet", use_container_width=True):
        show_cafeteria_modal()

# -------------------------------------------------------------------
# 7. 사이드바 (관리자 메뉴)
# -------------------------------------------------------------------
st.sidebar.title("🔐 카페 관리자 메뉴")
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
            st.sidebar.error("비밀번호가 올바르지 않습니다.")
else:
    st.sidebar.success("관리자 인증 완료")
    if st.sidebar.button("🟢 1단계: 이용가능 (200잔)", use_container_width=True):
        if sheet_stock: sheet_stock.update_cell(1, 2, 200)
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("🟡 2단계: 소진임박 (15잔)", use_container_width=True):
        if sheet_stock: sheet_stock.update_cell(1, 2, 15)
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("🔴 3단계: 카페마감 (0잔)", use_container_width=True):
        if sheet_stock: sheet_stock.update_cell(1, 2, 0)
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.is_admin_logged_in = False
        st.rerun()
