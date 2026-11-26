"""Standard episode folder layout, creation and approval gates."""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

from . import config

EPISODES_ROOT = config.REPO / "episodes"
GATES = ("research", "script", "storyboard", "prototype", "final_cut")
LAYOUT = ("research", "script", "storyboard", "blender/shots", "blender/scripts", "renders", "audio/narration",
          "audio/music", "audio/sfx", "audio/mix", "edit/clips", "thumbnail", "final", "logs", "qc")


class Episode:
    """Paths inside one episode folder. Nothing is created until a tool writes."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"Episode folder not found: {self.root}")

    # files
    episode_json = property(lambda self: self.root / "episode.json")
    dossier = property(lambda self: self.root / "research" / "source_dossier.json")
    ledger = property(lambda self: self.root / "research" / "claim_ledger.json")
    script = property(lambda self: self.root / "script" / "script.md")
    storyboard = property(lambda self: self.root / "storyboard" / "storyboard.json")
    log_file = property(lambda self: self.root / "logs" / "pipeline.log")
    qc_dir = property(lambda self: self.root / "qc")

    def shot_blend(self, scene_id: str) -> Path:
        return self.root / "blender" / "shots" / f"{scene_id}.blend"

    def render_dir(self, mode: str, scene_id: str) -> Path:
        return self.root / "renders" / mode / scene_id

    def clip(self, mode: str, scene_id: str) -> Path:
        return self.root / "edit" / "clips" / mode / f"{scene_id}.mp4"

    @property
    def meta(self) -> dict:
        return config.load_json(self.episode_json) if self.episode_json.is_file() else {}

    @property
    def episode_id(self) -> str:
        return self.meta.get("episode_id") or self.root.name.split("_")[0]

    def approve(self, gate: str, by: str, date: str | None = None) -> dict:
        if gate not in GATES:
            raise ValueError(f"Unknown gate {gate!r}; use one of {', '.join(GATES)}")
        meta = self.meta
        meta.setdefault("approvals", {g: None for g in GATES})
        meta["approvals"][gate] = {"approved_by": by, "date": date or _dt.date.today().isoformat()}
        config.write_json(self.episode_json, meta)
        return meta


def find_episode(ref: str, root: Path = EPISODES_ROOT) -> Path:
    """Accept a folder path or an episode ID such as 'EP002'."""
    p = Path(ref)
    if p.is_dir():
        return p.resolve()
    matches = sorted(d for d in Path(root).glob(f"{ref}_*") if d.is_dir()) + \
        [d for d in [Path(root) / ref] if d.is_dir()]
    if not matches:
        raise FileNotFoundError(f"No episode folder for {ref!r} under {root}")
    return matches[0].resolve()


def create_episode(episode_id: str, slug: str, title: str, pillar: str, root: Path = EPISODES_ROOT) -> Episode:
    if not re.fullmatch(r"EP\d{3,}", episode_id):
        raise ValueError("Episode ID must look like EP002")
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError("Slug must be lowercase letters, digits and underscores")
    folder = Path(root) / f"{episode_id}_{slug}"
    if folder.exists() or list(Path(root).glob(f"{episode_id}_*")):
        raise FileExistsError(f"Episode {episode_id} already exists under {root}")
    for sub in LAYOUT:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    meta = {"episode_id": episode_id, "slug": slug, "title": title, "pillar": pillar, "status": "research",
            "approvals": {g: None for g in GATES}}
    config.write_json(folder / "episode.json", meta)
    templates = config.REPO / "templates"
    for src, dst in (("source_dossier.example.json", "research/source_dossier.json"),
                     ("claim_ledger.example.json", "research/claim_ledger.json"),
                     ("script_template.md", "script/script.md")):
        text = (templates / src).read_text(encoding="utf-8").replace("EPXXX", episode_id)
        (folder / dst).write_text(text, encoding="utf-8")
    return Episode(folder)
