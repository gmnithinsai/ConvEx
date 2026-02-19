import json
from typing import Any

from google.genai import types

from src.common.conversation_history import (
    ConversationHistoryService,
)
from src.configs.domain.domain_loader import (
    render_yaml,
)
from src.configs.prompts.prompt_loader import (
    render_prompt,
)


def requirements_next_static_instruction() -> types.Content:
    """Static instruction for requirements_next_agent. Loaded once and reused across runs."""
    return types.Content(
        role="user",
        parts=[
            types.Part(
                text=render_prompt(
                    "response_layer/requirements_next/requirements_next_static.jinja2",
                ),
            ),
        ],
    )


def ensure_json(value: Any) -> dict:
    """Ensures the value is a dict. - If already dict → return - If string → try json.loads."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValueError("intent_detection_output is not valid JSON")  # noqa: B904
    raise TypeError("Unsupported intent_detection_output type")


def requirements_next_instruction(context):
    # 1️⃣ Read session state
    ctx_state = context.session.state
    history_service = ConversationHistoryService(context)
    conversation_history = history_service.build_history()

    # --------------------------------------------------
    # 🔥 HARD NORMALIZATION (PRODUCTION SAFE)
    # --------------------------------------------------
    raw_requirements_output = ctx_state.get("requirements_next_output")

    # raw_requirements_output = ctx_state.get("requirements_next_output")

    if raw_requirements_output is not None:
        if isinstance(raw_requirements_output, str):
            try:
                raw_requirements_output = json.loads(raw_requirements_output)
            except Exception:
                raw_requirements_output = {}

        if not isinstance(raw_requirements_output, dict):
            raw_requirements_output = {}

        # Normalize requirements_status (must be LIST)
        raw_status = raw_requirements_output.get("requirements_status")

        if isinstance(raw_status, str):
            try:
                raw_status = json.loads(raw_status)
            except Exception:
                raw_status = []

        if raw_status is None or not isinstance(raw_status, list):
            raw_status = []

        raw_requirements_output["requirements_status"] = raw_status

        ctx_state["requirements_next_output"] = raw_requirements_output

    else:
        ctx_state["requirements_next_output"] = {
            "requirements_status": [],
        }

    # --------------------------------------------------

    # 2️⃣ Get intent_detection_output
    raw_intent_output = ctx_state.get("intent_detection_agent_output")
    if raw_intent_output is None:
        raise ValueError("intent_detection_agent_output not found in session state")

    # 3️⃣ Ensure JSON + extract intent
    intent_json = ensure_json(raw_intent_output)
    intent_selected = intent_json.get("intent_selected")

    if not intent_selected:
        raise ValueError("intent_selected missing in intent_detection_output")

    # 4️⃣ Load domain-specific requirements config
    domain_config_file = f"requirements/{intent_selected}.yaml"
    domain_cfg = render_yaml(domain_config_file)

    # 5️⃣ Render prompt
    return render_prompt(
        "response_layer/requirements_next/requirements_next_variable.jinja2",
        requirements_info=domain_cfg["requirements"],
        conversation_history=conversation_history,
        context=context,
    )
