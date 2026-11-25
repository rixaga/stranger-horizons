#!/usr/bin/env python3
"""Basic structural checks for an episode folder."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

REQUIRED_DIRS = ("research", "script", "storyboard", "blender", "renders", "audio", "edit", "thumbnail", "final")

def validate_episode(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.exists() or not root.is_dir():
        return [f"Episode directory does not exist: {root}"]
    for folder in REQUIRED_DIRS:
        if not (root / folder).exists():
            errors.append(f"Missing folder: {folder}")
    storyboard_dir = root / "storyboard"
    if storyboard_dir.exists():
        for path in storyboard_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Invalid JSON in {path.name}: {exc}")
                continue
            if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
                errors.append(f"{path.name}: expected an object with a scenes array")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir", type=Path)
    args = parser.parse_args()
    errors = validate_episode(args.episode_dir)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
