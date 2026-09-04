from datetime import datetime, timezone, timedelta, time
import json
import gspread
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# 1. 페이지 기본 설정 및 시간대 정의
# -------------------------------------------------------------------
st.set_page_config(
    page_title="소담터 - KIOST 사내 카페",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)

# -------------------------------------------------------------------
# 2. KIOST 고대비 블루톤 CSS (다크모드 글씨 증발 완벽 방지)
# -------------------------------------------------------------------
kiost_blue_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

    :root {
        --kiost-primary: #003876;
        --kiost-secondary: #0072CE;
        --text-strong: #0A1C30;       /* 어떤 배경에서도 잘 보이는 최고 대비 텍스트 */
        --text-sub: #334E68;          /* 보조 설명용 진한 텍스트 */
        --card-bg: #FFFFFF;
        --border-color: rgba(0, 56, 118, 0.18);
    }

    /* 전체 화면 배경 */
    .stApp {
        background: linear-gradient(180deg, #E6F0FA 0%, #F4F8FC 100%) !important;
        color: var(--text-strong) !important;
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

    /* 모든 텍스트, 라벨, 캡션 강제 고대비 색상 적용 */
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: var(--text-strong);
    }

    /* 커피 시그니처 카드 */
    .cup-card {
        border-radius: 24px;
        padding: 22px 18px 16px;
        margin: 12px auto;
        max-width: 300px;
        text-align: center;
        background: var(--card-bg);
        border: 1.5px solid var(--border-color);
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
        color: var(--kiost-primary) !important;
        margin-top: 4px;
    }
    .cup-hours {
        font-size: 12.5px;
        font-weight: 600;
        color: var(--text-sub) !important;
        margin-bottom: 8px;
    }
    .cup-badge {
        display: inline-block;
        font-size: 12.5px;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 12px;
        border: 1.5px solid;
    }

    /* 📱 일체형 퀵메뉴 버튼 */
    div[data-testid="column"] .stButton > button {
        background-color: #FFFFFF !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 18px !important;
        padding: 10px 4px !important;
        height: auto !important;
        min-height: 86px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 12px rgba(0, 56, 118, 0.06) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="column"] .stButton > button p {
        margin: 0 !important;
        line-height: 1.3 !important;
        color: var(--kiost-primary) !important;
        font-weight: 800 !important;
        font-size: 13px !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        border-color: var(--kiost-secondary) !important;
        background-color: #F0F6FC !important;
        transform: translateY(-2px);
    }

    /* 입력창 및 모달 내부 고대비 강제 */
    .stTextInput input, .stNumberInput input, .stTimeInput input {
        background-color: #FFFFFF !important;
        color: #0A1C30 !important;
        border: 1.5px solid #CBD5E1 !important;
    }
    .stDialog {
        background-color: #FFFFFF !important;
    }
    .stDialog button {
        background-color: var(--kiost-primary) !important;
        color: #FFFFFF !important;
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
# 3. 구글 시트 연동 ('재고' 및 '식단' 탭 동기화)
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

        try:
            sheet_diet = doc.worksheet("식단")
        except gspread.WorksheetNotFound:
            sheet_diet = doc.add_worksheet(title="식단", rows=20, cols=7)
            default_headers = ["No.", "날짜", "요일", "메뉴구분", "메뉴", "후식", "등록일자"]
            sheet_diet.append_row(default_headers)

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

# 카페 재고 현황 계산
if current_stock > 30:
    status_label = "🟢 이용가능"
    badge_bg, badge_color = "#DCFCE7", "#15803D"
    cup_fill_y = 55
elif current_stock > 0:
    status_label = "🟡 소진임박"
    badge_bg, badge_color = "#FEF9C3", "#A16207"
    cup_fill_y = 100
else:
    status_label = "🔴 카페마감"
    badge_bg, badge_color = "#FEE2E2", "#B91C1C"
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
    st.markdown("<p style='font-size:13px; color:#334E68; font-weight:600;'>목표 40시간 달성 후 금요일 정시 퇴근 시각을 계산합니다.</p>", unsafe_allow_html=True)
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
            st.info(f"오늘 채워야 할 순 근무시간: **{remain_h}시간 {remain_m}분**")
            st.markdown(
                f"<div style='text-align:center; padding:15px; background:#EFF6FF; border-radius:14px; border:2px solid #003876; margin-top:10px;'>"
                f"<span style='font-size:13px; color:#1E3A8A; font-weight:700;'>금요일 퇴근 가능 시간</span><br>"
                f"<b style='font-size:28px; color:#003876;'>{leave_dt.strftime('%H:%M')}</b>"
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
            <div style="background:#F1F5F9; padding:12px 14px; border-radius:14px; border:1px solid #CBD5E1; margin-top:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:15px; color:#003876;">{item['name']}</b>
                    <span style="font-size:12px; color:#0284C7; font-weight:800;">{item['rating']}</span>
                </div>
                <div style="font-size:12.5px; color:#334155; margin-top:2px; font-weight:500;">
                    {item['dist']} · 대표메뉴: {item['menu']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# 3번: 구내식당 식판 모달 (실제 시트 컬럼 구조 완벽 대응)
@st.dialog("🍱 오늘 구내식당 점심 메뉴")
def show_cafeteria_modal():
    weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today_weekday_idx = now_kst.weekday()
    today_weekday_str = weekdays_kr[today_weekday_idx]
    
    today_date_slash = now_kst.strftime("%Y/%m/%d")
    today_display_str = now_kst.strftime("%m월 %d일")

    st.markdown(f"<p style='font-size:13px; color:#334E68; font-weight:700;'>📅 {today_display_str} ({today_weekday_str}요일) 중식 11:30 ~ 13:00</p>", unsafe_allow_html=True)

    diet_list = fetch_diet_data()

    if today_weekday_idx >= 5:
        st.info("🌿 주말에는 구내식당을 운영하지 않습니다. 편안한 주말 보내세요!")
        return

    # 오늘 날짜 또는 오늘 요일 매칭
    today_menus = []
    if diet_list:
        for row in diet_list:
            row_date = str(row.get("날짜", "")).strip().replace("-", "/")
            row_day = str(row.get("요일", "")).strip()
            
            if row_date == today_date_slash or (not row_date and row_day == today_weekday_str):
                today_menus.append(row)
        
        if not today_menus:
            for row in diet_list:
                if str(row.get("요일", "")).strip() == today_weekday_str:
                    today_menus.append(row)

    if not today_menus:
        st.warning("⚠️ 오늘 등록된 식단 정보가 없습니다.")
    else:
        corner_names = [f"📍 {m.get('메뉴구분', '중식')}" for m in today_menus]
        
        if len(today_menus) > 1:
            tabs = st.tabs(corner_names)
        else:
            tabs = [st.container()]

        for idx, current_tab in enumerate(tabs):
            with current_tab:
                menu_info = today_menus[idx]
                corner_title = menu_info.get("메뉴구분", "기본식")
                raw_menu_str = str(menu_info.get("메뉴", ""))
                dessert = str(menu_info.get("후식", "")).strip()

                dishes = [d.strip() for d in raw_menu_str.split(",") if d.strip()]
                main_dish = dishes[0] if dishes else "메뉴 준비중"
                sub_dishes = dishes[1:] if len(dishes) > 1 else []

                grid_html = f"""
                <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:18px; padding:16px; margin-top:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="font-weight:800; font-size:15px; color:#003876;">KIOST [{corner_title}]</span>
                        <span style="font-size:11.5px; background:#E0F2FE; color:#0369A1; padding:3px 8px; border-radius:8px; font-weight:800;">식판 구성</span>
                    </div>
                    <div style="background:#EFF6FF; border:1.5px solid #003876; border-radius:12px; padding:10px; text-align:center; font-weight:800; color:#003876; font-size:14.5px; margin-bottom:8px;">
                        🍲 {main_dish}
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px;">
                """
                
                for dish in sub_dishes:
                    grid_html += f"""<div style="background:#F8FAFC; border-radius:10px; padding:8px; text-align:center; font-size:12.5px; color:#0F172A; border:1px solid #E2E8F0; font-weight:600;">🥢 {dish}</div>"""
                
                if dessert and dessert != "-" and dessert != "nan":
                    grid_html += f"""<div style="grid-column: span 2; background:#FFF7ED; border-radius:10px; padding:8px; text-align:center; font-size:12.5px; color:#C2410C; border:1.5px solid #FDBA74; font-weight:800;">🍦 후식: {dessert}</div>"""

                grid_html += "</div></div>"
                st.markdown(grid_html, unsafe_allow_html=True)

    st.write("")
    with st.expander("📅 이번 주 전체 식단표 펼쳐보기"):
        if diet_list:
            df = pd.DataFrame(diet_list)
            cols_to_show = [c for c in ["날짜", "요일", "메뉴구분", "메뉴", "후식"] if c in df.columns]
            if cols_to_show:
                st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)
            else:
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
        <div style="width:36px; height:36px; border-radius:50%; background:#E0F2FE; display:flex; align-items:center; justify-content:center; border:1.5px solid #0072CE; font-size:17px;">
            ✈️
        </div>
        <div style="font-size:10px; color:#0072CE; margin-top:2px; font-weight:800;">알람받기</div>
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
    f'<div class="cup-badge" style="color:{badge_color}; background:{badge_bg}; border-color:{badge_color};">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# 6. 하단 편의 서비스 (일체형 원클릭 컴팩트 버튼)
# -------------------------------------------------------------------
st.markdown("<p style='margin-top:20px; margin-bottom:8px; font-size:13px; font-weight:800; color:#334E68;'>KIOST 편의 서비스</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⏰\n근무 계산기", key="btn_work", use_container_width=True):
        show_worktime_modal()

with col2:
    if st.button("🍽️\n근처 맛집", key="btn_res", use_container_width=True):
        show_restaurants_modal()

with col3:
    if st.button("🍱\n구내식당", key="btn_diet", use_container_width=True):
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
