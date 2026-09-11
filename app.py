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
    # 전체 기록을 넉넉하게 200개까지 불러오기
    activities = client.get_activities(0, 200)
    
    data = []
    for act in activities:
        if act['activityType']['typeKey'] == 'running':
            dist_km = round(act['distance'] / 1000, 2)
            dur_sec = int(act['duration'])
            
            # 누적 시간 포맷팅
            hrs = dur_sec // 3600
            mins = (dur_sec % 3600) // 60
            secs = dur_sec % 60
            time_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins}:{secs:02d}"
            
            # 평균 페이스 계산
            pace_sec = dur_sec / dist_km if dist_km > 0 else 0
            pace_min = int(pace_sec // 60)
            pace_sec_rem = int(pace_sec % 60)
            pace_str = f"{pace_min}:{pace_sec_rem:02d}"

            data.append({
                "날짜": act['startTimeLocal'][:10],
                "거리(km)": dist_km,
                "누적 시간": time_str,
                "평균 페이스(분/km)": pace_str,
                "평균 심박수": act.get('averageHR', 0)
            })
            
    df = pd.DataFrame(data)
    if not df.empty:
        df['날짜_dt'] = pd.to_datetime(df['날짜'])
        df['년월'] = df['날짜_dt'].dt.to_period('M').astype(str)
        df['주차'] = df['날짜_dt'].dt.strftime('%Y년 %U주차')
    return df

try:
    df = get_garmin_data()
    
    if df.empty:
        st.warning("등록된 러닝 기록이 없습니다.")
    else:
        # 상단 요약 카드
        col1, col2, col3 = st.columns(3)
        col1.metric("최근 러닝 거리", f"{df.iloc[0]['거리(km)']} km")
        col2.metric("최근 평균 페이스", df.iloc[0]['평균 페이스(분/km)'])
        col3.metric("최근 심박수", f"{df.iloc[0]['평균 심박수']} bpm")
        
        # 1. 월별 러닝 마일리지 차트
        st.write("### 📊 월별 러닝 마일리지")
        monthly_df = df.groupby('년월')['거리(km)'].sum().reset_index()
        st.bar_chart(monthly_df.set_index('년월'))

        # 2. 주차별 마일리지 확인 칸
        st.write("### 📅 주차별 누적 마일리지")
        weekly_df = df.groupby('주차')['거리(km)'].sum().reset_index()
        weekly_df.columns = ['주차', '총 거리(km)']
        st.dataframe(weekly_df.set_index('주차'), use_container_width=True)

        # 3. 훈련 상세 로그
        st.write("### 📝 훈련 상세 로그")
        display_df = df[['날짜', '거리(km)', '평균 페이스(분/km)', '누적 시간', '평균 심박수']]
        st.dataframe(display_df, use_container_width=True)

        # 4. AI 훈련 분석 (최근 기록 vs 직전 기록 비교)
        st.write("---")
        st.subheader("🤖 AI 훈련 분석")
        
        if st.button("오늘의 훈련 분석하기"):
            with st.spinner("Gemini 코치가 최근 기록과 직전 기록을 비교 분석 중입니다..."):
                recent_run = df.iloc[0]
                prev_run = df.iloc[1] if len(df) > 1 else None
                
                comparison_text = ""
                if prev_run is not None:
                    comparison_text = f"""
                    [직전 기록 (비교 대상)]
                    - 날짜: {prev_run['날짜']}
                    - 거리: {prev_run['거리(km)']}km
                    - 평균 페이스: {prev_run['평균 페이스(분/km)']}
                    - 평균 심박수: {prev_run['평균 심박수']}bpm
                    """
                
                prompt = f"""
                [가장 최근 러닝 기록]
                - 날짜: {recent_run['날짜']}
                - 거리: {recent_run['거리(km)']}km
                - 평균 페이스: {recent_run['평균 페이스(분/km)']}
                - 평균 심박수: {recent_run['평균 심박수']}bpm

                {comparison_text}

                이 러너는 다가오는 11월 JTBC 풀코스 마라톤을 준비 중입니다. 
                현재 10K 최고 기록은 45분대이고, 하프 마라톤은 1시간 39분 56초에 완주한 이력이 있습니다. 
                가장 최근 기록을 직전 기록과 비교하여 페이스 변화, 심박수 효율, 거리 증감의 의미를 분석하고, 
                풀코스 준비 관점에서 짧고 명확하게 피드백해 주세요. 
                또한 피로도를 고려해 내일 신을 러닝화(아디다스 EVO SL, 아식스 메가블라스트, 아디다스 아디오스 프로 4 중 선택)와 추천 훈련 강도를 작성해 주세요.
                """
                
                # 모델명을 최신 버전으로 변경
                model = genai.GenerativeModel("gemini-3.5-flash")
                response = model.generate_content(prompt)
                
                st.success("분석 완료!")
                st.write(response.text)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
