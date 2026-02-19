import json
from typing import Any

from google.genai import types

from src.common.conversation_history import ConversationHistoryService
from src.configs.domain.domain_loader import (
    render_yaml,
)
from src.configs.prompts.prompt_loader import render_prompt

# ----------------------------------------
# Static Instruction Builder
# ----------------------------------------


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


def build_information_extraction_static_instruction():
    """Returns static instruction Content object."""
    return types.Content(
        role="user",
        parts=[
            types.Part(
                text=render_prompt(
                    "response_layer/information_extraction/information_extraction_static.jinja2",
                ),
            ),
        ],
    )


# ----------------------------------------
# Dynamic Instruction Builder
# ----------------------------------------
def build_information_extraction_instruction(context):
    """Returns rendered variable instruction prompt."""
    ctx_state = context.session.state

    # Get intent_detection_output
    intent_output = ctx_state.get("intent_detection_agent_output")
    if intent_output is None:
        raise ValueError("intent_detection_agent_output not found in context")

    # Ensure JSON and extract intent
    intent_json = ensure_json(intent_output)
    intent_selected = intent_json.get("intent_selected")

    if not intent_selected:
        raise ValueError("intent_selected missing in intent_detection_output")

    # Load domain-specific requirements config
    domain_config_file = f"requirements/{intent_selected}.yaml"
    domain_cfg = render_yaml(domain_config_file)

    # Render prompt with requirements_info
    return render_prompt(
        "response_layer/information_extraction/information_extraction_variable.jinja2",
        conversation_history=ConversationHistoryService(context).build_history(),
        requirements_info=domain_cfg["requirements"],
        context=context,
    )
