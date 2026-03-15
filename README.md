# dialogue-agent

Conversational multi-agent app (Google ADK + FastAPI) for collecting structured requirements across domains (intents), with a small static frontend and optional persona/evals support.

## Repo Layout

- `src/agents/`: Google ADK agents (intent detection, information extraction, requirements status, next-question selection, etc.).
- `src/api/`: FastAPI app + routes to run agents and inspect session state.
- `src/configs/`: YAML/domain config, requirements per intent, and Jinja2 prompt templates.
- `frontend/`: Static HTML/JS/CSS UI (no build step).
- `evals/`: Persona agent + configs used for evaluations and testing flows.
- `Makefile`: Common dev commands (`backend`, `frontend`, `debug`).

## Prerequisites

- Python 3.13+
- (Recommended) a virtual environment (`.venv`)
- (Optional) `uv` if you prefer `uv sync` installs
- (Optional) Google ADK CLI (`adk`) for `make debug`

## Configuration (.env)

Create a `.env` file (see `.env.example`) and set at least one LLM option.

This repo supports multiple LLM backends via `src/common/llm.py`:

- Ollama / LiteLLM style: set `OLLAMA_MODEL` (example: `ollama_chat/gemma3:latest`)
- Gemini: set `GOOGLE_API_KEY` (and optionally `GOOGLE_MODEL` if enabled in code)
- Generic LiteLLM fallback: set `LLM_MODEL`, `LLM_API_KEY`, and optionally `LLM_API_BASE`

Langfuse is optional but enabled by default in `app.py` (requires `LANGFUSE_*` env vars).

## Install Dependencies

Using `pip`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

Using `uv` (if installed):

```powershell
uv sync
```

## Run

### Backend (FastAPI)

```powershell
make backend
```

This starts the API at `http://localhost:8000`.

- UI (served by FastAPI): `GET /` (serves `frontend/index.html`)
- Health: `GET /health`

### Frontend (Static Server)

If you want to serve the static UI separately:

```powershell
make ui
```

This serves `frontend/` at `http://localhost:5173`.

### ADK Debug UI

```powershell
make debug
```

This runs `adk web src/agents` to browse/run the agents with the ADK web UI.

### CLI Chat (Local)

```powershell
python app.py
```

## API Usage

### Run the root agent

Endpoint: `POST /root-agent/run`

```powershell
curl -X POST http://localhost:8000/root-agent/run `
  -H "Content-Type: application/json" `
  -d '{\"user_id\":\"u1\",\"session_id\":\"s1\",\"customer_message\":\"I need a flight from Delhi to NYC\",\"current_question\":\"Hello\"}'
```

### Inspect session state

Endpoint: `GET /root-agent/session-state?user_id=...&session_id=...`

```powershell
curl "http://localhost:8000/root-agent/session-state?user_id=u1&session_id=s1"
```

### List intents and personas

- `GET /root-agent/intents` (from `src/configs/domain/intents.yaml`)
- `GET /root-agent/persona-intents` (from `evals/config/persona_config.yaml`)
- `GET /root-agent/personas?intent_name=...` (from `evals/config/personas/`)

### Run the persona agent (evals)

Endpoint: `POST /persona-agent/run`

```powershell
curl -X POST http://localhost:8000/persona-agent/run `
  -H "Content-Type: application/json" `
  -d '{\"user_id\":\"u1\",\"session_id\":\"s1\",\"persona_id\":\"p1\",\"intent_name\":\"flight_booking\",\"user_question\":\"Where are you flying from?\"}'
```

## Domain/Requirements Configuration

- Intents live in `src/configs/domain/intents.yaml`.
- Requirements are loaded from `src/configs/requirements/<intent>.yaml` (for example `flight_booking.yaml`).
- Prompt templates are under `src/configs/prompts/`.

If an intent is listed in `intents.yaml` but there is no matching `src/configs/requirements/<intent>.yaml`, the requirements-based agents will fail when they try to load that YAML.

## Observability

- Langfuse client auth check happens in `app.py`.
- OpenInference instrumentation is enabled via `openinference.instrumentation.google_adk` in `app.py`.
