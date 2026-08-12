from datetime import datetime
import json
import gspread
import pytz
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
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #12131c 100%);
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
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
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .header-sub {
        font-size: 13px;
        color: #8E8EA0;
    }
    .stButton > button {
        background-color: #212232 !important;
        color: #e2e8f0 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 8px 16px !important;
        width: 100%;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #3b2d54 !important;
        border-color: #c084fc !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input {
        background-color: #181926 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #13141f;
        padding: 6px;
        border-radius: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 12px;
        color: #8E8EA0;
        font-weight: 600;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b2d54 !important;
        color: #ffffff !important;
    }
    [data-testid="stMetricValue"] {
        color: #c084fc !important;
    }
    .stAlert {
        border-radius: 16px !important;
        background-color: #181926 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------------
# 3. 텔레그램 알림 전송 함수
# -------------------------------------------------------------------


def send_telegram_alert(message):
    try:
        if "telegram" in st.secrets:
            bot_token = st.secrets["telegram"]["bot_token"]
            chat_id = st.secrets["telegram"]["chat_id"]
        else:
            bot_token = "여기에_봇토큰_입력"
            chat_id = "여기에_채널아이디_입력"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            st.toast("📢 텔레그램 채널로 알림이 전송되었습니다!")
        else:
            st.warning(f"텔레그램 전송 실패: {response.text}")
    except Exception as e:
        st.error(f"텔레그램 연동 오류: {e}")


# -------------------------------------------------------------------
# 4. 데이터 및 구글 시트 연동 (Caching)
# -------------------------------------------------------------------

now_kst = datetime.now(pytz.timezone("Asia/Seoul"))
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


@st.cache_data(ttl=10)
def fetch_stock_data():
    if sheet_stock:
        try:
            return int(sheet_stock.acell("B1").value)
        except:
            return 0
    return 0


@st.cache_data(ttl=10)
def fetch_vote_data():
    if sheet_vote:
        try:
            return sheet_vote.get_all_values()
        except:
            return []
    return []


@st.cache_data(ttl=10)
def fetch_guest_data():
    if sheet_guest:
        try:
            return sheet_guest.get_all_values()
        except:
            return []
    return []


current_stock = fetch_stock_data()

# -------------------------------------------------------------------
# 5. 상태별 테마 계산
# -------------------------------------------------------------------

if current_stock > 30:
    theme_bg = "radial-gradient(circle at 50% 30%, #1c3d2a 0%, #13141f 75%)"
    theme_shadow = "0 10px 40px rgba(34, 197, 94, 0.3)"
    theme_border = "rgba(34, 197, 94, 0.5)"
    theme_subtext_color = "#4ade80"
    status_label = "🟢 이용가능"
    badge_bg = "rgba(34, 197, 94, 0.15)"
    badge_color = "#22c55e"
elif current_stock > 0:
    theme_bg = "radial-gradient(circle at 50% 30%, #3d331c 0%, #13141f 75%)"
    theme_shadow = "0 10px 40px rgba(234, 179, 8, 0.3)"
    theme_border = "rgba(234, 179, 8, 0.5)"
    theme_subtext_color = "#facc15"
    status_label = "🟡 소진임박"
    badge_bg = "rgba(234, 179, 8, 0.15)"
    badge_color = "#eab308"
else:
    theme_bg = "radial-gradient(circle at 50% 30%, #3d1c1c 0%, #13141f 75%)"
    theme_shadow = "0 10px 40px rgba(239, 68, 68, 0.3)"
    theme_border = "rgba(239, 68, 68, 0.5)"
    theme_subtext_color = "#f87171"
    status_label = "🔴 카페마감"
    badge_bg = "rgba(239, 68, 68, 0.15)"
    badge_color = "#ef4444"

# -------------------------------------------------------------------
# 6. 상단 UI 및 동적 원형 카드 (텔레그램 링크 버튼 반영)
# -------------------------------------------------------------------

# 👈 본인의 텔레그램 채널 공개 링크 주소로 변경하세요
telegram_channel_url = "https://t.me/+n5J-xg8BI4tkYmE1"
st.markdown(
    f"""
<div class="top-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
    <div>
        <div class="header-title" style="font-size: 26px; font-weight: 700; color: #ffffff; margin: 0;">Good day ☕</div>
        <div class="header-sub" style="font-size: 13px; color: #8E8EA0; margin-top: 2px;">Sodam-teo Cafe</div>
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
            텔레그램 알림받기
        </div>
    </a>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div style="
    background: {theme_bg};
    border-radius: 50%;
    width: 260px;
    height: 260px;
    margin: 20px auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: {theme_shadow}, inset 0 0 15px rgba(255, 255, 255, 0.05);
    border: 1px solid {theme_border};
    transition: all 0.4s ease;
">
    <div style="font-size: 13px; color: {theme_subtext_color}; margin-bottom: 4px; font-weight: 600;">☕ Cafe Status</div>
    <div style="font-size: 32px; font-weight: 800; color: #ffffff; letter-spacing: -1px; margin-bottom: 4px;">
        소담터
    </div>
    <div style="font-size: 12px; color: #8E8EA0; margin-bottom: 8px;">운영시간 10:00 - 16:00</div>
    <div style="
        font-size: 13px;
        font-weight: 700;
        color: {badge_color};
        background: {badge_bg};
        padding: 4px 14px;
        border-radius: 12px;
        border: 1px solid {badge_color}40;
    ">
        {status_label}
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 7. 탭(Tab) 메뉴
# -------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["☕ 카페 현황", "🏆 인기 투표", "💬 끄적끄적 방명록"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
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
    vote_raw_data = fetch_vote_data()
    if len(vote_raw_data) > 1:
        try:
            vote_data = vote_raw_data[1:]
            vote_data.sort(key=lambda x: int(x[1]), reverse=True)
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
                for i, row in enumerate(vote_data):
                    menu_name = row[0]
                    current_votes = int(row[1])
                    if vote_cols[i % 4].button(menu_name, key=f"vote_{i}"):
                        if sheet_vote:
                            sheet_vote.update_cell(i + 2, 2, current_votes + 1)
                            st.cache_data.clear()
                            st.toast(f"{menu_name}에 투표하셨습니다! 🎉")
                            st.rerun()
        except Exception as e:
            st.warning(f"투표 데이터 처리 오류: {e}")

with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💬 끄적끄적 한줄 게시판")
    if sheet_guest:
        try:
            with st.form("guestbook_form", clear_on_submit=True):
                new_comment = st.text_input(
                    "메뉴 건의나 응원의 한마디를 남겨주세요!",
                    placeholder="예: 시원한 콜드브루도 들어오면 좋겠어요!",
                )
                submitted = st.form_submit_button("등록하기")
                if submitted and new_comment:
                    kst = datetime.now(pytz.timezone("Asia/Seoul")).strftime(
                        "%m-%d %H:%M"
                    )
                    sheet_guest.append_row([kst, new_comment])
                    st.cache_data.clear()
                    st.success("소중한 의견이 등록되었습니다!")
                    st.rerun()

            guest_data = fetch_guest_data()
            if len(guest_data) > 1:
                data_rows = guest_data[1:]
                st.markdown("##### 💌 최근 남겨진 이야기")
                for row in reversed(data_rows[-5:]):
                    st.info(f"**{row[0]}** | {row[1]}")
        except Exception as e:
            st.warning(f"방명록 처리 오류: {e}")

# -------------------------------------------------------------------
# 8. 관리자 사이드바 (상태 변경 시 텔레그램 자동 알림 발송)
# -------------------------------------------------------------------
st.sidebar.title("🔐 관리자 메뉴")

if "is_admin_logged_in" not in st.session_state:
    st.session_state.is_admin_logged_in = False

if not st.session_state.is_admin_logged_in:
    admin_pw = st.sidebar.text_input(
        "비밀번호를 입력하세요", type="password", key="admin_pw_input"
    )
    if st.sidebar.button("🔓 로그인", use_container_width=True, key="login_btn"):
        if admin_pw == "0000":
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

    st.sidebar.markdown("### 🛠️ 상태 변경 및 알림 발송")

    # 🟢 1단계 변경
    if st.sidebar.button("🟢 1단계: 이용가능 (200)", use_container_width=True):
        if sheet_stock:
            sheet_stock.update_cell(1, 2, 200)
            st.cache_data.clear()
            # 💡 텔레그램 알림 전송
            send_telegram_alert(
                "☕ **[소담터 카페]**\n맛있는 커피가 넉넉하게 준비되었습니다. 커피 한 잔 하러 오세요! 🟢"
            )
            st.rerun()

    # 🟡 2단계 변경
    if st.sidebar.button("🟡 2단계: 소진임박 (15)", use_container_width=True):
        if sheet_stock:
            sheet_stock.update_cell(1, 2, 15)
            st.cache_data.clear()
            # 💡 텔레그램 알림 전송
            send_telegram_alert(
                "🏃‍♂️ **[소담터 카페]**\n오늘 준비된 커피가 얼마 남지 않았습니다! 조금만 서둘러 주세요! 🟡"
            )
            st.rerun()

    # 🔴 3단계 변경
    if st.sidebar.button("🔴 3단계: 카페마감 (0)", use_container_width=True):
        if sheet_stock:
            sheet_stock.update_cell(1, 2, 0)
            st.cache_data.clear()
            # 💡 텔레그램 알림 전송
            send_telegram_alert(
                "🌙 **[소담터 카페]**\n오늘 준비된 재고가 모두 소진되어 영업을 마감합니다. 내일 만나요! 🔴"
            )
            st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state.is_admin_logged_in = False
        st.rerun()
