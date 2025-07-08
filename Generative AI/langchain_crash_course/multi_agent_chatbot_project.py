# ===============================
# File: agents.py
# Description: LangGraph backend with multi‑agent routing (FAQ → general/specific, Search)
# ===============================
from __future__ import annotations
import os
import re
from typing import Dict, Any

import pandas as pd
import wikipedia
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, initialize_agent
from langgraph.graph import Graph

# ---------- Tools ---------- #

class CSVFAQTool:
    """Simple lookup tool that returns an exact‑match answer from a CSV file.

    The CSV is expected to have two columns: `question` and `answer`."""

    def __init__(self, csv_path: str):
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(f"CSV FAQ file not found: {csv_path}")
        self.df = pd.read_csv(csv_path)
        # Normalize for quick lookup
        self.df["question_norm"] = self.df["question"].str.lower().str.strip()

    def __call__(self, question: str) -> str | None:
        match = self.df[self.df["question_norm"] == question.lower().strip()]
        if not match.empty:
            return match.iloc[0]["answer"]
        return None


def wiki_search(query: str, sentences: int = 2) -> str:
    """Return a short summary from Wikipedia (best effort)."""
    try:
        page_title = wikipedia.search(query)[0]
        summary = wikipedia.summary(page_title, sentences=sentences)
        return summary
    except Exception:
        return "Wikipedia did not return results."

# ---------- Agent / Node definitions ---------- #

def build_graph(csv_path: str) -> Graph:
    """Construct and return the LangGraph with three inner nodes and a hierarchical router.

    Nodes:
      • router            – chooses between faq_router or search
      • faq_router        – chooses between general_faq and specific_faq
      • general_faq       – LLM‑only answers
      • specific_faq      – CSV lookup, fallback to LLM
      • search            – web/wiki + LLM answer
    """

    # --- Shared resources --- #
    llm_det = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # deterministic for lookup
    llm_creative = ChatOpenAI(model="gpt-4o", temperature=0.7)

    csv_tool = CSVFAQTool(csv_path)

    # Prompt templates
    general_prompt = PromptTemplate.from_template(
        """You are an internal knowledge bot. Answer the question as clearly and concisely as possible.\n\nQuestion: {question}\nAnswer:"""
    )

    search_synthesis_prompt = PromptTemplate.from_template(
        """You are an expert research assistant. Based on the context below, craft a helpful answer.\n\nContext:\n{context}\n\nUser question: {question}\nHelpful answer:"""
    )

    # --- Node functions --- #
    def general_faq_node(state: Dict[str, Any]):
        q = state["input"]
        response = llm_det(general_prompt.format_prompt(question=q).to_messages()).content
        state["response"] = response
        return state

    def specific_faq_node(state: Dict[str, Any]):
        q = state["input"]
        answer = csv_tool(q)
        if answer:
            state["response"] = answer
        else:
            # Fallback to LLM with explicit notice
            reply = llm_creative(
                general_prompt.format_prompt(question=q + " (Answer based on best available knowledge)").to_messages()
            ).content
            state["response"] = reply
        return state

    def search_node(state: Dict[str, Any]):
        q = state["input"]
        wiki_ctx = wiki_search(q)
        # Could extend with real web search (SerpAPI / DuckDuckGo, etc.)
        combined_ctx = wiki_ctx
        answer = llm_creative(
            search_synthesis_prompt.format_prompt(context=combined_ctx, question=q).to_messages()
        ).content
        state["response"] = answer
        return state

    # --- Routers --- #
    def faq_router(state: Dict[str, Any]):
        q = state["input"].lower()
        # Very naive classifier – improve with few‑shot LLM classification
        if re.search(r"(order|payment|price|refund|shipping)", q):
            return "specific_faq"
        return "general_faq"

    def top_router(state: Dict[str, Any]):
        q = state["input"].lower()
        if q.startswith("search") or "wiki" in q or "web" in q:
            return "search"
        return "faq_router"

    # --- Graph wiring --- #
    graph = Graph()

    # Register nodes
    graph.add_node("general_faq", general_faq_node)
    graph.add_node("specific_faq", specific_faq_node)
    graph.add_node("search", search_node)

    # Register routers
    graph.add_node("faq_router", faq_router, edges={
        "general_faq": "general_faq",
        "specific_faq": "specific_faq",
    })

    graph.add_node("router", top_router, edges={
        "faq_router": "faq_router",
        "search": "search",
    })

    graph.set_entry_point("router")
    return graph

# Convenience wrapper for Streamlit UI
_graph_cache: Graph | None = None
def get_graph(csv_path: str = "faq_data.csv") -> Graph:
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = build_graph(csv_path)
    return _graph_cache


def run_chat(question: str, csv_path: str = "faq_data.csv") -> str:
    graph = get_graph(csv_path)
    result_state = graph.invoke({"input": question})
    return result_state["response"]

# ===============================
# File: streamlit_ui.py
# Description: Minimal Streamlit front‑end.
# ===============================

"""Streamlit UI for the multi‑agent LangGraph chatbot.
Save as `streamlit_ui.py` and run with:
    streamlit run streamlit_ui.py
"""

import streamlit as st
from agents import run_chat

st.set_page_config(page_title="Multi‑Agent Chatbot", page_icon="🤖")

if "history" not in st.session_state:
    st.session_state.history = []  # list[(role, text)]

st.title("🤖 Multi‑Agent LangGraph Chatbot")

user_input = st.chat_input("Ask me anything…")
if user_input:
    # Get response from backend
    answer = run_chat(user_input)
    st.session_state.history.append(("user", user_input))
    st.session_state.history.append(("bot", answer))

# Display conversation
for role, text in st.session_state.history:
    with st.chat_message("assistant" if role == "bot" else "user"):
        st.markdown(text)

st.sidebar.header("About")
st.sidebar.write(
    "This demo routes messages between FAQ (general/specific) and Search nodes using LangGraph.\n"
    "Configure your **OPENAI_API_KEY** in the environment before launching."
)

# ===============================
# Quick‑start notes (kept here for convenience)
# ===============================
# 1. Create `faq_data.csv` with two columns: `question,answer`.
# 2. Set the environment variable OPENAI_API_KEY (and optionally SERPAPI_KEY).
# 3. Install dependencies:
#       pip install langchain langgraph streamlit openai pandas wikipedia duckduckgo-search
# 4. Run: streamlit run streamlit_ui.py
# ===============================
