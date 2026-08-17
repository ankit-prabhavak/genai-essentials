"""
Taskline — Flask backend
=========================
This app wraps a LangGraph SQL agent (Groq-hosted LLM + a SQLite database
of tasks) behind a small JSON API, and serves a chat UI that supports both
typed and spoken (voice) input.

How the pieces fit together
----------------------------
1. SQLite database (`my_tasks.db`) stores the Tasks table.
2. `ChatGroq` is the LLM that powers the agent (fast Groq LPU inference).
3. `SQLDatabaseToolkit` gives the agent SQL tools (list tables, run a
   query, describe schema, etc).
4. `create_agent` builds a LangGraph agent that decides when to call
   those tools based on the system prompt below.
5. `InMemorySaver` gives the agent short-term memory *per conversation*,
   keyed by a `thread_id`. We hand out one thread_id per browser
   (stored in a signed Flask session cookie) so different visitors don't
   see each other's conversation history.
6. Flask exposes a tiny JSON API (`/api/chat`, `/api/reset`) that the
   front-end (templates/index.html + static/js/app.js) talks to.

Voice input/output is handled entirely in the browser via the Web Speech
API (SpeechRecognition + speechSynthesis) — no extra server-side audio
pipeline or API key is needed for that part. See static/js/app.js.
"""

import os
import uuid

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.checkpoint.memory import InMemorySaver

# ---------------------------------------------------------------------------
# 1. Environment & Flask app setup
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)

# Signs the session cookie that stores each visitor's conversation thread
# id. Falls back to a random value so the app still runs if you forget to
# set one, but that means sessions (and the "who am I talking to" link)
# won't survive a server restart — set FLASK_SECRET_KEY in .env for
# anything beyond local testing.
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# ---------------------------------------------------------------------------
# 2. Database setup — create the Tasks table if it doesn't exist yet
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("TASKS_DB_PATH", "my_tasks.db")
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

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

# ---------------------------------------------------------------------------
# 3. LLM + tools + agent — built once at startup and reused for every request
# ---------------------------------------------------------------------------
# openai/gpt-oss-20b is Groq's recommended replacement for the retired
# llama-3.1-8b-instant model, and is available on the free tier as of
# mid-2026. Groq's lineup shifts every couple of months — if you start
# seeing "model_not_found" errors again, check console.groq.com/docs/models
# and update GROQ_MODEL in your .env rather than editing this file.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# temperature=0 keeps the agent's SQL-writing behaviour predictable —
# you want deterministic query generation, not creative variation, when
# it's touching a real database.
model = ChatGroq(model=GROQ_MODEL, temperature=0)

toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

SYSTEM_PROMPT = """
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
15. Keep responses concise, clear, and user-friendly. This chat is read aloud by
    text-to-speech sometimes, so prefer short plain sentences over bullet lists
    or markdown tables when summarising results.

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

# InMemorySaver gives the agent a "scratchpad" per thread_id so it
# remembers earlier turns in *this* conversation. It resets whenever the
# server process restarts. If you need conversations to survive restarts,
# swap this for a persistent checkpointer (e.g. langgraph's SqliteSaver)
# without changing anything else below.
checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer,
    system_prompt=SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# 4. Helpers
# ---------------------------------------------------------------------------
def get_thread_id() -> str:
    """
    Return this browser's LangGraph thread id, creating one the first
    time a visitor shows up. Storing it in the signed Flask session
    cookie means every browser gets its own private conversation history
    with zero login system required.
    """
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
    return session["thread_id"]


def friendly_error(exc: Exception) -> str:
    """
    Translate common failure modes into plain language the chat UI can
    show directly to the user, instead of a raw stack trace. Full detail
    still goes to the server log via app.logger.exception in the caller.
    """
    text = str(exc).lower()
    if "model_not_found" in text or "does not exist" in text:
        return (
            "The configured Groq model isn't available anymore. Check "
            "GROQ_MODEL in your .env against console.groq.com/docs/models."
        )
    if "rate_limit" in text or "429" in text:
        return "Groq's rate limit was hit — wait a few seconds and try again."
    if "api_key" in text or "authentication" in text or "401" in text:
        return "Groq API key missing or invalid — check GROQ_API_KEY in your .env."
    return "Something went wrong talking to the assistant. Please try again."


# ---------------------------------------------------------------------------
# 5. Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the chat UI shell. Everything after this is JSON + JS."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.

    Request body:  {"message": "show me all my tasks"}
    Success reply: {"reply": "..."}
    Error reply:   {"error": "..."}  (still valid JSON, non-500 status)
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message can't be empty."}), 400

    thread_id = get_thread_id()

    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            {"configurable": {"thread_id": thread_id}},
        )
        reply = response["messages"][-1].content
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all at the API boundary
        app.logger.exception("Agent call failed")
        return jsonify({"error": friendly_error(exc)}), 502

    return jsonify({"reply": reply})


@app.route("/api/reset", methods=["POST"])
def reset():
    """
    Start a fresh conversation. We simply hand the browser a brand new
    thread_id — the old conversation's history stays in the checkpointer
    but is no longer referenced by anyone, so it's effectively forgotten.
    """
    session["thread_id"] = str(uuid.uuid4())
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # debug=True auto-reloads on code changes and shows tracebacks in the
    # browser — turn it off (or use a real WSGI server) in production.
    app.run(debug=True, port=5000)
