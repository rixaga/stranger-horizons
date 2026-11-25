"""Asset manager checks: every file under assets/ is registered, licensed and present."""
from __future__ import annotations

from pathlib import Path

from . import config

ASSET_DIRS = ("audio", "environments", "materials", "models")
IGNORED = {".gitkeep", ".DS_Store", "Thumbs.db"}


def check(register_path: Path = config.REPO / "assets" / "asset_register.json", repo_root: Path = config.REPO) -> dict:
    register_path, repo_root = Path(register_path), Path(repo_root)
    reg = config.load_json(register_path) if register_path.is_file() else {"assets": []}
    errors = [f"schema: {e}" for e in config.validate(reg, "asset_register")]
    entries = reg.get("assets", [])
    ids = [a.get("id") for a in entries]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        errors.append("duplicate asset IDs: " + ", ".join(dupes))

    missing = [a["id"] for a in entries if a.get("local_path") and not (repo_root / a["local_path"]).is_file()]
    attribution = [a["id"] for a in entries if a.get("attribution_required") and not a.get("attribution_text")]
    registered = {str(Path(a["local_path"])) for a in entries if a.get("local_path")}
    on_disk = []
    root = register_path.parent
    for d in ASSET_DIRS:
        for f in sorted((root / d).rglob("*")) if (root / d).is_dir() else []:
            if f.is_file() and f.name not in IGNORED:
                on_disk.append(str(f.relative_to(repo_root)))
    unregistered = [p for p in on_disk if p not in registered]
    if missing:
        errors.append("registered files missing on disk: " + ", ".join(missing))
    if unregistered:
        errors.append("files under assets/ not in the register: " + ", ".join(unregistered))
    if attribution:
        errors.append("attribution required but attribution_text empty: " + ", ".join(attribution))
    ai = [a["id"] for a in entries if a.get("ai_generated")]
    return {
        "status": "fail" if errors else "pass",
        "count": len(entries),
        "missing_files": missing,
        "unregistered_files": unregistered,
        "attribution_missing": attribution,
        "ai_generated": ai,
        "licenses": sorted({a.get("license", "?") for a in entries}),
        "errors": errors,
        "warnings": [f"AI-generated assets need disclosure review: {', '.join(ai)}"] if ai else [],
    }
