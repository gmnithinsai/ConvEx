from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = PROJECT_ROOT / "src" / "configs"


# --------------------------------
# CACHE STRUCTURE
# --------------------------------
class _YamlCacheEntry:
    __slots__ = ("data", "mtime")

    def __init__(self, data: Any, mtime: float):
        self.data = data
        self.mtime = mtime


_CACHE: dict[Path, _YamlCacheEntry] = {}
_LOCK = Lock()


# --------------------------------
# PUBLIC API
# --------------------------------
def render_yaml(
    path: str | Path,
    *,
    schema: type[T] | None = None,
    force_reload: bool = False,
) -> Any | T:
    path = PROMPTS_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    if path.suffix not in {".yaml", ".yml"}:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    current_mtime = path.stat().st_mtime

    with _LOCK:
        cached = _CACHE.get(path)

        if cached is None or cached.mtime != current_mtime or force_reload:
            try:
                raw = yaml.safe_load(path.read_text())
                if raw is None:
                    raise ValueError("YAML file is empty")

                if schema:
                    data = schema.model_validate(raw)
                else:
                    data = raw

            except yaml.YAMLError as e:
                raise RuntimeError(f"Invalid YAML syntax in {path}") from e

            except ValidationError as e:
                raise RuntimeError(
                    f"YAML schema validation failed for {path}:\n{e}",
                ) from e

            _CACHE[path] = _YamlCacheEntry(data=data, mtime=current_mtime)

    return _CACHE[path].data
