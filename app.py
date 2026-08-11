import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import requests
from datetime import datetime
import pytz # 한국 시간을 맞추기 위한 부품

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="사내 카페 알리미", page_icon="☕", layout="centered")

# 1. 구글 시트 연동 설정
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

doc = client.open("kiost_sodam")
sheet = doc.sheet1 # 첫번째 시트 (재고)

try:
    current_stock = int(sheet.acell('B1').value)
except:
    current_stock = 0

# ==========================================
# UI 1. 메인 화면 (재고 현황)
# ==========================================
st.markdown("<h1 style='text-align: center; color: #4B3832;'>☕ KIOST 사내 카페</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888;'>오늘의 커피 현황을 알려드려요</p>", unsafe_allow_html=True)
st.divider()

if current_stock > 30:
    st.success("### 🟢 여유 있어요!\n맛있는 커피가 넉넉하게 준비되어 있습니다. 천천히 오세요~ ☕")
elif current_stock > 0:
    st.warning("### 🟡 마감 임박!\n오늘 준비된 커피가 얼마 남지 않았어요. 조금만 서둘러 주세요! 🏃‍♂️")
else:
    st.error("### 🔴 금일 마감\n오늘 준비된 커피가 모두 소진되었습니다. 내일 더 맛있는 커피로 만나요! 🌙")

st.divider()

# ==========================================
# UI 2. 🏆 인기 메뉴 TOP 3 대시보드
# ==========================================
st.markdown("### 🏆 가장 사랑받는 메뉴 TOP 3")
try:
    sheet_vote = doc.worksheet("투표")
    vote_data = sheet_vote.get_all_values()[1:] # 첫 줄(제목) 제외하고 가져오기
    
    # 투표수(숫자) 기준으로 1등부터 정렬하기
    vote_data.sort(key=lambda x: int(x[1]), reverse=True)
    top3 = vote_data[:3] # 상위 3개만 자르기
    
    # 화면을 3칸으로 나누어 예쁘게 배치
    col1, col2, col3 = st.columns(3)
    if len(top3) >= 1:
        col1.metric(label="🥇 1위", value=top3[0][0], delta=f"{top3[0][1]}표")
    if len(top3) >= 2:
        col2.metric(label="🥈 2위", value=top3[1][0], delta=f"{top3[1][1]}표")
    if len(top3) >= 3:
        col3.metric(label="🥉 3위", value=top3[2][0], delta=f"{top3[2][1]}표")
        
    # (선택) 직원들이 직접 투표할 수 있는 버튼
    with st.expander("👉 나도 최애 메뉴에 투표하기"):
        st.caption("메뉴를 누르면 즉시 1표가 올라갑니다!")
        vote_cols = st.columns(4)
        for i, row in enumerate(vote_data):
            menu_name = row[0]
            current_votes = int(row[1])
            # 버튼을 누르면 구글 시트의 해당 메뉴 표수를 +1 합니다.
            if vote_cols[i % 4].button(menu_name, key=f"vote_{i}"):
                sheet_vote.update_cell(i + 2, 2, current_votes + 1)
                st.toast(f"{menu_name}에 투표하셨습니다! 🎉")
                st.rerun()
except Exception as e:
    st.caption("메뉴 데이터를 불러오는 중입니다. (투표 시트를 확인해주세요)")

st.divider()

# ==========================================
# UI 3. 💬 소통의 공간 (한줄 방명록)
# ==========================================
st.markdown("### 💬 끄적끄적 한줄 게시판")
try:
    sheet_guest = doc.worksheet("방명록")
    
    # 1. 댓글 남기기 폼(Form)
    with st.form("guestbook_form", clear_on_submit=True):
        new_comment = st.text_input("메뉴 건의나 응원의 한마디를 자유롭게 남겨주세요!", placeholder="예: 내일은 라떼가 땡기네요~")
        submitted = st.form_submit_button("등록하기")
        
        if submitted and new_comment:
            # 한국 시간으로 기록하기
            kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%m-%d %H:%M")
            sheet_guest.append_row([kst, new_comment])
            
            # --- 핵심 수정 부분 ---
            st.cache_data.clear() # 이전 기억을 지워서 즉시 최신 데이터를 불러오게 함!
            st.success("소중한 의견이 등록되었습니다!")
            st.rerun() # 즉시 화면 새로고침
            
    # 2. 최근 댓글 5개 보여주기
    guest_data = sheet_guest.get_all_values()
    if len(guest_data) > 1: # 제목줄 제외하고 데이터가 있을 때만
        data_rows = guest_data[1:]
        st.markdown("##### 💌 최근 남겨진 이야기")
        # 최신 글이 위로 오도록 뒤집어서 5개만 보여줌
        for row in reversed(data_rows[-5:]):
            st.info(f"**{row[0]}** | {row[1]}")
    else:
        st.caption("아직 등록된 글이 없습니다. 첫 번째 글을 남겨보세요!")
except Exception as e:
    st.caption(f"방명록을 불러오는 중 오류가 발생했습니다.")

# ==========================================
# UI 4. 하단 날씨 정보
# ==========================================
try:
    weather_req = requests.get("https://wttr.in/Busan?format=%c+%t&m", timeout=3)
    if weather_req.status_code == 200:
        st.caption(f"🌤️ 오늘의 부산 날씨: **{weather_req.text}**")
except:
    pass

# ==========================================
# UI 5. 카페 관리자용 화면 (사이드바) - 기존과 동일
# ==========================================
st.sidebar.title("🔐 관리자 메뉴")
admin_pw = st.sidebar.text_input("비밀번호를 입력하세요", type="password")

if admin_pw == "0000":
    st.sidebar.success("인증 완료")
    st.sidebar.info(f"📊 현재 남은 수량: **{current_stock}잔**")
    st.sidebar.divider()
    
    col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
    if col_btn1.button("-5잔"):
        sheet.update_acell('B1', max(0, current_stock - 5))
        st.rerun() 
    if col_btn2.button("-10잔"):
        sheet.update_acell('B1', max(0, current_stock - 10))
        st.rerun()
    if col_btn3.button("-20잔"):
        sheet.update_acell('B1', max(0, current_stock - 20))
        st.rerun() 
        
    st.sidebar.divider() 
    
    if st.sidebar.button("🚨 즉시 마감하기 (0잔)", use_container_width=True):
        sheet.update_acell('B1', 0)
        st.rerun()
    if st.sidebar.button("🔄 내일 장사 준비 (200잔)", use_container_width=True):
        sheet.update_acell('B1', 200)
        st.rerun()
