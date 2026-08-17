/**
 * Taskline — front-end
 * =====================
 * Talks to the Flask JSON API (/api/chat, /api/reset) and builds the
 * message-row markup that static/css/style.css styles. Voice is handled
 * entirely client-side:
 *
 *  - Voice input:  Web Speech API's SpeechRecognition turns speech into
 *                   text, sent through the normal chat flow. This streams
 *                   audio to the browser vendor's speech service (e.g.
 *                   Google's, in Chrome) — it needs real internet access
 *                   even though the app itself runs on localhost, which is
 *                   the #1 cause of the "network" error handled below.
 *  - Voice output: window.speechSynthesis reads assistant replies aloud
 *                   when the speaker toggle is on.
 */

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------
const chatLog = document.getElementById("chatLog");
const welcomeState = document.getElementById("welcomeState");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const speakToggle = document.getElementById("speakToggle");
const resetBtn = document.getElementById("resetBtn");
const composerHint = document.getElementById("composerHint");
const statusDot = document.getElementById("statusDot");

const DEFAULT_HINT = composerHint.textContent.trim();
let speakEnabled = false;

// Fill in the initial assistant message's timestamp (left static in the HTML).
document.querySelectorAll(".msg-time").forEach((el) => {
  if (!el.textContent.trim()) el.textContent = timeLabel();
});

// ---------------------------------------------------------------------------
// Rendering helpers
// ---------------------------------------------------------------------------

function timeLabel() {
  return new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/** Wrap task-status words in a colored pill span, purely cosmetic. */
function highlightStatuses(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(/\b(pending|in_progress|completed)\b/gi, (match) => {
    const key = match.toLowerCase();
    return `<span class="status-badge status-${key}">${match}</span>`;
  });
}

/** The welcome screen is only for a brand-new conversation. */
function hideWelcome() {
  welcomeState?.classList.add("is-hidden");
  if (welcomeState) welcomeState.style.display = "none";
}
function showWelcome() {
  if (welcomeState) welcomeState.style.display = "";
}

/** Build one assistant or user message row and append it to the log. */
function addMessage(role, text, { isError = false } = {}) {
  const row = document.createElement("div");
  row.className = `message-row ${role === "user" ? "user-row" : "assistant-row"}`;

  if (role === "assistant") {
    row.innerHTML = `
      <div class="avatar assistant-avatar"><span class="avatar-dot"></span></div>
      <div class="message-content">
        <div class="message-meta"><strong>Taskline</strong><span class="msg-time">${timeLabel()}</span></div>
        <div class="message-bubble ${isError ? "error-text" : ""}">
          <p>${highlightStatuses(text)}</p>
        </div>
      </div>`;
  } else {
    row.innerHTML = `
      <div class="message-content">
        <div class="message-bubble"><p>${escapeHtml(text)}</p></div>
        <span class="msg-time">${timeLabel()}</span>
      </div>`;
  }

  chatLog.appendChild(row);
  chatLog.scrollTop = chatLog.scrollHeight;
  return row;
}

function setTyping(isTyping) {
  const existing = document.getElementById("typingIndicator");
  if (existing) existing.remove();
  if (!isTyping) return;

  const row = document.createElement("div");
  row.className = "message-row assistant-row typing";
  row.id = "typingIndicator";
  row.innerHTML = `
    <div class="avatar assistant-avatar"><span class="avatar-dot"></span></div>
    <div class="message-content">
      <div class="message-bubble">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
    </div>`;
  chatLog.appendChild(row);
  chatLog.scrollTop = chatLog.scrollHeight;
}

/** Temporarily show a status line under the composer, then restore the default hint. */
function showHint(text, ms = 4000) {
  composerHint.textContent = text;
  if (ms) {
    clearTimeout(showHint._t);
    showHint._t = setTimeout(() => { composerHint.textContent = DEFAULT_HINT; }, ms);
  }
}

function flashStatus(ok) {
  statusDot.style.background = ok ? "var(--teal-bright)" : "var(--coral)";
}

// ---------------------------------------------------------------------------
// Sending messages
// ---------------------------------------------------------------------------
async function sendMessage(text) {
  const trimmed = text.trim();
  if (!trimmed) return;

  hideWelcome();
  addMessage("user", trimmed);
  messageInput.value = "";
  autoResize();
  setFormEnabled(false);
  setTyping(true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed }),
    });
    const data = await res.json();
    setTyping(false);

    if (!res.ok) {
      addMessage("assistant", data.error || "Something went wrong.", { isError: true });
      flashStatus(false);
      return;
    }

    addMessage("assistant", data.reply);
    flashStatus(true);
    if (speakEnabled) speak(data.reply);
  } catch (err) {
    setTyping(false);
    addMessage("assistant", "Couldn't reach the server — check your connection and try again.", {
      isError: true,
    });
    flashStatus(false);
  } finally {
    setFormEnabled(true);
    messageInput.focus();
  }
}

function setFormEnabled(enabled) {
  messageInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(messageInput.value);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(messageInput.value);
  }
});

function autoResize() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${messageInput.scrollHeight}px`;
}
messageInput.addEventListener("input", autoResize);

// ---------------------------------------------------------------------------
// Quick prompts (welcome screen + sidebar shortcuts) — fill and focus,
// let the person confirm by pressing Enter/Send rather than auto-sending.
// ---------------------------------------------------------------------------
document.querySelectorAll("[data-prompt]").forEach((el) => {
  el.addEventListener("click", () => {
    messageInput.value = el.dataset.prompt;
    autoResize();
    messageInput.focus();
  });
});

// ---------------------------------------------------------------------------
// Reset conversation
// ---------------------------------------------------------------------------
resetBtn.addEventListener("click", async () => {
  await fetch("/api/reset", { method: "POST" });

  // Remove every message row except none — welcome screen comes back and
  // owns the "empty state", so we just clear all rows and show it again.
  chatLog.querySelectorAll(".message-row").forEach((row) => row.remove());
  showWelcome();
  messageInput.focus();
});

// ---------------------------------------------------------------------------
// Voice input — SpeechRecognition
// ---------------------------------------------------------------------------
const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
let isRecording = false;

const RECOGNITION_ERROR_MESSAGES = {
  "network":
    "Voice recognition needs an internet connection (it transcribes via your browser's speech service, not this app). Check your connection, disable any ad-blocker/VPN that might block it, and try again.",
  "not-allowed":
    "Microphone access was blocked — check your browser's site permissions and allow the mic for this page.",
  "service-not-allowed":
    "Voice recognition was blocked by the browser or an extension. Try again or type your message instead.",
  "no-speech":
    "Didn't catch that — try again and speak right after the mic turns red.",
  "audio-capture":
    "No microphone was found. Check that one is connected and not in use by another app.",
  "aborted": "",
};

if (SpeechRecognitionImpl) {
  recognizer = new SpeechRecognitionImpl();
  recognizer.lang = "en-US";
  recognizer.continuous = false;
  recognizer.interimResults = true;

  recognizer.onstart = () => {
    isRecording = true;
    micBtn.setAttribute("aria-pressed", "true");
    showHint("Listening…", 0);
  };

  recognizer.onresult = (event) => {
    let transcript = "";
    let isFinal = false;
    for (const result of event.results) {
      transcript += result[0].transcript;
      if (result.isFinal) isFinal = true;
    }
    messageInput.value = transcript;
    autoResize();
    if (isFinal) sendMessage(transcript);
  };

  recognizer.onerror = (event) => {
    const message = RECOGNITION_ERROR_MESSAGES[event.error] ?? `Voice input error: ${event.error}`;
    if (message) showHint(message, 6000);
  };

  recognizer.onend = () => {
    isRecording = false;
    micBtn.setAttribute("aria-pressed", "false");
    if (composerHint.textContent === "Listening…") composerHint.textContent = DEFAULT_HINT;
  };

  micBtn.addEventListener("click", () => {
    if (isRecording) {
      recognizer.stop();
    } else {
      messageInput.value = "";
      try {
        recognizer.start();
      } catch (err) {
        // start() throws if called while already active — safe to ignore.
      }
    }
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input isn't supported in this browser";
}

// ---------------------------------------------------------------------------
// Voice output — speechSynthesis
// ---------------------------------------------------------------------------
function speak(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.02;
  window.speechSynthesis.speak(utterance);
}

speakToggle.addEventListener("click", () => {
  speakEnabled = !speakEnabled;
  speakToggle.setAttribute("aria-pressed", String(speakEnabled));
  if (!speakEnabled) window.speechSynthesis?.cancel();
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
messageInput.focus();
