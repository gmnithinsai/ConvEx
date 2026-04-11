// ─────────────────────────────────────────────────────────────
// CONFIG + STATE
// ─────────────────────────────────────────────────────────────

const state = {
  userId: "web_user",
  sessionId: `web_session_${Date.now()}`,
  currentQuestion: "",
  personas: [],
  selectedPersona: null,
  isRunning: false,
  runAbortController: null,
  config: {}
};

// ─────────────────────────────────────────────────────────────
// DOM REFS
// ─────────────────────────────────────────────────────────────

const messagesEl      = document.getElementById("messages");
const formEl          = document.getElementById("chat-form");
const messageInputEl  = document.getElementById("message-input");
const intentSelectEl  = document.getElementById("intent-select");
const personaListEl   = document.getElementById("persona-list");
const personaSubmitEl = document.getElementById("persona-submit");
const activePersonaEl = document.getElementById("active-persona");
const sessionIdEl     = document.getElementById("session-id");
const autoLoopEl      = document.getElementById("auto-loop");
const stopBtn         = document.getElementById("stop-btn");

// ─────────────────────────────────────────────────────────────
// LOGGER
// ─────────────────────────────────────────────────────────────

function log(...args) {
  if (state.config.DEBUG) console.log(...args);
}

function errorMessage(err) {
  if (!err) return "Unknown error";
  if (typeof err === "string") return err;
  if (typeof err === "number" || typeof err === "boolean") return String(err);
  if (err instanceof Error) return err.message || err.name || "Error";
  if (typeof err === "object") {
    if (typeof err.detail === "string") return err.detail;
    if (typeof err.message === "string") return err.message;
    try {
      return JSON.stringify(err);
    } catch {
      return "Unknown error";
    }
  }
  return "Unknown error";
}

// ─────────────────────────────────────────────────────────────
// CONFIG LOADER
// ─────────────────────────────────────────────────────────────

async function loadConfig() {
  const candidates = ["config.json", "/config.json", "/frontend/config.json"];
  let lastErr = null;

  for (const url of candidates) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        lastErr = new Error(`HTTP ${res.status} when loading ${url}`);
        continue;
      }

      state.config = await res.json();
      state.currentQuestion = state.config.INITIAL_QUESTION;
      return;
    } catch (err) {
      lastErr = err;
    }
  }

  throw new Error(
    `Failed to load config.json (tried: ${candidates.join(", ")}): ${lastErr?.message || "unknown error"}`
  );
}

// ─────────────────────────────────────────────────────────────
// API CLIENT (with timeout)
// ─────────────────────────────────────────────────────────────

async function apiRequest(endpoint, options = {}) {
  const { timeoutMs, ...fetchOptions } = options;

  const resolvedTimeoutMs = Number(timeoutMs ?? state.config.API_TIMEOUT_MS);
  const effectiveTimeoutMs =
    Number.isFinite(resolvedTimeoutMs) && resolvedTimeoutMs > 0
      ? resolvedTimeoutMs
      : 60000;

  const controller = new AbortController();
  if (fetchOptions.signal) {
    if (fetchOptions.signal.aborted) {
      controller.abort(fetchOptions.signal.reason);
    } else {
      fetchOptions.signal.addEventListener(
        "abort",
        () => controller.abort(fetchOptions.signal.reason),
        { once: true }
      );
    }
  }

  const timeout = setTimeout(
    () => controller.abort("timeout"),
    effectiveTimeoutMs
  );

  try {
    const res = await fetch(
      `${state.config.BACKEND_URL}${endpoint}`,
      {
        ...fetchOptions,
        signal: controller.signal
      }
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    if (err.name === "AbortError") {
      if (controller.signal.reason === "timeout") {
        throw new Error(
          `Request timed out (${effectiveTimeoutMs}ms): ${endpoint}`
        );
      }
      throw new Error(`Request cancelled: ${endpoint}`);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

// ─────────────────────────────────────────────────────────────
// UI HELPERS
// ─────────────────────────────────────────────────────────────

sessionIdEl.textContent = state.sessionId;

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendTypingIndicator() {
  removeTypingIndicator();
  const div = document.createElement("div");
  div.className = "bubble agent typing-indicator";
  div.id = "typing-indicator";
  div.innerHTML = `<span></span><span></span><span></span>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeTypingIndicator() {
  document.getElementById("typing-indicator")?.remove();
}

function setRunning(running) {
  state.isRunning = running;
  personaSubmitEl.disabled = running;
  personaSubmitEl.textContent = running ? "Running…" : "Run";
  if (stopBtn) stopBtn.style.display = running ? "inline-block" : "none";
}

// ─────────────────────────────────────────────────────────────
// PERSONA RENDERING
// ─────────────────────────────────────────────────────────────

function renderPersonas(personas) {
  personaListEl.innerHTML = "";

  if (!personas.length) {
    state.selectedPersona = null;
    activePersonaEl.textContent = "None";
    personaListEl.innerHTML = `<p class="hint">No personas available.</p>`;
    return;
  }

  personas.forEach((persona, index) => {
    const wrapper = document.createElement("label");
    wrapper.className = "persona-card";

    wrapper.innerHTML = `
      <input type="radio" name="persona" value="${persona.persona_id}" ${index === 0 ? "checked" : ""} />
      <div>
        <p><strong>Name:</strong> ${persona.name || "-"}</p>
        <p><strong>Email:</strong> ${persona.email || "-"}</p>
        <p><strong>Gender:</strong> ${persona.gender || "-"}</p>
        <p><strong>Nationality:</strong> ${persona.nationality || "-"}</p>
      </div>
    `;

    wrapper.querySelector("input").addEventListener("change", () => {
      state.selectedPersona = persona;
      activePersonaEl.textContent = persona.name;
    });

    personaListEl.appendChild(wrapper);
  });

  state.selectedPersona = personas[0];
  activePersonaEl.textContent = personas[0].name || "None";
}

// ─────────────────────────────────────────────────────────────
// LOAD DATA
// ─────────────────────────────────────────────────────────────

async function loadIntentOptions() {
  const data = await apiRequest("/root-agent/persona-intents");
  const intents = data.intents || [];

  if (!intents.length) throw new Error("No intents returned");

  intentSelectEl.innerHTML = intents
    .map(i => `<option value="${i}">${i}</option>`)
    .join("");

  const def = intents.includes(state.config.DEFAULT_INTENT)
    ? state.config.DEFAULT_INTENT
    : intents[0];

  intentSelectEl.value = def;
  await loadPersonas(def);
}

async function loadPersonas(intentName) {
  const data = await apiRequest(
    `/root-agent/personas?intent_name=${encodeURIComponent(intentName)}`
  );

  state.personas = data.personas || [];
  renderPersonas(state.personas);
}

// ─────────────────────────────────────────────────────────────
// CORE TURN LOGIC
// ─────────────────────────────────────────────────────────────

async function runSingleTurn() {
  if (!state.selectedPersona) {
    appendMessage("agent", "⚠️ Please select a persona first.");
    return false;
  }

  const selectedIntent =
    intentSelectEl.value || state.config.DEFAULT_INTENT;
  const runTimeoutMs =
    Number(state.config.RUN_TIMEOUT_MS) ||
    Number(state.config.API_TIMEOUT_MS) ||
    60000;

  state.runAbortController?.abort("new_run");
  state.runAbortController = new AbortController();

  appendTypingIndicator();

  try {
    const personaData = await apiRequest("/persona-agent/run", {
      timeoutMs: runTimeoutMs,
      signal: state.runAbortController.signal,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.userId,
        session_id: `${state.sessionId}_persona`,
        persona_id: state.selectedPersona.persona_id,
        intent_name: selectedIntent,
        user_question: state.currentQuestion
      })
    });

    removeTypingIndicator();

    const personaReply = (personaData.reply || "").trim();
    if (!personaReply) throw new Error("Empty persona reply");

    appendMessage("user", personaReply);

    appendTypingIndicator();

    const rootData = await apiRequest("/root-agent/run", {
      timeoutMs: runTimeoutMs,
      signal: state.runAbortController.signal,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.userId,
        session_id: state.sessionId,
        customer_message: `[persona:${state.selectedPersona.persona_id}] [intent:${selectedIntent}] ${personaReply}`,
        current_question: state.currentQuestion
      })
    });

    removeTypingIndicator();

    const result = rootData.result || {};
    const nextQuestion =
      typeof result === "object" && result.next_question
        ? result.next_question
        : result;

    state.currentQuestion = nextQuestion;
    appendMessage("agent", nextQuestion);

    return true;
  } catch (err) {
    removeTypingIndicator();
    appendMessage("agent", `⚠️ ${errorMessage(err)}`);
    return false;
  } finally {
    state.runAbortController = null;
  }
}

// ─────────────────────────────────────────────────────────────
// EVENTS
// ─────────────────────────────────────────────────────────────

personaSubmitEl.addEventListener("click", async () => {
  if (state.isRunning) return;

  const autoLoop = autoLoopEl?.checked ?? false;

  setRunning(true);

  if (autoLoop) {
    while (state.isRunning) {
      const ok = await runSingleTurn();
      if (!ok) break;
      await new Promise(r =>
        setTimeout(r, state.config.AUTO_LOOP_DELAY_MS)
      );
    }
  } else {
    await runSingleTurn();
  }

  setRunning(false);
});

stopBtn?.addEventListener("click", () => {
  state.runAbortController?.abort("user_stop");
  setRunning(false);
});

intentSelectEl.addEventListener("change", async () => {
  await loadPersonas(intentSelectEl.value);
});

// ─────────────────────────────────────────────────────────────
// BOOT
// ─────────────────────────────────────────────────────────────

async function startApp() {
  try {
    await loadConfig();
    await loadIntentOptions();
    appendMessage("agent", state.currentQuestion);
  } catch (err) {
    appendMessage("agent", `⚠️ ${errorMessage(err)}`);
    personaSubmitEl.disabled = true;
  }
}

startApp();
