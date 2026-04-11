# Agents

This repo uses Google ADK agents to run a sequential dialogue pipeline. This doc is only about the agents: where they live, what they do, and what they read/write in session state.

## Top-Level Pipeline

Entry point: `src/agents/root_agent/agent.py`

`conversation_pipeline_agent` is a `SequentialAgent` that runs these sub-agents in order:

1. `intent_detection_agent`
2. `information_extraction_agent`
3. `requirements_status_updater_agent`
4. `requirements_next_agent`

Note: there is also a `src/root_agent.yaml` used by some ADK tooling, but the Python pipeline in `src/agents/root_agent/agent.py` is the source of truth for the runtime behavior.

## Agents (By Layer)

### Intent Detection

- Location: `src/agents/intent_detection_layer/`
- Agent: `intent_detection_agent`
- Output key: `intent_detection_agent_output`
- Purpose: choose an intent (for example `flight_booking`) from `src/configs/domain/intents.yaml`.

### Information Extraction

- Location: `src/agents/response_layer/information_extraction/`
- Agent: `information_extraction_agent`
- Output key: `information_extraction_output`
- Purpose: extract structured fields from the latest user message (used downstream by requirements logic).

### Requirements Status Updater

- Location: `src/agents/response_layer/requirements_status_updater/`
- Agent: `requirements_status_updater_agent`
- Output key: `requirements_status_update`
- Purpose: evaluate each requirement field as `satisfied` or `missing` based on the latest user message.
- Callback: `src/common/requirement_updater.py:apply_requirements_status_update`
  - Applies the model output into the session `requirements_status` map.

### Requirements Next (Next Question Selector)

- Location: `src/agents/response_layer/requirements_next/`
- Agent: `requirements_next_agent`
- Output key: `requirements_next_output`
- Purpose: decide the next question to ask (based on requirements + current state).
- Callback: `src/common/requirement_updater.py:update_attempt_count_from_next_output`
  - Increments `attempt_count` for the chosen `next_question_id` and can mark fields as `complete` after repeated attempts.

### Persona Agent (Evals)

- Location: `evals/persona_agent/`
- Agent: `persona_agent`
- Output key: `persona_agent_output`
- Purpose: respond as a synthetic persona (used via `src/api/routes/persona_agent.py`).

## Shared Session State Keys

The agents communicate via ADK session state. Common keys you will see:

- `intent_detection_agent_output`: selected intent and intent metadata.
- `information_extraction_output`: structured fields extracted from user input.
- `requirements_info`: cached requirements YAML (loaded from `src/configs/requirements/<intent>.yaml`).
- `requirements_status`: canonical per-field status map built and updated over time:
  - `{ "<field_id>": { "attempt_count": int, "status": "missing|satisfied|complete" } }`
- `requirements_status_update`: latest status evaluation output from the status-updater agent.
- `requirements_next_output`: latest "next question" decision from the requirements-next agent.

## Adding Or Modifying Agents

1. Create a new agent package under `src/agents/<layer>/<agent_name>/` with:
   - `agent.py` (the `LlmAgent` definition)
   - `config.py` (prompt builders/instructions)
   - `schema.py` (Pydantic input/output schemas)
2. Wire it into the pipeline in `src/agents/root_agent/agent.py` (order matters for `SequentialAgent`).
3. If the agent needs to mutate state, prefer an `after_agent_callback` in a shared module (for example `src/common/requirement_updater.py`).
