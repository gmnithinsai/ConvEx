import json
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from src.configs.domain.domain_loader import render_yaml

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


def safe_json(value: Any) -> dict | None:
    """Best-effort conversion of state values into a dict."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def ensure_requirements_initialized(callback_context: CallbackContext) -> None:
    """
    Ensures the session state contains:
    - requirements_info: loaded from the selected intent's YAML
    - requirements_status: {<field_id>: {attempt_count, status}}
    """
    state = callback_context.state.to_dict()

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
        callback_context.state["requirements_info"] = domain_cfg.get("requirements", [])

    if "requirements_status" not in callback_context.state:
        requirements_info = callback_context.state.get("requirements_info", [])
        callback_context.state["requirements_status"] = build_requirements_status(
            requirements_info,
        )


def apply_requirements_status_update(
    callback_context: CallbackContext,
) -> types.Content | None:
    """
    Applies `requirements_status_update` into session `requirements_status`.

    Expected state payload shape:
    {
      "requirements_status": {
        "<field_id>": {
          "status": "satisfied|missing",
          "reason": "..."
        }
      }
    }
    """
    ensure_requirements_initialized(callback_context)

    state = callback_context.state.to_dict()
    update_payload = safe_json(state.get("requirements_status_update"))
    if not update_payload:
        return None

    update_fields = update_payload.get("requirements_status")
    if not isinstance(update_fields, dict):
        return None

    requirements_status = callback_context.state.get("requirements_status", {})
    if not isinstance(requirements_status, dict) or not requirements_status:
        return None

    for field_id, field_update in update_fields.items():
        if field_id not in requirements_status or not isinstance(field_update, dict):
            continue

        status = field_update.get("status")
        if not isinstance(status, str):
            continue

        normalized = status.strip().lower()
        if normalized == "satisfied":
            requirements_status[field_id]["status"] = "satisfied"
        elif normalized == "missing":
            # Keep missing unless already satisfied.
            if requirements_status[field_id].get("status") != "satisfied":
                requirements_status[field_id]["status"] = "missing"

    callback_context.state["requirements_status"] = requirements_status

    print(
        "Updated requirements_status (from status updater):",
        callback_context.state.get("requirements_status"),
    )

    return None


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


def update_attempt_count_from_next_output(
    callback_context: CallbackContext,
) -> None:
    """
    Updates attempt_count for the question in requirements_next_output.
    """
    ensure_requirements_initialized(callback_context)
    state = callback_context.state.to_dict()
    requirements_next_output = safe_json(state.get("requirements_next_output"))
    if requirements_next_output:
        next_question_id = requirements_next_output.get("next_question_id")
        requirements_status = callback_context.state.get("requirements_status", {})
        if next_question_id and next_question_id in requirements_status:
            requirements_status[next_question_id]["attempt_count"] += 1
            # Mark as "complete" after repeated failed attempts, but don't override "satisfied".
            if (
                requirements_status[next_question_id]["attempt_count"] >= 2
                and requirements_status[next_question_id].get("status") != "satisfied"
            ):
                requirements_status[next_question_id]["status"] = "complete"
            callback_context.state["requirements_status"] = requirements_status
    print(
        "Updated requirements_status (from next_output):",
        callback_context.state.get("requirements_status"),
    )


def update_attempt_count_from_status_update(
    callback_context: CallbackContext,
) -> None:
    """
    Updates attempt_count for each field in requirements_status_update (format: {"requirements_status": {<field_id>: {...}}})
    """
    ensure_requirements_initialized(callback_context)
    state = callback_context.state.to_dict()
    update_payload = safe_json(state.get("requirements_status_update"))
    if not update_payload:
        return
    update_fields = update_payload.get("requirements_status")
    if not isinstance(update_fields, dict):
        return
    requirements_status = callback_context.state.get("requirements_status", {})
    if not isinstance(requirements_status, dict) or not requirements_status:
        return
    for field_id in update_fields:
        if field_id in requirements_status:
            requirements_status[field_id]["attempt_count"] += 1
            # Mark as "complete" after repeated failed attempts, but don't override "satisfied".
            if (
                requirements_status[field_id]["attempt_count"] >= 2
                and requirements_status[field_id].get("status") != "satisfied"
            ):
                requirements_status[field_id]["status"] = "complete"
    callback_context.state["requirements_status"] = requirements_status
    print(
        "Updated requirements_status (from status_update):",
        callback_context.state.get("requirements_status"),
    )
