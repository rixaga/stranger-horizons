"""Repository paths, JSON config loading and JSON Schema validation."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO / "config"
SCHEMA_DIR = REPO / "schemas"
PRESET_DIR = CONFIG_DIR / "presets"

try:
    import jsonschema
except ImportError:  # validation degrades gracefully; check_environment reports it
    jsonschema = None


def load_json(path: Path):
    with Path(path).open(encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def render_config() -> dict:
    return load_json(CONFIG_DIR / "render_config.json")


def channel_config() -> dict:
    return load_json(CONFIG_DIR / "channel.json")


def camera_moves() -> dict:
    return load_json(CONFIG_DIR / "camera_presets.json")["moves"]


def environment_presets() -> list[str]:
    return sorted(p.stem for p in PRESET_DIR.glob("*.json") if p.stem != "base")


@lru_cache(maxsize=None)
def _schema(name: str) -> dict:
    return load_json(SCHEMA_DIR / f"{name}.schema.json")


def validate(data, schema_name: str) -> list[str]:
    """Return human-readable schema errors ('' list = valid). Empty if jsonschema is unavailable."""
    if jsonschema is None:
        return []
    validator = jsonschema.Draft202012Validator(_schema(schema_name))
    out = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(root)"
        out.append(f"{where}: {err.message}")
    return out
