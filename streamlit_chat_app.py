import streamlit as st
from datetime import datetime
import html
import uuid

# ---------------------- Shared in-memory state ----------------------
@st.experimental_singleton
def get_chat_state():
    # rooms: { room_name: [ {id, user, text, ts} ] }
    return {"rooms": {"General": [], "Tech": []}, "users_online": set()}

state = get_chat_state()

# ---------------------- Helpers ----------------------
def add_message(room, user, text):
    text = text.strip()
    if not text:
        return
    msg = {
        "id": str(uuid.uuid4()),
        "user": user,
        "text": html.escape(text),
        "ts": datetime.utcnow().isoformat() + "Z"
    }
    state["rooms"].setdefault(room, []).append(msg)

def format_message(msg):
    # returns HTML for a single message (escaped already)
    ts = datetime.fromisoformat(msg["ts"].replace("Z",""))
    time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
    user = html.escape(msg["user"])
    text = msg["text"]
    initials = "".join([p[0] for p in user.split() if p]).upper()[:2] or "U"
    avatar = f'<div style="width:40px;height:40px;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#6a11cb,#2575fc);color:white;font-weight:700;margin-right:10px;">{initials}</div>'
    bubble = f"""
    <div style="display:flex;align-items:flex-start;margin-bottom:12px;">
      {avatar}
      <div style="max-width:78%;">
        <div style="font-size:14px;font-weight:600;margin-bottom:4px;">{user} <span style="font-weight:400;font-size:12px;color:#888;margin-left:8px;">{time_str}</span></div>
        <div style="background:rgba(255,255,255,0.06);padding:10px;border-radius:8px;line-height:1.4;color:#fff;">{text}</div>
      </div>
    </div>
    """
    return bubble

# ---------------------- App UI ----------------------
st.set_page_config(page_title="✨ StreamChat — In-Memory Chat", layout="wide", initial_sidebar_state="expanded")

# Custom styling for a glassmorphism look
st.markdown(
    """
    <style>
    .reportview-container { background: linear-gradient(180deg,#0f1724 0%, #06121a 100%); color: #fff; }
    .stButton>button { background: linear-gradient(90deg,#7b2ff7,#2ac3f6); color: white; border: none; padding: 8px 14px; border-radius: 8px; }
    .stTextInput>div>div>input { background: rgba(255,255,255,0.03); color: #fff; border: none; padding: 10px; border-radius: 8px; }
    .stSelectbox>div>div>select { background: rgba(255,255,255,0.03); color: #fff; border-radius: 8px; padding:8px; }
    .stCheckbox>div>label { color: #fff; }
    </style>
    """, unsafe_allow_html=True
)

# Sidebar: user + rooms
with st.sidebar:
    st.markdown("## 🔮 StreamChat (No DB)")
    username = st.text_input("Enter your name", value=st.session_state.get("username", "Guest"))
    if username:
        st.session_state["username"] = username.strip()
    st.markdown("### Rooms")
    rooms = list(state["rooms"].keys())
    chosen = st.selectbox("Choose room", rooms, index=0)
    new_room = st.text_input("Create room (name)")
    if st.button("➕ Create room") and new_room.strip():
        rn = new_room.strip()
        if rn in state["rooms"]:
            st.warning("Room already exists.")
        else:
            state["rooms"][rn] = []
            st.experimental_rerun()

    st.markdown("---")
    live = st.checkbox("🔄 Live mode (auto-refresh every 2s)", value=True)
    st.markdown("Messages are kept **in-memory** and will disappear if the app restarts. Good for demos & prototypes!")
    st.markdown("---")
    st.markdown("**Quick tips**\n- Use a unique name to differentiate users.\n- Open multiple browser windows to simulate multiple users.\n- Live mode reloads the page automatically for near real-time.\n", unsafe_allow_html=True)

# Inject auto-reload JS if live
if live:
    reload_js = "<script>setInterval(()=>{location.reload();},2000);</script>"
    st.components.v1.html(reload_js, height=0)

# Main area: chat UI
col1, col2 = st.columns([3,1])

with col1:
    st.markdown(f"### 💬 Room: {chosen}")
    chat_box = st.container()

    # Message input
    with st.form(key="msg_form", clear_on_submit=True):
        msg_text = st.text_area("Write a message...", height=80, key="msg_input")
        submit = st.form_submit_button("Send")
        if submit:
            user = st.session_state.get("username", "Guest")
            add_message(chosen, user, msg_text)
            # after sending we rerun so messages show immediately
            st.experimental_rerun()

    # Display messages
    with chat_box:
        msgs = state["rooms"].get(chosen, [])
        # Show last 200 messages only (safety)
        for m in msgs[-200:]:
            st.markdown(format_message(m), unsafe_allow_html=True)

with col2:
    st.markdown("### 👥 Active Users (this demo)")
    # Simple active users list: we show the distinct recent authors in room
    msgs = state["rooms"].get(chosen, [])
    recent_users = list({m["user"] for m in msgs[-200:]})
    if recent_users:
        for u in recent_users:
            initials = "".join([p[0] for p in u.split() if p]).upper()[:2] or "U"
            st.markdown(f'<div style="display:flex;align-items:center;margin-bottom:8px;"><div style="width:36px;height:36px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#ff416c,#ff4b2b);color:white;font-weight:700;margin-right:10px;">{initials}</div><div style="font-weight:600">{html.escape(u)}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown("_No active users in this room yet._")

# Footer area: small controls
st.markdown("---")
colf1, colf2 = st.columns([3,1])
with colf1:
    if st.button("Clear room messages"):
        state["rooms"][chosen] = []
        st.experimental_rerun()
with colf2:
    if st.button("Reset all (wipe demo)"):
        # reset state - be careful
        for r in list(state["rooms"].keys()):
            state["rooms"][r] = []
        st.experimental_rerun()

# Small "system" info
st.markdown("<div style='color:#9ca3af;font-size:13px;'>In-memory mode — not persistent. To make this production-ready, connect a database or a backend server.</div>", unsafe_allow_html=True)
