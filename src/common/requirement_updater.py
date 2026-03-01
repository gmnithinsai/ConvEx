import json
from typing import Any, Optional
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from src.configs.domain.domain_loader import (
    render_yaml,
)
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

def build_requirements_status(requirements_info: list) -> dict:
    """
    Creates initial requirements_status structure
    from requirements_info YAML structure.
    """

    requirements_status = {}

    if not isinstance(requirements_info, list):
        return requirements_status

    for requirement in requirements_info:
        questions = requirement.get("questions", [])

        if not isinstance(questions, list):
            continue

        for question in questions:
            q_id = question.get("id")

            if not q_id:
                continue

            requirements_status[q_id] = {
                "attempt_count": 0,
                "status": "missing",
            }

    return requirements_status

def update_requirements_status(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    Updates requirements_status inside callback_context.state.
    Does NOT replace agent output.
    """

    state = callback_context.state.to_dict()

    # ---------------------------------------------------------
    # Safe JSON parser
    # ---------------------------------------------------------
    def safe_json(value):
        if not value:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    # ---------------------------------------------------------
    # Step 1: Load requirements_info (same logic as builder)
    # ---------------------------------------------------------
    if "requirements_info" not in callback_context.state:

        intent_output = state.get("intent_detection_agent_output")
        if not intent_output:
            raise ValueError("intent_detection_agent_output not found")

        intent_json = ensure_json(intent_output)
        intent_selected = intent_json.get("intent_selected")

        if not intent_selected:
            raise ValueError("intent_selected missing in intent_detection_agent_output")

        domain_config_file = f"requirements/{intent_selected}.yaml"
        domain_cfg = render_yaml(domain_config_file)

        requirements_info = domain_cfg.get("requirements", [])

        # Cache in session state
        callback_context.state["requirements_info"] = requirements_info

    else:
        requirements_info = callback_context.state.get("requirements_info", [])

    # ---------------------------------------------------------
    # Step 2: Initialize requirements_status (only once)
    # ---------------------------------------------------------
    if "requirements_status" not in callback_context.state:

        requirements_status = {}

        for requirement in requirements_info:
            for question in requirement.get("questions", []):
                q_id = question.get("id")
                if q_id:
                    requirements_status[q_id] = {
                        "attempt_count": 0,
                        "status": "missing",  # missing | satisfied | complete
                    }

        callback_context.state["requirements_status"] = requirements_status

    # ---------------------------------------------------------
    # Step 3: Update attempt count using requirements_next_output
    # ---------------------------------------------------------
    requirements_next_output = safe_json(
        state.get("requirements_next_output")
    )

    if requirements_next_output:
        next_question_id = requirements_next_output.get("next_question_id")

        requirements_status = callback_context.state.get(
            "requirements_status", {}
        )

        if next_question_id and next_question_id in requirements_status:
            requirements_status[next_question_id]["attempt_count"] += 1

            if requirements_status[next_question_id]["attempt_count"] >= 2:
                requirements_status[next_question_id]["status"] = "complete"

            callback_context.state["requirements_status"] = requirements_status

    # ---------------------------------------------------------
    # Step 4: Mark satisfied questions
    # ---------------------------------------------------------
    if requirements_next_output:
        req_status_list = requirements_next_output.get(
            "requirements_status", []
        )

        requirements_status = callback_context.state.get(
            "requirements_status", {}
        )

        for requirement in req_status_list:
            for question in requirement.get("questions", []):
                q_id = question.get("id")
                q_status = question.get("status")

                if q_id in requirements_status and q_status == "satisfied":
                    requirements_status[q_id]["status"] = "satisfied"

        callback_context.state["requirements_status"] = requirements_status

    print(
        "Updated requirements_status:",
        callback_context.state.get("requirements_status"),
    )

    # Preserve original agent output
    return None