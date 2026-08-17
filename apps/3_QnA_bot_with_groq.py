"""
Google Search Agent using:
- LangGraph
- LangChain
- Groq
- Google Serper
- Streamlit
- MemorySaver

Architecture:

User
  ↓
Streamlit UI
  ↓
LangGraph Agent
  ↓
Groq LLM
  ↓
Google Search Tool (when required)
  ↓
Final Answer
  ↓
Streamlit UI

Features:
- Google Search
- Groq LLM
- LangGraph Agent
- Conversation Memory
- Streaming Responses
- Streamlit Web Interface
"""

# 1. IMPORTS

import os

import streamlit as st
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver

# 2. LOAD ENVIRONMENT VARIABLES
load_dotenv()

# 3. CONFIGURATION
MODEL_NAME = "llama-3.3-70b-versatile"
THREAD_ID = "google-search-agent-thread"


# 4. CREATE LLM
def create_llm():
    """
    Create and return the Groq LLM.
    """

    return ChatGroq(
        model=MODEL_NAME,
        streaming=True,
        temperature=0
    )


# 5. CREATE GOOGLE SEARCH TOOL
def create_google_search_tool():
    """
    Create a Google Search tool using Google Serper API.
    """

    search = GoogleSerperAPIWrapper()

    @tool
    def google_search(query: str) -> str:
        """
        Search Google for current or up-to-date information.

        Use this tool when the user asks about:
        - Current events
        - Recent information
        - News
        - Live information
        - Information that may have changed recently
        """

        return search.run(query)

    return google_search


# 6. CREATE AGENT
def create_search_agent(memory):
    """
    Create the LangGraph agent.
    """

    llm = create_llm()
    google_search = create_google_search_tool()

    agent = create_agent(
        model=llm,
        tools=[google_search],
        system_prompt=(
            "You are a helpful AI search agent. "
            "You can use the google_search tool to find current "
            "and up-to-date information. "
            "Use Google Search whenever the question requires "
            "current, recent, or externally verifiable information. "
            "For general knowledge questions, answer directly. "
            "Give clear, accurate, and concise answers."
        ),
        checkpointer=memory
    )

    return agent

# 7. INITIALIZE STREAMLIT SESSION STATE
def initialize_session_state():
    """
    Initialize variables stored in Streamlit session state.
    """

    if "memory_saver" not in st.session_state:
        st.session_state.memory_saver = MemorySaver()

    if "history" not in st.session_state:
        st.session_state.history = []

    if "agent" not in st.session_state:
        st.session_state.agent = create_search_agent(
            st.session_state.memory_saver
        )

# 8. STREAM AGENT RESPONSE
def get_agent_response(agent, query):
    """
    Send the user's query to the LangGraph agent
    and stream the response.
    """

    response = agent.stream(
        {
            "messages": [
                HumanMessage(content=query)
            ]
        },
        {
            "configurable": {
                "thread_id": THREAD_ID
            }
        },
        stream_mode="messages"
    )

    return response


# 9. STREAMLIT PAGE CONFIGURATION
st.set_page_config(
    page_title="Google Search Agent",
    page_icon="🔎",
    layout="centered"
)

# 10. INITIALIZE APPLICATION
initialize_session_state()


# 11. STREAMLIT USER INTERFACE
st.title("🔎 Google Search Agent")

st.subheader(
    "Ask a question and the AI agent can search Google "
    "when current information is required."
)


# 12. DISPLAY CHAT HISTORY
for message in st.session_state.history:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# 13. USER INPUT
query = st.chat_input("Ask me anything...")


# 14. PROCESS USER QUERY
if query:

    # Display user message

    with st.chat_message("user"):
        st.markdown(query)

    # Save user message
    st.session_state.history.append(
        {
            "role": "user",
            "content": query
        }
    )

    # Generate AI response
    try:

        with st.chat_message("assistant"):

            response_container = st.empty()

            full_response = ""

            response_stream = get_agent_response(
                st.session_state.agent,
                query
            )

        
            # Stream response token by token
            for chunk, metadata in response_stream:

                # Make sure the chunk contains text
                if hasattr(chunk, "content"):

                    content = chunk.content

                    if content:

                        full_response += content

                        response_container.markdown(
                            full_response
                        )

            # Save assistant response
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "content": full_response
                }
            )

    except Exception as e:
        st.error(
            f"Error: Could not get a response.\n\n{e}"
        )


