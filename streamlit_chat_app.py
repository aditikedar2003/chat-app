import streamlit as st
from datetime import datetime
import time

st.set_page_config(page_title="WOW Chat 💬", layout="wide")

# Store chat state in memory (persists only during runtime)
@st.cache_resource
def get_state():
    return {"rooms": {}, "users": {}}

state = get_state()

# CSS for creative UI
st.markdown("""
<style>
body {
    background-color: #f4f4f4;
    font-family: 'Segoe UI', sans-serif;
}
.chat-container {
    background-color: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    height: 70vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}
.message {
    padding: 8px 12px;
    border-radius: 8px;
    margin: 4px 0;
    max-width: 70%;
}
.user-msg {
    background-color: #DCF8C6;
    align-self: flex-end;
}
.other-msg {
    background-color: #EAEAEA;
    align-self: flex-start;
}
.timestamp {
    font-size: 10px;
    color: gray;
}
.room-title {
    font-weight: bold;
    font-size: 22px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar - login / join room
with st.sidebar:
    st.header("Join Chat Room 💬")
    username = st.text_input("Enter your name")
    room = st.text_input("Enter room name", "General")
    join = st.button("Join Room")

# Initialize room if not exists
if join and username.strip() != "":
    if room not in state["rooms"]:
        state["rooms"][room] = []
    state["users"][username] = room
    st.session_state["username"] = username
    st.session_state["room"] = room
    st.rerun()

# Main Chat Interface
if "username" in st.session_state and "room" in st.session_state:
    current_user = st.session_state["username"]
    current_room = st.session_state["room"]

    st.markdown(f"<div class='room-title'>Room: {current_room}</div>", unsafe_allow_html=True)

    # Display messages
    chat_box = st.container()
    with chat_box:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for msg in state["rooms"].get(current_room, []):
            if msg["user"] == current_user:
                st.markdown(f"<div class='message user-msg'><b>{msg['user']}</b>: {msg['text']}<div class='timestamp'>{msg['time']}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='message other-msg'><b>{msg['user']}</b>: {msg['text']}<div class='timestamp'>{msg['time']}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Message input
    col1, col2 = st.columns([8, 2])
    with col1:
        message_text = st.text_input("Type your message...", key="msg_input")
    with col2:
        if st.button("Send"):
            if message_text.strip():
                state["rooms"][current_room].append({
                    "user": current_user,
                    "text": message_text,
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                st.session_state["msg_input"] = ""
                st.rerun()

    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()
else:
    st.info("Please join a chat room from the sidebar to start messaging.")
