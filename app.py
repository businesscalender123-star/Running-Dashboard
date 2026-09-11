import streamlit as st
from garminconnect import Garmin
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="My Running Analytics", layout="wide")
st.title("🏃‍♂️ 나만의 러닝 분석 대시보드")

# 보안 변수 불러오기
garmin_id = st.secrets["GARMIN_EMAIL"]
garmin_pw = st.secrets["GARMIN_PASSWORD"]
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data(ttl=3600)
def get_garmin_data():
    client = Garmin(garmin_id, garmin_pw)
    client.login()
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
    
    col1, col2, col3 = st.columns(3)
    col1.metric("최근 러닝 거리", f"{df.iloc[0]['거리(km)']} km")
    col2.metric("최근 평균 페이스", df.iloc[0]['평균 페이스(분/km)'])
    col3.metric("최근 심박수", f"{df.iloc[0]['평균 심박수']} bpm")
    
    st.write("### 📊 최근 거리 변화 추이")
    st.bar_chart(df.set_index("날짜")["거리(km)"])
    
    st.write("### 📝 훈련 상세 로그")
    st.dataframe(df)

    st.write("---")
    st.subheader("🤖 AI 훈련 분석")
    
    if st.button("오늘의 훈련 분석하기"):
        with st.spinner("Gemini 코치가 데이터를 분석하고 있습니다..."):
            recent_run = df.iloc[0]
            
            prompt = f"""
            오늘 달린 거리: {recent_run['거리(km)']}km
            평균 페이스: {recent_run['평균 페이스(분/km)']}
            평균 심박수: {recent_run['평균 심박수']}bpm
            
            이 러너는 다가오는 11월 JTBC 풀코스 마라톤을 준비 중입니다. 
            현재 10K 최고 기록은 45분대이고, 하프 마라톤은 1시간 39분 56초에 완주한 이력이 있습니다. 
            오늘의 훈련 데이터를 기존 최고 기록 및 풀코스 준비 과정과 연관 지어 짧고 명확하게 피드백해 주고, 
            피로도를 고려해 내일 신을 러닝화(아디다스 EVO SL, 아식스 메가블라스트, 아디다스 아디오스 프로 4 중 선택)와 추천 훈련 강도를 작성해 주세요.
            """
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            
            st.success("분석 완료!")
            st.write(response.text)

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다. 설정 상태를 확인해 주세요.")
