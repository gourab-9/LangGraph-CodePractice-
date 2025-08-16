# langgraph_backend.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

# Initialize LLM
llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

# Define state structure
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Chat node: calls LLM and appends AIMessage to state
def chat_node(state: ChatState):
    messages = state['messages']
    llm_reply = llm.invoke(messages)  # This is already an AIMessage
    return {"messages": [llm_reply]}  # Append bot reply

# Memory checkpointer
checkpointer = InMemorySaver()

# Build graph
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# Compile chatbot
chatbot = graph.compile(checkpointer=checkpointer)
