import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage
import re

# **************************************** utility functions *************************

def format_thread_name(text):
    """Fallback: extract main topic from user message."""
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    words = clean_text.split()
    if len(words) > 3:
        # Look for keywords like 'about', 'on', 'regarding'
        keywords = ["about", "on", "regarding"]
        for kw in keywords:
            if kw in [w.lower() for w in words]:
                idx = [w.lower() for w in words].index(kw)
                topic_words = words[idx + 1:]
                if topic_words:
                    topic = " ".join(topic_words).title()
                    return f"Discussion About {topic}"

    # Fallback: use last 3 words as topic
    topic = " ".join(words[-3:]).title()
    return f"Discussion About {topic}"

def get_title_from_llm(first_message):
    """Ask LLM to generate a short title from the first message."""
    prompt = (
        f"Generate a short, clear, and descriptive title for a conversation "
        f"based on this user request. Keep it under 6 words, avoid punctuation, "
        f"and make it sound like a topic:\n\n"
        f"User: {first_message}\n\n"
        f"Title:"
    )
    try:
        response = chatbot.invoke({"messages": [HumanMessage(content=prompt)]})
        title = response.content.strip()

        # Validate title
        if not title or len(title) > 60:
            return format_thread_name(first_message)
        return f"Discussion About {title.title()}"
    except Exception:
        return format_thread_name(first_message)

def reset_chat():
    st.session_state['thread_id'] = None
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']


# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = None

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []


# **************************************** Sidebar UI *********************************
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread_id):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************
# Display previous messages
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    # If it's the first message, get title from LLM (with fallback)
    if st.session_state['thread_id'] is None:
        st.session_state['thread_id'] = get_title_from_llm(user_input)
        add_thread(st.session_state['thread_id'])

    # Add user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Get assistant's response
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
