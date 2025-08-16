import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage

CONFIG = {'configurable': {'thread_id': 'thread-1'}}

# Initialize message history in session
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Display existing conversation
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])  

# User input
user_input = st.chat_input("ASK ME")

if user_input:
    # Store and display the user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    # Send latest user message to chatbot
    response = chatbot.invoke(
        {'messages': [HumanMessage(content=user_input)]},
        config=CONFIG
    )

    # Handle different response types
    if isinstance(response, str):
        ai_message = response
    elif hasattr(response, 'content'):  
        ai_message = response.content
    elif isinstance(response, dict) and 'messages' in response:
        # Take the last message from the response
        last_msg = response['messages'][-1]
        ai_message = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
    else:
        ai_message = str(response)

    # Store and display the AI message
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
    with st.chat_message("assistant"):
        st.markdown(ai_message)
