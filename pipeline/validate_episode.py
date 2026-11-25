#!/usr/bin/env python3
"""Structural and data checks for an episode folder.

Profiles:
  episode    full episode: all production folders required (default)
  prototype  visual prototype: only blender/ and renders/ required

Checks storyboard/*.json, research/source_dossier.json and research/claim_ledger.json
against the JSON Schemas in schemas/, and checks that every source ID cited by the
storyboard or claim ledger exists in the source dossier.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO / "schemas"

PROFILES = {
    "episode": ("research", "script", "storyboard", "blender", "renders", "audio", "edit", "thumbnail", "final"),
    "prototype": ("blender", "renders"),
}

try:
    import jsonschema
except ImportError:  # validation degrades to structure-only checks
    jsonschema = None


def _load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON in {path.name}: {exc}")
        return None


def _schema_errors(payload, schema_name: str, label: str) -> list[str]:
    if jsonschema is None:
        return []
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    out = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(root)"
        out.append(f"{label}: {where}: {err.message}")
    return out


def validate_episode(root: Path, profile: str = "episode") -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        return [f"Episode directory does not exist: {root}"], warnings
    if jsonschema is None:
        warnings.append("jsonschema not installed: schema checks skipped (pip install -r requirements.txt)")

    for folder in PROFILES[profile]:
        if not (root / folder).is_dir():
            errors.append(f"Missing folder: {folder}")

    known_sources: set[str] | None = None
    dossier_path = root / "research" / "source_dossier.json"
    if dossier_path.is_file():
        dossier = _load_json(dossier_path, errors)
        if dossier is not None:
            errors += _schema_errors(dossier, "source_dossier.schema.json", dossier_path.name)
            known_sources = {s.get("id") for s in dossier.get("sources", []) if isinstance(s, dict)}

    cited: list[tuple[str, str]] = []
    ledger_path = root / "research" / "claim_ledger.json"
    if ledger_path.is_file():
        ledger = _load_json(ledger_path, errors)
        if ledger is not None:
            errors += _schema_errors(ledger, "claim_ledger.schema.json", ledger_path.name)
            for claim in ledger.get("claims", []):
                for sid in claim.get("source_ids", []) if isinstance(claim, dict) else []:
                    cited.append((f"{ledger_path.name} claim {claim.get('claim_id')}", sid))

    storyboard_dir = root / "storyboard"
    if storyboard_dir.is_dir():
        for path in sorted(storyboard_dir.glob("*.json")):
            payload = _load_json(path, errors)
            if payload is None:
                continue
            if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
                errors.append(f"{path.name}: expected an object with a scenes array")
                continue
            errors += _schema_errors(payload, "storyboard.schema.json", path.name)
            for scene in payload["scenes"]:
                for sid in scene.get("source_ids", []) if isinstance(scene, dict) else []:
                    cited.append((f"{path.name} scene {scene.get('scene_id')}", sid))

    if cited:
        if known_sources is None:
            errors.append("Source IDs are cited but research/source_dossier.json is missing")
        else:
            for where, sid in cited:
                if sid not in known_sources:
                    errors.append(f"{where}: source {sid} not found in source_dossier.json")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("episode_dir", type=Path)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="episode")
    args = parser.parse_args()
    errors, warnings = validate_episode(args.episode_dir, args.profile)
    for w in warnings:
        print(f"WARNING: {w}")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALIDATION PASSED ({args.profile})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
