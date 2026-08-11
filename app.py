import streamlit as st
import requests
from datetime import datetime
import pytz

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="소담터 - 사내 카페",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. PC 모바일 뷰 고정 + 모던 다크 테마 커스텀 CSS
custom_css = """
<style>
    /* 전체 배경 (어두운 그래디언트) */
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #12131c 100%);
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* PC 접속 시 화면 중앙에 모바일 크기로 고정 (핵심) */
    .main .block-container {
        max-width: 430px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto;
    }

    /* Streamlit 기본 상단 헤더/푸터 숨기기 */
    header, footer {
        visibility: hidden !important;
        height: 0px !important;
    }

    /* 상단 프로필/시간 헤더 */
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

    /* 중앙 메인 원형 카드 */
    .main-circle-card {
        background: radial-gradient(circle at 50% 30%, #32234d 0%, #13141f 75%);
        border-radius: 50%;
        width: 260px;
        height: 260px;
        margin: 20px auto;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 10px 40px rgba(147, 51, 234, 0.2), inset 0 0 15px rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 배너/알림 반투명 카드 */
    .highlight-card {
        background: linear-gradient(135deg, rgba(88, 28, 135, 0.4) 0%, rgba(24, 24, 37, 0.7) 100%);
        border-radius: 20px;
        padding: 18px 20px;
        margin: 15px 0;
        border: 1px solid rgba(168, 85, 247, 0.25);
        backdrop-filter: blur(12px);
    }

    /* 그리드 라운드 카드 */
    .custom-card {
        background: #181926;
        border-radius: 20px;
        padding: 18px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
        text-align: center;
    }

    /* 버튼 모던 스타일 재정의 */
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

    /* 입력 폼 다크 스타일화 */
    .stTextInput > div > div > input {
        background-color: #181926 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* 탭(Tab) 디자인 커스텀 */
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

    /* Metric 및 Alert 카드 스타일 다크 톤 맞춤 */
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

# CSS 주입
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------------
# 상단 UI 헤더 및 메인 그래픽 영역
# -------------------------------------------------------------------

# 1. 상단 헤더
st.markdown("""
<div class="top-header">
    <div>
        <div class="header-title">Good day ☕</div>
        <div class="header-sub">Sodam-teo Cafe</div>
    </div>
    <div style="width: 40px; height: 40px; border-radius: 50%; background: #3b2d54; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,0.2);">
        ☕
    </div>
</div>
""", unsafe_allow_html=True)

# 2. 중앙 메인 원형 카드
st.markdown("""
<div class="main-circle-card">
    <div style="font-size: 13px; color: #c084fc; margin-bottom: 6px;">☕ Cafe Status</div>
    <div style="font-size: 32px; font-weight: 800; color: #ffffff; letter-spacing: -1px;">
        소담터
    </div>
    <div style="font-size: 12px; color: #8E8EA0; margin-top: 4px;">운영시간 10:00 - 16:00</div>
    <div style="margin-top: 14px; background: rgba(192, 132, 252, 0.15); padding: 5px 14px; border-radius: 20px; font-size: 12px; color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.3);">
        Real-time Inventory
    </div>
</div>
""", unsafe_allow_html=True)

# 3. 퀵 메모 섹션
with st.container():
    user_input = st.text_input("메모 작성", placeholder="오늘의 상태를 입력하세요...")
    if st.button("저장하기", key="save_btn"):
        if user_input:
            st.success(f"저장 완료: {user_input}")

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 기존 탭(Tab) 메뉴 및 백엔드 로직 연동
# -------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["☕ 카페 현황", "🏆 인기 투표", "💬 끄적끄적 방명록"])

# --- [탭 1] 카페 현황 및 날씨 ---
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not is_weekday or not is_opening_hours:
        st.error("### 🌙 운영 시간 외\n사내 카페 운영 시간은 **평일 10:00 ~ 16:00** 입니다.\n내일 영업 시간에 만나요! ☕")
    elif current_stock > 30:
        st.success("### 🟢 여유 있어요!\n맛있는 커피가 넉넉하게 준비되어 있습니다. 천천히 오세요~ ☕")
    elif current_stock > 0:
        st.warning("### 🟡 마감 임박!\n오늘 준비된 커피가 얼마 남지 않았어요. 조금만 서둘러 주세요! 🏃‍♂️")
    else:
        st.error("### 🔴 금일 마감\n오늘 준비된 커피가 모두 소진되었습니다. 내일 더 맛있는 커피로 만나요! 🌙")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        weather_req = requests.get("https://wttr.in/Busan?format=%c+%t&m", timeout=3)
        if weather_req.status_code == 200:
            st.info(f"🌤️ **오늘의 부산 날씨:** {weather_req.text}  |  상쾌한 음료와 함께 기분 좋은 하루 보내세요!")
    except:
        pass

# --- [탭 2] 인기 메뉴 TOP 3 & 투표 ---
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏆 가장 사랑받는 메뉴 TOP 3")
    
    try:
        sheet_vote = doc.worksheet("투표")
        vote_data = sheet_vote.get_all_values()[1:]
        vote_data.sort(key=lambda x: int(x[1]), reverse=True)
        top3 = vote_data[:3]
        
        col1, col2, col3 = st.columns(3)
        if len(top3) >= 1:
            col1.metric(label="🥇 1위", value=top3[0][0], delta=f"{top3[0][1]}표")
        if len(top3) >= 2:
            col2.metric(label="🥈 2위", value=top3[1][0], delta=f"{top3[1][1]}표")
        if len(top3) >= 3:
            col3.metric(label="🥉 3위", value=top3[2][0], delta=f"{top3[2][1]}표")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("👉 나도 최애 메뉴에 투표하기"):
            st.caption("메뉴를 누르면 즉시 1표가 올라갑니다!")
            vote_cols = st.columns(4)
            for i, row in enumerate(vote_data):
                menu_name = row[0]
                current_votes = int(row[1])
                if vote_cols[i % 4].button(menu_name, key=f"vote_{i}"):
                    sheet_vote.update_cell(i + 2, 2, current_votes + 1)
                    st.toast(f"{menu_name}에 투표하셨습니다! 🎉")
                    st.rerun()
    except:
        pass

# --- [탭 3] 한줄 게시판 (방명록) ---
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💬 끄적끄적 한줄 게시판")
    
    try:
        sheet_guest = doc.worksheet("방명록")
        
        with st.form("guestbook_form", clear_on_submit=True):
            new_comment = st.text_input("메뉴 건의나 응원의 한마디를 남겨주세요!", placeholder="예: 시원한 콜드브루도 들어오면 좋겠어요!")
            submitted = st.form_submit_button("등록하기")
            
            if submitted and new_comment:
                kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%m-%d %H:%M")
                sheet_guest.append_row([kst, new_comment])
                st.cache_data.clear()
                st.success("소중한 의견이 등록되었습니다!")
                st.rerun()
                
        guest_data = sheet_guest.get_all_values()
        if len(guest_data) > 1:
            data_rows = guest_data[1:]
            st.markdown("##### 💌 최근 남겨진 이야기")
            for row in reversed(data_rows[-5:]):
                st.info(f"**{row[0]}** | {row[1]}")
        else:
            st.caption("아직 등록된 글이 없습니다.")
    except:
        pass

# -------------------------------------------------------------------
# 관리자용 메뉴 (사이드바)
# -------------------------------------------------------------------
st.sidebar.title("🔐 관리자 메뉴")
admin_pw = st.sidebar.text_input("비밀번호를 입력하세요", type="password")

if admin_pw == "0000":
    st.sidebar.success("인증 완료")
    
    if current_stock > 30:
        current_status_text = "🟢 여유 가득"
    elif current_stock > 0:
        current_status_text = "🟡 마감 임박"
    else:
        current_status_text = "🔴 금일 마감"
        
    st.sidebar.info(f"현재 반영된 상태: **{current_status_text}**")
    st.sidebar.divider()
    
    st.sidebar.markdown("### 🛠️ 상태 변경하기")
    
    if st.sidebar.button("🟢 1단계: 여유 가득", use_container_width=True):
        sheet.update_acell('B1', 200)
        st.rerun()
        
    if st.sidebar.button("🟡 2단계: 마감 임박", use_container_width=True):
        sheet.update_acell('B1', 15)
        st.rerun()
        
    if st.sidebar.button("🔴 3단계: 금일 마감", use_container_width=True):
        sheet.update_acell('B1', 0)
        st.rerun()
