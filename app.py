from datetime import datetime, timezone, timedelta
import json
import gspread
import requests
import streamlit as st

# -------------------------------------------------------------------
# 1. 페이지 기본 설정
# -------------------------------------------------------------------
st.set_page_config(
    page_title="소담터 - 사내 카페",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------------
# 2. 커스텀 CSS (PC 모바일 뷰 고정 + 모던 다크 테마)
# -------------------------------------------------------------------
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

    :root {
        --bg-base: #120d0a;
        --bg-elevated: #1c140f;
        --bg-card: #1f1712;
        --accent: #c17a3d;
        --accent-light: #e0a458;
        --text-primary: #f5ece0;
        --text-secondary: #b3a08c;
        --border-soft: rgba(245, 236, 224, 0.08);
    }

    .stApp {
        background: linear-gradient(160deg, var(--bg-base) 0%, #1a120d 100%);
        color: var(--text-primary);
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main .block-container {
        max-width: 430px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto;
    }
    footer {
        visibility: hidden !important;
        height: 0px !important;
    }
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .header-title {
        font-family: 'Gaegu', cursive;
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }
    .header-sub {
        font-size: 13px;
        color: var(--text-secondary);
    }
    .stButton > button {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-radius: 14px !important;
        border: 1px solid var(--border-soft) !important;
        padding: 8px 16px !important;
        width: 100%;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: var(--accent) !important;
        border-color: var(--accent-light) !important;
        color: #1a120d !important;
    }
    .stTextInput > div > div > input {
        background-color: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-soft) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--bg-elevated);
        padding: 6px;
        border-radius: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 600;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: #1a120d !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--accent-light) !important;
    }
    .stAlert {
        border-radius: 16px !important;
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-soft) !important;
    }

    /* 커피잔 + 증기 시그니처 일러스트 */
    .cup-card {
        border-radius: 28px;
        padding: 26px 20px 20px;
        margin: 20px auto;
        max-width: 300px;
        text-align: center;
        transition: all 0.4s ease;
    }
    .cup-illustration {
        width: 130px;
        height: auto;
        display: block;
        margin: 0 auto;
    }
    .steam {
        transform-origin: center bottom;
        animation: steamRise 3s ease-in-out infinite;
    }
    .steam:nth-child(2) { animation-delay: 0.4s; }
    .steam:nth-child(3) { animation-delay: 0.8s; }
    @keyframes steamRise {
        0%   { transform: translateY(0) scaleY(1); }
        50%  { transform: translateY(-6px) scaleY(1.08); }
        100% { transform: translateY(0) scaleY(1); }
    }
    @media (prefers-reduced-motion: reduce) {
        .steam { animation: none; }
    }
    .cup-title {
        font-family: 'Gaegu', cursive;
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.5px;
        margin-top: 4px;
    }
    .cup-hours {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 10px;
    }
    .cup-badge {
        display: inline-block;
        font-size: 13px;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 12px;
        border: 1px solid;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------------
# 안전한 형변환 헬퍼 함수
# -------------------------------------------------------------------
def safe_int(val, default=0):
    try:
        if val is None:
            return default
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default

# -------------------------------------------------------------------
# 3. 텔레그램 알람 전송 함수
# -------------------------------------------------------------------
def send_telegram_alert(message):
    try:
        if "telegram" in st.secrets:
            bot_token = st.secrets["telegram"].get("bot_token", "여기에_봇토큰_입력")
            chat_id = st.secrets["telegram"].get("chat_id", "여기에_채널아이디_입력")
        else:
            bot_token = "여기에_봇토큰_입력"
            chat_id = "여기에_채널아이디_입력"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            st.toast("📢 텔레그램 채널로 알람이 전송되었습니다!")
        else:
            st.warning(f"텔레그램 전송 실패: {response.text}")
    except Exception as e:
        st.error(f"텔레그램 연동 오류: {e}")


# -------------------------------------------------------------------
# 4. 데이터 및 구글 시트 연동 (Caching)
# -------------------------------------------------------------------
# 표준 라이브러리를 사용하여 KST 시간 구하기 (pytz 종속성 제거로 오류 방지)
KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)
current_hour = now_kst.hour
current_weekday = now_kst.weekday()

is_weekday = current_weekday < 5
is_opening_hours = 10 <= current_hour < 16

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            secret_data = st.secrets["gcp_service_account"]
            creds_dict = (
                json.loads(secret_data)
                if isinstance(secret_data, str)
                else dict(secret_data)
            )
            return gspread.service_account_from_dict(creds_dict, scopes=SCOPES)
        else:
            return gspread.service_account(
                filename="service_account.json", scopes=SCOPES
            )
    except Exception as e:
        st.error(f"🔑 구글 API 인증 오류: {e}")
        return None


gc = get_gspread_client()


@st.cache_resource
def get_sheets(_gc):
    if not _gc:
        return None, None, None, None
    try:
        doc = _gc.open("kiost_sodam")
        sheet_stock = doc.worksheet("재고")
        sheet_vote = doc.worksheet("투표")
        sheet_guest = doc.worksheet("방명록")
        return doc, sheet_stock, sheet_vote, sheet_guest
    except Exception as e:
        st.error(f"📄 구글 시트 로드 실패: {e}")
        return None, None, None, None


doc, sheet_stock, sheet_vote, sheet_guest = get_sheets(gc)


# 캐싱 함수 내부에서 st.session_state를 직접 수정하는 오동작 방지 및 외부 예외 안전 처리 적용
@st.cache_data(ttl=60)
def fetch_stock_data():
    if not sheet_stock:
        raise ConnectionError("구글 시트에 연결되지 않았습니다.")
    try:
        return sheet_stock.acell("B1").value
    except Exception as e:
        raise RuntimeError(f"재고 셀(B1) 파싱 실패: {e}")


@st.cache_data(ttl=60)
def fetch_vote_data():
    if not sheet_vote:
        raise ConnectionError("구글 시트에 연결되지 않았습니다.")
    try:
        return sheet_vote.get_all_values()
    except Exception as e:
        raise RuntimeError(f"투표 데이터 로드 실패: {e}")


@st.cache_data(ttl=60)
def fetch_guest_data():
    if not sheet_guest:
        raise ConnectionError("구글 시트에 연결되지 않았습니다.")
    try:
        return sheet_guest.get_all_values()
    except Exception as e:
        raise RuntimeError(f"방명록 데이터 로드 실패: {e}")


# 메인 흐름에서 캐싱 함수의 결과를 안전하게 처리
stock_fetch_error = None
try:
    raw_stock = fetch_stock_data()
    current_stock = safe_int(raw_stock, 0)
except Exception as e:
    current_stock = 0
    stock_fetch_error = str(e)

# -------------------------------------------------------------------
# 5. 상태별 테마 계산
# -------------------------------------------------------------------

# 신호등 색상(초록/노랑/빨강)은 상태를 직관적으로 전달하는 기능색이라 그대로 유지하고,
# 카드 배경은 보라색 계열 대신 커피 테마에 맞는 다크 브라운 톤으로 옮긴다.
if current_stock > 30:
    theme_card_bg = "radial-gradient(circle at 50% 15%, rgba(34, 197, 94, 0.10) 0%, var(--bg-card) 70%)"
    theme_shadow = "0 10px 34px rgba(34, 197, 94, 0.12)"
    theme_border = "rgba(34, 197, 94, 0.35)"
    status_label = "🟢 이용가능"
    badge_bg = "rgba(34, 197, 94, 0.15)"
    badge_color = "#22c55e"
    cup_fill_y = 55       # 커피가 잔 위쪽까지 가득
    steam_visible = True
    steam_opacity = 0.85
elif current_stock > 0:
    theme_card_bg = "radial-gradient(circle at 50% 15%, rgba(234, 179, 8, 0.10) 0%, var(--bg-card) 70%)"
    theme_shadow = "0 10px 34px rgba(234, 179, 8, 0.12)"
    theme_border = "rgba(234, 179, 8, 0.35)"
    status_label = "🟡 소진임박"
    badge_bg = "rgba(234, 179, 8, 0.15)"
    badge_color = "#eab308"
    cup_fill_y = 100      # 절반 정도 남음
    steam_visible = True
    steam_opacity = 0.4
else:
    theme_card_bg = "radial-gradient(circle at 50% 15%, rgba(239, 68, 68, 0.10) 0%, var(--bg-card) 70%)"
    theme_shadow = "0 10px 34px rgba(239, 68, 68, 0.12)"
    theme_border = "rgba(239, 68, 68, 0.35)"
    status_label = "🔴 카페마감"
    badge_bg = "rgba(239, 68, 68, 0.15)"
    badge_color = "#ef4444"
    cup_fill_y = 140      # 커피 없음(빈 잔)
    steam_visible = False
    steam_opacity = 0

# 커피 채움 도형과 증기(steam) SVG 조각을 미리 조립
# 주의: 여기서 만드는 조각들은 반드시 개행(\n)이 없는 한 줄 문자열이어야 한다.
# st.markdown()에 삽입될 때 공백만 있는 줄이 생기면, 마크다운 파서가 그 지점부터
# 이후 내용을 HTML이 아닌 "들여쓰기 코드블록"으로 오인해서 태그가 그대로 노출된다.
_coffee_height = 140 - cup_fill_y
coffee_fill_svg = (
    f'<rect x="20" y="{cup_fill_y}" width="120" height="{_coffee_height}" '
    f'fill="var(--accent)" clip-path="url(#mugClip)" />'
    if _coffee_height > 0
    else ""
)

if steam_visible:
    _steam_path = (
        'stroke="var(--accent-light)" stroke-width="4" stroke-linecap="round" fill="none" />'
    )
    steam_svg = (
        f'<path class="steam" style="opacity:{steam_opacity};" d="M55,35 C48,25 62,15 55,5" {_steam_path}'
        f'<path class="steam" style="opacity:{steam_opacity};" d="M80,35 C73,25 87,15 80,3" {_steam_path}'
        f'<path class="steam" style="opacity:{steam_opacity};" d="M105,35 C98,25 112,15 105,5" {_steam_path}'
    )
else:
    steam_svg = ""

# 잔+손잡이 외곽선과 위 조각들을 하나의 한 줄짜리 SVG 마크업으로 합친다.
mug_svg = (
    '<svg class="cup-illustration" viewBox="0 0 160 170" xmlns="http://www.w3.org/2000/svg">'
    '<defs><clipPath id="mugClip">'
    '<path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" />'
    '</clipPath></defs>'
    + steam_svg
    + coffee_fill_svg
    + '<path d="M25,40 L135,40 L127,132 Q127,140 119,140 L41,140 Q33,140 33,132 Z" '
    'fill="none" stroke="#e8dcc8" stroke-width="4" stroke-linejoin="round" />'
    '<path d="M135,55 C165,55 165,105 135,105" '
    'fill="none" stroke="#e8dcc8" stroke-width="6" stroke-linecap="round" />'
    '</svg>'
)

# -------------------------------------------------------------------
# 6. 상단 UI 및 커피잔 시그니처 카드 (텔레그램 링크 버튼 반영)
# -------------------------------------------------------------------

# 👈 본인의 텔레그램 채널 공개 링크 주소로 변경하세요
telegram_channel_url = "https://t.me/+n5J-xg8BI4tkYmE1"
st.markdown(
    f"""
<div class="top-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
    <div>
        <div class="header-title" style="margin: 0;">Good day ☕</div>
        <div class="header-sub" style="margin-top: 2px;">Sodam-teo Cafe</div>
    </div>
    <a href="{telegram_channel_url}" target="_blank" style="text-decoration: none; display: flex; flex-direction: column; align-items: center;">
        <div style="
            width: 42px; 
            height: 42px; 
            border-radius: 50%; 
            background: rgba(42, 171, 238, 0.15); 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            border: 1px solid rgba(42, 171, 238, 0.4); 
            font-size: 20px;
            box-shadow: 0 4px 12px rgba(42, 171, 238, 0.2);
        ">
            ✈️
        </div>
        <div style="font-size: 11px; color: #2AAAEE; margin-top: 4px; font-weight: 600; letter-spacing: -0.3px;">
            텔레그램 알람받기
        </div>
    </a>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="cup-card" style="background: {theme_card_bg}; box-shadow: {theme_shadow}; '
    f'border: 1px solid {theme_border};">'
    f'{mug_svg}'
    f'<div class="cup-title">소담터</div>'
    f'<div class="cup-hours">운영시간 10:00 - 16:00</div>'
    f'<div class="cup-badge" style="color: {badge_color}; background: {badge_bg}; '
    f'border-color: {badge_color}40;">{status_label}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 7. 탭(Tab) 메뉴
# -------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["☕ 카페 현황", "🏆 인기 투표", "💬 끄적끄적 방명록"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    if stock_fetch_error:
        st.warning(
            f"⚠️ 재고 데이터를 불러오지 못해 임시로 마감 상태로 표시 중입니다. "
            f"(오류: {stock_fetch_error})"
        )
    if not is_weekday or not is_opening_hours:
        st.info("💡 현재는 **운영 시간(평일 10:00 ~ 16:00) 외** 시간입니다.")

    if current_stock > 30:
        st.success(
            "### 🟢 여유 있어요!\n맛있는 커피가 넉넉하게 준비되어 있습니다. 천천히 오세요~ ☕"
        )
    elif current_stock > 0:
        st.warning(
            "### 🟡 마감 임박!\n오늘 준비된 커피가 얼마 남지 않았어요. 조금만 서둘러 주세요! 🏃‍♂️"
        )
    else:
        st.error(
            "### 🔴 금일 마감\n오늘 준비된 커피가 모두 소진되었습니다. 내일 더 맛있는 커피로 만나요! 🌙"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    try:
        weather_req = requests.get(
            "https://wttr.in/Busan?format=%c+%t&m", timeout=3
        )
        if weather_req.status_code == 200:
            st.info(
                f"🌤️ **오늘의 부산 날씨:** {weather_req.text}  |  상쾌한 음료와 함께 기분 좋은 하루 보내세요!"
            )
    except:
        pass

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏆 가장 사랑받는 메뉴 TOP 3")
    
    vote_fetch_error = None
    vote_raw_data = []
    try:
        vote_raw_data = fetch_vote_data()
    except Exception as e:
        vote_fetch_error = str(e)
        
    if vote_fetch_error:
        st.warning(
            f"⚠️ 투표 데이터를 불러오지 못했습니다. (오류: {vote_fetch_error})"
        )
        
    if len(vote_raw_data) > 1:
        try:
            # 정렬 전에 시트의 실제 행 번호(2행부터 시작)를 각 항목에 붙여둔다.
            # 데이터 구조 불일치 대비 안전한 unpacking과 데이터 정제 과정 추가
            vote_data = []
            for sheet_row_num, row in enumerate(vote_raw_data[1:], start=2):
                if len(row) >= 2:
                    vote_data.append((row[0], safe_int(row[1], 0), sheet_row_num))
                elif len(row) == 1:
                    vote_data.append((row[0], 0, sheet_row_num))
                    
            vote_data.sort(key=lambda x: x[1], reverse=True)
            top3 = vote_data[:3]
            col1, col2, col3 = st.columns(3)
            if len(top3) >= 1:
                col1.metric(
                    label="🥇 1위", value=top3[0][0], delta=f"{top3[0][1]}표"
                )
            if len(top3) >= 2:
                col2.metric(
                    label="🥈 2위", value=top3[1][0], delta=f"{top3[1][1]}표"
                )
            if len(top3) >= 3:
                col3.metric(
                    label="🥉 3위", value=top3[2][0], delta=f"{top3[2][1]}표"
                )

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("👉 나도 최애 메뉴에 투표하기"):
                st.caption("메뉴를 누르면 즉시 1표가 올라갑니다!")
                vote_cols = st.columns(4)
                for i, (menu_name, current_votes, sheet_row_num) in enumerate(vote_data):
                    if vote_cols[i % 4].button(menu_name, key=f"vote_{i}"):
                        if sheet_vote:
                            sheet_vote.update_cell(sheet_row_num, 2, current_votes + 1)
                            st.cache_data.clear()
                            st.toast(f"{menu_name}에 투표하셨습니다! 🎉")
                            st.rerun()
        except Exception as e:
            st.warning(f"투표 데이터 처리 오류: {e}")

with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💬 끄적끄적 한줄 게시판")
    
    guest_fetch_error = None
    guest_raw_data = []
    try:
        guest_raw_data = fetch_guest_data()
    except Exception as e:
        guest_fetch_error = str(e)
        
    if guest_fetch_error:
        st.warning(
            f"⚠️ 방명록 데이터를 불러오지 못했습니다. (오류: {guest_fetch_error})"
        )
        
    if sheet_guest:
        try:
            with st.form("guestbook_form", clear_on_submit=True):
                new_comment = st.text_input(
                    "메뉴 건의나 응원의 한마디를 남겨주세요!",
                    placeholder="예: 시원한 콜드브루도 들어오면 좋겠어요!",
                )
                submitted = st.form_submit_button("등록하기")
                if submitted and new_comment:
                    kst = datetime.now(KST).strftime(
                        "%m-%d %H:%M"
                    )
                    sheet_guest.append_row([kst, new_comment])
                    st.cache_data.clear()
                    st.success("소중한 의견이 등록되었습니다!")
                    st.rerun()

            if len(guest_raw_data) > 1:
                data_rows = guest_raw_data[1:]
                st.markdown("##### 💌 최근 남겨진 이야기")
                for row in reversed(data_rows[-5:]):
                    if len(row) >= 2:
                        st.info(f"**{row[0]}** | {row[1]}")
                    elif len(row) == 1:
                        st.info(f"{row[0]}")
        except Exception as e:
            st.warning(f"방명록 처리 오류: {e}")

# -------------------------------------------------------------------
# 8. 관리자 사이드바 (상태 변경 시 텔레그램 자동 알람 발송)
# -------------------------------------------------------------------
st.sidebar.title("🔐 관리자 메뉴")

if "is_admin_logged_in" not in st.session_state:
    st.session_state.is_admin_logged_in = False

if not st.session_state.is_admin_logged_in:
    admin_pw = st.sidebar.text_input(
        "비밀번호를 입력하세요", type="password", key="admin_pw_input"
    )
    if st.sidebar.button("🔓 로그인", use_container_width=True, key="login_btn"):
        admin_secrets = st.secrets.get("admin")
        correct_pw = admin_secrets.get("password") if admin_secrets else None
        if not correct_pw:
            st.sidebar.error("⚠️ secrets.toml에 관리자 비밀번호가 설정되지 않았습니다.")
        elif admin_pw == correct_pw:
            st.session_state.is_admin_logged_in = True
            st.sidebar.success("인증 완료!")
            st.rerun()
        else:
            st.sidebar.error("비밀번호가 올바르지 않습니다.")

else:
    st.sidebar.success("인증 완료 상태입니다.")

    if current_stock > 30:
        current_status_text = "🟢 이용가능"
    elif current_stock > 0:
        current_status_text = "🟡 소진임박"
    else:
        current_status_text = "🔴 카페마감"

    st.sidebar.info(f"현재 반영된 상태: **{current_status_text}**")
    st.sidebar.divider()

    st.sidebar.markdown("### 🛠️ 상태 변경 및 알람 발송")

    # 🟢 1단계 변경
    if st.sidebar.button("🟢 1단계: 이용가능", use_container_width=True):
        if sheet_stock:
            sheet_stock.update_cell(1, 2, 200)
            st.cache_data.clear()
            # 💡 텔레그램 알람 전송
            # send_telegram_alert(
            #     "☕ **[소담터 카페]**\n맛있는 커피가 넉넉하게 준비되었습니다. 커피 한 잔 하러 오세요! 🟢"
            # )
            st.rerun()

    # 🟡 2단계 변경
    if st.sidebar.button("🟡 2단계: 소진임박", use_container_width=True):
        if sheet_stock:
            sheet_stock.update_cell(1, 2, 15)
            st.cache_data.clear()
            # 💡 텔레그램 알람 전송
            send_telegram_alert(
                 "🏃‍♂️ **[소담터 카페]**\n오늘 준비된 커피가 얼마 남지 않았습니다! 조금만 서둘러 주세요! 🟡"
            )
            st.rerun()

    # 🔴 3단계 변경
    if st.sidebar.button("🔴 3단계: 카페마감", use_container_width=True):
        if sheet_stock:
            sheet_stock.update_cell(1, 2, 0)
            st.cache_data.clear()
            # 💡 텔레그램 알람 전송
            send_telegram_alert(
                "🌙 **[소담터 카페]**\n오늘 준비된 재고가 모두 소진되어 영업을 마감합니다. 내일 만나요! 🔴"
            )
            st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state.is_admin_logged_in = False
        st.rerun()
