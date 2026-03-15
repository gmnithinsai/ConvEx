from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from jinja2 import Environment, StrictUndefined, Template

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = PROJECT_ROOT / "src" / "configs" / "prompts"


@dataclass
class CachedTemplate:
    template: Template
    last_modified: float


_TEMPLATE_CACHE: dict[str, CachedTemplate] = {}
_CACHE_LOCK = Lock()


_JINJA_ENV = Environment(
    autoescape=False,  # noqa: RUF123: This is a plain-text prompt, not HTML
    undefined=StrictUndefined,  # fail fast if variable missing
    trim_blocks=True,
    lstrip_blocks=True,
)


def _load_template_from_disk(template_name: str) -> CachedTemplate:
    template_path = PROMPTS_DIR / template_name

    if not template_path.exists():
        error_msg = f"Prompt template not found: {template_path}"
        raise FileNotFoundError(error_msg)

    source = template_path.read_text(encoding="utf-8")
    template = _JINJA_ENV.from_string(source)

    return CachedTemplate(
        template=template,
        last_modified=template_path.stat().st_mtime,
    )


def render_prompt(
    template_name: str,
    **variables: Any,
) -> str:
    template_path = PROMPTS_DIR / template_name
    if not template_path.exists():
        error_msg = f"Prompt template not found: {template_path}"
        raise FileNotFoundError(error_msg)

    current_mtime = template_path.stat().st_mtime

    with _CACHE_LOCK:
        cached = _TEMPLATE_CACHE.get(template_name)

        if cached is None or cached.last_modified != current_mtime:
            cached = _load_template_from_disk(template_name)
            _TEMPLATE_CACHE[template_name] = cached

    # Pre-render check for undefined variables in the template
    # Render with a custom context to catch undefined variables
    try:
        result = cached.template.render(**variables)
    except Exception as exc:
        # Try to provide more info if it's a StrictUndefined error
        import re

        msg = str(exc)
        # Try to extract variable name from error message
        match = re.search(r"'([^']+)' is undefined", msg)
        if match:
            missing_var = match.group(1)
            raise ValueError(
                f"Missing template variable: '{missing_var}' in template '{template_name}'",
            ) from exc
        raise
    return result


def clear_prompt_cache() -> None:
    """Clear all cached templates (useful for tests)."""
    with _CACHE_LOCK:
        _TEMPLATE_CACHE.clear()


def get_cached_templates() -> dict[str, float]:
    """Inspect cached templates and their mtimes."""
    with _CACHE_LOCK:
        return {name: data.last_modified for name, data in _TEMPLATE_CACHE.items()}


__all__ = ["clear_prompt_cache", "get_cached_templates", "render_prompt"]
