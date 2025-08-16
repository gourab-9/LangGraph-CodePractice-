import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage

# Fixed thread ID
THREAD_ID = "thread-1"
CONFIG = {"configurable": {"thread_id": THREAD_ID}}

# Load past conversation from LangGraph memory (once per session)
if "message_history" not in st.session_state:
    try:
        messages = chatbot.get_state(config=CONFIG).values.get("messages", [])
        st.session_state["message_history"] = [
            {"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content}
            for msg in messages
        ]
    except Exception:
        st.session_state["message_history"] = []

# Display existing conversation
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

# User input
user_input = st.chat_input("Type here")

if user_input:
    # Store and display user message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    # Stream AI response and save it
    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            )
        )

    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
