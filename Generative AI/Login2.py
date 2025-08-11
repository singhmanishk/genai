import streamlit as st
import sqlite3
import datetime

# ---------- Database Setup ----------
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    messages TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ---------- Helper Functions ----------
def register_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def save_chat(user_id, title, messages):
    c.execute("INSERT INTO chats (user_id, title, messages) VALUES (?, ?, ?)",
              (user_id, title, messages))
    conn.commit()

def get_user_chats(user_id):
    c.execute("SELECT id, title FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    return c.fetchall()

def get_chat_messages(chat_id):
    c.execute("SELECT messages FROM chats WHERE id = ?", (chat_id,))
    result = c.fetchone()
    return result[0] if result else ""

# ---------- Session State ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_title" not in st.session_state:
    st.session_state.chat_title = None
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

# ---------- Sidebar ----------
with st.sidebar:
    st.title("💬 Chatbot")

    if not st.session_state.logged_in:
        tab = st.radio("Select", ["Login", "Register"], label_visibility="collapsed")

        if tab == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.success("Login successful!")
                else:
                    st.error("Invalid credentials")

        elif tab == "Register":
            username = st.text_input("New Username")
            password = st.text_input("New Password", type="password")
            if st.button("Register", use_container_width=True):
                if register_user(username, password):
                    st.success("Registration successful! Please log in.")
                else:
                    st.error("Username already exists")

    else:
        # New Chat
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_title = f"Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            st.session_state.active_chat_id = None

        st.markdown("---")
        st.markdown("### Previous Chats")

        chats = get_user_chats(st.session_state.user_id)
        for cid, title in chats:
            if st.button(f"📄 {title}", key=f"chat_{cid}", use_container_width=True):
                st.session_state.messages = eval(get_chat_messages(cid))
                st.session_state.chat_title = title
                st.session_state.active_chat_id = cid

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.messages = []
            st.session_state.active_chat_id = None

# ---------- Main Chat Area ----------
st.title("💬 Chatbot")

if st.session_state.logged_in:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Replace this with actual AI call
        bot_reply = f"🤖 You said: {prompt}"
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    if st.button("💾 Save Chat"):
        if st.session_state.chat_title and st.session_state.messages:
            save_chat(st.session_state.user_id, st.session_state.chat_title, str(st.session_state.messages))
            st.success("Chat saved!")
else:
    st.info("Please log in to start chatting.")
