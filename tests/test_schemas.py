from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from conftest import REPO

SCHEMAS = sorted((REPO / "schemas").glob("*.schema.json"))


@pytest.mark.parametrize("path", SCHEMAS, ids=lambda p: p.name)
def test_schema_is_valid(path: Path):
    jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text()))


def load(name: str) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(json.loads((REPO / "schemas" / name).read_text()))


def test_storyboard_rejects_empty_scenes():
    v = load("storyboard.schema.json")
    assert list(v.iter_errors({"episode_id": "E", "title": "T", "fps": 30, "scenes": []}))


def test_storyboard_rejects_misspelled_scene_field():
    v = load("storyboard.schema.json")
    scene = {"scene_id": "S1", "duration_seconds": 1, "visual_intent": "x",
             "reconstruction_status": "abstract_visual", "camera": {}, "naration": "typo"}
    assert list(v.iter_errors({"episode_id": "E", "title": "T", "fps": 30, "scenes": [scene]}))


def test_new_schemas_exist():
    names = {p.name for p in SCHEMAS}
    assert {"source_dossier.schema.json", "claim_ledger.schema.json", "asset_register.schema.json"} <= names


@pytest.mark.parametrize("template,schema", [
    ("source_dossier.example.json", "source_dossier.schema.json"),
    ("claim_ledger.example.json", "claim_ledger.schema.json"),
    ("asset_register.example.json", "asset_register.schema.json"),
    ("storyboard.example.json", "storyboard.schema.json"),
])
def test_templates_validate(template: str, schema: str):
    data = json.loads((REPO / "templates" / template).read_text())
    errors = [e.message for e in load(schema).iter_errors(data)]
    assert errors == []


def test_claim_ledger_requires_evidence_label():
    v = load("claim_ledger.schema.json")
    claim = {"claim_id": "C1", "text": "x", "source_ids": ["SRC-001"], "evidence_label": "probably true"}
    assert list(v.iter_errors({"episode_id": "E", "claims": [claim]}))
