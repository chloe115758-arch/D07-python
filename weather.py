import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 파일의 키를 읽어 옴

API = {
    "날씨": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
    "대기질": "https://api.openweathermap.org/data/2.5/air_pollution",  # 🔌 OpenWeather 대기질
}

AQI_NAMES = {1: "좋음", 2: "양호", 3: "보통", 4: "나쁨", 5: "매우 나쁨"}
AQI_TIPS = {
    1: "공기가 깨끗해요. 야외 활동하기 좋아요.",
    2: "공기가 괜찮아요.",
    3: "민감한 분은 장시간 야외 활동을 줄이세요.",
    4: "마스크를 쓰고 야외 활동을 줄이세요.",
    5: "외출을 피하고 창문을 닫아 주세요.",
}

SEOUL = {"lat": 37.5665, "lon": 126.9780}  # 서울 위도·경도


class ApiError(Exception):
    """화면에 그대로 보여 줘도 되는 한국어 한 줄 안내"""


def describe_temp(feels):
    if feels <= 0:
        return "매우 추워요. 두꺼운 외투가 필요해요."
    if feels <= 10:
        return "쌀쌀해요. 겉옷을 챙기세요."
    if feels <= 20:
        return "선선해서 지내기 좋아요."
    if feels <= 27:
        return "따뜻해요. 가벼운 옷차림이 좋아요."
    return "더워요. 물을 자주 마시세요."


def describe_humidity(h):
    if h < 30:
        return "건조해요."
    if h <= 60:
        return "적당해요."
    return "습해요."


def call_api(url, extra):
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        raise ApiError(".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요")

    params = {**SEOUL, "appid": key, **extra}
    try:
        res = requests.get(url, params=params, timeout=10)  # 🔌 API 호출
    except requests.exceptions.RequestException:
        raise ApiError("서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요.") from None

    if res.status_code == 401:
        raise ApiError("키가 틀렸거나 아직 켜지지 않았어요(가입 후 최대 2시간).")
    if res.status_code == 429:
        raise ApiError("1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요.")
    if res.status_code != 200:
        raise ApiError("정보를 가져오지 못했어요. 잠시 뒤에 다시 해 주세요.")
    return res.json()


@st.cache_data(ttl=600)
def load_weather():
    data = call_api(API["날씨"], {"units": "metric", "lang": "kr"})
    return {
        "temp": data["main"]["temp"],  # data["main"]["temp"] = 지금 기온(°C)
        "feels": data["main"]["feels_like"],  # data["main"]["feels_like"] = 체감 온도(°C)
        "humidity": data["main"]["humidity"],  # data["main"]["humidity"] = 습도(%)
        "desc": data["weather"][0]["description"],  # data["weather"][0]["description"] = 날씨 설명
        "rain": data.get("rain", {}).get("1h", 0),  # data["rain"]["1h"] = 최근 1시간 비(mm)
        "snow": data.get("snow", {}).get("1h", 0),  # data["snow"]["1h"] = 최근 1시간 눈(mm)
    }


@st.cache_data(ttl=600)
def load_air():
    data = call_api(API["대기질"], {})
    item = data["list"][0]  # data["list"][0] = 가장 최근 대기질 한 건
    return {
        "aqi": item["main"]["aqi"],  # item["main"]["aqi"] = 대기질 등급(1 좋음 ~ 5 매우 나쁨)
        "pm25": item["components"]["pm2_5"],  # item["components"]["pm2_5"] = 초미세먼지(㎍/㎥)
        "pm10": item["components"]["pm10"],  # item["components"]["pm10"] = 미세먼지(㎍/㎥)
    }


def show_weather():
    try:
        w = load_weather()
    except ApiError as e:
        st.error(f"날씨: {e}")
        return
    st.subheader("날씨")
    st.metric("기온", f"{w['temp']:.1f}°C")
    st.write(w["desc"])
    st.write(f"체감 온도: {w['feels']:.1f}°C — {describe_temp(w['feels'])}")
    st.write(f"습도: {w['humidity']}% — {describe_humidity(w['humidity'])}")
    if w["rain"] or w["snow"]:
        st.write(f"강수: 비 {w['rain']}mm / 눈 {w['snow']}mm (최근 1시간)")
    else:
        st.write("강수: 지금은 비나 눈이 오지 않아요.")


def show_air():
    try:
        a = load_air()
    except ApiError as e:
        st.error(f"대기질: {e}")
        return
    st.subheader("대기질")
    st.metric("등급", AQI_NAMES[a["aqi"]])
    st.write(AQI_TIPS[a["aqi"]])
    st.write(f"초미세먼지(PM2.5): {a['pm25']:.1f}㎍/㎥")
    st.write(f"미세먼지(PM10): {a['pm10']:.1f}㎍/㎥")


def main():
    st.set_page_config(page_title="서울 날씨")
    st.markdown(
        """<style>
        .stApp { background: #ffffff; }
        div.stButton > button { background: #000000; color: #ffffff;
            border: none; border-radius: 12px; padding: 8px 20px; }
        div.stButton > button:hover { background: #333333; color: #ffffff; }
        </style>""",
        unsafe_allow_html=True,
    )
    st.title("서울 현재 날씨")

    if st.button("새로 불러오기"):
        st.cache_data.clear()  # 이 버튼에서만 캐시를 지움

    col1, col2 = st.columns(2)  # 칸마다 따로 불러서 한쪽이 실패해도 다른 쪽은 보임
    with col1:
        show_weather()
    with col2:
        show_air()

    st.caption("출처: 날씨·대기질 - OpenWeather (10분마다 갱신)")


if __name__ == "__main__":
    main()
