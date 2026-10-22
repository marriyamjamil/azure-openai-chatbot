import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env")

client = OpenAI(
    base_url=os.getenv("AZURE_OPENAI_BASE_URL", "https://niai-image-2026.services.ai.azure.com/openai/v1/"),
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)
MODEL = os.getenv("CHAT_DEPLOYMENT", "gpt-4.1-mini")
SYSTEM_PROMPT = "You are a helpful, friendly assistant."

st.set_page_config(
    page_title="Chatbot",
    page_icon="✻",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,500&display=swap');

    html, body, .stApp, [class*="css"] {font-family: 'Inter', sans-serif;}
    .stApp {background: #faf9f5;}

    /* Hide chrome and sidebar */
    [data-testid="stSidebar"], [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {display: none;}
    #MainMenu, footer, [data-testid="stToolbar"], .stAppDeployButton {display: none;}
    header[data-testid="stHeader"] {background: transparent;}
    .block-container {max-width: 720px; padding-top: 1.5rem; padding-bottom: 7rem;}

    /* Greeting */
    .greet {text-align: center; padding-top: 22vh;}
    .greet h1 {
        font-family: 'Source Serif 4', serif; font-weight: 300; font-size: 2.6rem;
        color: #3d3929; margin: 0; letter-spacing: -.5px;
    }
    .greet .star {color: #d97757; margin-right: .5rem;}
    .greet p {font-family: 'Source Serif 4', serif; color: #83827d; font-size: 1.15rem; margin-top: .6rem;}

    /* Top title */
    .top-title {font-family: 'Source Serif 4', serif; font-size: 1.3rem; color: #3d3929;}
    .top-title span {color: #d97757;}

    /* Hide avatars */
    [data-testid^="stChatMessageAvatar"], [data-testid^="chatAvatarIcon"] {display: none;}

    /* Messages */
    [data-testid="stChatMessage"] {background: transparent; padding: 6px 0; gap: 0;}
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
        font-family: 'Source Serif 4', serif; font-size: 1.05rem; line-height: 1.75; color: #3d3929;
    }
    [data-testid="stChatMessage"]:has([data-testid^="stChatMessageAvatarUser"]),
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #f0eee6; border-radius: 18px; padding: 10px 18px;
        width: fit-content; max-width: 85%; margin-left: auto; margin-bottom: 14px;
    }

    /* Input card */
    [data-testid="stBottom"] > div {background: #faf9f5;}
    [data-testid="stChatInput"] {
        background: #ffffff; border: 1px solid #e3e1d6; border-radius: 22px;
        box-shadow: 0 4px 24px rgba(61,57,41,.06);
    }
    [data-testid="stChatInput"] textarea {font-family: 'Inter', sans-serif;}
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.last_response_id = None


def greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


# ---------- Greeting / title ----------
if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="greet">
            <h1><span class="star">✻</span>{greeting()}</h1>
            <p>How can I help you today?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="top-title"><span>✻</span> Chatbot</div>', unsafe_allow_html=True)
    st.write("")

# ---------- History ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Input ----------
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            stream = client.responses.create(
                model=MODEL,
                instructions=SYSTEM_PROMPT,
                input=prompt,
                previous_response_id=st.session_state.last_response_id,
                stream=True,
            )

            def tokens():
                for event in stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta
                    elif event.type == "response.completed":
                        st.session_state.last_response_id = event.response.id

            answer = st.write_stream(tokens())
        except Exception as e:
            answer = f"Error: {e}"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()