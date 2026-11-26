"""Research Manager checks: dossier + claim ledger coverage.

Finding and judging sources is human work; this module checks that the record of
that work is complete and internally consistent.
"""
from __future__ import annotations

from collections import Counter

from . import config
from .paths import Episode

WEAK_TYPES = {"social_or_forum", "secondary_summary"}
WEAK_RELIABILITY = {"low", "lead_only"}


def coverage(ep: Episode) -> dict:
    errors: list[str] = []
    if not ep.dossier.is_file() or not ep.ledger.is_file():
        return {"status": "fail", "errors": ["research/source_dossier.json and research/claim_ledger.json are required"]}
    dossier, ledger = config.load_json(ep.dossier), config.load_json(ep.ledger)
    errors += [f"dossier: {e}" for e in config.validate(dossier, "source_dossier")]
    errors += [f"ledger: {e}" for e in config.validate(ledger, "claim_ledger")]

    sources = {s["id"]: s for s in dossier.get("sources", []) if isinstance(s, dict) and "id" in s}
    claims = [c for c in ledger.get("claims", []) if isinstance(c, dict) and c.get("status") != "removed"]
    used: set[str] = set()
    without, weak_only, unknown = [], [], []
    for c in claims:
        ids = c.get("source_ids", [])
        used.update(ids)
        for sid in ids:
            if sid not in sources:
                unknown.append(f"{c['claim_id']}→{sid}")
        known = [sources[s] for s in ids if s in sources]
        if not known and c.get("evidence_label") != "speculation":
            without.append(c["claim_id"])
        elif known and all(s.get("source_type") in WEAK_TYPES or s.get("reliability") in WEAK_RELIABILITY for s in known):
            weak_only.append(c["claim_id"])
    unused = sorted(set(sources) - used)
    if unknown:
        errors.append("claims cite unknown sources: " + ", ".join(unknown))
    if without:
        errors.append("claims without sources (only speculation may have none): " + ", ".join(without))

    warnings = []
    if weak_only:
        warnings.append("claims backed only by weak sources: " + ", ".join(weak_only))
    if unused:
        warnings.append("sources not cited by any claim: " + ", ".join(unused))
    return {
        "status": "fail" if errors else ("warn" if warnings else "pass"),
        "counts": {"sources": len(sources), "claims": len(claims)},
        "labels": dict(Counter(c.get("evidence_label") for c in claims)),
        "claims_without_sources": without,
        "claims_only_weak_sources": weak_only,
        "unused_sources": unused,
        "errors": errors,
        "warnings": warnings,
    }
