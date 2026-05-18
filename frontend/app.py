# frontend/app.py

import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Nepal Constitution Chatbot",
    page_icon="🏛️",
    layout="centered"
)

st.title("🏛️ Nepal Constitution Legal Chatbot v2")
st.caption("Powered by RAG + Agentic AI + Redis Memory")

# ── Session Management ────────────────────────

if "session_id" not in st.session_state:

    try:
        response = requests.post(
            f"{BACKEND_URL}/session"
        )

        response.raise_for_status()

        st.session_state.session_id = (
            response.json()["session_id"]
        )

        print(
            f"New session: "
            f"{st.session_state.session_id}"
        )

    except Exception as e:
        st.error(
            "Cannot connect to backend."
        )
        st.stop()

# ── Sidebar ───────────────────────────────────

with st.sidebar:

    st.header("Session Info")

    st.write(
        f"Session ID: "
        f"{st.session_state.session_id[:8]}..."
    )

    # clear history button
    if st.button("🗑️ Clear History"):

        try:
            requests.delete(
                f"{BACKEND_URL}/history/"
                f"{st.session_state.session_id}"
            )

            st.success("History cleared!")

            st.rerun()

        except Exception as e:
            st.error(str(e))

    # cache stats
    try:
        cache_response = requests.get(
            f"{BACKEND_URL}/cache/stats"
        )

        if cache_response.ok:

            stats = cache_response.json()

            st.metric(
                "Cached Answers",
                stats["cache_count"]
            )

    except:
        st.warning("Cache stats unavailable")

# ── Load Chat History ─────────────────────────

try:

    history_response = requests.get(
        f"{BACKEND_URL}/history/"
        f"{st.session_state.session_id}"
    )

    if history_response.ok:

        history = history_response.json()[
            "messages"
        ]

        for msg in history:

            with st.chat_message(msg["role"]):

                st.write(msg["content"])

except Exception as e:

    st.error(
        "Failed to load history."
    )

# ── Chat Input ────────────────────────────────

question = st.chat_input(
    "Ask a legal question..."
)

if question:

    # show user message immediately
    with st.chat_message("user"):
        st.write(question)

    try:

        with st.spinner(
            "Searching Constitution..."
        ):

            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "question": question,
                    "session_id":
                        st.session_state.session_id
                },
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

        # display assistant answer
        with st.chat_message("assistant"):

            st.write(data["answer"])

            if data["cache_hit"]:
                st.caption(
                    "⚡ Answered from semantic cache"
                )

        # show sources
        if data["sources"]:

            with st.expander("📚 Sources"):

                for source in data["sources"]:

                    st.write(
                        f"**Article "
                        f"{source['article']}:** "
                        f"{source['title']}"
                    )

        # rerun to refresh history
        st.rerun()

    except requests.exceptions.ConnectionError:

        st.error(
            "Backend server is not running."
        )

    except requests.exceptions.Timeout:

        st.error(
            "Request timed out."
        )

    except Exception as e:

        st.error(f"Error: {str(e)}")