import streamlit as st
from auth_db import (
    init_auth_db, register_user, authenticate_user,
    verify_email, request_password_reset, reset_password
)
from chatbot.core import run_chat

st.set_page_config(page_title="🧠 Jira Chatbot", layout="wide")
init_auth_db()

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", [
    "Login", "Register", "Verify Email", "Forgot Password", "Reset Password", "Chatbot"
])

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Register
if menu == "Register":
    st.subheader("Create Account")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        try:
            register_user(username, email, password)
            st.success("Registered! Check console for email verification token.")
        except Exception as e:
            st.error(f"Failed to register: {str(e)}")

# Verify Email
elif menu == "Verify Email":
    st.subheader("Verify Email")
    token = st.text_input("Verification Token")

    if st.button("Verify"):
        if verify_email(token):
            st.success("Email verified!")
        else:
            st.error("Invalid or expired token.")

# Login
elif menu == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(email, password):
            st.success(f"Welcome, {email}")
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = email
        else:
            st.error("Invalid login credentials")

# Forgot Password
elif menu == "Forgot Password":
    st.subheader("Forgot Password")
    email = st.text_input("Enter your email")

    if st.button("Send Reset Token"):
        token = request_password_reset(email)
        if token:
            st.success("Reset token generated. Check console.")
        else:
            st.error("Email not found")

# Reset Password
elif menu == "Reset Password":
    st.subheader("Reset Your Password")
    token = st.text_input("Reset Token")
    new_password = st.text_input("New Password", type="password")

    if st.button("Reset"):
        if reset_password(token, new_password):
            st.success("Password reset successful.")
        else:
            st.error("Failed. Token may be invalid or expired.")

# Chatbot
elif menu == "Chatbot" and st.session_state.get("logged_in"):
    st.title("🤖 Jira Semantic Assistant")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("Ask a Jira-related question...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            result = run_chat(user_input, user_email=st.session_state["user_email"], history=st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": result})

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

elif menu == "Chatbot":
    st.warning("Please log in to access the chatbot.")
