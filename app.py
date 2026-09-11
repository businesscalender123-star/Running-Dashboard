import streamlit as st
from garminconnect import Garmin
import pandas as pd

st.set_page_config(page_title="My Running Analytics", layout="wide")
st.title("🏃‍♂️ 나만의 러닝 분석 대시보드")

# Streamlit 보안 비밀번호(Secrets)에서 가민 로그인 정보 가져오기
garmin_id = st.secrets["GARMIN_EMAIL"]
garmin_pw = st.secrets["GARMIN_PASSWORD"]

@st.cache_data(ttl=3600) # 1시간마다 가민 데이터 새로고침
def get_garmin_data():
    client = Garmin(garmin_id, garmin_pw)
    client.login()
    # 최근 10개의 활동 가져오기
    activities = client.get_activities(0, 10)
    
    data = []
    for act in activities:
        if act['activityType']['typeKey'] == 'running':
            data.append({
                "날짜": act['startTimeLocal'][:10],
                "거리(km)": round(act['distance'] / 1000, 2),
                "시간(분)": round(act['duration'] / 60, 1),
                "평균 심박수": act.get('averageHR', 0),
                "평균 페이스(분/km)": f"{int((act['duration'] / (act['distance'] / 1000)) // 60)}:{int((act['duration'] / (act['distance'] / 1000)) % 60):02d}"
            })
    return pd.DataFrame(data)

st.subheader("🏆 11월 JTBC 풀코스 마라톤 대비 훈련 기록")

try:
    df = get_garmin_data()
    
    # 상단 요약 카드
    col1, col2, col3 = st.columns(3)
    col1.metric("최근 러닝 거리", f"{df.iloc[0]['거리(km)']} km")
    col2.metric("최근 평균 페이스", df.iloc[0]['평균 페이스(분/km)'])
    col3.metric("최근 심박수", f"{df.iloc[0]['평균 심박수']} bpm")
    
    # 표 및 차트 시각화
    st.write("### 📊 최근 거리 변화 추이")
    st.bar_chart(df.set_index("날짜")["거리(km)"])
    
    st.write("### 📝 훈련 상세 로그")
    st.dataframe(df)
    
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 비밀번호 설정을 확인해 주세요.")