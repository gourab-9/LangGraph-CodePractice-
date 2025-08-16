# backend.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import os

# ==============================
# Config & DB Setup
# ==============================
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

DB_PATH = "chatbot.db"

# Fresh DB each run (optional: remove this line if you want to keep chat history)
# if os.path.exists(DB_PATH):
#     os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ==============================
# LLM Setup
# ==============================
llm = ChatOpenAI(model="gpt-4o-mini",api_key=api_key)

# ==============================
# State Definition
# ==============================
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ==============================
# Node Logic
# ==============================
def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ==============================
# Graph Setup
# ==============================
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# ==============================
# Helper Function
# ==============================
def retrieve_all_threads():
    """Fetch all thread IDs from database."""
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)
