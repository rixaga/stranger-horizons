"""Script Generator checks: claim markers, story beats, timing.

The script itself is written by people (Claude drafts, owner approves) from
templates/script_template.md. This module verifies it against the claim ledger and
the channel's seven-beat structure, and estimates narration time.
"""
from __future__ import annotations

import re

from . import config
from .paths import Episode

WPM = 145
BEATS = [("Hook", "hook"), ("Context", "context"), ("Anomaly", "anomaly"), ("Investigation", "investigation"),
         ("Possibilities", "possibilit"), ("Verdict", "verdict"), ("Closing question", "closing")]
MARKER = re.compile(r"\[(C\d{2,})\]")
RECON = "{RECON}"


def parse(text: str) -> list[dict]:
    """Split on '## ' headings; stop at the first horizontal rule (reviewer notes follow it)."""
    body = re.split(r"^---\s*$", text, maxsplit=1, flags=re.M)[0]
    sections, current = [], None
    for line in body.splitlines():
        if line.startswith("## "):
            current = {"heading": line[3:].strip(), "lines": []}
            sections.append(current)
        elif current is not None and not line.startswith("#"):
            current["lines"].append(line)
    for s in sections:
        prose = " ".join(s.pop("lines"))
        s["markers"] = MARKER.findall(prose)
        s["recon"] = prose.count(RECON)
        spoken = re.sub(r"\[C\d+\]|\{RECON\}|<[^>]*>", " ", prose)
        s["words"] = len(re.findall(r"[A-Za-z0-9'’-]+", spoken))
    return sections


def check(ep: Episode) -> dict:
    if not ep.script.is_file():
        return {"status": "fail", "errors": ["script/script.md is missing"]}
    sections = parse(ep.script.read_text(encoding="utf-8"))
    ledger = config.load_json(ep.ledger) if ep.ledger.is_file() else {"claims": []}
    live = {c["claim_id"] for c in ledger.get("claims", []) if c.get("status") != "removed"}
    removed = {c["claim_id"] for c in ledger.get("claims", []) if c.get("status") == "removed"}
    used = [m for s in sections for m in s["markers"]]
    headings = [s["heading"].lower() for s in sections]
    missing_beats = [name for name, key in BEATS if not any(key in h for h in headings)]
    words = sum(s["words"] for s in sections)
    seconds = words / WPM * 60

    errors = []
    unknown = sorted(set(used) - live - removed)
    cites_removed = sorted(set(used) & removed)
    if unknown:
        errors.append("claim markers not in the ledger: " + ", ".join(unknown))
    if cites_removed:
        errors.append("script cites claims marked removed: " + ", ".join(cites_removed))
    if missing_beats:
        errors.append("missing story beats: " + ", ".join(missing_beats))
    warnings = []
    target = config.channel_config().get("long_form_target_minutes", {})
    if target and not (target["min"] * 60 <= seconds <= target["max"] * 60):
        warnings.append(f"estimated length {seconds / 60:.1f} min is outside {target['min']}–{target['max']} min")
    return {
        "status": "fail" if errors else ("warn" if warnings else "pass"),
        "sections": sections,
        "word_count": words,
        "estimated_seconds": seconds,
        "claim_markers": sorted(set(used)),
        "unknown_claim_markers": unknown,
        "reconstruction_markers": sum(s["recon"] for s in sections),
        "missing_beats": missing_beats,
        "errors": errors,
        "warnings": warnings,
    }
