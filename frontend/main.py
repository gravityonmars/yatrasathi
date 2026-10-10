import streamlit as st
import requests
import uuid

st.set_page_config(page_title="YatraSathi AI", page_icon="🏔️", layout="centered")
st.title("🏔️ YatraSathi - Nepal Travel Assistant")

API_URL = "http://127.0.0.1:8000/chat"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest_traveler"
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about weather, forex, or trekking in Nepal..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Finding information..."):
            try:
                payload = {
                    "message": prompt,
                    "user_id": st.session_state.user_id,
                    "session_id": st.session_state.session_id,
                }
                res = requests.post(API_URL, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    reply = data.get("response", "No response received.")
                    st.session_state.session_id = data.get("session_id", st.session_state.session_id)
                else:
                    reply = f"Error {res.status_code}: {res.text}"
            except Exception as e:
                reply = f"Failed to connect to backend: {e}"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})