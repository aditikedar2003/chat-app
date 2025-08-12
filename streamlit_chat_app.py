import streamlit as st
from datetime import datetime

# -------------------- PAGE SETTINGS --------------------
st.set_page_config(page_title="WOW Chat App", page_icon="💬", layout="wide")

# -------------------- CUSTOM CSS --------------------
st.markdown("""
    <style>
        body {
            background-color: #1e003d;
            color: white;
        }
        .stTextInput>div>div>input {
            background-color: #2b0057;
            color: white;
            border: 1px solid #7b2cbf;
            border-radius: 8px;
        }
        .stButton>button {
            background-color: #7b2cbf;
            color: white;
            border-radius: 8px;
            font-weight: bold;
            border: none;
        }
        .stButton>button:hover {
            background-color: #9d4edd;
            color: white;
        }
        .chat-bubble-user {
            background-color: #7b2cbf;
            padding: 10px;
            border-radius: 12px;
            margin: 5px 0;
            color: white;
        }
        .chat-bubble-bot {
            background-color: #2b0057;
            padding: 10px;
            border-radius: 12px;
            margin: 5px 0;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE INIT --------------------
if "rooms" not in st.session_state:
    st.session_state.rooms = {}  # {room_name: [{"sender":..., "text":..., "time":...}]}
if "current_room" not in st.session_state:
    st.session_state.current_room = None
if "msg_input" not in st.session_state:
    st.session_state.msg_input = ""

# -------------------- FUNCTIONS --------------------
def select_room(room):
    st.session_state.current_room = room
    if room not in st.session_state.rooms:
        st.session_state.rooms[room] = []

def send_message():
    msg = st.session_state.msg_input.strip()
    if msg and st.session_state.current_room:
        # Append user message
        st.session_state.rooms[st.session_state.current_room].append({
            "sender": "You",
            "text": msg,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        # Append bot reply
        st.session_state.rooms[st.session_state.current_room].append({
            "sender": "Bot",
            "text": f"You said: {msg}",
            "time": datetime.now().strftime("%H:%M:%S")
        })
        # Clear input
        st.session_state.msg_input = ""

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.title("💬 WOW Chat")
    st.subheader("Rooms")
    room_name = st.text_input("Create / Join Room")
    if st.button("Enter Room"):
        if room_name:
            select_room(room_name)

    if st.session_state.rooms:
        st.subheader("Available Rooms")
        for r in st.session_state.rooms.keys():
            if st.button(r):
                select_room(r)

# -------------------- MAIN CHAT AREA --------------------
if st.session_state.current_room:
    st.header(f"🏠 Room: {st.session_state.current_room}")

    # Show chat history
    for msg in st.session_state.rooms[st.session_state.current_room]:
        if msg["sender"] == "You":
            st.markdown(f"<div class='chat-bubble-user'><b>{msg['sender']}:</b> {msg['text']} <br><small>{msg['time']}</small></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-bot'><b>{msg['sender']}:</b> {msg['text']} <br><small>{msg['time']}</small></div>", unsafe_allow_html=True)

    # Input box
    st.text_input("Type your message...", key="msg_input", on_change=send_message)

else:
    st.info("👈 Join or create a room from the sidebar to start chatting.")
