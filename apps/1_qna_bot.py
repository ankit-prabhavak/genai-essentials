from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
import streamlit as st

load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-oss-20b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


st.title("Q&A Bot")

st.markdown("I am a Q&A bot powered by the openai/gpt-oss-20b:free model.")


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    st.chat_message(role).write(content)

query = st.chat_input("Ask me anything...")

if query:
  st.session_state.messages.append({"role": "user", "content": query})
  st.chat_message("user").write(query)
  
  prompts = [
      {"role": "system", "content": "you are a helpful assistant"},
      {"role": "user", "content": query},
  ]
  
  res = llm.invoke(prompts)
  st.session_state.messages.append({"role": "assistant", "content": res.content})
  st.chat_message("assistant").write(res.content)
  