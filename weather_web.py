import os
import pathlib
import webbrowser
from datetime import datetime
from html import escape

import requests

from weather import (API, AQI_NAMES, AQI_TIPS, SEOUL, describe_humidity,
                     describe_temp)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather.html")

CSS = """
* { box-sizing: border-box; }
body { margin: 0; background: #fff; color: #111; padding: 16px;
       font-family: -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }
main { max-width: 480px; margin: 0 auto; }
h1 { font-size: 22px; }
.card { border: 1px solid #e5e5e5; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.card h2 { font-size: 15px; color: #666; margin: 0 0 12px; }
.big { font-size: 40px; font-weight: 700; margin: 0 0 4px; }
.row { display: flex; justify-content: space-between; padding: 8px 0; border-top: 1px solid #f0f0f0; }
.row span:first-child { color: #666; }
.tip { margin-top: 12px; padding: 12px; background: #fafafa; border-radius: 12px; }
.error { color: #b00020; }
footer { color: #888; font-size: 13px; text-align: center; }
"""


def fetch(url, extra):
    """API 한 번 호출. 성공하면 (JSON, None), 실패하면 (None, 한국어 안내)"""
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        return None, ".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요"
    params = {**SEOUL, "appid": key, **extra}
    try:
        res = requests.get(url, params=params, timeout=10)  # 🔌 API 호출
    except requests.exceptions.RequestException:
        return None, "서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."
    if res.status_code == 401:
        return None, "키가 틀렸거나 아직 켜지지 않았어요(가입 후 최대 2시간)."
    if res.status_code == 429:
        return None, "1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요."
    if res.status_code != 200:
        return None, "정보를 가져오지 못했어요. 잠시 뒤에 다시 해 주세요."
    return res.json(), None


def weather_card():
    data, err = fetch(API["날씨"], {"units": "metric", "lang": "kr"})
    if err:
        return f'<div class="card"><h2>날씨</h2><p class="error">{escape(err)}</p></div>'
    temp = data["main"]["temp"]  # data["main"]["temp"] = 지금 기온(°C)
    feels = data["main"]["feels_like"]  # data["main"]["feels_like"] = 체감 온도(°C)
    humidity = data["main"]["humidity"]  # data["main"]["humidity"] = 습도(%)
    desc = data["weather"][0]["description"]  # data["weather"][0]["description"] = 날씨 설명
    rain = data.get("rain", {}).get("1h", 0)  # data["rain"]["1h"] = 최근 1시간 비(mm)
    snow = data.get("snow", {}).get("1h", 0)  # data["snow"]["1h"] = 최근 1시간 눈(mm)
    precip = f"비 {rain}mm / 눈 {snow}mm" if rain or snow else "없음"
    return f"""<div class="card"><h2>서울 현재 날씨</h2>
<p class="big">{temp:.1f}°C</p><p>{escape(desc)}</p>
<div class="row"><span>체감 온도</span><span>{feels:.1f}°C</span></div>
<div class="row"><span>습도</span><span>{humidity}% ({describe_humidity(humidity)})</span></div>
<div class="row"><span>강수</span><span>{precip}</span></div>
<div class="tip">{describe_temp(feels)}</div></div>"""


def air_card():
    data, err = fetch(API["대기질"], {})
    if err:
        return f'<div class="card"><h2>대기질</h2><p class="error">{escape(err)}</p></div>'
    item = data["list"][0]  # data["list"][0] = 가장 최근 대기질 한 건
    aqi = item["main"]["aqi"]  # item["main"]["aqi"] = 대기질 등급(1 좋음 ~ 5 매우 나쁨)
    pm25 = item["components"]["pm2_5"]  # item["components"]["pm2_5"] = 초미세먼지(㎍/㎥)
    pm10 = item["components"]["pm10"]  # item["components"]["pm10"] = 미세먼지(㎍/㎥)
    return f"""<div class="card"><h2>대기질</h2>
<p class="big">{AQI_NAMES[aqi]}</p>
<div class="row"><span>초미세먼지(PM2.5)</span><span>{pm25:.1f}㎍/㎥</span></div>
<div class="row"><span>미세먼지(PM10)</span><span>{pm10:.1f}㎍/㎥</span></div>
<div class="tip">{AQI_TIPS[aqi]}</div></div>"""


def main():
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>서울 날씨</title><style>{CSS}</style></head>
<body><main>
<h1>서울 날씨</h1>
{weather_card()}
{air_card()}
<footer>{now} 기준 · 출처: 날씨·대기질 - OpenWeather</footer>
</main></body></html>"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("weather.html 을 만들었어요. 브라우저에서 열게요.")
    webbrowser.open(pathlib.Path(OUT).as_uri())


if __name__ == "__main__":
    main()
