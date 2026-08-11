import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import requests

# --- 페이지 기본 설정 ---
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

# ==========================================
# UI 1. 메인 화면 (숫자 제거 & 감성 문구)
# ==========================================
st.markdown("<h1 style='text-align: center; color: #4B3832;'>☕ KIOST 사내 카페</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888;'>오늘의 커피 현황을 알려드려요</p>", unsafe_allow_html=True)
st.divider()

# 숫자를 숨기고 3단계 '신호등' 상태로 보여주기
if current_stock > 30:
    # 30잔 초과일 때: 넉넉함
    st.success("### 🟢 여유 있어요!\n맛있는 커피가 넉넉하게 준비되어 있습니다. 천천히 오세요~ ☕")
    
elif current_stock > 0:
    # 30잔 이하 ~ 1잔 이상일 때: 마감 임박
    st.warning("### 🟡 마감 임박!\n오늘 준비된 커피가 얼마 남지 않았어요. 조금만 서둘러 주세요! 🏃‍♂️")
    
else:
    # 0잔일 때: 영업 마감
    st.error("### 🔴 금일 마감\n오늘 준비된 커피가 모두 소진되었습니다. 내일 더 맛있는 커피로 만나요! 🌙")

st.divider()

# ==========================================
# UI 2. 하단 날씨 정보 (한국 섭씨 온도 &m 적용)
# ==========================================
st.markdown("### 🌤️ 오늘의 부산 날씨")
try:
    weather_req = requests.get("https://wttr.in/Busan?format=%c+%t&m", timeout=3)
    if weather_req.status_code == 200:
        st.info(f"지금 밖은 **{weather_req.text}** 입니다. 기분 좋은 하루 보내세요!")
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
    
    # 관리자에게만 현재 정확한 남은 수량을 보여줍니다!
    st.sidebar.info(f"📊 현재 남은 수량: **{current_stock}잔**")
    st.sidebar.divider()
    
    col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
    if col_btn1.button("-5잔"):
        new_stock = max(0, current_stock - 5)
        sheet.update_acell('B1', new_stock)
        st.rerun() 
        
    if col_btn2.button("-10잔"):
        new_stock = max(0, current_stock - 10)
        sheet.update_acell('B1', new_stock)
        st.rerun()

    if col_btn3.button("-20잔"):
        new_stock = max(0, current_stock - 20)
        sheet.update_acell('B1', new_stock)
        st.rerun() 
        
    st.sidebar.divider() 
    
    if st.sidebar.button("🚨 즉시 마감하기 (0잔)", use_container_width=True):
        sheet.update_acell('B1', 0)
        st.rerun()
        
    if st.sidebar.button("🔄 내일 장사 준비 (200잔)", use_container_width=True):
        sheet.update_acell('B1', 200)
        st.rerun()
