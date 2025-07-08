# =============================
# File: chatbot_graph.py
# =============================
"""
LangGraph + LangChain based chatbot back‑end for an e‑commerce help‑desk.

* Routes: FAQ (sub‑routes: Payments, Orders) and General Query
* Uses OpenAI chat model via LangChain (replace OPENAI_API_KEY env‑var)
* Exposes `run_chatbot()` so the Streamlit UI can invoke the graph easily.
"""

from __future__ import annotations

import os
from typing import List, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

# ──────────────────────────────────────────────────────────────────────────────
# Model setup
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk‑YOUR_KEY_HERE")  # <‑‑ replace in .env or OS env
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=OPENAI_API_KEY)

# ──────────────────────────────────────────────────────────────────────────────
# Node functions
# ──────────────────────────────────────────────────────────────────────────────

def faq_payments_node(state: Dict) -> Dict:
    """Handle FAQ → Payments questions."""
    q = state["user_input"]
    history: List[BaseMessage] = state.get("chat_history", [])
    sys_prompt = (
        "You are an e‑commerce customer‑service FAQ assistant. "
        "Answer QUESTIONS ABOUT PAYMENTS only (billing, refunds, failed payments, accepted methods, etc.). "
        "Be concise and friendly."
    )
    messages = [HumanMessage(content=f"{sys_prompt}\n\nQ: {q}")]
    ans = llm.invoke(messages).content

    history += [HumanMessage(content=q), AIMessage(content=ans)]
    state.update({"chat_history": history, "response": ans})
    return state


def faq_orders_node(state: Dict) -> Dict:
    """Handle FAQ → Orders questions."""
    q = state["user_input"]
    history: List[BaseMessage] = state.get("chat_history", [])
    sys_prompt = (
        "You are an e‑commerce customer‑service FAQ assistant. "
        "Answer QUESTIONS ABOUT ORDERS only (status, tracking, cancellation, modifications, etc.). "
        "Be concise and friendly."
    )
    messages = [HumanMessage(content=f"{sys_prompt}\n\nQ: {q}")]
    ans = llm.invoke(messages).content

    history += [HumanMessage(content=q), AIMessage(content=ans)]
    state.update({"chat_history": history, "response": ans})
    return state


def general_query_node(state: Dict) -> Dict:
    """Handle any other general customer‑support query."""
    q = state["user_input"]
    history: List[BaseMessage] = state.get("chat_history", [])
    sys_prompt = (
        "You are a helpful, empathetic e‑commerce customer‑support assistant. "
        "Answer the user's question in a clear, friendly manner."
    )
    messages = [HumanMessage(content=f"{sys_prompt}\n\nQ: {q}")]
    ans = llm.invoke(messages).content

    history += [HumanMessage(content=q), AIMessage(content=ans)]
    state.update({"chat_history": history, "response": ans})
    return state

# ──────────────────────────────────────────────────────────────────────────────
# Graph construction helper
# ──────────────────────────────────────────────────────────────────────────────

def build_chatbot_graph():
    sg = StateGraph(dict)  # our state type is just a vanilla dict

    # Identity router node – does nothing but let us attach conditional edges
    def identity(state: Dict) -> Dict:
        return state

    sg.add_node("router", identity)
    sg.add_node("FAQ_PAYMENTS", faq_payments_node)
    sg.add_node("FAQ_ORDERS", faq_orders_node)
    sg.add_node("GENERAL", general_query_node)

    # ‑‑ Edge selection logic (LangChain routing inside LangGraph) ‑‑
    def route_selector(state: Dict) -> str:
        """Decide which node to send control to next, based on UI‑supplied metadata."""
        route = (state.get("route") or "").lower()
        sub = (state.get("subroute") or "").lower()
        if route == "faq":
            return "FAQ_PAYMENTS" if sub == "payments" else "FAQ_ORDERS"
        return "GENERAL"

    sg.add_conditional_edges(
        "router",
        route_selector,
        {
            "FAQ_PAYMENTS": "FAQ_PAYMENTS",
            "FAQ_ORDERS": "FAQ_ORDERS",
            "GENERAL": "GENERAL",
        },
    )

    # All leaf nodes end the graph
    sg.add_edge("FAQ_PAYMENTS", END)
    sg.add_edge("FAQ_ORDERS", END)
    sg.add_edge("GENERAL", END)

    sg.set_entry_point("router")
    return sg.compile()

# Build once at import time so Streamlit can reuse it across reruns
_graph = build_chatbot_graph()


def run_chatbot(
    user_input: str,
    route: str,
    subroute: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
):
    """Helper invoked by the UI. Returns (response, updated_history)."""
    chat_history = chat_history or []
    result_state = _graph.invoke(
        {
            "user_input": user_input,
            "route": route,
            "subroute": subroute,
            "chat_history": chat_history,
        }
    )
    return result_state["response"], result_state["chat_history"]


# =============================
# File: app.py   (Streamlit UI)
# =============================

"""
Streamlit front‑end driving the LangGraph chatbot defined in chatbot_graph.py.
Run with:
    streamlit run app.py
"""

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from chatbot_graph import run_chatbot  # local import

st.set_page_config(page_title="E‑Commerce Chatbot", page_icon="🛒", layout="centered")

st.title("🛍️ Customer‑Support Chatbot")

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar – conversation settings (routing input)
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Routing Settings")
    query_type = st.selectbox("Query category", ["FAQ", "General"], index=0)
    subroute = None
    if query_type == "FAQ":
        subroute = st.radio("FAQ topic", ["Payments", "Orders"], horizontal=True)
    st.markdown("---")
    st.markdown(
        "*Powered by LangChain + LangGraph*  \n"
        "[GitHub](https://github.com/langchain-ai/langgraph) | "
        "[Streamlit](https://streamlit.io)"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Session‑state for chat history
# ──────────────────────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history: List[BaseMessage] = []

# ──────────────────────────────────────────────────────────────────────────────
# Chat input & handling
# ──────────────────────────────────────────────────────────────────────────────
user_msg = st.chat_input("Ask me anything…")

if user_msg:
    # Echo user message
    st.chat_message("user").markdown(user_msg)

    # Call back‑end
    reply, updated_hist = run_chatbot(
        user_input=user_msg,
        route=query_type,
        subroute=subroute,
        chat_history=st.session_state.history,
    )

    st.session_state.history = updated_hist

    st.chat_message("assistant").markdown(reply)

# ──────────────────────────────────────────────────────────────────────────────
# Optional expandable chat log
# ──────────────────────────────────────────────────────────────────────────────
with st.expander("Conversation log"):
    for msg in st.session_state.history:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        st.markdown(f"**{role}:** {msg.content}")

# =============================
# File: requirements.txt (optional helper)
# =============================
# langgraph>=0.0.40
# langchain-openai>=0.1.0
# streamlit>=1.33
# python-dotenv  # if you prefer .env files for API keys
