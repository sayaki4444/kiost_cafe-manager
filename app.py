import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import requests # 날씨를 가져오기 위한 부품 추가

# --- 페이지 기본 설정 (가장 위에 있어야 합니다) ---
st.set_page_config(page_title="사내 카페 알리미", page_icon="☕", layout="centered")

# 1. 구글 시트 연동 설정
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open("kiost_sodam").sheet1

try:
    current_stock = int(sheet.acell('B1').value)
except:
    current_stock = 0

MAX_STOCK = 200 # 기준 수량
display_stock = min(current_stock, MAX_STOCK) # 에러 방지용

# ==========================================
# UI 1. 메인 화면 (디자인 업그레이드)
# ==========================================
# 예쁜 제목과 설명 (중앙 정렬)
st.markdown("<h1 style='text-align: center; color: #4B3832;'>☕ KIOST 사내 카페</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888;'>헛걸음하지 마시고 남은 수량을 미리 확인하세요!</p>", unsafe_allow_html=True)
st.divider()

if current_stock > 0:
    st.success("🟢 현재 영업 중입니다! 맛있는 커피가 기다리고 있어요.")
    
    # 남은 수량을 화면 가운데에 예쁘게 배치
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(label="오늘 남은 커피", value=f"{current_stock} 잔")
    
    # 시각적인 게이지 바 (Progress bar)
    st.progress(display_stock / MAX_STOCK, text="오늘의 커피 잔여량")

else:
    st.error("🔴 오늘 준비된 커피가 모두 소진되었습니다. 내일 뵙겠습니다!")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(label="오늘 남은 커피", value="0 잔")
    st.progress(0.0, text="영업 마감")

st.divider()

# ==========================================
# UI 2. 하단 날씨 정보 (가입 필요 없는 무료 API 활용)
# ==========================================
st.markdown("### 🌤️ 오늘의 부산 날씨")
try:
    # 3초 안에 부산 날씨(이모티콘+온도)를 가져옵니다.
    weather_req = requests.get("https://wttr.in/Busan?format=%c+%t", timeout=3)
    if weather_req.status_code == 200:
        st.info(f"지금 밖은 **{weather_req.text}** 입니다. 커피 한 잔 어떠세요?")
    else:
        st.caption("날씨 정보를 잠시 불러올 수 없습니다.")
except:
    st.caption("날씨 정보를 잠시 불러올 수 없습니다.")


# ==========================================
# UI 3. 카페 관리자용 화면 (사이드바)
# ==========================================
st.sidebar.title("🔐 관리자 메뉴")
admin_pw = st.sidebar.text_input("비밀번호를 입력하세요", type="password")

if admin_pw == "0000":
    st.sidebar.success("인증 완료")
    
    # 버튼들을 2개씩 나란히 배치해서 깔끔하게 만듦
    col_btn1, col_btn2 = st.sidebar.columns(2)
    if col_btn1.button("-1잔"):
        new_stock = max(0, current_stock - 1)
        sheet.update_acell('B1', new_stock)
        st.rerun() 
        
    if col_btn2.button("-5잔"):
        new_stock = max(0, current_stock - 5)
        sheet.update_acell('B1', new_stock)
        st.rerun()
        
    st.sidebar.divider() 
    
    # 버튼 가로 길이를 꽉 차게 변경 (use_container_width=True)
    if st.sidebar.button("🚨 즉시 마감하기 (0잔)", use_container_width=True):
        sheet.update_acell('B1', 0)
        st.rerun()
        
    if st.sidebar.button("🔄 내일 장사 준비 (200잔)", use_container_width=True):
        sheet.update_acell('B1', 200)
        st.rerun()
