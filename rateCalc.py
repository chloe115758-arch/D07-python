import os
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 파일의 키를 읽어 옴

API = {
    "환율": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 환율(달러 기준)
}

# 통화코드: (국기, 이름, 국기 색상들)
CURRENCIES = {
    "KRW": ("🇰🇷", "대한민국 원", ["#FFFFFF", "#CD2E3A", "#0047A0", "#000000"]),
    "USD": ("🇺🇸", "미국 달러", ["#B22234", "#FFFFFF", "#3C3B6E"]),
    "JPY": ("🇯🇵", "일본 엔", ["#FFFFFF", "#BC002D", "#FFFFFF"]),
    "EUR": ("🇪🇺", "유로", ["#003399", "#FFCC00", "#003399"]),
    "CNY": ("🇨🇳", "중국 위안", ["#DE2910", "#FFDE00"]),
    "GBP": ("🇬🇧", "영국 파운드", ["#012169", "#FFFFFF", "#C8102E"]),
    "AUD": ("🇦🇺", "호주 달러", ["#00008B", "#FFFFFF", "#FF0000"]),
    "CAD": ("🇨🇦", "캐나다 달러", ["#FF0000", "#FFFFFF", "#FF0000"]),
    "CHF": ("🇨🇭", "스위스 프랑", ["#FF0000", "#FFFFFF", "#FF0000"]),
    "THB": ("🇹🇭", "태국 바트", ["#A51931", "#F4F5F8", "#2D2A4A", "#F4F5F8", "#A51931"]),
    "VND": ("🇻🇳", "베트남 동", ["#DA251D", "#FFFF00"]),
}
NO_DECIMAL = {"KRW", "JPY", "VND"}  # 소수점 없이 보여 줄 통화


class ApiError(Exception):
    """화면에 그대로 보여 줘도 되는 한국어 한 줄 안내"""


@st.cache_data(ttl=3600)
def load_rates():
    key = os.getenv("EXCHANGERATE_API_KEY")
    if not key:
        raise ApiError(".env에 EXCHANGERATE_API_KEY가 없어요. .env.example을 보고 채워 주세요")

    try:
        res = requests.get(
            API["환율"],
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )  # 🔌 API 호출
        data = res.json()
    except requests.exceptions.RequestException:
        raise ApiError("환율 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요.") from None
    except ValueError:
        raise ApiError("환율 정보를 읽지 못했어요. 잠시 뒤에 다시 해 주세요.") from None

    if data.get("result") != "success":  # data["result"] = "success" 또는 "error"
        error_type = data.get("error-type")  # data["error-type"] = 에러 종류
        if error_type == "invalid-key":
            raise ApiError("환율 키가 틀렸어요.")
        if error_type == "inactive-account":
            raise ApiError("환율 사이트 가입 인증 메일을 확인해 주세요.")
        if error_type == "quota-reached":
            raise ApiError("이번 달 무료 사용량(1,500번)을 다 썼어요.")
        raise ApiError("환율 정보를 가져오지 못했어요. 잠시 뒤에 다시 해 주세요.")

    return {
        "rates": data["conversion_rates"],  # data["conversion_rates"] = 1달러당 각 통화 값
        "updated": data["time_last_update_utc"],  # data["time_last_update_utc"] = 환율 기준 시각(UTC)
    }


def to_korea_time(utc_text):
    return parsedate_to_datetime(utc_text).astimezone(ZoneInfo("Asia/Seoul"))


def stripe(colors):
    """국기 색을 가로 띠로 보여 주는 CSS"""
    n = len(colors)
    parts = [f"{c} {i * 100 / n:.2f}% {(i + 1) * 100 / n:.2f}%" for i, c in enumerate(colors)]
    return f"linear-gradient(to right, {', '.join(parts)})"


def money(value, code):
    return f"{value:,.0f}" if code in NO_DECIMAL else f"{value:,.2f}"


def label(code):
    flag, name, _ = CURRENCIES[code]
    return f"{flag} {code} · {name}"


def flag_card(code, text):
    flag, name, colors = CURRENCIES[code]
    return f"""<div class="card">
<div class="stripe" style="background:{stripe(colors)}"></div>
<div class="card-body"><span class="flag">{flag}</span>
<span class="code">{code}</span> <span class="name">{name}</span>
<div class="value">{text}</div></div></div>"""


STYLE = """<style>
.stApp { background: #ffffff; }
div.stButton > button { background: #000000; color: #ffffff; border: none;
    border-radius: 12px; padding: 8px 20px; }
div.stButton > button:hover { background: #333333; color: #ffffff; }
.card { border: 1px solid #e5e5e5; border-radius: 12px; overflow: hidden; margin-bottom: 12px; }
.stripe { height: 12px; border-bottom: 1px solid #e5e5e5; }
.card-body { padding: 14px 16px; }
.flag { font-size: 28px; margin-right: 8px; }
.code { font-weight: 700; font-size: 18px; }
.name { color: #666666; font-size: 14px; }
.value { font-size: 28px; font-weight: 700; margin-top: 6px; }
.row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-top: 1px solid #f0f0f0; }
.chip { width: 40px; height: 14px; border: 1px solid #e5e5e5; border-radius: 12px; flex: none; }
.row .grow { flex: 1; }
</style>"""


def main():
    st.set_page_config(page_title="환율 계산기")
    st.markdown(STYLE, unsafe_allow_html=True)
    st.title("환율 계산기")

    if st.button("새로 불러오기"):
        st.cache_data.clear()  # 이 버튼에서만 캐시를 지움

    try:
        loaded = load_rates()
    except ApiError as e:
        st.error(str(e))
        return
    rates = loaded["rates"]

    codes = [c for c in CURRENCIES if c in rates]
    col1, col2 = st.columns(2)
    with col1:
        src = st.selectbox("보내는 통화", codes, index=codes.index("USD"), format_func=label)
    with col2:
        dst = st.selectbox("받는 통화", codes, index=codes.index("KRW"), format_func=label)
    amount = st.number_input("금액", min_value=0.0, value=100.0, step=10.0)

    result = amount / rates[src] * rates[dst]  # 달러 기준 값끼리 나누어 환산
    one = rates[dst] / rates[src]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(flag_card(src, money(amount, src)), unsafe_allow_html=True)
    with c2:
        st.markdown(flag_card(dst, money(result, dst)), unsafe_allow_html=True)
    st.write(f"1 {src} = {one:,.4f} {dst}")

    st.subheader(f"1 {src}는 얼마일까요?")
    rows = ""
    for code in codes:
        flag, name, colors = CURRENCIES[code]
        value = rates[code] / rates[src]
        rows += (
            f'<div class="row"><div class="chip" style="background:{stripe(colors)}"></div>'
            f'<div class="grow">{flag} {code} · {name}</div><b>{value:,.4f}</b></div>'
        )
    st.markdown(rows, unsafe_allow_html=True)

    updated = to_korea_time(loaded["updated"]).strftime("%Y-%m-%d %H:%M")
    st.caption(f"환율: ExchangeRate-API · 기준 시각: {updated} (한국 시간) · 하루 한 번 갱신돼요")


if __name__ == "__main__":
    main()
