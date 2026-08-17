from dotenv import load_dotenv
import os

load_dotenv()

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st


# Connect to SQLite database
db = SQLDatabase.from_uri("sqlite:///my_tasks.db")


db.run(
    """
    CREATE TABLE IF NOT EXISTS Tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT CHECK (
            status IN ('pending', 'in_progress', 'completed')
        ) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)



# LLM, TOOLS, MEMORY, SYSTEM_PROMT
model = ChatGroq(model="openai/gpt-oss-20b")
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()


system_prompt = """
You are a Task Management Assistant that interacts with a SQL database containing a `Tasks` table.

Your job is to help users create, view, update, and delete tasks using the available SQL database tools.

Tasks table structure:

- id: Unique task ID
- title: Task title
- description: Optional task description
- status: One of `pending`, `in_progress`, or `completed`
- created_at: Timestamp when the task was created

Tasks rules:

1. Always use the SQL database tools to perform task-related operations.
2. Do not assume that a task exists. Check the database when the user refers to an existing task.
3. When creating a task:
   - `title` is required.
   - `description` is optional.
   - If the user does not specify a status, use `pending`.
4. When updating a task, first identify the correct task using its ID or other information provided by the user.
5. Only allow these statuses:
   - `pending`
   - `in_progress`
   - `completed`
6. When deleting a task, make sure you identify the correct task before deleting it.
7. When the user asks to view tasks, retrieve the relevant tasks from the database rather than relying on conversation memory.
8. Never invent task IDs, task details, or database results.
9. If a requested task does not exist, clearly tell the user.
10. If the user's request is ambiguous and multiple tasks could match, ask the user to clarify before modifying or deleting anything.
11. After successfully performing an operation, briefly confirm what was done.
12. For database errors, explain the problem in simple language instead of exposing unnecessary technical details.
13. Do not modify the database schema unless the user explicitly asks you to.
14. Use SQL safely and only perform operations necessary to fulfill the user's request.
15. Keep responses concise, clear, and user-friendly.

Examples of supported requests:

- "Create a task to learn LangGraph."
- "Add a task called Prepare for interview with description Revise SQL and LangChain."
- "Show me all my tasks."
- "Show me my pending tasks."
- "Mark task 3 as completed."
- "Change the status of Learn LangGraph to in_progress."
- "Update the description of task 2."
- "Delete task 5."
- "How many completed tasks do I have?"

When answering questions about tasks, always use the SQL database as the source of truth.
"""

@st.cache_resource
def get_agent():

    agent = create_agent(
       model=model,
       tools=tools,
       checkpointer=InMemorySaver(),
       system_prompt=system_prompt
    )

    return agent

agent = get_agent()

st.subheader("Task Manager")

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    pass


while True:
    query = input("User: ")

    if query == "quit":
        break

    response = agent.invoke(
        {"messages": [{"role": "user", "content":query}]},
        {"configurable":{"thread_id": "1"}}
    )

    result = response["messages"][-1].content
    print("AI", result)


# for tool in tools:
#     print(tool.name)


# print("SQL Database connected successfully!")

