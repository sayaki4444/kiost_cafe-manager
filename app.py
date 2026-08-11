import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 구글 시트 연동 설정 (스트림릿 시크릿 사용)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# 배포 시 스트림릿 클라우드의 'Secrets'에 저장할 JSON 데이터를 불러옵니다.
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 2. 스프레드시트 불러오기
# 주의: '사내카페재고'라는 이름이 일치해야 합니다.
sheet = client.open("kiost_sodam").sheet1 

# 3. 현재 남은 수량 읽어오기 (B1 셀)
current_stock = int(sheet.acell('B1').value)

# ==========================================
# UI 1. 일반 직원용 화면 (메인 화면)
# ==========================================
st.title("☕ 사내 카페 실시간 현황")

if current_stock > 0:
    st.success("🟢 현재 영업 중입니다! 카페로 오세요~")
    # 예쁘고 큰 숫자로 보여주기
    st.metric(label="오늘 남은 커피", value=f"{current_stock} 잔")
else:
    st.error("🔴 오늘 준비된 커피가 모두 소진되었습니다. 내일 뵙겠습니다!")
    st.metric(label="오늘 남은 커피", value="0 잔")


# ==========================================
# UI 2. 카페 관리자용 화면 (사이드바)
# ==========================================
st.sidebar.title("🔐 관리자 메뉴")
admin_pw = st.sidebar.text_input("비밀번호를 입력하세요", type="password")

# 비밀번호가 맞을 때만 아래 버튼들이 나타납니다. (비번은 원하는 대로 변경하세요)
if admin_pw == "0000":
    st.sidebar.success("인증 완료")
    
    if st.sidebar.button("-1잔 차감"):
        new_stock = max(0, current_stock - 1)
        sheet.update_acell('B1', new_stock)
        st.rerun() # 화면 새로고침
        
    if st.sidebar.button("-5잔 차감 (단체주문)"):
        new_stock = max(0, current_stock - 5)
        sheet.update_acell('B1', new_stock)
        st.rerun()
        
    st.sidebar.divider() # 구분선
    
    if st.sidebar.button("🚨 즉시 마감하기 (0잔)"):
        sheet.update_acell('B1', 0)
        st.rerun()
        
    if st.sidebar.button("🔄 내일 장사 준비 (200잔 초기화)"):
        sheet.update_acell('B1', 200)
        st.rerun()