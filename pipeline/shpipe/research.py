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
        return {"status": "fail", "errors": ["research/sources.json (or source_dossier.json) and research/claim_ledger.json are required"]}
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


LABEL_NAMES = {"established_fact": "Established fact", "strong_evidence": "Strong evidence", "hypothesis": "Hypothesis",
               "disputed": "Disputed", "unverified_report": "Unverified report", "speculation": "Speculation"}


def ledger_markdown(ep: Episode) -> str:
    """Human-readable CLAIM_LEDGER.md generated from claim_ledger.json (the JSON stays the source of truth)."""
    ledger = config.load_json(ep.ledger)
    sources = {s["id"]: s for s in config.load_json(ep.dossier).get("sources", [])} if ep.dossier.is_file() else {}
    claims = ledger.get("claims", [])
    counts = Counter(c.get("evidence_label") for c in claims if c.get("status") != "removed")
    out = [f"# Claim Ledger — {ledger.get('episode_id', ep.episode_id)}", "",
           "Generated from `research/claim_ledger.json` by `sh.py ledger-md`; edit the JSON, not this file.", "",
           "| Label | Claims |", "|---|---|"]
    out += [f"| {LABEL_NAMES.get(k, k)} | {v} |" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
    out += ["", "| ID | Claim | Label | Sources | Status |", "|---|---|---|---|---|"]
    for c in claims:
        ids = ", ".join(c.get("source_ids", [])) or "—"
        text = c["text"].replace("|", "\\|")
        out.append(f"| {c['claim_id']} | {text} | {LABEL_NAMES.get(c['evidence_label'], c['evidence_label'])} | {ids} | {c.get('status', 'draft')} |")
    out += ["", "## Notes per claim", ""]
    for c in claims:
        out.append(f"### {c['claim_id']} — {LABEL_NAMES.get(c['evidence_label'], c['evidence_label'])}")
        out.append(c["text"])
        for sid in c.get("source_ids", []):
            s = sources.get(sid)
            out.append(f"- **{sid}**: {s['title']} ({s['author_or_org']}, {s.get('published', 'n.d.')})" if s else f"- **{sid}**: (not in dossier)")
        if c.get("counter_evidence"):
            out.append(f"- *Counter-evidence / caveats:* {c['counter_evidence']}")
        if c.get("alternative_explanations"):
            out.append("- *Alternatives:* " + "; ".join(c["alternative_explanations"]))
        if c.get("script_wording"):
            out.append(f"- *Approved wording (draft):* \"{c['script_wording']}\"")
        out.append("")
    return "\n".join(out)
