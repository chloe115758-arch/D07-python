import os

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

load_dotenv()  # .env 파일의 키를 읽어 옴

API = {
    "채팅": "https://api.openai.com/v1/chat/completions",  # 🔌 OpenAI 채팅 (openai 패키지가 이 주소로 요청)
}
MODEL = "gpt-4o-mini"


class ApiError(Exception):
    """화면에 그대로 보여 줘도 되는 한국어 한 줄 안내"""


def ask(messages):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ApiError(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요")

    try:
        client = OpenAI(api_key=key, timeout=30)
        res = client.chat.completions.create(model=MODEL, messages=messages)  # 🔌 API 호출
        return res.choices[0].message.content  # res.choices[0].message.content = 챗봇 답변
    except AuthenticationError:
        raise ApiError("OpenAI 키가 틀렸어요.") from None
    except RateLimitError:
        raise ApiError("너무 많이 불렀거나 사용량(크레딧)이 부족해요. 잠시 뒤에 다시 해 주세요.") from None
    except APIConnectionError:
        raise ApiError("OpenAI 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요.") from None
    except Exception:
        raise ApiError("답변을 가져오지 못했어요. 잠시 뒤에 다시 해 주세요.") from None


STYLE = """<style>
.stApp { background: #ffffff; }
div.stButton > button { background: #000000; color: #ffffff; border: none;
    border-radius: 12px; padding: 8px 20px; }
div.stButton > button:hover { background: #333333; color: #ffffff; }
</style>"""


# 마우스를 따라오는 캐릭터: 부모 페이지에 직접 붙여서 화면 전체에서 따라오게 함
FOLLOWER = """<script>
const doc = window.parent.document;
if (!doc.getElementById("gpt-follower")) {
  const el = doc.createElement("div");
  el.id = "gpt-follower";
  el.innerHTML = "🤖<span style='position:absolute;left:34px;top:-6px;background:#000;color:#fff;"
    + "font-size:12px;padding:3px 8px;border-radius:12px;white-space:nowrap'>ChatGPT</span>";
  el.style.cssText = "position:fixed;left:0;top:0;font-size:36px;z-index:99999;"
    + "pointer-events:none;user-select:none;";
  doc.body.appendChild(el);

  let mx = 100, my = 100, x = 100, y = 100;
  doc.addEventListener("mousemove", (e) => { mx = e.clientX + 16; my = e.clientY + 16; });
  (function loop() {
    x += (mx - x) * 0.12;  // 조금씩 늦게 따라오게
    y += (my - y) * 0.12;
    el.style.transform = `translate(${x}px, ${y}px)`;
    requestAnimationFrame(loop);
  })();
}
</script>"""


def main():
    st.set_page_config(page_title="챗봇")
    st.markdown(STYLE, unsafe_allow_html=True)
    components.html(FOLLOWER, height=0)
    st.title("챗봇")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("대화 지우기"):
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    prompt = st.chat_input("메시지를 입력하세요")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("생각 중..."):
                    answer = ask(st.session_state.messages)
            except ApiError as e:
                st.error(str(e))
                st.session_state.messages.pop()  # 실패한 질문은 대화에서 뺌
                return
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    st.caption(f"모델: {MODEL} · 답변: OpenAI")


if __name__ == "__main__":
    main()
