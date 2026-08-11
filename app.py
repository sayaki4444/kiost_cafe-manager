import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import requests
from datetime import datetime
import pytz

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="KIOST 사내 카페", page_icon="☕", layout="centered")

# 1. 구글 시트 연동 및 시간 설정
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
doc = client.open("kiost_sodam")
sheet = doc.sheet1

# 한국 시간 가져오기
tz = pytz.timezone('Asia/Seoul')
now = datetime.now(tz)
is_weekday = now.weekday() < 5 # 0:월 ~ 4:금
is_opening_hours = 10 <= now.hour < 16

try:
    current_stock = int(sheet.acell('B1').value)
except:
    current_stock = 0

# ==========================================
# UI 상단: 시원한 여름 카페 배너 이미지 🖼️
# ==========================================
# use_column_width 대신 use_container_width로 수정 완료!
st.image("https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=1000&q=80", use_container_width=True)

st.markdown("<h2 style='text-align: center; color: #0077B6;'>🌊 KIOST Summer 사내 카페 🧊</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #0096C7; font-weight: bold;'>시원한 아이스 아메리카노와 함께 활기찬 여름 보내세요! 🌴</p>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 탭(Tab) 메뉴로 깔끔하게 화면 분리하기 📱
# ==========================================
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
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
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


# ==========================================
# UI 5. 카페 관리자용 화면 (사이드바)
# ==========================================
st.sidebar.title("🔐 관리자 메뉴")
admin_pw = st.sidebar.text_input("비밀번호를 입력하세요", type="password")

if admin_pw == "0000":
    st.sidebar.success("인증 완료")
    
    if current_stock > 30:
        current_status_text = "🟢 여유 있어요"
    elif current_stock > 0:
        current_status_text = "🟡 마감 임박"
    else:
        current_status_text = "🔴 금일 마감"
        
    st.sidebar.info(f"현재 반영된 상태: **{current_status_text}**")
    st.sidebar.divider()
    
    st.sidebar.markdown("### 🛠️ 상태 변경하기")
    
    if st.sidebar.button("🟢 1단계: 여유 있어요로 변경", use_container_width=True):
        sheet.update_acell('B1', 200)
        st.rerun()
        
    if st.sidebar.button("🟡 2단계: 마감 임박으로 변경", use_container_width=True):
        sheet.update_acell('B1', 15)
        st.rerun()
        
    if st.sidebar.button("🔴 3단계: 즉시 마감하기", use_container_width=True):
        sheet.update_acell('B1', 0)
        st.rerun()
