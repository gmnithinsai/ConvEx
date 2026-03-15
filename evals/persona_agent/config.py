from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from google.genai import types
from jinja2 import Environment, StrictUndefined, Template

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PERSONA_PROMPT_PATH = PROJECT_ROOT / "evals" / "config" / "persona_prompt.jinja2"

_JINJA_ENV = Environment(
    autoescape=False,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
_TEMPLATE_CACHE: Template | None = None
_TEMPLATE_MTIME: float | None = None
_CACHE_LOCK = Lock()


def _load_template() -> Template:
    if not PERSONA_PROMPT_PATH.exists():
        msg = f"Prompt template not found: {PERSONA_PROMPT_PATH}"
        raise FileNotFoundError(msg)

    source = PERSONA_PROMPT_PATH.read_text(encoding="utf-8")
    # Current file includes raw guards; strip before rendering.
    source = source.replace("{% raw %}", "").replace("{% endraw %}", "")
    return _JINJA_ENV.from_string(source)


def _get_cached_template() -> Template:
    global _TEMPLATE_CACHE
    global _TEMPLATE_MTIME

    mtime = PERSONA_PROMPT_PATH.stat().st_mtime
    with _CACHE_LOCK:
        if _TEMPLATE_CACHE is None or mtime != _TEMPLATE_MTIME:
            _TEMPLATE_CACHE = _load_template()
            _TEMPLATE_MTIME = mtime
    return _TEMPLATE_CACHE


def render_persona_prompt(*, persona: dict[str, Any], user_question: str) -> str:
    template = _get_cached_template()
    return template.render(persona=persona, user_question=user_question)


def build_persona_static_instruction() -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "You are a persona simulation agent. "
                    "Always follow the dynamic persona prompt exactly and return only reply text."
                ),
            ),
        ],
    )


def _extract_payload_from_context(context) -> dict[str, Any]:
    events = getattr(context.session, "events", [])
    for event in reversed(events):
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            continue
        for part in content.parts:
            text = getattr(part, "text", None)
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
    return {}


def build_persona_instruction(context) -> str:
    payload = _extract_payload_from_context(context)
    prompt_text = payload.get("prompt_text")
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("prompt_text missing for persona_agent input.")
    return prompt_text
