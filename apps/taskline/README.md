# Taskline

A voice-and-text chat UI for a LangGraph SQL agent that manages a `Tasks`
table over SQLite, served with Flask (no Streamlit).

## What you get

- **Clean chat UI** — ticket-stub styled assistant replies, auto-highlighted
  task-status badges (`pending` / `in_progress` / `completed`), typing
  indicator, auto-resizing input, dark theme.
- **Voice input** — press the mic, speak, and your words are transcribed
  and sent automatically (uses the browser's built-in `SpeechRecognition`,
  no extra API key or server-side audio pipeline needed).
- **Voice output** — toggle the speaker icon to have replies read aloud
  with `speechSynthesis`.
- **Per-browser memory** — each visitor gets their own private conversation
  thread via a signed session cookie, so multiple people can use the same
  server without seeing each other's chat history.
- **Friendly error handling** — Groq rate limits, bad API keys, and
  decommissioned models surface as plain-language messages instead of
  stack traces.

## Setup

```bash
python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # then edit .env and add your GROQ_API_KEY
python app.py
```

Open [http://localhost:5000].

## Project layout

```text
taskline/
├── app.py                  # Flask app: routes, agent setup, DB init
├── requirements.txt
├── .env.example
├── templates/
│   └── index.html          # Chat UI shell
└── static/
    ├── css/style.css       # Design system (dark ink + parchment ticket bubbles)
    └── js/app.js           # Chat logic, SpeechRecognition, speechSynthesis
```

## Notes & known limitations

- **Voice input browser support**: `SpeechRecognition` works well in Chrome
  and Edge, partially in Safari, and isn't available in Firefox as of 2026.
  The mic button disables itself automatically where it's unsupported.
- **Conversation memory vs. chat log**: the agent's memory
  (`InMemorySaver`) lives on the server and persists for as long as the
  process runs, keyed to your session cookie's `thread_id`. If you refresh
  the page, the *visible* chat log resets, but the agent still remembers
  earlier turns from that cookie. Click **New conversation** to actually
  start over on both ends.
- **If Groq deprecates the model again**: just change `GROQ_MODEL` in
  `.env` — nothing else needs to change. Check
  `console.groq.com/docs/models` for what's currently free-tier.
- **Scaling beyond a demo**: `InMemorySaver` and the dev server
  (`app.run(debug=True)`) are fine for local use but not production. For
  real deployment: run behind `gunicorn`/`waitress`, and swap
  `InMemorySaver` for a persistent LangGraph checkpointer (e.g. one backed
  by SQLite or Postgres) so history survives restarts.
