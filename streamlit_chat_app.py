# streamlit_chat_app.py
import streamlit as st
from datetime import datetime
import sqlite3
import uuid
import html
import difflib
from time import sleep

# -------------------- Config / Theme --------------------
APP_TITLE = "WOW Chat — Pro (SQLite)"
ACCENT = "#7C3AED"
ACCENT_LIGHT = "#C4B5FD"
SIDEBAR_BG = "#F6F0FF"
CHAT_BG = "#0F1724"
USER_BUBBLE = "#8B5CF6"
BOT_BUBBLE = "#6D28D9"

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="💬")

# -------------------- CSS (Noupe-inspired feel, original) --------------------
st.markdown(f"""
<style>
/* Page bg */
.reportview-container, .main {{
  background: linear-gradient(180deg, {CHAT_BG} 0%, #071024 100%);
  color: #e8e6f8;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
  background: {SIDEBAR_BG};
  padding: 18px;
  color: #1f1146;
}}

/* Chat card */
.chat-card {{
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 18px;
  height: 68vh;
  overflow: auto;
  box-shadow: 0 12px 40px rgba(2,6,23,0.6);
}}

/* bubbles */
.bubble-user {{
  background: linear-gradient(90deg, {USER_BUBBLE}, {ACCENT_LIGHT});
  color: white;
  padding: 12px 14px;
  border-radius: 14px;
  display:inline-block;
  margin: 10px 0;
  max-width:78%;
}}
.bubble-bot {{
  background: linear-gradient(90deg, {BOT_BUBBLE}, #3b0f7a);
  color: white;
  padding: 12px 14px;
  border-radius: 14px;
  display:inline-block;
  margin: 10px 0;
  max-width:78%;
}}
.meta {{
  font-size:12px;
  color:#cfc7ff;
  margin-top:6px;
}}
.room-button {{
  display:inline-block;
  border-radius:10px;
  padding:8px 12px;
  margin:6px 6px 6px 0;
  background: linear-gradient(90deg, {ACCENT}, {ACCENT_LIGHT});
  color:white;
  font-weight:600;
  border:none;
}}
.input-text input {{
  border-radius:10px !important;
  padding:10px !important;
  background:#071129 !important;
  color:#eee !important;
  border: 1px solid rgba(124,58,237,0.35) !important;
}}
.stButton>button {{
  background: linear-gradient(90deg, {ACCENT}, {ACCENT_LIGHT});
  color: white;
  border-radius: 10px;
  padding: 8px 14px;
  font-weight:700;
  border: none;
}}
@media (max-width:760px) {{
  .chat-card {{ height: 55vh; }}
}}
</style>
""", unsafe_allow_html=True)

# -------------------- SQLite: connection & helpers --------------------
@st.cache_resource
def get_db_conn(path: str = "chat_app.sqlite"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # create tables if not exist
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        room_name TEXT NOT NULL,
        sender TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn

db = get_db_conn()

def ensure_room(room_name: str):
    cur = db.cursor()
    cur.execute("SELECT name FROM rooms WHERE name = ?", (room_name,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO rooms (id, name, created_at) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), room_name, datetime.now().isoformat()))
        db.commit()

def add_msg_db(room_name: str, sender: str, text: str):
    cur = db.cursor()
    cur.execute("INSERT INTO messages (id, room_name, sender, text, timestamp) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), room_name, sender, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()

def get_messages(room_name: str, limit: int = 500):
    cur = db.cursor()
    cur.execute("SELECT sender, text, timestamp FROM messages WHERE room_name = ? ORDER BY rowid ASC LIMIT ?", (room_name, limit))
    return cur.fetchall()

def get_rooms():
    cur = db.cursor()
    cur.execute("SELECT name FROM rooms ORDER BY rowid ASC")
    return [r["name"] for r in cur.fetchall()]

# -------------------- Session state init --------------------
if "username" not in st.session_state:
    st.session_state.username = "Guest"
if "active_room" not in st.session_state:
    st.session_state.active_room = "General"
if "bot_typing" not in st.session_state:
    st.session_state.bot_typing = False

# ensure default room exists
ensure_room("General")

# -------------------- Bot logic (rule-based + fuzzy) --------------------
BOT_KV = {
    "hello": "Hello! 👋 I'm WOW Chat. Ask me anything or type 'help' to see commands.",
    "hi": "Hi! Nice to meet you. Try 'help' to see options.",
    "how are you": "I'm a demo bot — running smoothly! 😊",
    "help": "Try: 'hello', 'time', 'joke', 'bye', or ask about the app.",
    "time": lambda _: f"Server time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "joke": "Why do programmers prefer dark mode? Because light attracts bugs! 🐞",
    "bye": "Goodbye! Have a great day 👋",
    "thanks": "You're welcome! 🙌"
}
BOT_KEYS = list(BOT_KV.keys())

def bot_respond(text: str) -> str:
    t = (text or "").lower()
    for k in BOT_KEYS:
        if k in t:
            v = BOT_KV[k]
            return v(t) if callable(v) else v
    # fuzzy match by short strings
    best = difflib.get_close_matches(t, BOT_KEYS, n=1, cutoff=0.6)
    if best:
        v = BOT_KV[best[0]]
        return v(t) if callable(v) else v
    # fallback simple: mirror with suggestion
    words = t.split()
    if any(w in words for w in ["who","what","why","how","where"]):
        return "That's a great question — as a demo bot I give simple replies. Try 'help' for examples."
    return "I don't know that. Try 'help' or ask something else!"

# -------------------- Sidebar UI --------------------
with st.sidebar:
    st.title("💬 WOW Chat")
    st.write("A polished demo chat app — fully yours, original code.")
    user = st.text_input("Display name", value=st.session_state.username)
    st.session_state.username = (user.strip() or "Guest")
    st.markdown("---")
    st.subheader("Rooms")
    # show rooms list
    known_rooms = get_rooms()
    # create/join
    new_room = st.text_input("Create / Join room (name)", key="__new_room")
    if st.button("Enter room"):
        r = (new_room or "").strip()
        if r:
            ensure_room(r)
            st.session_state.active_room = r
            st.experimental_rerun()
    st.markdown("**Available**")
    for r in known_rooms:
        if st.button(r, key=f"room_{r}"):
            st.session_state.active_room = r
            st.experimental_rerun()
    st.markdown("---")
    if st.button("Clear this room messages"):
        cur = db.cursor()
        cur.execute("DELETE FROM messages WHERE room_name = ?", (st.session_state.active_room,))
        db.commit()
        st.experimental_rerun()
    if st.button("Reset DB (wipe)"):
        cur = db.cursor()
        cur.execute("DELETE FROM messages")
        cur.execute("DELETE FROM rooms")
        db.commit()
        ensure_room("General")
        st.session_state.active_room = "General"
        st.experimental_rerun()

# -------------------- Main chat area --------------------
st.markdown(f"## 🏠 Room: {html.escape(st.session_state.active_room)}")

# chat card container
chat_holder = st.container()
with chat_holder:
    st.markdown('<div class="chat-card" id="chatcard">', unsafe_allow_html=True)

    msgs = get_messages(st.session_state.active_room, limit=1000)
    for m in msgs:
        sender = html.escape(m["sender"])
        text = html.escape(m["text"])
        ts = m["timestamp"]
        if sender == st.session_state.username:
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:flex-end;"><div class="bubble-user">{sender}: {text}</div><div class="meta">{ts}</div></div>', unsafe_allow_html=True)
        elif sender.lower().startswith("bot"):
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:flex-start;"><div class="bubble-bot">{sender}: {text}</div><div class="meta">{ts}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:flex-start;"><div class="bubble-bot">{sender}: {text}</div><div class="meta">{ts}</div></div>', unsafe_allow_html=True)

    # typing indicator
    if st.session_state.bot_typing:
        st.markdown('<div class="meta">Bot is typing...</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# auto-scroll to bottom (JS)
st.components.v1.html("""
<script>
const el = document.getElementById("chatcard");
if (el) { el.scrollTop = el.scrollHeight; }
</script>
""", height=0)

# -------------------- Message input form --------------------
with st.form(key="msg_form", clear_on_submit=False):
    cols = st.columns([9,1])
    with cols[0]:
        message = st.text_input("Type a message", key="msg_input", placeholder="Say hello, try 'help' or 'joke'...")
    with cols[1]:
        send = st.form_submit_button("Send")
    if send:
        txt = (message or "").strip()
        if txt:
            add_msg_db(st.session_state.active_room, st.session_state.username, txt)
            # set typing flag and rerun so UI shows "Bot is typing..."
            st.session_state.bot_typing = True
            # trigger rerun to render typing indicator
            st.experimental_rerun()

# -------------------- Bot responder when typing flag is set --------------------
if st.session_state.bot_typing:
    # small UX delay
    sleep(0.8)
    # get last message in room
    msgs = get_messages(st.session_state.active_room, limit=1000)
    if msgs:
        last = msgs[-1]
        if last["sender"] == st.session_state.username:
            bot_text = bot_respond(last["text"])
            add_msg_db(st.session_state.active_room, "Bot", bot_text)
    st.session_state.bot_typing = False
    # clear input safely
    if "msg_input" in st.session_state:
        st.session_state.msg_input = ""
    st.experimental_rerun()

# -------------------- Footer controls --------------------
st.markdown("---")
c1, c2, c3 = st.columns([1,1,8])
with c1:
    if st.button("Refresh"):
        st.experimental_rerun()
with c2:
    if st.button("Export messages (.txt)"):
        # simple export of current room messages
        rows = get_messages(st.session_state.active_room, limit=5000)
        txt = "\n".join([f"{r['timestamp']} | {r['sender']}: {r['text']}" for r in rows])
        st.download_button("Download", txt, file_name=f"{st.session_state.active_room}_messages.txt", mime="text/plain")
with c3:
    st.markdown("Messages persist in local SQLite `chat_app.sqlite`. To deploy to Streamlit Cloud, push repo and set file path accordingly.")
