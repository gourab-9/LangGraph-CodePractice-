# frontend.py
import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import re

# ==============================
# Title Generation
# ==============================
def format_thread_name(text):
    clean_text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    words = clean_text.split()

    if len(words) > 3:
        keywords = ["about", "on", "regarding"]
        for kw in keywords:
            if kw in [w.lower() for w in words]:
                idx = [w.lower() for w in words].index(kw)
                topic_words = words[idx + 1:]
                if topic_words:
                    topic = " ".join(topic_words).title()
                    return f"Discussion About {topic}"
    topic = " ".join(words[-3:]).title()
    return f"Discussion About {topic}"

def get_title_from_llm(first_message):
    prompt = (
        f"Generate a short, clear, and descriptive title for a conversation "
        f"based on this user request. Keep it under 6 words, avoid punctuation, "
        f"and make it sound like a topic:\n\nUser: {first_message}\n\nTitle:"
    )
    try:
        response = chatbot.invoke({"messages": [HumanMessage(content=prompt)]})
        title = response.content.strip()
        if not title or len(title) > 60:
            return format_thread_name(first_message)
        return f"Discussion About {title.title()}"
    except Exception:
        return format_thread_name(first_message)

# ==============================
# Session State Setup
# ==============================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

# ==============================
# Sidebar
# ==============================
st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    st.session_state["thread_id"] = None
    st.session_state["message_history"] = []

st.sidebar.header("My Conversations")
for thread_id in st.session_state["chat_threads"][::-1]:
    if st.sidebar.button(thread_id):
        st.session_state["thread_id"] = thread_id
        messages = chatbot.get_state(config={"configurable": {"thread_id": thread_id}}).values["messages"]
        temp_messages = []
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            temp_messages.append({"role": role, "content": msg.content})
        st.session_state["message_history"] = temp_messages

# ==============================
# Chat Display
# ==============================
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])  # Markdown prevents word-by-word issue

user_input = st.chat_input("Type your message here...")
if user_input:
    if st.session_state["thread_id"] is None:
        st.session_state["thread_id"] = get_title_from_llm(user_input)
        if st.session_state["thread_id"] not in st.session_state["chat_threads"]:
            st.session_state["chat_threads"].append(st.session_state["thread_id"])

    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}

    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            chunk.content for chunk, _ in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            )
        )

    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
