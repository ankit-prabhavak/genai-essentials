from dotenv import load_dotenv
import os

from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_agent

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

search = GoogleSerperAPIWrapper()


@tool
def google_search(query: str):
    """Search Google for information and return the search results.
       
       Args:
           query : A string having the user query
    """
    return search.run(query)


agent = create_agent(
    model=llm,
    tools=[google_search],
    system_prompt="You are an agent that can search Google to answer questions. When you need current information, call the google_search tool with a concise query."
)


while True:
    query = input("\nUser: ")
    if query.lower() == "quit":
        print("Good Bye")
        break
    try:
        res = agent.invoke({"messages": [{"role": "user", "content": query}]})
        print("\nHere is your search result:\n")
        print(res["messages"][-1].content)
    except Exception as e:
        print(f"\n[Error: could not get a response — {e}]\n")


