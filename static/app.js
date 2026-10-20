const form = document.getElementById("form");
const input = document.getElementById("message");
const chat = document.getElementById("chat");
const sendButton = form.querySelector('button[type="submit"]');

function addBubble(label, text, className, hintType = "") {
  const item = document.createElement("div");
  item.className = "bubble " + className;
  const title = document.createElement("strong");
  title.textContent = label;
  const body = document.createElement("div");
  body.className = "bubble-text";
  body.textContent = text;
  item.append(title, body);
  if (hintType) {
    const tag = document.createElement("span");
    tag.className = "hint-type";
    tag.textContent = hintType;
    item.appendChild(tag);
  }
  chat.appendChild(item);
  chat.scrollTop = chat.scrollHeight;
  return item;
}

document.getElementById("new-question").addEventListener("click", async () => {
  try {
    const response = await fetch("/reset", { method: "POST" });
    if (!response.ok) throw new Error("Reset request failed");
    chat.replaceChildren();
    addBubble("HintOS", "Ready for a new OS question. What would you like to work on?", "tutor");
    input.focus();
  } catch (error) {
    addBubble("HintOS", "Could not start a new question. Please try again.", "tutor");
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || sendButton.disabled) return;
  addBubble("You", text, "student");
  input.value = "";
  sendButton.disabled = true;
  sendButton.textContent = "Thinking...";
  const waiting = addBubble("HintOS", "One moment...", "tutor waiting");
  const slowNotice = window.setTimeout(() => {
    waiting.querySelector(".bubble-text").textContent =
      "Still working on this locally. The first reply can take longer while the model warms up.";
  }, 7000);
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HintOS returned an error (${response.status}).`);
    }
    const result = await response.json();
    waiting.remove();
    let replyLabel = result.hint_type || "";
    if (result.status === "correct") replyLabel = "Correct";
    if (result.status === "incorrect") replyLabel = "Check this step";
    addBubble("HintOS", result.message, "tutor", replyLabel);
    loadHistory();
  } catch (error) {
    waiting.remove();
    const message = error instanceof TypeError
      ? "Could not reach HintOS. Check that the server window is still running, then try again."
      : error.message || "HintOS could not complete that reply. Please try again.";
    addBubble("HintOS", message, "tutor");
  } finally {
    window.clearTimeout(slowNotice);
    sendButton.disabled = false;
    sendButton.textContent = "Send";
    input.focus();
  }
});

async function loadHistory() {
  try {
    const response = await fetch("/history");
    if (!response.ok) return;
    const data = await response.json();
    const history = document.getElementById("history");
    history.replaceChildren();
    data.attempts.forEach((item) => {
      const row = document.createElement("div");
      row.className = "history-row";
      row.textContent = `${item.created_at} - ${item.hint_type}: ${item.hint}`;
      history.appendChild(row);
    });
    document.getElementById("history-empty").hidden = data.attempts.length > 0;
  } catch (error) {
    // History is optional; the chat can still be used if it is unavailable.
  }
}

loadHistory();
loadConversation();

async function loadConversation() {
  try {
    const response = await fetch("/conversation");
    if (!response.ok) return;
    const data = await response.json();
    if (!Array.isArray(data.turns) || !data.turns.length) return;
    chat.replaceChildren();
    data.turns.forEach((turn) => {
      if (turn.role === "user") addBubble("You", turn.text, "student");
      else addBubble("HintOS", turn.text, "tutor");
    });
  } catch (error) {
    // The server's conversational context still works if transcript restore fails.
  }
}

async function loadStatus() {
  const status = document.getElementById("ai-status");
  try {
    const response = await fetch("/status");
    const data = await response.json();
    status.textContent = data.ready
      ? `${data.message} Model: ${data.model}.`
      : `${data.message} The numeric checker still works; install the local model for full conversation.`;
    status.classList.toggle("ready", data.ready);
  } catch (error) {
    status.textContent = "Could not check the local AI status.";
  }
}

loadStatus();
